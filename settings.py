TORTOISE_CONFIG = {
    'connections': {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host":"localhost",
                "port": 3306,             # 容器内端口
                "user": "root",
                "password": "161231",
                "database": "scforum",
                "pool_recycle": 3600,
                "connect_timeout": 30,
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

SECRET_KEY="df019c7cb10e06fb1825ca75c6d7e3c2637cf579da38c487392e0ceb1cccf662"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_BASE_URL="http://localhost:8080"
BASE_HOST="localhost"
# BASE_HOST="192.168.43.15"
# APP_BASE_URL="http://192.168.43.15:8080"
