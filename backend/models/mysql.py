from enum import Enum

from tortoise import fields
from tortoise.fields import CASCADE, SET_NULL
from tortoise.models import Model


class TagType(str, Enum):
    CHARACTER = "character"
    CROSS = "cross"
    WORK = "work"


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
    user = fields.ForeignKeyField("models.User", related_name="profile")
    first_name = fields.CharField(max_length=50, null=True)
    last_name = fields.CharField(max_length=50, null=True)
    birth_date = fields.DateField(null=True)
    location = fields.CharField(max_length=100, null=True)
    website = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "user_profiles"


class Tag(Model):
    """通用标签"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    type = fields.CharEnumField(TagType, max_length=20)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tags"
        unique_together = ("name", "type")


class TagRelation(Model):
    """作品标签与角色标签的关联"""
    id = fields.IntField(pk=True)
    work_tag = fields.ForeignKeyField(
        "models.Tag",
        related_name="character_relations",
        on_delete=CASCADE,
    )
    character_tag = fields.ForeignKeyField(
        "models.Tag",
        related_name="work_relations",
        on_delete=CASCADE,
    )
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tag_relations"
        unique_together = ("work_tag", "character_tag")


class Article(Model):
    """文章内容"""
    id = fields.IntField(pk=True, auto_increment=True)
    title = fields.CharField(max_length=200)
    subtitle = fields.CharField(max_length=500, null=True)
    author = fields.ForeignKeyField("models.User", related_name="articles")
    content = fields.TextField()
    image_urls = fields.JSONField(null=True)
    collection = fields.ForeignKeyField(
        "models.Collection",
        related_name="articles",
        null=True,
        on_delete=SET_NULL,
    )

    view_count = fields.IntField(default=0)
    like_count = fields.IntField(default=0)
    favorite_count = fields.IntField(default=0)
    reward_amount = fields.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = fields.CharField(max_length=20, default="published")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    published_at = fields.DatetimeField(null=True)
    tags = fields.ManyToManyField(
        "models.Tag",
        related_name="articles",
    )

    class Meta:
        table = "articles"


class UserViewHistory(Model):
    """用户浏览记录"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="view_history")
    article = fields.ForeignKeyField("models.Article", related_name="views")
    viewed_at = fields.DatetimeField(auto_now_add=True)
    duration = fields.IntField(default=0)

    class Meta:
        table = "user_view_histories"


class UserFavorite(Model):
    """用户收藏"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="favorites")
    article = fields.ForeignKeyField("models.Article", related_name="favorited_by")
    favorited_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_favorites"
        unique_together = ("user", "article")


class UserLike(Model):
    """用户点赞"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="likes")
    article = fields.ForeignKeyField("models.Article", related_name="liked_by")
    liked_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_likes"
        unique_together = ("user", "article")


class Reward(Model):
    """打赏记录"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="rewards_given")
    article = fields.ForeignKeyField("models.Article", related_name="rewards_received")
    amount = fields.DecimalField(max_digits=15, decimal_places=2)
    message = fields.TextField(null=True)
    rewarded_at = fields.DatetimeField(auto_now_add=True)
    status = fields.CharField(max_length=20, default="completed")

    class Meta:
        table = "rewards"


class ArticleRewardRanking(Model):
    """文章打赏者排行"""
    id = fields.IntField(pk=True)
    article = fields.ForeignKeyField(
        "models.Article", related_name="reward_rankings"
    )
    user = fields.ForeignKeyField("models.User")
    total_amount = fields.DecimalField(max_digits=15, decimal_places=2, default=0)
    reward_count = fields.IntField(default=0)
    last_rewarded_at = fields.DatetimeField()

    class Meta:
        table = "article_reward_rankings"
        unique_together = ("article", "user")


class UserInterest(Model):
    """用户兴趣偏好"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="interests")
    tag = fields.ForeignKeyField("models.Tag")
    interest_score = fields.FloatField(default=0.0)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_interests"
        unique_together = ("user", "tag")


class ArticleRecommendation(Model):
    """文章推荐记录"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="recommendations")
    article = fields.ForeignKeyField("models.Article")
    score = fields.FloatField(default=0.0)
    recommended_at = fields.DatetimeField(auto_now_add=True)
    is_clicked = fields.BooleanField(default=False)
    clicked_at = fields.DatetimeField(null=True)

    class Meta:
        table = "article_recommendations"


class ArticleComment(Model):
    """文章评论（支持多级评论）"""
    id = fields.IntField(pk=True)
    article = fields.ForeignKeyField(
        "models.Article", related_name="comments", on_delete=CASCADE
    )
    user = fields.ForeignKeyField(
        "models.User", related_name="comments", on_delete=SET_NULL, null=True
    )
    parent = fields.ForeignKeyField(
        "models.ArticleComment",
        related_name="replies",
        on_delete=SET_NULL,
        null=True,
    )
    content = fields.TextField()
    like_count = fields.IntField(default=0)
    reply_count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "article_comments"


class ArticleCommentLike(Model):
    """文章评论点赞"""
    id = fields.IntField(pk=True)
    comment = fields.ForeignKeyField(
        "models.ArticleComment",
        related_name="likes",
        on_delete=CASCADE,
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="comment_likes",
        on_delete=CASCADE,
    )
    liked_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "article_comment_likes"
        unique_together = ("comment", "user")
