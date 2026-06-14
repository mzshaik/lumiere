"""Lumiere Web Dashboard — Flask-based movie browsing UI."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, render_template, request, jsonify, send_from_directory
from ..core.scanner import MovieScanner
from ..reports.html import generate_html
from ..sources.tmdb import GENRE_BY_NAME, genre_id_from_name
import tempfile
import json


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.urandom(24)
    scanner = MovieScanner()

    @app.route("/")
    def index():
        genres = sorted(GENRE_BY_NAME.keys())
        return render_template("index.html", genres=genres)

    @app.route("/api/search")
    def api_search():
        query = request.args.get("q", "")
        if not query:
            return jsonify([])
        movies = scanner.search(query, limit=10)
        return jsonify([m.to_dict() for m in movies])

    @app.route("/api/movie/<int:movie_id>")
    def api_movie(movie_id):
        movie = scanner.get_movie(movie_id)
        if not movie:
            return jsonify({"error": "Not found"}), 404
        return jsonify(movie.to_dict())

    @app.route("/api/scan")
    def api_scan():
        args = request.args
        try:
            movies = scanner.scan(
                min_rating=float(args.get("min_rating", 6.5)),
                language=args.get("language") or None,
                year_start=args.get("year_start") or None,
                year_end=args.get("year_end") or None,
                genre_ids=[genre_id_from_name(args["genre"])] if args.get("genre") else None,
                max_pages=int(args.get("max_pages", 50)),
                fetch_rt=args.get("no_rt", "false").lower() != "true",
                fetch_imdb=args.get("no_imdb", "false").lower() != "true",
                progress_callback=lambda msg: None,
            )
            limit = int(args.get("limit", 50))
            if limit < len(movies):
                movies = movies[:limit]
            return jsonify([m.to_dict() for m in movies])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/report")
    def api_report():
        try:
            movies_json = request.args.get("movies")
            if movies_json:
                movies_data = json.loads(movies_json)
                from ..core.models import Movie, RottenTomatoesScore, IMDBScore
                movies = []
                for md in movies_data:
                    rt = RottenTomatoesScore(**md.get("rt", {}))
                    imdb = IMDBScore(**md.get("imdb", {}))
                    movies.append(Movie(
                        tmdb_id=md["tmdb_id"],
                        title=md["title"],
                        original_title=md.get("original_title", ""),
                        overview=md.get("overview", ""),
                        release_date=md.get("release_date", ""),
                        original_language=md.get("original_language", ""),
                        vote_average=md.get("vote_average", 0),
                        vote_count=md.get("vote_count", 0),
                        popularity=md.get("popularity", 0),
                        genre_names=md.get("genre_names", []),
                        genre_ids=md.get("genre_ids", []),
                        imdb_id=md.get("imdb_id"),
                        runtime=md.get("runtime"),
                        tagline=md.get("tagline"),
                        rt=rt,
                        imdb=imdb,
                    ))
            else:
                movies = scanner.scan(
                    max_pages=50, fetch_rt=True, fetch_imdb=True,
                    progress_callback=lambda msg: None,
                )

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            path = generate_html(movies, tmp.name, "Lumiere Web Scan")
            return jsonify({"path": path})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/report/<path:filename>")
    def serve_report(filename):
        return send_from_directory(tempfile.gettempdir(), filename)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
