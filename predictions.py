import logging
from sklearn.linear_model import LinearRegression
import numpy as np
from database_connection import get_connection

def update_player_predictions():
    """Update player predictions using linear regression on historical data."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    conn = get_connection()
    c = conn.cursor()
    # Get all players
    c.execute('SELECT id, now_cost FROM players')
    players = c.fetchall()
    for player_id, now_cost in players:
        logger.info(f"Processing player ID: {player_id}")
        # Get player history: difficulty and points
        c.execute('SELECT fixture_difficulty, total_points FROM player_history WHERE player_id = ? AND fixture_difficulty IS NOT NULL AND total_points IS NOT NULL', (player_id,))
        history = c.fetchall()
        logger.info(f"Player {player_id}: Found {len(history)} historical matches with valid data")
        
        if len(history) < 2:
            logger.warning(f"Player {player_id}: Not enough data to fit model (only {len(history)} matches)")
            pred_points = [None, None, None]
            total_pred = None
            pred_per_mil = None
        else:
            # Check for nulls (though query already filters)
            difficulties = [h[0] for h in history]
            points = [h[1] for h in history]
            if None in difficulties or None in points:
                raise ValueError(f"Player {player_id}: Null values found in history data")
            
            X = np.array(difficulties).reshape(-1, 1)
            y = np.array(points)
            model = LinearRegression()
            model.fit(X, y)
            logger.info(f"Player {player_id}: Model fitted with slope {model.coef_[0]:.4f}, intercept {model.intercept_:.4f}")
            
            # Get next 3 fixture difficulties
            c.execute('SELECT fixture_difficulty FROM player_history WHERE player_id = ? AND total_points IS NULL ORDER BY round ASC LIMIT 3', (player_id,))
            next_diffs = [row[0] for row in c.fetchall()]
            logger.info(f"Player {player_id}: Next difficulties: {next_diffs}")
            
            # If not enough future fixtures, pad with mean difficulty
            if len(next_diffs) < 3:
                mean_diff = int(np.mean(X)) if len(X) > 0 else 3
                next_diffs += [mean_diff] * (3 - len(next_diffs))
                logger.warning(f"Player {player_id}: Padded with mean difficulty {mean_diff}")
            
            pred_points = [round(float(model.predict(np.array([[d]]))[0]), 1) for d in next_diffs]
            logger.info(f"Player {player_id}: Predicted points: {pred_points}")
            
            # Check if all predictions are the same, but only if not all difficulties are the same (padded)
            pred_set = set(round(p, 1) for p in pred_points)  # Round to 1 decimal for comparison
            if len(pred_set) == 1 and len(set(next_diffs)) > 1:
                logger.warning(f"Player {player_id}: All predictions are identical ({pred_points[0]}). Possible issue with model or data.")
                # Don't raise error, just warn
            elif len(set(pred_points)) == 1:
                logger.warning(f"Player {player_id}: All predictions are identical due to same difficulties (padded).")
            
            total_pred = round(sum(pred_points), 1)
            pred_per_mil = round(total_pred / (now_cost / 10), 1) if now_cost and now_cost > 0 else None
            logger.info(f"Player {player_id}: Total pred: {total_pred}, Pred per mil: {pred_per_mil}")
        
        # Update player row
        c.execute('''UPDATE players SET pred_match1 = ?, pred_match2 = ?, pred_match3 = ?, total_pred = ?, pred_per_mil = ? WHERE id = ?''',
                  (pred_points[0], pred_points[1], pred_points[2], total_pred, pred_per_mil, player_id))
    conn.commit()
    conn.close()
    logger.info("All players processed successfully")