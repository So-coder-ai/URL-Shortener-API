import redis
import json
from typing import Optional, Dict, Any
from app.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


class RedisCache:
    CACHE_EXPIRY = 3600  # 1 hour
    
    @staticmethod
    def get_url_mapping(short_code: str) -> Optional[Dict[str, Any]]:
        """Get URL mapping from cache."""
        try:
            cached_data = redis_client.get(f"url:{short_code}")
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Redis get error: {e}")
        return None
    
    @staticmethod
    def set_url_mapping(short_code: str, url_data: Dict[str, Any]) -> bool:
        """Set URL mapping in cache."""
        try:
            redis_client.setex(
                f"url:{short_code}",
                RedisCache.CACHE_EXPIRY,
                json.dumps(url_data)
            )
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    @staticmethod
    def invalidate_url_cache(short_code: str) -> bool:
        """Remove URL mapping from cache."""
        try:
            redis_client.delete(f"url:{short_code}")
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    @staticmethod
    def get_analytics(short_code: str) -> Optional[Dict[str, Any]]:
        """Get analytics data from cache."""
        try:
            cached_data = redis_client.get(f"analytics:{short_code}")
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Redis analytics get error: {e}")
        return None
    
    @staticmethod
    def set_analytics(short_code: str, analytics_data: Dict[str, Any]) -> bool:
        """Set analytics data in cache."""
        try:
            redis_client.setex(
                f"analytics:{short_code}",
                300,  # 5 minutes cache for analytics
                json.dumps(analytics_data)
            )
            return True
        except Exception as e:
            print(f"Redis analytics set error: {e}")
            return False
