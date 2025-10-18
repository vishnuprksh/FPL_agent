#!/usr/bin/env python3
"""
FPL Agent - Load elements data from FPL API to SQLite database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from fpl_agent import FPLAPIClient, FPLDatabase


def main():
    """Main function to load FPL elements data."""
    # Define database path
    db_path = Path("data/fpl_agent.db")
    
    print("Fetching FPL data...")
    api_client = FPLAPIClient()
    fpl_data = api_client.fetch_bootstrap_data()
    
    print("Creating database...")
    db = FPLDatabase(str(db_path))
    db_path.parent.mkdir(exist_ok=True)
    db.create_elements_table()
    
    print("Loading elements data...")
    elements = fpl_data.get('elements', [])
    teams = fpl_data.get('teams', [])
    db.insert_elements_data(elements, teams)
    
    print(f"Successfully loaded {len(elements)} players to {db_path}")


if __name__ == "__main__":
    main()
