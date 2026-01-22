from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `good_comment_likes` DROP COLUMN `icon_types`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `good_comment_likes` ADD `icon_types` JSON;"""
