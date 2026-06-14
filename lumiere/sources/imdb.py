"""IMDB rating scraper — fetches IMDB ratings for movies."""

import re
import time
import json
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from ..core.models import IMDBScore

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
}


def _extract_from_jsonld(soup: BeautifulSoup) -> dict:
    """Extract rating from JSON-LD script tag on IMDB pages."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if not isinstance(data, dict):
                continue
            agg = data.get("aggregateRating", {})
            result = {}
            if agg.get("ratingValue"):
                result["rating"] = float(agg["ratingValue"])
            if agg.get("ratingCount"):
                result["vote_count"] = int(agg["ratingCount"])
            return result
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    return {}


def _extract_from_html(soup: BeautifulSoup) -> dict:
    """Extract rating from visible HTML elements on IMDB pages."""
    result = {}

    # Try the star rating element
    star_elem = soup.find("span", class_="sc-eb51e184-1")
    if not star_elem:
        star_elem = soup.find("span", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
    if not star_elem:
        star_elem = soup.find(string=re.compile(r"^\d\.\d/\d+"))
    if star_elem:
        text = star_elem.get_text(strip=True) if hasattr(star_elem, "get_text") else str(star_elem)
        m = re.search(r"(\d+\.?\d*)\s*/\s*10", text)
        if m:
            result["rating"] = float(m.group(1))

    # Try vote count
    vote_elem = soup.find("span", class_="sc-eb51e184-3")
    if not vote_elem:
        vote_elem = soup.find("span", {"data-testid": "hero-rating-bar__aggregate-rating__count"})
    if not vote_elem:
        # Try any element with "K" or "M" vote patterns
        vote_elem = soup.find(string=re.compile(r"(\d+[KMB]?\d*)\s*(ratings?|votes?)", re.I))
    if vote_elem:
        text = vote_elem.get_text(strip=True) if hasattr(vote_elem, "get_text") else str(vote_elem)
        m = re.search(r"(\d+(?:\.\d+)?)([KMB])?\s*(?:ratings?|votes?)", text, re.I)
        if m:
            val = float(m.group(1))
            unit = m.group(2)
            if unit == "K":
                val *= 1000
            elif unit == "M":
                val *= 1000000
            result["vote_count"] = int(val)

    # Try the star rating in the main section
    rating_bar = soup.find("div", {"data-testid": "hero-rating-bar__aggregate-rating"})
    if rating_bar:
        for span in rating_bar.find_all("span"):
            text = span.get_text(strip=True)
            m = re.search(r"(\d+\.?\d*)", text)
            if m:
                val = float(m.group(1))
                if 1 <= val <= 10 and val != int(val):
                    result["rating"] = val

    return result


def fetch_imdb_rating(
    imdb_id: str,
    timeout: int = 10,
) -> IMDBScore:
    """Fetch IMDB rating for a movie by its IMDB ID (e.g., 'tt1375666')."""
    result = IMDBScore()
    url = f"https://www.imdb.com/title/{imdb_id}/"
    result.url = url

    try:
        time.sleep(0.3)  # Be polite
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code != 200:
            return result

        soup = BeautifulSoup(resp.text, "lxml")

        extracted = {}
        extracted.update(_extract_from_jsonld(soup))
        extracted.update(_extract_from_html(soup))

        if extracted.get("rating") is not None:
            result.rating = extracted["rating"]
        if extracted.get("vote_count") is not None:
            result.vote_count = extracted["vote_count"]

        if result.rating is not None:
            result.fetched = True

    except Exception as e:
        logger.debug(f"IMDB scrape failed for {url}: {e}")

    return result
