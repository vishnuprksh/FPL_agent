import sqlite3

DB_PATH = 'data/fpl_data.db'

def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DB_PATH)

def close_connection(conn):
    """Close the database connection."""
    if conn:
        conn.close()