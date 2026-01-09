from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        Drop TABLE IF EXISTS `testmodel_aa`;
        DROP TABLE IF EXISTS `aa`;
        DROP TABLE IF EXISTS `testmodel`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
