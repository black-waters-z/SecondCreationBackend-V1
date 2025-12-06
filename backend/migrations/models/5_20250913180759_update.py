from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `likes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `is_active` BOOL NOT NULL DEFAULT 1,
    `article_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_likes_user_id_002ffb` (`user_id`, `article_id`),
    CONSTRAINT `fk_likes_articles_2b2bb3e9` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_likes_users_a61ca3f4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='id:主键';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `likes`;"""
