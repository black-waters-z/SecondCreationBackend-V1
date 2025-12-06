from tortoise import models, fields
from tortoise.fields import CASCADE, SET_NULL  # 导入正确的类型


class Comment(models.Model):
    """
    content:评论内容
    poster:发布者的id
    post_to:发布对象article的id
    likes_count:点赞数
    share_count:转发数
    created_at:发布时间
    """
    id=fields.IntField(primary_key=True)
    content=fields.CharField(max_length=100,null=False)
    likes_count = fields.IntField(default=0)
    share_count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    is_read=fields.BooleanField(default=False,description="有没有被接收")

    poster = fields.ForeignKeyField("models.User", related_name="comments",on_delete=CASCADE)
    post_to = fields.ForeignKeyField("models.Article", related_name="comments",on_delete=CASCADE)
    class Meta:
        """
        table:显式指定表名
        indexes:数据库索引
        """
        table = "comments"
        indexes = [
            ("poster", "created_at"),
            ("post_to", "created_at")
        ]
