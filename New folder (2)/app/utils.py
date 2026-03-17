import random
import string
import hashlib
from typing import Optional
from app.config import settings


def generate_short_code(length: Optional[int] = None) -> str:
    """Generate a random short code for URL."""
    if length is None:
        length = settings.short_code_length
    
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def hash_url(url: str) -> str:
    """Create a hash of the URL for potential deduplication."""
    return hashlib.md5(url.encode()).hexdigest()


def validate_custom_alias(alias: str) -> bool:
    """Validate custom alias format."""
    if not alias or len(alias) < 3 or len(alias) > 50:
        return False
    
    # Only allow alphanumeric characters, hyphens, and underscores
    allowed_chars = set(string.ascii_letters + string.digits + '-_')
    return all(c in allowed_chars for c in alias)


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    url = url.strip()
    return url.startswith(('http://', 'https://')) and '.' in url
