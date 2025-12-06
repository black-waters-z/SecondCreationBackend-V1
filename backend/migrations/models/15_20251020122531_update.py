from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `drafts` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(15),
    `introduction` VARCHAR(100),
    `content` LONGTEXT NOT NULL,
    `images` JSON,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `poster_id` INT NOT NULL,
    CONSTRAINT `fk_drafts_users_50b36417` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_drafts_title_e17015` (`title`, `poster_id`)
) CHARACTER SET utf8mb4 COMMENT='id:自动生成的编号';
        CREATE TABLE `drafts_zones` (
    `drafts_id` INT NOT NULL REFERENCES `drafts` (`id`) ON DELETE CASCADE,
    `zone_id` INT NOT NULL REFERENCES `zones` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `drafts_zones`;
        DROP TABLE IF EXISTS `drafts`;
       """
