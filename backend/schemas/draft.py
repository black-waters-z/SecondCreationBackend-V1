from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator
from backend.models import Draft


class DraftCreate(BaseModel):
    title: str
    content: str
    subtitle: Optional[str] = None
    image_urls: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class DraftUpdate(BaseModel):
    title: str
    content: str
    subtitle: Optional[str] = None
    image_urls: Optional[List[str]] = None
    created_at: Optional[datetime] = None


DraftOut = pydantic_model_creator(Draft, name="DraftOut", exclude=("author_id",))
DraftSimpleOut = pydantic_model_creator(Draft, name="DraftSimpleOut",
                                        exclude=("author_id", "content", "subtitle", "image_urls"))
