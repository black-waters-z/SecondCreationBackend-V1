from tortoise import models,fields
from tortoise.fields import CASCADE, SET_NULL  # 导入正确的类型


class Like(models.Model):
    """
    id:主键
    user:用户id外键
    article_id:多对多外键
    """
    id=fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="likes",on_delete=CASCADE)
    article = fields.ForeignKeyField("models.Article", related_name="likes",on_delete=CASCADE)
    created_at = fields.DatetimeField(auto_now_add=True)  # 点赞时间
    is_active = fields.BooleanField(default=True)  # 是否有效（可用于取消点赞）

    class Meta:
        table = "likes"
        unique_together = [("user", "article")]  # 防止重复点赞
