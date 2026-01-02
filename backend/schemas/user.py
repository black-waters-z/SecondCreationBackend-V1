from datetime import date
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password_hash: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None


class UserProfileCreate(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    location: Optional[str] = None
    website: Optional[str] = None


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    location: Optional[str] = None
    website: Optional[str] = None
