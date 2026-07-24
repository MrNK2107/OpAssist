import logging
from datetime import datetime, timezone

from .base import GenericScraper

logger = logging.getLogger(__name__)


class IndiaProgramsScraper(GenericScraper):
    """India-specific programs scraper — curated high-value opportunities.

    Aggregates India-exclusive programs that other scrapers miss:
    - GitHub India Externship
    - Microsoft Engage Mentorship
    - Google STEP India
    - FOSSEE Summer Fellowship (IIT Bombay)
    - Code for GovTech (C4GT)
    - Flipkart Runway
    - Amazon WOW Internship
    - Crio Winter of Doing
    - S.N. Bose Scholars Program
    - Adobe India Women-in-Tech Scholarship
    - Generation Google Scholarship (APAC)
    - Venkat Panchapakesan Memorial Scholarship

    These are sourced from the curated lists in SPEC.md (one4All, yashisrani/List-of-OpenSource-Programs).
    """

    platform_name = "IndiaPrograms"
    source_key = "india_programs"
    verticals = ["internship", "scholarship", "fellowship", "event"]

    PROGRAMS = [
        {
            "title": "GitHub India Externship",
            "type": "internship",
            "organizer": "GitHub India",
            "description": "90-day remote fellowship for pre-final year students at GitHub Campus Partner schools. Work on real open source projects with GitHub mentors.",
            "url": "https://externship.github.in/",
            "location": "Remote",
            "prize": "Paid (stipend)",
            "date": "",
            "tags": ["github", "externship", "open-source", "india", "remote", "pre-final-year"],
            "difficulty": "intermediate",
        },
        {
            "title": "Microsoft Engage Mentorship",
            "type": "internship",
            "organizer": "Microsoft India",
            "description": "May-June mentorship program for sophomores. Top performers get Microsoft India internship offers.",
            "url": "https://microsoftengage.com/",
            "location": "Remote",
            "prize": "Internship opportunity",
            "date": "",
            "tags": ["microsoft", "engage", "mentorship", "india", "sophomore"],
            "difficulty": "beginner",
        },
        {
            "title": "Google STEP India",
            "type": "internship",
            "organizer": "Google India",
            "description": "Student Training in Engineering Program — a 12-week internship for first and second-year university students. Focus on computer science fundamentals and software engineering.",
            "url": "https://buildyourfuture.withgoogle.com/programs/step/",
            "location": "India",
            "prize": "Paid internship + mentorship",
            "date": "",
            "tags": ["google", "step", "india", "first-year", "second-year", "internship"],
            "difficulty": "beginner",
        },
        {
            "title": "FOSSEE Summer Fellowship",
            "type": "fellowship",
            "organizer": "IIT Bombay",
            "description": "Free and Open Source Software for Education — paid summer fellowship at IIT Bombay. Work on open source tools for education. India-specific.",
            "url": "https://fossee.in/fellowship/",
            "location": "IIT Bombay, India",
            "prize": "Paid fellowship (Rs. 10,000+/month)",
            "date": "",
            "tags": ["fossee", "iit-bombay", "open-source", "summer", "fellowship", "india"],
            "difficulty": "intermediate",
        },
        {
            "title": "Code for GovTech (C4GT) Dedicated Mentoring Program",
            "type": "fellowship",
            "organizer": "Code for GovTech",
            "description": "Annual 3-month mentoring program. Contribute to open source government technology projects. Build portfolio and impact public services in India.",
            "url": "https://codeforgovtech.in/",
            "location": "Remote",
            "prize": "Stipend + mentorship",
            "date": "",
            "tags": ["c4gt", "govtech", "open-source", "india", "fellowship", "mentorship"],
            "difficulty": "intermediate",
        },
        {
            "title": "Flipkart Runway",
            "type": "internship",
            "organizer": "Flipkart India",
            "description": "Diversity hiring program for women in tech. Pre-final year women students. Get mentored by Flipkart leaders and compete for internship offers.",
            "url": "https://www.flipkart.com/careers/runway",
            "location": "India",
            "prize": "Paid internship + PPI opportunity",
            "date": "",
            "tags": ["flipkart", "runway", "women-in-tech", "diversity", "india", "internship"],
            "difficulty": "intermediate",
        },
        {
            "title": "Amazon WOW Internship",
            "type": "internship",
            "organizer": "Amazon India",
            "description": "Virtual recruiting program for women in tech in India. Connects women students with Amazon internship opportunities. Includes mentorship and skill-building.",
            "url": "https://amazonwowindia.splashthat.com/",
            "location": "India",
            "prize": "Paid internship + mentorship",
            "date": "",
            "tags": ["amazon", "wow", "women-in-tech", "india", "internship", "diversity"],
            "difficulty": "intermediate",
        },
        {
            "title": "Crio Winter of Doing",
            "type": "internship",
            "organizer": "Crio.Do",
            "description": "Work on real-world software development projects during winter break. For final year students and working professionals. Build portfolio with micro-internships.",
            "url": "https://www.crio.do/crio-winter-of-doing/",
            "location": "Remote",
            "prize": "Certification + project experience",
            "date": "",
            "tags": ["crio", "winter-of-doing", "project", "india", "micro-internship"],
            "difficulty": "beginner",
        },
        {
            "title": "Generation Google Scholarship (APAC)",
            "type": "scholarship",
            "organizer": "Google",
            "description": "For women in tech pursuing computer science degrees in Asia Pacific. Includes financial support and invitation to Google's scholars retreat. Opens annually in March.",
            "url": "https://buildyourfuture.withgoogle.com/scholarships/generation-google-scholarship/",
            "location": "APAC",
            "prize": "Up to $5,000 USD",
            "date": "",
            "tags": ["google", "scholarship", "women-in-tech", "apac", "india"],
            "difficulty": "intermediate",
        },
        {
            "title": "Adobe India Women-in-Tech Scholarship",
            "type": "scholarship",
            "organizer": "Adobe India",
            "description": "For women pursuing engineering in India. Includes financial award, mentorship, and internship opportunity at Adobe India. Opens annually in August.",
            "url": "https://www.adobe.com/in/women-in-tech.html",
            "location": "India",
            "prize": "Scholarship + internship opportunity",
            "date": "",
            "tags": ["adobe", "women-in-tech", "scholarship", "india", "mentorship"],
            "difficulty": "intermediate",
        },
        {
            "title": "Venkat Panchapakesan Memorial Scholarship",
            "type": "scholarship",
            "organizer": "Google",
            "description": "Honoring the memory of Venkat Panchapakesan. For students in India pursuing computer science. Includes financial support and mentorship.",
            "url": "https://buildyourfuture.withgoogle.com/scholarships/venkat-panchapakesan-memorial-scholarship/",
            "location": "India",
            "prize": "Financial award + mentorship",
            "date": "",
            "tags": ["google", "scholarship", "india", "memorial", "computer-science"],
            "difficulty": "beginner",
        },
        {
            "title": "Smart India Hackathon (SIH)",
            "type": "hackathon",
            "organizer": "Government of India",
            "description": "India's flagship hackathon organized by Ministry of Education's Innovation Cell. Problem statements from govt departments. Software and hardware editions. Biggest hackathon in India.",
            "url": "https://www.sih.gov.in/",
            "location": "India",
            "prize": "Prizes, recognition, incubation opportunities",
            "date": "",
            "tags": ["sih", "government", "hackathon", "india", "flagship", "ministry-of-education"],
            "difficulty": "intermediate",
        },
        {
            "title": "Flipkart Grid",
            "type": "hackathon",
            "organizer": "Flipkart India",
            "description": "Major India hackathon by Flipkart. PPI (Pre-Placement Interview) opportunities for top performers. Multiple tracks including tech, design, and supply chain.",
            "url": "https://unstop.com/competitions/flipkart-grid",
            "location": "India",
            "prize": "PPI + prizes up to INR 10L+",
            "date": "",
            "tags": ["flipkart", "grid", "hackathon", "india", "ppi", "competition"],
            "difficulty": "intermediate",
        },
        {
            "title": "Adobe India Hackathon",
            "type": "hackathon",
            "organizer": "Adobe India",
            "description": "Annual hackathon by Adobe India. MacBook Air + INR 1L/month internship + trip to Adobe HQ for winners.",
            "url": "https://www.adobe.com/in/hackathon.html",
            "location": "India",
            "prize": "MacBook Air + internship + Adobe HQ trip",
            "date": "",
            "tags": ["adobe", "hackathon", "india", "internship"],
            "difficulty": "intermediate",
        },
        {
            "title": "CodeAgon by CodeNation",
            "type": "hackathon",
            "organizer": "CodeNation India",
            "description": "Annual coding competition by CodeNation India. INR 200K+ prizes, SDE interviews, and internship opportunities.",
            "url": "https://www.codenation.com/hiring/codeagon.html",
            "location": "India",
            "prize": "INR 200K+ + SDE interviews + internships",
            "date": "",
            "tags": ["codenation", "codeagon", "hackathon", "india", "coding-competition"],
            "difficulty": "advanced",
        },
        {
            "title": "Capgemini Tech Challenge",
            "type": "hackathon",
            "organizer": "Capgemini India",
            "description": "Largest campus hackathon in India with 7.5L+ participants. Multiple tracks across tech domains. Hiring pipeline for top performers.",
            "url": "https://www.capgemini.com/in-en/careers/capgemini-tech-challenge/",
            "location": "India",
            "prize": "Prizes + hiring pipeline",
            "date": "",
            "tags": ["capgemini", "tech-challenge", "hackathon", "india", "campus"],
            "difficulty": "intermediate",
        },
        {
            "title": "ET AI Hackathon",
            "type": "hackathon",
            "organizer": "Economic Times India",
            "description": "AI/ML hackathon by Economic Times India. INR 10L+ prizes and hiring pipeline.",
            "url": "https://hackathon.economictimes.com/",
            "location": "India",
            "prize": "INR 10L+ prizes + hiring pipeline",
            "date": "",
            "tags": ["economic-times", "ai", "hackathon", "india", "machine-learning"],
            "difficulty": "advanced",
        },
        {
            "title": "S.N. Bose Scholars Program",
            "type": "fellowship",
            "organizer": "Indo-US Science and Technology Forum",
            "description": "India-US research internship for Indian science and engineering students. Spend summer at top US universities doing research. Fully funded.",
            "url": "https://iusstf.org/s-n-bose-scholars-program",
            "location": "United States",
            "prize": "Fully funded — travel, stipend, housing",
            "date": "",
            "tags": ["research", "fellowship", "india", "usa", "summer", "fully-funded"],
            "difficulty": "advanced",
        },
    ]

    def scrape(self, client) -> list[dict]:
        items = []
        for program in self.PROGRAMS:
            items.append({
                "title": program["title"],
                "type": program["type"],
                "link": program["url"],
                "organizer": program["organizer"],
                "description": program["description"],
                "location": program["location"],
                "prize": program["prize"],
                "date": program["date"],
                "tags": program["tags"],
                "difficulty": program["difficulty"],
                "image_url": "",
                "is_closed": False,
            })
        logger.info(f"IndiaPrograms: {len(items)} curated programs loaded")
        return items
