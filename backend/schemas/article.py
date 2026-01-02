from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class ArticleCreate(BaseModel):
    title: str
    author_id: int
    content: str
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = "published"
    published_at: Optional[datetime] = None
    tag_ids: Optional[List[int]] = None


class ArticleShow(BaseModel):
    id: int = None
    title: str
    author_id: int
    content: str
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = "published"
    published_at: Optional[datetime] = None
    tag_ids: Optional[List[int]] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[int] = None
    content: Optional[str] = None
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    reward_amount: Optional[Decimal] = None
    published_at: Optional[datetime] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    favorite_count: Optional[int] = None
    tag_ids: Optional[List[int]] = None


class ArticleRewardRankingCreate(BaseModel):
    article_id: int
    user_id: int
    total_amount: Optional[Decimal] = Decimal("0.00")
    reward_count: Optional[int] = 0
    last_rewarded_at: Optional[datetime] = None


class ArticleRewardRankingUpdate(BaseModel):
    total_amount: Optional[Decimal] = None
    reward_count: Optional[int] = None
    last_rewarded_at: Optional[datetime] = None


class ArticleRecommendationCreate(BaseModel):
    user_id: int
    article_id: int
    score: Optional[float] = 0.0
    is_clicked: Optional[bool] = False
    clicked_at: Optional[datetime] = None


class ArticleRecommendationUpdate(BaseModel):
    score: Optional[float] = None
    is_clicked: Optional[bool] = None
    clicked_at: Optional[datetime] = None
