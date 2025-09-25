from fpl_agent.database_connection import get_connection

def get_player_columns():
    """Get all column names from players table."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("PRAGMA table_info(players)")
    columns = [row[1] for row in c.fetchall()]
    conn.close()
    return columns

def get_players(columns=None):
    """Retrieve players with selected columns."""
    # prediction columns removed from schema; only include available columns
    columns = ['player_code', 'web_name', 'position', 'team_name', 'now_cost', 'total_points', 'form']

    
    select_columns = []
    for col in columns:
        if col == 'position':
            select_columns.append("CASE p.element_type WHEN 1 THEN 'GK' WHEN 2 THEN 'DEF' WHEN 3 THEN 'MID' WHEN 4 THEN 'FWD' END as position")
        elif col == 'team_name':
            select_columns.append("t.name as team_name")
        
        else:
            select_columns.append(f"p.{col}")
    
    query = f"SELECT {', '.join(select_columns)} FROM players p JOIN teams t ON p.team = t.id ORDER BY p.web_name"
    
    conn = get_connection()
    c = conn.cursor()
    c.execute(query)
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
    """Retrieve all teams."""
    conn = get_connection()
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

def get_player_history(player_id):
    """Retrieve history for a specific player."""
    conn = get_connection()
    c = conn.cursor()
    # player_history stores player identifiers in the 'player_code' column
    # join using players.player_code (stable code across seasons). Also filter by ph.player_code
    c.execute('''SELECT ph.*, p.web_name, p.team, t.name as team_name
                 FROM player_history ph
                 JOIN players p ON ph.player_code = p.player_code
                 JOIN teams t ON ph.opponent_team = t.id
                 WHERE ph.player_code = ?
                 ORDER BY ph.season DESC, ph.round''', (player_id,))
    history_data = c.fetchall()
    
    # Get column names
    column_names = [description[0] for description in c.description]
    
    conn.close()
    
    history = []
    for row in history_data:
        history_dict = dict(zip(column_names, row))
        history.append(history_dict)
    
    return history

def get_null_percentages():
    """Retrieve null value percentages for all tables and columns."""
    conn = get_connection()
    c = conn.cursor()
    
    # Get all table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in c.fetchall()]
    
    null_data = []
    
    for table in tables:
        # Get column info
        c.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in c.fetchall()]  # column names
        
        # Get total rows
        c.execute(f"SELECT COUNT(*) FROM {table}")
        total_rows = c.fetchone()[0]
        
        if total_rows == 0:
            continue
        
        for column in columns:
            # Count nulls
            c.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
            null_count = c.fetchone()[0]
            percentage = (null_count / total_rows) * 100 if total_rows > 0 else 0
            null_data.append({
                'table': table,
                'column': column,
                'total_rows': total_rows,
                'null_count': null_count,
                'percentage': round(percentage, 2)
            })
    
    conn.close()
    return null_data
