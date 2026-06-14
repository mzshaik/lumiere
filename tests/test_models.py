"""Tests for Lumiere data models."""

from lumiere.core.models import Movie, RottenTomatoesScore


class TestRottenTomatoesScore:
    def test_tomatometer_labels(self):
        assert RottenTomatoesScore(tomatometer=95, tomatometer_count=100).tomatometer_label == "Certified Fresh"
        assert RottenTomatoesScore(tomatometer=85, tomatometer_count=50).tomatometer_label == "Fresh"
        assert RottenTomatoesScore(tomatometer=60).tomatometer_label == "Fresh"
        assert RottenTomatoesScore(tomatometer=59).tomatometer_label == "Rotten"
        assert RottenTomatoesScore().tomatometer_label == "N/A"

    def test_popcornmeter_labels(self):
        assert RottenTomatoesScore(popcornmeter=95).popcornmeter_label == "Verified Hot"
        assert RottenTomatoesScore(popcornmeter=75).popcornmeter_label == "Fresh"
        assert RottenTomatoesScore(popcornmeter=59).popcornmeter_label == "Rotten"
        assert RottenTomatoesScore().popcornmeter_label == "N/A"


class TestMovie:
    def test_properties(self):
        m = Movie(tmdb_id=550, title="Fight Club", release_date="1999-10-15",
                  vote_average=8.4, vote_count=27000,
                  imdb_id="tt0137523")
        assert m.year == "1999"
        assert m.tmdb_url == "https://www.themoviedb.org/movie/550"
        assert m.imdb_url == "https://www.imdb.com/title/tt0137523/"
        assert m.combined_score == 8.4  # No RT data

    def test_combined_score_with_rt(self):
        m = Movie(tmdb_id=1, title="Test", vote_average=8.0,
                  rt=RottenTomatoesScore(tomatometer=90, popcornmeter=85))
        # (8.0 + 9.0 + 8.5) / 3 = 8.5
        assert m.combined_score == 8.5

    def test_no_poster_url(self):
        m = Movie(tmdb_id=1, title="Test")
        assert m.poster_url is None

    def test_poster_url(self):
        m = Movie(tmdb_id=1, title="Test", poster_path="/abc.jpg")
        assert m.poster_url == "https://image.tmdb.org/t/p/w500/abc.jpg"
