#!/usr/bin/env python3
"""
FPL Agent - Initialize database with complete data pipeline.

This script orchestrates the complete FPL data pipeline:
1. Fetch and load current FPL API data (players, teams, fixtures)
2. Load historic gameweek data from GitHub
3. Calculate team attack/defense valuations
4. Build player match context
5. Train ML models for points prediction
6. Generate final predictions for all remaining fixtures
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from pathlib import Path
from fpl_agent import FPLDataPipeline


def main():
    """Run the complete FPL data initialization pipeline."""
    parser = argparse.ArgumentParser(
        description='Initialize FPL database with complete data pipeline'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/fpl_agent.db',
        help='Path to SQLite database file (default: data/fpl_agent.db)'
    )
    parser.add_argument(
        '--season',
        type=str,
        default='2025-26',
        help='Season to load historic data for (default: 2025-26)'
    )
    parser.add_argument(
        '--max-gameweeks',
        type=int,
        default=38,
        help='Maximum number of gameweeks to check (default: 38)'
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    pipeline = FPLDataPipeline(db_path=args.db_path)
    results = pipeline.run(season=args.season, max_gameweeks=args.max_gameweeks)
    
    return results


if __name__ == "__main__":
    main()
