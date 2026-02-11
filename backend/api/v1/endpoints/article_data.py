from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Dict, List, Optional, Tuple
from pypika import functions as fn
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from jwt import InvalidTokenError
from pydantic import BaseModel, Field
from pypika_tortoise.functions import Extract

from tortoise.expressions import F, RawSQL
from tortoise.functions import Count

from backend.config import ALGORITHM, SECRET_KEY
from backend.controller import article_controller
from backend.models import (
    Article,
    Reward,
    UserFavorite,
    UserLike,
    UserViewHistory, ArticleComment,
)
from backend.sc_utils import _parse_image_url
from backend.sc_utils.parse_token import _extract_user_id_from_token
from backend.schemas import ArticleCreate, ArticleUpdate
from backend.security.password_security import oauth2_scheme
from settings import APP_BASE_URL

article_data = APIRouter(prefix="/article_data", tags=["文章数据接口"])


class StatsBucket(BaseModel):
    label: str
    count: int


class ArticleStatsResponse(BaseModel):
    view_count: int
    like_count: int
    favorite_count: int
    reward_amount: Decimal
    daily_likes: List[StatsBucket]
    daily_favorites: List[StatsBucket]
    daily_rewards: List[StatsBucket]
    monthly_likes: List[StatsBucket]
    monthly_favorites: List[StatsBucket]
    monthly_rewards: List[StatsBucket]
    yearly_likes: List[StatsBucket]
    yearly_favorites: List[StatsBucket]
    yearly_rewards: List[StatsBucket]


async def _get_article_comments_data(article_id: int, group_by: str, start_date: datetime, end_date: datetime) -> List[
    StatsBucket]:
    comments = await ArticleComment.filter(
        article_id=article_id,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).annotate(
        date=RawSQL("DATE(created_at)"),  # 提取日期部分（按天分组）
        week=RawSQL("YEARWEEK(created_at, 1)"),
        month=RawSQL("DATE_FORMAT(created_at, '%%Y-%%m')")
    ).group_by(group_by).annotate(count=Count("id")).values("date", "count","week","month")

    return [StatsBucket(label=str(item[group_by]), count=item["count"]) for item in comments]


async def _get_article_likes_data(article_id: int, group_by: str, start_date: datetime, end_date: datetime) -> List[
    StatsBucket]:
    likes = await UserLike.filter(
        article_id=article_id,
        liked_at__gte=start_date,
        liked_at__lte=end_date
    ).annotate(
        date=RawSQL("DATE(liked_at)"),  # 提取日期部分（按天分组）
        week=RawSQL("YEARWEEK(liked_at, 1)"),
        month=RawSQL("DATE_FORMAT(liked_at, '%%Y-%%m')")
    ).group_by(group_by).annotate(count=Count("id")).values("date", "count","week","month")

    return [StatsBucket(label=str(item[group_by]), count=item["count"]) for item in likes]


async def _get_article_favorites_data(article_id: int, group_by: str, start_date: datetime, end_date: datetime) -> List[
    StatsBucket]:
    favorites = await UserFavorite.filter(
        article_id=article_id,
        favorited_at__gte=start_date,
        favorited_at__lte=end_date
    ).annotate(
        date=RawSQL("DATE(favorited_at)"),  # 提取日期部分（按天分组）
        week=RawSQL("YEARWEEK(favorited_at, 1)"),
        month=RawSQL("DATE_FORMAT(favorited_at, '%%Y-%%m')")
    ).group_by(group_by).annotate(count=Count("id")).values("date", "count","week","month")

    return [StatsBucket(label=str(item[group_by]), count=item["count"]) for item in favorites]


search_time = {
    "month": [datetime.utcnow() - timedelta(days=360), datetime.utcnow()],
    "week": [datetime.utcnow() - timedelta(days=30), datetime.utcnow()],
    "date": [datetime.utcnow() - timedelta(days=7), datetime.utcnow()]
}


def _generate_bucket_labels(group_by: str, start_date: datetime, end_date: datetime) -> List[str]:
    labels: List[str] = []
    seen = set()
    current_day = start_date.date()
    end_day = end_date.date()

    while current_day <= end_day:
        if group_by == "date":
            label = current_day.strftime("%Y-%m-%d")
        elif group_by == "week":
            iso_year, iso_week, _ = current_day.isocalendar()
            label = f"{iso_year}{iso_week:02d}"
        else:
            label = current_day.strftime("%Y-%m")

        if label not in seen:
            labels.append(label)
            seen.add(label)

        current_day += timedelta(days=1)

    return labels


def _fill_missing_buckets(data: List[StatsBucket], labels: List[str]) -> List[StatsBucket]:
    buckets = {bucket.label: bucket.count for bucket in data}
    return [StatsBucket(label=label, count=buckets.get(label, 0)) for label in labels]


@article_data.get("/stats_list")
async def get_article_stats_list(page: int = Query(1), size: int = Query(10)):
    total,records = await article_controller.list_items(page, size)
    article_ids= [article.id for article in records]
    results= []
    for article_id in article_ids:
        result = []
        for group_by in ['date','week', 'month']:
            start_time, end_time = search_time[group_by]
            bucket_labels = _generate_bucket_labels(group_by, start_time, end_time)

            comments_group_by_data = await _get_article_comments_data(article_id, group_by,
                                                                      start_time,
                                                                      end_time)
            favorites_group_by_data = await _get_article_favorites_data(article_id, group_by,
                                                                        start_time,
                                                                        end_time)
            likes_group_by_data = await _get_article_likes_data(article_id, group_by,
                                                                start_time,
                                                                end_time)
            result.append({
                group_by: {
                    "like": _fill_missing_buckets(likes_group_by_data, bucket_labels),
                    "favorite": _fill_missing_buckets(favorites_group_by_data, bucket_labels),
                    "comment": _fill_missing_buckets(comments_group_by_data, bucket_labels),
                }
            })
        results.append(result)

    return results


@article_data.post("/{article_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def record_article_view(article_id: int, token: Annotated[str, Depends(oauth2_scheme)]):
    history = await UserViewHistory.filter(user_id=_extract_user_id_from_token(token), article_id=article_id).first()
    if history:
        # 如果已经有浏览记录，更新浏览时间
        history.viewed_at = datetime.utcnow()
        await history.save()
    else:
        await UserViewHistory.create(user_id=_extract_user_id_from_token(token), article_id=article_id,
                                     viewed_at=datetime.utcnow())
