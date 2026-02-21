"""
数据库orm模型
"""

# models/__init__.py
from .mysql import *
from .shop import *
from .test import *
from .buy_or_cart import *
from .collection import *
# 导出所有模型
__all__ = [
    'User', 'UserProfile', 'Tag', 'TagRelation', 'Article',
    'UserViewHistory', 'UserFavorite', 'UserLike', 'Reward',
    'ArticleRewardRanking', 'UserInterest', 'ArticleRecommendation',
    'ArticleComment', 'ArticleCommentLike', 'Collection',
    'Good', 'GoodChoice', 'GoodComment', 'GoodCommentLike', "Order", "Cart",
    'Draft'
]
"""
数据库迁移命令:
aerich init -t config.TORTOISE_CONFIG
aerich init-db
aerich migrate --name add_column
"""
