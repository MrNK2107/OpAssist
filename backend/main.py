from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from api import opportunities, profiles, bookmarks, applications, scraping, ai, communities, notifications


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("OpAssist starting up...")
    try:
        from scheduler.jobs import start_scheduler
        start_scheduler(settings.scrape_interval_hours)
        print(f"Scheduler started (scrape every {settings.scrape_interval_hours}h)")
    except Exception as exc:
        print(f"Scheduler failed to start: {exc}")
    yield
    # Shutdown
    try:
        from scheduler.jobs import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
    print("OpAssist shutting down...")


app = FastAPI(
    title="OpAssist API",
    description="All-in-one opportunity discovery platform for university students",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - use environment-based origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Only add HSTS in production (not localhost)
    if "localhost" not in str(request.url):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Simple rate limiting using a dict (for production, use Redis)
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100  # per window
AI_RATE_LIMIT_MAX = 20  # stricter for AI endpoints
_cleanup_counter = 0


def _check_rate_limit(client_ip: str, endpoint_type: str = "default") -> bool:
    """Check if request is within rate limit. Returns True if allowed."""
    import time
    global _cleanup_counter
    now = time.time()
    key = f"{client_ip}:{endpoint_type}"

    if key not in _rate_limit_store:
        _rate_limit_store[key] = []

    # Clean old entries
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < RATE_LIMIT_WINDOW]

    # Periodic cleanup of stale keys (every 1000 requests)
    _cleanup_counter += 1
    if _cleanup_counter >= 1000:
        _cleanup_counter = 0
        stale_keys = [k for k, v in _rate_limit_store.items() if not v]
        for k in stale_keys:
            del _rate_limit_store[k]

    max_req = AI_RATE_LIMIT_MAX if endpoint_type == "ai" else RATE_LIMIT_MAX_REQUESTS
    if len(_rate_limit_store[key]) >= max_req:
        return False

    _rate_limit_store[key].append(now)
    return True


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health check
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    endpoint_type = "ai" if "/api/ai/" in request.url.path else "default"

    if not _check_rate_limit(client_ip, endpoint_type):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
        )

    return await call_next(request)


# Global exception handler to prevent stack trace leaks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
app.include_router(profiles.router, prefix="/api/profile", tags=["profile"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(scraping.router, prefix="/api/scrape", tags=["scraping"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(communities.router, prefix="/api/communities", tags=["communities"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])


@app.get("/")
async def root():
    return {"message": "OpAssist API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
