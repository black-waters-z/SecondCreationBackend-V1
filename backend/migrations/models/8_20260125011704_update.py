from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `article_favorites` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `favorited_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `article_id` INT NOT NULL,
    `favorite_user_id` INT NOT NULL,
    UNIQUE KEY `uid_article_fav_article_96ed54` (`article_id`, `favorite_user_id`),
    CONSTRAINT `fk_article__articles_9d81f773` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_article__users_f111dbf1` FOREIGN KEY (`favorite_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='文章收藏';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `article_favorites`;"""
