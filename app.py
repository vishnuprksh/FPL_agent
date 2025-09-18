from flask import Flask, render_template
import requests

app = Flask(__name__)

API_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/players')
def players():
    response = requests.get(API_URL)
    data = response.json()
    players = data.get('elements', [])
    teams = data.get('teams', [])
    team_dict = {t['id']: t['name'] for t in teams}
    position_dict = {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}
    for player in players:
        player['team_name'] = team_dict.get(player['team'], 'Unknown')
        player['position'] = position_dict.get(player['element_type'], 'Unknown')
    all_keys = list(players[0].keys()) if players else []
    return render_template('players.html', players=players, all_keys=all_keys)

@app.route('/teams')
def teams():
    response = requests.get(API_URL)
    data = response.json()
    teams = data.get('teams', [])
    all_keys = list(teams[0].keys()) if teams else []
    return render_template('teams.html', teams=teams, all_keys=all_keys)

if __name__ == '__main__':
    app.run(debug=True)