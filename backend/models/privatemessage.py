from tortoise import models, fields
from tortoise.fields import CASCADE


class PrivateMessage(models.Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    message = fields.TextField()

    poster = fields.ForeignKeyField("models.User", related_name="sent_message", on_delete=CASCADE)
    post_to = fields.ForeignKeyField("models.User", related_name="receive_message", on_delete=CASCADE)

    poster_delete = fields.BooleanField(default=False, description="发布者删除")
    post_to_delete = fields.BooleanField(default=False, description="接受者删除")

    class Meta:
        table = "privatemessage"
        indexes = [
            ("poster", "post_to")
        ]
