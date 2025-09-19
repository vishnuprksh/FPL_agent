from src.database_connection import get_connection
from src.data_fetcher import fetch_bootstrap_data, fetch_player_history

def clear_tables(conn):
    """Clear existing data from tables."""
    c = conn.cursor()
    c.execute('DELETE FROM players')
    c.execute('DELETE FROM teams')
    c.execute('DELETE FROM player_history')
    conn.commit()

def insert_teams(conn, teams):
    """Insert teams into the database."""
    c = conn.cursor()
    for team in teams:
        c.execute('''INSERT INTO teams (
                        id, code, draw, form, loss, name, played, points, position,
                        short_name, strength, team_division, unavailable, win,
                        strength_overall_home, strength_overall_away, strength_attack_home,
                        strength_attack_away, strength_defence_home, strength_defence_away, pulse_id
                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (team['id'], team.get('code'), team.get('draw'), team.get('form'), team.get('loss'),
                   team['name'], team.get('played'), team.get('points'), team.get('position'),
                   team.get('short_name'), team.get('strength'), team.get('team_division'),
                   team.get('unavailable'), team.get('win'), team.get('strength_overall_home'),
                   team.get('strength_overall_away'), team.get('strength_attack_home'),
                   team.get('strength_attack_away'), team.get('strength_defence_home'),
                   team.get('strength_defence_away'), team.get('pulse_id')))

def insert_players(conn, players):
    """Insert players into the database."""
    c = conn.cursor()
    for player in players:
        c.execute('''INSERT INTO players (
                        assists, birth_date, bonus, bps, can_select, can_transact,
                        chance_of_playing_next_round, chance_of_playing_this_round,
                        clean_sheets, clean_sheets_per_90, clearances_blocks_interceptions,
                        code, corners_and_indirect_freekicks_order, corners_and_indirect_freekicks_text,
                        cost_change_event, cost_change_event_fall, cost_change_start,
                        cost_change_start_fall, creativity, creativity_rank, creativity_rank_type,
                        defensive_contribution, defensive_contribution_per_90, direct_freekicks_order,
                        direct_freekicks_text, dreamteam_count, element_type, ep_next, ep_this,
                        event_points, expected_assists, expected_assists_per_90,
                        expected_goal_involvements, expected_goal_involvements_per_90,
                        expected_goals, expected_goals_conceded, expected_goals_conceded_per_90,
                        expected_goals_per_90, first_name, form, form_rank, form_rank_type,
                        goals_conceded, goals_conceded_per_90, goals_scored, has_temporary_code,
                        ict_index, ict_index_rank, ict_index_rank_type, id, in_dreamteam,
                        influence, influence_rank, influence_rank_type, minutes, news,
                        news_added, now_cost, now_cost_rank, now_cost_rank_type, opta_code,
                        own_goals, penalties_missed, penalties_order, penalties_saved,
                        penalties_text, photo, points_per_game, points_per_game_rank,
                        points_per_game_rank_type, recoveries, red_cards, region, removed,
                        saves, saves_per_90, second_name, selected_by_percent, selected_rank,
                        selected_rank_type, special, squad_number, starts, starts_per_90,
                        status, tackles, team, team_code, team_join_date, threat,
                        threat_rank, threat_rank_type, total_points, transfers_in,
                        transfers_in_event, transfers_out, transfers_out_event, value_form,
                        value_season, web_name, yellow_cards
                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (player.get('assists'), player.get('birth_date'), player.get('bonus'),
                   player.get('bps'), player.get('can_select'), player.get('can_transact'),
                   player.get('chance_of_playing_next_round'), player.get('chance_of_playing_this_round'),
                   player.get('clean_sheets'), player.get('clean_sheets_per_90'),
                   player.get('clearances_blocks_interceptions'), player.get('code'),
                   player.get('corners_and_indirect_freekicks_order'), player.get('corners_and_indirect_freekicks_text'),
                   player.get('cost_change_event'), player.get('cost_change_event_fall'),
                   player.get('cost_change_start'), player.get('cost_change_start_fall'),
                   player.get('creativity'), player.get('creativity_rank'), player.get('creativity_rank_type'),
                   player.get('defensive_contribution'), player.get('defensive_contribution_per_90'),
                   player.get('direct_freekicks_order'), player.get('direct_freekicks_text'),
                   player.get('dreamteam_count'), player.get('element_type'), player.get('ep_next'),
                   player.get('ep_this'), player.get('event_points'), player.get('expected_assists'),
                   player.get('expected_assists_per_90'), player.get('expected_goal_involvements'),
                   player.get('expected_goal_involvements_per_90'), player.get('expected_goals'),
                   player.get('expected_goals_conceded'), player.get('expected_goals_conceded_per_90'),
                   player.get('expected_goals_per_90'), player.get('first_name'), player.get('form'),
                   player.get('form_rank'), player.get('form_rank_type'), player.get('goals_conceded'),
                   player.get('goals_conceded_per_90'), player.get('goals_scored'), player.get('has_temporary_code'),
                   player.get('ict_index'), player.get('ict_index_rank'), player.get('ict_index_rank_type'),
                   player.get('id'), player.get('in_dreamteam'), player.get('influence'),
                   player.get('influence_rank'), player.get('influence_rank_type'), player.get('minutes'),
                   player.get('news'), player.get('news_added'), player.get('now_cost'),
                   player.get('now_cost_rank'), player.get('now_cost_rank_type'), player.get('opta_code'),
                   player.get('own_goals'), player.get('penalties_missed'), player.get('penalties_order'),
                   player.get('penalties_saved'), player.get('penalties_text'), player.get('photo'),
                   player.get('points_per_game'), player.get('points_per_game_rank'),
                   player.get('points_per_game_rank_type'), player.get('recoveries'), player.get('red_cards'),
                   player.get('region'), player.get('removed'), player.get('saves'), player.get('saves_per_90'),
                   player.get('second_name'), player.get('selected_by_percent'), player.get('selected_rank'),
                   player.get('selected_rank_type'), player.get('special'), player.get('squad_number'),
                   player.get('starts'), player.get('starts_per_90'), player.get('status'), player.get('tackles'),
                   player.get('team'), player.get('team_code'), player.get('team_join_date'), player.get('threat'),
                   player.get('threat_rank'), player.get('threat_rank_type'), player.get('total_points'),
                   player.get('transfers_in'), player.get('transfers_in_event'), player.get('transfers_out'),
                   player.get('transfers_out_event'), player.get('value_form'), player.get('value_season'),
                   player.get('web_name'), player.get('yellow_cards')))

def insert_player_history(conn, player_id, history):
    """Insert player history into the database."""
    c = conn.cursor()
    for match in history:
        c.execute('''INSERT INTO player_history (player_id, round, total_points, opponent_team)
                     VALUES (?, ?, ?, ?)''',
                  (player_id, match.get('round'), match.get('total_points'), match.get('opponent_team')))

def fetch_and_store_data():
    """Fetch data from API and store in database."""
    data = fetch_bootstrap_data()
    teams = data.get('teams', [])
    players = data.get('elements', [])
    
    conn = get_connection()
    clear_tables(conn)
    insert_teams(conn, teams)
    insert_players(conn, players)
    
    # Fetch and store player history
    for idx, player in enumerate(players):
        element_id = player['id']
        web_name = player.get('web_name', f'Player {element_id}')
        print(f"Fetching history for {web_name} ({idx+1}/{len(players)})")
        try:
            history_data = fetch_player_history(element_id)
            history = history_data.get('history', [])
            insert_player_history(conn, element_id, history)
        except Exception as e:
            print(f"Error fetching history for player {element_id}: {e}")
    
    conn.commit()
    conn.close()