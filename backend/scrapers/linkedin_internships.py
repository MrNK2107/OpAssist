import logging

from .linkedin_guest import LinkedInGuestScraper

logger = logging.getLogger(__name__)


class LinkedinInternshipsScraper(LinkedInGuestScraper):
    platform_name = "LinkedInInternships"
    source_key = "linkedin_internships"
    verticals = ["internship"]

    @property
    def item_type(self) -> str:
        return "internship"

    @property
    def search_queries(self) -> list[str]:
        return [f"internship {q}" for q in self.SEARCH_QUERIES]
