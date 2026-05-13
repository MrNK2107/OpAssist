# OpAssist - Project Specification

> Last Updated: May 2026
> Status: Research Complete - Ready for Implementation

---

## 1. Project Overview

**OpAssist** is an all-in-one opportunity discovery platform for university students to find hackathons, open source projects, internships, scholarships, tech events, and more — in one place.

### Vision Statement

"Your university career dashboard — all hackathons, OSS projects, internships, and more in one feed, filtered by your college and academic calendar."

### Differentiation from Existing Platforms

| Existing Platform | Gap OpAssist Fills |
|---|---|
| Devpost | Only hackathons, no internships/OS projects |
| LinkedIn | Overwhelming, not student-focused, no hackathons |
| GitHub Explore | Open source only, no time-context |
| Handshake | Only career fairs/ internships, no community |
| Unstop (India) | Hackathons + internships + scholarships, but no personalization or university awareness |
| Atlas (global) | US-focused, doesn't cover India-specific programs or campus ambassador tracks |

**OpAssist's unique differentiators:**
1. **University-aware** — Filter by college, sync with academic calendar, prerequisite awareness
2. **Opportunity lifecycle** — Students progress from beginner (projects) → intermediate (hackathons) → advanced (internships, OSS) — tracked and recommended
3. **Time-contextual** — Shows opportunities relevant to current semester/exam season (e.g., no 3-month intensive hackathons during finals week)
4. **One-click save & apply** — Unified bookmarks, quick-apply via OAuth (GitHub, Devpost, LinkedIn)
5. **Social layer** — See what peers are applying to, teammate finder for hackathons
6. **India-first** — Covers Unstop, Devfolio, HackerEarth, campus ambassador programs, SIH, FOSSEE, C4GT and more

---

## 2. Competitive Landscape

### Pure Aggregators (Global)

| Platform | Focus | Notes |
|---|---|---|
| **ATLAS** (atlascareer.org) | All-in-one feed (jobs, hackathons, scholarships) | Pre-fill applications, school-specific filtering |
| **Lanci** (withlanci.com) | Scholarships, programs, internships | Filters by resume/profile |
| **Oppora** (opporaglobal.com) | Internships, competitions, scholarships | Verified database, filter by major |
| **Opyway** (opyway.com) | Scholarships, grants, competitions | Profile-matched filtering |
| **Elevate Access** (elevateaccess.app) | Hackathons, grants, scholarships, fellowships | "AI matching coming soon" |

### Open Source Discovery (Global)

| Platform | Focus | Notes |
|---|---|---|
| **OS Atlas** (osatlas.tech) | GSoC, LFX, SoB, outreachy — organizational database | Timeline tracking, program comparison |
| **IssueScout** (issuescout.dev) | Beginner-friendly GitHub issues | Community health scores + AI difficulty |
| **Opensox** (opensox.ai) | OSS repos by language/stack | "10,000+ engineers" |
| **GitDB** (gitdb.net) | GitHub repo analytics | Star velocity, maintenance signals |

### Student Career Platforms (Global)

| Platform | Focus | Notes |
|---|---|---|
| **EduNatives** (edunatives.net) | MENA tech students — profile portfolio, AI CV feedback | Projects over resumes |
| **The Interns Company** | Tech internships matching, campus ambassadors | Premium paywall |
| **Aply** (aply.com) | Portfolio-based hiring, AI recruiters, invite-only brands | $20/mo premium |
| **Peerful** (peerful.ai) | Gen-Z networking + 1-click apply | Local-first, no paywalls |
| **Alma** (joinalma.ai) | University alumni mentorship via AI intros | Verified email required |
| **ElevateGrad** (elevategrad.com) | Campus events, clubs, announcements + internships | Student-led community |
| **Crewsity Connect** | Team formation for hackathons + AI skill matching | Beta stage |

### India-Specific Opportunity Platforms

| Platform | Type | Focus | Notes |
|---|---|---|---|
| **Unstop** (unstop.com) | Aggregation | Hackathons, internships, competitions, scholarships | Dominant in India, hosts SIH, Adobe India Hackathon, ET AI Hackathon |
| **Devfolio** (devfolio.co) | Hackathon hosting | AI/Web3 hackathons, community hackathons | "One application to the best hackathons" |
| **HackerEarth** (hackerearth.com) | Challenges + hiring | Hackathons, coding contests, campus hiring | Major Indian competitor |
| **HackIndia** (hackindia.org) | Hackathon series | AI/Web3 companies + 3.1M devs + 5000+ colleges | Company-facing platform |
| **Internshala** (internshala.com) | Internships | Internships, trainings, scholarships | India's biggest internship platform |
| **OSCode** (oscode.co.in) | Community | DSA bootcamp, open source sprints, hackathon season | India-focused dev community |

---

## 3. Key Gaps in the Market

Based on all research, here's what **isn't being done well**:

1. **Unified hackathon + OSS + internship feed** — Most platforms pick ONE vertical. ATLAS is closest but focuses on jobs/hackathons, not OSS projects or summer programs.

2. **University-calendar-aware scheduling** — No platform shows "these opportunities won't clash with your midterms" or "perfect timing before winter break."

3. **Student progression tracking** — No platform says "you bookmarked 3 hackathons, you're ready to apply to GSoC next." A growth journey concept.

4. **Peer reputation / social proof** — "5 students from IIT Bombay applied here and won" — this doesn't exist anywhere.

5. **One-click apply across all sources** — ATLAS does pre-fill, but no one does OAuth-merge (GitHub + Devpost + LinkedIn) for seamless applications.

6. **Beginner-to-advanced funnel** — Platforms either target beginners (IssueScout) or advanced (OS Atlas). Nothing guides you through the journey.

7. **Regional / non-US focused** — Most platforms are US-centric. Nothing covers India + Southeast Asia + South Asia broadly.

8. **Campus ambassador programs** — A huge India-specific category with rolling deadlines that no platform tracks.

9. **Government programs** — SIH, FOSSEE, C4GT are major opportunities unique to India.

10. **No platform combines ALL of these**: opportunities + team formation + social proof + university awareness + application management.

---

## 4. India-Specific Opportunity Categories

### Campus Ambassador Programs (Major India Feature)

- Microsoft Learn Student Ambassador (all years, rolling)
- GitHub Campus Expert (Feb + Aug, India active)
- GeeksforGeeks Campus Ambassador (May/June)
- HackerEarth/HackerRank Campus Ambassador
- AWS Educate, Cisco Devnet, Intel Software Innovator
- GitHub India Externship (90-day remote fellowship for pre-final year at Campus Partner schools)

### India-Specific Hackathons

- **Smart India Hackathon (SIH)** — government's flagship, software + hardware editions
- **Capgemini Tech Challenge** — 7.5L+ participants, largest in India
- **ET AI Hackathon** (Economic Times) — INR 10L+ prizes, hiring pipeline
- **Adobe India Hackathon** — MacBook Air + INR 1L/month internship + trip to Adobe HQ
- **Flipkart Grid** — PPI opportunities
- **CodeAgon** (CodeNation) — INR 200K+ prizes, SDE interviews, internships

### India-Specific Internships/Externships

- **GitHub India Externship** — 90-day remote fellowship for pre-final year students at GitHub Campus Partner schools
- **Microsoft Engage Mentorship** — May-June, sophomore only → Microsoft India internship
- **Google STEP India** — November, first/second year
- **FOSSEE Summer Fellowship** (IIT Bombay) — India-specific, paid
- **Code for GovTech (C4GT)** — Dedicated Mentoring Program, annual 3-month
- **Flipkart Runway / Diversity Hiring** — specific to India
- **Amazon WOW Internship** — women in tech India
- **Crio Winter of Doing** — final year students + working professionals

### Research Opportunities

- IIT/NIT/IIIT summer research internships (many have dedicated portals)
- S.N. Bose Scholars Program (India-US)
- IISc, IITs, IIITs research internships (direct apply)

### Scholarships

- Generation Google Scholarship (APAC, March)
- Adobe India Women-in-Tech Scholarship (August)
- Nutanix Heart Women in Tech (India)
- Venkat Panchapakesan Memorial Scholarship (May-Aug)
- State/Central government tech scholarships

---

## 5. GitHub Reference Projects (Reusable Code)

### Complete Stack References (directly reusable)

| Project | Stars | Tech | What to steal |
|---|---|---|---|
| **HackathonHunt** | 0 | Next.js + FastAPI + PostgreSQL | Scraping architecture, multi-source aggregation (Devpost, Devfolio, MLH, Unstop), Supabase integration pattern |
| **OpportuneX** | - | Next.js + FastAPI + Supabase | Multi-platform scraping (4 sources), scheduler management, duplicate detection |
| **Repeto** | 1 | Next.js + ? | Curated opportunity database with recurrence tracking, filtering logic |
| **CampusSphere AI** | - | React + MongoDB + Groq | Blueprint engine, smart matcher, T-Minus alert protocol, semantic search |

### Portfolio Showcase Platforms (Supabase + Next.js patterns)

| Project | What to learn |
|---|---|
| **ProjectSphere** | Next.js + Supabase auth, multimedia uploads, bookmark system, search/filter UI |
| **Smart Student Hub v2** | Activity submission flow, portfolio management, JWT auth with SQLite dev / Postgres prod |
| **UniPlanner.ai** | Repository pattern with Supabase, AI recommendations, university comparison logic |
| **lalding-portfolio** | Production-grade: shadcn/ui + CVA + Framer Motion + Supabase Auth + Sentry + GitHub Actions CI |

### Scraping / API Tools (directly usable)

| Tool | Purpose |
|---|---|
| **devpost-api** (PyPI) | Unofficial Devpost client — scrapes hackathons, software, users with retries, caching, CLI |
| **get-hackathons** (npm) | Fetch user hackathons/wins from Devpost by username |
| **github-scraper** (npm) | Scrape GitHub profiles, repos, issues, stars without API rate limits |
| **cheerio** | Standard HTML parsing for any website scraping |

### Awesome Lists (curated opportunity databases)

- **OWASP-STUDENT-CHAPTER/oss-programs** (14 stars) — Mentorship/hackathon directory with calendar export, Fuse.js search
- **Surajv311/one4All** (195 stars) — Comprehensive CS opportunities — hackathons, ambassadors, OSS, scholarships, diversity programs, externships, research — India-focused
- **yashisrani/List-of-OpenSource-Programs** (74 stars) — Active 2026 programs with GSoC, LFX, OSPP, C4GT, FOSSEE (IIT Bombay)
- **ketankauntia/gsoc-orgs** — GSoC org explorer with tech stack filtering, year-wise data
- **ummadiviany/Awesome-Internships** — IIT/NIT/IIIT internship compilations, research, GOI internships

### Application Tracking (CareerPulse-inspired)

| Project | Stars | Tech | Key Features |
|---|---|---|---|
| **CareerPulse** (tcpsyn) | 11 | Python FastAPI + Vanilla JS SPA | 14-source scraping, AI job matching, ATS auto-fill Chrome extension, pipeline management, calendar sync, 1248 tests |
| **InternAtlas** | - | Next.js + Prisma + Firebase | 2000+ companies, 300K+ listings, GitHub Actions crawling, Greenhouse/Lever/Workday/iCIMS |
| **FutureStack** | 1.4 | Next.js + Supabase + Clerk | Kanban board, analytics, PDF reports, deadline calendar, document uploads |
| **opentern** | 1 | Next.js + Convex | GitHub API scraping, virtual scrolling, Google OAuth, fuzzy search |
| **didtheyghost.me** | 65 | Next.js + Supabase + Clerk | Community-driven application tracking, response timeline per company |

### Student Job Platforms

| Project | Stars | Tech | Notes |
|---|---|---|---|
| **gradwork** | 6 | Next.js + NestJS + Prisma + Supabase | Dual backend (Next.js + NestJS), student profile, job CRUD, application tracking |
| **Interntrack** | - | Next.js + Prisma + PostgreSQL | College internship management, HR email verification, attendance tracking |
| **Campus-Helper** | 1 | Next.js + Supabase | Part-time jobs + study materials + forum + chat + AI assistant |
| **CampusSphere** | - | React + Node.js + MongoDB | Academic event aggregator, Groq AI, resume parsing, deadline alerts |

---

## 6. Framework & Tool Recommendations

### Scraping & Data Aggregation Layer

| Framework/Lib | Use Case | Source |
|---|---|---|
| **httpx + aiosqlite** | Async HTTP with connection pooling + SQLite for lightweight storage | CareerPulse |
| **BeautifulSoup4 + feedparser** | HTML scraping + RSS feed parsing | CareerPulse |
| **ApScheduler** | Background job scheduling for periodic scraping | CareerPulse |
| **FastAPI** | Async Python backend for scraping API | HackathonHunt, OpportuneX, CampusSphere |
| **Playwright / Puppeteer** | Headless browser scraping for JS-heavy pages | CampusSphere AI |

### AI Matching & Scoring

| Framework | Use Case | Source |
|---|---|---|
| **Groq** | High-speed LLM inference for real-time opportunity analysis | CampusSphere AI |
| **Anthropic SDK / OpenAI SDK** | Job matching scoring against resume | CareerPulse |
| **Ollama** | Fully local AI inference (no API costs) | CareerPulse |
| **Gemini AI** | Enhanced matching algorithms | Alternship, didtheyghost.me |

### UI Components & Styling

| Framework | Use Case | Source |
|---|---|---|
| **shadcn/ui** | Reusable component library | Interntrack, student-job-platform, gradwork |
| **Tailwind CSS** | Utility-first styling, responsive design | ALL Next.js projects |
| **Mantine UI** | Modern accessible UI components | mploy-app |
| **Framer Motion** | Smooth animations | Campus-Helper, lalding-portfolio |
| **Lucide React** | Icon library | All recent projects |
| **Glassmorphism/Bento Box UI** | High information density dashboards | CampusSphere AI |

### Data Management

| Framework | Use Case | Source |
|---|---|---|
| **Prisma ORM** | PostgreSQL schema management | gradwork, InternAtlas, Interntrack |
| **Supabase PostgreSQL** | Auth + DB + Storage + Realtime in one | Campus-Helper, gradwork, FutureStack |
| **Convex** | Real-time backend with virtual scrolling | opentern |
| **MongoDB + aggregation pipelines** | Regex search with pagination | CampusSphere |

### Email & Notifications

| Framework | Use Case | Source |
|---|---|---|
| **Nodemailer** | SMTP email delivery for deadline alerts | CampusSphere, Interntrack |
| **React Email** | Email templates | student-job-platform, lalding-portfolio |
| **Resend API** | Transactional email | lalding-portfolio |

### Resume & Document Processing

| Framework | Use Case | Source |
|---|---|---|
| **pdf-parse** | Parse PDF resumes to extract skills | CampusSphere |
| **PyMuPDF** | PDF generation for tailored resumes | CareerPulse |
| **python-docx** | DOCX export for resumes | CareerPulse |
| **Uploadthing** | Resume file uploads | student-job-platform |
| **Supabase Storage** | Store profile images, PDFs | Campus-Helper, gradwork |

---

## 7. Architecture Patterns (Borrow & Adapt)

### From CareerPulse → OpAssist adaptation:
1. **Scraping**: Replace job boards with hackathon/internship platforms (Unstop, Devfolio, HackerEarth)
2. **AI Matching**: Score opportunities against student profile (skills, interests, year) instead of resume
3. **Pipeline**: Track application status instead of job status
4. **Chrome Extension**: Auto-fill on Unstop/Devfolio application forms

### From InternAtlas → OpAssist adaptation:
1. **GitHub Actions cron** for scheduled scraping (every 6-12 hours)
2. **Prisma + PostgreSQL** for structured opportunity data
3. **Firebase/Firestore** for user-specific data (bookmarks, profile, tracking)

### From CampusSphere AI → OpAssist adaptation:
1. **Blueprint Engine**: Generate preparation roadmap per opportunity type
2. **Groq-powered** semantic search (fuzzy matching across tags)
3. **Resume parsing**: Extract skills → match against opportunity tags

### From opentern → OpAssist adaptation:
1. **Convex** for real-time application tracking with virtual scrolling
2. **GitHub API scraping** for open source opportunities
3. **Drag-and-drop** pipeline for application stages

---

## 8. Tech Stack

```
Frontend:  Next.js 16+ (App Router), TypeScript, Tailwind CSS, shadcn/ui
Backend:   Next.js API Routes (Server Actions) + FastAPI scraper service
Database:  Supabase (PostgreSQL)
Auth:      Supabase Auth (email + OAuth: GitHub, Google)
Storage:   Supabase Storage (profile images, banners)
Realtime:  Supabase Realtime (for notifications)
AI:        Groq SDK (fast, cheap) / Ollama (local)
Scraping:  FastAPI + BeautifulSoup + httpx + APScheduler
Hosting:   Vercel (frontend) + Railway/Supabase (backend)
```

---

## 9. Data Model (Supabase)

```
users ────────── profiles ────────── bookmarks
  │                   │                  │
  │                   │                  │
  └── skills (many)    └── interests (many) ── opportunities
                                                │
profiles.university ────────────────────────────┘
```

### Core Tables

- **profiles** — user_id, name, bio, university, year, avatar_url, skill_tags[], interests[]
- **opportunities** — id, title, type, description, url, deadline, location, difficulty, tags[], source (devpost, unstop, github, etc.), recurring (boolean), academic_year_availability
- **bookmarks** — user_id, opportunity_id, notes, created_at
- **applications** — user_id, opportunity_id, status (saved/applied/interviewing/offered/rejected), applied_at, notes
- **peer_activity** — user_id, opportunity_id, action (applied/won/bookmarked), timestamp
- **universities** — id, name, domain, academic_calendar_json
- **scraper_schedule** — source, last_run, interval_hours, status

---

## 10. Pages / Routes

```
/                          → Landing page (hero, features, CTA)
/auth/login                → Login page
/auth/signup               → Signup page
/dashboard                 → Main personalized feed
/opportunities            → Browse all (filterable)
/opportunities/[id]        → Detail page + apply/bookmark
/profile                   → User profile + skills
/profile/edit              → Edit profile
/bookmarks                 → Saved opportunities
/applications              → Application pipeline (kanban view)
/notifications             → Deadline reminders
/calendar                  → Calendar view with .ics export
/leaderboard               → Campus rankings (wins, applications)
/team-finder               → Teammate matching for hackathons
/university/[slug]        → University-specific opportunities
```

---

## 11. Feature Phases

### Phase 1 — MVP (Core Discovery)
- [ ] **Opportunity feed** — Aggregate hackathons, OSS projects, internships, scholarships, campus ambassador programs, tech events
- [ ] **Filtering & search** — By type, location, skill level, deadline, university, difficulty
- [ ] **User profiles** — Skills, interests, university, year
- [ ] **Bookmarks/wishlist** — Save opportunities
- [ ] **Tags & categories** — Easy browsing
- [ ] **India-first scraping** — Unstop, Devfolio, HackerEarth, GitHub (OSS projects)

### Phase 2 — Personalization
- [ ] **Recommendation engine** — Based on profile, past bookmarks, skill level, academic year
- [ ] **Deadline reminders** — Email/notification before opportunities close
- [ ] **Calendar integration** — Import/export to Google Calendar, iCal
- [ ] **Academic calendar awareness** — Auto-hide high-effort opportunities during exam weeks
- [ ] **AI matching score** — Score opportunities 0-100 against student profile

### Phase 3 — Community & Social
- [ ] **Peer activity feed** — See what classmates are saving/attending
- [ ] **Teammate finder** — Match for hackathons by skill/interest
- [ ] **Success stories** — User-submitted writeups on how they got selected
- [ ] **Campus leaderboard** — Rankings by wins, applications, streaks

### Phase 4 — University Integration
- [ ] **University SSO** — Login via college email (.edu)
- [ ] **Department filtering** — CS, ECE, Design, etc.
- [ ] **Admin portal** — Universities can post exclusive opportunities
- [ ] **Campus ambassador tracking** — Track progress in ambassador programs

---

## 12. Implementation Roadmap

### Week 1 — Setup & Auth
- Initialize Next.js project with TypeScript, Tailwind, shadcn/ui
- Set up Supabase project, schema, RLS policies
- Auth flow (email + GitHub OAuth)
- Basic profile creation with skills/interests

### Week 2 — Core UI & Data
- Build landing page
- Opportunity feed with mock data (scraper later)
- Filtering & search UI (Fuse.js for fuzzy search)
- Bookmark functionality
- Supabase database integration

### Week 3 — Scraping & Backend
- Build FastAPI scraper service for Unstop, Devfolio, HackerEarth
- GitHub Actions cron for scheduled scraping (every 6 hours)
- Store scraped data in Supabase PostgreSQL
- Deduplication logic
- API routes for opportunity CRUD

### Week 4 — Personalization & AI
- Skill/interest selection on profile
- AI matching score (Groq SDK)
- Recommendation logic (filtering by profile)
- Dashboard customization
- Deadline reminder notifications

### Week 5 — Community & Polish
- Peer activity feed
- Application pipeline (kanban view)
- Calendar view with .ics export
- Responsive design
- Deploy to Vercel

### Future — Team Formation & University Integration
- Teammate finder for hackathons
- University-specific pages
- Campus ambassador program tracking
- Chrome extension for auto-fill on application forms

---

## 13. Scraping Strategy

### Primary Sources (Priority Order)

| Source | Type | Scraping Method | Priority |
|---|---|---|---|
| **Unstop** | Hackathons + internships + scholarships + competitions | API + HTML scraping | **P0** |
| **Devfolio** | Hackathons (AI/Web3 focused) | API + HTML scraping | **P0** |
| **HackerEarth** | Challenges + hackathons + campus hiring | REST API | P1 |
| **GitHub** | Open source projects, GSOC orgs, Hacktoberfest | GraphQL + REST API | P1 |
| **one4All / Repeto** (reference) | Curated program data | Manual JSON import | P1 |
| **Code for GovTech** | C4GT Dedicated Mentoring Program | HTML scraping | P1 |
| **FOSSEE** (IIT Bombay) | Summer Fellowship | HTML scraping | P1 |

### Scraping Architecture (from HackathonHunt + OpportuneX)

```
FastAPI Scraper Service
├── scrapers/
│   ├── unstop.py      (API + BeautifulSoup)
│   ├── devfolio.py    (API + BeautifulSoup)
│   ├── hackerearth.py (REST API)
│   ├── github.py      (GraphQL/REST)
│   └── base.py        (exponential backoff, UA rotation, rate limiting)
├── scheduler/
│   └── apscheduler.py (run every 6 hours via GitHub Actions)
├── models/
│   └── opportunity.py (normalized schema)
└── database/
    └── supabase.py    (upsert to PostgreSQL)
```

---

## 14. Key Differentiators (Summary)

Based on all research, the **unique angle** that no existing project covers:

**India-university-aware opportunity lifecycle** — Combine:
- Unstop/Devfolio scraping (like HackathonHunt)
- Student profile with college + year + skills (like gradwork)
- Application tracking (like CareerPulse but for hackathons/internships)
- AI matching + deadline alerts (like CampusSphere AI)
- University-calendar integration (exam weeks hide high-effort opportunities)
- Peer activity (see classmates applying to the same hackathon)
- Campus ambassador programs (a huge India-specific category no platform covers)

This combination doesn't exist in any single platform.

---

## 15. Open Questions (To Finalize Before Implementation)

1. **Geographic focus** — India-only, or India + global? This changes scraping sources and university integrations.
2. **Revenue model** — Free with ads? Freemium (premium features)? University subscription?
3. **Data sourcing** — Manual curation (slow but high quality), community submissions, or scraping (fast but messy)?
4. **MVP scope** — What are the 3-5 core features to ship first?
5. **Auth requirements** — Is university email verification (.edu) important from the start?
6. **AI features** — Start with simple matching, or go full AI from day 1 (blueprint engine, skill gap analysis)?

---

## 16. Useful Links & Resources

### Platforms to scrape
- https://unstop.com/hackathons
- https://devfolio.co/hackathons
- https://hackerearth.com/challenges/hackathon/
- https://github.com/OWASP-STUDENT-CHAPTER/oss-programs
- https://externship.github.in/

### Reference GitHub repos
- https://github.com/tcpsyn/CareerPulse
- https://github.com/ShaikhWarsi/HackathonHunt
- https://github.com/Jain-Tirth/OpportuneX
- https://github.com/Surajv311/one4All
- https://github.com/yashisrani/List-of-OpenSource-Programs
- https://github.com/CodeCompasss/repeto
- https://github.com/jonahr4/InternAtlas
- https://github.com/Venkat-Kolasani/FutureStack
- https://github.com/didtheyghostme/didtheyghostme
- https://github.com/gpossst/opentern

### Inspiration
- https://osatlas.tech (OS Atlas - GSoC explorer)
- https://issuescout.dev (IssueScout - beginner OSS issues)
- https://campus-sphere-orcin.vercel.app (CampusSphere - academic events)
- https://codecompasss.github.io/repeto/ (Repeto - recurring opportunities)
- https://oscode.co.in (OSCode - India dev community)