from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` ALTER COLUMN `avatar` SET DEFAULT 'avatar1.PNG';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` ALTER COLUMN `avatar` SET DEFAULT 'avatar.png';"""
