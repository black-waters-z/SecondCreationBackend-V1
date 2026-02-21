from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `drafts` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `subtitle` VARCHAR(500),
    `content` LONGTEXT NOT NULL,
    `image_urls` JSON,
    `author_id` INT NOT NULL,
    CONSTRAINT `fk_drafts_users_d5864523` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='文章草稿';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `drafts`;"""
