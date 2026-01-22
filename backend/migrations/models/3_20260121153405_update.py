from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `goods` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `description` LONGTEXT,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='商品信息';
        CREATE TABLE IF NOT EXISTS `good_choices` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `price` DECIMAL(10,2) NOT NULL,
    `swiper_img` VARCHAR(255) NOT NULL,
    `stock` INT NOT NULL DEFAULT 0,
    `display_order` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `good_id` INT NOT NULL,
    CONSTRAINT `fk_good_cho_goods_6ba4f96f` FOREIGN KEY (`good_id`) REFERENCES `goods` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='商品可选项';
        CREATE TABLE IF NOT EXISTS `good_comments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `content` LONGTEXT NOT NULL,
    `like_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `is_deleted` BOOL NOT NULL DEFAULT 0,
    `deleted_at` DATETIME(6),
    `good_id` INT NOT NULL,
    `parent_id` INT,
    `user_id` INT,
    CONSTRAINT `fk_good_com_goods_df457864` FOREIGN KEY (`good_id`) REFERENCES `goods` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_good_com_good_com_ea2307ce` FOREIGN KEY (`parent_id`) REFERENCES `good_comments` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_good_com_users_ea64cc1f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COMMENT='商品评论（支持多级评论）';
        CREATE TABLE IF NOT EXISTS `good_comment_likes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `comment_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_good_commen_comment_b38913` (`comment_id`, `user_id`),
    CONSTRAINT `fk_good_com_good_com_8385a5d0` FOREIGN KEY (`comment_id`) REFERENCES `good_comments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_good_com_users_f15af23f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='用户针对商品评论的点赞/互动';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `goods`;
        DROP TABLE IF EXISTS `good_comments`;
        DROP TABLE IF EXISTS `good_comment_likes`;
        DROP TABLE IF EXISTS `good_choices`;"""
