from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class UserViewHistoryCreate(BaseModel):
    user_id: int
    article_id: int
    duration: Optional[int] = 0


class UserViewHistoryUpdate(BaseModel):
    duration: Optional[int] = None


class UserFavoriteCreate(BaseModel):
    user_id: int
    article_id: int


class UserFavoriteUpdate(BaseModel):
    user_id: Optional[int] = None
    article_id: Optional[int] = None


class UserLikeCreate(BaseModel):
    user_id: int
    article_id: int


class UserLikeUpdate(BaseModel):
    user_id: Optional[int] = None
    article_id: Optional[int] = None


class RewardCreate(BaseModel):
    user_id: int
    article_id: int
    amount: Decimal
    message: Optional[str] = None
    status: Optional[str] = "completed"


class RewardUpdate(BaseModel):
    amount: Optional[Decimal] = None
    message: Optional[str] = None
    status: Optional[str] = None


class UserInterestCreate(BaseModel):
    user_id: int
    tag_id: int
    interest_score: Optional[float] = 0.0


class UserInterestUpdate(BaseModel):
    interest_score: Optional[float] = None
