#!/usr/bin/env python3
"""
Simple script to show the top 3 performers in each position for this week.
Based on predicted points (ep_this) from the FPL database.
"""

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