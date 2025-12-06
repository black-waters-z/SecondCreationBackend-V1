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
    `introduction` VARCHAR(100),
    `content` LONGTEXT NOT NULL,
    `images` JSON,
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
    `content` VARCHAR(100) NOT NULL,
    `likes_count` INT NOT NULL DEFAULT 0,
    `share_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `is_read` BOOL NOT NULL COMMENT '有没有被接收' DEFAULT 0,
    `post_to_id` INT NOT NULL,
    `poster_id` INT NOT NULL,
    CONSTRAINT `fk_comments_articles_5f4dd2a2` FOREIGN KEY (`post_to_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_comments_users_9b846666` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_comments_poster__b3a0b0` (`poster_id`, `created_at`),
    KEY `idx_comments_post_to_2b5749` (`post_to_id`, `created_at`)
) CHARACTER SET utf8mb4 COMMENT='content:评论内容';
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
CREATE TABLE IF NOT EXISTS `favorites` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(10) NOT NULL COMMENT '收藏夹名',
    `description` VARCHAR(30) NOT NULL COMMENT '关于收藏夹的叙述',
    `poster_id` INT NOT NULL,
    UNIQUE KEY `uid_favorites_name_567098` (`name`, `poster_id`),
    CONSTRAINT `fk_favorite_users_1a959948` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='id:主键';
CREATE TABLE IF NOT EXISTS `likes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `is_active` BOOL NOT NULL DEFAULT 1,
    `article_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_likes_user_id_002ffb` (`user_id`, `article_id`),
    CONSTRAINT `fk_likes_articles_2b2bb3e9` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_likes_users_a61ca3f4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='id:主键';
CREATE TABLE IF NOT EXISTS `privatemessage` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `message` LONGTEXT NOT NULL,
    `poster_delete` BOOL NOT NULL COMMENT '发布者删除' DEFAULT 0,
    `post_to_delete` BOOL NOT NULL COMMENT '接受者删除' DEFAULT 0,
    `post_to_id` INT NOT NULL,
    `poster_id` INT NOT NULL,
    CONSTRAINT `fk_privatem_users_2f143e36` FOREIGN KEY (`post_to_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_privatem_users_4234727c` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_privatemess_poster__4651d9` (`poster_id`, `post_to_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `secondcomments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `content` VARCHAR(100) NOT NULL,
    `likes_count` INT NOT NULL DEFAULT 0,
    `share_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `is_read` BOOL NOT NULL COMMENT '有没有被接收' DEFAULT 0,
    `parent_comment_id` INT COMMENT '二级评论回复的二级评论对象',
    `post_to_id` INT NOT NULL COMMENT '评论的一级评论id',
    `poster_id` INT NOT NULL COMMENT '发出评论的用户id',
    CONSTRAINT `fk_secondco_secondco_fe217b48` FOREIGN KEY (`parent_comment_id`) REFERENCES `secondcomments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_secondco_comments_817a9967` FOREIGN KEY (`post_to_id`) REFERENCES `comments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_secondco_users_52eb1f31` FOREIGN KEY (`poster_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='content:评论内容';
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
CREATE TABLE IF NOT EXISTS `user_follows` (
    `follower_id` INT NOT NULL,
    `following_id` INT NOT NULL,
    FOREIGN KEY (`follower_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`following_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_user_follow_followe_edaeec` (`follower_id`, `following_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `articles_zones` (
    `articles_id` INT NOT NULL,
    `zone_id` INT NOT NULL,
    FOREIGN KEY (`articles_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`zone_id`) REFERENCES `zones` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_articles_zo_article_ac2bb0` (`articles_id`, `zone_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `drafts_zones` (
    `drafts_id` INT NOT NULL,
    `zone_id` INT NOT NULL,
    FOREIGN KEY (`drafts_id`) REFERENCES `drafts` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`zone_id`) REFERENCES `zones` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_drafts_zone_drafts__9557a7` (`drafts_id`, `zone_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `favorites_articles` (
    `favorites_id` INT NOT NULL,
    `article_id` INT NOT NULL,
    FOREIGN KEY (`favorites_id`) REFERENCES `favorites` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_favorites_a_favorit_702148` (`favorites_id`, `article_id`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
