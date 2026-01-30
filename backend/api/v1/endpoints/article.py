from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, List, Optional, Tuple
from settings import APP_BASE_URL
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from jwt import InvalidTokenError
from pydantic import BaseModel, Field
from tortoise import fields

from backend.config import ALGORITHM, SECRET_KEY
from backend.controller import article_controller
from backend.models import Article, Collection, UserFavorite, UserLike, UserViewHistory, User
from backend.schemas import ArticleCreate, ArticleUpdate
from backend.security.password_security import oauth2_scheme

article = APIRouter(prefix="/articles", tags=["文章管理接口"])


# TagOut 模型，用于表示标签信息

class TagOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True  # 使其支持从 ORM 对象转换


# ArticleOut 模型，用于表示文章信息
class ArticleOut(BaseModel):
    id: int
    title: str
    subtitle: Optional[str] = None
    author_id: int
    content: str
    image_urls: Optional[List[str]] = None
    view_count: int
    like_count: int
    favorite_count: int
    reward_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    tags: List[TagOut] = None
    has_liked: Optional[bool] = False
    has_favorited: Optional[bool] = False

    class Config:
        from_attributes = True  # 使其支持从 ORM 对象转换


class UserInfo(BaseModel):
    id: int
    name: str
    avatar: str


class Pr_Nx_ArticleOut(BaseModel):
    id: int
    title: str


class ArticleCollectionIn(BaseModel):
    id: int
    name: str
    previous: Optional[Pr_Nx_ArticleOut] = None
    next: Optional[Pr_Nx_ArticleOut] = None


class ArticlePageOut(BaseModel):
    article: ArticleOut
    userInfo: UserInfo
    collection: Optional[ArticleCollectionIn] = None


class ArticleListResponse(BaseModel):
    total: int
    items: List[ArticleOut]


class ArticleHistoryRecordIn(BaseModel):
    articleId: int = Field(..., ge=1)
    duration: Optional[int] = Field(default=None, ge=0)


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


def _build_user_info(user: Optional[User]) -> UserInfo:
    if not user:
        return UserInfo(id=0, name="", avatar="")
    return UserInfo(
        id=user.id,
        name=user.username or "",
        avatar=user.avatar_url or "",
    )


@article.get("/page/{page}")
async def list_articles(page: int):
    total, articles = await article_controller.list_items(page, 10)
    items = [await ArticleOut.from_tortoise_orm(article) for article in articles]
    return ArticleListResponse(total=total, items=items)


@article.get(
    "/favorites",
    response_model=List[ArticleOut],
    summary="分页查询当前用户收藏",
)
async def list_favorite_articles(
        token: Annotated[str, Depends(oauth2_scheme)],
        page: int = Query(1, ge=1),
) -> List[ArticleOut]:
    user_id = _extract_user_id_from_token(token)
    page_size = 100
    offset = (page - 1) * page_size
    favorites = await (
        UserFavorite.filter(user_id=user_id)
            .order_by("-favorited_at")
            .offset(offset)
            .limit(page_size)
            .prefetch_related("article__tags")
    )
    articles: List[ArticleOut] = []
    for favorite in favorites:
        article_obj = getattr(favorite, "article", None)
        if not article_obj:
            continue
        article_obj.content = article_obj.content[:100]
        article_obj.has_favorited = True
        article_obj.image_urls=_parse_image_url(article_obj)
        articles.append(article_obj)
    return articles


@article.get(
    "/likes",
    response_model=List[ArticleOut],
    summary="分页查询当前用户点赞",
)
async def list_liked_articles(
    token: Annotated[str, Depends(oauth2_scheme)],
    page: int = Query(1, ge=1),
) -> List[ArticleOut]:
    user_id = _extract_user_id_from_token(token)
    page_size = 15
    offset = (page - 1) * page_size
    likes = await (
        UserLike.filter(user_id=user_id)
        .order_by("-liked_at")
        .offset(offset)
        .limit(page_size)
        .prefetch_related("article__tags")
    )
    article_ids = {like.article_id for like in likes if getattr(like, "article_id", None)}
    favorited_ids: set[int] = set()
    if article_ids:
        favorited_ids = set(
            await UserFavorite.filter(
                user_id=user_id,
                article_id__in=list(article_ids),
            ).values_list("article_id", flat=True)
        )
    articles: List[ArticleOut] = []
    for like in likes:
        article_obj = getattr(like, "article", None)
        if not article_obj:
            continue
        article_obj.content = article_obj.content[:100]
        article_obj.has_liked = True
        article_obj.has_favorited = article_obj.id in favorited_ids
        article_obj.image_urls=_parse_image_url(article_obj)
        articles.append(article_obj)
    return articles


@article.post("/favorite/{article_id}")
async def delete_or_add_favorite_article(token: Annotated[str, Depends(oauth2_scheme)], article_id: int):
    try:
        user_id = _extract_user_id_from_token(token)
        favorite_exist = await UserFavorite.filter(user_id=user_id, article_id=article_id).exists()
        if favorite_exist:
            await UserFavorite.filter(user_id=user_id, article_id=article_id).delete()
            message="删除成功"
        else:
            await UserFavorite.create(user_id=user_id, article_id=article_id)
            message="添加成功"
        return {"message": message}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="收藏操作失败",
        )


@article.post("/like/{article_id}")
async def delete_or_add_like_article(
    token: Annotated[str, Depends(oauth2_scheme)],
    article_id: int,
):
    try:
        user_id = _extract_user_id_from_token(token)
        like_exist = await UserLike.filter(user_id=user_id, article_id=article_id).exists()
        if like_exist:
            await UserLike.filter(user_id=user_id, article_id=article_id).delete()
            message = "取消点赞成功"
        else:
            await UserLike.create(user_id=user_id, article_id=article_id)
            message = "点赞成功"
        return {"message": message}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="点赞操作失败",
        )


@article.get(
    "/history",
    response_model=List[ArticleOut],
    summary="分页查询用户浏览历史",
)
async def list_view_history(
        token: Annotated[str, Depends(oauth2_scheme)],
        page: int = Query(1, ge=1),
) -> List[ArticleOut]:
    user_id = _extract_user_id_from_token(token)
    page_size = 15
    offset = (page - 1) * page_size
    histories = await (
        UserViewHistory.filter(user_id=user_id)
            .order_by("-viewed_at")
            .offset(offset)
            .limit(page_size)
            .prefetch_related("article__tags")
    )
    articles: List[ArticleOut] = []
    for history in histories:
        article_obj = getattr(history, "article", None)
        if not article_obj:
            continue
        articles.append(await ArticleOut.from_tortoise_orm(article_obj))
    return articles


@article.post(
    "/history",
    response_model=ArticleOut,
    status_code=status.HTTP_201_CREATED,
    summary="记录用户浏览历史",
)
async def create_view_history(
        payload: ArticleHistoryRecordIn,
        token: Annotated[str, Depends(oauth2_scheme)],
) -> ArticleOut:
    user_id = _extract_user_id_from_token(token)
    article_obj = await Article.filter(id=payload.articleId).prefetch_related("tags").first()
    if not article_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在",
        )
    duration_value = payload.duration if payload.duration is not None else 0
    existing = await UserViewHistory.filter(
        user_id=user_id,
        article_id=payload.articleId,
    ).first()
    if existing:
        await existing.delete()
    await UserViewHistory.create(
        user_id=user_id,
        article_id=payload.articleId,
        duration=duration_value,
    )
    return await ArticleOut.from_tortoise_orm(article_obj)


@article.get("/recommendations", response_model=List[ArticleOut])
async def get_recommended_articles(token: Annotated[str, Depends(oauth2_scheme)],
                                   limit: int = Query(default=15, ge=1, le=50, description="返回的推荐文章数量"),
                                   ):
    user_id = _extract_user_id_from_token(token)
    query = (
        Article.filter(status="published")
            .order_by("-view_count", "-like_count", "-favorite_count", "-reward_amount")
            .limit(limit)
    )
    articles = await query.prefetch_related("tags")
    await UserLike.filter()
    serialized_articles: List[ArticleOut] = []
    favorited_list = await UserFavorite.filter(user_id=user_id).all().values_list("article_id", flat=True)
    for article_obj in articles:
        if article_obj.content:
            article_obj.content = article_obj.content[:100]
        favorited = article_obj.id in favorited_list
        article_obj.has_favorited = favorited
        article_obj.image_urls=_parse_image_url(article_obj)
        serialized_articles.append(article_obj)
    return serialized_articles


def _resolve_time_range(
        range_type: str, year: int, month: Optional[int], day: Optional[int]
) -> Tuple[datetime, datetime]:
    normalized = range_type.lower()
    if normalized == "year":
        start = datetime(year, 1, 1)
        end = datetime(year + 1, 1, 1)
        return start, end
    if normalized == "month":
        if month is None:
            raise ValueError("month参数在month查询类型时必填")
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        return start, end
    if normalized == "week":
        if month is None or day is None:
            raise ValueError("week查询类型需要提供month和day参数")
        target_date = datetime(year, month, day)
        week_start = target_date - timedelta(days=target_date.weekday())
        start = datetime(week_start.year, week_start.month, week_start.day)
        end = start + timedelta(days=7)
        return start, end
    raise ValueError("range_type参数仅支持year、month或week")


@article.get("/get-filter-articles", response_model=ArticleListResponse)
async def get_filtered_articles(
        token: Annotated[str, Depends(oauth2_scheme)],
        range_type: Optional[str] = Query(None, description="统计周期 year、month 或 week"),
        year: Optional[int] = Query(None, ge=1900, description="查询年份"),
        month: Optional[int] = Query(None, ge=1, le=12, description="查询月份"),
        day: Optional[int] = Query(None, ge=1, le=31, description="查询日（week类型需要）"),
        tags: Optional[str] = Query(
            None, description="标签ID，多个以逗号分割，例如 1,2,3"
        ),
        page: int = Query(1, ge=1),
):
    user_id = _extract_user_id_from_token(token)
    query = Article.filter(status="published")

    if range_type:
        if year is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当指定range_type时必须提供year参数",
            )
        try:
            start_dt, end_dt = _resolve_time_range(range_type, year, month, day)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        query = query.filter(
            published_at__gte=start_dt,
            published_at__lt=end_dt,
        )

    tag_ids: List[int] = []
    if tags:
        try:
            tag_ids = [int(tag.strip()) for tag in tags.split(",") if tag.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tags参数必须是逗号分隔的整数",
            )
        if tag_ids:
            query = query.filter(tags__id__in=tag_ids).distinct()

    page_size = 10
    offset = (page - 1) * page_size

    records = await (
        query.order_by(
            "-view_count",
            "-like_count",
            "-favorite_count",
            "-reward_amount",
        )
            .offset(offset)
            .limit(page_size)
            .prefetch_related("tags")
    )

    # 获取用户收藏的id
    favorited_ids = await UserFavorite.filter(user_id=user_id).values_list("article_id", flat=True)
    items: List[ArticleOut] = []
    for article_obj in records:
        if article_obj.content:
            article_obj.content = article_obj.content[:100]
        article_obj.has_favorited = article_obj.id in favorited_ids
        items.append(article_obj)
    count = len(items)
    return ArticleListResponse(total=count, items=items)


@article.get("/from_tag_get", response_model=List[ArticleOut])
async def list_articles(tag_id: str = Query(default=None)):
    if not tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tag_id参数必填",
        )
    try:
        tag_ids = [int(value.strip()) for value in tag_id.split(",") if value.strip()]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tag_id必须是整数，多个值请用逗号分隔",
        )
    if not tag_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请至少提供一个tag_id",
        )

    query = Article.filter(tags__id__in=tag_ids)
    articles = await query.prefetch_related("tags")

    # 确保获取实际的 tags 数据
    return [article for article in articles]


@article.post("", response_model=ArticleOut)
async def create_article(
        article_in: ArticleCreate,
        token: Annotated[str, Depends(oauth2_scheme)],
):
    user_id = _extract_user_id_from_token(token)
    try:
        article_obj = await article_controller.create(article_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if article_in.collection:
        collection_data = article_in.collection.model_dump(exclude_none=True)
        name_value = collection_data.get("name")
        existing = (
            await Collection.filter(author_id=user_id, name=name_value or "")
                .first()
            if name_value
            else None
        )
        if existing:
            article_obj.collection_id = existing.id
        else:
            new_collection = await Collection.create(
                author_id=user_id,
                name=name_value or "",
                description=collection_data.get("description"),
                image_url=collection_data.get("image_url"),
            )
            article_obj.collection_id = new_collection.id
        await article_obj.save()
    return article_obj


def _parse_image_url(article_obj:dict):
    images = []
    if hasattr(article_obj, 'image_urls') and article_obj.image_urls:
        for image_url in article_obj.image_urls:
            if not image_url.startswith("http"):
                if image_url.endswith(".png") or image_url.endswith(".jpg") or image_url.endswith(".jpeg"):
                    images.append(APP_BASE_URL + '/static/upload_IMG/' + image_url)
                else:
                    images.append(APP_BASE_URL + '/static/upload_Video/' + image_url)
    return images

# 查询整个文章的接口
@article.get(
    "/{article_id}/with-status",
    response_model=ArticlePageOut,
    summary="根据文章ID查询（包含点赞/收藏状态）",
)
async def get_article_with_status(
        article_id: int,
        token: Annotated[str, Depends(oauth2_scheme)],
) -> ArticlePageOut:
    user_id = _extract_user_id_from_token(token)
    article_obj = (
        await Article.filter(id=article_id)
            .prefetch_related("tags")
            .prefetch_related("collection")
            .prefetch_related("author")
            .first()
    )
    if not article_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在",
        )
    liked = await UserLike.filter(user_id=user_id, article_id=article_id).exists()
    favorited = await UserFavorite.filter(user_id=user_id, article_id=article_id).exists()

    # 处理标签数据
    tags_data = []
    if hasattr(article_obj, 'tags'):
        # 预加载的标签已经可以直接访问
        async for tag in article_obj.tags:
            tags_data.append(TagOut.from_orm(tag))

    # 构建 ArticleOut 实例
    images = []
    if hasattr(article_obj, 'image_urls') and article_obj.image_urls:
        for image_url in article_obj.image_urls:
            if not image_url.startswith("http"):
                if image_url.endswith(".png") or image_url.endswith(".jpg") or image_url.endswith(".jpeg"):
                    images.append(APP_BASE_URL + '/static/upload_IMG/' + image_url)
                else:
                    images.append(APP_BASE_URL + '/static/upload_Video/' + image_url)

    article_out = ArticleOut(
        id=article_obj.id,
        title=article_obj.title,
        subtitle=article_obj.subtitle,
        author_id=article_obj.author_id,
        content=article_obj.content,
        image_urls=images,
        view_count=article_obj.view_count,
        like_count=article_obj.like_count,
        favorite_count=article_obj.favorite_count,
        reward_amount=article_obj.reward_amount,
        status=article_obj.status,
        created_at=article_obj.created_at,
        updated_at=article_obj.updated_at,
        published_at=article_obj.published_at,
        tags=tags_data,
        has_liked=liked,
        has_favorited=favorited
    )

    # 获取作者信息
    author = getattr(article_obj, "author", None)
    if author:
        author_info = UserInfo(
            id=author.id,
            name=author.username,
            avatar=author.avatar_url,
        )
    else:
        author_info = UserInfo(id=0, name="", avatar="")

    collection_payload = None
    if article_obj.collection_id:
        collection_obj = await article_obj.collection
        previous_article = await (
            Article.filter(collection_id=collection_obj.id, id__lt=article_obj.id)
                .order_by("-id")
                .first()
        )
        next_article = await (
            Article.filter(collection_id=collection_obj.id, id__gt=article_obj.id)
                .order_by("id")
                .first()
        )
        previous = Pr_Nx_ArticleOut(id=previous_article.id, title=previous_article.title) if previous_article else None
        next = Pr_Nx_ArticleOut(id=next_article.id, title=next_article.title) if next_article else None
        collection_payload = ArticleCollectionIn(
            id=collection_obj.id,
            name=collection_obj.name,
            previous=previous,
            next=next
        )

    return ArticlePageOut(
        article=article_out,
        userInfo=author_info,
        collection=collection_payload
    )


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
