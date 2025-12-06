"""
数据库orm模型
"""

# models/__init__.py
from .user import User
from .article import Article
from .comment import Comment
from .zone import Zone
from .favorites import Favorites
from .like import Like
from .privatemessage import PrivateMessage
from .secondcomments import SecondComment
from .drafts import Draft
# 导出所有模型
__all__ = ["User", "Article", "Comment","Zone","Favorites","SecondComment","Draft"]

"""
数据库迁移命令:
aerich init -t config.TORTOISE_CONFIG
aerich init-db
aerich migrate --name add_column
"""