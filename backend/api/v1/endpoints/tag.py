from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from backend.models import RoleTag, WorkName
from backend.controller import role_tag_controller
from backend.schemas import RoleTagCreate, RoleTagUpdate

role_tag = APIRouter(prefix="/tag/roletag", tags=["RoleTag"])

RoleTagOut = pydantic_model_creator(RoleTag, name="RoleTagOut")


class RoleTagListResponse(BaseModel):
    total: int
    items: List[RoleTagOut]


@role_tag.get("/", response_model=RoleTagListResponse)
async def list_role_tags(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    key_word: str = None
):
    search = Q()
    if key_word:
        search = Q(name__icontains=key_word)
    total, records = await role_tag_controller.list_items(
        page=page, page_size=page_size,search=search, order=["-created_at"]
    )
    items = [await RoleTagOut.from_tortoise_orm(obj) for obj in records]
    return RoleTagListResponse(total=total, items=items)


@role_tag.post("/", response_model=RoleTagOut, status_code=status.HTTP_201_CREATED)
async def create_role_tag(tag_in: RoleTagCreate):
    work_title = tag_in.work_name_title.strip()
    if not work_title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Work name is required")
    work_name, _ = await WorkName.get_or_create(workName=work_title)
    payload = tag_in.model_dump(exclude={"work_name_title"})
    payload["work_name_id"] = work_name.id
    created = await role_tag_controller.create_item(payload)
    return await RoleTagOut.from_tortoise_orm(created)


@role_tag.get("/{tag_id}", response_model=RoleTagOut)
async def get_role_tag(tag_id: int):
    try:
        record = await role_tag_controller.get_item(tag_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role tag not found")
    return await RoleTagOut.from_tortoise_orm(record)


@role_tag.put("/{tag_id}", response_model=RoleTagOut)
async def update_role_tag(tag_id: int, tag_in: RoleTagUpdate):
    update_data = tag_in.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one field to update"
        )
    work_title = update_data.pop("work_name_title", None)
    if work_title is not None:
        stripped = work_title.strip()
        if not stripped:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Work name cannot be empty"
            )
        work_name, _ = await WorkName.get_or_create(title=stripped)
        update_data["work_name_id"] = work_name.id
    try:
        updated = await role_tag_controller.update_item(tag_id, update_data)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role tag not found")
    return await RoleTagOut.from_tortoise_orm(updated)


@role_tag.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_tag(tag_id: int):
    try:
        await role_tag_controller.delete_item(tag_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role tag not found")
