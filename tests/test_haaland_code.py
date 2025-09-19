#!/usr/bin/env python3
"""
Test script to verify that the player code 223094 belongs to Erling Haaland.
"""

import sqlite3

DB_PATH = '../data/fpl_data.db'

def test_haaland_code():
    """Test that code 223094 is for Haaland."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT first_name, second_name, web_name FROM players WHERE code = ?", (223094,))
    result = c.fetchone()
    conn.close()

    if result is None:
        print("No player found with code 223094")
        return False

    first_name, second_name, web_name = result
    print(f"Player with code 223094: {first_name} {second_name} ({web_name})")

    if second_name == 'Haaland':
        print("✓ Confirmed: Code 223094 is for Haaland")
        return True
    else:
        print(f"✗ Error: Expected Haaland, but got {second_name}")
        return False

if __name__ == "__main__":
    test_haaland_code()