from datetime import timedelta
from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from backend.api.v1.endpoints.article import _extract_user_id_from_token
from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES
from backend.core import rt
from backend.controller import user_controller
from backend.models import User, UserAttention
from backend.schemas import UserCreate, UserUpdate
from backend.security.password_security import create_access_token, verify_password, get_password_hash, oauth2_scheme

user = APIRouter(prefix="/users", tags=["用户管理接口"])

UserOut = pydantic_model_creator(User, name="UserOut", exclude=("password_hash",))


class UserListResponse(BaseModel):
    total: int
    items: List[UserOut]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SimpleUser(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None


class UserAttentionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[SimpleUser]


@user.get("/me", description="获取当前用户信息")
async def get_me(token: Annotated[str, Depends(oauth2_scheme)], input_user_id: Optional[int] = None):
    user_id = _extract_user_id_from_token(token)
    if input_user_id:
        following = await UserAttention.filter(following_id=input_user_id, follower_id=user_id).exists()
        userInfo = await User.get(id=input_user_id)
    else:
        following = await UserAttention.filter(following_id=user_id, follower_id=user_id).exists()
        userInfo = await User.get(id=user_id)

    user = (await UserOut.from_tortoise_orm(userInfo)).model_dump()
    return {
        **user,
        'following': following,
    }


@user.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate):
    created = await user_controller.create_item(user_in)
    return await UserOut.from_tortoise_orm(created)


@user.get("/", response_model=UserListResponse)
async def list_users(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        keyword: Optional[str] = None,
):
    search = Q()
    if keyword:
        search = Q(username__icontains=keyword) | Q(email__icontains=keyword)
    total, records = await user_controller.list_items(
        page=page, page_size=page_size, search=search, order=["-created_at"]
    )
    items = [await UserOut.from_tortoise_orm(obj) for obj in records]
    return UserListResponse(total=total, items=items)


@user.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_record = await User.filter(username=form_data.username).first()
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或密码错误",
        )
    if not user_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    verify = verify_password(form_data.password, user_record.password_hash)
    if not verify:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=verify,
        )

    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_record.username, "uid": user_record.id},
        expires_delta=expires_delta,
    )
    ttl_seconds = int(expires_delta.total_seconds())
    redis_key = f"user:token:{user_record.id}"
    try:
        rt.setex(redis_key, ttl_seconds, access_token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌缓存失败",
        ) from exc

    return LoginResponse(access_token=access_token, expires_in=ttl_seconds)


@user.get("/attentions", response_model=UserAttentionListResponse, description="获取当前用户关注的用户列表")
async def list_user_attentions(
        token: Annotated[str, Depends(oauth2_scheme)],
        page: int = Query(1, ge=1),
):
    user_id = _extract_user_id_from_token(token)
    page_size = 20
    queryset = UserAttention.filter(follower_id=user_id).prefetch_related("following").order_by("-created_at")
    total = await queryset.count()
    records = await queryset.offset((page - 1) * page_size).limit(page_size)
    items = [
        SimpleUser(
            id=attention.following.id,
            username=attention.following.username,
            avatar_url=attention.following.avatar_url,
        )
        for attention in records
    ]
    return UserAttentionListResponse(total=total, page=page, page_size=page_size, items=items)


@user.post("/attentions")
async def toggle_attention(token: Annotated[str, Depends(oauth2_scheme)],
                           following_id: int):
    user_id = _extract_user_id_from_token(token)
    user_attention = UserAttention.filter(follower_id=user_id, following_id=following_id)
    exist = await user_attention.exists()
    if exist:
        result = await user_attention.first()
        await result.delete()
        return {
            'msg': '已取消关注',
            'following_id': result.following_id
        }
    else:
        result = await UserAttention.create(follower_id=user_id, following_id=following_id)
        return {
            'msg': '关注成功',
            'following_id': result.following_id
        }


@user.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    try:
        record = await user_controller.get_item(user_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return await UserOut.from_tortoise_orm(record)


@user.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_in: UserUpdate):
    if not user_in.model_dump(exclude_unset=True, exclude_none=True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请至少提供一个需要更新的字段")
    try:
        updated = await user_controller.update_item(user_id, user_in)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return await UserOut.from_tortoise_orm(updated)


@user.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    try:
        await user_controller.delete_item(user_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
