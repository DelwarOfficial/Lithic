"""Multi-tier caching system with Redis backend support."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any, Dict, Optional, Union

_log = logging.getLogger("lithic_cli.caching")


class CacheBackend(ABC):
    """Abstract cache backend interface."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        """Get value by key."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        """Set key-value pair with optional TTL."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all keys."""
        pass
    
    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check backend health."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory LRU cache backend."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: list[str] = []
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            # Check TTL
            entry = self._cache[key]
            if entry['expires'] and time.time() > entry['expires']:
                del self._cache[key]
                self._access_order.remove(key)
                self._misses += 1
                return None
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self._hits += 1
            return entry['value']
    
    def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        with self._lock:
            expires = time.time() + ttl if ttl else None
            
            self._cache[key] = {
                'value': value,
                'created': time.time(),
                'expires': expires
            }
            
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            # Evict oldest if over limit
            while len(self._cache) > self.max_size:
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
            
            return True
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return True
            return False
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def clear(self) -> bool:
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            return True
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "type": "memory",
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "total_memory_mb": sum(
                    len(entry['value']) for entry in self._cache.values()
                ) / (1024 * 1024)
            }
    
    def health_check(self) -> Dict[str, Any]:
        return {"healthy": True, "backend": "memory", "size": len(self._cache)}


class RedisCacheBackend(CacheBackend):
    """Redis cache backend with connection pooling."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: Optional[str] = None, 
                 key_prefix: str = "lithic:"):
        self.host = host
        self.port = port  
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self._redis = None
        self._connected = False
        
        try:
            import redis
            self._redis = redis.Redis(
                host=host, port=port, db=db, password=password,
                decode_responses=False, socket_timeout=5, socket_connect_timeout=5
            )
            # Test connection
            self._redis.ping()
            self._connected = True
            _log.info(f"Connected to Redis at {host}:{port}")
        except ImportError:
            _log.warning("Redis not installed, falling back to memory cache")
        except Exception as e:
            _log.warning(f"Redis connection failed: {e}, falling back to memory cache")
            self._redis = None
    
    def _key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Optional[bytes]:
        if not self._redis:
            return None
        
        try:
            return self._redis.get(self._key(key))
        except Exception as e:
            _log.warning(f"Redis get failed: {e}")
            return None
    
    def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        if not self._redis:
            return False
        
        try:
            return self._redis.set(self._key(key), value, ex=ttl)
        except Exception as e:
            _log.warning(f"Redis set failed: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        if not self._redis:
            return False
        
        try:
            return bool(self._redis.delete(self._key(key)))
        except Exception as e:
            _log.warning(f"Redis delete failed: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        if not self._redis:
            return False
        
        try:
            return bool(self._redis.exists(self._key(key)))
        except Exception as e:
            _log.warning(f"Redis exists failed: {e}")
            return False
    
    def clear(self) -> bool:
        if not self._redis:
            return False
        
        try:
            # Delete all keys with our prefix
            keys = self._redis.keys(f"{self.key_prefix}*")
            if keys:
                self._redis.delete(*keys)
            return True
        except Exception as e:
            _log.warning(f"Redis clear failed: {e}")
            return False
    
    def stats(self) -> Dict[str, Any]:
        if not self._redis:
            return {"type": "redis", "connected": False}
        
        try:
            info = self._redis.info()
            keys = len(self._redis.keys(f"{self.key_prefix}*"))
            
            return {
                "type": "redis",
                "connected": self._connected,
                "keys": keys,
                "memory_usage_mb": info.get("used_memory", 0) / (1024 * 1024),
                "hit_rate": info.get("keyspace_hit_rate", 0),
                "connections": info.get("connected_clients", 0)
            }
        except Exception as e:
            _log.warning(f"Redis stats failed: {e}")
            return {"type": "redis", "connected": False, "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        if not self._redis:
            return {"healthy": False, "backend": "redis", "error": "Not connected"}
        
        try:
            self._redis.ping()
            return {"healthy": True, "backend": "redis", "host": self.host, "port": self.port}
        except Exception as e:
            return {"healthy": False, "backend": "redis", "error": str(e)}


class MultiTierCache:
    """Multi-tier cache with L1 (memory) and L2 (Redis/disk) backends."""
    
    def __init__(self, l1_size: int = 1000, enable_redis: bool = True):
        self.l1 = MemoryCacheBackend(l1_size)
        
        # Try to initialize L2 (Redis or disk)
        self.l2: Optional[CacheBackend] = None
        if enable_redis:
            redis_config = self._get_redis_config()
            if redis_config:
                self.l2 = RedisCacheBackend(**redis_config)
                if not self.l2._connected:
                    self.l2 = None
        
        self._hits_l1 = 0
        self._hits_l2 = 0
        self._misses = 0
        self._lock = Lock()
    
    def _get_redis_config(self) -> Optional[Dict[str, Any]]:
        """Get Redis configuration from environment."""
        redis_url = os.getenv("REDIS_URL") or os.getenv("LITHIC_REDIS_URL")
        if redis_url:
            # Parse redis://localhost:6379/0 format
            import urllib.parse
            parsed = urllib.parse.urlparse(redis_url)
            return {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 6379,
                "db": int(parsed.path.lstrip('/')) if parsed.path else 0,
                "password": parsed.password
            }
        
        # Individual config options
        host = os.getenv("LITHIC_REDIS_HOST", "localhost")
        port = int(os.getenv("LITHIC_REDIS_PORT", "6379"))
        db = int(os.getenv("LITHIC_REDIS_DB", "0"))
        password = os.getenv("LITHIC_REDIS_PASSWORD")
        
        return {"host": host, "port": port, "db": db, "password": password}
    
    def get(self, key: str) -> Optional[str]:
        """Get value with multi-tier lookup."""
        # Try L1 first
        value = self.l1.get(key)
        if value:
            with self._lock:
                self._hits_l1 += 1
            return value.decode('utf-8')
        
        # Try L2 if available
        if self.l2:
            value = self.l2.get(key)
            if value:
                # Promote to L1
                self.l1.set(key, value, ttl=3600)  # 1 hour in L1
                with self._lock:
                    self._hits_l2 += 1
                return value.decode('utf-8')
        
        with self._lock:
            self._misses += 1
        return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in both tiers."""
        value_bytes = value.encode('utf-8')
        
        # Set in L1 (shorter TTL)
        l1_ttl = min(ttl or 3600, 3600)  # Max 1 hour in L1
        self.l1.set(key, value_bytes, ttl=l1_ttl)
        
        # Set in L2 if available (longer TTL)  
        if self.l2:
            l2_ttl = ttl or 86400  # Default 24 hours in L2
            return self.l2.set(key, value_bytes, ttl=l2_ttl)
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete from both tiers."""
        l1_result = self.l1.delete(key)
        l2_result = self.l2.delete(key) if self.l2 else True
        return l1_result or l2_result
    
    def clear(self) -> bool:
        """Clear both tiers."""
        l1_result = self.l1.clear()
        l2_result = self.l2.clear() if self.l2 else True
        return l1_result and l2_result
    
    def content_hash(self, content: str, algorithm: str = "default") -> str:
        """Generate content-addressed cache key."""
        # Include algorithm version in hash for cache invalidation
        hashable = f"{content}:{algorithm}:v1"
        return hashlib.sha256(hashable.encode()).hexdigest()[:16]
    
    def stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            total_requests = self._hits_l1 + self._hits_l2 + self._misses
            hit_rate = (self._hits_l1 + self._hits_l2) / total_requests if total_requests > 0 else 0
            
            stats = {
                "hit_rate": hit_rate,
                "hits_l1": self._hits_l1,
                "hits_l2": self._hits_l2, 
                "misses": self._misses,
                "l1_stats": self.l1.stats(),
                "l2_stats": self.l2.stats() if self.l2 else None,
                "l2_available": self.l2 is not None
            }
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all cache tiers."""
        return {
            "l1": self.l1.health_check(),
            "l2": self.l2.health_check() if self.l2 else {"healthy": False, "backend": "none"}
        }


# Global cache instance
_global_cache: Optional[MultiTierCache] = None


def get_cache() -> MultiTierCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiTierCache()
    return _global_cache