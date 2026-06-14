"""Data models for Lumiere movies with multi-source ratings."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RottenTomatoesScore:
    """Rotten Tomatoes ratings for a movie."""
    tomatometer: Optional[int] = None       # Critic score (0-100)
    tomatometer_count: Optional[int] = None # Number of critic reviews
    popcornmeter: Optional[int] = None      # Audience score (0-100)
    popcornmeter_count: Optional[int] = None# Number of audience ratings
    consensus: Optional[str] = None         # Critics consensus
    url: Optional[str] = None               # RT page URL
    fetched: bool = False                   # Whether RT data was successfully fetched

    @property
    def tomatometer_label(self) -> str:
        if self.tomatometer is None:
            return "N/A"
        if self.tomatometer >= 75:
            return "Certified Fresh" if self.tomatometer_count and self.tomatometer_count >= 80 else "Fresh"
        elif self.tomatometer >= 60:
            return "Fresh"
        else:
            return "Rotten"

    @property
    def popcornmeter_label(self) -> str:
        if self.popcornmeter is None:
            return "N/A"
        return "Verified Hot" if self.popcornmeter >= 90 else "Fresh" if self.popcornmeter >= 60 else "Rotten"

    def to_dict(self) -> dict:
        return {
            "tomatometer": self.tomatometer,
            "tomatometer_count": self.tomatometer_count,
            "tomatometer_label": self.tomatometer_label,
            "popcornmeter": self.popcornmeter,
            "popcornmeter_count": self.popcornmeter_count,
            "popcornmeter_label": self.popcornmeter_label,
            "consensus": self.consensus,
            "url": self.url,
            "fetched": self.fetched,
        }


@dataclass
class IMDBScore:
    """IMDB ratings for a movie."""
    rating: Optional[float] = None      # Rating (0-10)
    vote_count: Optional[int] = None    # Number of votes
    url: Optional[str] = None           # IMDB page URL
    fetched: bool = False               # Whether IMDB data was fetched

    def to_dict(self) -> dict:
        return {
            "rating": self.rating,
            "vote_count": self.vote_count,
            "url": self.url,
            "fetched": self.fetched,
        }


@dataclass
class Movie:
    """Unified movie record with data from TMDB + Rotten Tomatoes + IMDB."""
    tmdb_id: int
    title: str
    original_title: str = ""
    overview: str = ""
    release_date: str = ""
    original_language: str = ""
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    genre_ids: list = field(default_factory=list)
    genre_names: list = field(default_factory=list)
    imdb_id: Optional[str] = None
    runtime: Optional[int] = None
    tagline: Optional[str] = None
    rt: RottenTomatoesScore = field(default_factory=RottenTomatoesScore)
    imdb: IMDBScore = field(default_factory=IMDBScore)

    @property
    def year(self) -> str:
        return self.release_date[:4] if self.release_date else ""

    @property
    def tmdb_url(self) -> str:
        return f"https://www.themoviedb.org/movie/{self.tmdb_id}"

    @property
    def imdb_url(self) -> Optional[str]:
        return f"https://www.imdb.com/title/{self.imdb_id}/" if self.imdb_id else None

    @property
    def poster_url(self) -> Optional[str]:
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    @property
    def combined_score(self) -> float:
        """Weighted score combining all available ratings (normalised to 0-10)."""
        scores = []
        if self.vote_average:
            scores.append(self.vote_average * 1.0)
        if self.rt.tomatometer is not None:
            scores.append(self.rt.tomatometer / 10)
        if self.rt.popcornmeter is not None:
            scores.append(self.rt.popcornmeter / 10)
        if self.imdb.rating is not None:
            scores.append(self.imdb.rating)
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 1)

    def to_dict(self) -> dict:
        return {
            "tmdb_id": self.tmdb_id,
            "title": self.title,
            "original_title": self.original_title,
            "overview": self.overview,
            "release_date": self.release_date,
            "year": self.year,
            "original_language": self.original_language,
            "vote_average": self.vote_average,
            "vote_count": self.vote_count,
            "popularity": self.popularity,
            "poster_url": self.poster_url,
            "genre_ids": self.genre_ids,
            "genre_names": self.genre_names,
            "imdb_id": self.imdb_id,
            "runtime": self.runtime,
            "tagline": self.tagline,
            "tmdb_url": self.tmdb_url,
            "imdb_url": self.imdb_url,
            "combined_score": self.combined_score,
            "vote_average": self.vote_average,
            "rt": self.rt.to_dict(),
            "imdb": self.imdb.to_dict(),
        }
