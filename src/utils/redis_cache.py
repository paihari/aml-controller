"""
Redis caching utility for API calls
"""
import json
import os
import redis
import hashlib
from typing import Any, Optional, Dict
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis caching wrapper for API responses"""
    
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"✅ Redis cache connected: {redis_url}")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, caching disabled: {e}")
            self.redis_client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate cache key from prefix and parameters"""
        # Create consistent string from parameters
        param_string = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_string.encode()).hexdigest()[:8]
        return f"{prefix}:{param_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
            
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds"""
        if not self.enabled:
            return False
            
        try:
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def delete(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self.enabled:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
        return 0
    
    def cache_api_call(self, cache_key_prefix: str, params: Dict[str, Any], 
                      api_function, ttl: int = 3600):
        """
        Wrapper for caching API calls
        
        Args:
            cache_key_prefix: Prefix for cache key
            params: Parameters dict to generate unique key
            api_function: Function to call if cache miss
            ttl: Time to live in seconds (default 1 hour)
        """
        cache_key = self._generate_key(cache_key_prefix, params)
        
        # Try cache first
        cached_result = self.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached_result
        
        # Cache miss - call API
        logger.debug(f"Cache MISS: {cache_key}")
        try:
            result = api_function()
            if result is not None:
                self.set(cache_key, result, ttl)
            return result
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise

# Global cache instance
cache = RedisCache()

def cached_opensanctions_request(url: str, ttl: int = 1800):
    """
    Cache OpenSanctions API requests for 30 minutes
    
    Args:
        url: API URL to request
        ttl: Cache time in seconds (default 30 minutes)
    """
    def make_request():
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    
    return cache.cache_api_call(
        cache_key_prefix="opensanctions",
        params={"url": url},
        api_function=make_request,
        ttl=ttl
    )

def cached_supabase_query(table: str, query_params: Dict[str, Any], 
                         query_function, ttl: int = 300):
    """
    Cache Supabase queries for 5 minutes
    
    Args:
        table: Table name
        query_params: Query parameters
        query_function: Function that executes the query
        ttl: Cache time in seconds (default 5 minutes)
    """
    return cache.cache_api_call(
        cache_key_prefix=f"supabase:{table}",
        params=query_params,
        api_function=query_function,
        ttl=ttl
    )

def clear_cache(pattern: str = "*") -> int:
    """Clear cache entries matching pattern"""
    return cache.delete(pattern)