"""Multi-strategy movie scanner with TMDB + RT + IMDB enrichment."""

import time
import logging
from typing import Optional, Callable
from datetime import datetime

from .config import LumiereConfig
from .models import Movie
from ..sources.tmdb import TMDBClient
from ..sources.rottentomatoes import fetch_rt_scores
from ..sources.imdb import fetch_imdb_rating

logger = logging.getLogger(__name__)


class MovieScanner:
    """Comprehensive movie scanner — TMDB scan + RT enrichment + IMDB enrichment."""

    def __init__(self, config: Optional[LumiereConfig] = None):
        self.config = config or LumiereConfig.from_env()
        self.client = TMDBClient(self.config.api_base_url)

    def scan(
        self,
        min_rating: Optional[float] = None,
        language: Optional[str] = None,
        year_start: Optional[str] = None,
        year_end: Optional[str] = None,
        max_pages: Optional[int] = None,
        genre_ids: Optional[list[int]] = None,
        sort_methods: Optional[list[str]] = None,
        enrich: bool = True,
        fetch_rt: bool = True,
        fetch_imdb: bool = True,
        progress_callback: Optional[Callable] = None,
    ) -> list[Movie]:
        """Run a full multi-strategy TMDB scan, deduplicate, enrich, and optionally fetch RT + IMDB scores.

        Args:
            min_rating: Minimum TMDB vote average
            language: Language code (None = all)
            year_start: Start year (YYYY)
            year_end: End year (YYYY)
            max_pages: Max pages per sort strategy
            genre_ids: List of TMDB genre IDs
            sort_methods: Override sort strategies
            enrich: Whether to fetch extended details (runtime, IMDB ID)
            fetch_rt: Whether to scrape Rotten Tomatoes scores
            fetch_imdb: Whether to scrape IMDB ratings
            progress_callback: Optional callback for progress messages

        Returns:
            List of Movie objects with multi-source ratings
        """
        min_rating = min_rating if min_rating is not None else self.config.min_rating
        language = language if language is not None else self.config.language
        year_start = year_start or self.config.year_start
        year_end = year_end or self.config.year_end
        max_pages = max_pages or self.config.max_pages
        sort_methods = sort_methods or self.config.sort_methods

        today = datetime.now().strftime("%Y-%m-%d")
        if year_end is None:
            year_end = today

        seen_ids = set()
        raw_movies = []

        for sort_method in sort_methods:
            if progress_callback:
                progress_callback(f"Sort: {sort_method}")

            page = 1
            while page <= max_pages:
                try:
                    data = self.client.discover_movies_raw(
                        page=page,
                        sort_by=sort_method,
                        language=language,
                        min_rating=min_rating,
                        year_start=year_start,
                        year_end=year_end,
                        genre_ids=genre_ids,
                    )
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"  Stopped at page {page}: {e}")
                    break

                movies = data.get("results", [])
                if not movies:
                    break

                new_count = 0
                for m in movies:
                    mid = m.get("id")
                    if mid not in seen_ids:
                        seen_ids.add(mid)
                        raw_movies.append(m)
                        new_count += 1

                if progress_callback:
                    progress_callback(
                        f"  Page {page}: +{new_count} new ({len(raw_movies)} total)"
                    )

                total_pages = data.get("total_pages", 1)
                if page >= total_pages:
                    break
                page += 1
                time.sleep(0.25)

        movies = [self.client.raw_to_movie(m) for m in raw_movies]
        if not movies:
            return movies

        if enrich:
            if progress_callback:
                progress_callback("Enriching movie details...")
            for i, movie in enumerate(movies):
                self.client.enrich_movie(movie)
                if progress_callback and (i + 1) % 10 == 0:
                    progress_callback(f"  Enriched {i + 1}/{len(movies)}")

        if fetch_rt:
            if progress_callback:
                progress_callback("Fetching Rotten Tomatoes scores...")
            for i, movie in enumerate(movies):
                rt = fetch_rt_scores(movie.title, movie.year, movie.imdb_id, self.config.rt_user_agent)
                movie.rt = rt
                if progress_callback and (i + 1) % 5 == 0:
                    status = f"  RT: {i + 1}/{len(movies)}"
                    if rt.tomatometer is not None:
                        status += f" (T:{rt.tomatometer}% P:{rt.popcornmeter}%)"
                    progress_callback(status)

        if fetch_imdb:
            if progress_callback:
                progress_callback("Fetching IMDB ratings...")
            for i, movie in enumerate(movies):
                if movie.imdb_id:
                    imdb = fetch_imdb_rating(movie.imdb_id)
                    movie.imdb = imdb
                if progress_callback and (i + 1) % 5 == 0:
                    status = f"  IMDB: {i + 1}/{len(movies)}"
                    if movie.imdb.rating:
                        status += f" ({movie.imdb.rating}/10)"
                    progress_callback(status)

        return movies

    def search(self, query: str, limit: int = 10) -> list[Movie]:
        """Search movies by title."""
        data = self.client.search_raw(query)
        results = data.get("results", [])[:limit]
        movies = [self.client.raw_to_movie(m) for m in results]
        for movie in movies:
            self.client.enrich_movie(movie)
        return movies

    def get_movie(self, tmdb_id: int, fetch_rt: bool = True, fetch_imdb: bool = True) -> Optional[Movie]:
        """Get a single movie by TMDB ID with full enrichment."""
        try:
            details = self.client.get_movie_details_raw(tmdb_id)
            movie = self.client.raw_to_movie(details)
            self.client.enrich_movie(movie)
            if fetch_rt and movie.imdb_id:
                rt = fetch_rt_scores(movie.title, movie.year, movie.imdb_id, self.config.rt_user_agent)
                movie.rt = rt
            if fetch_imdb and movie.imdb_id:
                imdb = fetch_imdb_rating(movie.imdb_id)
                movie.imdb = imdb
            return movie
        except Exception:
            return None
