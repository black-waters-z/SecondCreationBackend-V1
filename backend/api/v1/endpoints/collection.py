from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.models import Collection, User
from backend.security.password_security import oauth2_scheme
from backend.api.v1.endpoints.article import _extract_user_id_from_token

collection = APIRouter(prefix="/collections", tags=["合集接口"])


@collection.post("/{collection_id}/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def subscribe_collection(
    collection_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    user_id = _extract_user_id_from_token(token)
    collection_obj = await Collection.filter(id=collection_id).first()
    if not collection_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合集不存在",
        )
    user=await User.get(id=user_id)
    await collection_obj.subscribers.add(user)
    return {"message": "订阅成功"}


@collection.get("")
async def list_collections():
    # await Collection
    pass