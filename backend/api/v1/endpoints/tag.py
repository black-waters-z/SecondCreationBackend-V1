from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from backend.controller import tag_controller, tag_relation_controller
from backend.models import Tag, TagRelation
from backend.schemas import (
    TagCreate,
    TagRelationCreate,
    TagRelationUpdate,
    TagType,
    TagUpdate,
)

tag = APIRouter(prefix="/tags")
tag_relation = APIRouter(prefix="/tag-relations")
TagOut = pydantic_model_creator(Tag, name="TagOut")
TagRelationOut = pydantic_model_creator(TagRelation, name="TagRelationOut")


class TagListResponse(BaseModel):
    total: int
    items: List[TagOut]


class TagRelationListResponse(BaseModel):
    total: int
    items: List[TagRelationOut]


@tag.get("/", response_model=TagListResponse)
async def list_tags(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tag_type: Optional[TagType] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
):
    search = Q()
    if tag_type:
        search &= Q(type=tag_type)
    if keyword:
        search &= Q(name__icontains=keyword)

    total, records = await tag_controller.list_items(
        page=page, page_size=page_size, search=search, order=["-created_at"]
    )
    items = [await TagOut.from_tortoise_orm(obj) for obj in records]
    return TagListResponse(total=total, items=items)


@tag.post("/", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(tag_in: TagCreate):
    created = await tag_controller.create_item(tag_in)
    return await TagOut.from_tortoise_orm(created)


@tag.get("/{tag_id}", response_model=TagOut)
async def get_tag(tag_id: int):
    try:
        record = await tag_controller.get_item(tag_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return await TagOut.from_tortoise_orm(record)


@tag.put("/{tag_id}", response_model=TagOut)
async def update_tag(tag_id: int, tag_in: TagUpdate):
    try:
        updated = await tag_controller.update_item(tag_id, tag_in)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return await TagOut.from_tortoise_orm(updated)


@tag.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int):
    try:
        await tag_controller.delete_item(tag_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")


@tag_relation.get("/", response_model=TagRelationListResponse)
async def list_tag_relations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    work_tag_id: Optional[int] = Query(default=None),
    character_tag_id: Optional[int] = Query(default=None),
):
    search = Q()
    if work_tag_id:
        search &= Q(work_tag_id=work_tag_id)
    if character_tag_id:
        search &= Q(character_tag_id=character_tag_id)

    total, records = await tag_relation_controller.list_items(
        page=page, page_size=page_size, search=search, order=["-created_at"]
    )
    items = [await TagRelationOut.from_tortoise_orm(obj) for obj in records]
    return TagRelationListResponse(total=total, items=items)


@tag_relation.post("/", response_model=TagRelationOut, status_code=status.HTTP_201_CREATED)
async def create_tag_relation(relation_in: TagRelationCreate):
    try:
        created = await tag_relation_controller.create_item(relation_in)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关联的标签不存在")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return await TagRelationOut.from_tortoise_orm(created)


@tag_relation.get("/{relation_id}", response_model=TagRelationOut)
async def get_tag_relation(relation_id: int):
    try:
        record = await tag_relation_controller.get_item(relation_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签关联不存在")
    return await TagRelationOut.from_tortoise_orm(record)


@tag_relation.put("/{relation_id}", response_model=TagRelationOut)
async def update_tag_relation(relation_id: int, relation_in: TagRelationUpdate):
    try:
        updated = await tag_relation_controller.update_item(relation_id, relation_in)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签关联不存在")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return await TagRelationOut.from_tortoise_orm(updated)


@tag_relation.delete("/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_relation(relation_id: int):
    try:
        await tag_relation_controller.delete_item(relation_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签关联不存在")


# @tag.post("/test")
# async def test():
#     test=await TestModel.create(id=1)
#     aa=await AA.get(id=1)
#     await test.name_id.add(aa)