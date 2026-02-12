from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from tortoise.expressions import F

from backend.api.v1.endpoints.article import _extract_user_id_from_token
from backend.models import Article, ArticleComment, ArticleCommentLike, User, UserFavorite, UserLike
from backend.security.password_security import oauth2_scheme

contact = APIRouter(prefix="/contact")


class ContactArticle(BaseModel):
    id: int
    title: str


class ContactToMeData(BaseModel):
    userId: int
    username: str
    userAction: str
    article: ContactArticle
    comment: Optional[str] = ''
    tip: Optional[int] = 0
    created_at: datetime


@contact.get("/new_count")
async def get_contact_new_count(token: Annotated[str, Depends(oauth2_scheme)]):
    user_id = _extract_user_id_from_token(token)

    count = 0
    count += await ArticleComment.filter(article__author_id=user_id, has_viewed=False).count()
    count += await UserFavorite.filter(article__author_id=user_id, has_viewed=False).count()
    count += await UserLike.filter(article__author_id=user_id, has_viewed=False).count()
    return count


@contact.get("/new")
async def get_contact_new(token: Annotated[str, Depends(oauth2_scheme)]):
    user_id = _extract_user_id_from_token(token)

    comments = await ArticleComment.filter(article__author_id=user_id).prefetch_related('user',
                                                                                        'article').order_by(
        '-created_at').all()
    favorites = await UserFavorite.filter(article__author_id=user_id).prefetch_related('user',
                                                                                       'article').order_by(
        '-favorited_at').all()
    likes = await UserLike.filter(article__author_id=user_id).prefetch_related('user',
                                                                               'article').order_by(
        '-liked_at').all()
    comment_result = []
    for comment in comments:
        article = {}
        article['id'] = comment.article.id
        article['title'] = comment.article.title
        item = ContactToMeData(
            userId=comment.user.id,
            username=comment.user.username,
            userAction='评论',
            article=article,
            comment=comment.content,
            created_at=comment.created_at,
            tip=0
        )

        comment_result.append(item)

    favorite_result = []
    for favorite in favorites:
        article = {}
        article['id'] = favorite.article.id
        article['title'] = favorite.article.title
        item = ContactToMeData(userId=favorite.user.id,
                               username=favorite.user.username,
                               userAction='收藏',
                               article=article,
                               comment=None,
                               created_at=favorite.favorited_at,
                               tip=0
                               )

        favorite_result.append(item)

    like_result = []
    for like in likes:
        article = {}
        article['id'] = like.article.id
        article['title'] = like.article.title
        item = ContactToMeData(userId=like.user.id,
                               username=like.user.username,
                               userAction='喜欢',
                               article=article,
                               comment=None,
                               created_at=like.liked_at,
                               tip=0
                               )

        like_result.append(item)

    comment_ids = [comment.id for comment in comments]
    favorite_ids = [favorite.id for favorite in favorites]
    like_ids = [like.id for like in likes]

    if comment_ids:
        await ArticleComment.filter(id__in=comment_ids).update(has_viewed=True)
    if favorite_ids:
        await UserFavorite.filter(id__in=favorite_ids).update(has_viewed=True)
    if like_ids:
        await UserLike.filter(id__in=like_ids).update(has_viewed=True)

    return {
        'comment': comment_result,
        'favorite': favorite_result,
        'like': like_result
    }
