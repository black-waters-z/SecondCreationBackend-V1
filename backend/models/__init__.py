"""
数据库orm模型
"""

# models/__init__.py
from .mysql import *
# 导出所有模型
__all__ = [
    'User', 'UserProfile', 'WorkName', 'RoleTag', 'CrossRoleTag', 'Article',
    'ArticleTag', 'UserViewHistory', 'UserFavorite', 'UserLike',
    'Reward', 'ArticleRewardRanking', 'UserInterest', 'ArticleRecommendation'
]
"""
数据库迁移命令:
aerich init -t config.TORTOISE_CONFIG
aerich init-db
aerich migrate --name add_column
"""
