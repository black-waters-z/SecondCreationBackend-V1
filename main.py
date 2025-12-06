from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from tortoise.contrib.fastapi import register_tortoise
from settings import TORTOISE_CONFIG
from backend.api.v1.endpoints \
    import *
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

app = FastAPI()

register_tortoise(app,
                  config=TORTOISE_CONFIG,
                  # generate_schemas=True, # 如果数据库为空则自动生成对应表单，生产环境不要开
                  # add_exception_handlers=True # 生产环境不要开，会泄露调试信息
                  )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.mount("/static", StaticFiles(directory="./backend/static"), name="static")

@app.get("/static/{file_path:path}")
async def serve_static_file(file_path: str):
    static_dir = Path("./backend/static")
    full_path = static_dir / file_path

    # 安全检查
    try:
        full_path.resolve().relative_to(static_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        str(full_path),
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(user, tags=["用户管理接口"])
app.include_router(login, tags=["登录接口"])
app.include_router(email, tags=["邮件发送服务"])
app.include_router(active, tags=["激活账号"])
app.include_router(article, tags=["文章管理"])
app.include_router(favorites, tags=["收藏夹"])
app.include_router(like, tags=["点赞接口"])
app.include_router(first_comment, tags=["评论接口"])
app.include_router(file, tags=["文件上传"])
app.include_router(ws, tags=["私信ws接口"])
app.include_router(follow, tags=["关注接口"])
app.include_router(second_comment, tags=["二级评论"])
app.include_router(draft, tags=["草稿箱"])
app.include_router(test, tags=["测试"])

if __name__ == '__main__':
    # 宿舍
    uvicorn.run("main:app", port=8080, reload=True, log_level=True, host="localhost")
    # 教室
    # uvicorn.run("main:app",port=8080, reload=True, log_level=True,host="10.81.24.42")
