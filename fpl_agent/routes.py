from flask import render_template, request
from fpl_agent.queries import get_players, get_teams, get_player_history, get_null_percentages, get_player_columns

def home():
    return render_template('home.html')

def players():
    columns = request.args.get('columns')
    if columns:
        columns = columns.split(',')
    players = get_players(columns)
    all_keys = get_player_columns() + ['position', 'team_name']
    selected_columns = columns if columns else ['id', 'web_name', 'position', 'team_name', 'now_cost', 'total_points', 'form']
    return render_template('players.html', players=players, all_keys=all_keys, selected_columns=selected_columns)

def teams():
    teams_list = get_teams()
    all_keys = list(teams_list[0].keys()) if teams_list else []
    return render_template('teams.html', teams=teams_list, all_keys=all_keys)

def player_history(player_id):
    history = get_player_history(player_id)
    player_name = history[0]['web_name'] if history else f"Player {player_id}"
    all_keys = list(history[0].keys()) if history else []
    return render_template('player_history.html', history=history, player_name=player_name, all_keys=all_keys)

def null_values():
    null_data = get_null_percentages()
    return render_template('null_values.html', null_data=null_data)
