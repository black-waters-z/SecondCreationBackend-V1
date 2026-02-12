from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `article_comments` ADD `has_viewed` BOOL NOT NULL DEFAULT 0;
        ALTER TABLE `user_favorites` ADD `has_viewed` BOOL NOT NULL DEFAULT 0;
        ALTER TABLE `user_likes` ADD `has_viewed` BOOL NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `user_likes` DROP COLUMN `has_viewed`;
        ALTER TABLE `user_favorites` DROP COLUMN `has_viewed`;
        ALTER TABLE `article_comments` DROP COLUMN `has_viewed`;"""
