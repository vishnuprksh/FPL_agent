from flask import render_template
from db import get_players, get_teams

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