# OpAssist demo script (about 4 minutes)

## Setup (once)

```bash
cd frontend
npm ci
npm run build
npm start          # http://localhost:3000
```

You don't need a backend, database or Firebase keys for this demo. Use a fresh browser profile or a private window so the Radar starts from the sample profile.

The demo data is a snapshot of 143 real listings, hand-checked on 2 Nov 2026. Countdowns are measured from today's date in IST. If you demo long after the snapshot, many listings will show as closed. Regenerate the seed with `node scripts/snapshot-seed.mjs <dir> <date>` (see the README).

## 1. The problem (30 s): landing page `/`

- Read the headline: *"Every hackathon and internship worth your time, ranked for you."*
- Point at the example match card: a score, three plain-language reasons and one caution.
- Scroll to **Where OpAssist fits**. We don't compete with Unstop, Devfolio, Internshala or LinkedIn; students still apply there. OpAssist finds the listing, checks eligibility and keeps the date.
- Click **Try it now, no sign-up**.

## 2. Matching that explains itself (60 s): `/radar`

- The sample student is in **2nd year in Chennai**, works **solo**, and knows Python, React, AI/ML and LLMs.
- The top card is an AI engineering internship. Read its reasons: the skills it asks for, remote, open to 2nd-years, solo welcome.
- **Live change:** turn off *Python* and turn on *Blockchain*. The ranking reshuffles instantly, and web3 hackathons move up.
- Set **Year of study** to *1*. Listings restricted to 2nd year onward disappear, because *I'm eligible* is on.
- Turn *I'm eligible* off. Those listings come back dimmed, with the blocker shown first: *"Open to 2nd/3rd/4th/5th year only; you are in 1st year"*.
- Set **Team size** to *Just me*, then *4 people*, and watch team-only hackathons swap in and out.

## 3. Eligibility filters (30 s)

- Tap **Hackathons** to hide them, leaving internships only. Tap it again to bring them back.
- Tap **In person** off to see only online and hybrid listings, or use **Online or Chennai**.
- Search `chennai` and you get IIT Madras Shaastra and other local events.

## 4. Deadline radar and calendar (45 s): `/radar/deadlines`

- The ink strip shows the next 28 days. Coral bars close this week; marigold bars close later.
- The lists are grouped as *Closes today*, *This week*, *Next two weeks*, *Later* and *Rolling*.
- Press **+** on two hackathons to track them.
- Press **All N to calendar** and open the downloaded `.ics` file. Each deadline is an all-day event with reminders 3 days and 1 day before. It imports into Google, Apple or Outlook calendars.

## 5. Application board (45 s): `/radar/board`

- The tracked items sit in **Shortlisted**. Move one to **Preparing** with the arrow, and type a note: *"Team: Priya + Arjun, idea: RAG over syllabus PDFs"*.
- Move another to **Applied**. Reload the page and everything is still there (stored in this browser).
- **Board deadlines to calendar** exports only what you are actually going for.

## 6. Close (15 s)

- **Save my radar** leads to sign-up. A signed-in user gets the full scraped feed from 40+ sources, bookmarks, server-side application tracking, team finder and the campus leaderboard.
- Every matching rule is deterministic and unit-tested (`frontend/lib/radar/*`, 177 frontend tests).

## Fallbacks

- If the landing page shows *"Opportunities (illustrative)"*, the backend is not running. That is expected for this demo, and the page says so.
- If the Radar shows *Nothing on the radar*, press **Reset filters**, or reset the profile to the sample with the **Sample** button.
