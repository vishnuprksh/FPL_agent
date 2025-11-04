#!/usr/bin/env python3
"""
FPL Agent - Validate prediction model accuracy.

This script validates the ML model by generating predictions for past gameweeks
using only historical data available before each gameweek, then comparing
predictions against actual results to measure accuracy.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import numpy as np
from pathlib import Path
from fpl_agent.database import FPLDatabase
from fpl_agent.pipeline import PointsPredictor


class TestPredictionsGenerator:
    """Generate test predictions for past gameweeks to validate model accuracy."""
    
    def __init__(self, db: FPLDatabase):
        self.db = db
        self.test_gameweeks = []
    
    def get_available_gameweeks(self, season: str = "2025-26"):
        """Get list of gameweeks with data."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT gw FROM player_gameweek_history
                WHERE season = ?
                ORDER BY gw
            """, (season,))
            return [row[0] for row in cursor]
    
    def train_predictor_up_to_gw(self, max_gw: int):
        """Train a predictor using only data up to max_gw."""
        predictor = PointsPredictor(self.db, model_path=f"models/test_predictor_gw{max_gw}.pkl")
        
        # Load training data filtered by gameweek
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT element, name, team_attack_value, team_defense_value,
                       opponent_attack_value, opponent_defense_value, was_home, total_points
                FROM player_match_context
                WHERE gw <= ?
                  AND team_attack_value IS NOT NULL AND team_defense_value IS NOT NULL
                  AND opponent_attack_value IS NOT NULL AND opponent_defense_value IS NOT NULL
                  AND was_home IS NOT NULL AND total_points IS NOT NULL
            """, (max_gw,))
            data = cursor.fetchall()
        
        if not data:
            return None
        
        # Group by player
        player_data = {}
        for row in data:
            element = row[0]
            team_attack = row[2]
            team_defense = row[3]
            opp_attack = row[4]
            opp_defense = row[5]
            was_home = row[6]
            total_points = row[7]
            
            # Calculate differential features
            attack_advantage = team_attack - opp_defense
            defense_advantage = team_defense - opp_attack
            
            if element not in player_data:
                player_data[element] = {'name': row[1], 'X': [], 'y': []}
            
            # Features: [attack_advantage, defense_advantage, was_home]
            player_data[element]['X'].append([attack_advantage, defense_advantage, was_home])
            player_data[element]['y'].append(total_points)
        
        # Convert to numpy arrays and train
        for element in player_data:
            player_data[element]['X'] = np.array(player_data[element]['X'])
            player_data[element]['y'] = np.array(player_data[element]['y'])
            
            result = predictor.train_model(player_data[element]['X'], player_data[element]['y'])
            if result is not None:
                model_dict, mae = result
                predictor.models[element] = {
                    'model': model_dict['model'],
                    'scaler': model_dict['scaler'],
                    'name': player_data[element]['name'],
                    'samples': len(player_data[element]['X']),
                    'mae': mae
                }
        
        return predictor
    
    def get_team_valuations_up_to_gw(self, max_gw: int):
        """Get team valuations using only data up to max_gw."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT team, AVG(attack_value), AVG(defense_value)
                FROM team_fixture_valuations
                WHERE gw <= ?
                GROUP BY team
            """, (max_gw,))
            return {row[0]: {'attack': row[1], 'defense': row[2]} for row in cursor}
    
    def create_table(self):
        """Create test predictions table."""
        with self.db.get_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS test_predictions")
            conn.execute("""
                CREATE TABLE test_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_gw INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    player_name TEXT NOT NULL,
                    team_name TEXT NOT NULL,
                    opponent_name TEXT NOT NULL,
                    was_home BOOLEAN NOT NULL,
                    predicted_points REAL NOT NULL,
                    actual_points INTEGER,
                    error REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX idx_test_gw ON test_predictions(test_gw)")
            conn.execute("CREATE INDEX idx_test_player ON test_predictions(player_id)")
            conn.commit()
    
    def run(self, season: str = "2025-26"):
        """Generate test predictions and validate."""
        print(f"\n{'='*60}")
        print("GENERATING TEST PREDICTIONS FOR VALIDATION")
        print(f"{'='*60}")
        
        self.create_table()
        
        available_gws = self.get_available_gameweeks(season)
        if len(available_gws) < 2:
            print("  ⚠ Not enough gameweeks for testing (need at least 2)")
            return {'test_gameweeks': 0, 'predictions': 0}
        
        # Test on gameweeks where we have data, starting from GW 2
        test_gws = [gw for gw in available_gws if gw > 1]
        print(f"  ✓ Will test predictions for GW: {test_gws}")
        
        all_predictions = []
        
        for test_gw in test_gws:
            print(f"\n  Testing GW {test_gw}:")
            
            # Train on data up to previous gameweek
            train_up_to = test_gw - 1
            print(f"    Training on data up to GW {train_up_to}...")
            predictor = self.train_predictor_up_to_gw(train_up_to)
            
            if predictor is None or not predictor.models:
                print(f"    ✗ No training data available")
                continue
            
            print(f"    ✓ Trained {len(predictor.models)} player models")
            
            # Get team valuations up to training cutoff
            team_valuations = self.get_team_valuations_up_to_gw(train_up_to)
            
            # Get actual matches from test gameweek
            with self.db.get_connection() as conn:
                matches = conn.execute("""
                    SELECT element, name, team, opponent_team, was_home, total_points,
                           team_attack_value, team_defense_value,
                           opponent_attack_value, opponent_defense_value
                    FROM player_match_context
                    WHERE gw = ? AND season = ?
                """, (test_gw, season)).fetchall()
            
            if not matches:
                print(f"    ✗ No match data found for GW {test_gw}")
                continue
            
            # Generate predictions
            for match in matches:
                player_id, name, team, opp, is_home, actual_pts, t_atk, t_def, o_atk, o_def = match
                
                # Use historic valuations if available, otherwise current
                if team in team_valuations:
                    team_attack = team_valuations[team]['attack']
                    team_defense = team_valuations[team]['defense']
                else:
                    team_attack, team_defense = t_atk, t_def
                
                if opp in team_valuations:
                    opp_attack = team_valuations[opp]['attack']
                    opp_defense = team_valuations[opp]['defense']
                else:
                    opp_attack, opp_defense = o_atk, o_def
                
                pred_pts = predictor.predict(player_id, team_attack, team_defense, opp_attack, opp_defense, is_home)
                error = pred_pts - actual_pts
                
                all_predictions.append((test_gw, player_id, name, team, opp, is_home, pred_pts, actual_pts, error))
            
            print(f"    ✓ Generated {len(matches)} predictions")
        
        # Insert all predictions
        if all_predictions:
            with self.db.get_connection() as conn:
                conn.executemany("""
                    INSERT INTO test_predictions (
                        test_gw, player_id, player_name, team_name, opponent_name,
                        was_home, predicted_points, actual_points, error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, all_predictions)
                conn.commit()
        
        print(f"\n  ✓ Generated {len(all_predictions)} test predictions")
        
        # Calculate validation metrics
        self.display_validation_summary()
        
        return {'test_gameweeks': len(test_gws), 'predictions': len(all_predictions)}
    
    def display_validation_summary(self):
        """Display validation metrics."""
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        
        with self.db.get_connection() as conn:
            # Overall metrics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as n,
                    AVG(ABS(error)) as mae,
                    AVG(error * error) as mse,
                    AVG(predicted_points) as avg_pred,
                    AVG(actual_points) as avg_actual
                FROM test_predictions
            """)
            row = cursor.fetchone()
            n, mae, mse, avg_pred, avg_actual = row
            rmse = np.sqrt(mse) if mse else 0
            
            print(f"\nOverall Metrics ({n} predictions):")
            print(f"  MAE (Mean Absolute Error):  {mae:.2f} points")
            print(f"  RMSE (Root Mean Squared):   {rmse:.2f} points")
            print(f"  Average Predicted Points:   {avg_pred:.2f}")
            print(f"  Average Actual Points:      {avg_actual:.2f}")
            
            # Per gameweek breakdown
            print(f"\nPer Gameweek Breakdown:")
            cursor = conn.execute("""
                SELECT 
                    test_gw,
                    COUNT(*) as n,
                    AVG(ABS(error)) as mae,
                    AVG(predicted_points) as avg_pred,
                    AVG(actual_points) as avg_actual
                FROM test_predictions
                GROUP BY test_gw
                ORDER BY test_gw
            """)
            for row in cursor:
                gw, n, mae, avg_pred, avg_actual = row
                print(f"  GW {gw:2d}: MAE={mae:.2f}, Pred={avg_pred:.2f}, Actual={avg_actual:.2f} ({n} predictions)")
            
            # Best and worst predictions
            print(f"\nBest Predictions (smallest error):")
            cursor = conn.execute("""
                SELECT player_name, team_name, test_gw, predicted_points, actual_points, ABS(error) as abs_error
                FROM test_predictions
                ORDER BY abs_error ASC
                LIMIT 5
            """)
            for row in cursor:
                name, team, gw, pred, actual, err = row
                print(f"  {name:20s} ({team:15s}) GW{gw}: Pred={pred:4.1f}, Actual={actual:2d}, Error={err:.1f}")
            
            print(f"\nWorst Predictions (largest error):")
            cursor = conn.execute("""
                SELECT player_name, team_name, test_gw, predicted_points, actual_points, ABS(error) as abs_error
                FROM test_predictions
                ORDER BY abs_error DESC
                LIMIT 5
            """)
            for row in cursor:
                name, team, gw, pred, actual, err = row
                print(f"  {name:20s} ({team:15s}) GW{gw}: Pred={pred:4.1f}, Actual={actual:2d}, Error={err:.1f}")
        
        print(f"{'='*60}\n")


def main():
    """Run validation analysis."""
    parser = argparse.ArgumentParser(
        description='Validate FPL prediction model accuracy'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/fpl_agent.db',
        help='Path to SQLite database file (default: data/fpl_agent.db)'
    )
    parser.add_argument(
        '--season',
        type=str,
        default='2025-26',
        help='Season to validate (default: 2025-26)'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    db = FPLDatabase(args.db_path)
    
    # Run validation
    validator = TestPredictionsGenerator(db)
    results = validator.run(season=args.season)
    
    print(f"\nValidation complete!")
    print(f"  Test gameweeks: {results['test_gameweeks']}")
    print(f"  Total predictions: {results['predictions']}")
    print(f"  Results saved to: test_predictions table in {args.db_path}\n")
    
    return results


if __name__ == "__main__":
    main()
