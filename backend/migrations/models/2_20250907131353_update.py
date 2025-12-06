from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `articles` ADD `introduction` VARCHAR(100);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `articles` DROP COLUMN `introduction`;"""
