from tortoise import fields
from tortoise.fields import CASCADE
from tortoise.models import Model


class Collection(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=200)
    description = fields.TextField(null=True)
    image_url = fields.CharField(max_length=255, null=True)
    author = fields.ForeignKeyField(
        "models.User",
        related_name="collections",
        on_delete=CASCADE,
    )
    subscribers = fields.ManyToManyField(
        "models.User",
        related_name="subscribed_collections",
        through="collection_subscribers",
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "collections"
