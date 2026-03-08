import redis
import json
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
CACHE_EXPIRATION = int(os.getenv("CACHE_EXPIRATION_SECONDS", 3600))

redis_client = redis.Redis(
    host = REDIS_HOST,
    port = REDIS_PORT,
    db = REDIS_DB,
    password = REDIS_PASSWORD,
    decode_responses = True
)

class RedisCache:

    def __init__(self, client = redis_client):
        self.client = client
        self.default_expiration = CACHE_EXPIRATION
    
    def get_link(self, short_code: str) -> Optional[Dict[str, Any]]:
        try:
            data = self.client.get(short_code)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error fetching from Redis: {e}")
            return None
    
    def set_link(self, short_code: str, link_data: Dict[str, Any], expiry:int=None):
        try:
            expiry = expiry or self.default_expiry
            self.client.setex(
                f"link:{short_code}",
                expiry,
                json.dumps(link_data, default=str)
            )
        except Exception as e:
            print(f"Error setting Redis cache: {e}")
    
    def delete_link(self, short_code: str):
        try:
            self.client.delete(f"link:{short_code}")
        except Exception as e:
            print(f"Error deleting from Redis: {e}")
    
    def increment_clicks(self, short_code: str):
        try:
            self.client.incr(f"clicks:{short_code}")
        except Exception as e:
            print(f"Error incrementing clicks in Redis: {e}")
            return 0
        
    def get_clicks(self, short_code: str) -> int:
        try:
            clicks = self.client.get(f"clicks:{short_code}")
            return int(clicks) if clicks else 0
        except Exception as e:
            print(f"Error fetching clicks from Redis: {e}")
            return 0
cache = RedisCache()