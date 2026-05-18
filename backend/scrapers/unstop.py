import logging
import re
from datetime import datetime
import httpx
from .base import GenericScraper

logger = logging.getLogger(__name__)


class UnstopScraper(GenericScraper):
    """Unstop scraper — hackathons, internships, scholarships."""

    platform_name = "Unstop"
    API_URL = "https://unstop.com/api/public/opportunity/search-result"

    OPPORTUNITY_TYPES = {
        "hackathons": "hackathon",
        "internships": "internship",
        "scholarships": "scholarship",
    }

    def scrape(self, client: httpx.Client) -> list[dict]:
        items = []
        for opp_type, mapped_type in self.OPPORTUNITY_TYPES.items():
            logger.info(f"Unstop fetching: {opp_type}")
            try:
                batch = self._fetch_type(client, opp_type, mapped_type)
                items.extend(batch)
                logger.info(f"Unstop {opp_type}: {len(batch)} items")
            except Exception as exc:
                logger.warning(f"Unstop {opp_type} failed: {exc}")
        return items

    def _fetch_type(self, client: httpx.Client, opp_type: str, mapped_type: str) -> list[dict]:
        all_items = []
        for page in range(1, 6):
            params = {
                "opportunity": opp_type,
                "page": page,
                "per_page": 50,
                "oppstatus": "open",
            }
            try:
                response = client.get(self.API_URL, params=params)
                if not response.is_success:
                    logger.warning(f"Unstop {opp_type} page {page}: HTTP {response.status_code}")
                    break
                payload = response.json()
                data = payload.get("data", {})
                results = data.get("data", [])
                if not results:
                    break
                for item in results:
                    parsed = self._parse_item(item, mapped_type)
                    if parsed:
                        all_items.append(parsed)
                total = data.get("total", 0)
                if page * 50 >= total:
                    break
            except Exception as exc:
                logger.warning(f"Unstop {opp_type} page {page} error: {exc}")
                break
        return all_items

    def _normalize_dt(self, raw: str) -> str:
        if not raw:
            return ""
        try:
            d = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return d.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return raw[:10] if len(raw) >= 10 else raw

    def _parse_item(self, h: dict, mapped_type: str) -> dict | None:
        title = (h.get("title") or "").strip()
        if not title:
            return None

        seo_url = h.get("seo_url") or ""
        link = seo_url or f"https://unstop.com/{h.get('public_url', '')}"

        regn_req = h.get("regnRequirements") or {}
        end_date = self._normalize_dt(regn_req.get("end_regn_dt") or h.get("end_date") or "")
        start_date = self._normalize_dt(regn_req.get("start_regn_dt") or "")

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if end_dt < datetime.now():
                    return None
            except ValueError:
                pass

        region = (h.get("region") or "online").lower()
        if region == "online":
            location = "Remote"
        else:
            locs = h.get("locations") or []
            city = locs[0].get("name", "") if locs else ""
            addr = h.get("address_with_country_logo") or {}
            country_raw = addr.get("country") or ""
            country = country_raw if isinstance(country_raw, str) else ""
            location = ", ".join(p for p in [city, country] if p)
            if not location:
                location = region.capitalize()

        org = h.get("organisation") or {}
        organizer = org.get("name", "")

        tags = []
        for t in (h.get("tags") or []):
            if isinstance(t, dict):
                tags.append(str(t.get("name", "")))
            elif isinstance(t, str):
                tags.append(t)
        for wf in (h.get("workfunction") or []):
            if isinstance(wf, dict) and wf.get("name"):
                tags.append(wf["name"])
        for rs in (h.get("required_skills") or []):
            if isinstance(rs, dict) and rs.get("skill"):
                tags.append(rs["skill"])

        prizes_list = h.get("prizes") or []
        prize_str = ""
        if prizes_list:
            parts = []
            for p in prizes_list:
                cash = p.get("cash")
                rank = p.get("rank", "")
                other = p.get("others", "")
                if cash:
                    parts.append(f"{rank}: {cash}" if rank else str(cash))
                if other:
                    parts.append(other)
            prize_str = " | ".join(parts)

        details = h.get("details") or ""
        plain_desc = re.sub(r"<[^>]+>", " ", details).strip()
        plain_desc = re.sub(r"\s+", " ", plain_desc)[:500]

        return {
            "title": title,
            "organizer": organizer,
            "start_date": start_date or None,
            "end_date": end_date or None,
            "date": end_date or "",
            "location": location,
            "link": link,
            "source_platform": "Unstop",
            "description": plain_desc,
            "prize": prize_str,
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": h.get("logoUrl2") or "",
            "type": mapped_type,
            "is_closed": h.get("status", "").upper() != "LIVE",
        }
