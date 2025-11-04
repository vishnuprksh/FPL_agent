"""
FPL Agent - Data pipeline components for database initialization.
"""

import pandas as pd
import requests
import numpy as np
import pickle
from io import StringIO
from pathlib import Path
from datetime import datetime
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error

from .database import FPLDatabase


class HistoricDataLoader:
    """Load historic gameweek data from GitHub."""
    
    def __init__(self, db: FPLDatabase, season: str = "2025-26"):
        self.db = db
        self.season = season
        self.base_url = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master"
    
    def fetch_gameweek_csv(self, gw: int) -> pd.DataFrame:
        """Fetch gameweek CSV data from GitHub repository."""
        url = f"{self.base_url}/data/{self.season}/gws/gw{gw}.csv"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
            return df
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception:
            raise
    
    def run(self, max_gameweeks: int = 38, replace_existing: bool = False):
        """Load historic gameweek data."""
        print(f"\n{'='*60}")
        print(f"STEP 1: Loading historic gameweek data for {self.season}")
        print(f"{'='*60}")
        
        self.db.create_player_gameweek_history_table()
        
        total_records = 0
        successful_gameweeks = []
        
        for gw in range(1, max_gameweeks + 1):
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM player_gameweek_history WHERE season = ? AND gw = ?",
                    (self.season, gw)
                )
                existing_count = cursor.fetchone()[0]
            
            if existing_count > 0 and not replace_existing:
                successful_gameweeks.append(gw)
                total_records += existing_count
                continue
            
            if existing_count > 0 and replace_existing:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM player_gameweek_history WHERE season = ? AND gw = ?",
                        (self.season, gw)
                    )
                    conn.commit()
            
            df = self.fetch_gameweek_csv(gw)
            
            if df is not None:
                try:
                    self.db.insert_gameweek_data(self.season, gw, df)
                    total_records += len(df)
                    successful_gameweeks.append(gw)
                except Exception as e:
                    print(f"  ✗ Error inserting GW{gw}: {e}")
                    raise
        
        print(f"  ✓ Loaded {len(successful_gameweeks)} gameweeks ({total_records} records)")
        return {'gameweeks': len(successful_gameweeks), 'records': total_records}


class TeamValuationCalculator:
    """Calculate team attack and defense valuations from historic data."""
    
    def __init__(self, db: FPLDatabase):
        self.db = db
    
    def create_table(self):
        """Create team valuations table."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_fixture_valuations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    season TEXT NOT NULL,
                    gw INTEGER NOT NULL,
                    fixture INTEGER NOT NULL,
                    team TEXT NOT NULL,
                    defense_value REAL NOT NULL,
                    attack_value REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(season, gw, fixture, team)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_fixture 
                ON team_fixture_valuations(season, gw, fixture, team)
            """)
            conn.commit()
    
    def run(self):
        """Calculate and insert team valuations."""
        print(f"\n{'='*60}")
        print("STEP 2: Calculating team valuations")
        print(f"{'='*60}")
        
        self.create_table()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO team_fixture_valuations 
                (season, gw, fixture, team, defense_value, attack_value)
                SELECT 
                    season, gw, fixture, team,
                    COALESCE(SUM(CASE WHEN position IN ('GK', 'DEF') THEN value ELSE 0 END), 0) as defense_value,
                    COALESCE(SUM(CASE WHEN position IN ('MID', 'FWD') THEN value ELSE 0 END), 0) as attack_value
                FROM player_gameweek_history
                WHERE starts = 1
                GROUP BY season, gw, fixture, team
                ORDER BY season, gw, fixture, team
            """)
            conn.commit()
            rows = cursor.rowcount
        
        print(f"  ✓ Calculated valuations for {rows} team-fixtures")
        return {'valuations': rows}


class PlayerMatchContextBuilder:
    """Build player match context with team and opponent data."""
    
    def __init__(self, db: FPLDatabase):
        self.db = db
    
    def create_table(self):
        """Create player match context table."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_match_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    season TEXT NOT NULL,
                    gw INTEGER NOT NULL,
                    fixture INTEGER NOT NULL,
                    element INTEGER NOT NULL,
                    name TEXT,
                    team TEXT,
                    total_points INTEGER,
                    value REAL,
                    was_home BOOLEAN,
                    team_attack_value REAL,
                    team_defense_value REAL,
                    opponent_team TEXT,
                    opponent_attack_value REAL,
                    opponent_defense_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(season, gw, fixture, element)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_player_match 
                ON player_match_context(element, season, gw)
            """)
            conn.commit()
    
    def run(self):
        """Populate player match context."""
        print(f"\n{'='*60}")
        print("STEP 3: Building player match context")
        print(f"{'='*60}")
        
        self.create_table()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO player_match_context (
                    season, gw, fixture, element, name, team, total_points, value, was_home,
                    team_attack_value, team_defense_value, opponent_team,
                    opponent_attack_value, opponent_defense_value
                )
                SELECT 
                    h.season, h.gw, h.fixture, h.element, h.name, h.team,
                    h.total_points, h.value, h.was_home,
                    tv.attack_value, tv.defense_value, ov.team,
                    ov.attack_value, ov.defense_value
                FROM player_gameweek_history h
                LEFT JOIN team_fixture_valuations tv 
                    ON h.season = tv.season AND h.gw = tv.gw 
                    AND h.fixture = tv.fixture AND h.team = tv.team
                LEFT JOIN team_fixture_valuations ov 
                    ON h.season = ov.season AND h.gw = ov.gw 
                    AND h.fixture = ov.fixture AND h.team != ov.team
                WHERE tv.team IS NOT NULL AND ov.team IS NOT NULL
                ORDER BY h.season, h.gw, h.fixture, h.element
            """)
            conn.commit()
            rows = cursor.rowcount
        
        print(f"  ✓ Built context for {rows} player matches")
        return {'matches': rows}


class PointsPredictor:
    """Train ML models to predict player points."""
    
    def __init__(self, db: FPLDatabase, model_path: str = "models/player_points_predictors.pkl"):
        self.db = db
        self.model_path = Path(model_path)
        self.models = {}
    
    def load_training_data(self):
        """Load player match context data grouped by player."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT element, name, team_attack_value, team_defense_value,
                       opponent_attack_value, opponent_defense_value, was_home, total_points
                FROM player_match_context
                WHERE team_attack_value IS NOT NULL AND team_defense_value IS NOT NULL
                  AND opponent_attack_value IS NOT NULL AND opponent_defense_value IS NOT NULL
                  AND was_home IS NOT NULL AND total_points IS NOT NULL
            """)
            data = cursor.fetchall()
        
        if not data:
            raise ValueError("No training data found")
        
        # Group by player
        player_data = {}
        for row in data:
            element = row[0]
            if element not in player_data:
                player_data[element] = {'name': row[1], 'X': [], 'y': []}
            player_data[element]['X'].append([row[2], row[3], row[4], row[5], row[6]])
            player_data[element]['y'].append(row[7])
        
        # Convert to numpy arrays
        for element in player_data:
            player_data[element]['X'] = np.array(player_data[element]['X'])
            player_data[element]['y'] = np.array(player_data[element]['y'])
        
        return player_data
    
    def train_model(self, X, y, min_samples=5):
        """Train Ridge regression model for a player."""
        if len(X) < min_samples:
            return None
        
        model = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', Ridge(alpha=1.0))
        ])
        model.fit(X, y)
        
        y_pred = model.predict(X)
        mae = mean_absolute_error(y, y_pred)
        
        return model, mae
    
    def run(self):
        """Train models for all players."""
        print(f"\n{'='*60}")
        print("STEP 4: Training points prediction models")
        print(f"{'='*60}")
        
        player_data = self.load_training_data()
        print(f"  ✓ Loaded data for {len(player_data)} players")
        
        trained = 0
        skipped = 0
        
        for element, data in player_data.items():
            result = self.train_model(data['X'], data['y'])
            if result is None:
                skipped += 1
                continue
            
            model, mae = result
            self.models[element] = {
                'model': model,
                'name': data['name'],
                'samples': len(data['X']),
                'mae': mae
            }
            trained += 1
        
        # Save models
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.models, f)
        
        print(f"  ✓ Trained {trained} models (skipped {skipped})")
        print(f"  ✓ Saved to {self.model_path}")
        return {'trained': trained, 'skipped': skipped}
    
    def predict(self, player_id, team_attack, team_defense, opp_attack, opp_defense, is_home):
        """Predict points for a player."""
        if player_id not in self.models:
            return 0.0
        
        features = np.array([[team_attack, team_defense, opp_attack, opp_defense, is_home]])
        predicted = self.models[player_id]['model'].predict(features)[0]
        return np.clip(predicted, 0, 15)


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
            if element not in player_data:
                player_data[element] = {'name': row[1], 'X': [], 'y': []}
            player_data[element]['X'].append([row[2], row[3], row[4], row[5], row[6]])
            player_data[element]['y'].append(row[7])
        
        # Convert to numpy arrays and train
        for element in player_data:
            player_data[element]['X'] = np.array(player_data[element]['X'])
            player_data[element]['y'] = np.array(player_data[element]['y'])
            
            result = predictor.train_model(player_data[element]['X'], player_data[element]['y'])
            if result is not None:
                model, mae = result
                predictor.models[element] = {
                    'model': model,
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
        print("STEP 6: Generating test predictions for validation")
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


class FinalPredictionsGenerator:
    """Generate predictions for all players in all remaining fixtures."""
    
    def __init__(self, db: FPLDatabase, predictor: PointsPredictor):
        self.db = db
        self.predictor = predictor
    
    def get_latest_team_valuations(self):
        """Get latest team valuations."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT team, AVG(attack_value), AVG(defense_value)
                FROM team_fixture_valuations
                WHERE (season, gw) = (
                    SELECT season, MAX(gw) FROM team_fixture_valuations
                    GROUP BY season ORDER BY season DESC LIMIT 1
                )
                GROUP BY team
            """)
            return {row[0]: {'attack': row[1], 'defense': row[2]} for row in cursor}
    
    def create_table(self):
        """Create final predictions table."""
        with self.db.get_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS final_predictions")
            conn.execute("""
                CREATE TABLE final_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    player_name TEXT NOT NULL,
                    player_web_name TEXT NOT NULL,
                    element_type INTEGER NOT NULL,
                    element_type_name TEXT NOT NULL,
                    team_id INTEGER NOT NULL,
                    team_name TEXT NOT NULL,
                    fixture_id INTEGER NOT NULL,
                    gameweek INTEGER,
                    kickoff_time TEXT NOT NULL,
                    is_home BOOLEAN NOT NULL,
                    opponent_id INTEGER NOT NULL,
                    opponent_name TEXT NOT NULL,
                    own_team_attack REAL NOT NULL,
                    own_team_defense REAL NOT NULL,
                    opponent_attack REAL NOT NULL,
                    opponent_defense REAL NOT NULL,
                    predicted_points REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX idx_player_predictions ON final_predictions(player_id)")
            conn.execute("CREATE INDEX idx_fixture_predictions ON final_predictions(fixture_id)")
            conn.execute("CREATE INDEX idx_team_predictions ON final_predictions(team_id)")
            conn.commit()
    
    def run(self):
        """Generate predictions."""
        print(f"\n{'='*60}")
        print("STEP 5: Generating final predictions")
        print(f"{'='*60}")
        
        self.create_table()
        
        team_valuations = self.get_latest_team_valuations()
        print(f"  ✓ Loaded valuations for {len(team_valuations)} teams")
        
        # Get remaining fixtures
        with self.db.get_connection() as conn:
            fixtures = conn.execute("""
                SELECT f.id, f.event, f.kickoff_time, f.team_h, f.team_a,
                       th.name, ta.name
                FROM fixtures f
                JOIN teams th ON f.team_h = th.id
                JOIN teams ta ON f.team_a = ta.id
                WHERE f.finished = 0
                ORDER BY f.kickoff_time
            """).fetchall()
        
        # Get all players
        with self.db.get_connection() as conn:
            players = conn.execute("""
                SELECT id, first_name || ' ' || second_name, web_name,
                       element_type, element_type_name, team, team_name
                FROM elements
                ORDER BY id
            """).fetchall()
        
        print(f"  ✓ Found {len(fixtures)} fixtures, {len(players)} players")
        
        # Generate predictions
        predictions = []
        for player in players:
            player_id, name, web_name, elem_type, elem_type_name, team_id, team_name = player
            
            if team_name not in team_valuations:
                continue
            
            for fixture in fixtures:
                fix_id, gw, kickoff, home_id, away_id, home_name, away_name = fixture
                
                if home_id == team_id:
                    is_home, opp_id, opp_name = True, away_id, away_name
                elif away_id == team_id:
                    is_home, opp_id, opp_name = False, home_id, home_name
                else:
                    continue
                
                if opp_name not in team_valuations:
                    continue
                
                own_atk = team_valuations[team_name]['attack']
                own_def = team_valuations[team_name]['defense']
                opp_atk = team_valuations[opp_name]['attack']
                opp_def = team_valuations[opp_name]['defense']
                
                pred_pts = self.predictor.predict(player_id, own_atk, own_def, opp_atk, opp_def, is_home)
                
                predictions.append((
                    player_id, name, web_name, elem_type, elem_type_name,
                    team_id, team_name, fix_id, gw, kickoff, is_home,
                    opp_id, opp_name, own_atk, own_def, opp_atk, opp_def, pred_pts
                ))
        
        # Insert predictions
        with self.db.get_connection() as conn:
            conn.executemany("""
                INSERT INTO final_predictions (
                    player_id, player_name, player_web_name, element_type, element_type_name,
                    team_id, team_name, fixture_id, gameweek, kickoff_time, is_home,
                    opponent_id, opponent_name, own_team_attack, own_team_defense,
                    opponent_attack, opponent_defense, predicted_points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, predictions)
            conn.commit()
        
        print(f"  ✓ Generated {len(predictions)} predictions")
        return {'predictions': len(predictions)}


class FPLDataPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, db_path: str = "data/fpl_agent.db"):
        self.db_path = Path(db_path)
        self.db = None
        self.results = {}
    
    def setup_database(self):
        """Initialize database with API data."""
        print(f"\n{'='*60}")
        print("STEP 0: Setting up database")
        print(f"{'='*60}")
        
        from .api_client import FPLAPIClient
        
        api_client = FPLAPIClient()
        fpl_data = api_client.fetch_bootstrap_data()
        fixtures = api_client.fetch_fixtures()
        
        self.db = FPLDatabase(str(self.db_path))
        self.db_path.parent.mkdir(exist_ok=True)
        
        self.db.create_elements_table()
        self.db.create_teams_table()
        self.db.create_fixtures_table()
        
        elements = fpl_data.get('elements', [])
        teams = fpl_data.get('teams', [])
        
        self.db.insert_elements_data(elements, teams)
        self.db.insert_teams_data(teams)
        self.db.insert_fixtures_data(fixtures)
        self.db.update_current_team_with_latest_data()
        
        print(f"  ✓ Loaded {len(elements)} players, {len(teams)} teams, {len(fixtures)} fixtures")
        return {'players': len(elements), 'teams': len(teams), 'fixtures': len(fixtures)}
    
    def run(self, season: str = "2025-26", max_gameweeks: int = 38):
        """Run the complete pipeline."""
        start_time = datetime.now()
        print(f"\n{'#'*60}")
        print(f"# FPL DATA PIPELINE - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}")
        
        # Step 0: Setup database
        self.results['setup'] = self.setup_database()
        
        # Step 1: Load historic data
        loader = HistoricDataLoader(self.db, season)
        self.results['historic_data'] = loader.run(max_gameweeks)
        
        # Step 2: Calculate team valuations
        valuations = TeamValuationCalculator(self.db)
        self.results['valuations'] = valuations.run()
        
        # Step 3: Build player match context
        context_builder = PlayerMatchContextBuilder(self.db)
        self.results['context'] = context_builder.run()
        
        # Step 4: Train prediction models
        predictor = PointsPredictor(self.db)
        self.results['models'] = predictor.run()
        
        # Step 5: Generate final predictions
        predictions_gen = FinalPredictionsGenerator(self.db, predictor)
        self.results['predictions'] = predictions_gen.run()
        
        # Step 6: Generate test predictions for validation
        test_predictor = TestPredictionsGenerator(self.db)
        self.results['validation'] = test_predictor.run(season)
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print("PIPELINE COMPLETE")
        print(f"{'='*60}")
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Database: {self.db_path}")
        print(f"\n  Results:")
        for step, metrics in self.results.items():
            print(f"    {step}: {metrics}")
        print(f"{'='*60}\n")
        
        return self.results
