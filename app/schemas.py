from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class LinkBase(BaseModel):
    original_url : str

class LinkCreate(LinkBase):
    custom_code : Optional[str] = None

class Link(LinkBase):
    id : int
    short_code : str
    created_at : datetime
    clicks_count : int

    class Config:
        orm_mode = True

class ClickBase(BaseModel):
    ip_address : Optional[str] = None
    user_agent : Optional[str] = None
    referer : Optional[str] = None

class Click(ClickBase):
    id : int
    timestamp : datetime
    link_id : int

    class Config:
        orm_mode = True

class LinkStats(Link):
    clicks : List[Click] 