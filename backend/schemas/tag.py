from typing import Optional

from pydantic import BaseModel

from backend.models.mysql import TagType


class TagBase(BaseModel):
    name: str
    type: TagType
    description: Optional[str] = None


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[TagType] = None
    description: Optional[str] = None


class TagRelationCreate(BaseModel):
    work_tag_id: int
    character_tag_id: int


class TagRelationUpdate(BaseModel):
    work_tag_id: Optional[int] = None
    character_tag_id: Optional[int] = None
