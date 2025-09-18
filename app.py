from flask import Flask
from db import init_db, fetch_and_store_data
from routes import home, players, teams
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

if __name__ == '__main__':
    app.run(debug=True)