from flask import Flask
from db import init_db, fetch_and_store_data
from routes import home, players, teams, player_history
import sys

app = Flask(__name__)

# Initialize DB on startup
init_db()
if '--clean' in sys.argv:
    fetch_and_store_data()

@app.route('/')
def home_route():
    return home()

@app.route('/players')
def players_route():
    return players()

@app.route('/teams')
def teams_route():
    return teams()

@app.route('/player/<int:player_id>/history')
def player_history_route(player_id):
    return player_history(player_id)

if __name__ == '__main__':
    app.run(debug=True)