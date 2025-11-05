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
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
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
        """Calculate team attack/defense scores based on rolling average points."""
        print(f"\n{'='*60}")
        print("STEP 2: Calculating team valuations")
        print(f"{'='*60}")
        
        self.create_table()
        
        # Get all gameweek data ordered by player and gameweek
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT season, gw, fixture, team, element, position, total_points, starts
                FROM player_gameweek_history
                ORDER BY season, element, gw
            """)
            all_data = cursor.fetchall()
        
        # Calculate rolling average for each player
        player_rolling_avg = {}  # {(season, element): [points history]}
        team_scores = []
        
        for row in all_data:
            season, gw, fixture, team, element, position, total_points, starts = row
            
            # Skip if didn't start
            if starts != 1:
                continue
            
            # Initialize player history if needed
            key = (season, element)
            if key not in player_rolling_avg:
                player_rolling_avg[key] = []
            
            # Calculate rolling average (mean of all previous points including current)
            player_rolling_avg[key].append(total_points)
            avg_points = sum(player_rolling_avg[key]) / len(player_rolling_avg[key])
            
            # Store for aggregation
            team_scores.append((season, gw, fixture, team, position, avg_points))
        
        # Aggregate by team/fixture for attack and defense
        team_fixture_scores = {}
        for season, gw, fixture, team, position, avg_points in team_scores:
            key = (season, gw, fixture, team)
            if key not in team_fixture_scores:
                team_fixture_scores[key] = {'attack': [], 'defense': []}
            
            if position in ('MID', 'FWD'):
                team_fixture_scores[key]['attack'].append(avg_points)
            elif position in ('GK', 'DEF'):
                team_fixture_scores[key]['defense'].append(avg_points)
        
        # Insert into database
        valuations = []
        for (season, gw, fixture, team), scores in team_fixture_scores.items():
            attack_score = sum(scores['attack']) if scores['attack'] else 0.0
            defense_score = sum(scores['defense']) if scores['defense'] else 0.0
            valuations.append((season, gw, fixture, team, defense_score, attack_score))
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM team_fixture_valuations")
            cursor.executemany("""
                INSERT INTO team_fixture_valuations 
                (season, gw, fixture, team, defense_value, attack_value)
                VALUES (?, ?, ?, ?, ?, ?)
            """, valuations)
            conn.commit()
        
        print(f"  ✓ Calculated valuations for {len(valuations)} team-fixtures")
        return {'valuations': len(valuations)}


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
    """Train ML models to predict player points using two-level hierarchy.
    
    Level 1: Position-specific models (FWD, MID, DEF, GK) - baseline for all players
    Level 2: Player-specific models - individual skill adjustments
    
    Final prediction = weighted blend of both levels (if both available)
    """
    
    def __init__(self, db: FPLDatabase, model_path: str = "models/player_points_predictors.pkl", 
                 player_weight: float = 0.7):
        self.db = db
        self.model_path = Path(model_path)
        self.models = {}  # Player-specific models
        self.position_models = {}  # Position-level models (fallback)
        self.player_weight = player_weight  # Weight for player model (0.7 means 70% player, 30% position)
        self._load_models()
    
    def _load_models(self):
        """Load existing models if they exist."""
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                saved_data = pickle.load(f)
                
                # Handle new format (dict with 'players' and 'positions')
                if isinstance(saved_data, dict) and 'players' in saved_data:
                    self.models = saved_data.get('players', {})
                    self.position_models = saved_data.get('positions', {})
                else:
                    # Old format - just player models
                    self.models = saved_data
                    self.position_models = {}
    
    def load_training_data(self):
        """Load player match context data grouped by player and position with differential features."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pmc.element, pmc.name, pmc.team_attack_value, pmc.team_defense_value,
                       pmc.opponent_attack_value, pmc.opponent_defense_value, pmc.was_home, 
                       pmc.total_points, e.element_type_name
                FROM player_match_context pmc
                JOIN elements e ON pmc.element = e.id
                WHERE pmc.team_attack_value IS NOT NULL AND pmc.team_defense_value IS NOT NULL
                  AND pmc.opponent_attack_value IS NOT NULL AND pmc.opponent_defense_value IS NOT NULL
                  AND pmc.was_home IS NOT NULL AND pmc.total_points IS NOT NULL
                  AND e.element_type_name IS NOT NULL
            """)
            data = cursor.fetchall()
        
        if not data:
            raise ValueError("No training data found")
        
        # Group by player and position with differential features
        player_data = {}
        position_data = {}
        
        for row in data:
            element = row[0]
            team_attack = row[2]
            team_defense = row[3]
            opp_attack = row[4]
            opp_defense = row[5]
            was_home = row[6]
            total_points = row[7]
            position = row[8]  # element_type_name (FWD, MID, DEF, GK)
            
            # Calculate differential features
            attack_advantage = team_attack - opp_defense  # Our attack vs their defense
            defense_advantage = team_defense - opp_attack  # Our defense vs their attack
            
            # Group by player
            if element not in player_data:
                player_data[element] = {'name': row[1], 'position': position, 'X': [], 'y': []}
            
            # Features: [attack_advantage, defense_advantage, was_home]
            player_data[element]['X'].append([attack_advantage, defense_advantage, was_home])
            player_data[element]['y'].append(total_points)
            
            # Group by position for position-level models
            if position not in position_data:
                position_data[position] = {'X': [], 'y': []}
            position_data[position]['X'].append([attack_advantage, defense_advantage, was_home])
            position_data[position]['y'].append(total_points)
        
        # Convert to numpy arrays
        for element in player_data:
            player_data[element]['X'] = np.array(player_data[element]['X'])
            player_data[element]['y'] = np.array(player_data[element]['y'])
        
        for position in position_data:
            position_data[position]['X'] = np.array(position_data[position]['X'])
            position_data[position]['y'] = np.array(position_data[position]['y'])
        
        return player_data, position_data
    
    def train_model(self, X, y, min_samples=5):
        """Train Linear Regression model with feature scaling for a player."""
        if len(X) < min_samples:
            return None
        
        # Create and fit scaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train linear regression model
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        # Calculate MAE on training data
        y_pred = model.predict(X_scaled)
        mae = mean_absolute_error(y, y_pred)
        
        return {'model': model, 'scaler': scaler}, mae
    
    def train_position_model(self, X, y, min_samples=20):
        """Train position-level model with more samples required."""
        if len(X) < min_samples:
            return None
        
        # Create and fit scaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train linear regression model
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        # Calculate MAE on training data
        y_pred = model.predict(X_scaled)
        mae = mean_absolute_error(y, y_pred)
        
        return {'model': model, 'scaler': scaler}, mae
    
    def run(self):
        """Train models for all players using hierarchical approach."""
        print(f"\n{'='*60}")
        print("STEP 4: Training hierarchical prediction models")
        print(f"{'='*60}")
        
        player_data, position_data = self.load_training_data()
        print(f"  ✓ Loaded data for {len(player_data)} players across {len(position_data)} positions")
        
        # First, train position-level models (Level 1)
        print(f"\n  Training Level 1: Position-specific models...")
        position_trained = 0
        for position, data in position_data.items():
            result = self.train_position_model(data['X'], data['y'])
            if result is None:
                print(f"    ⚠ Skipped {position} (insufficient samples: {len(data['X'])})")
                continue
            
            model_dict, mae = result
            self.position_models[position] = {
                'model': model_dict['model'],
                'scaler': model_dict['scaler'],
                'samples': len(data['X']),
                'mae': mae
            }
            print(f"    ✓ {position}: {len(data['X'])} samples, MAE={mae:.2f}")
            position_trained += 1
        
        print(f"  ✓ Trained {position_trained} position models")
        
        # Then, train player-specific models (Level 2)
        print(f"\n  Training Level 2: Player-specific models...")
        player_trained = 0
        player_skipped = 0
        
        for element, data in player_data.items():
            result = self.train_model(data['X'], data['y'])
            if result is None:
                player_skipped += 1
                continue
            
            model_dict, mae = result
            self.models[element] = {
                'model': model_dict['model'],
                'scaler': model_dict['scaler'],
                'name': data['name'],
                'position': data['position'],
                'samples': len(data['X']),
                'mae': mae
            }
            player_trained += 1
        
        # Save both models
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({'players': self.models, 'positions': self.position_models}, f)
        
        print(f"  ✓ Trained {player_trained} player models (skipped {player_skipped})")
        print(f"  ✓ Saved to {self.model_path}")
        return {
            'position_models': position_trained,
            'player_models': player_trained,
            'player_skipped': player_skipped
        }
    
    def predict(self, player_id, team_attack, team_defense, opp_attack, opp_defense, is_home):
        """Predict points using weighted blend of position and player models.
        
        Strategy:
        - If both models available: blend them (e.g., 70% player + 30% position)
        - If only player model: use it (rare case - new position without baseline)
        - If only position model: use it (new player without history)
        - If neither: return 0
        """
        # Calculate differential features (same as training)
        attack_advantage = team_attack - opp_defense
        defense_advantage = team_defense - opp_attack
        features = np.array([[attack_advantage, defense_advantage, is_home]])
        
        # Get player's position from database
        position = None
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT element_type_name FROM elements WHERE id = ?", 
                (player_id,)
            )
            row = cursor.fetchone()
            if row:
                position = row[0]
        
        # Get predictions from both levels
        player_prediction = None
        position_prediction = None
        
        # Level 2: Player-specific model
        if player_id in self.models:
            features_scaled = self.models[player_id]['scaler'].transform(features)
            player_prediction = self.models[player_id]['model'].predict(features_scaled)[0]
        
        # Level 1: Position-level model
        if position and position in self.position_models:
            features_scaled = self.position_models[position]['scaler'].transform(features)
            position_prediction = self.position_models[position]['model'].predict(features_scaled)[0]
        
        # Combine predictions based on availability
        if player_prediction is not None and position_prediction is not None:
            # Both available - weighted blend
            # Example: Haaland's 15 points + FWD baseline 8 points = 70%*15 + 30%*8 = 12.9
            blended = (self.player_weight * player_prediction + 
                      (1 - self.player_weight) * position_prediction)
            return np.clip(blended, 0, 15)
        elif player_prediction is not None:
            # Only player model available
            return np.clip(player_prediction, 0, 15)
        elif position_prediction is not None:
            # Only position model available (new player)
            return np.clip(position_prediction, 0, 15)
        else:
            # No model available
            return 0.0


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
