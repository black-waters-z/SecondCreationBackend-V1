from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from tortoise import fields
from backend.controller import article_controller
from backend.models import Article
from backend.schemas import ArticleCreate, ArticleUpdate

article = APIRouter(prefix="/articles", tags=["文章管理接口"])
from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
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
    tags: List[TagOut] =None

    class Config:
        from_attributes = True   # 使其支持从 ORM 对象转换

class ArticleListResponse(BaseModel):
    total: int
    items: List[ArticleOut]


@article.get("/page/{page}")
async def list_articles(page: int):
    total, articles = await article_controller.list_items(page, 10)
    items = [await ArticleOut.from_tortoise_orm(article) for article in articles]
    return ArticleListResponse(total=total, items=items)


@article.get("/recommendations", response_model=List[ArticleOut])
async def get_recommended_articles(
    limit: int = Query(default=15, ge=1, le=50, description="返回的推荐文章数量"),
):
    query = (
        Article.filter(status="published")
        .order_by("-view_count", "-like_count", "-favorite_count", "-reward_amount")
        .limit(limit)
    )
    articles = await query.prefetch_related("tags")
    serialized_articles: List[ArticleOut] = []
    for article_obj in articles:
        if article_obj.content:
            article_obj.content = article_obj.content[:100]
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
    range_type: str = Query(..., description="统计周期 year、month 或 week"),
    year: int = Query(..., ge=1900, description="查询年份"),
    month: Optional[int] = Query(None, ge=1, le=12, description="查询月份"),
    day: Optional[int] = Query(None, ge=1, le=31, description="查询日（week类型需要）"),
    tags: Optional[str] = Query(
        None, description="标签ID，多个以逗号分割，例如 1,2,3"
    ),
    page: int = Query(1, ge=1),
):
    try:
        start_dt, end_dt = _resolve_time_range(range_type, year, month, day)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    query = Article.filter(
        status="published",
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

    total = await query.count()
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

    items: List[ArticleOut] = []
    for article_obj in records:
        if article_obj.content:
            article_obj.content = article_obj.content[:100]
        items.append(await ArticleOut.from_tortoise_orm(article_obj))

    return ArticleListResponse(total=total, items=items)


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


@article.post("",response_model=ArticleOut)
async def create_article(article_in: ArticleCreate):
    try:
        # 这里再查一下tag_id
        article_obj = await article_controller.create(article_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return await article_obj


@article.get("/detail/{article_id}")
async def get_article(article_id: int):
    article_obj = await article_controller.get_item(article_id)
    return await ArticleOut.from_tortoise_orm(article_obj)


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
