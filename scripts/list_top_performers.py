#!/usr/bin/env python3
"""
List Top Performers

Shows the top performing players for each position.
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpl_agent import FPLDatabase, FPLFormatter

def main():
    parser = argparse.ArgumentParser(description='List top performers for upcoming weeks')
    parser.add_argument('--weeks', type=int, default=3, help='Number of upcoming weeks to consider (default: 3)')
    args = parser.parse_args()
    
    db_path = "/workspaces/FPL_agent/data/fpl_agent.db"
    
    # Load player data
    db = FPLDatabase(db_path)
    df = db.load_top_performers_for_weeks(num_weeks=args.weeks)
    
    # Format and display results
    formatter = FPLFormatter()
    print(formatter.format_top_performers(df, top_n=5, weeks=args.weeks))

if __name__ == "__main__":
    main()