from typing import Any, Dict

from backend.models import Tag, TagRelation
from backend.models.mysql import TagType
from backend.schemas.tag import (
    TagCreate,
    TagRelationCreate,
    TagRelationUpdate,
    TagUpdate,
)

from .base import ApiController


class TagController(ApiController[Tag, TagCreate, TagUpdate]):
    def __init__(self) -> None:
        super().__init__(Tag)


class TagRelationController(
    ApiController[TagRelation, TagRelationCreate, TagRelationUpdate]
):
    def __init__(self) -> None:
        super().__init__(TagRelation)

    async def list_relations(
            self,
            other_tag_id: int | None = None,
    ):
        tag_relations = await TagRelation.filter(character_tag=other_tag_id).select_related("work_tag",
                                                                                            "character_tag").all()
        other_tag = await Tag.get(id=other_tag_id)
        work_tags = []
        if tag_relations:
            for relation in tag_relations:
                work_tags.append(relation.work_tag)

        return {"work_tags": work_tags, "other_tag": other_tag}

    async def create_item(
            self, obj_in: TagRelationCreate | Dict[str, Any]
    ) -> TagRelation:
        payload = await self._normalize_payload(obj_in, partial=False)
        return await super().create_item(payload)

    async def update_item(
            self,
            id: int,
            obj_in: TagRelationUpdate | Dict[str, Any],
    ) -> TagRelation:
        payload = await self._normalize_payload(obj_in, partial=True)
        return await super().update_item(id, payload)

    async def _normalize_payload(
            self,
            obj_in: TagRelationCreate | TagRelationUpdate | Dict[str, Any],
            *,
            partial: bool,
    ) -> Dict[str, Any]:
        if isinstance(obj_in, dict):
            payload = obj_in
        else:
            payload = obj_in.model_dump(
                exclude_none=True, exclude_unset=partial
            )

        if not partial:
            if "work_tag_id" not in payload or "character_tag_id" not in payload:
                raise ValueError("work_tag_id 和 character_tag_id 为必填字段")

        if "work_tag_id" in payload:
            work_tag = await Tag.get(id=payload["work_tag_id"])
            if work_tag.type != TagType.WORK:
                raise ValueError("work_tag_id 必须指向作品类型标签")

        if "character_tag_id" in payload:
            character_tag = await Tag.get(id=payload["character_tag_id"])
            if character_tag.type != TagType.CHARACTER:
                raise ValueError("character_tag_id 必须指向角色类型标签")

        return payload


tag_controller = TagController()
tag_relation_controller = TagRelationController()
