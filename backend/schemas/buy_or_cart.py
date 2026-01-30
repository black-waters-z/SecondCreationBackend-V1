from typing import Optional

from pydantic import BaseModel


class CartBase(BaseModel):
    good_choice_id: Optional[int] = None
    cart_owner_id: Optional[int] = None
    quantity: Optional[int] = None


class CartCreate(CartBase):
    good_choice_id: int
    cart_owner_id: int
    quantity: int = 1


class CartUpdate(CartBase):
    pass

