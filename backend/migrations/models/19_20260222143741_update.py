from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `collection_subscribers`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE `collection_subscribers` (
    `user_id` INT NOT NULL REFERENCES `users` (`id`) ON DELETE CASCADE,
    `collections_id` INT NOT NULL REFERENCES `collections` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""
