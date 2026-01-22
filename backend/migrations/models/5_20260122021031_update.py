from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `goods` ADD `publisher_id` INT;
        ALTER TABLE `goods` ADD CONSTRAINT `fk_goods_users_edb1323a` FOREIGN KEY (`publisher_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `goods` DROP FOREIGN KEY `fk_goods_users_edb1323a`;
        ALTER TABLE `goods` DROP COLUMN `publisher_id`;"""
