"""Rotten Tomatoes scraper — fetches Tomatometer and Popcornmeter scores."""

import re
import time
import logging
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from ..core.models import RottenTomatoesScore

logger = logging.getLogger(__name__)

# ── Headers to look like a real browser ──
BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def _extract_from_jsonld(soup: BeautifulSoup) -> dict:
    """Extract ratings from JSON-LD script tag."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict):
                result = {}
                agg = data.get("aggregateRating", {})
                if agg.get("ratingValue"):
                    result["tomatometer"] = int(float(agg["ratingValue"]) * 10)
                if agg.get("ratingCount"):
                    result["tomatometer_count"] = int(agg["ratingCount"])
                # Audience rating often in a different field
                rev = data.get("review", [])
                if isinstance(rev, dict):
                    rev = [rev]
                for r in rev:
                    if r.get("author", {}).get("@type") == "Organization":
                        # Critic review from RT
                        pass
                    elif r.get("author", {}).get("@type") == "Person":
                        # Could be audience review
                        pass
                return result
        except Exception:
            continue
    return {}


def _extract_from_rt_json(soup: BeautifulSoup) -> dict:
    """Try to extract ratings from embedded RT data in script tags."""
    result = {}
    for script in soup.find_all("script"):
        if not script.string:
            continue
        text = script.string

        # Look for tomatometer score
        m = re.search(r'"tomatometerScore":\s*\{[^}]*"value"\s*:\s*(\d+)', text)
        if m:
            result["tomatometer"] = int(m.group(1))

        m = re.search(r'"audienceScore":\s*\{[^}]*"value"\s*:\s*(\d+)', text)
        if m:
            result["popcornmeter"] = int(m.group(1))

        m = re.search(r'"ratingCount":\s*(\d+)', text)
        if m and "tomatometer_count" not in result:
            # This could be either critic or audience count
            result.setdefault("tomatometer_count", int(m.group(1)))

        # Try another pattern
        m = re.search(r'"criticsRating":\s*"([^"]+)"', text)
        if m:
            result["critics_rating"] = m.group(1)

        m = re.search(r'"audienceRating":\s*"([^"]+)"', text)
        if m:
            result["audience_rating"] = m.group(1)

    return result


def _extract_from_html(soup: BeautifulSoup) -> dict:
    """Extract ratings visible in the HTML DOM."""
    result = {}
    # Look for the scoreboard
    scoreboard = soup.find("score-board-deprecated")
    if scoreboard:
        # Try to get attributes
        for attr in ["tomatometerscore", "audiencescore"]:
            val = scoreboard.get(attr)
            if val:
                key = "tomatometer" if "tomatometer" in attr else "popcornmeter"
                try:
                    result[key] = int(val)
                except ValueError:
                    pass

    # Try rt-button elements
    for btn in soup.find_all("rt-button"):
        slot = btn.get("slot", "")
        if "critics" in slot or "tomatometer" in slot:
            text = btn.get_text(strip=True)
            m = re.search(r"(\d+)%", text)
            if m:
                result["tomatometer"] = int(m.group(1))
        elif "audience" in slot:
            text = btn.get_text(strip=True)
            m = re.search(r"(\d+)%", text)
            if m:
                result["popcornmeter"] = int(m.group(1))

    # Try finding percentage text near certain labels
    for label_text in ["Tomatometer", "Critic Score", "Critics"]:
        label = soup.find(string=re.compile(label_text, re.I))
        if label:
            parent = label.parent
            if parent:
                pct = parent.find(string=re.compile(r"\d+%"))
                if pct:
                    m = re.search(r"(\d+)%", pct)
                    if m:
                        result["tomatometer"] = int(m.group(1))

    for label_text in ["Audience Score", "Popcornmeter", "Audience"]:
        label = soup.find(string=re.compile(label_text, re.I))
        if label:
            parent = label.parent
            if parent:
                pct = parent.find(string=re.compile(r"\d+%"))
                if pct:
                    m = re.search(r"(\d+)%", pct)
                    if m:
                        result["popcornmeter"] = int(m.group(1))

    # Critic consensus
    consensus = soup.find(string=re.compile(r"Critics Consensus", re.I))
    if consensus:
        parent = consensus.parent
        if parent:
            text = parent.get_text(strip=True)
            text = re.sub(r"^Critics?\s*Consensus\s*:?\s*", "", text, flags=re.I)
            if text and len(text) > 10:
                result["consensus"] = text

    return result


def fetch_rt_scores(
    title: str,
    year: str = "",
    imdb_id: Optional[str] = None,
    user_agent: Optional[str] = None,
    timeout: int = 10,
) -> RottenTomatoesScore:
    """Fetch Rotten Tomatoes scores for a movie by scraping its RT page.

    Tries multiple strategies to extract Tomatometer and Popcornmeter.
    """
    headers = {"User-Agent": user_agent or BASE_HEADERS["User-Agent"]}
    headers.update({k: v for k, v in BASE_HEADERS.items() if k != "User-Agent"})

    result = RottenTomatoesScore()

    # Strategy 1: Try constructing RT URL from IMDB ID
    # RT uses format: https://www.rottentomatoes.com/m/<slug>
    # We need the slug. First try searching RT.
    search_url = f"https://www.rottentomatoes.com/search?search={quote(title)}"
    slug = None

    try:
        resp = requests.get(search_url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")

            # Find search results
            # Look for movie results in the search page
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("/m/") and href != "/m/":
                    # Check if the title matches
                    link_text = link.get_text(strip=True).lower()
                    if title.lower() in link_text:
                        slug = href
                        break

            # If not found, try the first movie result
            if not slug:
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if href.startswith("/m/") and href != "/m/":
                        slug = href
                        break
    except Exception as e:
        logger.debug(f"RT search failed for '{title}': {e}")
        return result

    if not slug:
        return result

    # Strategy 2: Scrape the movie page
    movie_url = f"https://www.rottentomatoes.com{slug}"
    result.url = movie_url

    try:
        time.sleep(0.5)  # Be polite
        resp = requests.get(movie_url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return result

        soup = BeautifulSoup(resp.text, "lxml")

        # Try all extraction methods
        extracted = {}
        extracted.update(_extract_from_jsonld(soup))
        extracted.update(_extract_from_rt_json(soup))
        extracted.update(_extract_from_html(soup))

        if extracted.get("tomatometer") is not None:
            result.tomatometer = extracted["tomatometer"]
        if extracted.get("tomatometer_count") is not None:
            result.tomatometer_count = extracted["tomatometer_count"]
        if extracted.get("popcornmeter") is not None:
            result.popcornmeter = extracted["popcornmeter"]
        if extracted.get("consensus"):
            result.consensus = extracted["consensus"]

        # If we got any data, mark as fetched
        if result.tomatometer is not None or result.popcornmeter is not None:
            result.fetched = True

    except Exception as e:
        logger.debug(f"RT scrape failed for {movie_url}: {e}")

    return result


def fetch_rt_scores_batch(
    movies: list,
    user_agent: Optional[str] = None,
    max_workers: int = 3,
) -> list:
    """Fetch RT scores for a list of movie dicts with title/year."""
    results = []
    for i, movie in enumerate(movies):
        title = movie.get("title", "") if isinstance(movie, dict) else movie.title
        year = movie.get("year", "") if isinstance(movie, dict) else movie.year
        imdb_id = movie.get("imdb_id") if isinstance(movie, dict) else movie.imdb_id

        rt = fetch_rt_scores(title, year, imdb_id, user_agent)
        results.append(rt)

        if i < len(movies) - 1:
            time.sleep(0.3)  # Rate limiting

    return results
