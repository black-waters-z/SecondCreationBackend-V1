from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `files` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `file_hash` VARCHAR(32) NOT NULL,
    `total_chunks` INT NOT NULL,
    `uploaded_chunks` INT NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_files_file_ha_66cdcc` (`file_hash`, `user_id`),
    CONSTRAINT `fk_files_users_de5c82ea` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='大文件上传';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `files`;"""
