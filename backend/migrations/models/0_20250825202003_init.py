from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(20) NOT NULL UNIQUE,
    `password_hash` VARCHAR(128),
    `email` VARCHAR(20) NOT NULL,
    `avatar` VARCHAR(100) NOT NULL DEFAULT 'avatar.png',
    `activated` BOOL NOT NULL DEFAULT 0,
    `silence` BOOL NOT NULL DEFAULT 0
) CHARACTER SET utf8mb4 COMMENT='这是一个使用用户user的tortoise模型';
CREATE TABLE IF NOT EXISTS `articles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(15),
    `content` LONGTEXT NOT NULL,
    `images` JSON NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `likes_count` INT NOT NULL DEFAULT 0,
    `share_count` INT NOT NULL DEFAULT 0,
    `favorite_count` INT NOT NULL DEFAULT 0,
    `poster_id` INT NOT NULL,
    CONSTRAINT `fk_articles_users_3fde5cfd` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_articles_title_49ec94` (`title`, `poster_id`)
) CHARACTER SET utf8mb4 COMMENT='id:自动生成的编号';
CREATE TABLE IF NOT EXISTS `comments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `likes_count` INT NOT NULL DEFAULT 0,
    `share_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `post_to_id` INT NOT NULL,
    `poster_id` INT NOT NULL,
    CONSTRAINT `fk_comments_articles_5f4dd2a2` FOREIGN KEY (`post_to_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_comments_users_9b846666` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_comments_poster__b3a0b0` (`poster_id`, `created_at`),
    KEY `idx_comments_post_to_2b5749` (`post_to_id`, `created_at`)
) CHARACTER SET utf8mb4 COMMENT='poster:发布者的id';
CREATE TABLE IF NOT EXISTS `zones` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(10) NOT NULL,
    `image` VARCHAR(20) NOT NULL DEFAULT 'icon.png'
) CHARACTER SET utf8mb4 COMMENT='区域:(文，画，扒糖处，灌水区)';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `articles_zones` (
    `articles_id` INT NOT NULL,
    `zone_id` INT NOT NULL,
    FOREIGN KEY (`articles_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`zone_id`) REFERENCES `zones` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_articles_zo_article_ac2bb0` (`articles_id`, `zone_id`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
