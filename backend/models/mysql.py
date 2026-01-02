from tortoise import models, fields
from tortoise.fields import CASCADE, SET_NULL  # 导入正确的类型
from tortoise.models import Model


class User(Model):
    """用户基础信息"""
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    password_hash = fields.CharField(max_length=255)
    avatar_url = fields.TextField(null=True)
    bio = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "users"


class UserProfile(Model):
    """用户详细资料"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='profile')
    first_name = fields.CharField(max_length=50, null=True)
    last_name = fields.CharField(max_length=50, null=True)
    birth_date = fields.DateField(null=True)
    location = fields.CharField(max_length=100, null=True)
    website = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "user_profiles"


class WorkName(Model):
    """作品名称"""
    id = fields.IntField(pk=True)
    workName = fields.CharField(max_length=200, unique=True)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "work_names"


class RoleTag(Model):
    """角色标签"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)
    description = fields.TextField(null=True)
    color = fields.CharField(max_length=7, default="#000000")  # HEX颜色值
    work_name = fields.ForeignKeyField('models.WorkName', related_name='role_tags', null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "role_tags"


class CrossRoleTag(Model):
    """交叉角色标签 - 两两角色的组合"""
    id = fields.IntField(pk=True)
    role_a = fields.ForeignKeyField('models.RoleTag', related_name='cross_role_a')
    role_b = fields.ForeignKeyField('models.RoleTag', related_name='cross_role_b')
    name = fields.CharField(max_length=100, unique=True)  # 组合名称
    description = fields.TextField(null=True)
    weight = fields.FloatField(default=1.0)  # 权重，用于推荐算法

    class Meta:
        table = "cross_role_tags"
        unique_together = ("role_a", "role_b")


class Article(Model):
    """文章内容"""
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    subtitle = fields.CharField(max_length=500, null=True)  # 小字
    author = fields.ForeignKeyField('models.User', related_name='articles')
    content = fields.TextField()
    image_url = fields.TextField(null=True)  # 文章图片地址
    tags = fields.ManyToManyField('models.CrossRoleTag', related_name='articles')
    view_count = fields.IntField(default=0)
    like_count = fields.IntField(default=0)
    favorite_count = fields.IntField(default=0)
    reward_amount = fields.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = fields.CharField(max_length=20, default="published")  # published, draft, deleted
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    published_at = fields.DatetimeField(null=True)

    class Meta:
        table = "articles"


class ArticleTag(Model):
    """文章与交叉标签关联"""
    id = fields.IntField(pk=True)
    article = fields.ForeignKeyField('models.Article')
    tag = fields.ForeignKeyField('models.CrossRoleTag')

    class Meta:
        table = "article_tags"
        unique_together = ("article", "tag")


class UserViewHistory(Model):
    """用户浏览记录"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='view_history')
    article = fields.ForeignKeyField('models.Article', related_name='views')
    viewed_at = fields.DatetimeField(auto_now_add=True)
    duration = fields.IntField(default=0)  # 浏览时长(秒)

    class Meta:
        table = "user_view_histories"


class UserFavorite(Model):
    """用户收藏"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='favorites')
    article = fields.ForeignKeyField('models.Article', related_name='favorited_by')
    favorited_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_favorites"
        unique_together = ("user", "article")


class UserLike(Model):
    """用户点赞"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='likes')
    article = fields.ForeignKeyField('models.Article', related_name='liked_by')
    liked_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_likes"
        unique_together = ("user", "article")


class Reward(Model):
    """打赏记录"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='rewards_given')
    article = fields.ForeignKeyField('models.Article', related_name='rewards_received')
    amount = fields.DecimalField(max_digits=15, decimal_places=2)
    message = fields.TextField(null=True)  # 打赏留言
    rewarded_at = fields.DatetimeField(auto_now_add=True)
    status = fields.CharField(max_length=20, default="completed")  # completed, pending, failed

    class Meta:
        table = "rewards"


class ArticleRewardRanking(Model):
    """文章打赏者排名"""
    id = fields.IntField(pk=True)
    article = fields.ForeignKeyField('models.Article', related_name='reward_rankings')
    user = fields.ForeignKeyField('models.User')
    total_amount = fields.DecimalField(max_digits=15, decimal_places=2, default=0)
    reward_count = fields.IntField(default=0)
    last_rewarded_at = fields.DatetimeField()

    class Meta:
        table = "article_reward_rankings"
        unique_together = ("article", "user")


class UserInterest(Model):
    """用户兴趣偏好"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='interests')
    tag = fields.ForeignKeyField('models.CrossRoleTag')
    interest_score = fields.FloatField(default=0.0)  # 兴趣分数
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_interests"
        unique_together = ("user", "tag")


class ArticleRecommendation(Model):
    """文章推荐记录"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='recommendations')
    article = fields.ForeignKeyField('models.Article')
    score = fields.FloatField(default=0.0)  # 推荐分数
    recommended_at = fields.DatetimeField(auto_now_add=True)
    is_clicked = fields.BooleanField(default=False)  # 是否点击
    clicked_at = fields.DatetimeField(null=True)

    class Meta:
        table = "article_recommendations"


# 在 backend/models/mysql.py 中添加以下模型定义
class ArticleComment(Model):
    """文章评论（支持多级评论）"""
    id = fields.IntField(pk=True)
    article = fields.ForeignKeyField('models.Article', related_name='comments', on_delete=CASCADE)
    user = fields.ForeignKeyField('models.User', related_name='comments', on_delete=SET_NULL, null=True)
    parent = fields.ForeignKeyField('models.ArticleComment', related_name='replies', on_delete=SET_NULL, null=True)
    content = fields.TextField()
    like_count = fields.IntField(default=0)
    reply_count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)  # 软删除标记
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "article_comments"
