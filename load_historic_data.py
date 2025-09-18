import pandas as pd
import sqlite3
import requests

DB_PATH = 'fpl_data.db'

def load_historic_data(season='2024-25'):
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

        # Analyze features
        print("\nData types:")
        print(combined_df.dtypes)

        print("\nSample data:")
        print(combined_df.head())

        # Now insert/update into database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        updated = 0
        for _, row in combined_df.iterrows():
            player_id = int(row['element'])
            round_num = int(row['round'])
            season_val = row['season']

            # Check if record already exists for this player, round, and season
            c.execute('SELECT COUNT(*) FROM player_history WHERE player_id = ? AND round = ? AND season = ?',
                      (player_id, round_num, season_val))
            exists = c.fetchone()[0]

            if exists == 0:
                # Insert new record
                c.execute('''INSERT INTO player_history (
                                player_id, round, total_points, opponent_team, season,
                                assists, bonus, bps, clean_sheets, creativity, goals_conceded,
                                goals_scored, ict_index, influence, minutes, own_goals,
                                penalties_missed, penalties_saved, red_cards, saves, threat,
                                value, was_home, yellow_cards, fixture, xP, expected_assists,
                                expected_goal_involvements, expected_goals, expected_goals_conceded,
                                kickoff_time, modified, selected, starts, team_a_score, team_h_score,
                                transfers_balance, transfers_in, transfers_out, clearances_blocks_interceptions,
                                defensive_contribution, recoveries, tackles
                             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (player_id, round_num, int(row['total_points']), int(row['opponent_team']), season_val,
                           int(row['assists']), int(row['bonus']), int(row['bps']), int(row['clean_sheets']),
                           float(row['creativity']), int(row['goals_conceded']), int(row['goals_scored']),
                           float(row['ict_index']), float(row['influence']), int(row['minutes']),
                           int(row['own_goals']), int(row['penalties_missed']), int(row['penalties_saved']),
                           int(row['red_cards']), int(row['saves']), float(row['threat']),
                           int(row['value']), bool(row['was_home']), int(row['yellow_cards']),
                           int(row.get('fixture', 0)), float(row.get('xP', 0.0)), float(row.get('expected_assists', 0.0)),
                           float(row.get('expected_goal_involvements', 0.0)), float(row.get('expected_goals', 0.0)),
                           float(row.get('expected_goals_conceded', 0.0)), str(row.get('kickoff_time', '')),
                           bool(row.get('modified', False)), int(row.get('selected', 0)), int(row.get('starts', 0)),
                           int(row.get('team_a_score', 0)), int(row.get('team_h_score', 0)),
                           int(row.get('transfers_balance', 0)), int(row.get('transfers_in', 0)),
                           int(row.get('transfers_out', 0)), int(row.get('clearances_blocks_interceptions', 0)),
                           int(row.get('defensive_contribution', 0)), int(row.get('recoveries', 0)),
                           int(row.get('tackles', 0))))
                updated += 1
            else:
                # Update existing record
                c.execute('''UPDATE player_history SET
                                total_points = ?, opponent_team = ?,
                                assists = ?, bonus = ?, bps = ?, clean_sheets = ?, creativity = ?,
                                goals_conceded = ?, goals_scored = ?, ict_index = ?, influence = ?,
                                minutes = ?, own_goals = ?, penalties_missed = ?, penalties_saved = ?,
                                red_cards = ?, saves = ?, threat = ?, value = ?, was_home = ?, yellow_cards = ?,
                                fixture = ?, xP = ?, expected_assists = ?, expected_goal_involvements = ?,
                                expected_goals = ?, expected_goals_conceded = ?, kickoff_time = ?, modified = ?,
                                selected = ?, starts = ?, team_a_score = ?, team_h_score = ?, transfers_balance = ?,
                                transfers_in = ?, transfers_out = ?, clearances_blocks_interceptions = ?,
                                defensive_contribution = ?, recoveries = ?, tackles = ?
                             WHERE player_id = ? AND round = ? AND season = ?''',
                          (int(row['total_points']), int(row['opponent_team']),
                           int(row['assists']), int(row['bonus']), int(row['bps']), int(row['clean_sheets']),
                           float(row['creativity']), int(row['goals_conceded']), int(row['goals_scored']),
                           float(row['ict_index']), float(row['influence']), int(row['minutes']),
                           int(row['own_goals']), int(row['penalties_missed']), int(row['penalties_saved']),
                           int(row['red_cards']), int(row['saves']), float(row['threat']),
                           int(row['value']), bool(row['was_home']), int(row['yellow_cards']),
                           int(row.get('fixture', 0)), float(row.get('xP', 0.0)), float(row.get('expected_assists', 0.0)),
                           float(row.get('expected_goal_involvements', 0.0)), float(row.get('expected_goals', 0.0)),
                           float(row.get('expected_goals_conceded', 0.0)), str(row.get('kickoff_time', '')),
                           bool(row.get('modified', False)), int(row.get('selected', 0)), int(row.get('starts', 0)),
                           int(row.get('team_a_score', 0)), int(row.get('team_h_score', 0)),
                           int(row.get('transfers_balance', 0)), int(row.get('transfers_in', 0)),
                           int(row.get('transfers_out', 0)), int(row.get('clearances_blocks_interceptions', 0)),
                           int(row.get('defensive_contribution', 0)), int(row.get('recoveries', 0)),
                           int(row.get('tackles', 0)),
                           player_id, round_num, season_val))
                updated += 1

        conn.commit()
        conn.close()
        print(f"Processed {updated} records for {season}")

if __name__ == "__main__":
    import sys
    season = sys.argv[1] if len(sys.argv) > 1 else '2025-26'
    print(f"Loading data for season: {season}")
    load_historic_data(season)