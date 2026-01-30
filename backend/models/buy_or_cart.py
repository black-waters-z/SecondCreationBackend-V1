from enum import Enum

from tortoise import fields
from tortoise.fields import CASCADE, SET_NULL
from tortoise.models import Model


# 订单,一个订单可以有多个good_choice.order_id应该随机生成永久不得重复
class Order(Model):
    id = fields.IntField(pk=True,unique=True)
    order_id = fields.CharField(max_length=64)
    created_at = fields.DatetimeField(auto_now_add=True)
    orderer = fields.ForeignKeyField(
        "models.User",
        related_name="orders",
        on_delete=SET_NULL,
        null=True,
    )
    good_choice = fields.ForeignKeyField(
        "models.GoodChoice",
        related_name="order_good_choices",
        on_delete=SET_NULL,
        null=True,
    )
    quantity = fields.IntField(default=1)


# 从获取到的cart_owner的id来获取整个购物车
class Cart(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    cart_owner = fields.ForeignKeyField(
        "models.User",
        related_name="carts",
        on_delete=SET_NULL,
        null=True,
    )
    good_choice = fields.ForeignKeyField(
        "models.GoodChoice",
        related_name="carts",
        on_delete=SET_NULL,
        null=True,
    )
    quantity = fields.IntField(default=1)
