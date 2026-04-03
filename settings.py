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
            'models': ['backend.models', 'aerich.models'],
            'default_connection': 'default'
        }
    },
    'user_tz': False,
    'timezone': 'Asia/Shanghai'
}

# ... existing code ...

SECRET_KEY="df019c7cb10e06fb1825ca75c6d7e3c2637cf579da38c487392e0ceb1cccf662"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_BASE_URL="http://localhost:8080"
BASE_HOST="localhost"
AI_TOKEN="jshoFKSRcnSAhXjJOmIU:ozKndSjiatvoMNmTnsTh"
# BASE_HOST="192.168.43.15"
# APP_BASE_URL="http://192.168.43.15:8080"
