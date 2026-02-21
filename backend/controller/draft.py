from typing import Tuple

from tortoise.expressions import Q

from .base import ApiController
from ..models import Draft
from backend.schemas import DraftCreate, DraftUpdate


class DraftController(ApiController[Draft, DraftCreate, DraftUpdate]):
    def __init__(self) -> None:
        super().__init__(Draft)

    async def list_items(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        user_id: int = None,
    ):
        return await self.model.filter(author_id=user_id).offset((page - 1) * page_size).limit(page_size).order_by("-created_at")


draft_controller = DraftController()