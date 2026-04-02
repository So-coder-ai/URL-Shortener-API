# URL Shortener API

A scalable URL shortener built with FastAPI, PostgreSQL, Redis, and SQLAlchemy.

## Features

- **URL Shortening**: Generate short URLs from long URLs
- **Custom Aliases**: Create custom short codes
- **Analytics**: Track clicks, timestamps, and user information
- **Caching**: Redis caching for improved performance
- **Rate Limiting**: Prevent abuse with configurable rate limits
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Clean API Design**: RESTful API with proper HTTP status codes

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Reliable relational database
- **Redis**: In-memory data structure store for caching
- **SQLAlchemy**: Python SQL toolkit and ORM
- **Alembic**: Database migration tool
- **SlowAPI**: Rate limiting for FastAPI
- **Docker**: Containerization

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run with Docker Compose:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL and Redis
3. Configure environment variables in `.env`
4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Create Short URL
```http
POST /shorten
Content-Type: application/json

{
  "original_url": "https://example.com/very/long/url",
  "custom_alias": "my-custom-alias",  // optional
  "expires_at": "2024-12-31T23:59:59Z"  // optional
}
```

### Redirect to Original URL
```http
GET /{short_code}
```

### Get URL Statistics
```http
GET /stats/{short_code}
```

### Get Detailed URL Information
```http
GET /detail/{short_code}
```

### Health Check
```http
GET /health
```

## Configuration

Environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `BASE_URL`: Base URL for generating short URLs
- `SHORT_CODE_LENGTH`: Default length for generated short codes
- `RATE_LIMIT_REQUESTS`: Number of requests allowed per window
- `RATE_LIMIT_WINDOW`: Time window for rate limiting (seconds)

## Database Schema

### URLs Table
- `id`: Primary key
- `original_url`: The original long URL
- `short_code`: Generated short code
- `custom_alias`: Optional custom alias
- `created_at`: Creation timestamp
- `expires_at`: Optional expiration date
- `is_active`: Whether the URL is active
- `click_count`: Total number of clicks

### URL Analytics Table
- `id`: Primary key
- `url_id`: Foreign key to URLs table
- `ip_address`: Visitor's IP address
- `user_agent`: Visitor's browser info
- `referer`: Referer header
- `country`: Visitor's country (if available)
- `city`: Visitor's city (if available)
- `clicked_at`: Click timestamp

## Rate Limiting

- Default: 100 requests per minute per IP
- Stricter limits for analytics endpoints
- Configurable via environment variables

## Caching Strategy

- URL mappings cached in Redis (1 hour TTL)
- Analytics data cached (5 minutes TTL)
- Cache invalidation on updates

## Development

### Running Tests
```bash
# Add test commands here
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Production Considerations

- Use HTTPS in production
- Configure proper CORS settings
- Set up monitoring and logging
- Use environment-specific configurations
- Consider using a reverse proxy (Nginx)
- Implement proper backup strategies

