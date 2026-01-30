from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `collections` DROP FOREIGN KEY `fk_collecti_articles_75b97bca`;
        ALTER TABLE `articles` ADD `collection_id` INT;
        ALTER TABLE `collections` DROP COLUMN `article_id`;
        ALTER TABLE `articles` ADD CONSTRAINT `fk_articles_collecti_988782a4` FOREIGN KEY (`collection_id`) REFERENCES `collections` (`id`) ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `articles` DROP FOREIGN KEY `fk_articles_collecti_988782a4`;
        ALTER TABLE `articles` DROP COLUMN `collection_id`;
        ALTER TABLE `collections` ADD `article_id` INT NOT NULL;
        ALTER TABLE `collections` ADD CONSTRAINT `fk_collecti_articles_75b97bca` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE;"""
