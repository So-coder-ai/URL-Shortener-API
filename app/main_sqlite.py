from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.database import get_db, engine
from app.models import Base, URL
from app.schemas import URLCreate, URLResponse, URLStats, URLDetailResponse
from app.services import URLService
from app.config_sqlite import settings  # Use SQLite config

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description="A scalable URL shortener with analytics and caching",
    version="1.0.0"
)

# Add rate limiting middleware
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.post("/shorten", response_model=URLResponse)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def create_short_url(
    request: Request,
    url_data: URLCreate,
    db: Session = Depends(get_db)
):
    """Create a shortened URL."""
    service = URLService(db)
    response = service.create_short_url(url_data)
    return response


@app.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Redirect to original URL and track analytics."""
    service = URLService(db)
    url = service.get_url_by_short_code(short_code)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found or expired"
        )
    
    # Track analytics
    service.track_click(
        short_code=short_code,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent", ""),
        referer=request.headers.get("referer", "")
    )
    
    return RedirectResponse(url.original_url, status_code=status.HTTP_302_FOUND)


@app.get("/stats/{short_code}", response_model=URLStats)
@limiter.limit("10/minute")
async def get_url_stats(
    request: Request,
    short_code: str,
    db: Session = Depends(get_db)
):
    """Get URL statistics."""
    service = URLService(db)
    stats = service.get_url_stats(short_code)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found"
        )
    
    return stats


@app.get("/detail/{short_code}", response_model=URLDetailResponse)
@limiter.limit("5/minute")
async def get_url_detail(
    request: Request,
    short_code: str,
    db: Session = Depends(get_db)
):
    """Get detailed URL information with analytics."""
    service = URLService(db)
    detail = service.get_url_detail(short_code)
    
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found"
        )
    
    return detail


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "URL Shortener API",
        "version": "1.0.0",
        "endpoints": {
            "create": "POST /shorten",
            "redirect": "GET /{short_code}",
            "stats": "GET /stats/{short_code}",
            "detail": "GET /detail/{short_code}",
            "health": "GET /health"
        }
    }
