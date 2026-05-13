# -*- coding: utf-8 -*-
"""
带有 Redis 缓存的推荐服务
实现分批次生成推荐数据，并使用 Redis 缓存
支持 FastAPI BackgroundTasks
"""
import json
import asyncio
import threading
from typing import List, Dict, Any, Optional

import redis

from backend.core.redis import rt
from backend.sc_utils.recommend_3 import HybridMultimodalRecommender

# Redis 键名前缀
REDIS_RECOMMEND_PREFIX = "recommend:user:"

# 缓存配置
MIN_CACHE_SIZE = 30  # 最小缓存数量，低于此值触发后台补充
BATCH_SIZE = 30      # 每次生成的批次大小
CACHE_TTL = 3600     # 缓存过期时间（秒）


class CachedRecommender:
    """带有 Redis 缓存的推荐器"""

    def __init__(self):
        self.redis_client = rt
        self.recommender = HybridMultimodalRecommender()
        self.generation_lock = threading.Lock()

    def _get_cache_key(self, user_id: int) -> str:
        """获取用户推荐缓存的键名"""
        return f"{REDIS_RECOMMEND_PREFIX}{user_id}"

    def _get_cached_count(self, user_id: int) -> int:
        """获取缓存中推荐数据的数量"""
        cache_key = self._get_cache_key(user_id)
        try:
            return self.redis_client.llen(cache_key)
        except Exception as e:
            print(f"Error getting cached count for user {user_id}: {e}")
            return 0

    def _push_recommendations(self, user_id: int, recommendations: List[Dict[str, Any]]):
        """向 Redis 列表尾部添加推荐数据"""
        cache_key = self._get_cache_key(user_id)
        try:
            pipeline = self.redis_client.pipeline()
            for rec in recommendations:
                pipeline.rpush(cache_key, json.dumps(rec))
            pipeline.expire(cache_key, CACHE_TTL)
            pipeline.execute()
        except Exception as e:
            print(f"Error pushing recommendations to cache for user {user_id}: {e}")

    def _pop_recommendations(self, user_id: int, count: int) -> List[Dict[str, Any]]:
        """从 Redis 列表头部取出指定数量的推荐数据"""
        cache_key = self._get_cache_key(user_id)
        results = []
        try:
            for _ in range(count):
                item = self.redis_client.lpop(cache_key)
                if item:
                    results.append(json.loads(item))
                else:
                    break

            # 刷新过期时间
            self.redis_client.expire(cache_key, CACHE_TTL)
        except Exception as e:
            print(f"Error popping recommendations from cache for user {user_id}: {e}")

        return results

    def _generate_batch(self, user_id: int, batch_size: int = BATCH_SIZE) -> List[Dict[str, Any]]:
        """生成一批推荐数据"""
        try:
            recommendations = self.recommender.recommend(user_id, top_k=batch_size)
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations for user {user_id}: {e}")
            return []

    def background_refill_cache(self, user_id: int, target_count: int = MIN_CACHE_SIZE):
        """
        后台任务：生成推荐数据并填充到缓存
        此方法设计为可被 FastAPI BackgroundTasks 调用
        """
        with self.generation_lock:
            current_count = self._get_cached_count(user_id)
            if current_count >= target_count:
                return  # 已有足够数据

            needed = target_count - current_count

            # 按需生成，只生成需要的数量
            recommendations = self._generate_batch(user_id, needed)
            if recommendations:
                self._push_recommendations(user_id, recommendations)

    def get_recommendations(self, user_id: int, count: int = 15) -> List[Dict[str, Any]]:
        """
        获取推荐数据（同步版本）
        :param user_id: 用户ID
        :param count: 需要的推荐数量
        :return: 推荐结果列表
        """
        # 1. 获取缓存中的数据（会从Redis删除）
        results = self._pop_recommendations(user_id, count)

        # 2. 如果缓存数据不足，生成新数据
        if len(results) < count:
            needed = count - len(results)
            # 生成当前请求所需的数量 + 额外储备数量（用于填充缓存）
            total_to_generate = needed + BATCH_SIZE
            additional = self._generate_batch(user_id, total_to_generate)

            if additional:
                # 返回给用户的数据（优先使用刚生成的数据）
                results.extend(additional[:needed])

                # 将额外生成的数据存入缓存（供后续请求使用）
                if len(additional) > needed:
                    cache_data = additional[needed:]
                    self._push_recommendations(user_id, cache_data)

        return results[:count]

    def get_cached_count(self, user_id: int) -> int:
        """获取当前缓存数量（供外部判断是否需要触发后台任务）"""
        return self._get_cached_count(user_id)


# 全局推荐器实例
cached_recommender = CachedRecommender()


def get_recommendations(user_id: int, count: int = 15) -> List[Dict[str, Any]]:
    """
    获取推荐结果（同步版本）
    :param user_id: 用户ID
    :param count: 需要的推荐数量
    :return: 推荐结果列表
    """
    return cached_recommender.get_recommendations(user_id, count)


def get_current_cache_count(user_id: int) -> int:
    """
    获取当前缓存数量
    :param user_id: 用户ID
    :return: 缓存中的推荐数量
    """
    return cached_recommender.get_cached_count(user_id)


def refill_cache_task(user_id: int):
    """
    后台填充缓存任务（供 FastAPI BackgroundTasks 调用）
    :param user_id: 用户ID
    """
    cached_recommender.background_refill_cache(user_id, MIN_CACHE_SIZE)
