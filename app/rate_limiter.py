from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from app.config import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_headers() -> dict:
    """Get rate limit headers for responses."""
    return {
        "X-RateLimit-Limit": str(settings.rate_limit_requests),
        "X-RateLimit-Window": str(settings.rate_limit_window),
        "X-RateLimit-Remaining": "0",  # This would be calculated dynamically
    }
