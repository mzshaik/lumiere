#!/usr/bin/env python3
"""Lumiere — Cinema Intelligence Platform.

Discover, compare, and analyze movies with TMDB + Rotten Tomatoes ratings.

Usage:
  python main.py discover --min-rating 7.0 --year 2026
  python main.py discover --language hi --report --dashboard
  python main.py discover --genre action --limit 50 --export csv
  python main.py search "Inception"
  python main.py info 550
  python main.py serve              # Launch web UI
  python main.py demo               # Generate demo HTML dashboard
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lumiere.cli import cli

if __name__ == "__main__":
    cli()
