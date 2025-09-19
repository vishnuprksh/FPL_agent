import requests
import csv

API_URL = 'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/players_raw.csv'

def fetch_bootstrap_data():
    """Fetch bootstrap data from GitHub CSV."""
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.text
    reader = csv.DictReader(data.splitlines())
    players = list(reader)
    return {'elements': players}

def fetch_player_history(player_id):
    """Fetch player history for a specific player."""
    history_url = f'https://fantasy.premierleague.com/api/element-summary/{player_id}/'
    response = requests.get(history_url)
    response.raise_for_status()
    return response.json()