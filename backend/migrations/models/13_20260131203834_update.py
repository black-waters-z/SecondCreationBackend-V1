from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `article_comment_likes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `liked_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `comment_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_article_com_comment_63be9a` (`comment_id`, `user_id`),
    CONSTRAINT `fk_article__article__150ffb68` FOREIGN KEY (`comment_id`) REFERENCES `article_comments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_article__users_77a21c53` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='文章评论点赞';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `article_comment_likes`;"""
