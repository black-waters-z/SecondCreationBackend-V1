from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from backend.controller import user_view_history_controller
from backend.models import UserViewHistory
from backend.schemas import UserViewHistoryCreate, UserViewHistoryUpdate

user_view_history = APIRouter(
    prefix="/user-view-histories",
    tags=["用户浏览记录接口"],
)

UserViewHistoryOut = pydantic_model_creator(
    UserViewHistory,
    name="UserViewHistoryOut",
    include=("id", "user_id", "article_id", "duration", "viewed_at"),
)


class UserViewHistoryListResponse(BaseModel):
    total: int
    items: List[UserViewHistoryOut]


@user_view_history.get("/", response_model=UserViewHistoryListResponse)
async def list_user_view_histories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(default=None),
    article_id: Optional[int] = Query(default=None),
):
    search = Q()
    if user_id:
        search &= Q(user_id=user_id)
    if article_id:
        search &= Q(article_id=article_id)

    total, records = await user_view_history_controller.list_items(
        page=page,
        page_size=page_size,
        search=search,
        order=["-viewed_at"],
    )
    items = [await UserViewHistoryOut.from_tortoise_orm(obj) for obj in records]
    return UserViewHistoryListResponse(total=total, items=items)


@user_view_history.post(
    "/",
    response_model=UserViewHistoryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_view_history(payload: UserViewHistoryCreate):
    created = await user_view_history_controller.create_item(payload)
    return await UserViewHistoryOut.from_tortoise_orm(created)


@user_view_history.get("/{history_id}", response_model=UserViewHistoryOut)
async def get_user_view_history(history_id: int):
    try:
        record = await user_view_history_controller.get_item(history_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="浏览记录不存在",
        )
    return await UserViewHistoryOut.from_tortoise_orm(record)


@user_view_history.put("/{history_id}", response_model=UserViewHistoryOut)
async def update_user_view_history(
    history_id: int,
    history_in: UserViewHistoryUpdate,
):
    if not history_in.model_dump(exclude_unset=True, exclude_none=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请至少提供一个需要更新的字段",
        )
    try:
        updated = await user_view_history_controller.update_item(
            history_id,
            history_in,
        )
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="浏览记录不存在",
        )
    return await UserViewHistoryOut.from_tortoise_orm(updated)


@user_view_history.delete(
    "/{history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_view_history(history_id: int):
    try:
        await user_view_history_controller.delete_item(history_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="浏览记录不存在",
        )
