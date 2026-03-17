from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class URL(Base):
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(50), unique=True, index=True, nullable=False)
    custom_alias = Column(String(50), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    click_count = Column(Integer, default=0)
    
    # Relationship with analytics
    analytics = relationship("URLAnalytics", back_populates="url", cascade="all, delete-orphan")


class URLAnalytics(Base):
    __tablename__ = "url_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)  # ISO 3166-1 alpha-2
    city = Column(String(100), nullable=True)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    url = relationship("URL", back_populates="analytics")
