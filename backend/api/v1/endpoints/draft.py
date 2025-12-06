import random
from fastapi import APIRouter, HTTPException, status, Depends
from backend.models import Article, Zone, Favorites, Draft
from backend.schemas import Draft_Pydantic, DraftIn_Pydantic
from datetime import datetime, timedelta
from backend.security import get_current_user
from pydantic import BaseModel, ConfigDict

draft = APIRouter(prefix="/draft", dependencies=[Depends(get_current_user)])


class Drafts(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime


@draft.get("")
async def get_draft(draft_id: int, user: dict = Depends(get_current_user)):
    try:
        result = await Draft.get(id=draft_id, poster_id=user.get("id"))
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="获取草稿失败")


@draft.get("/all_drafts")
async def get_drafts(user: dict = Depends(get_current_user)):
    try:
        result = await Draft.filter(poster_id=user.get("id")).all()
        drafts_list = [Drafts.model_validate(draft) for draft in result]
        return drafts_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="获取草稿箱失败")


@draft.post("")
async def post_draft(content: DraftIn_Pydantic, zone_name: str, poster=Depends(get_current_user)):
    try:
        # 这个是增加草稿
        draft_content = await Draft.create(**content.dict(exclude_unset=True), poster_id=poster.get("id"))
        choose_zone = await Zone.get(name=zone_name)
        await draft_content.zones.add(choose_zone)
        return await Draft_Pydantic.from_tortoise_orm(draft_content)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发布失败！请登录重试。")


# 更新草稿图片
@draft.put("/images")
async def put_draft_images(images: dict, draft_id: int):
    result = await Draft.get(id=draft_id)
    result.images = images
    await result.save()
    return {"msg": "更新图片成功"}


@draft.put("")
async def put_draft(draft_content: DraftIn_Pydantic, draft_id: int, zone_name: str,
                    user: dict = Depends(get_current_user)):
    result = await Draft.get(id=draft_id, poster_id=user.get("id"))
    await result.zones.clear()
    await result.delete()
    await Draft.create(id=draft_id, **draft_content.dict(), poster_id=user.get("id"))
    choose_zone = await Zone.get(name=zone_name)
    await result.zones.add(choose_zone)
    return {
        "msg": "草稿更新成功"
    }


@draft.delete("")
async def delete_draft(draft_id: int, user: dict = Depends(get_current_user)):
    result = await Draft.get(id=draft_id, poster_id=user.get("id"))
    await result.zones.clear()
    await result.delete()
    return {
        "msg": "草稿删除成功"
    }
