# OpAssist - Implementation Plan

> Based on research from: CareerPulse (tcpsyn/CareerPulse) + find-a-thon (MrNK2107/find-a-thon)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OpAssist Architecture                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐       │
│  │   Frontend      │    │   FastAPI       │    │   Supabase      │       │
│  │   Next.js 16    │◄──►│   Scraper API   │◄──►│   PostgreSQL    │       │
│  │   (App Router)  │    │   (Port 8000)   │    │   (Auth + DB)   │       │
│  └────────┬────────┘    └────────┬────────┘    └─────────────────┘       │
│           │                      │                                         │
│           │                      │                                         │
│  ┌────────▼────────┐    ┌────────▼────────┐                                │
│  │   Client       │    │   Scrapers     │                                │
│  │   Components   │    │   (from find-   │                                │
│  │   shadcn/ui    │    │    a-thon)     │                                │
│  └─────────────────┘    └─────────────────┘                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    Background Jobs (APScheduler)               │        │
│  │  • Scrape: Every 6 hours                                       │        │
│  │  • Enrichment: Every 2 hours                                   │        │
│  │  • AI Scoring: Every 1 hour                                   │        │
│  │  • Cleanup: Daily                                              │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Reusable Code from GitHub Repos

### 2.1 From find-a-thon (MrNK2107/find-a-thon)

| File | Purpose | Reuse Strategy |
|------|---------|-----------------|
| `backend/devfolio.py` | Devfolio scraper with API + Playwright fallback | **Copy directly** to `scrapers/devfolio.py` |
| `backend/base_scraper.py` | GenericScraper base class | **Copy directly** to `scrapers/base.py` |
| `backend/models.py` | HackathonItem model | **Adapt** for OpAssist schema |
| `backend/dedup.py` | Deduplication logic | **Copy directly** with modifications |
| `backend/utils.py` | Date extraction, URL normalization | **Copy directly** |
| `backend/filters.py` | Filtering utilities | **Copy directly** |
| `backend/unstop.py` | Unstop scraper | **Copy and adapt** for API changes |
| `backend/hackerearth.py` | HackerEarth scraper | **Copy and adapt** |
| `backend/knowafest.py` | Knowafest scraper | **Copy directly** |
| `backend/campus_karma.py` | CampusKarma scraper | **Copy directly** |

### 2.2 From CareerPulse (tcpsyn/CareerPulse)

| Component | Purpose | Reuse Strategy |
|------------|---------|----------------|
| `app/scrapers/` | 14-job-source scraping architecture | **Adapt** for hackathon/internship sources |
| `AIClient` | Multi-provider AI (Anthropic, OpenAI, Ollama) | **Copy directly** |
| `JobMatcher` | AI scoring 0-100 | **Adapt** to OpportunityMatcher |
| `app/database.py` | SQLite 37-table schema | **Convert** to Supabase PostgreSQL |
| `APScheduler` | Background job scheduling | **Copy directly** |
| Chrome Extension | Auto-fill ATS forms | **Adapt** for Unstop/Devfolio forms |

---

## 3. Project Structure

```
OpAssist/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── package.json
├── pyproject.toml
├── README.md
│
├── frontend/                     # Next.js 16 App Router
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── opportunities/page.tsx
│   │   │   ├── opportunities/[id]/page.tsx
│   │   │   ├── bookmarks/page.tsx
│   │   │   ├── applications/page.tsx
│   │   │   ├── profile/page.tsx
│   │   │   ├── calendar/page.tsx
│   │   │   ├── team-finder/page.tsx
│   │   │   └── leaderboard/page.tsx
│   │   ├── page.tsx              # Landing page
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                   # shadcn/ui components
│   │   ├── opportunities/        # Opportunity cards, filters
│   │   ├── dashboard/            # Dashboard widgets
│   │   └── layout/               # Nav, sidebar, etc.
│   ├── lib/
│   │   ├── supabase.ts
│   │   └── utils.ts
│   └── public/
│
├── backend/                      # FastAPI Scraper Service
│   ├── main.py                   # FastAPI app entry
│   ├── config.py                 # Configuration
│   ├── requirements.txt
│   │
│   ├── api/                      # API routes
│   │   ├── opportunities.py
│   │   ├── profiles.py
│   │   ├── bookmarks.py
│   │   ├── applications.py
│   │   ├── scraping.py
│   │   ├── ai.py
│   │   └── communities.py
│   │
│   ├── scrapers/                 # Scraping modules
│   │   ├── __init__.py
│   │   ├── base.py               # From find-a-thon
│   │   ├── devfolio.py           # From find-a-thon
│   │   ├── devpost.py            # From find-a-thon
│   │   ├── unstop.py             # From find-a-thon
│   │   ├── hackerearth.py        # From find-a-thon
│   │   ├── knowafest.py          # From find-a-thon
│   │   ├── github_oss.py         # NEW - GitHub OSS/GSoC
│   │   └── community_scrapers.py # From find-a-thon
│   │
│   ├── services/                # Business logic
│   │   ├── scraper_service.py    # Orchestration
│   │   ├── enrichment_service.py
│   │   ├── matching_service.py   # AI matching (from CareerPulse)
│   │   └── notification_service.py
│   │
│   ├── models/                  # Data models
│   │   ├── opportunity.py
│   │   ├── user.py
│   │   └── application.py
│   │
│   ├── database/
│   │   └── supabase_client.py
│   │
│   └── scheduler/
│       └── jobs.py               # APScheduler jobs
│
├── supabase/
│   └── migrations/
│       └── 001_initial.sql
│
└── extension/                    # Chrome Extension (future)
    ├── manifest.json
    ├── popup/
    └── content/
```

---

## 4. Implementation Phases

### Phase 1: Core Setup (Week 1-2)

#### 1.1 Initialize Project
- [ ] Initialize Next.js 16 project with TypeScript
- [ ] Set up Tailwind CSS + shadcn/ui
- [ ] Configure Supabase project
- [ ] Set up FastAPI backend with uvicorn

#### 1.2 Database Schema
```sql
-- Core tables adapted from CareerPulse + OpAssist requirements

-- Users (extends Supabase Auth)
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  name TEXT,
  university TEXT,
  year INTEGER,
  bio TEXT,
  avatar_url TEXT,
  skills TEXT[],  -- Array of skill tags
  interests TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Opportunities (main data)
CREATE TABLE opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  organizer TEXT,
  type TEXT NOT NULL,  -- 'hackathon' | 'internship' | 'scholarship' | 'oss' | 'ambassador' | 'event'
  url TEXT NOT NULL,
  source TEXT NOT NULL,  -- 'devfolio' | 'unstop' | 'hackerearth' | 'github'
  start_date DATE,
  end_date DATE,
  deadline DATE,
  location TEXT,
  is_offline BOOLEAN,
  image_url TEXT,
  prize TEXT,
  tags TEXT[],
  difficulty TEXT,  -- 'beginner' | 'intermediate' | 'advanced'
  requirements TEXT[],
  is_closed BOOLEAN DEFAULT FALSE,
  last_seen_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bookmarks
CREATE TABLE bookmarks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  opportunity_id UUID REFERENCES opportunities(id),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, opportunity_id)
);

-- Applications (pipeline tracking)
CREATE TABLE applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  opportunity_id UUID REFERENCES opportunities(id),
  status TEXT NOT NULL,  -- 'saved' | 'preparing' | 'applied' | 'interviewing' | 'offered' | 'rejected'
  applied_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Peer Activity (social layer)
CREATE TABLE peer_activity (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  opportunity_id UUID REFERENCES opportunities(id),
  action TEXT NOT NULL,  -- 'bookmarked' | 'applied' | 'won'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Universities (for university-aware features)
CREATE TABLE universities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  domain TEXT,
  academic_calendar JSONB  -- Store exam weeks, breaks
);
```

#### 1.3 Basic UI Pages
- Landing page with hero and features
- Login/Signup with Supabase Auth (GitHub + Google OAuth)
- Basic dashboard with opportunity feed

---

### Phase 2: Scraper Integration (Week 3-4)

#### 2.1 Copy scrapers from find-a-thon
- [ ] `scrapers/base.py` - GenericScraper base class
- [ ] `scrapers/devfolio.py` - Devfolio (already well-implemented)
- [ ] `scrapers/unstop.py` - Unstop hackathons
- [ ] `scrapers/hackerearth.py` - HackerEarth challenges
- [ ] `scrapers/knowafest.py` - Knowafest college fests

#### 2.2 Add new scrapers
- [ ] `scrapers/github_oss.py` - GitHub OSS projects, GSoC orgs
- [ ] `scrapers/devpost.py` - Devpost hackathons (global)
- [ ] `scrapers/campus_karma.py` - Campus events

#### 2.3 Scraper Service
```python
# orchestrates all scrapers with retry logic
class ScraperService:
  async def scrape_all(self):
    tasks = [
      self.scrape_devfolio(),
      self.scrape_unstop(),
      self.scrape_hackerearth(),
      # ...
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    await self.deduplicate_and_store(results)
```

#### 2.4 Background Jobs (APScheduler)
- Scraping: Every 6 hours
- Date enrichment: Every 2 hours
- Stale cleanup: Daily

---

### Phase 3: AI & Personalization (Week 5-6)

#### 3.1 AI Matching (adapted from CareerPulse)
- [ ] Integrate AIClient with multiple providers
- [ ] Implement OpportunityMatcher (score 0-100)
- [ ] Add skill gap analysis
- [ ] Add resume/profile parsing

#### 3.2 Recommendation Engine
- [ ] Filter by user profile (skills, interests, university)
- [ ] Difficulty-based filtering (beginner/intermediate/advanced)
- [ ] Academic calendar awareness (hide high-effort during exams)

#### 3.3 Notifications
- [ ] Deadline reminders (7 days, 1 day before)
- [ ] Daily digest of new opportunities

---

### Phase 4: Community & Social (Week 7-8)

#### 4.1 Social Features
- [ ] Peer activity feed (see what classmates are applying to)
- [ ] Team finder for hackathons (skill matching)
- [ ] Campus leaderboard (wins, applications, streaks)
- [ ] Success stories / writeups

#### 4.2 Application Pipeline (adapted from CareerPulse)
- [ ] Kanban board (saved → preparing → applied → interviewing → offered)
- [ ] Interview round tracking
- [ ] Calendar integration (iCal export)

---

### Phase 5: University Integration (Week 9-10)

#### 5.1 University Features
- [ ] University-specific pages
- [ ] Department filtering (CS, ECE, Design)
- [ ] Campus ambassador program tracking

#### 5.2 Future: Chrome Extension
- [ ] Auto-fill on Unstop/Devfolio applications
- [ ] Overlay on job boards

---

## 5. Tech Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Frontend | Next.js 16 (App Router) | From SPEC.md |
| UI | shadcn/ui + Tailwind | Industry standard |
| Backend | FastAPI | Async, from CareerPulse |
| Database | Supabase PostgreSQL | Auth + DB + Storage + Realtime |
| AI | Groq SDK / Ollama | Fast + cheap / fully local |
| Scraping | Playwright + httpx | From find-a-thon |
| Scheduling | APScheduler | From CareerPulse |
| Hosting | Vercel + Railway | Per SPEC.md |

---

## 6. API Endpoints

### Opportunities
- `GET /api/opportunities` - List with filters
- `GET /api/opportunities/:id` - Detail
- `POST /api/opportunities/:id/match` - AI score

### Bookmarks
- `GET /api/bookmarks` - User's bookmarks
- `POST /api/bookmarks` - Add bookmark
- `DELETE /api/bookmarks/:id` - Remove

### Applications
- `GET /api/applications` - User's pipeline
- `POST /api/applications` - Update status
- `POST /api/applications/:id/events` - Add timeline note

### Profile
- `GET /api/profile` - User profile
- `PUT /api/profile` - Update profile

### AI
- `POST /api/ai/match` - Score opportunity
- `POST /api/ai/recommend` - Get recommendations
- `POST /api/ai/analyze` - Career trajectory

### Scrape
- `POST /api/scrape/trigger` - Manual scrape (admin)
- `GET /api/scrape/status` - Scrape progress

---

## 7. Key Differentiators Implementation

| Feature | Implementation |
|---------|---------------|
| University-aware | Filter by `profiles.university`, sync with academic calendar |
| Student progression | Track: first_hackathon → first_oss → first_internship |
| Time-contextual | Hide 3-month hackathons during exam weeks (configurable) |
| One-click save | Bookmarks with Supabase realtime |
| Social layer | `peer_activity` table + real-time subscriptions |
| India-first | Focus scrapers on Unstop, Devfolio, HackerEarth |

---

## 8. Reuse Summary

### From find-a-thon
- **Direct copy**: base_scraper.py, devfolio.py, models.py (adapted), dedup.py, filters.py, utils.py
- **Adapt**: unstop.py, hackerearth.py, knowafest.py (API changes)
- **Add**: github_oss.py

### From CareerPulse
- **Direct copy**: APScheduler setup, background jobs pattern
- **Adapt**: AIClient for opportunities (not jobs), JobMatcher → OpportunityMatcher
- **Reference**: Database schema (37 tables → 6 core tables), Chrome extension pattern

---

## 9. Testing Strategy

Following CareerPulse's 1,248 tests approach:
- **Backend**: pytest for scrapers, API, matching
- **Frontend**: Vitest for components
- **Integration**: E2E tests with Playwright

Target: 80%+ coverage

---

## 10. Dependencies

### Backend (Python)
```
fastapi
uvicorn
httpx
playwright
beautifulsoup4
apscheduler
groq
anthropic
python-dotenv
python-multipart
pydantic
supabase
```

### Frontend (Node.js)
```
next@16
react@19
typescript
tailwindcss
@supabase/supabase-js
shadcn-ui
lucide-react
framer-motion
```

---

## 11. Quick Start

```bash
# Clone and setup
git clone https://github.com/your-org/OpAssist.git
cd OpAssist

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

---

## 12. Next Steps

1. **Initialize project** with structure above
2. **Copy scrapers** from find-a-thon
3. **Set up Supabase** and run migrations
4. **Build basic UI** (landing + auth)
5. **Test scrapers** individually
6. **Build opportunity feed**
7. **Add AI matching**
8. **Implement social features**

---

*Generated: May 2026*
*Based on: SPEC.md + CareerPulse + find-a-thon research*