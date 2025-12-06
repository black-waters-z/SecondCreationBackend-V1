from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `favorites` ADD UNIQUE INDEX `uid_favorites_name_567098` (`name`, `poster_id`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `favorites` DROP INDEX `uid_favorites_name_567098`;"""
