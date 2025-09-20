import pandas as pd
import sqlite3
import requests
import os
import argparse

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'fpl_data.db')

def load_historic_data(season='2025-26', if_exists='replace'):
    if season == '2025-26':
        # Use FPL API for current season
        bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        try:
            response = requests.get(bootstrap_url).json()
            players_df = pd.DataFrame(response['elements'])
            id_to_code = dict(zip(players_df['id'], players_df['code']))
            print(f"Loaded player mapping for {season}: {len(id_to_code)} players")
        except Exception as e:
            print(f"Error loading bootstrap-static for {season}: {e}")
            id_to_code = {}

        all_data = []
        for gw in range(1, 39):  # GW1 to GW38
            live_url = f"https://fantasy.premierleague.com/api/event/{gw}/live/"
            try:
                response = requests.get(live_url).json()
                data = []
                for elem in response['elements']:
                    row = elem['stats'].copy()
                    row['element'] = elem['id']
                    data.append(row)
                df = pd.DataFrame(data)
                df['round'] = gw  # Ensure round is set
                df['season'] = season  # Add season column
                all_data.append(df)
                print(f"Loaded {season} GW{gw}: {len(df)} records")
            except Exception as e:
                print(f"Error loading {season} GW{gw}: {e}")
                break
    else:
        # Use GitHub CSV for previous seasons
        all_data = []
        for gw in range(1, 39):  # GW1 to GW38
            url = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/gws/gw{gw}.csv"
            try:
                df = pd.read_csv(url)
                df['round'] = gw  # Ensure round is set
                df['season'] = season  # Add season column
                all_data.append(df)
                print(f"Loaded {season} GW{gw}: {len(df)} records")
            except Exception as e:
                print(f"Error loading {season} GW{gw}: {e}")
                break

        # Load players_raw.csv to get id to code mapping
        players_url = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/players_raw.csv"
        try:
            players_df = pd.read_csv(players_url)
            id_to_code = dict(zip(players_df['id'], players_df['code']))
            print(f"Loaded player mapping for {season}: {len(id_to_code)} players")
        except Exception as e:
            print(f"Error loading players_raw.csv for {season}: {e}")
            id_to_code = {}

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"Total records for {season}: {len(combined_df)}")
        print("Columns:", combined_df.columns.tolist())

        # Add missing columns with defaults
        optional_cols = {
            'fixture': 0,
            'xP': 0.0,
            'expected_assists': 0.0,
            'expected_goal_involvements': 0.0,
            'expected_goals': 0.0,
            'expected_goals_conceded': 0.0,
            'kickoff_time': '',
            'modified': False,
            'selected': 0,
            'starts': 0,
            'team_a_score': 0,
            'team_h_score': 0,
            'transfers_balance': 0,
            'transfers_in': 0,
            'transfers_out': 0,
            'clearances_blocks_interceptions': 0,
            'defensive_contribution': 0,
            'recoveries': 0,
            'tackles': 0,
            'opponent_team': 0,
            'was_home': False,
            'value': 0
        }
        for col, default in optional_cols.items():
            if col not in combined_df.columns:
                combined_df[col] = default

        # Set data types
        dtype_map = {
            'player_id': 'int64',  # element
            'round': 'int64',
            'total_points': 'int64',
            'opponent_team': 'int64',
            'season': 'object',
            'assists': 'int64',
            'bonus': 'int64',
            'bps': 'int64',
            'clean_sheets': 'int64',
            'creativity': 'float64',
            'goals_conceded': 'int64',
            'goals_scored': 'int64',
            'ict_index': 'float64',
            'influence': 'float64',
            'minutes': 'int64',
            'own_goals': 'int64',
            'penalties_missed': 'int64',
            'penalties_saved': 'int64',
            'red_cards': 'int64',
            'saves': 'int64',
            'threat': 'float64',
            'value': 'int64',
            'was_home': 'bool',
            'yellow_cards': 'int64',
            'fixture': 'int64',
            'xP': 'float64',
            'expected_assists': 'float64',
            'expected_goal_involvements': 'float64',
            'expected_goals': 'float64',
            'expected_goals_conceded': 'float64',
            'kickoff_time': 'object',
            'modified': 'bool',
            'selected': 'int64',
            'starts': 'int64',
            'team_a_score': 'int64',
            'team_h_score': 'int64',
            'transfers_balance': 'int64',
            'transfers_in': 'int64',
            'transfers_out': 'int64',
            'clearances_blocks_interceptions': 'int64',
            'defensive_contribution': 'int64',
            'recoveries': 'int64',
            'tackles': 'int64'
        }
        combined_df.rename(columns={'element': 'player_id'}, inplace=True)
        combined_df = combined_df[list(dtype_map.keys())]
        combined_df = combined_df.astype(dtype_map)

        # Add code column using the mapping
        combined_df['code'] = combined_df['player_id'].map(id_to_code).fillna(0).astype('int64')

        # Analyze features
        print("\nData types:")
        print(combined_df.dtypes)

        print("\nSample data:")
        print(combined_df.head())

        # Recreate table and insert data
        conn = sqlite3.connect(DB_PATH)
        combined_df.to_sql('player_history', conn, if_exists=if_exists, index=False)
        conn.commit()
        conn.close()
        print(f"Inserted {len(combined_df)} records for {season}")

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
    import argparse

    parser = argparse.ArgumentParser(description='Load FPL data')
    parser.add_argument('--data_type', choices=['historic', 'fixtures', 'both'], default='both',
                       help='Type of data to load (default: both)')
    parser.add_argument('--previous_years', type=int, default=1, 
                       help='Number of previous seasons to collect (default: 1)')

    args = parser.parse_args()

    # Load current season + N previous seasons
    seasons = []
    for i in range(args.previous_years + 1):
        year = 2025 - i
        season = f"{year}-{str(year + 1)[-2:]}"
        seasons.append(season)

    for season in seasons:
        print(f"Loading data for season: {season}")
        
        if args.data_type in ['historic', 'both']:
            if_exists = 'replace' if season == seasons[0] else 'append'
            load_historic_data(season, if_exists)
        
        if args.data_type in ['fixtures', 'both']:
            load_fixture_data(season)