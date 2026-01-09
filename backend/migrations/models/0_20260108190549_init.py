from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `aa` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `tags` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `type` VARCHAR(20) NOT NULL COMMENT 'CHARACTER: character\nCROSS: cross\nWORK: work',
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY `uid_tags_name_ce8f15` (`name`, `type`)
) CHARACTER SET utf8mb4 COMMENT='通用标签';
CREATE TABLE IF NOT EXISTS `tag_relations` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `character_tag_id` INT NOT NULL,
    `work_tag_id` INT NOT NULL,
    UNIQUE KEY `uid_tag_relatio_work_ta_5637e7` (`work_tag_id`, `character_tag_id`),
    CONSTRAINT `fk_tag_rela_tags_70e15da4` FOREIGN KEY (`character_tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tag_rela_tags_dd8318c9` FOREIGN KEY (`work_tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='作品标签与角色标签的关联';
CREATE TABLE IF NOT EXISTS `testmodel` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `avatar_url` LONGTEXT,
    `bio` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `is_active` BOOL NOT NULL DEFAULT 1
) CHARACTER SET utf8mb4 COMMENT='用户基础信息';
CREATE TABLE IF NOT EXISTS `articles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `subtitle` VARCHAR(500),
    `content` LONGTEXT NOT NULL,
    `image_urls` JSON,
    `view_count` INT NOT NULL DEFAULT 0,
    `like_count` INT NOT NULL DEFAULT 0,
    `favorite_count` INT NOT NULL DEFAULT 0,
    `reward_amount` DECIMAL(15,2) NOT NULL DEFAULT 0,
    `status` VARCHAR(20) NOT NULL DEFAULT 'published',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `published_at` DATETIME(6),
    `author_id` INT NOT NULL,
    CONSTRAINT `fk_articles_users_3b493172` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='文章内容';
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
CREATE TABLE IF NOT EXISTS `article_recommendations` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `score` DOUBLE NOT NULL DEFAULT 0,
    `recommended_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `is_clicked` BOOL NOT NULL DEFAULT 0,
    `clicked_at` DATETIME(6),
    `article_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_article__articles_d3c03b8e` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_article__users_d1f53bd8` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='文章推荐记录';
CREATE TABLE IF NOT EXISTS `article_reward_rankings` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `total_amount` DECIMAL(15,2) NOT NULL DEFAULT 0,
    `reward_count` INT NOT NULL DEFAULT 0,
    `last_rewarded_at` DATETIME(6) NOT NULL,
    `article_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_article_rew_article_fa7bcf` (`article_id`, `user_id`),
    CONSTRAINT `fk_article__articles_e36ee74c` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_article__users_d52bffed` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='文章打赏者排行';
CREATE TABLE IF NOT EXISTS `rewards` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `amount` DECIMAL(15,2) NOT NULL,
    `message` LONGTEXT,
    `rewarded_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `status` VARCHAR(20) NOT NULL DEFAULT 'completed',
    `article_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_rewards_articles_8c4ed276` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_rewards_users_142b5d91` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='打赏记录';
CREATE TABLE IF NOT EXISTS `user_favorites` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `favorited_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `article_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_user_favori_user_id_c6d9c6` (`user_id`, `article_id`),
    CONSTRAINT `fk_user_fav_articles_c3d5c73c` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_fav_users_3fb5003a` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='用户收藏';
CREATE TABLE IF NOT EXISTS `user_interests` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `interest_score` DOUBLE NOT NULL DEFAULT 0,
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `tag_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_user_intere_user_id_74cb16` (`user_id`, `tag_id`),
    CONSTRAINT `fk_user_int_tags_914668f6` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_int_users_14a5b077` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='用户兴趣偏好';
CREATE TABLE IF NOT EXISTS `user_likes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `liked_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `article_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_user_likes_user_id_180529` (`user_id`, `article_id`),
    CONSTRAINT `fk_user_lik_articles_9e6bb644` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_lik_users_4c074754` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='用户点赞';
CREATE TABLE IF NOT EXISTS `user_profiles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `first_name` VARCHAR(50),
    `last_name` VARCHAR(50),
    `birth_date` DATE,
    `location` VARCHAR(100),
    `website` VARCHAR(255),
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_user_pro_users_f50f74ad` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='用户详细资料';
CREATE TABLE IF NOT EXISTS `user_view_histories` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `viewed_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `duration` INT NOT NULL DEFAULT 0,
    `article_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_user_vie_articles_e5ec067a` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_vie_users_3381cec7` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='用户浏览记录';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `testmodel_aa` (
    `testmodel_id` INT NOT NULL,
    `aa_id` INT NOT NULL,
    FOREIGN KEY (`testmodel_id`) REFERENCES `testmodel` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`aa_id`) REFERENCES `aa` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_testmodel_a_testmod_30669e` (`testmodel_id`, `aa_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `articles_tags` (
    `articles_id` INT NOT NULL,
    `tag_id` INT NOT NULL,
    FOREIGN KEY (`articles_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_articles_ta_article_bd1351` (`articles_id`, `tag_id`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
