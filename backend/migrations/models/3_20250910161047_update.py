from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `favorites` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(10) NOT NULL COMMENT '收藏夹名',
    `description` VARCHAR(30) NOT NULL COMMENT '关于收藏夹的叙述',
    `poster_id_id` INT NOT NULL,
    CONSTRAINT `fk_favorite_users_bc3c0d62` FOREIGN KEY (`poster_id_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='id:主键';
        CREATE TABLE `favorites_articles` (
    `article_id` INT NOT NULL REFERENCES `articles` (`id`) ON DELETE CASCADE,
    `favorites_id` INT NOT NULL REFERENCES `favorites` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `favorites_articles`;
        DROP TABLE IF EXISTS `favorites`;"""
