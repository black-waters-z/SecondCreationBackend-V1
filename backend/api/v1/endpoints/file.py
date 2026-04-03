import os
from typing import Annotated

from fastapi import APIRouter, UploadFile, HTTPException, File, Depends
from pydantic import BaseModel
import base64
import uuid
import re

import os
from fastapi import UploadFile, Form

from backend.models import FileUploadModel
from backend.sc_utils import _extract_user_id_from_token
from backend.security.password_security import oauth2_scheme

UPLOAD_DIR = "/static/uploads/"

file = APIRouter()

class ImageUploadRequest(BaseModel):
    file: dict = {}
    status: str = ""
    message: str = ""
    objectUrl: str = ""
    content: str  # Base64 图片数据


@file.post("/upload-image-file")
async def upload_image_file(image: UploadFile = File(...)):
    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }

    if image.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    filename = f"{uuid.uuid4().hex}{allowed_types[image.content_type]}"
    upload_dir = os.path.join("backend", "static", "upload_IMG")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, filename)

    try:
        contents = await image.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        with open(save_path, "wb") as buffer:
            buffer.write(contents)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error: {exc}")

    return {
        "status": "success",
        "message": "Image uploaded successfully",
        "objectUrl": f"/static/upload_IMG/{filename}",
        "filename": filename,
        "fileSize": len(contents),
    }


@file.post("/upload-video-file")
async def upload_video_file(video: UploadFile = File(...)):
    allowed_video_types = {
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/ogg": ".ogv",
    }

    if video.content_type not in allowed_video_types:
        raise HTTPException(status_code=400, detail="Unsupported video format")

    filename = f"{uuid.uuid4().hex}{allowed_video_types[video.content_type]}"
    upload_dir = os.path.join("backend", "static", "upload_Video")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, filename)

    try:
        contents = await video.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        with open(save_path, "wb") as buffer:
            buffer.write(contents)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error: {exc}")

    return {
        "status": "success",
        "message": "Video uploaded successfully",
        "objectUrl": f"/static/upload_Video/{filename}",
        "filename": filename,
        "fileSize": len(contents),
    }


@file.post("/upload-image")
async def post_upload_image(request: ImageUploadRequest):
    try:
        # 检查是否有 content 数据
        if not request.content:
            raise HTTPException(status_code=400, detail="No image data provided")

        # 解析 Base64 数据
        base64_data = request.content

        # 使用正则表达式匹配 data URL 格式
        match = re.match(r'^data:image/(\w+);base64,(.+)$', base64_data)

        if not match:
            raise HTTPException(status_code=400, detail="Invalid base64 image format")

        # 获取文件类型和纯 Base64 数据
        image_type = match.group(1)
        pure_base64 = match.group(2)

        # 确保图片类型有效
        if image_type not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
            raise HTTPException(status_code=400, detail="Unsupported image format")

        # 解码 Base64
        try:
            image_data = base64.b64decode(pure_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 encoding")

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.{image_type}"
        print(">>>", request.file)
        save_path = f"backend/static/uploadimg/{filename}"

        # 确保上传目录存在
        import os
        os.makedirs("backend/static/uploadimg", exist_ok=True)

        # 保存文件
        with open(save_path, "wb") as f:
            f.write(image_data)

        # 返回成功响应
        return {
            "status": "success",
            "message": "Image uploaded successfully",
            "objectUrl": f"/static/uploadimg/{filename}",
            "filename": filename,
            "fileSize": len(image_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@file.delete("/upload-image")
def delete_upload_image(file_name: str):
    file_path = f'backend/static/uploadimg/{file_name}'
    print(">>>", file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"status": "success", "message": "文件删除成功"}
    else:
        return {"status": "error", "message": "文件不存在"}


class InitUploadRequest(BaseModel):
    file_hash: str
    total_chunks: int


@file.post("/upload/init", summary="大文件切片初始化上传")
async def init_upload(token: Annotated[str, Depends(oauth2_scheme)], init_request: InitUploadRequest):
    # 写数据库
    task = {
        "file_hash": init_request.file_hash,
        "total_chunks": init_request.total_chunks,
        "uploaded_chunks": 0
    }
    user_id = _extract_user_id_from_token(token)
    print(">>>", task)
    await FileUploadModel.create(**task, user_id=user_id)

    return {"msg": "ok"}


@file.post("/upload/chunk", summary="大文件切片上传")
async def upload_chunk(
        file: UploadFile,
        hash: str = Form(...),
        index: int = Form(...)
):
    chunk_dir = os.path.join("backend", "static", "uploads", hash)

    os.makedirs(chunk_dir, exist_ok=True)

    chunk_path = f"{chunk_dir}/{index}"

    with open(chunk_path, "wb") as f:
        f.write(await file.read())

    # 更新数据库进度
    # uploaded_chunks += 1

    return {"msg": "chunk uploaded"}


@file.get("/upload/progress", summary="大文件上传进度查询")
def progress(file_hash: str):
    chunk_dir = f"uploads/{file_hash}"

    if not os.path.exists(chunk_dir):
        return {"uploaded": []}

    uploaded = os.listdir(chunk_dir)

    return {"uploaded": uploaded}


class MergeChunksRequest(BaseModel):
    file_hash: str


@file.post("/upload/merge", summary="大文件切片合并")
async def merge_chunks(token: Annotated[str, Depends(oauth2_scheme)], file_request: MergeChunksRequest):
    import shutil
    user_id = _extract_user_id_from_token(token)
    file_upload = await FileUploadModel.get(file_hash=file_request.file_hash, user_id=user_id)
    if not file_upload:
        raise HTTPException(status_code=404, detail="File upload not found")
    chunk_dir = os.path.join("backend", "static", "uploads", file_request.file_hash)
    file_path = os.path.join("backend", "static", "upload_Video", f"{file_request.file_hash}.mp4")
    os.makedirs(chunk_dir, exist_ok=True)
    with open(file_path, "wb") as f:
        for i in range(file_upload.total_chunks):
            chunk_path = f"{chunk_dir}/{i}"
            with open(chunk_path, "rb") as chunk_file:
                f.write(chunk_file.read())
    # 删除切片
    await file_upload.delete()
    # 删除切片 目录
    shutil.rmtree(chunk_dir)
    return {"msg": "ok",
            "fileUrl": f"{file_request.file_hash}.mp4"
            }
