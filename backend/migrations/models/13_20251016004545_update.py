from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `secondcomments` ADD `parent_comment_id` INT COMMENT '二级评论回复的二级评论对象';
        ALTER TABLE `secondcomments` ADD CONSTRAINT `fk_secondco_secondco_fe217b48` FOREIGN KEY (`parent_comment_id`) REFERENCES `secondcomments` (`id`) ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `secondcomments` DROP FOREIGN KEY `fk_secondco_secondco_fe217b48`;
        ALTER TABLE `secondcomments` DROP COLUMN `parent_comment_id`;"""
