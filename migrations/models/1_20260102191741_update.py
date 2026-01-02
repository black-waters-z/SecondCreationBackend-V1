from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `article_comments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `content` LONGTEXT NOT NULL,
    `like_count` INT NOT NULL DEFAULT 0,
    `reply_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `is_deleted` BOOL NOT NULL DEFAULT 0,
    `deleted_at` DATETIME(6),
    `article_id` INT NOT NULL,
    `parent_id` INT,
    `user_id` INT,
    CONSTRAINT `fk_article__articles_30a04598` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_article__article__03b7affd` FOREIGN KEY (`parent_id`) REFERENCES `article_comments` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_article__users_5dff2832` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COMMENT='文章评论（支持多级评论）';
        ALTER TABLE `role_tags` ADD `work_name_id` INT;
        CREATE TABLE IF NOT EXISTS `work_names` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `workName` VARCHAR(200) NOT NULL UNIQUE,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='作品名称';
        ALTER TABLE `role_tags` ADD CONSTRAINT `fk_role_tag_work_nam_9f58e7cd` FOREIGN KEY (`work_name_id`) REFERENCES `work_names` (`id`) ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `role_tags` DROP FOREIGN KEY `fk_role_tag_work_nam_9f58e7cd`;
        ALTER TABLE `role_tags` DROP COLUMN `work_name_id`;
        DROP TABLE IF EXISTS `work_names`;
        DROP TABLE IF EXISTS `article_comments`;"""
