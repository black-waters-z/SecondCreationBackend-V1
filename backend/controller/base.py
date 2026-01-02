from typing import Any, Dict, List, Tuple

from tortoise.expressions import Q

from backend.core.crud import (
    CRUDBase,
    CreateSchemaType,
    ModelType,
    Total,
    UpdateSchemaType,
)


class ApiController(CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Common wrapper around CRUDBase that exposes stable helper names
    used by the FastAPI endpoints.
    """

    async def get_item(self, id: int) -> ModelType:
        return await super().get(id)

    async def list_items(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        order: List[str] | None = None,
    ) -> Tuple[Total, List[ModelType]]:
        order = order or []
        return await super().list(
            page=page,
            page_size=page_size,
            search=search,
            order=order,
        )

    async def create_item(self, obj_in: CreateSchemaType | Dict[str, Any]) -> ModelType:
        return await self.create(obj_in)

    async def update_item(
        self,
        id: int,
        obj_in: UpdateSchemaType | Dict[str, Any],
    ) -> ModelType:
        return await self.update(id=id, obj_in=obj_in)

    async def delete_item(self, id: int) -> None:
        await self.remove(id)
