import logging

from .linkedin_guest import LinkedInGuestScraper

logger = logging.getLogger(__name__)


class LinkedinJobsScraper(LinkedInGuestScraper):
    platform_name = "LinkedInJobs"
    source_key = "linkedin_jobs"
    verticals = ["job"]

    @property
    def item_type(self) -> str:
        return "job"
