"""Beautiful HTML dashboard report generator with Chart.js visualizations."""

import os
import json
from datetime import datetime
from ..core.models import Movie


def _score_bar_html(label: str, score, max_val: float = 100, suffix: str = "%") -> str:
    if score is None:
        return (
            '<div class="score-row">'
            + f'<span class="score-label">{label}</span>'
            + '<span class="score-na">N/A</span>'
            + '</div>'
        )
    pct = score / max_val * 100
    if score / max_val >= 0.75:
        color = "#2ecc71"
    elif score / max_val >= 0.6:
        color = "#f39c12"
    else:
        color = "#e74c3c"
    return (
        '<div class="score-row">'
        + f'<span class="score-label">{label}</span>'
        + f'<div class="score-bar-bg"><div class="score-bar-fill" style="width:{pct}%;background:{color}"></div></div>'
        + f'<span class="score-value">{score}{suffix}</span>'
        + '</div>'
    )


def _movie_card_html(movie) -> str:
    poster = movie.poster_url or ""
    rt_t = movie.rt.tomatometer
    rt_p = movie.rt.popcornmeter
    tmdb_r = movie.vote_average
    imdb_r = movie.imdb.rating
    combined = movie.combined_score
    genres = ", ".join(movie.genre_names) if movie.genre_names else ""
    overview = movie.overview[:200] + "..." if len(movie.overview) > 200 else movie.overview

    links_html = "".join(
        f'<a href="{l}" target="_blank">{t}</a>'
        for l, t in [(movie.tmdb_url, "TMDB"), (movie.imdb_url, "IMDB"), (movie.rt.url, "Rotten Tomatoes")]
        if l
    )

    card = (
        '<div class="movie-card">'
        + f'<div class="movie-poster" style="background-image:url({poster})">'
        + f'<div class="movie-combined">{combined}/10</div>'
        + '</div>'
        + '<div class="movie-info">'
        + f"<h3>{movie.title}</h3>"
        + f'<div class="movie-meta">{movie.year} {"&bull; " + genres if genres else ""} {"&bull; " + str(movie.runtime) + "min" if movie.runtime else ""}</div>'
        + '<div class="scores">'
        + _score_bar_html("TMDB", tmdb_r, 10, "/10")
        + _score_bar_html("IMDB", imdb_r, 10, "/10")
        + _score_bar_html("Tomatometer", rt_t, 100, "%")
        + _score_bar_html("Popcornmeter", rt_p, 100, "%")
        + '</div>'
        + f'<p class="overview">{overview}</p>'
        + f'<div class="movie-links">{links_html}</div>'
        + '</div>'
        + '</div>'
    )
    return card


def generate_html(
    movies: list[Movie],
    output_path: str,
    title: str = "Lumiere Movie Dashboard",
) -> str:
    """Generate a beautiful, self-contained HTML dashboard."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    with_rt = sum(1 for m in movies if m.rt.tomatometer is not None)
    with_pop = sum(1 for m in movies if m.rt.popcornmeter is not None)
    with_imdb = sum(1 for m in movies if m.imdb.rating is not None)
    avg_tmdb = sum(m.vote_average for m in movies) / len(movies) if movies else 0
    avg_imdb = sum((m.imdb.rating or 0) for m in movies if m.imdb.rating) / max(with_imdb, 1)
    avg_rt_t = sum((m.rt.tomatometer or 0) for m in movies if m.rt.tomatometer) / max(with_rt, 1)
    avg_rt_p = sum((m.rt.popcornmeter or 0) for m in movies if m.rt.popcornmeter) / max(with_pop, 1)

    movies_data = []
    genre_counts = {}
    year_counts = {}

    for m in movies:
        movies_data.append({
            "title": m.title,
            "year": m.year,
            "tmdb": m.vote_average,
            "imdb": m.imdb.rating,
            "rt_critic": m.rt.tomatometer,
            "rt_audience": m.rt.popcornmeter,
            "combined": m.combined_score,
        })
        y = m.year
        if y:
            year_counts[y] = year_counts.get(y, 0) + 1
        for g in m.genre_names:
            genre_counts[g] = genre_counts.get(g, 0) + 1

    movies_json = json.dumps(movies_data)
    genre_labels = json.dumps(list(genre_counts.keys()))
    genre_values = json.dumps(list(genre_counts.values()))
    year_labels = json.dumps(sorted(year_counts.keys()))
    year_values = json.dumps([year_counts[y] for y in sorted(year_counts.keys())])

    cards_html = "\n".join(_movie_card_html(m) for m in movies)

    NL = "\n"
    Q = '"'

    html = (
        '<!DOCTYPE html>' + NL
        + '<html lang="en">' + NL
        + '<head>' + NL
        + '<meta charset="UTF-8">' + NL
        + '<meta name="viewport" content="width=device-width, initial-scale=1.0">' + NL
        + f'<title>{title}</title>' + NL
        + '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>' + NL
        + '<style>' + NL
        + '* { margin: 0; padding: 0; box-sizing: border-box; }' + NL
        + 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0d1117; color: #e6edf3; }' + NL
        + '.header { background: linear-gradient(135deg, #1a0a2e, #16213e, #0f3460); padding: 3rem 2rem; text-align: center; border-bottom: 2px solid #e94560; }' + NL
        + '.header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }' + NL
        + '.header h1 span { color: #e94560; }' + NL
        + '.header .subtitle { color: #8b949e; font-size: 1rem; }' + NL
        + '.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; padding: 2rem; max-width: 1200px; margin: 0 auto; }' + NL
        + '.stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 1.5rem; text-align: center; }' + NL
        + '.stat-card .stat-value { font-size: 2rem; font-weight: 700; color: #e94560; }' + NL
        + '.stat-card .stat-label { color: #8b949e; font-size: 0.9rem; margin-top: 0.25rem; }' + NL
        + '.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; padding: 2rem; max-width: 1200px; margin: 0 auto; }' + NL
        + '.chart-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 1.5rem; }' + NL
        + '.chart-card h3 { margin-bottom: 1rem; color: #e94560; }' + NL
        + '.movies-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1.5rem; padding: 2rem; max-width: 1400px; margin: 0 auto; }' + NL
        + '.movie-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; }' + NL
        + '.movie-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(233,69,96,0.15); }' + NL
        + '.movie-poster { height: 200px; background-size: cover; background-position: center; position: relative; background-color: #1a1a2e; }' + NL
        + '.movie-combined { position: absolute; top: 10px; right: 10px; background: rgba(233,69,96,0.9); color: white; padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; font-size: 1.1rem; }' + NL
        + '.movie-info { padding: 1.25rem; flex: 1; display: flex; flex-direction: column; }' + NL
        + '.movie-info h3 { font-size: 1.1rem; margin-bottom: 0.25rem; }' + NL
        + '.movie-meta { color: #8b949e; font-size: 0.85rem; margin-bottom: 0.75rem; }' + NL
        + '.scores { margin-bottom: 0.75rem; }' + NL
        + '.score-row { display: flex; align-items: center; margin-bottom: 0.4rem; gap: 0.5rem; }' + NL
        + '.score-label { font-size: 0.8rem; color: #8b949e; min-width: 100px; }' + NL
        + '.score-bar-bg { flex: 1; height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; }' + NL
        + '.score-bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }' + NL
        + '.score-value { font-size: 0.85rem; font-weight: 600; min-width: 45px; text-align: right; }' + NL
        + '.score-na { color: #555; font-size: 0.85rem; }' + NL
        + '.overview { color: #8b949e; font-size: 0.85rem; line-height: 1.5; flex: 1; }' + NL
        + '.movie-links { margin-top: 0.75rem; display: flex; gap: 0.75rem; }' + NL
        + '.movie-links a { color: #58a6ff; text-decoration: none; font-size: 0.85rem; }' + NL
        + '.movie-links a:hover { text-decoration: underline; }' + NL
        + '.footer { text-align: center; padding: 2rem; color: #484f58; font-size: 0.85rem; border-top: 1px solid #21262d; }' + NL
        + '</style>' + NL
        + '</head>' + NL
        + '<body>' + NL
        + '<div class="header">' + NL
        + '<h1><span>Lumiere</span></h1>' + NL
        + f'<p class="subtitle">{title} &mdash; Generated on {today}</p>' + NL
        + '</div>' + NL
        + '<div class="stats-grid">' + NL
        + f'<div class="stat-card"><div class="stat-value">{len(movies)}</div><div class="stat-label">Movies Scanned</div></div>' + NL
        + f'<div class="stat-card"><div class="stat-value">{avg_tmdb:.1f}</div><div class="stat-label">Avg TMDB Score</div></div>' + NL
        + f'<div class="stat-card"><div class="stat-value">{avg_imdb:.1f}</div><div class="stat-label">Avg IMDB Rating</div></div>' + NL
        + f'<div class="stat-card"><div class="stat-value">{avg_rt_t:.0f}%</div><div class="stat-label">Avg Tomatometer</div></div>' + NL
        + f'<div class="stat-card"><div class="stat-value">{avg_rt_p:.0f}%</div><div class="stat-label">Avg Popcornmeter</div></div>' + NL
        + f'<div class="stat-card"><div class="stat-value">{with_imdb}</div><div class="stat-label">With IMDB Data</div></div>' + NL
        + '</div>' + NL
        + '<div class="charts-grid">' + NL
        + '<div class="chart-card"><h3>All Scores Comparison (Top 15)</h3><canvas id="scoreChart" height="280"></canvas></div>' + NL
        + '<div class="chart-card"><h3>Genre Distribution</h3><canvas id="genreChart" height="250"></canvas></div>' + NL
        + '<div class="chart-card"><h3>Movies by Year</h3><canvas id="yearChart" height="250"></canvas></div>' + NL
        + '<div class="chart-card"><h3>TMDB Ratings Distribution</h3><canvas id="tmdbHistChart" height="250"></canvas></div>' + NL
        + '</div>' + NL
        + '<h2 style="padding: 1rem 2rem 0; color:#e94560;">Movies</h2>' + NL
        + '<div class="movies-grid">' + NL
        + cards_html + NL
        + '</div>' + NL
        + '<div class="footer">Built by mzshaik with \u2764\ufe0f for cinema and data.</div>' + NL
        + '<script>' + NL
        + f'const movies = {movies_json};' + NL
        + 'new Chart(document.getElementById("scoreChart"), {' + NL
        + '    type: "bar",' + NL
        + '    data: {' + NL
        + '        labels: movies.slice(0, 15).map(m => m.title.length > 20 ? m.title.slice(0,20)+"..." : m.title),' + NL
        + '        datasets: [' + NL
        + '            { label: "TMDB", data: movies.slice(0,15).map(m => m.tmdb * 10 || 0), backgroundColor: "#3498db", borderRadius: 4 },' + NL
        + '            { label: "IMDB", data: movies.slice(0,15).map(m => (m.imdb || 0) * 10 || 0), backgroundColor: "#f39c12", borderRadius: 4 },' + NL
        + '            { label: "Tomatometer", data: movies.slice(0,15).map(m => m.rt_critic || 0), backgroundColor: "#e94560", borderRadius: 4 },' + NL
        + '            { label: "Popcornmeter", data: movies.slice(0,15).map(m => m.rt_audience || 0), backgroundColor: "#2ecc71", borderRadius: 4 }' + NL
        + '        ]' + NL
        + '    },' + NL
        + '    options: { responsive: true, plugins: { legend: { labels: { color: "#8b949e" } } }, scales: { y: { beginAtZero: true, max: 100, grid: { color: "#21262d" }, ticks: { color: "#8b949e" } }, x: { grid: { display: false }, ticks: { color: "#8b949e" } } } }' + NL
        + '});' + NL
        + 'new Chart(document.getElementById("genreChart"), {' + NL
        + '    type: "doughnut",' + NL
        + '    data: {' + NL
        + f'        labels: {genre_labels},' + NL
        + f'        datasets: [{{ data: {genre_values}, backgroundColor: ["#e94560","#0f3460","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e74c3c","#3498db","#e67e22","#2c3e50","#16a085","#c0392b"] }}]' + NL
        + '    },' + NL
        + '    options: { responsive: true, plugins: { legend: { position: "right", labels: { color: "#8b949e" } } } }' + NL
        + '});' + NL
        + 'new Chart(document.getElementById("yearChart"), {' + NL
        + '    type: "bar",' + NL
        + '    data: {' + NL
        + f'        labels: {year_labels},' + NL
        + f'        datasets: [{{ label: "Movies", data: {year_values}, backgroundColor: "#0f3460", borderRadius: 4 }}]' + NL
        + '    },' + NL
        + '    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: "#21262d" }, ticks: { color: "#8b949e" } }, x: { grid: { display: false }, ticks: { color: "#8b949e" } } } }' + NL
        + '});' + NL
        + 'new Chart(document.getElementById("tmdbHistChart"), {' + NL
        + '    type: "bar",' + NL
        + '    data: {' + NL
        + '        labels: ["5-6","6-7","7-8","8-9","9-10"],' + NL
        + '        datasets: [{' + NL
        + '            label: "Movies",' + NL
        + '            data: [' + NL
        + '                movies.filter(m => m.tmdb >=5 && m.tmdb <6).length,' + NL
        + '                movies.filter(m => m.tmdb >=6 && m.tmdb <7).length,' + NL
        + '                movies.filter(m => m.tmdb >=7 && m.tmdb <8).length,' + NL
        + '                movies.filter(m => m.tmdb >=8 && m.tmdb <9).length,' + NL
        + '                movies.filter(m => m.tmdb >=9).length,' + NL
        + '            ],' + NL
        + '            backgroundColor: "#e94560", borderRadius: 4' + NL
        + '        }]' + NL
        + '    },' + NL
        + '    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: "#21262d" }, ticks: { color: "#8b949e" } }, x: { grid: { display: false }, ticks: { color: "#8b949e" } } } }' + NL
        + '});' + NL
        + '</script>' + NL
        + '</body>' + NL
        + '</html>' + NL
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
