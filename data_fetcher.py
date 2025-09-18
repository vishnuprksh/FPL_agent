import requests

API_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'

def fetch_bootstrap_data():
    """Fetch bootstrap data from FPL API."""
    response = requests.get(API_URL)
    response.raise_for_status()
    return response.json()

def fetch_player_history(player_id):
    """Fetch player history for a specific player."""
    history_url = f'https://fantasy.premierleague.com/api/element-summary/{player_id}/'
    response = requests.get(history_url)
    response.raise_for_status()
    return response.json()