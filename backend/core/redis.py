import redis
from redis import ConnectionPool

pool = ConnectionPool(host="127.0.0.1", port=6379)
rt = redis.Redis(connection_pool=pool)
