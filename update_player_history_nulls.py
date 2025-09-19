import sqlite3

DB_PATH = 'fpl_data.db'

def update_nulls():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # List of columns to update with 0 if null
    numeric_columns = [
        'total_points', 'opponent_team', 'assists', 'bonus', 'bps', 'clean_sheets',
        'creativity', 'goals_conceded', 'goals_scored', 'ict_index', 'influence',
        'minutes', 'own_goals', 'penalties_missed', 'penalties_saved', 'red_cards',
        'saves', 'threat', 'value', 'was_home', 'yellow_cards', 'fixture', 'xP',
        'expected_assists', 'expected_goal_involvements', 'expected_goals',
        'expected_goals_conceded', 'selected', 'starts', 'team_a_score', 'team_h_score',
        'transfers_balance', 'transfers_in', 'transfers_out', 'clearances_blocks_interceptions',
        'defensive_contribution', 'recoveries', 'tackles', 'fixture_difficulty'
    ]

    text_columns = ['kickoff_time']

    boolean_columns = ['modified']

    for col in numeric_columns:
        c.execute(f'UPDATE player_history SET {col} = 0 WHERE {col} IS NULL')
        updated = c.rowcount
        print(f'Updated {updated} nulls in {col} to 0')

    for col in text_columns:
        c.execute(f'UPDATE player_history SET {col} = "" WHERE {col} IS NULL')
        updated = c.rowcount
        print(f'Updated {updated} nulls in {col} to ""')

    for col in boolean_columns:
        c.execute(f'UPDATE player_history SET {col} = 0 WHERE {col} IS NULL')
        updated = c.rowcount
        print(f'Updated {updated} nulls in {col} to 0')

    # For season, if null, perhaps set to 'unknown', but only 3, maybe leave or set to '2025-26'
    c.execute("UPDATE player_history SET season = '2025-26' WHERE season IS NULL")
    updated = c.rowcount
    print(f'Updated {updated} null seasons to 2025-26')

    conn.commit()
    conn.close()
    print("All nulls updated.")

if __name__ == "__main__":
    update_nulls()