from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional, Set

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from jwt import InvalidTokenError
from pydantic import BaseModel, Field
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from backend.config import ALGORITHM, SECRET_KEY
from backend.controller import (
    good_choice_controller,
    good_comment_controller,
    good_comment_like_controller,
    good_controller,
)
from backend.models import Good, GoodChoice, GoodComment, GoodCommentLike, User
from backend.schemas import (
    GoodChoiceCreate,
    GoodChoiceUpdate,
    GoodCommentCreate,
    GoodCommentLikeCreate,
    GoodCommentLikeUpdate,
    GoodCreate,
    GoodWithChoicesCreate,
    GoodUpdate,
)
from backend.security.password_security import oauth2_scheme

goods = APIRouter(prefix="/goods", tags=["商品管理接口"])
good_choices = APIRouter(prefix="/good-choices", tags=["商品选项接口"])
good_comments = APIRouter(prefix="/good-comments", tags=["商品评论接口"])
good_comment_likes = APIRouter(prefix="/good-comment-likes", tags=["商品评论点赞接口"])

COMMENT_PAGE_SIZE = 10

def _extract_user_id_from_token(token: str) -> int:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="????", headers={"WWW-Authenticate": "Bearer"})
    user_id = decoded.get("uid")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="????", headers={"WWW-Authenticate": "Bearer"})
    return user_id

def _extract_user_id_from_token(token: str) -> int:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="凭证无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decoded.get("uid")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="凭证无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


GoodOut = pydantic_model_creator(
    Good,
    name="GoodOut",
    include=(
        "id",
        "title",
        "description",
        "good_img",
        "is_active",
        "publisher_id",
        "created_at",
        "updated_at",
    ),
)
GoodChoiceOut = pydantic_model_creator(
    GoodChoice,
    name="GoodChoiceOut",
    include=(
        "id",
        "good_id",
        "name",
        "price",
        "swiper_img",
        "stock",
        "display_order",
        "created_at",
        "updated_at",
    ),
)
GoodCommentOut = pydantic_model_creator(
    GoodComment,
    name="GoodCommentOut",
    include=(
        "id",
        "good_id",
        "user_id",
        "parent_id",
        "content",
        "like_count",
        "is_deleted",
        "created_at",
        "updated_at",
    ),
)
GoodCommentLikeOut = pydantic_model_creator(
    GoodCommentLike,
    name="GoodCommentLikeOut",
    include=("id", "comment_id", "user_id", "created_at"),
)


class GoodChoiceListResponse(BaseModel):
    total: int
    items: List[GoodChoiceOut]


class GoodChoiceInfo(BaseModel):
    id: int
    name: str
    price: Decimal
    swiperImg: str
    stock: int = Field(default=0, ge=0)


class IconWithNum(BaseModel):
    type: Optional[List[str]] = None
    num: int = 0


class StoreInfo(BaseModel):
    avatar: str = ""
    name: str = ""


class CommentPayload(BaseModel):
    id: int
    goodId: int
    userId: Optional[int] = None
    parentId: Optional[int] = None
    content: str
    likeCount: int
    createdAt: datetime
    updatedAt: datetime
    isDeleted: bool = False
    hasBeenLiked: bool = False


class CommentUser(BaseModel):
    id: int
    username: str
    avatarUrl: Optional[str] = None


class CommentInfo(BaseModel):
    user: Optional[CommentUser] = None
    comment: CommentPayload
    icons: List[IconWithNum] = Field(default_factory=list)
    storeInfo: Optional["StoreInfoPayload"] = None


class GoodInfosResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    goodImg: Optional[str] = None
    store: StoreInfo
    choices: List[GoodChoiceInfo] = Field(default_factory=list)
    comments: List[CommentInfo] = Field(default_factory=list)


class GoodListItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    goodImg: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    store: StoreInfo


class GoodInfo(BaseModel):
    id: int
    goodImg: Optional[str] = None
    title: str
    store: Optional[StoreInfo] = None
    has_been_favorited: bool = False


class StoreInfoPayload(BaseModel):
    storeOwner: StoreInfo
    Goods: List[GoodInfo] = Field(default_factory=list)


class GoodCommentListResponse(BaseModel):
    total: int
    page: int
    pageSize: int
    items: List[CommentInfo]


class GoodListResponse(BaseModel):
    total: int
    items: List[GoodListItem]


def _build_comment_infos(
    comments: List[GoodComment],
    *,
    include_store_info: bool = False,
    liked_comment_ids: Optional[Set[int]] = None,
) -> List[CommentInfo]:
    comment_infos: List[CommentInfo] = []
    for comment in comments:
        if comment.like_count > 0:
            icon = IconWithNum(num=comment.like_count)
        else:
            icon = IconWithNum(type=["like"], num=0)
        icons = [icon]

        has_been_liked = (
            bool(liked_comment_ids) and comment.id in liked_comment_ids
        )
        user_model = getattr(comment, "user", None)
        user_payload = (
            CommentUser(
                id=user_model.id,
                username=user_model.username,
                avatarUrl=user_model.avatar_url,
            )
            if user_model
            else None
        )

        store_info_payload: Optional[StoreInfoPayload] = None
        if include_store_info:
            good_model = getattr(comment, "good", None)
            if good_model:
                store_info_payload = StoreInfoPayload(
                    storeOwner=_build_store_info(getattr(good_model, "publisher", None)),
                    Goods=[
                        GoodInfo(
                            id=good_model.id,
                            goodImg=good_model.good_img,
                            title=good_model.title,
                            store=None,
                            has_been_favorited=False,
                        )
                    ],
                )

        comment_infos.append(
            CommentInfo(
                user=user_payload,
                comment=CommentPayload(
                    id=comment.id,
                    goodId=comment.good_id,
                    userId=comment.user_id,
                    parentId=comment.parent_id,
                    content=comment.content,
                    likeCount=comment.like_count,
                    createdAt=comment.created_at,
                    updatedAt=comment.updated_at,
                    isDeleted=comment.is_deleted,
                    hasBeenLiked=has_been_liked,
                ),
                icons=icons,
                storeInfo=store_info_payload,
            )
        )
    return comment_infos


def _build_store_info(user: Optional[User]) -> StoreInfo:
    if not user:
        return StoreInfo()
    return StoreInfo(avatar=user.avatar_url or "", name=user.username or "")


async def _get_liked_comment_ids(
    user_id: Optional[int],
    comment_ids: List[int],
) -> Set[int]:
    if not user_id or not comment_ids:
        return set()
    liked = await GoodCommentLike.filter(
        user_id=user_id, comment_id__in=comment_ids
    ).values_list("comment_id", flat=True)
    return set(liked)


@goods.get("/", response_model=GoodListResponse)
async def list_goods(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
):
    search = Q()
    if keyword:
        search &= Q(title__icontains=keyword)
    if is_active is not None:
        search &= Q(is_active=is_active)
    total, records = await good_controller.list_items(
        page=page,
        page_size=page_size,
        search=search,
        order=["-created_at"],
    )
    items: List[GoodListItem] = []
    for good in records:
        publisher = getattr(good, "publisher", None)
        items.append(
            GoodListItem(
                id=good.id,
                title=good.title,
                description=good.description,
                goodImg=good.good_img,
                is_active=good.is_active,
                created_at=good.created_at,
                updated_at=good.updated_at,
                store=_build_store_info(publisher),
            )
        )
    return GoodListResponse(total=total, items=items)


async def _build_good_infos_response(good_id: int) -> GoodInfosResponse:
    good = await good_controller.get_item(good_id)
    choices = await GoodChoice.filter(good_id=good_id).order_by("display_order", "id")
    comments = (
        await GoodComment.filter(good_id=good_id)
        .order_by("-created_at")
        .prefetch_related("user")
    )

    choice_payloads = [
        GoodChoiceInfo(
            id=choice.id,
            name=choice.name,
            price=choice.price,
            swiperImg=choice.swiper_img,
            stock=choice.stock,
        )
        for choice in choices
    ]

    comment_infos = _build_comment_infos(comments)
    store = _build_store_info(getattr(good, "publisher", None))

    return GoodInfosResponse(
        id=good.id,
        title=good.title,
        description=good.description,
        goodImg=good.good_img,
        store=store,
        choices=choice_payloads,
        comments=comment_infos,
    )


@goods.post("/", response_model=GoodInfosResponse, status_code=status.HTTP_201_CREATED)
async def create_good(payload: GoodWithChoicesCreate):
    base_data = payload.model_dump(exclude={"choices"})
    created = await good_controller.create_item(GoodCreate(**base_data))

    for index, choice in enumerate(payload.choices or []):
        choice_data = choice.model_dump()
        if "display_order" not in choice_data or choice_data["display_order"] is None:
            choice_data["display_order"] = index
        await good_choice_controller.create_item(
            GoodChoiceCreate(good_id=created.id, **choice_data)
        )

    return await _build_good_infos_response(created.id)


@goods.get("/{good_id}", response_model=GoodInfosResponse)
async def get_good(good_id: int):
    try:
        return await _build_good_infos_response(good_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")


@goods.put("/{good_id}", response_model=GoodOut)
async def update_good(good_id: int, payload: GoodUpdate):
    if not payload.model_dump(exclude_unset=True, exclude_none=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="请提供需要更新的字段"
        )
    try:
        updated = await good_controller.update_item(good_id, payload)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    return await GoodOut.from_tortoise_orm(updated)


@goods.delete("/{good_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_good(good_id: int):
    try:
        await good_controller.delete_item(good_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")


@good_choices.get("/", response_model=GoodChoiceListResponse)
async def list_good_choices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    good_id: Optional[int] = Query(default=None),
):
    search = Q()
    if good_id:
        search &= Q(good_id=good_id)
    total, records = await good_choice_controller.list_items(
        page=page,
        page_size=page_size,
        search=search,
        order=["display_order", "id"],
    )
    items = [await GoodChoiceOut.from_tortoise_orm(obj) for obj in records]
    return GoodChoiceListResponse(total=total, items=items)


@good_choices.get(
    "/from-good-get-choices",
    response_model=GoodChoiceListResponse,
    summary="根据商品ID获取全部选项",
)
async def get_choices_by_good(good_id: int = Query(..., ge=1)):
    query = (
        GoodChoice.filter(good_id=good_id)
        .order_by("display_order", "id")
        .only(
            "id",
            "good_id",
            "name",
            "price",
            "swiper_img",
            "stock",
            "display_order",
            "created_at",
            "updated_at",
        )
    )
    records = await query
    items = [await GoodChoiceOut.from_tortoise_orm(obj) for obj in records]
    return GoodChoiceListResponse(total=len(items), items=items)


@good_comments.get(
    "/from-good-get-comments",
    response_model=GoodCommentListResponse,
    summary="根据商品ID分页获取评论（每页10条）",
)
async def get_comments_by_good(
    token: Annotated[str, Depends(oauth2_scheme)],
    good_id: int = Query(..., ge=1),
    page: int = Query(1, ge=1),
):
    user_id = _extract_user_id_from_token(token)
    base_query = GoodComment.filter(good_id=good_id)
    total = await base_query.count()

    offset = (page - 1) * COMMENT_PAGE_SIZE
    records = (
        await base_query.order_by("-created_at")
        .offset(offset)
        .limit(COMMENT_PAGE_SIZE)
        .prefetch_related("user")
    )
    comment_ids = [comment.id for comment in records]
    liked_ids = await _get_liked_comment_ids(user_id, comment_ids)
    items = _build_comment_infos(records, liked_comment_ids=liked_ids)
    return GoodCommentListResponse(
        total=total,
        page=page,
        pageSize=COMMENT_PAGE_SIZE,
        items=items,
    )


@good_comments.get(
    "/by-likes",
    response_model=GoodCommentListResponse,
    summary="获取全部评论（按点赞数排序）",
)
async def list_comments_by_likes(
    token: Annotated[str, Depends(oauth2_scheme)],
    page: int = Query(1, ge=1),
):
    user_id = _extract_user_id_from_token(token)
    base_query = GoodComment.all()
    total = await base_query.count()

    offset = (page - 1) * COMMENT_PAGE_SIZE
    query = (
        base_query.order_by("-like_count", "-created_at")
        .offset(offset)
        .limit(COMMENT_PAGE_SIZE)
        .prefetch_related("user", "good__publisher")
    )
    records = await query
    comment_ids = [comment.id for comment in records]
    liked_ids = await _get_liked_comment_ids(user_id, comment_ids)
    items = _build_comment_infos(
        records,
        include_store_info=True,
        liked_comment_ids=liked_ids,
    )
    return GoodCommentListResponse(
        total=total,
        page=page,
        pageSize=COMMENT_PAGE_SIZE,
        items=items,
    )


@good_choices.get("/{choice_id}", response_model=GoodChoiceOut)
async def get_good_choice(choice_id: int):
    try:
        record = await good_choice_controller.get_item(choice_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选项不存在")
    return await GoodChoiceOut.from_tortoise_orm(record)


@good_choices.put("/{choice_id}", response_model=GoodChoiceOut)
async def update_good_choice(choice_id: int, payload: GoodChoiceUpdate):
    if not payload.model_dump(exclude_unset=True, exclude_none=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="请提供需要更新的字段"
        )
    try:
        updated = await good_choice_controller.update_item(choice_id, payload)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选项不存在")
    return await GoodChoiceOut.from_tortoise_orm(updated)


@good_choices.delete("/{choice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_good_choice(choice_id: int):
    try:
        await good_choice_controller.delete_item(choice_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选项不存在")


@good_comments.post(
    "/", response_model=GoodCommentOut, status_code=status.HTTP_201_CREATED
)
async def create_good_comment(
    payload: GoodCommentCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="凭证无效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise credentials_exception

    user_id = decoded.get("uid")
    if not user_id:
        raise credentials_exception

    data = payload.model_dump()
    data["user_id"] = user_id
    created = await good_comment_controller.create_item(data)
    return await GoodCommentOut.from_tortoise_orm(created)


@good_comment_likes.post(
    "/", response_model=GoodCommentLikeOut, status_code=status.HTTP_201_CREATED
)
async def create_good_comment_like(payload: GoodCommentLikeCreate):
    created = await good_comment_like_controller.create_item(payload)
    return await GoodCommentLikeOut.from_tortoise_orm(created)


@good_comment_likes.get("/check")
async def check_good_comment_like(
    comment_id: int = Query(..., ge=1),
    user_id: int = Query(..., ge=1),
):
    exists = await GoodCommentLike.filter(
        comment_id=comment_id,
        user_id=user_id,
    ).exists()
    return {"liked": exists}
