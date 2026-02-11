from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from tortoise.expressions import F

from backend.api.v1.endpoints.article import _extract_user_id_from_token
from backend.models import Article, ArticleComment, ArticleCommentLike, User
from backend.security.password_security import oauth2_scheme

comment = APIRouter(prefix="/comments", tags=["文章评论接口"])

PAGE_SIZE = 10


class UserInfo(BaseModel):
    id: int
    username: str
    avatar_url: str


class ArticleCommentBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    parent_id: Optional[int] = None
    content: str
    like_count: int
    reply_count: int
    has_liked: Optional[bool] = Field(default=False)
    created_at: datetime
    updated_at: datetime
    user: UserInfo

    @field_validator('user', mode='before')
    @classmethod
    def validate_user(cls, value):
        if isinstance(value, dict):
            return UserInfo(**value)
        elif hasattr(value, 'username') and hasattr(value, 'avatar_url') and hasattr(value, 'id'):
            # 假设这是一个 User ORM 实例
            return UserInfo(username=value.username, avatar_url=value.avatar_url, id=value.id)
        return value


class ArticleCommentListItem(ArticleCommentBaseOut):
    pass


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


async def _resolve_root_comment_id(comment: ArticleComment) -> Optional[int]:
    """
    获取评论所属会话的最顶层评论ID，用于在多级回复场景中标记根节点
    """
    current = comment
    visited_parent_ids = set()
    while current and current.parent_id:
        parent_id = current.parent_id
        if parent_id in visited_parent_ids:
            break
        visited_parent_ids.add(parent_id)
        parent_comment = await ArticleComment.filter(
            id=parent_id,
            is_deleted=False,
        ).first()
        if not parent_comment:
            return parent_id
        current = parent_comment
    return current.id if current else None


@comment.get("", response_model=ArticleCommentListResponse)
async def list_article_comments(
        article_id: int = Query(..., ge=1),
        page: int = Query(1, ge=1),
):
    await _ensure_article_exists(article_id)
    query = ArticleComment.filter(
        article_id=article_id,
        # 首先取一级评论
        parent_id__isnull=True,
        is_deleted=False,
    ).order_by("-created_at").prefetch_related("user")
    total = await query.count()
    records = await query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    # 获取所有二级评论指向的一级                                                                                                         flat=True)
    items: List[ArticleCommentListItem] = []
    for record in records:
        # 将model转化为pydantic实例
        parent_payload = ArticleCommentBaseOut.model_validate(record)
        items.append(
            ArticleCommentListItem(
                # model_dump 将pydantic实例转化为字典
                **parent_payload.model_dump(),
            )
        )
    return ArticleCommentListResponse(
        total=total,
        page=page,
        page_size=PAGE_SIZE,
        items=items,
    )


@comment.get("/childComment")
async def list_article_child_comments(
        token: Annotated[str, Depends(oauth2_scheme)],
        parent_id: int = Query(..., ge=1),
        page: int = Query(1, ge=1),
        page_size: int = Query(PAGE_SIZE, ge=1),
        order_by: str = Query("created_at" or "-created_at" or "like_count")
):
    user_id = _extract_user_id_from_token(token)
    query = (ArticleComment.filter(parent_id=parent_id).prefetch_related("user").order_by(order_by))
    childs = await query.offset(page - 1).limit(page_size)
    result = []
    for child in childs:
        data = ArticleCommentBaseOut.model_validate(child)
        has_liked = await ArticleCommentLike.filter(user_id=user_id, comment_id=child.id).exists()
        data.has_liked = has_liked
        result.append(
            data
        )
    return result


@comment.post(
    "",
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

    new_comment = await ArticleComment.create(
        article_id=payload.article_id,
        parent_id=payload.parent_id,
        user_id=user_id,
        content=payload.content,
    )
    grand_parent_id: Optional[int] = None
    if parent_comment:
        await ArticleComment.filter(id=parent_comment.id).update(
            reply_count=F("reply_count") + 1
        )
        grand_parent_id = await _resolve_root_comment_id(parent_comment)

    user = await User.filter(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    response_payload = {
        "comment_id": new_comment.id,
        "user": {
            "id": user.id,
            "avatar": user.avatar_url,
            "name": user.username,
        },
    }
    if grand_parent_id is not None:
        response_payload["grand_parent_id"] = grand_parent_id
    return response_payload


@comment.delete("/{comment_id}",summary="删除文章评论")
async def delete_article_comment(
        comment_id: int,
        token: Annotated[str, Depends(oauth2_scheme)],
):
    user_id = _extract_user_id_from_token(token)
    comment = await ArticleComment.filter(id=comment_id).first()
    if not comment or comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在",
        )
    if comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除该评论",
        )
    await ArticleComment.filter(id=comment_id).update(is_deleted=True)
    if comment.parent_id:
        await ArticleComment.filter(id=comment.parent_id).update(
            reply_count=F("reply_count") - 1
        )
    return {"message": "删除成功"}

