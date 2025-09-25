import requests
import pandas as pd
from fpl_agent.database_connection import get_connection

def fetch_and_store_data():
    """Fetch data from FPL API and store in database"""
    print("Fetching data from FPL API...")

    # Fetch bootstrap static data
    bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    try:
        response = requests.get(bootstrap_url).json()

        # Store teams
        teams_df = pd.DataFrame(response['teams'])
        conn = get_connection()
        teams_df.to_sql('teams', conn, if_exists='replace', index=False)

        # Store players
        players_df = pd.DataFrame(response['elements'])
        players_df.to_sql('players', conn, if_exists='replace', index=False)

        conn.close()
        print(f"Stored {len(teams_df)} teams and {len(players_df)} players")

    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_and_store_data()
