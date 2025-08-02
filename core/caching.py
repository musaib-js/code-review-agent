import redis
from core.config import REDIS_HOST, REDIS_PORT, REDIS_DB
import json

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)


def cache_result(task_id: str, result: dict):
    """Cache the result of a task in Redis.
    Args:
        task_id (str): Unique identifier for the task.
        result (dict): Result data to cache.
    """
    result = json.dumps(result)
    redis_client.set(task_id, result)
    
def get_cached_result(task_id: str):
    """Retrieve a cached result from Redis.
    Args:
        task_id (str): Unique identifier for the task.
    Returns:
        dict: Cached result data if found, otherwise None.
    """
    cached_result = redis_client.get(task_id)
    if cached_result:
        return json.loads(cached_result)
    return None