from typing import Dict, Any
from backend.security.password_security import get_password_hash
from backend.models import User, UserProfile
from backend.schemas.user import (
    UserCreate,
    UserProfileCreate,
    UserProfileUpdate,
    UserUpdate,
)

from backend.core.crud import (
    CreateSchemaType,
)

from .base import ApiController


class UserController(ApiController[User, UserCreate, UserUpdate]):
    def __init__(self) -> None:
        super().__init__(User)

    async def create_item(self,obj_in: CreateSchemaType | Dict[str, Any]):
        obj_in.password_hash = get_password_hash(obj_in.password_hash)
        return await super().create_item(obj_in)


class UserProfileController(
    ApiController[UserProfile, UserProfileCreate, UserProfileUpdate]
):
    def __init__(self) -> None:
        super().__init__(UserProfile)


user_controller = UserController()
user_profile_controller = UserProfileController()
