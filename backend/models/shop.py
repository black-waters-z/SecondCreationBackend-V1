from tortoise import fields
from tortoise.fields import CASCADE, SET_NULL
from tortoise.models import Model


class Good(Model):
    """商品信息"""

    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    description = fields.TextField(null=True)
    good_img = fields.CharField(max_length=255, null=True)
    publisher = fields.ForeignKeyField(
        "models.User",
        related_name="published_goods",
        on_delete=SET_NULL,
        null=True,
    )
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "goods"


class GoodChoice(Model):
    """商品可选项"""

    id = fields.IntField(pk=True)
    good = fields.ForeignKeyField(
        "models.Good",
        related_name="choices",
        on_delete=CASCADE,
    )
    name = fields.CharField(max_length=100)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    swiper_img = fields.CharField(max_length=255)
    stock = fields.IntField(default=0)
    display_order = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "good_choices"
        ordering = ("display_order", "id")


class GoodComment(Model):
    """商品评论（支持多级评论）"""

    id = fields.IntField(pk=True)
    good = fields.ForeignKeyField(
        "models.Good",
        related_name="comments",
        on_delete=CASCADE,
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="good_comments",
        on_delete=SET_NULL,
        null=True,
    )
    parent = fields.ForeignKeyField(
        "models.GoodComment",
        related_name="replies",
        on_delete=SET_NULL,
        null=True,
    )
    content = fields.TextField()
    like_count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "good_comments"


class GoodCommentLike(Model):
    """用户针对商品评论的点赞/互动"""

    id = fields.IntField(pk=True)
    comment = fields.ForeignKeyField(
        "models.GoodComment",
        related_name="likes",
        on_delete=CASCADE,
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="good_comment_likes",
        on_delete=CASCADE,
    )
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "good_comment_likes"
        unique_together = ("comment", "user")
