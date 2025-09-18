import sqlite3
from db import DB_PATH

def test_predictions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Get a few players with their predictions
    c.execute('''SELECT id, web_name, pred_match1, pred_match2, pred_match3, total_pred, pred_per_mil
                 FROM players
                 WHERE pred_match1 IS NOT NULL
                 LIMIT 5''')
    results = c.fetchall()
    conn.close()

    if not results:
        print("No prediction data found in database. Run update_player_predictions() first.")
        return

    print("Prediction data for first 5 players with predictions:")
    for row in results:
        player_id, web_name, pred1, pred2, pred3, total, per_mil = row
        print(f"Player: {web_name} (ID: {player_id})")
        print(f"  Pred Match 1: {pred1}")
        print(f"  Pred Match 2: {pred2}")
        print(f"  Pred Match 3: {pred3}")
        print(f"  Total Pred: {total}")
        print(f"  Pred per Mil: {per_mil}")
        print()

if __name__ == "__main__":
    test_predictions()