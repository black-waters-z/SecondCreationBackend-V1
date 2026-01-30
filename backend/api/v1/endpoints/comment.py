from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from tortoise.expressions import F

from backend.api.v1.endpoints.article import _extract_user_id_from_token
from backend.models import Article, ArticleComment
from backend.security.password_security import oauth2_scheme

comment = APIRouter(prefix="/comments", tags=["文章评论接口"])

PAGE_SIZE = 10


class ArticleCommentBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    parent_id: Optional[int] = None
    user_id: Optional[int] = None
    content: str
    like_count: int
    reply_count: int
    created_at: datetime
    updated_at: datetime


class ArticleCommentListItem(ArticleCommentBaseOut):
    childs: List[ArticleCommentBaseOut] = Field(default_factory=list)


class ArticleCommentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ArticleCommentListItem] = Field(default_factory=list)


class ArticleCommentCreate(BaseModel):
    article_id: int = Field(..., ge=1)
    content: str = Field(..., min_length=1)
    parent_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("评论内容不能为空")
        return cleaned


async def _ensure_article_exists(article_id: int) -> None:
    exists = await Article.filter(id=article_id).exists()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在",
        )


async def _load_child_comments(parent_id: int) -> List[ArticleCommentBaseOut]:
    children = (
        await ArticleComment.filter(parent_id=parent_id, is_deleted=False)
        .order_by("created_at")
        .limit(3)
    )
    return [
        ArticleCommentBaseOut.model_validate(child)
        for child in children
    ]


@comment.get("", response_model=ArticleCommentListResponse)
async def list_article_comments(
    article_id: int = Query(..., ge=1),
    page: int = Query(1, ge=1),
):
    await _ensure_article_exists(article_id)
    query = ArticleComment.filter(
        article_id=article_id,
        parent_id__isnull=True,
        is_deleted=False,
    ).order_by("-created_at")
    total = await query.count()
    records = await query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    items: List[ArticleCommentListItem] = []
    for record in records:
        parent_payload = ArticleCommentBaseOut.model_validate(record)
        childs = await _load_child_comments(record.id)
        items.append(
            ArticleCommentListItem(
                **parent_payload.model_dump(),
                childs=childs,
            )
        )
    return ArticleCommentListResponse(
        total=total,
        page=page,
        page_size=PAGE_SIZE,
        items=items,
    )


@comment.post(
    "",
    response_model=ArticleCommentBaseOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_article_comment(
    payload: ArticleCommentCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    user_id = _extract_user_id_from_token(token)
    await _ensure_article_exists(payload.article_id)
    parent_comment: Optional[ArticleComment] = None
    if payload.parent_id is not None:
        parent_comment = await ArticleComment.filter(
            id=payload.parent_id,
            is_deleted=False,
        ).first()
        if not parent_comment or parent_comment.article_id != payload.article_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父级评论不存在",
            )

    created = await ArticleComment.create(
        article_id=payload.article_id,
        parent_id=payload.parent_id,
        user_id=user_id,
        content=payload.content,
    )
    if parent_comment:
        await ArticleComment.filter(id=parent_comment.id).update(
            reply_count=F("reply_count") + 1
        )
    await created.fetch_from_db()
    return ArticleCommentBaseOut.model_validate(created)
