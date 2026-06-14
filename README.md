# Lumiere

> A unified movie discovery platform that aggregates ratings from TMDB, Rotten Tomatoes, and IMDB.

Lumiere scans TMDB for movies, fetches critic and audience scores from Rotten Tomatoes, and retrieves user ratings from IMDB — then presents everything in a clean CLI, interactive web dashboard, or exportable report.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Commands](#commands)
- [Discover Options](#discover-options)
- [Language Reference](#language-reference)
- [Genre Reference](#genre-reference)
- [Sort Strategies](#sort-strategies)
- [Score Reference](#score-reference)
- [Output Formats](#output-formats)
- [Web Dashboard](#web-dashboard)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Examples](#examples)

---

## Quick Start

```bash
git clone https://github.com/mzshaik/lumiere.git
cd lumiere
pip install -r requirements.txt

# Discover top-rated movies across all sources
python main.py discover --min-rating 7.0

# Hindi movies with full report
python main.py discover --language hi --year 2026 --dashboard

# Search and inspect specific movies
python main.py search "Inception"
python main.py info 550

# Launch the web interface
python main.py serve
```

---

## Commands

| Command | Description |
|---------|-------------|
| `discover` | Scan TMDB across multiple sort strategies, enrich with RT and IMDB ratings |
| `search` | Search for movies by title |
| `info` | Retrieve detailed information for a specific TMDB ID |
| `serve` | Start the Flask web dashboard |
| `demo` | Generate a sample HTML report with example data |

---

## Discover Options

### Rating Filters

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--min-rating` | `float` | `6.5` | Minimum TMDB vote average (0–10) |
| `--no-rt` | `flag` | off | Skip Rotten Tomatoes fetching |
| `--no-imdb` | `flag` | off | Skip IMDB rating fetching |

### Language and Year

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--language` | `string` | all languages | ISO 639-1 language code |
| `--year` | `string` | — | Single year filter |
| `--year-start` | `string` | — | Start of year range |
| `--year-end` | `string` | — | End of year range |

### Genre

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--genre` | `string` | all genres | Genre name (see genre reference) |

### Scan Control

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--limit` | `int` | unlimited | Maximum number of movies to return |
| `--max-pages` | `int` | `500` | Maximum pages per sort strategy |
| `--sort` | `string` | 4 strategies | Comma-separated sort methods |

### Output

| Flag | Type | Description |
|------|------|-------------|
| `--report` | `flag` | Generate a Markdown report |
| `--dashboard` | `flag` | Generate an HTML dashboard with Chart.js |
| `--export` | `choice` | `md`, `html`, `csv`, or `json` |
| `--output` | `string` | Custom output filename (without extension) |

---

## Language Reference

Use the `--language` flag with an ISO 639-1 code. Omit the flag to scan **all languages**.

### Widely Spoken Languages

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| `en` | English | `hi` | Hindi | `es` | Spanish |
| `fr` | French | `de` | German | `it` | Italian |
| `pt` | Portuguese | `ru` | Russian | `ja` | Japanese |
| `ko` | Korean | `zh` | Chinese | `ar` | Arabic |
| `bn` | Bengali | `pa` | Punjabi | `ta` | Tamil |
| `te` | Telugu | `mr` | Marathi | `gu` | Gujarati |
| `kn` | Kannada | `ml` | Malayalam | `ur` | Urdu |

### European Languages

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| `nl` | Dutch | `sv` | Swedish | `no` | Norwegian |
| `da` | Danish | `fi` | Finnish | `pl` | Polish |
| `cs` | Czech | `sk` | Slovak | `hu` | Hungarian |
| `ro` | Romanian | `bg` | Bulgarian | `sr` | Serbian |
| `hr` | Croatian | `el` | Greek | `tr` | Turkish |
| `uk` | Ukrainian | `vi` | Vietnamese | `th` | Thai |

### Asian and Middle Eastern Languages

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| `id` | Indonesian | `ms` | Malay | `tl` | Filipino |
| `my` | Burmese | `km` | Khmer | `lo` | Lao |
| `mn` | Mongolian | `ne` | Nepali | `si` | Sinhala |
| `fa` | Persian | `he` | Hebrew | `ku` | Kurdish |
| `ps` | Pashto | `sd` | Sindhi | `am` | Amharic |

### African Languages

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| `sw` | Swahili | `ha` | Hausa | `yo` | Yoruba |
| `ig` | Igbo | `zu` | Zulu | `af` | Afrikaans |
| `st` | Sesotho | `tn` | Tswana | `xh` | Xhosa |

### Examples by Language

```bash
# Hindi cinema
python main.py discover --language hi

# Japanese animation
python main.py discover --language ja --genre animation

# Korean films
python main.py discover --language ko --year 2025

# Tamil movies
python main.py discover --language ta

# Telugu cinema
python main.py discover --language te
```

---

## Genre Reference

| Genre | TMDB ID | Genre | TMDB ID | Genre | TMDB ID |
|-------|---------|-------|---------|-------|---------|
| `action` | 28 | `adventure` | 12 | `animation` | 16 |
| `comedy` | 35 | `crime` | 80 | `documentary` | 99 |
| `drama` | 18 | `family` | 10751 | `fantasy` | 14 |
| `history` | 36 | `horror` | 27 | `music` | 10402 |
| `mystery` | 9648 | `romance` | 10749 | `sci-fi` | 878 |
| `thriller` | 53 | `war` | 10752 | `western` | 37 |

```bash
python main.py discover --genre action
python main.py discover --genre sci-fi --year-start 2020
python main.py discover --genre horror --min-rating 7.0
python main.py discover --language ja --genre animation
```

---

## Sort Strategies

By default, Lumiere runs all four strategies and deduplicates results. Use `--sort` to override.

| Strategy | Description |
|----------|-------------|
| `popularity.desc` | Most popular first |
| `vote_average.desc` | Highest rated first |
| `release_date.desc` | Newest first |
| `vote_count.desc` | Most votes first |
| `revenue.desc` | Highest grossing first |
| `original_title.asc` | Alphabetical A–Z |

```bash
# Single strategy
python main.py discover --sort popularity.desc

# Custom order
python main.py discover --sort "vote_average.desc,popularity.desc"

# New releases
python main.py discover --sort release_date.desc --year 2026
```

---

## Score Reference

### Rating Sources

| Source | Range | Description |
|--------|-------|-------------|
| **TMDB** | 0–10 | Weighted average of all TMDB user votes |
| **IMDB** | 0–10 | Weighted average of all IMDB user votes |
| **Tomatometer** | 0–100% | Percentage of critic reviews that are positive |
| **Popcornmeter** | 0–100% | Percentage of audience ratings that are positive |
| **Combined** | 0–10 | Average of all available scores, normalised |

### Rotten Tomatoes Labels

| Tomatometer | Label | Condition |
|-------------|-------|-----------|
| 75–100% | Certified Fresh | 80+ critic reviews |
| 60–100% | Fresh | Generally positive |
| 0–59% | Rotten | Generally negative |

| Popcornmeter | Label | Condition |
|-------------|-------|-----------|
| 90–100% | Verified Hot | Audiences love it |
| 60–89% | Fresh | Audiences like it |
| 0–59% | Rotten | Audiences dislike it |

### Combined Score Formula

```
combined = (tmdb + imdb + tomatometer/10 + popcornmeter/10) / number_of_available_scores
```

All four sources are weighted equally. Missing sources are excluded from the average.

---

## Output Formats

### Markdown Report (`--report`)

A structured Markdown document with summary statistics, per-movie score breakdowns, and links to TMDB, IMDB, and Rotten Tomatoes.

### HTML Dashboard (`--dashboard`)

A self-contained HTML file featuring:
- Four Chart.js visualisations: score comparison, genre distribution, year distribution, and TMDB rating histogram
- Movie cards with individual score bars for all four rating sources
- Dark theme with responsive grid layout
- No external dependencies (Chart.js loaded from CDN)

### CSV Export (`--export csv`)

Tabular data suitable for spreadsheet analysis or data pipelines.

### JSON Export (`--export json`)

Complete structured data for programmatic consumption.

---

## Web Dashboard

```bash
python main.py serve
```

Opens at `http://127.0.0.1:5000` with:
- Interactive scanning with all filter parameters
- Movie cards displaying all four rating sources
- Critic-versus-audience comparison charts
- Live search by title
- One-click HTML report generation

---

## Architecture

```
lumiere/
├── main.py                       # CLI entry point
├── lumiere/
│   ├── cli.py                    # Click command definitions
│   ├── core/
│   │   ├── config.py             # Environment-based configuration
│   │   ├── models.py             # Movie, RottenTomatoesScore, IMDBScore
│   │   └── scanner.py            # Multi-strategy scan engine
│   ├── sources/
│   │   ├── tmdb.py               # TMDB API client (Balloonerism proxy)
│   │   ├── rottentomatoes.py     # Rotten Tomatoes scraper
│   │   └── imdb.py               # IMDB rating scraper
│   ├── reports/
│   │   ├── markdown.py           # Markdown report generator
│   │   └── html.py               # HTML dashboard generator
│   └── web/
│       ├── app.py                # Flask application
│       └── templates/
│           └── index.html        # Dashboard frontend
├── tests/
│   ├── test_models.py
│   └── test_filter.py
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Configuration

Copy `.env.example` to `.env`:

```env
# Balloonerism API base URL (TMDB proxy)
BALLOONERISM_API_URL=https://api.balloonerismm.workers.dev

# Default scan parameters
DEFAULT_MIN_RATING=6.5
DEFAULT_MAX_PAGES=500
DEFAULT_LANGUAGE=           # Leave blank for all languages
```

---

## Examples

```bash
# Top-rated movies across all sources
python main.py discover --min-rating 8.0 --limit 50

# Best Hindi films of 2026 with HTML dashboard
python main.py discover --language hi --year 2026 --dashboard

# Action movies with strong critic and audience consensus
python main.py discover --genre action --min-rating 7.0 --report

# Movies critics disliked but audiences loved
python main.py discover --year 2025 --export csv

# Japanese animated films
python main.py discover --language ja --genre animation --min-rating 7.5

# Korean cinema from the last five years
python main.py discover --language ko --year-start 2021

# Horror movies with high audience approval
python main.py discover --genre horror --min-rating 6.0 --dashboard

# Science fiction from the 2020s, exported for analysis
python main.py discover --genre sci-fi --year-start 2020 --export csv

# Current year releases, sorted by recency
python main.py discover --year 2026 --sort release_date.desc

# Fast scan — TMDB only, no enrichment
python main.py discover --sort popularity.desc --no-rt --no-imdb --limit 20

# Comprehensive scan with all output formats
python main.py discover --year 2026 --min-rating 6.5 --dashboard --report --export csv

# Weekly scan suitable for cron scheduling
python main.py discover --year 2026 --min-rating 7.0 --report --output weekly_report

# Search for a specific title
python main.py search "The Dark Knight"

# Detailed information for a known TMDB ID
python main.py info 550

# Launch the web interface
python main.py serve
```

---

## Data Sources

- **TMDB** — Movie metadata via the [Balloonerism API](https://api.balloonerismm.workers.dev) proxy
- **Rotten Tomatoes** — Critic and audience scores via web scraping
- **IMDB** — User ratings via web scraping

All scraping is rate-limited and uses standard browser headers. No API keys are required.

---

Built by [mzshaik](https://github.com/mzshaik) with ❤️ for cinema and data.