# OpAssist: product brief

> The opportunity radar for Indian college students. It finds the hackathons and internships you can actually enter, says why each one fits, and keeps the deadlines on your calendar.

## Audience

**Primary: undergraduate engineering and computer-applications students in India, 1st to 4th year.** Most attend tier-2 and tier-3 colleges, and their placement cell does not feed them opportunities. For them, a hackathon win or an internship is the main way to stand out. Most have a laptop and a phone, and many travel by train.

What they have in common:

- **Their time is fragmented.** Classes, labs and internal exams leave a few hours a week for "extra" work. They need to pick the right three things, not browse forty.
- **They are often unsure whether they are eligible.** "2nd year onward", "team of 2–4", "students only", "₹200 registration" and "finals in Kanpur" are buried in the rules text, and they usually find the blocker after they have already invested time.
- **Deadlines leak.** Their current system is a WhatsApp group, a Telegram channel and memory. Missing a registration by one day is the most common failure.

**Secondary:** campus club leads and placement coordinators who curate opportunities for a batch. They need the same feed with an export.

## The problem

1. **Discovery is scattered.** Hackathons live on Devfolio, Unstop, Devpost, MLH and individual college-fest sites. Internships live on Internshala, LinkedIn and career pages. Open source lives on GSoC, LFX and GitHub. Each site has its own login, search and notification settings.
2. **Ranking ignores the student.** Every platform sorts by recency, popularity or what was paid for. None of them tell a 2nd-year Python student in Chennai who works solo which five listings to apply to this week, or why.
3. **Eligibility comes after excitement.** Filters cover category and location, if anything. Year of study, team size and entry fee are free text.
4. **There is no single calendar.** A student tracking six applications across four sites has no single view of what closes when.

## Positioning

OpAssist does not replace the platforms students apply on. **It sits on top of them.** It finds the listing, checks the student can enter, explains the fit, and keeps the date. The student still applies on the organiser's page.

| | What it is great at | What it leaves open, and where OpAssist fits |
|---|---|---|
| **Unstop** | The largest catalogue of competitions, quizzes and college fests in India, with on-platform registration and team formation. | It covers only what organisers post there, ranks by popularity and promotion, and puts eligibility in rules text. OpAssist ranks Unstop listings next to everything else, per student, and shows the blockers up front. |
| **Devfolio** | The home of Indian hackathons. Great builder profiles, project galleries, and trusted organisers (ETHIndia, college MLH events). | It covers hackathons only, has no internships or scholarships, and offers no cross-platform deadline view. OpAssist links to Devfolio for applying and adds the calendar. |
| **Internshala** | The biggest student internship marketplace, with one-click apply and a huge employer base. | It covers internships and courses only, with no hackathons or open source. Its "matching" is keyword search. OpAssist explains the fit in plain language and puts internships on the same board as hackathons. |
| **LinkedIn** | Recruiter reach, and the network that matters after graduation. | It is built for experienced hires, students are an afterthought, and eligibility (year, team, fee) is not a filter. OpAssist is student-first and needs no network. |

**Where OpAssist is weaker today, stated honestly:** it is smaller than every platform above, applying always happens off-site, it has no community, team-formation or project-gallery features to match Devfolio or Unstop, and its scrapers depend on the source sites staying scrapeable. The demo dataset is a hand-checked snapshot, not a live feed.

## Differentiators

1. **Explainable matching.** Every score is the sum of visible reasons: the skills it asks for that the student has, online or in their city, open to their year, solo allowed, free, verified. Every hard blocker appears as a caution. There is no black box, and the rules are unit-tested (`frontend/lib/radar/match.ts`).
2. **Eligibility filters are on by default.** "I'm eligible" hides anything blocked by year of study, team size or audience (for example startups only). Fee and online-vs-my-city filters are one tap away.
3. **The deadline radar.** It shows four weeks of closing dates as a day-by-day strip, grouped into *today / this week / next two weeks / later / rolling*. A single `.ics` export with reminders 3 days and 1 day before works in Google, Apple and Outlook calendars with no account linking.
4. **One application board** for hackathons and internships: Shortlisted, Preparing, Applied, Heard back, with a note per card for teammates, ideas or which resume version was sent.
5. **Try before sign-up.** The Radar works fully in the browser with no account. Profile and board are stored locally. Signing up unlocks the full scraped feed, bookmarks and server-side tracking.
6. **India-first details.** IST deadline maths, Indian city names (Bengaluru/Bangalore, Gurugram/Gurgaon), roman-numeral year rules ("II and III year"), "pre-final year", and INR stipends.

## Headline features (built)

| Feature | Where | Notes |
|---|---|---|
| Personalised matching with "why this fits" | `/radar` | Profile: skills, year, city, team size, no-travel. The ranking updates live. |
| Eligibility filters | `/radar` | Kind, mode, free entry, I'm eligible, online or my city, text search. |
| Deadline radar + ICS export | `/radar/deadlines` | 28-day strip, buckets, export everything or only your board. |
| Application tracker board | `/radar/board` | 4 stages, keyboard-accessible move buttons, notes, export the board's deadlines. |

The signed-in dashboard keeps its existing features: the scraped feed, bookmarks, the applications API, the calendar, team finder, leaderboard and notifications.

## Brand

- **Name:** OpAssist, short for opportunity assistant.
- **Idea:** *a radar*. OpAssist sweeps every source, and the blip is the opportunity that fits you.
- **Mark:** an ink tile with a marigold radar sweep and one green blip (`components/brand/radar-mark.tsx`, `app/icon.svg`).
- **Palette:**
  - **Ink** `hsl(228 45% 10%)`: hero, primary text, active chips.
  - **Paper** `hsl(42 33% 96%)`: the warm off-white app background.
  - **Marigold** `hsl(38 92% 50%)`: primary actions and highlights. Marigold is the festival colour of India, and it sets OpAssist apart from the blues of LinkedIn, Unstop and Devfolio.
  - **Fit green** `hsl(160 64% 30%)`: "why this fits" and strong matches.
  - **Urgent coral** `hsl(6 74% 48%)`: deadlines within the week.
- **Type:**
  - **Bricolage Grotesque** for display: confident and a little playful.
  - **Inter** for UI text.
  - **JetBrains Mono** for every number: scores, countdowns, counts. Numbers read as data, not decoration.
- **Voice:** a senior who has done this before. Direct, specific and honest about limits. The product says "Closes in 2 days" rather than "Hurry!", and "Needs a team of at least 2; you have 1" rather than "Not eligible".
- **Accessibility:** WCAG AA contrast in light and dark mode (axe-core 4.10 shows 0 violations on the landing page, the Radar pages and login at 1366px and 390px), `prefers-reduced-motion` stops the sweep, and every icon button has a label.

## Metrics we would track

- **Activation:** percentage of visitors who change the sample profile within their first session.
- **Intent:** listings tracked per active student per week, and `.ics` exports per week.
- **Outcome:** percentage of tracked cards that reach *Applied*. This is the north star: applications submitted, not page views.
- **Trust:** reported wrong deadlines per 100 listings shown.

## Next

1. Feed the Radar from the live `/api/opportunities` once Supabase is populated. The seed file is the fallback.
2. Sync the board to `/api/applications` for signed-in users, and import the local board on first sign-in.
3. Add scholarships and open-source programmes to the Radar schema (they need eligibility fields: income, gender, state).
4. A weekly email digest of "3 new strong fits, 2 deadlines this week".
5. Club-lead mode: curate a list and share it as a link and an `.ics` feed.
