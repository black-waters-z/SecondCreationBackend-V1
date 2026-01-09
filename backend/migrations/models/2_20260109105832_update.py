from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `articles` ADD `image_urls` JSON;
        ALTER TABLE `articles` DROP COLUMN `image_url`;
        DROP TABLE IF EXISTS `testmodel`;
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `articles` ADD `image_url` LONGTEXT;
        ALTER TABLE `articles` DROP COLUMN `image_urls`;"""
