from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `privatemessage` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `message` LONGTEXT NOT NULL,
    `post_to_id` INT NOT NULL,
    `poster_id` INT NOT NULL,
    CONSTRAINT `fk_privatem_users_2f143e36` FOREIGN KEY (`post_to_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_privatem_users_4234727c` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_privatemess_poster__4651d9` (`poster_id`, `post_to_id`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `privatemessage`;"""
