import os

from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel
import base64
import uuid
import re

file = APIRouter()


class ImageUploadRequest(BaseModel):
    file: dict = {}
    status: str = ""
    message: str = ""
    objectUrl: str = ""
    content: str  # Base64 图片数据


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
