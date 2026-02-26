from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Annotated, Dict, List, Optional, Tuple

from tortoise.expressions import F, Q

from backend.sc_utils import _parse_image_url, _extract_user_id_from_token
from settings import APP_BASE_URL
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from jwt import InvalidTokenError
from pydantic import BaseModel, Field
from tortoise.functions import Count

from backend.config import ALGORITHM, SECRET_KEY
from backend.controller import draft_controller
from backend.models import Article, ArticleComment, Collection, UserFavorite, UserLike, UserViewHistory, User, \
    UserAttention
from backend.schemas import ArticleCreate, ArticleUpdate, DraftCreate, DraftUpdate
from backend.security.password_security import oauth2_scheme

draft = APIRouter(prefix="/drafts", tags=["Drafts"])


@draft.get("/items", response_model=List[DraftCreate], summary="获取用户草稿列表")
async def get_drafts(
        token: Annotated[str, Depends(oauth2_scheme)],
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
):
    """
    获取用户草稿
    """
    user_id = _extract_user_id_from_token(token)
    return await draft_controller.list_items(page, page_size, Q(), user_id)


@draft.post("", summary="创建草稿", status_code=status.HTTP_201_CREATED)
async def create_draft(
        token: Annotated[str, Depends(oauth2_scheme)],
        draft_in: DraftCreate
):
    """
    创建草稿
    """
    user_id = _extract_user_id_from_token(token)
    await draft_controller.create_item(
        draft_in.dict(exclude_none=True, exclude_unset=True, exclude_defaults=True) | {"author_id": user_id})
    return {"message": "创建成功"}


@draft.put("/{draft_id}", summary="更新草稿")
async def update_draft(
        token: Annotated[str, Depends(oauth2_scheme)],
        draft_id: int,
        draft_in: DraftUpdate
):
    """
    更新草稿
    """
    user_id = _extract_user_id_from_token(token)
    await draft_controller.update_item(draft_id,
                                       draft_in.dict(exclude_none=True, exclude_unset=True, exclude_defaults=True),
                                       Q(author_id=user_id))

    return {"message": "更新成功"}


@draft.delete("/{draft_id}", summary="删除草稿")
async def delete_draft(
        token: Annotated[str, Depends(oauth2_scheme)],
        draft_id: int
):
    """
    删除草稿
    """
    user_id = _extract_user_id_from_token(token)
    await draft_controller.delete_item(draft_id, Q(author_id=user_id))
