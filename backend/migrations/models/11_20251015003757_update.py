from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `user_follows`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE `user_follows` (
    `follower_id` INT NOT NULL REFERENCES `users` (`id`) ON DELETE CASCADE,
    `following_id` INT NOT NULL REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""
