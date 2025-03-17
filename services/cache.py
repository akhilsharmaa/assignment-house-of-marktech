import json
from redis.asyncio import Redis

redis_client = Redis(host="localhost", port=6379, decode_responses=True)

async def get_cache(key: str):
    cached_data = await redis_client.get(key)
    if cached_data:
        return json.loads(cached_data)
    return None

async def set_cache(key: str, value: dict):
    await redis_client.set(key, json.dumps(value))

async def clear_cache(key: str):
    await redis_client.delete(key)

async def get_id_list():
    id_list = await redis_client.lrange("task_ids", 0, -1)
    return [int(task_id) for task_id in id_list]

async def add_to_id_list(task_id: int):
    await redis_client.rpush("task_ids", task_id)

async def remove_from_id_list(task_id: int):
    await redis_client.lrem("task_ids", 0, str(task_id))