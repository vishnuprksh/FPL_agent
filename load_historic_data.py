import pandas as pd
import sqlite3
import requests

DB_PATH = 'fpl_data.db'

def load_historic_data(season='2024-25', if_exists='replace'):
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
            'tackles': 0
        }
        for col, default in optional_cols.items():
            if col not in combined_df.columns:
                combined_df[col] = default

        # Set data types
        dtype_map = {
            'element': 'int64',  # player_id
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
        combined_df = combined_df.astype(dtype_map)
        combined_df.rename(columns={'element': 'player_id'}, inplace=True)

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

if __name__ == "__main__":
    import sys
    season = sys.argv[1] if len(sys.argv) > 1 else '2025-26'
    if season == 'both':
        print("Loading data for season: 2024-25")
        load_historic_data('2024-25', 'replace')
        print("Loading data for season: 2025-26")
        load_historic_data('2025-26', 'append')
    else:
        print(f"Loading data for season: {season}")
        load_historic_data(season, 'replace')