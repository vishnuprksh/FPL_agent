#!/usr/bin/env python3
"""
Script to load historic gameweek data from GitHub into the database.
Downloads CSV files for all available gameweeks in the 2025-26 season.
"""

import sys
import pandas as pd
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fpl_agent.database import FPLDatabase


def fetch_gameweek_csv(season: str, gw: int) -> pd.DataFrame:
    """Fetch gameweek CSV data from GitHub repository.
    
    Args:
        season: Season identifier (e.g., '2025-26')
        gw: Gameweek number
        
    Returns:
        DataFrame with gameweek data, or None if not found
    """
    base_url = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master"
    url = f"{base_url}/data/{season}/gws/gw{gw}.csv"
    
    try:
        print(f"Fetching GW{gw} data from {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse CSV
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        print(f"  ✓ Found {len(df)} player records for GW{gw}")
        return df
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"  ✗ GW{gw} not found (probably hasn't been played yet)")
            return None
        else:
            raise
    except Exception as e:
        print(f"  ✗ Error fetching GW{gw}: {e}")
        return None


def main():
    """Main function to load historic gameweek data."""
    # Configuration
    DB_PATH = "data/fpl.db"
    SEASON = "2025-26"
    MAX_GAMEWEEKS = 38  # Premier League has 38 gameweeks
    
    print(f"Loading historic gameweek data for season {SEASON}")
    print("=" * 60)
    
    # Initialize database
    db = FPLDatabase(DB_PATH)
    
    # Create table
    print("\nCreating player_gameweek_history table...")
    db.create_player_gameweek_history_table()
    print("  ✓ Table created/verified")
    
    # Fetch and load data for each gameweek
    total_records = 0
    successful_gameweeks = []
    
    print(f"\nFetching gameweek data (max {MAX_GAMEWEEKS} gameweeks)...")
    
    for gw in range(1, MAX_GAMEWEEKS + 1):
        df = fetch_gameweek_csv(SEASON, gw)
        
        if df is not None:
            try:
                # Insert into database
                count = db.insert_gameweek_data(SEASON, gw, df)
                total_records += len(df)
                successful_gameweeks.append(gw)
                print(f"  ✓ Inserted {len(df)} records for GW{gw}")
                
            except Exception as e:
                print(f"  ✗ Error inserting GW{gw} data: {e}")
        else:
            # Stop if we encounter a gameweek that doesn't exist
            # (assuming gameweeks are sequential and no gaps)
            print(f"\nStopping at GW{gw} - no more data available")
            break
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Season: {SEASON}")
    print(f"  Gameweeks loaded: {len(successful_gameweeks)}")
    if successful_gameweeks:
        print(f"  GW range: {min(successful_gameweeks)} - {max(successful_gameweeks)}")
    print(f"  Total records: {total_records}")
    print(f"  Database: {DB_PATH}")
    print("=" * 60)
    
    # Verify data
    if successful_gameweeks:
        print("\nVerifying data in database...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count total records
            cursor.execute("""
                SELECT COUNT(*) FROM player_gameweek_history 
                WHERE season = ?
            """, (SEASON,))
            db_count = cursor.fetchone()[0]
            
            # Count distinct gameweeks
            cursor.execute("""
                SELECT COUNT(DISTINCT gw) FROM player_gameweek_history 
                WHERE season = ?
            """, (SEASON,))
            gw_count = cursor.fetchone()[0]
            
            # Get some sample data
            cursor.execute("""
                SELECT season, gw, element, name, position, team, total_points, minutes
                FROM player_gameweek_history 
                WHERE season = ?
                ORDER BY total_points DESC
                LIMIT 5
            """, (SEASON,))
            
            top_performers = cursor.fetchall()
            
            print(f"  ✓ Total records in DB: {db_count}")
            print(f"  ✓ Distinct gameweeks: {gw_count}")
            print("\n  Top 5 performances by points:")
            for row in top_performers:
                season, gw, element, name, pos, team, pts, mins = row
                print(f"    GW{gw}: {name} ({pos}, {team}) - {pts} pts ({mins} mins)")
    
    print("\n✓ Historic gameweek data loaded successfully!")


if __name__ == "__main__":
    main()
