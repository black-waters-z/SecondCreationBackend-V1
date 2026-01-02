from typing import Optional

from pydantic import BaseModel


class RoleTagCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#000000"
    work_name_title: str


class RoleTagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    work_name_title: Optional[str] = None


class CrossRoleTagCreate(BaseModel):
    role_a_id: int
    role_b_id: int
    name: str
    description: Optional[str] = None
    weight: Optional[float] = 1.0


class CrossRoleTagUpdate(BaseModel):
    role_a_id: Optional[int] = None
    role_b_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    weight: Optional[float] = None


class ArticleTagCreate(BaseModel):
    article_id: int
    tag_id: int


class ArticleTagUpdate(BaseModel):
    article_id: Optional[int] = None
    tag_id: Optional[int] = None
