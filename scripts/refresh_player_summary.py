#!/usr/bin/env python3
"""
Refresh Player Summary Table

Rebuilds the player_summary table with current data from elements and final_predictions.
This is useful after running predictions or when you want to change the number of weeks.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from fpl_agent import FPLDatabase


def main():
    parser = argparse.ArgumentParser(
        description='Refresh player_summary table with summed predictions'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/fpl_agent.db',
        help='Path to SQLite database file (default: data/fpl_agent.db)'
    )
    parser.add_argument(
        '--weeks',
        type=int,
        default=3,
        help='Number of weeks to sum predictions for (default: 3)'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    db = FPLDatabase(args.db_path)
    
    print(f"Refreshing player_summary table with {args.weeks} weeks of predictions...")
    
    # Create and populate table
    db.create_player_summary_table()
    count = db.populate_player_summary(num_weeks=args.weeks)
    
    print(f"✓ Successfully populated player_summary with {count} players")
    print(f"  - Predictions summed over next {args.weeks} gameweeks")
    
    # Show sample data
    with db.get_connection() as conn:
        import pandas as pd
        sample_df = pd.read_sql_query("""
            SELECT name, position, team_name, price, predicted_points
            FROM player_summary
            ORDER BY predicted_points DESC
            LIMIT 10
        """, conn)
        
        print(f"\nTop 10 players by predicted points ({args.weeks} weeks):")
        print(sample_df.to_string(index=False))


if __name__ == "__main__":
    main()
