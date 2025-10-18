#!/usr/bin/env python3
"""
Simple script to show the top 3 performers in each position for this week.
Based on predicted points (ep_this) from the FPL database.
"""

import sqlite3
import pandas as pd

def main():
    db_path = "/workspaces/FPL_agent/data/fpl_agent.db"
    
    query = """
    SELECT 
        web_name as name,
        element_type_name as position,
        team,
        ep_this as predicted_points
    FROM elements 
    WHERE can_select = 1 
    AND ep_this IS NOT NULL 
    AND now_cost > 0
    ORDER BY ep_this DESC
    """
    
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)
    
    positions = ['GK', 'DEF', 'MID', 'FWD']
    
    print("Top 3 Performers by Position (This Week)")
    print("=" * 50)
    
    for pos in positions:
        pos_df = df[df['position'] == pos].head(5)
        if not pos_df.empty:
            print(f"\n{pos}:")
            for _, player in pos_df.iterrows():
                print(f"  {player['name']} ({player['team']}) - {player['predicted_points']:.2f} pts")
        else:
            print(f"\n{pos}: No data available")

if __name__ == "__main__":
    main()