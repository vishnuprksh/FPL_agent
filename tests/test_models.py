import sqlite3
from fpl_agent import models


def test_init_db_creates_tables(tmp_path, monkeypatch):
    """Ensure init_db creates the expected tables in a temporary database."""
    db_path = tmp_path / "test_fpl_data.db"

    # Monkeypatch models.get_connection to return a connection to our temp DB
    def _get_conn():
        return sqlite3.connect(str(db_path))

    monkeypatch.setattr(models, "get_connection", _get_conn)

    # Call the function under test
    models.init_db()

    # Open a new connection to inspect which tables were created
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    expected = {"teams", "players", "player_history", "fixtures"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"
