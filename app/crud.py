from sqlalchemy.orm import Session
from models import Link, Click
import schemas
import random
import string

def create_short_code(db: Session, custom_code: str = None) -> str:
    if custom_code:
        existing = db.query(Link).filter(Link.short_code == custom_code).first()
        if existing:
            raise ValueError("Short code already exists")
        return custom_code
    
    chars = string.ascii_letters + string.digits
    while True:
        short_code = ''.join(random.choices(chars, k=6))
        if not db.query(Link).filter(Link.short_code == short_code).first():
            return short_code

def create_link(db: Session, link: schemas.LinkCreate):
    short_code = create_short_code(db, link.custom_code)
    # Fix: Use original_url field name
    db_link = Link(short_code=short_code, original_url=link.original_url)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def get_link_by_code(db: Session, short_code: str):
    return db.query(Link).filter(Link.short_code == short_code).first()

def create_click(db: Session, link_id: int, click_data: schemas.ClickBase):
    db_click = Click(link_id=link_id, **click_data.dict())
    db.add(db_click)
    db.query(Link).filter(Link.id == link_id).update({"clicks_count": Link.clicks_count + 1})
    db.commit()
    db.refresh(db_click)  # Fix: Fixed typo from 'referesh' to 'refresh'
    return db_click

def get_link_stats(db: Session, short_code: str):  # CORRECT - using short_code
    return db.query(Link).filter(Link.short_code == short_code).first()

from cache_utils import invalidate_link_cache

def update_link(db: Session, short_code: str, new_url: str):
    """Example of updating a link (if you add this feature)"""
    link = get_link_by_code(db, short_code)
    if link:
        link.original_url = new_url
        db.commit()
        db.refresh(link)
        # Invalidate cache
        invalidate_link_cache(short_code)
        return link
    return None