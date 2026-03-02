from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from .database import Base
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import relationship

Base = declarative_base()
class Link(Base):

    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(10), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    clicks_count = Column(Integer, default=0)
    clicks = relationship("Click", back_populates="link",
                          cascade="all, delete-orphan")

class Click(Base):

    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id", ondelete="CASCADE"),nullable=False )
    timestamp = Column(DateTime(timezone=True), server_defaut=func.now())
    user_agent = Column(String(255))
    referer = Column(String(255))
    link = relationship("Link", back_populates="clicks")
