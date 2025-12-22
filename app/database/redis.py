"""
Redis client and token blacklist management
"""
from redis.asyncio import Redis

from app.config import db_settings


# Token blacklist Redis client (separate from cache)
_token_blacklist = Redis(
    host=db_settings.REDIS_HOST,
    port=int(db_settings.REDIS_PORT),
    db=0,
    decode_responses=True,
)

# Cache Redis client (for backward compatibility)
_cache_client = None


async def get_redis():
    """Get Redis client for cache (backward compatibility)"""
    global _cache_client
    if _cache_client is None:
        from redis.asyncio import Redis as AsyncRedis
        _cache_client = AsyncRedis(
            host=db_settings.REDIS_HOST,
            port=int(db_settings.REDIS_PORT),
            db=1,  # Use different DB for cache
            decode_responses=True,
        )
        try:
            await _cache_client.ping()
            print("✅ Connected to Redis (cache)")
        except Exception as e:
            print(f"❌ Error connecting to Redis: {e}")
            raise
    return _cache_client


async def close_redis():
    """Close Redis connections"""
    global _cache_client
    if _cache_client:
        await _cache_client.close()
        _cache_client = None
    await _token_blacklist.close()


# Cache functions (backward compatibility)
async def set_cache(key: str, value: str, expire_seconds: int = 3600):
    """Save to cache"""
    client = await get_redis()
    await client.setex(key, expire_seconds, value)


async def get_cache(key: str) -> str | None:
    """Get from cache"""
    client = await get_redis()
    return await client.get(key)


async def delete_cache(key: str):
    """Delete from cache"""
    client = await get_redis()
    await client.delete(key)


# Token blacklist functions (new API from Section 16)
async def add_jti_to_blacklist(jti: str) -> None:
    """Add a JTI to the blacklist to invalidate token (logout)"""
    await _token_blacklist.set(jti, "blacklisted")


async def is_jti_blacklisted(jti: str) -> bool:
    """Check if a JTI is in the blacklist"""
    return await _token_blacklist.exists(jti) > 0


# Backward compatibility aliases (deprecated)
async def add_to_blacklist(jti: str, expires_in: int = 86400) -> None:
    """Deprecated: Use add_jti_to_blacklist instead"""
    await add_jti_to_blacklist(jti)


async def is_blacklisted(jti: str) -> bool:
    """Deprecated: Use is_jti_blacklisted instead"""
    return await is_jti_blacklisted(jti)
