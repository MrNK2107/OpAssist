<p align="center">
  <img src="https://img.shields.io/badge/OpAssist-v1.0-blue?style=for-the-badge&logo=data:image/svg+xml;base64,..." alt="OpAssist">
</p>

<h1 align="center">
  <pre>
  ╔══════════════════════════════════════════════╗
  ║                                              ║
  ║     ╭━━━━╮  ╭━━━╮  ╭━━━╮  ╭━━╮  ╭━━━╮     ║
  ║     ┃╭━╮┃  ┃╭━╮┃  ┃╭━╮┃  ╰┫┣╯  ┃╭━╮┃     ║
  ║     ┃┃ ┃┃  ┃╰━╯┃  ┃╰━╯┃   ┃┃   ┃╰━╯┃     ║
  ║     ┃╰━╯┃  ┃╭━━╯  ┃╭━━╯  ╭┫┣╮  ┃╭━━╯     ║
  ║    ╰━━━━╯  ╰╯     ╰╯     ╰━━╯  ╰╯         ║
  ║                                              ║
  ║     Your Gateway to Every Opportunity        ║
  ║                                              ║
  ╚══════════════════════════════════════════════╝
  </pre>
</h1>

<p align="center">
  <strong>All-in-one opportunity discovery platform for Indian university students</strong>
  <br/>
  Hackathons | Internships | Scholarships | Open Source | Tech Events
  <br/><br/>
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js&style=flat-square" alt="Next.js">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&style=flat-square" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&style=flat-square" alt="TypeScript">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?logo=supabase&style=flat-square" alt="Supabase">
  <img src="https://img.shields.io/badge/Firebase-Auth-FFCA28?logo=firebase&style=flat-square" alt="Firebase">
  <img src="https://img.shields.io/badge/Chrome-Extension-4285F4?logo=google-chrome&style=flat-square" alt="Chrome Extension">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License">
</p>

---

## The Problem

> *"Where do I find hackathons? Internships? Scholarships? GSoC? Open source programs?"*

Every Indian university student asks this question — and the answer is always the same: **check 6 different platforms, hope you didn't miss anything, and pray the deadlines haven't passed.**

Devpost for hackathons. Internshala for internships. Unstop for competitions. GitHub Explore for open source. Handshake for career fairs. Each one a separate tab, a separate login, a separate search.

**There had to be a better way.**

## The Solution

**OpAssist** unifies everything into a single, intelligent feed. One dashboard. Every opportunity. Filtered by your university, your skills, and your academic calendar.

```
┌─────────────────────────────────────────────────────────────────┐
│  OpAssist Dashboard                                    [Profile]│
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                  │
│  Discover    │  ┌────────────────────────────────────────────┐  │
│  Bookmarks   │  │  AI Match: 92%  |  Deadline: Mar 15       │  │
│  Applications│  │  ────────────────────────────────────      │  │
│  Calendar    │  │  Smart India Hackathon 2026               │  │
│  Team Finder │  │  Government of India | Hackathon          │  │
│  Leaderboard │  │  Skills: React, Python, AI/ML             │  │
│  Notifications│ │  ────────────────────────────────────      │  │
│              │  │  [Apply] [Bookmark] [Share]                │  │
│              │  └────────────────────────────────────────────┘  │
│              │                                                  │
│              │  ┌────────────────────────────────────────────┐  │
│              │  │  AI Match: 87%  |  Deadline: Apr 1        │  │
│              │  │  ────────────────────────────────────      │  │
│              │  │  GSoC 2026 - Google                       │  │
│              │  │  Open Source | Stipend: $3,000+            │  │
│              │  │  ────────────────────────────────────      │  │
│              │  │  [Apply] [Bookmark] [Share]                │  │
│              │  └────────────────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Unified Feed** | Aggregated opportunities from Devfolio, Unstop, HackerEarth, GitHub, Internshala, and more |
| **AI Match Scoring** | Groq/Anthropic-powered scores telling you *why* an opportunity fits you |
| **Application Tracker** | Kanban pipeline: Saved → Preparing → Applied → Interviewing → Offered |
| **Calendar View** | Monthly deadline visualization with `.ics` export to Google/Apple Calendar |
| **Smart Bookmarks** | Save, tag, and organize opportunities across categories |
| **Team Finder** | Find hackathon teammates by skills, university, and availability |
| **Campus Leaderboard** | See how you rank against peers at your university |
| **Deadline Notifications** | Never miss another application deadline |
| **Chrome Extension** | One-click save from Devfolio, Unstop, and HackerEarth directly |

---

## Architecture

```
OpAssist/
├── frontend/          Next.js 16 + React 19 + TypeScript + Tailwind CSS + Zustand
│   ├── app/           App Router with route groups (auth) & (dashboard)
│   ├── components/    Reusable UI: cards, badges, buttons, layout primitives
│   ├── stores/        Zustand stores for auth, bookmarks, applications
│   ├── hooks/         Custom React hooks (useAuth, etc.)
│   └── lib/           Firebase client, API helpers, university data
│
├── backend/           FastAPI + Python + Supabase + AI integrations
│   ├── api/           REST endpoints: opportunities, bookmarks, applications, AI
│   ├── scrapers/      Multi-source scrapers: Devfolio, Unstop, GitHub, Internshala...
│   ├── services/      Business logic: matching, notifications, scraping orchestration
│   ├── scheduler/     Background job scheduling for periodic scraping
│   ├── database/      Supabase client with typed queries
│   └── models/        Pydantic schemas for request/response validation
│
├── extension/         Chrome Extension (Manifest V3)
│   ├── background/    Service worker for extension lifecycle
│   ├── content/       Content scripts for Devfolio, Unstop, HackerEarth
│   └── popup/         Extension popup UI
│
└── supabase/          PostgreSQL migrations
    ├── migrations/    Schema, RLS policies, seed data, indexes
    └── setup.sql      One-shot database bootstrap
```

---

## Scrapers

OpAssist aggregates from **8+ sources**, each with API-first + DOM-fallback strategies:

| Source | Opportunities | Method |
|--------|--------------|--------|
| **Devfolio** | Hackathons | REST API + DOM fallback |
| **Unstop** | Hackathons, Internships, Scholarships | Public API + DOM fallback |
| **HackerEarth** | Challenges, Hackathons | REST API + DOM fallback |
| **GitHub** | OSS, GSoC, Hacktoberfest | GraphQL + REST |
| **Internshala** | Internships | HTML + JSON-LD scraping |
| **Hack2Skill** | Events, Hackathons | Public API |
| **MLH** | Hackathons | Web scraping |
| **Devpost** | Hackathons | Web scraping |

---

## Quick Start

### Prerequisites

- **Node.js** 18+
- **Python** 3.12+
- **Supabase** account ([free tier](https://supabase.com) works)

### 1. Clone & Install

```bash
git clone https://github.com/MrNK2107/OpAssist.git
cd OpAssist
```

### 2. Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run migrations in order:

```bash
# In Supabase SQL Editor, run each file:
supabase/setup.sql                    # Full bootstrap (or run individually)
# OR run migrations one by one:
supabase/migrations/001_create_tables.sql
supabase/migrations/002_rls_policies.sql
supabase/migrations/003_seed_data.sql
supabase/migrations/004_indexes.sql
supabase/migrations/005_team_notifications_config.sql
supabase/migrations/006_team_members.sql
```

### 3. Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your Supabase credentials
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
# API runs at http://localhost:8000
```

### 4. Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local with your Supabase + Firebase credentials
npm install
npm run dev
# App runs at http://localhost:3000
```

### 5. Chrome Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` directory

---

## Environment Variables

See [`.env.example`](.env.example) for the full list.

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase anonymous/public key |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key (backend only) |
| `NEXT_PUBLIC_FIREBASE_*` | Yes | Firebase config for auth |
| `GROQ_API_KEY` | No | Enables AI match scoring (Groq) |
| `ANTHROPIC_API_KEY` | No | Enables AI match scoring (Anthropic) |

---

## API Endpoints

| Route | Methods | Description |
|-------|---------|-------------|
| `/api/opportunities` | `GET` `POST` | Browse and save opportunities |
| `/api/opportunities/{id}/match` | `POST` | Get AI match score for an opportunity |
| `/api/profile` | `GET` `PUT` | User profile CRUD |
| `/api/bookmarks` | `GET` `POST` `DELETE` | Bookmark management |
| `/api/applications` | `GET` `POST` `PUT` `DELETE` | Application pipeline tracking |
| `/api/notifications` | `GET` `PUT` | Notifications with read/unread |
| `/api/communities/leaderboard` | `GET` | Campus rankings |
| `/api/communities/team-find` | `POST` | Find hackathon teammates |
| `/api/scrape/trigger` | `POST` | Manual scrape trigger |
| `/api/ai/match` | `POST` | AI match scoring |
| `/api/ai/recommend` | `POST` | AI-powered recommendations |
| `/api/ai/analyze` | `POST` | Career trajectory analysis |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS, Zustand |
| **Backend** | FastAPI, Python 3.12+, Pydantic v2 |
| **Database** | PostgreSQL (Supabase) with Row Level Security |
| **Auth** | Firebase Authentication |
| **AI** | Groq (Llama 3), Anthropic (Claude) |
| **Scraping** | httpx, BeautifulSoup, Playwright |
| **Extension** | Chrome Manifest V3, vanilla JS |
| **Scheduling** | APScheduler for periodic scraping |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-thing`
3. Commit your changes: `git commit -m 'Add amazing thing'`
4. Push to the branch: `git push origin feature/amazing-thing`
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with late nights and chai</strong>
  <br/>
  <sub>OpAssist - Because every student deserves a fair shot at every opportunity.</sub>
</p>
