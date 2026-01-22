from datetime import datetime
from typing import Any, Dict, List, Optional

from tortoise.expressions import Q

from backend.models import Good, GoodChoice, GoodComment, GoodCommentLike
from backend.schemas.shop import (
    GoodChoiceCreate,
    GoodChoiceUpdate,
    GoodCommentCreate,
    GoodCommentLikeCreate,
    GoodCommentLikeUpdate,
    GoodCommentUpdate,
    GoodCreate,
    GoodUpdate,
)

from .base import ApiController


class GoodController(ApiController[Good, GoodCreate, GoodUpdate]):
    def __init__(self) -> None:
        super().__init__(Good)

    async def get_item(self, id: int) -> Good:
        good = await super().get_item(id)
        await good.fetch_related("choices", "comments", "publisher")
        return good

    async def list_items(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        order: Optional[List[str]] = None,
    ):
        total, records = await super().list_items(page, page_size, search, order)
        for good in records:
            await good.fetch_related("choices", "publisher")
        return total, records


class GoodChoiceController(
    ApiController[GoodChoice, GoodChoiceCreate, GoodChoiceUpdate]
):
    def __init__(self) -> None:
        super().__init__(GoodChoice)


class GoodCommentController(
    ApiController[GoodComment, GoodCommentCreate, GoodCommentUpdate]
):
    def __init__(self) -> None:
        super().__init__(GoodComment)

    async def update(
        self,
        id: int,
        obj_in: GoodCommentUpdate | Dict[str, Any],
    ) -> GoodComment:
        if isinstance(obj_in, dict):
            data = obj_in
        else:
            data = obj_in.model_dump(exclude_unset=True)
        if "is_deleted" in data:
            if data["is_deleted"]:
                data.setdefault("deleted_at", datetime.utcnow())
            else:
                data["deleted_at"] = None
        return await super().update(id=id, obj_in=data)


class GoodCommentLikeController(
    ApiController[GoodCommentLike, GoodCommentLikeCreate, GoodCommentLikeUpdate]
):
    def __init__(self) -> None:
        super().__init__(GoodCommentLike)

    async def create(
        self,
        obj_in: GoodCommentLikeCreate | Dict[str, Any],
    ) -> GoodCommentLike:
        like = await super().create(obj_in)
        await self._refresh_comment_like_count(like.comment_id)
        return like

    async def update(
        self,
        id: int,
        obj_in: GoodCommentLikeUpdate | Dict[str, Any],
    ) -> GoodCommentLike:
        existing = await self.get(id=id)
        old_comment_id = existing.comment_id
        like = await super().update(id=id, obj_in=obj_in)
        if like.comment_id != old_comment_id:
            await self._refresh_comment_like_count(old_comment_id)
        await self._refresh_comment_like_count(like.comment_id)
        return like

    async def remove(self, id: int) -> None:
        like = await self.get(id=id)
        comment_id = like.comment_id
        await super().remove(id)
        await self._refresh_comment_like_count(comment_id)

    @staticmethod
    async def _refresh_comment_like_count(comment_id: int) -> None:
        total = await GoodCommentLike.filter(comment_id=comment_id).count()
        await GoodComment.filter(id=comment_id).update(like_count=total)


good_controller = GoodController()
good_choice_controller = GoodChoiceController()
good_comment_controller = GoodCommentController()
good_comment_like_controller = GoodCommentLikeController()
