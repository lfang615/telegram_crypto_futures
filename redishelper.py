import redis.asyncio as redis

class RedisHelper:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

    async def set_token(self, token: str):
        await self.redis.set(f"auth_token", token)

    async def get_token(self) -> str:
        return await self.redis.get(f"auth_token")
