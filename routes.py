from flask import render_template
from db import get_players, get_teams, get_player_history

def home():
    return render_template('home.html')

def players():
    players = get_players()
    all_keys = list(players[0].keys()) if players else []
    return render_template('players.html', players=players, all_keys=all_keys)

def teams():
    teams_list = get_teams()
    all_keys = list(teams_list[0].keys()) if teams_list else []
    return render_template('teams.html', teams=teams_list, all_keys=all_keys)

def player_history(player_id):
    history = get_player_history(player_id)
    player_name = history[0]['web_name'] if history else f"Player {player_id}"
    all_keys = list(history[0].keys()) if history else []
    return render_template('player_history.html', history=history, player_name=player_name, all_keys=all_keys)