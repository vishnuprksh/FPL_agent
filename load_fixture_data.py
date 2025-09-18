import pandas as pd
import sqlite3

DB_PATH = 'fpl_data.db'

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

        print(f"Processed {len(fixture_difficulty)} fixtures for {season}")

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