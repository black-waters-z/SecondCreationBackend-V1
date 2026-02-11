from typing import Annotated, List

from tortoise.contrib.pydantic import pydantic_model_creator

from backend.sc_utils import _parse_image_url
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from backend.models import Collection, User, Article
from backend.security.password_security import oauth2_scheme
from backend.api.v1.endpoints.article import _extract_user_id_from_token

collection = APIRouter(prefix="/collections", tags=["合集接口"])


class CollectionArticleOut(BaseModel):
    id: int
    title: str
    content: str
    image_urls: list[str]
    like_count: int
    favorite_count: int
    comment_count: int


UserOut = pydantic_model_creator(User, name="UserOut", exclude=("password_hash",))


class CollectionArticleWithUserOut(BaseModel):
    user: UserOut
    items: List[CollectionArticleOut]


@collection.post("/{collection_id}/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def subscribe_collection(
        collection_id: int,
        token: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    user_id = _extract_user_id_from_token(token)
    collection_obj = await Collection.filter(id=collection_id).first()
    if not collection_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在",
        )
    user = await User.get(id=user_id)
    await collection_obj.subscribers.add(user)
    return {"message": "订阅成功"}


@collection.get("", summary="列举用户合集")
async def list_collections(token: Annotated[str, Depends(oauth2_scheme)],
                           page: int = Query(1, ge=1),
                           page_size: int = Query(10, ge=10, le=100)):
    # await Collection
    user_id = _extract_user_id_from_token(token)
    user_collection = await Collection.filter(author_id=user_id) \
        .offset((page - 1) * page_size).limit(page_size) \
        .values("id", "name", "description")

    for collection in user_collection:
        collection["article_count"] = await Collection.filter(id=collection["id"]).count()
    return user_collection


@collection.get("/articles", summary="从合集获取文章", response_model=CollectionArticleWithUserOut)
async def list_collection_articles(token: Annotated[str, Depends(oauth2_scheme)],
                                   collection_id: int,
                                   page: int = Query(1, ge=1),
                                   page_size: int = Query(10, ge=10, le=100)):
    user_id = _extract_user_id_from_token(token)
    # 查询合集的作者
    collection = await Collection.filter(id=collection_id).prefetch_related("author").first()
    # 查询合集文章信息
    articles = await Article.filter(collection_id=collection_id, author_id=user_id). \
        offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for article in articles:
        # 创建响应模型实例
        comment_count = await article.comments.all().count()  # 预加载评论数量
        article_out = CollectionArticleOut(
            id=article.id,
            title=article.title,
            content=article.content[:100],  # 截取内容
            image_urls=_parse_image_url(article),  # 传递 ORM 对象
            like_count=article.like_count,
            favorite_count=article.favorite_count,
            comment_count=comment_count,  # 这里需要根据实际情况计算评论数量
        )
        result.append(article_out)
    return {
        "items":result,
        "user": UserOut.from_orm(collection.author)
    }
