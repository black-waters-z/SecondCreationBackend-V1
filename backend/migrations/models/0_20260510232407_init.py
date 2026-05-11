from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "tags" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "type" VARCHAR(20) NOT NULL /* CHARACTER: character\nCROSS: cross\nWORK: work */,
    "description" TEXT,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "uid_tags_name_ce8f15" UNIQUE ("name", "type")
) /* 通用标签 */;
CREATE TABLE IF NOT EXISTS "tag_relations" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "character_tag_id" INT NOT NULL REFERENCES "tags" ("id") ON DELETE CASCADE,
    "work_tag_id" INT NOT NULL REFERENCES "tags" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_tag_relatio_work_ta_5637e7" UNIQUE ("work_tag_id", "character_tag_id")
) /* 作品标签与角色标签的关联 */;
CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255),
    "avatar_url" TEXT,
    "bio" TEXT,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_active" INT NOT NULL DEFAULT 1
) /* 用户基础信息 */;
CREATE TABLE IF NOT EXISTS "collections" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "image_url" VARCHAR(255),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "author_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "articles" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "subtitle" VARCHAR(500),
    "content" TEXT NOT NULL,
    "image_urls" JSON,
    "view_count" INT NOT NULL DEFAULT 0,
    "like_count" INT NOT NULL DEFAULT 0,
    "favorite_count" INT NOT NULL DEFAULT 0,
    "reward_amount" VARCHAR(40) NOT NULL DEFAULT 0,
    "status" VARCHAR(20) NOT NULL DEFAULT 'published',
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "published_at" TIMESTAMP,
    "author_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "collection_id" INT REFERENCES "collections" ("id") ON DELETE SET NULL
) /* 文章内容 */;
CREATE TABLE IF NOT EXISTS "article_comments" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "content" TEXT NOT NULL,
    "like_count" INT NOT NULL DEFAULT 0,
    "reply_count" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" INT NOT NULL DEFAULT 0,
    "deleted_at" TIMESTAMP,
    "has_viewed" INT NOT NULL DEFAULT 0,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "parent_id" INT REFERENCES "article_comments" ("id") ON DELETE SET NULL,
    "user_id" INT REFERENCES "users" ("id") ON DELETE SET NULL
) /* 文章评论（支持多级评论） */;
CREATE TABLE IF NOT EXISTS "article_comment_likes" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "liked_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "comment_id" INT NOT NULL REFERENCES "article_comments" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_article_com_comment_63be9a" UNIQUE ("comment_id", "user_id")
) /* 文章评论点赞 */;
CREATE TABLE IF NOT EXISTS "article_recommendations" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "score" REAL NOT NULL DEFAULT 0,
    "recommended_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_clicked" INT NOT NULL DEFAULT 0,
    "clicked_at" TIMESTAMP,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* 文章推荐记录 */;
CREATE TABLE IF NOT EXISTS "article_reward_rankings" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "total_amount" VARCHAR(40) NOT NULL DEFAULT 0,
    "reward_count" INT NOT NULL DEFAULT 0,
    "last_rewarded_at" TIMESTAMP NOT NULL,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_article_rew_article_fa7bcf" UNIQUE ("article_id", "user_id")
) /* 文章打赏者排行 */;
CREATE TABLE IF NOT EXISTS "collection_subscriptions" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "collection_id" INT NOT NULL REFERENCES "collections" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_collection__collect_19c80a" UNIQUE ("collection_id", "user_id")
);
CREATE TABLE IF NOT EXISTS "drafts" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "subtitle" VARCHAR(500),
    "content" TEXT NOT NULL,
    "image_urls" JSON,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "author_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* 文章草稿 */;
CREATE TABLE IF NOT EXISTS "files" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "file_hash" VARCHAR(32) NOT NULL,
    "total_chunks" INT NOT NULL,
    "uploaded_chunks" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_files_file_ha_66cdcc" UNIQUE ("file_hash", "user_id")
) /* 大文件上传 */;
CREATE TABLE IF NOT EXISTS "goods" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "good_img" VARCHAR(255),
    "is_active" INT NOT NULL DEFAULT 1,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "publisher_id" INT REFERENCES "users" ("id") ON DELETE SET NULL
) /* 商品信息 */;
CREATE TABLE IF NOT EXISTS "good_choices" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "price" VARCHAR(40) NOT NULL,
    "swiper_img" VARCHAR(255) NOT NULL,
    "stock" INT NOT NULL DEFAULT 0,
    "display_order" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "good_id" INT NOT NULL REFERENCES "goods" ("id") ON DELETE CASCADE
) /* 商品可选项 */;
CREATE TABLE IF NOT EXISTS "cart" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "quantity" INT NOT NULL DEFAULT 1,
    "cart_owner_id" INT REFERENCES "users" ("id") ON DELETE SET NULL,
    "good_choice_id" INT REFERENCES "good_choices" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "good_comments" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "content" TEXT NOT NULL,
    "like_count" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" INT NOT NULL DEFAULT 0,
    "deleted_at" TIMESTAMP,
    "good_id" INT NOT NULL REFERENCES "goods" ("id") ON DELETE CASCADE,
    "parent_id" INT REFERENCES "good_comments" ("id") ON DELETE SET NULL,
    "user_id" INT REFERENCES "users" ("id") ON DELETE SET NULL
) /* 商品评论（支持多级评论） */;
CREATE TABLE IF NOT EXISTS "good_comment_likes" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "comment_id" INT NOT NULL REFERENCES "good_comments" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_good_commen_comment_b38913" UNIQUE ("comment_id", "user_id")
) /* 用户针对商品评论的点赞\/互动 */;
CREATE TABLE IF NOT EXISTS "order" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "order_id" VARCHAR(64) NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "quantity" INT NOT NULL DEFAULT 1,
    "good_choice_id" INT REFERENCES "good_choices" ("id") ON DELETE SET NULL,
    "orderer_id" INT REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "rewards" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "amount" VARCHAR(40) NOT NULL,
    "message" TEXT,
    "rewarded_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(20) NOT NULL DEFAULT 'completed',
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* 打赏记录 */;
CREATE TABLE IF NOT EXISTS "user_attentions" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "follower_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "following_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_attent_followe_69abb1" UNIQUE ("follower_id", "following_id")
) /* 用户关注记录 */;
CREATE TABLE IF NOT EXISTS "user_favorites" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "favorited_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "has_viewed" INT NOT NULL DEFAULT 0,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_favori_user_id_c6d9c6" UNIQUE ("user_id", "article_id")
) /* 用户收藏 */;
CREATE TABLE IF NOT EXISTS "user_interests" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "interest_score" REAL NOT NULL DEFAULT 0,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "tag_id" INT NOT NULL REFERENCES "tags" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_intere_user_id_74cb16" UNIQUE ("user_id", "tag_id")
) /* 用户兴趣偏好 */;
CREATE TABLE IF NOT EXISTS "user_likes" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "liked_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "has_viewed" INT NOT NULL DEFAULT 0,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_likes_user_id_180529" UNIQUE ("user_id", "article_id")
) /* 用户点赞 */;
CREATE TABLE IF NOT EXISTS "user_profiles" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "first_name" VARCHAR(50),
    "last_name" VARCHAR(50),
    "birth_date" DATE,
    "location" VARCHAR(100),
    "website" VARCHAR(255),
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* 用户详细资料 */;
CREATE TABLE IF NOT EXISTS "user_view_histories" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "viewed_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "duration" INT NOT NULL DEFAULT 0,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* 用户浏览记录 */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "articles_tags" (
    "articles_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "tag_id" INT NOT NULL REFERENCES "tags" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_articles_ta_article_bd1351" ON "articles_tags" ("articles_id", "tag_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
