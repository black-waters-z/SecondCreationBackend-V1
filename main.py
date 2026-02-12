from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from tortoise.contrib.fastapi import register_tortoise

import settings
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
app.include_router(file, tags=["文件上传"])
app.include_router(article, tags=["文章管理接口"])
app.include_router(comment, tags=["文章评论接口"])
app.include_router(tag, tags=["标签管理接口"])
app.include_router(tag_relation, tags=["标签关联接口"])
app.include_router(user_view_history, tags=["用户浏览记录接口"])
app.include_router(goods, tags=["商品管理接口"])
app.include_router(good_choices, tags=["商品选项接口"])
app.include_router(good_comments, tags=["商品评论接口"])
app.include_router(good_comment_likes, tags=["商品评论点赞接口"])
app.include_router(cart, tags=["购物车接口"])
app.include_router(collection, tags=["合集接口"])
app.include_router(article_data, tags=["文章数据接口"])
app.include_router(contact, tags=["所有互动接口"])

if __name__ == '__main__':
    # 宿舍
    # uvicorn.run("main:app", port=8080, reload=True, log_level=True, host="localhost")
    # 教室
    uvicorn.run("main:app",port=8080, reload=True, log_level=True,host=settings.BASE_HOST)
