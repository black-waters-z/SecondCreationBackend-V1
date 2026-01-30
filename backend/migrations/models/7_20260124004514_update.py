from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `cart` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `quantity` INT NOT NULL DEFAULT 1,
    `cart_owner_id` INT,
    `good_choice_id` INT,
    CONSTRAINT `fk_cart_users_a230026d` FOREIGN KEY (`cart_owner_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_cart_good_cho_bf544667` FOREIGN KEY (`good_choice_id`) REFERENCES `good_choices` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `order` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `order_id` VARCHAR(64) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `quantity` INT NOT NULL DEFAULT 1,
    `good_choice_id` INT,
    `orderer_id` INT,
    CONSTRAINT `fk_order_good_cho_6810e89a` FOREIGN KEY (`good_choice_id`) REFERENCES `good_choices` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_order_users_21543a9a` FOREIGN KEY (`orderer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `order`;
        DROP TABLE IF EXISTS `cart`;"""
