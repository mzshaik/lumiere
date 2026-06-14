"""TMDB API client via Balloonerism proxy."""

import requests
from typing import Optional, Generator
from datetime import datetime
from ..core.models import Movie


GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
    53: "Thriller", 10752: "War", 37: "Western",
}

GENRE_BY_NAME = {v.lower(): k for k, v in GENRE_MAP.items()}


def genre_id_from_name(name: str) -> Optional[int]:
    return GENRE_BY_NAME.get(name.lower().strip())


class TMDBClient:
    """Client for the Balloonerism TMDB proxy API."""

    def __init__(self, base_url: str = "https://api.balloonerismm.workers.dev"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Lumiere/2.0"})

    def discover_movies_raw(
        self,
        page: int = 1,
        sort_by: str = "popularity.desc",
        language: Optional[str] = None,
        min_rating: Optional[float] = None,
        year_start: Optional[str] = None,
        year_end: Optional[str] = None,
        genre_ids: Optional[list[int]] = None,
    ) -> dict:
        url = f"{self.base_url}/discover/movie"
        params = {"page": page, "sort_by": sort_by}
        if language:
            params["with_original_language"] = language
        if min_rating is not None:
            params["vote_average.gte"] = min_rating
        if year_start:
            params["primary_release_date.gte"] = year_start
        if year_end:
            params["primary_release_date.lte"] = year_end
        if genre_ids:
            params["with_genres"] = ",".join(str(g) for g in genre_ids)

        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_movie_details_raw(self, movie_id: int) -> dict:
        url = f"{self.base_url}/movie/{movie_id}"
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_external_ids(self, movie_id: int) -> dict:
        """Get external IDs (IMDB, etc.) for a movie."""
        try:
            url = f"{self.base_url}/movie/{movie_id}/external_ids"
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {}

    def search_raw(self, query: str, page: int = 1) -> dict:
        url = f"{self.base_url}/search/movie"
        params = {"query": query, "page": page}
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def raw_to_movie(self, raw: dict) -> Movie:
        """Convert raw TMDB API dict to Movie model."""
        return Movie(
            tmdb_id=raw.get("id", 0),
            title=raw.get("title", "Unknown"),
            original_title=raw.get("original_title", ""),
            overview=raw.get("overview", ""),
            release_date=raw.get("release_date", ""),
            original_language=raw.get("original_language", ""),
            vote_average=float(raw.get("vote_average", 0) or 0),
            vote_count=int(raw.get("vote_count", 0) or 0),
            popularity=float(raw.get("popularity", 0) or 0),
            poster_path=raw.get("poster_path"),
            backdrop_path=raw.get("backdrop_path"),
            genre_ids=raw.get("genre_ids", []),
            genre_names=[GENRE_MAP.get(g, "") for g in (raw.get("genre_ids") or [])],
        )

    def enrich_movie(self, movie: Movie) -> Movie:
        """Fetch and attach extra details (IMDB ID, runtime, tagline) to a movie."""
        try:
            details = self.get_movie_details_raw(movie.tmdb_id)
            movie.runtime = details.get("runtime")
            movie.tagline = details.get("tagline")
            # Get genre names from details (more complete)
            genres = details.get("genres", [])
            if genres:
                movie.genre_names = [g["name"] for g in genres]
                movie.genre_ids = [g["id"] for g in genres]
            # Get external IDs
            ext = self.get_external_ids(movie.tmdb_id)
            movie.imdb_id = ext.get("imdb_id")
        except Exception:
            pass
        return movie
