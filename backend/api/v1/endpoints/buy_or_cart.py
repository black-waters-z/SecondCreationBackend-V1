from typing import Annotated, List, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from jwt import InvalidTokenError
from pydantic import BaseModel, Field

from backend.config import ALGORITHM, SECRET_KEY
from backend.controller import cart_controller
from backend.models import Cart, GoodChoice
from backend.security.password_security import oauth2_scheme


class ChoiceOut(BaseModel):
    id: int
    choiceName: str
    price: int
    buyNum: int
    choiceImg: str


class CartGoodChoice(BaseModel):
    id: int
    goodName: str
    choice: ChoiceOut


class CartGoodChoicesOut(BaseModel):
    id: int
    items: List[CartGoodChoice]


class CartAddChoice(BaseModel):
    """
    interface cartAddChoice {
        goodChoiceId: number;
        quantity: number;
    }
    """

    goodChoiceId: int = Field(..., ge=1)
    quantity: int = Field(1, ge=1)


cart = APIRouter(prefix="/cart", tags=["购物车接口"])


def _extract_user_id_from_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="凭证无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("uid")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="凭证无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


def _build_cart_item_payload(record: Cart) -> Optional[CartGoodChoice]:
    choice_model = getattr(record, "good_choice", None)
    if not choice_model:
        return None
    good_model = getattr(choice_model, "good", None)
    price_value = choice_model.price
    price_as_int = int(price_value) if price_value is not None else 0
    return CartGoodChoice(
        id=record.id,
        goodName=getattr(good_model, "title", ""),
        choice=ChoiceOut(
            id=choice_model.id,
            choiceName=choice_model.name,
            price=price_as_int,
            buyNum=record.quantity,
            choiceImg=choice_model.swiper_img,
        ),
    )


@cart.get(
    "/items",
    response_model=CartGoodChoicesOut,
    summary="查询购物车内的商品",
)
async def list_cart_items(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CartGoodChoicesOut:
    user_id = _extract_user_id_from_token(token)
    cart_records = await cart_controller.list_items_by_owner(user_id)
    items: List[CartGoodChoice] = []
    for record in cart_records:
        payload = _build_cart_item_payload(record)
        if payload:
            items.append(payload)
    return CartGoodChoicesOut(id=user_id, items=items)


@cart.post(
    "/items",
    response_model=CartGoodChoice,
    status_code=status.HTTP_201_CREATED,
    summary="加入购物车",
)
async def add_cart_choice(
    payload: CartAddChoice,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CartGoodChoice:
    user_id = _extract_user_id_from_token(token)
    exists = await GoodChoice.filter(id=payload.goodChoiceId).exists()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品选项不存在",
        )
    record = await cart_controller.add_choice(
        owner_id=user_id,
        good_choice_id=payload.goodChoiceId,
        quantity=payload.quantity,
    )
    response_payload = _build_cart_item_payload(record)
    if not response_payload:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="购物车信息异常",
        )
    return response_payload


@cart.delete("/items/{good_choice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cart_item(
    good_choice_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    user_id = _extract_user_id_from_token(token)
    deleted = await Cart.filter(good_choice_id=good_choice_id, cart_owner_id=user_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="购物车条目不存在")
    return {"message": "删除成功"}