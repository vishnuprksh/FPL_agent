from flask import Flask
from fpl_agent.models import init_db
from fpl_agent.update_db import load_historic_data, load_fixture_data
from fpl_agent.routes import home, players, teams, player_history, null_values
import sys

app = Flask(__name__)
app.template_folder = '/workspaces/FPL_agent/templates'

# If --clean is passed, reload current season + previous seasons into the DB
if '--clean' in sys.argv:
    # Default behavior: load current season and 1 previous season; you can
    # pass a different number by using --previous_years=N when running the app
    # (the update_db.main CLI also supports this).
    # Load historic player data then fixture data for the same seasons.
    load_historic_data()
    load_fixture_data()

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

@app.route('/null-values')
def null_values_route():
    return null_values()

def main():
    app.run(debug=True)

if __name__ == '__main__':
    main()
