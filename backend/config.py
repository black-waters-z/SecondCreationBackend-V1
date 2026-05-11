import asyncio

from tortoise import Tortoise

TORTOISE_CONFIG = {
    'connections': {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": "./scforum.db",  # SQLite 数据库文件路径
            }
        }
    },
    'apps': {
        'models': {
            'models': ['models', 'aerich.models'],
            'default_connection': 'default'
        }
    },
    'user_tz': False,
    'timezone': 'Asia/Shanghai'
}

# ... existing code ...


SECRET_KEY="df019c7cb10e06fb1825ca75c6d7e3c2637cf579da38c487392e0ceb1cccf662"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60


async def test_connection():
    try:
        await Tortoise.init(config=TORTOISE_CONFIG)
        print("✅ 数据库连接成功！")

        # 检查模型注册
        models = Tortoise.apps.get("models")
        print("✅ 已注册模型:")
        for name in models.keys():
            print(f"  - {name}")

        await Tortoise.close_connections()
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())