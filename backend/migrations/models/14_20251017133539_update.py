from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `privatemessage` ADD `post_to_delete` BOOL NOT NULL COMMENT '接受者删除' DEFAULT 0;
        ALTER TABLE `privatemessage` ADD `poster_delete` BOOL NOT NULL COMMENT '发布者删除' DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `privatemessage` DROP COLUMN `post_to_delete`;
        ALTER TABLE `privatemessage` DROP COLUMN `poster_delete`;"""
