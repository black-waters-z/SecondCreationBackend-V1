from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `articles` MODIFY COLUMN `images` JSON;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `articles` MODIFY COLUMN `images` JSON NOT NULL;"""
