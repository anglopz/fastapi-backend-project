import redis.asyncio as redis  # type: ignore
import os
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_redis_client = None


async def get_redis() -> redis.Redis:
    """Obtener cliente Redis"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        try:
            await _redis_client.ping()
            print("✅ Conectado a Redis")
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
            raise
    return _redis_client


async def close_redis():
    """Cerrar conexión Redis"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def set_cache(key: str, value: str, expire_seconds: int = 3600):
    """Guardar en cache"""
    client = await get_redis()
    await client.setex(key, expire_seconds, value)


async def get_cache(key: str) -> Optional[str]:
    """Obtener de cache"""
    client = await get_redis()
    return await client.get(key)


async def delete_cache(key: str):
    """Eliminar de cache"""
    client = await get_redis()
    await client.delete(key)

# Funciones para blacklist de tokens (logout system)
async def add_to_blacklist(jti: str, expires_in: int = 86400) -> None:
    """Añade un JTI a la blacklist para invalidar token (logout)"""
    redis_client = await get_redis()
    await redis_client.setex(f"token:blacklist:{jti}", expires_in, "1")

async def is_blacklisted(jti: str) -> bool:
    """Verifica si un JTI está en la blacklist"""
    redis_client = await get_redis()
    result = await redis_client.get(f"token:blacklist:{jti}")
    return result is not None
