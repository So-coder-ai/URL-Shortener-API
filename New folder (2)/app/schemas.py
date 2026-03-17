from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional, List


class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None


class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    custom_alias: Optional[str]
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    click_count: int
    
    class Config:
        from_attributes = True


class URLStats(BaseModel):
    original_url: str
    short_code: str
    total_clicks: int
    created_at: datetime
    last_clicked: Optional[datetime]
    
    class Config:
        from_attributes = True


class URLAnalyticsResponse(BaseModel):
    id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    referer: Optional[str]
    country: Optional[str]
    city: Optional[str]
    clicked_at: datetime
    
    class Config:
        from_attributes = True


class URLDetailResponse(URLResponse):
    analytics: List[URLAnalyticsResponse] = []
