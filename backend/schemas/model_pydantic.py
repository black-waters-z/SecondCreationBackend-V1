from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise import models, fields
from pydantic import BaseModel
from ..models import User, Article, Favorites, Like, Comment, SecondComment, Draft

User_Pydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude=("id", "avatar", "activated", "silence"))
Article_Pydantic = pydantic_model_creator(Article, name="Article")
ArticleIn_Pydantic = pydantic_model_creator(Article, name="ArticleIn", exclude=(
    "id", "likes_count", "share_count", "favorite_count", "created_at"))
Draft_Pydantic = pydantic_model_creator(Draft, name="Draft")
DraftIn_Pydantic = pydantic_model_creator(Draft, name="DraftIn", exclude=("id", "created_at"))

Favorites_Pydantic = pydantic_model_creator(Favorites, name="Favorites")
FavoritesIn_Pydantic = pydantic_model_creator(Favorites, name="FavoritesIn", exclude_readonly=True)
Like_Pydantic = pydantic_model_creator(Like, name="Like")
LikeIn_Pydantic = pydantic_model_creator(Like, name="LikeIn", exclude_readonly=True)
Comment_Pydantic = pydantic_model_creator(Comment, name="Comment")
CommentIn_Pydantic = pydantic_model_creator(Comment, name="CommentIn", exclude=("id", "created_at", "likes_count",
                                                                                "share_count", "is_read"))
SecondComment_Pydantic = pydantic_model_creator(SecondComment, name="SecondComment")
SecondCommentIn_Pydantic = pydantic_model_creator(SecondComment, name="SecondCommentIn",
                                                  exclude=("id", "created_at", "likes_count",
                                                           "share_count", "is_read"))


class loginIn_pydantic(BaseModel):
    """
    login时的输入模型
    """
    name: str
    password: str


class Token(BaseModel):
    """
    token输出模型
    """
    access_token: str
    token_type: str
