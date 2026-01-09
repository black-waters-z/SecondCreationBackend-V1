from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from backend.controller import article_controller
from backend.models import Article
from backend.schemas import ArticleCreate, ArticleUpdate

article = APIRouter(prefix="/articles", tags=["文章管理接口"])

ArticleOut = pydantic_model_creator(
    Article,
    name="ArticleOut",
    include=(
        "id",
        "title",
        "subtitle",
        "author_id",
        "content",
        "image_urls",
        "status",
        "published_at",
        "created_at",
        "updated_at",
        "tags",
    )
)


class ArticleListResponse(BaseModel):
    total: int
    items: List[ArticleOut]


@article.get("/{page}")
async def list_articles(page: int):
    total, articles = await article_controller.list_items(page, 10)
    items = [await ArticleOut.from_tortoise_orm(article) for article in articles]
    return ArticleListResponse(total=total, items=items)


@article.post("")
async def create_article(article_in: ArticleCreate):
    try:
        article_obj = await article_controller.create(article_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return await ArticleOut.from_tortoise_orm(article_obj)


@article.get("/detail/{article_id}")
async def get_article(article_id: int):
    article_obj = await article_controller.get_item(article_id)
    return await ArticleOut.from_tortoise_orm(article_obj)


@article.put("/{article_id}")
async def update_article(article_id: int, article_in: ArticleUpdate):
    try:
        updated_article = await article_controller.update_item(article_id, article_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return await ArticleOut.from_tortoise_orm(updated_article)


@article.delete("/{article_id}")
async def delete_article(article_id: int):
    await article_controller.delete_item(article_id)
    return {"status": "success", "message": "删除成功"}
