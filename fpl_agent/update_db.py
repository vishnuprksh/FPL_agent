import pandas as pd
import sqlite3
import requests
import os
import argparse
from fpl_agent.database_connection import get_connection
from fpl_agent.models import init_db

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'fpl_data.db')

def load_historic_data(season='2025-26', if_exists='replace'):
    # Unified approach: prefer GitHub CSVs for all seasons (simpler and consistent).
    all_data = []
    players_df = None

    # Load GW files
    for gw in range(1, 39):  # GW1 to GW38
        csv_url = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/gws/gw{gw}.csv"
        try:
            df = pd.read_csv(csv_url)
            df['round'] = gw
            df['season'] = season
            # element in the GW CSV is the player id for that season
            df.rename(columns={'element': 'season_id'}, inplace=True)
            all_data.append(df)
            print(f"Loaded {season} GW{gw} from CSV: {len(df)} records")
        except Exception as csv_err:
            print(f"Warning: Could not load GW{gw} for {season}: {csv_err}")

    # Load players only for the current season (2025-26)
    if season == '2025-26':
        players_url = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/players_raw.csv"
        try:
            players_df = pd.read_csv(players_url)
            players_df.rename(columns={'id': 'season_id', 'code': 'player_code'}, inplace=True)
            players_df['season'] = season
            print(f"Loaded players_raw.csv for {season} from CSV: {len(players_df)} players")
        except Exception as pcsv_err:
            raise Exception(f"Error loading players_raw.csv for {season}: {pcsv_err}")
    else:
        print(f"Skipping players_raw.csv for {season} - only collecting for current season (2025-26)")

    # Concatenate all GW data
    if len(all_data) > 0:
        all_df = pd.concat(all_data, ignore_index=True)
    else:
        all_df = pd.DataFrame()

    # Map season_id -> player_code using players_df (only available for current season)
    if not all_df.empty and players_df is not None and not players_df.empty:
        # players_df has season_id and player_code
        # Ensure both are same dtype
        all_df['season_id'] = all_df['season_id'].astype(players_df['season_id'].dtype)
        players_map = players_df[['season_id', 'player_code']].drop_duplicates()
        all_df = all_df.merge(players_map, on='season_id', how='left')
        print(f"Mapped player_code into GW data; missing player_code count: {all_df['player_code'].isna().sum()}")
    elif not all_df.empty and players_df is None:
        print(f"No player_code mapping available for {season} - historical seasons don't include player_code")

    # Insert into the SQLite DB using column intersection so we only write matching columns
    conn = get_connection()
    c = conn.cursor()

    # If requested, remove existing rows for this season before inserting (safer than dropping tables)
    if if_exists == 'replace':
        try:
            c.execute('DELETE FROM players WHERE season = ?', (season,))
            c.execute('DELETE FROM player_history WHERE season = ?', (season,))
            conn.commit()
            print(f"Cleared existing players and player_history rows for season {season}")
        except Exception as e:
            conn.rollback()
            raise

    def insert_dataframe(df: pd.DataFrame, table_name: str) -> int:
        """Insert rows from df into table_name by matching columns present in the DB.

        Returns number of rows attempted to insert.
        """
        if df is None or df.empty:
            return 0

        # Get table columns
        c.execute(f"PRAGMA table_info({table_name})")
        cols_info = c.fetchall()
        table_cols = [r[1] for r in cols_info]

        # Keep columns that exist in the table
        common_cols = [col for col in df.columns if col in table_cols]
        if not common_cols:
            return 0

        cols_sql = ",".join(common_cols)
        placeholders = ",".join(["?" for _ in common_cols])
        sql = f"INSERT OR REPLACE INTO {table_name} ({cols_sql}) VALUES ({placeholders})"

        # Replace NaN with None so sqlite stores NULLs
        records = df[common_cols].where(pd.notnull(df[common_cols]), None).values.tolist()

        try:
            c.executemany(sql, records)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return len(records)

    # Only insert players data for current season
    if players_df is not None:
        players_inserted = insert_dataframe(players_df, 'players')
    else:
        players_inserted = 0
    history_inserted = insert_dataframe(all_df, 'player_history')

    conn.close()
    if players_inserted > 0:
        print(f"Inserted {players_inserted} players and {history_inserted} player_history rows for {season}")
    else:
        print(f"Inserted {history_inserted} player_history rows for {season} (no players data for historical seasons)")


def load_teams_data(season='2025-26', if_exists='replace'):
    """Load teams data for a given season from the vaastav GitHub CSV and insert into DB."""
    teams_url = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/teams.csv"
    try:
        df = pd.read_csv(teams_url)
        print(f"Loaded teams CSV for {season}: {len(df)} rows")
    except Exception as e:
        print(f"Error loading teams CSV for {season}: {e}")
        return 0

    # Normalize column names if necessary (keep as-is; insert_dataframe will pick matching cols)
    conn = get_connection()
    c = conn.cursor()

    if if_exists == 'replace':
        try:
            c.execute('DELETE FROM teams')
            conn.commit()
            print(f"Cleared existing teams rows for season {season}")
        except Exception:
            conn.rollback()
            raise

    # Reuse insert_dataframe defined in load_historic_data by importing local helper.
    # To avoid duplication, implement a small local helper that mirrors insert_dataframe behavior
    # but scoped for teams (no need to re-open connection).
    def insert_df_into_table(df_in: pd.DataFrame, table_name: str) -> int:
        if df_in is None or df_in.empty:
            return 0

        c.execute(f"PRAGMA table_info({table_name})")
        cols_info = c.fetchall()
        table_cols = [r[1] for r in cols_info]

        common_cols = [col for col in df_in.columns if col in table_cols]
        if not common_cols:
            return 0

        cols_sql = ",".join(common_cols)
        placeholders = ",".join(["?" for _ in common_cols])
        sql = f"INSERT OR REPLACE INTO {table_name} ({cols_sql}) VALUES ({placeholders})"

        records = df_in[common_cols].where(pd.notnull(df_in[common_cols]), None).values.tolist()
        try:
            c.executemany(sql, records)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return len(records)

    inserted = insert_df_into_table(df, 'teams')
    conn.close()
    if inserted == 0:
        print("No matching team columns to insert into DB")
    else:
        print(f"Inserted {inserted} teams for {season}")
    return inserted

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
    parser.add_argument('--previous_years', type=int, default=1,
                        help='Number of previous seasons to collect (default: 1)')

    args = parser.parse_args()

    init_db()

    # Load current season + N previous seasons
    seasons = []
    for i in range(args.previous_years + 1):
        year = 2025 - i
        season = f"{year}-{str(year + 1)[-2:]}"
        seasons.append(season)

    for season in seasons:
        print(f"Loading data for season: {season}")

        # Always load both historic and fixture data
        if_exists = 'replace' if season == seasons[0] else 'append'
        # Load teams first so joins against teams will work
        try:
            load_teams_data(season, if_exists)
        except Exception as e:
            print(f"Warning: failed to load teams for {season}: {e}")

        load_historic_data(season, if_exists)
        load_fixture_data(season)

if __name__ == '__main__':
    main()
