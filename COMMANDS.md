# OpAssist Commands

## Quick Start

```bash
start.bat              # Windows: install deps + setup
python -m scripts.run_scraper  # Run all scrapers
```

---

## Backend

### Run the server

```bash
cd backend
uvicorn main:app --reload          # Dev server (auto-restart on changes)
uvicorn main:app --host 0.0.0.0 --port 8000  # Production
```

### Scrapers

```bash
python scripts/run_scraper.py              # Run ALL scrapers
python scripts/run_scraper.py --source devfolio  # Run one source
python scripts/run_scraper.py --list       # List available sources
```

**API endpoints (triggered remotely):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scrape/trigger` | Trigger full scrape |
| GET | `/api/scrape/status` | Scrape status & last run info |
| GET | `/api/scrape/sources` | List sources & their config |
| POST | `/api/scrape/source/{name}/toggle?enabled=true` | Enable/disable a source |

### Database

```bash
python -c "from services.scraper_service import delete_expired; print(delete_expired())"   # Clean expired entries
python -c "from services.scraper_service import deduplicate_opportunities; print(deduplicate_opportunities())"  # Deduplicate
```

### Tests

```bash
cd backend
pytest                          # All tests
pytest -v                       # Verbose
pytest tests/test_services.py   # Specific file
pytest -k "scraper"             # Filter by keyword
```

---

## Frontend

```bash
cd frontend
npm run dev          # Dev server (http://localhost:3000)
npm run build        # Production build
npm run lint         # Lint check
npm run typecheck    # TypeScript check
npx next lint        # ESLint
```

---

## Root-level commands (from project root)

```bash
npm run dev:backend      # Start backend dev server
npm run dev:frontend     # Start frontend dev server
npm run build:frontend   # Build frontend
npm run lint:frontend    # Lint frontend
npm run typecheck:frontend  # TypeScript check frontend
```

---

## Docker

```bash
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose logs -f        # Follow logs
```

---

## Useful Python one-liners

```bash
# Inside backend/ directory:

# Check API health
curl http://localhost:8000/health

# Trigger scrape via API
curl -X POST http://localhost:8000/api/scrape/trigger

# Check scrape status
curl http://localhost:8000/api/scrape/status

# Get profile
curl http://localhost:8000/api/profile -H "Authorization: Bearer <token>"
```
