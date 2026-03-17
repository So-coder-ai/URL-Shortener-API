from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from app.models import URL, URLAnalytics
from app.schemas import URLCreate, URLResponse, URLStats, URLDetailResponse
from app.utils import generate_short_code, validate_custom_alias, is_valid_url
from app.redis_client import RedisCache
from app.config import settings


class URLService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_short_url(self, url_data: URLCreate) -> URLResponse:
        """Create a new shortened URL."""
        # Validate URL
        if not is_valid_url(str(url_data.original_url)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format"
            )
        
        # Handle custom alias
        short_code = url_data.custom_alias
        if short_code:
            if not validate_custom_alias(short_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid custom alias format"
                )
            
            # Check if custom alias already exists
            existing_url = self.db.query(URL).filter(
                (URL.short_code == short_code) | (URL.custom_alias == short_code)
            ).first()
            if existing_url:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Custom alias already exists"
                )
        else:
            # Generate unique short code
            max_attempts = 10
            for _ in range(max_attempts):
                short_code = generate_short_code()
                existing_url = self.db.query(URL).filter(
                    (URL.short_code == short_code) | (URL.custom_alias == short_code)
                ).first()
                if not existing_url:
                    break
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to generate unique short code"
                )
        
        # Create URL record
        db_url = URL(
            original_url=str(url_data.original_url),
            short_code=short_code,
            custom_alias=url_data.custom_alias if url_data.custom_alias else None,
            expires_at=url_data.expires_at
        )
        
        self.db.add(db_url)
        self.db.commit()
        self.db.refresh(db_url)
        
        # Cache the URL mapping
        url_mapping = {
            "original_url": db_url.original_url,
            "is_active": db_url.is_active,
            "expires_at": db_url.expires_at.isoformat() if db_url.expires_at else None
        }
        RedisCache.set_url_mapping(short_code, url_mapping)
        
        return URLResponse(
            id=db_url.id,
            original_url=db_url.original_url,
            short_code=db_url.short_code,
            custom_alias=db_url.custom_alias,
            short_url=f"{settings.base_url}/{short_code}",
            created_at=db_url.created_at,
            expires_at=db_url.expires_at,
            is_active=db_url.is_active,
            click_count=db_url.click_count
        )
    
    def get_url_by_short_code(self, short_code: str) -> Optional[URL]:
        """Get URL by short code, checking cache first."""
        # Try cache first
        cached_data = RedisCache.get_url_mapping(short_code)
        if cached_data:
            # Verify URL still exists and is active
            db_url = self.db.query(URL).filter(URL.short_code == short_code).first()
            if db_url and db_url.is_active and (not db_url.expires_at or db_url.expires_at > datetime.utcnow()):
                return db_url
            else:
                # Invalidate cache if URL is no longer valid
                RedisCache.invalidate_url_cache(short_code)
                return None
        
        # Query database
        db_url = self.db.query(URL).filter(URL.short_code == short_code).first()
        if db_url and db_url.is_active and (not db_url.expires_at or db_url.expires_at > datetime.utcnow()):
            # Cache the result
            url_mapping = {
                "original_url": db_url.original_url,
                "is_active": db_url.is_active,
                "expires_at": db_url.expires_at.isoformat() if db_url.expires_at else None
            }
            RedisCache.set_url_mapping(short_code, url_mapping)
            return db_url
        
        return None
    
    def track_click(self, short_code: str, ip_address: str, user_agent: str, referer: str) -> None:
        """Track URL click and update analytics."""
        db_url = self.db.query(URL).filter(URL.short_code == short_code).first()
        if not db_url:
            return
        
        # Update click count
        db_url.click_count += 1
        
        # Create analytics record
        analytics = URLAnalytics(
            url_id=db_url.id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            country=self._get_country_from_ip(ip_address),
            city=self._get_city_from_ip(ip_address)
        )
        
        self.db.add(analytics)
        self.db.commit()
        
        # Invalidate cache to force refresh
        RedisCache.invalidate_url_cache(short_code)
    
    def get_url_stats(self, short_code: str) -> Optional[URLStats]:
        """Get URL statistics."""
        # Try cache first
        cached_stats = RedisCache.get_analytics(short_code)
        if cached_stats:
            return URLStats(**cached_stats)
        
        db_url = self.db.query(URL).filter(URL.short_code == short_code).first()
        if not db_url:
            return None
        
        # Get last click time
        last_click = self.db.query(URLAnalytics).filter(
            URLAnalytics.url_id == db_url.id
        ).order_by(URLAnalytics.clicked_at.desc()).first()
        
        stats = URLStats(
            original_url=db_url.original_url,
            short_code=db_url.short_code,
            total_clicks=db_url.click_count,
            created_at=db_url.created_at,
            last_clicked=last_click.clicked_at if last_click else None
        )
        
        # Cache the stats
        RedisCache.set_analytics(short_code, stats.dict())
        
        return stats
    
    def get_url_detail(self, short_code: str) -> Optional[URLDetailResponse]:
        """Get detailed URL information with analytics."""
        db_url = self.db.query(URL).filter(URL.short_code == short_code).first()
        if not db_url:
            return None
        
        # Get analytics
        analytics = self.db.query(URLAnalytics).filter(
            URLAnalytics.url_id == db_url.id
        ).order_by(URLAnalytics.clicked_at.desc()).limit(100).all()
        
        return URLDetailResponse(
            id=db_url.id,
            original_url=db_url.original_url,
            short_code=db_url.short_code,
            custom_alias=db_url.custom_alias,
            short_url=f"{settings.base_url}/{short_code}",
            created_at=db_url.created_at,
            expires_at=db_url.expires_at,
            is_active=db_url.is_active,
            click_count=db_url.click_count,
            analytics=[URLAnalyticsResponse.from_orm(a) for a in analytics]
        )
    
    def _get_country_from_ip(self, ip_address: str) -> Optional[str]:
        """Get country from IP address using a geolocation service."""
        try:
            # This is a placeholder - in production, you'd use a service like ip-api.com
            # or MaxMind GeoIP2 database
            if ip_address in ['127.0.0.1', '::1']:
                return "US"
            return None
        except Exception:
            return None
    
    def _get_city_from_ip(self, ip_address: str) -> Optional[str]:
        """Get city from IP address using a geolocation service."""
        try:
            # This is a placeholder - in production, you'd use a service like ip-api.com
            # or MaxMind GeoIP2 database
            if ip_address in ['127.0.0.1', '::1']:
                return "Localhost"
            return None
        except Exception:
            return None
