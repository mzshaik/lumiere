#!/usr/bin/env python3
"""Lumiere CLI — Discover, compare, and analyze movies with multi-source ratings."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

from lumiere import __version__
from lumiere.core.config import LumiereConfig
from lumiere.core.scanner import MovieScanner
from lumiere.sources.tmdb import genre_id_from_name, GENRE_BY_NAME
from lumiere.reports.markdown import generate_markdown
from lumiere.reports.html import generate_html

console = Console()
GENRE_NAMES = sorted(GENRE_BY_NAME.keys())


def _fmt_rt(val, label="%", colorize=True):
    if val is None:
        return "[dim]N/A[/dim]"
    if colorize:
        if val >= 75:
            return f"[green]{val}{label}[/green]"
        elif val >= 60:
            return f"[yellow]{val}{label}[/yellow]"
        else:
            return f"[red]{val}{label}[/red]"
    return f"{val}{label}"


def _fmt_tmdb(val, colorize=True):
    if colorize:
        if val >= 8:
            return f"[green]{val:.1f}[/green]"
        elif val >= 7:
            return f"[yellow]{val:.1f}[/yellow]"
        else:
            return f"[red]{val:.1f}[/red]"
    return f"{val:.1f}"


def _fmt_imdb(val, colorize=True):
    if val is None:
        return "[dim]N/A[/dim]"
    if colorize:
        if val >= 8:
            return f"[green]{val:.1f}[/green]"
        elif val >= 7:
            return f"[yellow]{val:.1f}[/yellow]"
        else:
            return f"[red]{val:.1f}[/red]"
    return f"{val:.1f}"


@click.group()
@click.version_option(version=__version__, prog_name="Lumiere")
def cli():
    """Lumiere — Cinema Intelligence Platform.

    Discover movies from TMDB, compare critic vs audience scores from Rotten Tomatoes,
    check IMDB ratings, and generate beautiful reports.
    """


@cli.command()
@click.option("--min-rating", default=None, type=float, help="Minimum TMDB rating (default: 6.5)")
@click.option("--language", default=None, help="Language code: 'hi', 'en', 'ja', etc. Omit for ALL languages.")
@click.option("--year", default=None, help="Filter by release year (e.g., '2026')")
@click.option("--year-start", default=None, help="Start year")
@click.option("--year-end", default=None, help="End year")
@click.option("--genre", default=None, help="Genre filter: action, comedy, drama, thriller, etc.")
@click.option("--limit", default=None, type=int, help="Max movies to show")
@click.option("--no-rt", is_flag=True, help="Skip Rotten Tomatoes fetching (faster)")
@click.option("--no-imdb", is_flag=True, help="Skip IMDB rating fetching (faster)")
@click.option("--export", default=None, type=click.Choice(["md", "html", "csv", "json"]), help="Export format")
@click.option("--output", default=None, help="Output file path")
@click.option("--report", is_flag=True, help="Generate a Markdown report")
@click.option("--dashboard", is_flag=True, help="Generate an HTML dashboard with charts")
@click.option("--max-pages", default=None, type=int, help="Max pages per sort strategy")
@click.option("--sort", default=None, help="Comma-separated sort strategies: popularity.desc,vote_average.desc")
def discover(min_rating, language, year, year_start, year_end, genre, limit,
             no_rt, no_imdb, export, output, report, dashboard, max_pages, sort):
    """Discover movies with multi-source ratings (TMDB + RT + IMDB)."""
    cfg = LumiereConfig.from_env()

    if year:
        year_start = year_start or year
        year_end = year_end or year

    genre_ids = None
    if genre:
        gid = genre_id_from_name(genre)
        if not gid:
            console.print(f"[red]Unknown genre: '{genre}'[/red]")
            console.print(f"Available: {', '.join(GENRE_NAMES)}")
            return
        genre_ids = [gid]

    sort_methods = None
    if sort:
        sort_methods = [s.strip() for s in sort.split(",")]

    scanner = MovieScanner(cfg)
    movies = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Scanning...", total=None)

        def cb(msg):
            progress.console.print(f"  {msg}")

        movies = scanner.scan(
            min_rating=min_rating,
            language=language,
            year_start=year_start,
            year_end=year_end,
            max_pages=max_pages,
            genre_ids=genre_ids,
            sort_methods=sort_methods,
            fetch_rt=not no_rt,
            fetch_imdb=not no_imdb,
            progress_callback=cb,
        )
        progress.update(task, completed=True)

    if not movies:
        console.print("[yellow]No movies found matching your criteria.[/yellow]")
        return

    if limit and limit < len(movies):
        movies = movies[:limit]

    # Summary
    summary = f"Found [bold]{len(movies)}[/bold] movies"
    with_rt = sum(1 for m in movies if m.rt.fetched)
    with_imdb = sum(1 for m in movies if m.imdb.fetched)
    if not no_rt:
        summary += f" | [bold]{with_rt}[/bold] with RT scores"
    if not no_imdb:
        summary += f" | [bold]{with_imdb}[/bold] with IMDB ratings"

    table = Table(title=summary, box=box.ROUNDED, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="cyan", no_wrap=True)
    table.add_column("Year", style="green", width=5)
    table.add_column("TMDB", justify="center", width=5)
    table.add_column("IMDB", justify="center", width=5)
    table.add_column("Tomatometer", justify="center", width=12)
    table.add_column("Popcornmeter", justify="center", width=12)
    table.add_column("Combined", justify="center", width=8)
    table.add_column("Genre", style="blue", width=14)

    for i, m in enumerate(movies[:30], 1):
        title_display = m.title[:38] + ".." if len(m.title) > 38 else m.title
        table.add_row(
            str(i),
            title_display,
            m.year,
            _fmt_tmdb(m.vote_average),
            _fmt_imdb(m.imdb.rating),
            _fmt_rt(m.rt.tomatometer),
            _fmt_rt(m.rt.popcornmeter),
            _fmt_tmdb(m.combined_score),
            ", ".join(m.genre_names[:2]) if m.genre_names else "",
        )
    console.print(table)

    if len(movies) > 30:
        console.print(f"[dim]Showing 30 of {len(movies)} movies. Use --limit to adjust.[/dim]")

    # Highlights
    if not no_rt:
        with_rt_list = [m for m in movies if m.rt.fetched]
        if with_rt_list:
            gaps = [(m, abs((m.rt.tomatometer or 0) - (m.rt.popcornmeter or 0)))
                    for m in with_rt_list if m.rt.tomatometer is not None and m.rt.popcornmeter is not None]
            if gaps:
                gaps.sort(key=lambda x: x[1], reverse=True)
                widest = gaps[0]
                console.print(Panel(
                    f"[bold]{widest[0].title}[/bold] has the widest critic/audience gap: "
                    f"Tomatometer [red]{widest[0].rt.tomatometer}%[/red] vs "
                    f"Popcornmeter [green]{widest[0].rt.popcornmeter}%[/green] "
                    f"(gap: {widest[1]} points)",
                    title="Biggest Critic vs Audience Gap",
                    border_style="yellow",
                ))

    # Exports
    base_name = output or f"lumiere_{language or 'all'}_{year or 'any'}"

    if report or (export and "md" in export):
        path = generate_markdown(movies, f"{base_name}.md")
        console.print(f"[green]Markdown report saved:[/green] {path}")

    if dashboard or (export and "html" in export):
        path = generate_html(movies, f"{base_name}.html")
        console.print(f"[green]HTML dashboard saved:[/green] {path}")

    if export and "csv" in export:
        import csv
        path = output.replace(".csv", "") + ".csv" if output else f"{base_name}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "title", "year", "tmdb_rating", "imdb_rating", "rt_tomatometer", "rt_popcornmeter",
                "combined_score", "language", "genres", "vote_count", "runtime",
                "overview", "tmdb_url", "imdb_url", "rt_url",
            ])
            w.writeheader()
            for m in movies:
                w.writerow({
                    "title": m.title, "year": m.year,
                    "tmdb_rating": m.vote_average,
                    "imdb_rating": m.imdb.rating,
                    "rt_tomatometer": m.rt.tomatometer,
                    "rt_popcornmeter": m.rt.popcornmeter,
                    "combined_score": m.combined_score,
                    "language": m.original_language,
                    "genres": ", ".join(m.genre_names),
                    "vote_count": m.vote_count,
                    "runtime": m.runtime,
                    "overview": m.overview[:200],
                    "tmdb_url": m.tmdb_url,
                    "imdb_url": m.imdb_url or "",
                    "rt_url": m.rt.url or "",
                })
        console.print(f"[green]CSV saved:[/green] {path}")

    if export and "json" in export:
        import json
        path = output.replace(".json", "") + ".json" if output else f"{base_name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in movies], f, indent=2, ensure_ascii=False)
        console.print(f"[green]JSON saved:[/green] {path}")


@cli.command()
@click.argument("query")
@click.option("--limit", default=10, help="Max results")
@click.option("--no-rt", is_flag=True, help="Skip RT scores")
@click.option("--no-imdb", is_flag=True, help="Skip IMDB ratings")
def search(query, limit, no_rt, no_imdb):
    """Search movies by title."""
    scanner = MovieScanner()
    with console.status(f"Searching for '{query}'..."):
        movies = scanner.search(query, limit)

    if not movies:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        return

    table = Table(title=f"Search: '{query}'", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", style="cyan")
    table.add_column("Year", width=5)
    table.add_column("TMDB", justify="center", width=5)
    table.add_column("IMDB", justify="center", width=5)
    table.add_column("Language", width=4)

    for m in movies:
        table.add_row(
            str(m.tmdb_id),
            m.title[:50],
            m.year,
            _fmt_tmdb(m.vote_average),
            _fmt_imdb(m.imdb.rating),
            m.original_language.upper(),
        )
    console.print(table)


@cli.command()
@click.argument("movie_id", type=int)
@click.option("--no-rt", is_flag=True, help="Skip RT scores")
@click.option("--no-imdb", is_flag=True, help="Skip IMDB ratings")
def info(movie_id, no_rt, no_imdb):
    """Get detailed info for a movie by TMDB ID."""
    scanner = MovieScanner()
    with console.status(f"Fetching movie {movie_id}..."):
        movie = scanner.get_movie(movie_id, fetch_rt=not no_rt, fetch_imdb=not no_imdb)

    if not movie:
        console.print(f"[red]Movie with ID {movie_id} not found.[/red]")
        return

    console.print("")
    console.print(f"[bold cyan]{movie.title}[/bold cyan]")
    if movie.tagline:
        console.print(f"[italic]{movie.tagline}[/italic]")
    console.print("")

    # Scores panel
    t = f"TMDB: {_fmt_tmdb(movie.vote_average)}"
    if movie.imdb.rating is not None:
        t += f"  |  IMDB: {_fmt_imdb(movie.imdb.rating)}"
    if movie.rt.tomatometer is not None:
        t += f"  |  Tomatometer: {_fmt_rt(movie.rt.tomatometer)}"
    if movie.rt.popcornmeter is not None:
        t += f"  |  Popcornmeter: {_fmt_rt(movie.rt.popcornmeter)}"
    t += f"  |  Combined: {_fmt_tmdb(movie.combined_score)}"
    console.print(Panel(t, border_style="magenta"))

    console.print(f"Release: {movie.release_date or '?'}  |  Lang: {movie.original_language.upper()}  |  Runtime: {movie.runtime or '?'} min")
    console.print(f"Genres: {', '.join(movie.genre_names) if movie.genre_names else '?'}  |  Votes: TMDB={movie.vote_count}" +
                  (f" IMDB={movie.imdb.vote_count}" if movie.imdb.vote_count else ""))
    if movie.rt.fetched and movie.rt.consensus:
        console.print(f"Critics Consensus: [italic]{movie.rt.consensus}[/italic]")
    console.print("")
    console.print(f"[bold]Overview:[/bold]")
    console.print(movie.overview)
    console.print("")
    if movie.tmdb_url:
        console.print(f"TMDB: {movie.tmdb_url}")
    if movie.imdb_url:
        console.print(f"IMDB: {movie.imdb_url}")
    if movie.rt.url:
        console.print(f"Rotten Tomatoes: {movie.rt.url}")
    console.print("")


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind")
@click.option("--port", default=5000, type=int, help="Port")
@click.option("--debug", is_flag=True, help="Debug mode")
def serve(host, port, debug):
    """Launch the Lumiere web dashboard."""
    from lumiere.web.app import create_app
    app = create_app()
    console.print(f"[green]Lumiere Web UI starting at http://{host}:{port}[/green]")
    app.run(host=host, port=port, debug=debug)


@cli.command()
@click.argument("output", default="lumiere_demo.html")
def demo(output):
    """Generate a demo HTML dashboard with sample data."""
    from lumiere.core.models import Movie, RottenTomatoesScore, IMDBScore

    sample_movies = [
        Movie(tmdb_id=278, title="The Shawshank Redemption", release_date="1994-09-23",
              original_language="en", vote_average=8.7, vote_count=25000, popularity=100,
              genre_names=["Drama"], overview="Two convicts form a friendship over several years.",
              imdb_id="tt0111161", runtime=142,
              rt=RottenTomatoesScore(tomatometer=91, popcornmeter=98, fetched=True),
              imdb=IMDBScore(rating=9.3, vote_count=2800000, fetched=True)),
        Movie(tmdb_id=238, title="The Godfather", release_date="1972-03-14",
              original_language="en", vote_average=8.7, vote_count=19000, popularity=85,
              genre_names=["Drama", "Crime"], overview="The aging patriarch of an organized crime dynasty.",
              imdb_id="tt0068646", runtime=175,
              rt=RottenTomatoesScore(tomatometer=97, popcornmeter=98, fetched=True),
              imdb=IMDBScore(rating=9.2, vote_count=1900000, fetched=True)),
        Movie(tmdb_id=496243, title="Parasite", release_date="2019-05-30",
              original_language="ko", vote_average=8.5, vote_count=17000, popularity=80,
              genre_names=["Comedy", "Thriller", "Drama"],
              overview="Greed and class discrimination threaten the symbiotic relationship.",
              imdb_id="tt6751668", runtime=132,
              rt=RottenTomatoesScore(tomatometer=98, popcornmeter=90, fetched=True),
              imdb=IMDBScore(rating=8.5, vote_count=900000, fetched=True)),
        Movie(tmdb_id=155, title="The Dark Knight", release_date="2008-07-16",
              original_language="en", vote_average=8.5, vote_count=31000, popularity=120,
              genre_names=["Drama", "Action", "Crime", "Thriller"],
              overview="When the menace known as the Joker wreaks havoc on Gotham.",
              imdb_id="tt0468569", runtime=152,
              rt=RottenTomatoesScore(tomatometer=94, popcornmeter=94, fetched=True),
              imdb=IMDBScore(rating=9.0, vote_count=2800000, fetched=True)),
        Movie(tmdb_id=680, title="Pulp Fiction", release_date="1994-09-10",
              original_language="en", vote_average=8.5, vote_count=26000, popularity=90,
              genre_names=["Thriller", "Crime"],
              overview="The lives of two mob hitmen, a boxer, a gangster and his wife.",
              imdb_id="tt0110912", runtime=154,
              rt=RottenTomatoesScore(tomatometer=92, popcornmeter=96, fetched=True),
              imdb=IMDBScore(rating=8.9, vote_count=2200000, fetched=True)),
    ]

    path = generate_html(sample_movies, output, "Lumiere Demo Dashboard")
    console.print(f"[green]Demo dashboard generated:[/green] {path}")
    console.print(f"Open in your browser to see the full interactive dashboard.")


if __name__ == "__main__":
    cli()
