import pandas as pd
import sqlite3
import os
import argparse
import requests

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'fpl_data.db')

def load_fixture_data(season='2025-26'):
    """Load fixture data and store in database"""
    
    if season == '2025-26':
        # Use FPL API for current season
        fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"
        try:
            response = requests.get(fixtures_url).json()
            df = pd.DataFrame(response)
            print(f"Loaded {season} fixtures from API: {len(df)} records")
        except Exception as e:
            print(f"Error loading fixtures from API for {season}: {e}")
            return
    else:
        # Use GitHub CSV for previous seasons
        url = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/fixtures.csv"
        try:
            df = pd.read_csv(url)
            print(f"Loaded {season} fixtures from CSV: {len(df)} records")
        except Exception as e:
            print(f"Error loading fixtures CSV for {season}: {e}")
            return

    # Insert fixtures into database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    inserted = 0
    for _, row in df.iterrows():
        try:
            c.execute('''INSERT OR REPLACE INTO fixtures (
                            id, code, event, finished, finished_provisional, kickoff_time,
                            minutes, provisional_start_time, started, team_a, team_a_score,
                            team_h, team_h_score, team_h_difficulty, team_a_difficulty, pulse_id, season
                         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (int(row['id']), 
                       int(row['code']) if not pd.isna(row['code']) else 0,
                       int(row['event']) if not pd.isna(row['event']) else 0,
                       bool(row['finished']) if not pd.isna(row['finished']) else False,
                       bool(row['finished_provisional']) if not pd.isna(row['finished_provisional']) else False,
                       str(row['kickoff_time']) if not pd.isna(row['kickoff_time']) else '',
                       int(row['minutes']) if not pd.isna(row['minutes']) else 0,
                       str(row['provisional_start_time']) if not pd.isna(row['provisional_start_time']) else '',
                       bool(row['started']) if not pd.isna(row['started']) else False,
                       int(row['team_a']) if not pd.isna(row['team_a']) else 0,
                       int(row['team_a_score']) if not pd.isna(row['team_a_score']) else 0,
                       int(row['team_h']) if not pd.isna(row['team_h']) else 0,
                       int(row['team_h_score']) if not pd.isna(row['team_h_score']) else 0,
                       int(row['team_h_difficulty']) if not pd.isna(row['team_h_difficulty']) else 0,
                       int(row['team_a_difficulty']) if not pd.isna(row['team_a_difficulty']) else 0,
                       int(row['pulse_id']) if not pd.isna(row['pulse_id']) else 0,
                       season))
            inserted += 1
        except Exception as e:
            print(f"Error inserting fixture {row['id']}: {e}")
    
    conn.commit()
    conn.close()
    print(f"Inserted {inserted} fixtures for {season}")

def main():
    parser = argparse.ArgumentParser(description='Load FPL fixture data')
    parser.add_argument('--seasons', type=str, nargs='+', 
                       default=['2025-26', '2024-25'],
                       help='Seasons to load fixture data for (default: 2025-26 2024-25)')
    
    args = parser.parse_args()
    
    for season in args.seasons:
        print(f"Loading fixture data for season: {season}")
        load_fixture_data(season)

if __name__ == "__main__":
    main()