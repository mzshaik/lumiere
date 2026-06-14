"""Tests for filter engine."""

from lumiere.sources.tmdb import genre_id_from_name, GENRE_BY_NAME


class TestGenreMapping:
    def test_genre_id_from_name(self):
        assert genre_id_from_name("action") == 28
        assert genre_id_from_name("Comedy") == 35
        assert genre_id_from_name("SCI-FI") == 878
        assert genre_id_from_name("unknown") is None

    def test_all_genres_mapped(self):
        assert len(GENRE_BY_NAME) >= 18  # At least 18 genres
        for name, gid in GENRE_BY_NAME.items():
            assert isinstance(gid, int)
            assert isinstance(name, str)
