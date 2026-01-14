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
    ArticleCreate
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
        all: bool = Query(default=False, description="是否返回所有标签"),
):
    search = Q()
    filter_kwargs = {}
    if tag_type:
        search &= Q(type=tag_type)
        filter_kwargs["type"] = tag_type
    if keyword:
        search &= Q(name__icontains=keyword)
        filter_kwargs["name__icontains"] = keyword

    if all:
        query = Tag.filter(**filter_kwargs) if filter_kwargs else Tag.all()
        records = await query.order_by("-created_at")
        total = len(records)
    else:
        total, records = await tag_controller.list_items(
            page=page, page_size=page_size, search=search, order=["-created_at"]
        )
    items = [await TagOut.from_tortoise_orm(obj) for obj in records]
    return TagListResponse(total=total, items=items)


@tag.post("/", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(tag_in: TagCreate):
    created = await tag_controller.create_item(tag_in)
    return await TagOut.from_tortoise_orm(created)


class TagsIn(BaseModel):
    workTags: List[str] = None
    characterTags: List[str] = None
    crossTags: List[str] = None


# 返回处理好后的文章tag_ids,呃，这个之后再说吧，可能会有更好的处理方案，
# 也许可以做个依赖直接插入呢，这样子只需要一个接口就可以完成。
@tag.post("/articleTags", status_code=status.HTTP_201_CREATED)
async def create_article_tags(tag_in: TagsIn):
    tag_objects = []

    # 获取已存在的标签
    existing_tags = await Tag.all().values('name', 'type')  # 获取数据库中所有标签的name和type字段
    existing_tags_set = {(tag['name'], tag['type']) for tag in existing_tags}

    if tag_in.workTags:
        for tag in tag_in.workTags:
            if (tag, 'work') not in existing_tags_set:  # 检查是否已存在该标签
                tag_objects.append(Tag(name=tag, type='work'))

    if tag_in.characterTags:
        for tag in tag_in.characterTags:
            if (tag, 'character') not in existing_tags_set:
                tag_objects.append(Tag(name=tag, type='character'))

    if tag_in.crossTags:
        for tag in tag_in.crossTags:
            if (tag, 'cross') not in existing_tags_set:
                tag_objects.append(Tag(name=tag, type='cross'))

    # 批量插入新的标签
    await Tag.bulk_create(tag_objects)

    work_tags = await Tag.filter(type='work', name__in=tag_in.workTags).all()
    character_tags = await Tag.filter(type='character', name__in=tag_in.characterTags).all()
    cross_tags = await Tag.filter(type='cross', name__in=tag_in.crossTags).all()

    tag_relations = []
    existing_tags_relations = await TagRelation.all().values('work_tag_id',
                                                             'character_tag_id')  # 获取数据库中所有标签的name和type字段
    existing_tags_relations_set = {(relation['work_tag_id'], relation['character_tag_id']) for relation in
                                   existing_tags_relations}

    for work_tag in work_tags:
        for character_tag in character_tags:
            if (work_tag.id, character_tag.id) not in existing_tags_relations_set:
                tag_relations.append(TagRelation(work_tag=work_tag, character_tag=character_tag))

        for cross_tag in cross_tags:
            if (work_tag.id, cross_tag.id) not in existing_tags_relations_set:
                tag_relations.append(TagRelation(work_tag=work_tag, character_tag=cross_tag))

    await TagRelation.bulk_create(tag_relations)
    return {"message": "Tags successfully created",
            "tag_ids": [tag.id for tag in [*work_tags, *character_tags, *cross_tags]]
            }


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


@tag_relation.get("/get_work_tags", status_code=status.HTTP_200_OK)
async def list_tag_relations(other_tag_id: int | None = None):
    return await tag_relation_controller.list_relations(other_tag_id=other_tag_id)


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
