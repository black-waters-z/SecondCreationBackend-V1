from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class GoodBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    good_img: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = True


class GoodCreate(GoodBase):
    publisher_id: Optional[int] = None


class GoodUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    good_img: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None
    publisher_id: Optional[int] = None


class GoodChoiceBase(BaseModel):
    name: str = Field(..., max_length=100)
    price: Decimal = Field(..., ge=0)
    swiper_img: str = Field(..., max_length=255)
    stock: int = Field(default=0, ge=0)
    display_order: Optional[int] = Field(default=0, ge=0)


class GoodChoiceCreate(GoodChoiceBase):
    good_id: int


class GoodChoiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    price: Optional[Decimal] = Field(default=None, ge=0)
    swiper_img: Optional[str] = Field(default=None, max_length=255)
    stock: Optional[int] = Field(default=None, ge=0)
    display_order: Optional[int] = Field(default=None, ge=0)


class GoodCommentCreate(BaseModel):
    good_id: int
    parent_id: Optional[int] = None
    content: str


class GoodCommentUpdate(BaseModel):
    content: Optional[str] = None
    is_deleted: Optional[bool] = None


class GoodCommentLikeCreate(BaseModel):
    comment_id: int
    user_id: int


class GoodCommentLikeUpdate(BaseModel):
    comment_id: Optional[int] = None


class GoodWithChoicesCreate(GoodBase):
    publisher_id: Optional[int] = None
    choices: Optional[List[GoodChoiceBase]] = None
