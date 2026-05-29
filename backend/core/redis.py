import redis
from redis import ConnectionPool

# 如果 Redis 设置了密码，请修改此处
REDIS_PASSWORD = ""  # 与 docker-compose.yml 中的密码一致

pool = ConnectionPool(
    host="127.0.0.1",
    port=6379,
    # password=REDIS_PASSWORD,
    decode_responses=True  # 自动解码响应为字符串
)
rt = redis.Redis(connection_pool=pool)
