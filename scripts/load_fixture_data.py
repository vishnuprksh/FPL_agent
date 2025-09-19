import pandas as pd
import sqlite3

DB_PATH = '../data/fpl_data.db'

def load_fixture_data(season='2025-26'):
    """Load fixture data and update player_history with fixture difficulty"""
    url = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/fixtures.csv"

    try:
        df = pd.read_csv(url)
        print(f"Loaded {season} fixtures: {len(df)} records")
        print("Columns:", df.columns.tolist())

        # Create a dictionary mapping fixture_id to difficulty for home and away
        fixture_difficulty = {}
        for _, row in df.iterrows():
            fixture_id = int(row['id'])
            fixture_difficulty[fixture_id] = {
                'home_difficulty': int(row['team_h_difficulty']),
                'away_difficulty': int(row['team_a_difficulty'])
            }

        # Insert fixtures
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for _, row in df.iterrows():
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
        conn.commit()
        conn.close()
        print(f"Inserted {len(df)} fixtures for {season}")

        # Update player_history table
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        updated = 0
        for fixture_id, difficulties in fixture_difficulty.items():
            # Update home team players (was_home = 1)
            c.execute('''UPDATE player_history
                         SET fixture_difficulty = ?
                         WHERE fixture = ? AND was_home = 1 AND season = ?''',
                      (difficulties['home_difficulty'], fixture_id, season))

            # Update away team players (was_home = 0)
            c.execute('''UPDATE player_history
                         SET fixture_difficulty = ?
                         WHERE fixture = ? AND was_home = 0 AND season = ?''',
                      (difficulties['away_difficulty'], fixture_id, season))

            updated += c.rowcount

        conn.commit()
        conn.close()
        print(f"Updated {updated} player_history records for {season} with fixture difficulty")

        # Insert future fixtures into player_history
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get unfinished fixtures
        c.execute('SELECT id, event, team_h, team_a, team_h_difficulty, team_a_difficulty FROM fixtures WHERE finished = 0 AND season = ?', (season,))
        future_fixtures = c.fetchall()
        
        inserted = 0
        for fixture_id, event, team_h, team_a, h_diff, a_diff in future_fixtures:
            # Insert home team players
            c.execute('SELECT id FROM players WHERE team = ?', (team_h,))
            home_players = [row[0] for row in c.fetchall()]
            for player_id in home_players:
                c.execute('''INSERT OR IGNORE INTO player_history (
                                player_id, round, total_points, opponent_team, season, fixture, was_home, fixture_difficulty
                             ) VALUES (?, ?, NULL, ?, ?, ?, 1, ?)''',
                          (player_id, event, team_a, season, fixture_id, h_diff))
                inserted += c.rowcount
            
            # Insert away team players
            c.execute('SELECT id FROM players WHERE team = ?', (team_a,))
            away_players = [row[0] for row in c.fetchall()]
            for player_id in away_players:
                c.execute('''INSERT OR IGNORE INTO player_history (
                                player_id, round, total_points, opponent_team, season, fixture, was_home, fixture_difficulty
                             ) VALUES (?, ?, NULL, ?, ?, ?, 0, ?)''',
                          (player_id, event, team_h, season, fixture_id, a_diff))
                inserted += c.rowcount
        
        conn.commit()
        conn.close()
        print(f"Inserted {inserted} future player_history records for {season}")

    except Exception as e:
        print(f"Error loading {season} fixtures: {e}")

if __name__ == "__main__":
    import sys
    season = sys.argv[1] if len(sys.argv) > 1 else '2025-26'
    print(f"Loading fixture data for season: {season}")
    load_fixture_data(season)

    # Also update the other season
    other_season = '2024-25' if season == '2025-26' else '2025-26'
    print(f"Loading fixture data for season: {other_season}")
    load_fixture_data(other_season)