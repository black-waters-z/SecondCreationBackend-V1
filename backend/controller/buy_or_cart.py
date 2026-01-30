from typing import List

from backend.models import Cart
from backend.schemas.buy_or_cart import CartCreate, CartUpdate

from .base import ApiController


class CartController(ApiController[Cart, CartCreate, CartUpdate]):
    def __init__(self) -> None:
        super().__init__(Cart)

    async def list_items_by_owner(self, owner_id: int) -> List[Cart]:
        query = (
            self.model.filter(cart_owner_id=owner_id)
            .prefetch_related("good_choice__good")
            .order_by("-created_at")
        )
        return await query

    async def add_choice(
        self,
        owner_id: int,
        good_choice_id: int,
        quantity: int,
    ) -> Cart:
        record = await self.model.filter(
            cart_owner_id=owner_id, good_choice_id=good_choice_id
        ).first()
        if record:
            record.quantity += quantity
            await record.save()
        else:
            record = self.model(
                cart_owner_id=owner_id,
                good_choice_id=good_choice_id,
                quantity=quantity,
            )
            await record.save()
        await record.fetch_related("good_choice__good")
        return record


cart_controller = CartController()
