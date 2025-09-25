import sqlite3
import os

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'fpl_data.db')

def get_connection():
    """Get a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)
