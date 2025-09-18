import sqlite3
import requests

API_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'
DB_PATH = 'fpl_data.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY,
                    code INTEGER,
                    draw INTEGER,
                    form REAL,
                    loss INTEGER,
                    name TEXT,
                    played INTEGER,
                    points INTEGER,
                    position INTEGER,
                    short_name TEXT,
                    strength INTEGER,
                    team_division INTEGER,
                    unavailable BOOLEAN,
                    win INTEGER,
                    strength_overall_home INTEGER,
                    strength_overall_away INTEGER,
                    strength_attack_home INTEGER,
                    strength_attack_away INTEGER,
                    strength_defence_home INTEGER,
                    strength_defence_away INTEGER,
                    pulse_id INTEGER
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS players (
                    assists INTEGER,
                    birth_date TEXT,
                    bonus INTEGER,
                    bps INTEGER,
                    can_select BOOLEAN,
                    can_transact BOOLEAN,
                    chance_of_playing_next_round REAL,
                    chance_of_playing_this_round REAL,
                    clean_sheets INTEGER,
                    clean_sheets_per_90 TEXT,
                    clearances_blocks_interceptions INTEGER,
                    code INTEGER,
                    corners_and_indirect_freekicks_order INTEGER,
                    corners_and_indirect_freekicks_text TEXT,
                    cost_change_event INTEGER,
                    cost_change_event_fall INTEGER,
                    cost_change_start INTEGER,
                    cost_change_start_fall INTEGER,
                    creativity TEXT,
                    creativity_rank INTEGER,
                    creativity_rank_type INTEGER,
                    defensive_contribution INTEGER,
                    defensive_contribution_per_90 TEXT,
                    direct_freekicks_order INTEGER,
                    direct_freekicks_text TEXT,
                    dreamteam_count INTEGER,
                    element_type INTEGER,
                    ep_next TEXT,
                    ep_this TEXT,
                    event_points INTEGER,
                    expected_assists TEXT,
                    expected_assists_per_90 TEXT,
                    expected_goal_involvements TEXT,
                    expected_goal_involvements_per_90 TEXT,
                    expected_goals TEXT,
                    expected_goals_conceded TEXT,
                    expected_goals_conceded_per_90 TEXT,
                    expected_goals_per_90 TEXT,
                    first_name TEXT,
                    form TEXT,
                    form_rank INTEGER,
                    form_rank_type INTEGER,
                    goals_conceded INTEGER,
                    goals_conceded_per_90 TEXT,
                    goals_scored INTEGER,
                    has_temporary_code BOOLEAN,
                    ict_index TEXT,
                    ict_index_rank INTEGER,
                    ict_index_rank_type INTEGER,
                    id INTEGER PRIMARY KEY,
                    in_dreamteam BOOLEAN,
                    influence TEXT,
                    influence_rank INTEGER,
                    influence_rank_type INTEGER,
                    minutes INTEGER,
                    news TEXT,
                    news_added TEXT,
                    now_cost INTEGER,
                    now_cost_rank INTEGER,
                    now_cost_rank_type INTEGER,
                    opta_code INTEGER,
                    own_goals INTEGER,
                    penalties_missed INTEGER,
                    penalties_order INTEGER,
                    penalties_saved INTEGER,
                    penalties_text TEXT,
                    photo TEXT,
                    points_per_game TEXT,
                    points_per_game_rank INTEGER,
                    points_per_game_rank_type INTEGER,
                    recoveries INTEGER,
                    red_cards INTEGER,
                    region INTEGER,
                    removed BOOLEAN,
                    saves INTEGER,
                    saves_per_90 TEXT,
                    second_name TEXT,
                    selected_by_percent TEXT,
                    selected_rank INTEGER,
                    selected_rank_type INTEGER,
                    special BOOLEAN,
                    squad_number INTEGER,
                    starts INTEGER,
                    starts_per_90 TEXT,
                    status TEXT,
                    tackles INTEGER,
                    team INTEGER,
                    team_code INTEGER,
                    team_join_date TEXT,
                    threat TEXT,
                    threat_rank INTEGER,
                    threat_rank_type INTEGER,
                    total_points INTEGER,
                    transfers_in INTEGER,
                    transfers_in_event INTEGER,
                    transfers_out INTEGER,
                    transfers_out_event INTEGER,
                    value_form TEXT,
                    value_season TEXT,
                    web_name TEXT,
                    yellow_cards INTEGER
                )''')
    conn.commit()
    conn.close()

def fetch_and_store_data():
    response = requests.get(API_URL)
    data = response.json()
    teams = data.get('teams', [])
    players = data.get('elements', [])
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Clear existing data
    c.execute('DELETE FROM players')
    c.execute('DELETE FROM teams')
    
    # Insert teams
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
    
    # Insert players
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
                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
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
    
    conn.commit()
    conn.close()

def get_players():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT p.web_name,
                        CASE p.element_type
                            WHEN 1 THEN 'GK'
                            WHEN 2 THEN 'DEF'
                            WHEN 3 THEN 'MID'
                            WHEN 4 THEN 'FWD'
                        END as position,
                        t.name as team_name,
                        p.now_cost,
                        p.total_points,
                        p.form
                 FROM players p
                 JOIN teams t ON p.team = t.id
                 ORDER BY p.web_name''')
    players_data = c.fetchall()
    
    # Get column names
    column_names = [description[0] for description in c.description]
    
    conn.close()
    
    players = []
    for row in players_data:
        player_dict = dict(zip(column_names, row))
        players.append(player_dict)
    
    return players

def get_teams():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT * FROM teams''')
    teams_data = c.fetchall()
    
    # Get column names
    column_names = [description[0] for description in c.description]
    
    conn.close()
    
    teams_list = []
    for row in teams_data:
        team_dict = dict(zip(column_names, row))
        teams_list.append(team_dict)
    
    return teams_list
