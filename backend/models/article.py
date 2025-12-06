from tortoise import models, fields
from tortoise.fields import CASCADE, SET_NULL  # 导入正确的类型


class Article(models.Model):
    """
    id:自动生成的编号
    title:标题，可以为空
    introduction:副标题
    content:文章内容
    images:上传的图片文件名，json格式存储
    created_at:发布时间
    likes_count:点赞数
    share_count:转发数
    favorite_count:收藏数

    poster:发布者的id,外键指向user的id
    """
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=15, null=True)
    introduction=fields.CharField(max_length=100,null=True)
    content = fields.TextField()  # 在前端对输入的长度进行一个约束
    images = fields.JSONField(default=list,null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    likes_count = fields.IntField(default=0)
    share_count = fields.IntField(default=0)
    favorite_count = fields.IntField(default=0)

    poster = fields.ForeignKeyField("models.User", related_name="articles", on_delete=CASCADE)  # related_name 反向查询
    zones = fields.ManyToManyField("models.Zone", related_name="articles")

    class Meta:
        table = "articles"
        indexes = [
            ("title", "poster")
        ]
