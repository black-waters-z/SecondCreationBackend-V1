from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Annotated, Dict, List, Optional, Tuple

from tortoise.exceptions import DoesNotExist
from tortoise.expressions import F, Q

from backend.sc_utils import _parse_image_url, _extract_user_id_from_token
from backend.schemas.draft import DraftIn
from settings import APP_BASE_URL
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.controller import draft_controller
from backend.models import Draft
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
        draft_in: DraftIn
):
    """
    创建草稿
    """
    user_id = _extract_user_id_from_token(token)
    await draft_controller.create_item(
        draft_in.dict(exclude_none=True, exclude_unset=True, exclude_defaults=True) | {"author_id": user_id})
    return {"message": "创建成功"}


@draft.get("/{draft_id}", response_model=DraftCreate, summary="获取草稿")
async def get_draft(
        token: Annotated[str, Depends(oauth2_scheme)],
        draft_id: int
):
    """
    获取草稿
    """
    try:
        user_id = _extract_user_id_from_token(token)
        return await Draft.get(id=draft_id, author_id=user_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="草稿不存在")


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


@draft.delete("/{draft_id}", summary="删除草稿", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
        token: Annotated[str, Depends(oauth2_scheme)],
        draft_id: int
):
    """
    删除草稿
    """
    user_id = _extract_user_id_from_token(token)
    await Draft.filter(id=draft_id, author_id=user_id).delete()
    return {"message": "删除成功"}
