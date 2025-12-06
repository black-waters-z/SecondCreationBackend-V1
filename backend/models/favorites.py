from tortoise import models, fields
from tortoise.fields import CASCADE, SET_NULL  # 导入正确的类型


class Favorites(models.Model):
    """
    id:主键
    name:收藏夹名字
    poster_id:多对一，建立收藏夹的用户的id，外键
    article_id:多对多，收藏夹中的文章的id
    """
    id = fields.IntField(primary_key=True)
    name=fields.CharField(max_length=10,description="收藏夹名")
    description=fields.CharField(max_length=30,description="关于收藏夹的叙述")
    poster=fields.ForeignKeyField("models.User",related_name="favorites",on_delete=CASCADE)
    article=fields.ManyToManyField("models.Article",related_name="favorites")

    class Meta:
        """
        table:显式指定表名
        indexes:数据库索引
        """
        table = "favorites"
        unique_together = [("name", "poster")]






