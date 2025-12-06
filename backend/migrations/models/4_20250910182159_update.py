from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `favorites` DROP FOREIGN KEY `fk_favorite_users_bc3c0d62`;
        ALTER TABLE `favorites` RENAME COLUMN `poster_id_id` TO `poster_id`;
        ALTER TABLE `favorites` ADD CONSTRAINT `fk_favorite_users_1a959948` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `favorites` DROP FOREIGN KEY `fk_favorite_users_1a959948`;
        ALTER TABLE `favorites` RENAME COLUMN `poster_id` TO `poster_id_id`;
        ALTER TABLE `favorites` ADD CONSTRAINT `fk_favorite_users_bc3c0d62` FOREIGN KEY (`poster_id_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;"""
