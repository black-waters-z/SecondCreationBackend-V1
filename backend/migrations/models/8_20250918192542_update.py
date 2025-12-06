from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `comments` ADD `is_read` BOOL NOT NULL COMMENT '有没有被接收' DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `comments` DROP COLUMN `is_read`;"""
