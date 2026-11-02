from .base import GenericScraper, ScraperResult, SourceConfig, register_scraper, get_scrapers_for_vertical, get_all_source_keys, Vertical, SCRAPER_REGISTRY
from .linkedin_guest import LinkedInGuestScraper

# --- Hackathon scrapers ---
from .devfolio import DevfolioScraper
from .unstop import UnstopScraper
from .hackerearth import HackerEarthScraper
from .devpost import DevpostScraper
from .hack2skill import Hack2SkillScraper
from .mlh import MLHScraper
from .dorahacks import DoraHacksScraper
from .techgig import TechGigScraper
from .hackerrank import HackerRankScraper
from .codechef import CodeChefScraper
from .reskilll import ReskilllScraper

# --- Internship scrapers ---
from .internshala import InternshalaScraper
from .linkedin_internships import LinkedinInternshipsScraper
from .indeed_internships import IndeedInternshipsScraper
from .hellointern import HelloInternScraper
from .letsintern import LetsInternScraper
from .twenty19 import Twenty19Scraper
from .glassdoor_internships import GlassdoorInternshipsScraper
from .myinternships import MyInternshipsScraper
from .aicte_internship import AICTEInternshipScraper

# --- Job scrapers ---
from .internshala_jobs import InternshalaJobsScraper
from .naukri import NaukriScraper
from .adzuna import AdzunaScraper
from .linkedin_jobs import LinkedinJobsScraper
from .indeed_jobs import IndeedJobsScraper
from .foundit import FounditScraper
from .shine import ShineScraper
from .apna import ApnaScraper
from .instahyre import InstahyreScraper
from .hirist import HiristScraper
from .timesjobs import TimesJobsScraper
from .onjob import OnJobScraper
from .workindia import WorkIndiaScraper
from .freshersworld import FreshersworldScraper
from .skill_india import SkillIndiaScraper

# --- Lateral / experienced job scrapers ---
from .cutshort import CutshortScraper
from .wellfound import WellfoundScraper

# --- India-specific curated programs ---
from .sih import SIHScraper
from .india_programs import IndiaProgramsScraper

# ============================================================
# SCHOLARSHIP & FELLOWSHIP SCRAPERS
# ============================================================
from .buddy4study import Buddy4StudyScraper
from .ambassador import AmbassadorScraper
from .fellowship import FellowshipScraper

# ============================================================
# SCRAPER REGISTRY
# ============================================================

# -- Hackathons --
register_scraper("devfolio", SourceConfig(
    name="Devfolio", verticals=["hackathon"], priority="critical",
    interval_hours=12, max_pages=5, description="Devfolio hackathons API",
))
register_scraper("devpost", SourceConfig(
    name="Devpost", verticals=["hackathon"], priority="critical",
    interval_hours=12, max_pages=5, description="Devpost hackathons API",
))
register_scraper("hack2skill", SourceConfig(
    name="Hack2Skill", verticals=["hackathon"], priority="high",
    interval_hours=12, max_pages=10, description="Hack2Skill hackathons API",
))
register_scraper("mlh", SourceConfig(
    name="MLH", verticals=["hackathon"], priority="high",
    interval_hours=24, max_pages=1, description="MLH season events (Inertia.js)",
))
register_scraper("hackerearth", SourceConfig(
    name="HackerEarth", verticals=["hackathon", "internship"], priority="high",
    interval_hours=12, max_pages=1, description="HackerEarth challenges + hiring",
))
register_scraper("unstop", SourceConfig(
    name="Unstop", verticals=["hackathon", "internship"], priority="critical",
    interval_hours=12, max_pages=5, description="Unstop hackathons + internships",
))
register_scraper("dorahacks", SourceConfig(
    name="DoraHacks", verticals=["hackathon"], priority="high",
    interval_hours=12, max_pages=5, description="DoraHacks hackathons API",
))
register_scraper("techgig", SourceConfig(
    name="TechGig", verticals=["hackathon"], priority="high",
    interval_hours=12, max_pages=3, requires_playwright=True,
    description="TechGig hackathons (may need JS)",
))
register_scraper("hackerrank", SourceConfig(
    name="HackerRank", verticals=["hackathon"], priority="medium",
    interval_hours=12, max_pages=3, description="HackerRank upcoming contests",
))
register_scraper("codechef", SourceConfig(
    name="CodeChef", verticals=["hackathon"], priority="medium",
    interval_hours=12, max_pages=1, description="CodeChef future contests API",
))
register_scraper("reskilll", SourceConfig(
    name="Reskilll", verticals=["hackathon"], priority="high",
    interval_hours=12, max_pages=5, description="Reskilll hackathon listings (RSC payload)",
))

# -- Internships --
register_scraper("internshala", SourceConfig(
    name="Internshala", verticals=["internship"], priority="critical",
    interval_hours=6, max_pages=10, description="Internshala internships (two-pass)",
))
register_scraper("linkedin_internships", SourceConfig(
    name="LinkedInInternships", verticals=["internship"], priority="critical",
    interval_hours=6, max_pages=3,
    description="LinkedIn internships via guest API",
))
register_scraper("hellointern", SourceConfig(
    name="HelloIntern", verticals=["internship"], priority="high",
    interval_hours=12, max_pages=3, description="HelloIntern internship listings",
))
register_scraper("letsintern", SourceConfig(
    name="LetsIntern", verticals=["internship"], priority="high",
    interval_hours=12, max_pages=3, description="LetsIntern listings (Cloudflare)",
))
register_scraper("myinternships", SourceConfig(
    name="MyInternships", verticals=["internship"], priority="high",
    interval_hours=6, max_pages=5, description="MyInternships.in internship listings",
))
register_scraper("twenty19", SourceConfig(
    name="Twenty19", verticals=["internship"], priority="medium",
    interval_hours=12, max_pages=3, requires_playwright=True,
    description="Twenty19 internship listings",
))
register_scraper("aicte_internship", SourceConfig(
    name="AICTEInternship", verticals=["internship"], priority="low",
    interval_hours=24, max_pages=3, description="AICTE Internship Portal listings",
))
register_scraper("indeed_internships", SourceConfig(
    name="IndeedInternships", verticals=["internship"], priority="medium",
    interval_hours=12, max_pages=3, requires_playwright=True,
    description="Indeed India internships",
))
register_scraper("glassdoor_internships", SourceConfig(
    name="GlassdoorInternships", verticals=["internship"], priority="medium",
    interval_hours=12, max_pages=3, requires_playwright=True, status="unstable",
    description="Glassdoor India internships (DOM changes frequently)",
))

# -- Jobs --
register_scraper("internshala_jobs", SourceConfig(
    name="InternshalaJobs", verticals=["job"], priority="critical",
    interval_hours=6, max_pages=3, description="Internshala fresher jobs",
))
register_scraper("adzuna", SourceConfig(
    name="Adzuna", verticals=["job"], priority="high",
    interval_hours=12, max_pages=3, requires_api_key=True,
    description="Adzuna API entry-level tech jobs",
))
register_scraper("linkedin_jobs", SourceConfig(
    name="LinkedInJobs", verticals=["job"], priority="critical",
    interval_hours=6, max_pages=3,
    description="LinkedIn entry-level jobs via guest API",
))
register_scraper("foundit", SourceConfig(
    name="Foundit", verticals=["job"], priority="high",
    interval_hours=12, max_pages=3, requires_playwright=True,
    description="Foundit (ex-Monster) jobs",
))
register_scraper("shine", SourceConfig(
    name="Shine", verticals=["job"], priority="high",
    interval_hours=12, max_pages=3, requires_playwright=True,
    description="Shine.com fresher jobs",
))
register_scraper("apna", SourceConfig(
    name="Apna", verticals=["job"], priority="high",
    interval_hours=12, max_pages=1,
    description="Apna.co entry-level jobs (SSR HTML)",
))
register_scraper("instahyre", SourceConfig(
    name="Instahyre", verticals=["job"], priority="medium",
    interval_hours=12, max_pages=3, requires_playwright=True,
    description="Instahyre tech jobs (Cloudflare)",
))
register_scraper("hirist", SourceConfig(
    name="Hirist", verticals=["job"], priority="medium",
    interval_hours=12, max_pages=3, description="Hirist tech jobs API/BS4",
))
register_scraper("workindia", SourceConfig(
    name="WorkIndia", verticals=["job"], priority="high",
    interval_hours=6, max_pages=3, description="WorkIndia blue-collar & fresher jobs",
))
register_scraper("indeed_jobs", SourceConfig(
    name="IndeedJobs", verticals=["job"], priority="high",
    interval_hours=12, max_pages=3, requires_playwright=True,
    description="Indeed India fresher jobs (via Playwright)",
))
register_scraper("onjob", SourceConfig(
    name="OnJob", verticals=["job"], priority="high",
    interval_hours=12, max_pages=1, description="OnJob.io free job feed",
))
register_scraper("timesjobs", SourceConfig(
    name="TimesJobs", verticals=["job"], priority="critical",
    interval_hours=6, max_pages=5, description="TimesJobs fresher & entry-level jobs",
))
register_scraper("freshersworld", SourceConfig(
    name="Freshersworld", verticals=["job", "internship"], priority="high",
    interval_hours=6, max_pages=5, description="Freshersworld fresher jobs & internships",
))
register_scraper("skill_india", SourceConfig(
    name="SkillIndia", verticals=["job", "internship"], priority="low",
    interval_hours=24, max_pages=3, description="Skill India Portal listings",
))
register_scraper("naukri", SourceConfig(
    name="Naukri", verticals=["job"], priority="medium",
    interval_hours=12, max_pages=3, requires_playwright=True,
    description="Naukri fresher jobs (Playwright stealth)",
))

# -- Lateral / experienced jobs --
register_scraper("cutshort", SourceConfig(
    name="CutShort", verticals=["job_lateral"], priority="high",
    interval_hours=6, max_pages=3, requires_playwright=True,
    description="CutShort startup lateral roles (2-10yr) with API intercept",
))
register_scraper("wellfound", SourceConfig(
    name="Wellfound", verticals=["job_lateral"], priority="low",
    interval_hours=24, max_pages=1, requires_playwright=True, status="unstable",
    description="Wellfound/AngelList startup jobs (Playwright, site frequently restructures)",
))

# -- Scholarships & Fellowships --
register_scraper("buddy4study", SourceConfig(
    name="Buddy4Study", verticals=["scholarship"], priority="high",
    interval_hours=24, max_pages=2, requires_playwright=True,
    description="Buddy4Study scholarships (Playwright)",
))
register_scraper("ambassador", SourceConfig(
    name="Ambassador", verticals=["ambassador"], priority="medium",
    interval_hours=48, max_pages=1,
    description="Campus ambassador programs",
))
# -- India-specific curated programs --
register_scraper("india_programs", SourceConfig(
    name="IndiaPrograms", verticals=["internship", "scholarship", "fellowship", "event"], priority="critical",
    interval_hours=24, max_pages=1,
    description="Curated India-specific programs (18 sources)",
))

register_scraper("fellowship", SourceConfig(
    name="Fellowship", verticals=["fellowship"], priority="medium",
    interval_hours=48, max_pages=1,
    description="Tech fellowships (C4GT, Outreachy, MLH)",
))

# ============================================================
# REGISTRY LOOKUP
# ============================================================

def get_scraper_class(source_key: str):
    mapping = {
        "devfolio": DevfolioScraper,
        "devpost": DevpostScraper,
        "hack2skill": Hack2SkillScraper,
        "mlh": MLHScraper,
        "hackerearth": HackerEarthScraper,
        "unstop": UnstopScraper,
        "dorahacks": DoraHacksScraper,
        "techgig": TechGigScraper,
        "hackerrank": HackerRankScraper,
        "codechef": CodeChefScraper,
        "reskilll": ReskilllScraper,
        "internshala": InternshalaScraper,
        "linkedin_internships": LinkedinInternshipsScraper,
        "indeed_internships": IndeedInternshipsScraper,
        "hellointern": HelloInternScraper,
        "letsintern": LetsInternScraper,
        "twenty19": Twenty19Scraper,
        "glassdoor_internships": GlassdoorInternshipsScraper,
        "myinternships": MyInternshipsScraper,
        "aicte_internship": AICTEInternshipScraper,
        "internshala_jobs": InternshalaJobsScraper,
        "naukri": NaukriScraper,
        "adzuna": AdzunaScraper,
        "linkedin_jobs": LinkedinJobsScraper,
        "indeed_jobs": IndeedJobsScraper,
        "foundit": FounditScraper,
        "shine": ShineScraper,
        "apna": ApnaScraper,
        "instahyre": InstahyreScraper,
        "hirist": HiristScraper,
        "onjob": OnJobScraper,
        "timesjobs": TimesJobsScraper,
        "workindia": WorkIndiaScraper,
        "freshersworld": FreshersworldScraper,
        "skill_india": SkillIndiaScraper,
        "cutshort": CutshortScraper,
        "wellfound": WellfoundScraper,
        "sih": SIHScraper,
        "india_programs": IndiaProgramsScraper,
        "buddy4study": Buddy4StudyScraper,
        "ambassador": AmbassadorScraper,
        "fellowship": FellowshipScraper,
    }
    return mapping.get(source_key)

__all__ = [
    "GenericScraper", "ScraperResult", "SourceConfig",
    "register_scraper", "get_scrapers_for_vertical", "get_all_source_keys",
    "get_scraper_class", "SCRAPER_REGISTRY",
]
