from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE `secondcomments` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `content` VARCHAR(100) NOT NULL,
            `likes_count` INT NOT NULL DEFAULT 0,
            `share_count` INT NOT NULL DEFAULT 0,
            `created_at` DATETIME(6) NOT NULL,
            `is_read` BOOL NOT NULL DEFAULT 0,
            `poster_id` INT NOT NULL,
            `post_to_id` INT NOT NULL,
            FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
            FOREIGN KEY (`post_to_id`) REFERENCES `comments` (`id`) ON DELETE CASCADE
        ) CHARACTER SET utf8mb4;
        CREATE TABLE `user_follows` (
    `follower_id` INT NOT NULL REFERENCES `users` (`id`) ON DELETE CASCADE,
    `following_id` INT NOT NULL REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `user_follows`;
        DROP TABLE IF EXISTS `user_follows`;"""
