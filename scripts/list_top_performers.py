#!/usr/bin/env python3
"""
List Top Performers

Shows the top performing players for each position.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpl_agent import FPLDatabase, FPLFormatter

def main():
    db_path = "/workspaces/FPL_agent/data/fpl_agent.db"
    
    # Load player data
    db = FPLDatabase(db_path)
    df = db.load_player_data()
    
    # Sort by predicted points
    df = df.sort_values('predicted_points', ascending=False)
    
    # Format and display results
    formatter = FPLFormatter()
    print(formatter.format_top_performers(df, top_n=5))

if __name__ == "__main__":
    main()