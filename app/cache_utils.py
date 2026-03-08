from typing import Optional, Dict, Any
from django import db
from models import Link
from sqlalchemy.orm import Session
import json
from datetime import datetime
from redis_config import cache

def link_to_dict(link: Link)-> Dict[str, Any]:
    return {
        "id" : link.id,
        "short_code" : link.short_code,
        "url" : link.original_url,
        "created_at" : link.created_at.isoformat() if link.created_at else None,
        "clicks_count" : link.clicks_count
    }

def dict_to_link(data : Dict[str, Any]) -> Optional[Link]:
    if not data:
        return None
    
    link = Link()
    link.id = data.get("id")
    link.short_code = data.get("short_code")
    link.original_url = data.get("original_url")
    link.clicks_count = data.get("clicks_count", 0)

    if data.get("created_at"):
        try:
            link.created_at = datetime.fromisoformat(data["created_at"])
        except:
            link.created_at = None
    return link

async def get_cached_link(short_code: str) -> Optional[Link]:
    cached_data = cache.get_link(short_code)
    if cached_data:
        print(f"Cache hit for {short_code}")
        link = dict_to_link(cached_data)
        if link:
            return link
    print(f"Cache miss for {short_code}")
    from crud import get_link_by_code
    link = get_link_by_code(db, short_code)

    if link:
        cache.set_link(short_code, link_to_dict(link))
    
    return link

def invalidate_cache(short_code: str):
    cache.delete_link(short_code)
    print(f"Cache invalidated for {short_code}")