"""
Database utilities for FPL data storage and retrieval.

Tables:
- elements: Player master data from FPL API
- teams: Team master data from FPL API
- fixtures: Fixture data from FPL API
- final_predictions: Weekly prediction data for all players by gameweek
- player_summary: Aggregated player data with summed predictions for next N weeks (main query table)
- current_team: User's saved team configuration
- player_gameweek_history: Historical gameweek performance data
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List


class FPLDatabase:
    """Database handler for FPL data."""
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def load_player_data(self, gameweek: int = None, num_weeks: int = 1) -> pd.DataFrame:
        """Load player data from player_summary table.
        
        Note: This method now reads from the player_summary table, which must be
        populated first using populate_player_summary(). If the table doesn't exist
        or num_weeks doesn't match, it will be auto-created/updated.
        
        Args:
            gameweek: Specific gameweek (unused, kept for compatibility)
            num_weeks: Number of weeks to sum predictions for (default: 1)
            
        Returns:
            DataFrame with player data and predicted points (summed over num_weeks)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if player_summary table exists and has correct num_weeks
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='player_summary'
            """)
            
            table_exists = cursor.fetchone() is not None
            needs_refresh = False
            
            if table_exists:
                # Check if num_weeks matches
                cursor.execute("""
                    SELECT DISTINCT num_weeks FROM player_summary LIMIT 1
                """)
                result = cursor.fetchone()
                if not result or result[0] != num_weeks:
                    needs_refresh = True
            else:
                needs_refresh = True
            
            # Create/refresh table if needed
            if needs_refresh:
                print(f"Refreshing player_summary table with {num_weeks} weeks of predictions...")
                self.create_player_summary_table()
                count = self.populate_player_summary(num_weeks)
                print(f"Populated player_summary with {count} players")
            
            # Read from player_summary table
            query = """
                SELECT 
                    player_id as id,
                    name,
                    position,
                    team,
                    price,
                    predicted_points
                FROM player_summary
                ORDER BY player_id
            """
            
            df = pd.read_sql_query(query, conn)
        
        return df
    
    def create_elements_table(self) -> None:
        """Create elements table with all API fields."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop existing table to recreate with all fields
            cursor.execute("DROP TABLE IF EXISTS elements")
            
            # Create elements table with all API fields
            cursor.execute("""
                CREATE TABLE elements (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    second_name TEXT,
                    web_name TEXT,
                    element_type INTEGER,
                    element_type_name TEXT,
                    team INTEGER,
                    team_name TEXT,
                    team_code INTEGER,
                    now_cost INTEGER,
                    total_points INTEGER,
                    points_per_game REAL,
                    selected_by_percent REAL,
                    form REAL,
                    minutes INTEGER,
                    goals_scored INTEGER,
                    assists INTEGER,
                    clean_sheets INTEGER,
                    goals_conceded INTEGER,
                    yellow_cards INTEGER,
                    red_cards INTEGER,
                    saves INTEGER,
                    bonus INTEGER,
                    bps INTEGER,
                    influence REAL,
                    creativity REAL,
                    threat REAL,
                    ict_index REAL,
                    status TEXT,
                    transfers_in INTEGER,
                    transfers_out INTEGER,
                    transfers_in_event INTEGER,
                    transfers_out_event INTEGER,
                    expected_goals REAL,
                    expected_assists REAL,
                    expected_goal_involvements REAL,
                    expected_goals_conceded REAL,
                    can_select BOOLEAN,
                    can_transact BOOLEAN,
                    chance_of_playing_next_round INTEGER,
                    chance_of_playing_this_round INTEGER,
                    code INTEGER,
                    cost_change_event INTEGER,
                    cost_change_event_fall INTEGER,
                    cost_change_start INTEGER,
                    cost_change_start_fall INTEGER,
                    dreamteam_count INTEGER,
                    ep_next REAL,
                    ep_this REAL,
                    event_points INTEGER,
                    in_dreamteam BOOLEAN,
                    news TEXT,
                    news_added TEXT,
                    own_goals INTEGER,
                    penalties_missed INTEGER,
                    penalties_saved INTEGER,
                    photo TEXT,
                    removed BOOLEAN,
                    special BOOLEAN,
                    squad_number INTEGER,
                    value_form REAL,
                    value_season REAL,
                    birth_date TEXT,
                    has_temporary_code BOOLEAN,
                    opta_code TEXT,
                    region INTEGER,
                    team_join_date TEXT,
                    clean_sheets_per_90 REAL,
                    saves_per_90 REAL,
                    goals_conceded_per_90 REAL,
                    expected_goals_per_90 REAL,
                    expected_assists_per_90 REAL,
                    expected_goal_involvements_per_90 REAL,
                    expected_goals_conceded_per_90 REAL,
                    defensive_contribution INTEGER,
                    defensive_contribution_per_90 REAL,
                    clearances_blocks_interceptions INTEGER,
                    recoveries INTEGER,
                    tackles INTEGER,
                    starts INTEGER,
                    starts_per_90 REAL,
                    creativity_rank INTEGER,
                    creativity_rank_type INTEGER,
                    form_rank INTEGER,
                    form_rank_type INTEGER,
                    ict_index_rank INTEGER,
                    ict_index_rank_type INTEGER,
                    influence_rank INTEGER,
                    influence_rank_type INTEGER,
                    now_cost_rank INTEGER,
                    now_cost_rank_type INTEGER,
                    points_per_game_rank INTEGER,
                    points_per_game_rank_type INTEGER,
                    selected_rank INTEGER,
                    selected_rank_type INTEGER,
                    threat_rank INTEGER,
                    threat_rank_type INTEGER,
                    corners_and_indirect_freekicks_order INTEGER,
                    corners_and_indirect_freekicks_text TEXT,
                    direct_freekicks_order INTEGER,
                    direct_freekicks_text TEXT,
                    penalties_order INTEGER,
                    penalties_text TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def insert_elements_data(self, elements: List[Dict], teams: List[Dict]) -> None:
        """Insert elements data into database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM elements")
            
            # Element type mapping
            element_type_map = {
                1: "GK",  # Goalkeeper
                2: "DEF",  # Defender
                3: "MID",  # Midfielder
                4: "FWD"   # Forward
            }
            
            # Team mapping
            team_map = {team['id']: team['name'] for team in teams}
            
            # Insert new data
            for element in elements:
                cursor.execute("""
                    INSERT INTO elements (
                        id, first_name, second_name, web_name, element_type, element_type_name, team, team_name, team_code,
                        now_cost, total_points, points_per_game, selected_by_percent, form,
                        minutes, goals_scored, assists, clean_sheets, goals_conceded,
                        yellow_cards, red_cards, saves, bonus, bps, influence, creativity,
                        threat, ict_index, status, transfers_in, transfers_out,
                        transfers_in_event, transfers_out_event, expected_goals, expected_assists,
                        expected_goal_involvements, expected_goals_conceded, can_select, can_transact,
                        chance_of_playing_next_round, chance_of_playing_this_round, code,
                        cost_change_event, cost_change_event_fall, cost_change_start,
                        cost_change_start_fall, dreamteam_count, ep_next, ep_this, event_points,
                        in_dreamteam, news, news_added, own_goals, penalties_missed,
                        penalties_saved, photo, removed, special, squad_number, value_form,
                        value_season, birth_date, has_temporary_code, opta_code, region,
                        team_join_date, clean_sheets_per_90, saves_per_90, goals_conceded_per_90,
                        expected_goals_per_90, expected_assists_per_90, expected_goal_involvements_per_90,
                        expected_goals_conceded_per_90, defensive_contribution, defensive_contribution_per_90,
                        clearances_blocks_interceptions, recoveries, tackles, starts, starts_per_90,
                        creativity_rank, creativity_rank_type, form_rank, form_rank_type,
                        ict_index_rank, ict_index_rank_type, influence_rank, influence_rank_type,
                        now_cost_rank, now_cost_rank_type, points_per_game_rank, points_per_game_rank_type,
                        selected_rank, selected_rank_type, threat_rank, threat_rank_type,
                        corners_and_indirect_freekicks_order, corners_and_indirect_freekicks_text,
                        direct_freekicks_order, direct_freekicks_text, penalties_order, penalties_text
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, self._extract_element_data(element, element_type_map, team_map))
            
            conn.commit()
    
    def _extract_element_data(self, element: Dict, element_type_map: Dict, team_map: Dict) -> tuple:
        """Extract and format element data for database insertion."""
        return (
            element['id'],
            element['first_name'],
            element['second_name'],
            element['web_name'],
            element['element_type'],
            element_type_map.get(element['element_type'], 'UNK'),
            element['team'],
            team_map.get(element['team'], 'Unknown'),
            element['team_code'],
            element['now_cost'],
            element['total_points'],
            self._safe_float(element['points_per_game']),
            self._safe_float(element['selected_by_percent']),
            self._safe_float(element['form']),
            element['minutes'],
            element['goals_scored'],
            element['assists'],
            element['clean_sheets'],
            element['goals_conceded'],
            element['yellow_cards'],
            element['red_cards'],
            element['saves'],
            element['bonus'],
            element['bps'],
            self._safe_float(element['influence']),
            self._safe_float(element['creativity']),
            self._safe_float(element['threat']),
            self._safe_float(element['ict_index']),
            element['status'],
            element['transfers_in'],
            element['transfers_out'],
            element['transfers_in_event'],
            element['transfers_out_event'],
            self._safe_float(element['expected_goals']),
            self._safe_float(element['expected_assists']),
            self._safe_float(element['expected_goal_involvements']),
            self._safe_float(element['expected_goals_conceded']),
            element['can_select'],
            element['can_transact'],
            self._safe_int(element['chance_of_playing_next_round']),
            self._safe_int(element['chance_of_playing_this_round']),
            element['code'],
            element['cost_change_event'],
            element['cost_change_event_fall'],
            element['cost_change_start'],
            element['cost_change_start_fall'],
            element['dreamteam_count'],
            self._safe_float(element['ep_next']),
            self._safe_float(element['ep_this']),
            element['event_points'],
            element['in_dreamteam'],
            element['news'],
            element['news_added'],
            element['own_goals'],
            element['penalties_missed'],
            element['penalties_saved'],
            element['photo'],
            element['removed'],
            element['special'],
            self._safe_int(element['squad_number']),
            self._safe_float(element['value_form']),
            self._safe_float(element['value_season']),
            element['birth_date'],
            element['has_temporary_code'],
            element['opta_code'],
            element['region'],
            element['team_join_date'],
            element['clean_sheets_per_90'],
            element['saves_per_90'],
            element['goals_conceded_per_90'],
            element['expected_goals_per_90'],
            element['expected_assists_per_90'],
            element['expected_goal_involvements_per_90'],
            element['expected_goals_conceded_per_90'],
            element['defensive_contribution'],
            element['defensive_contribution_per_90'],
            element['clearances_blocks_interceptions'],
            element['recoveries'],
            element['tackles'],
            element['starts'],
            element['starts_per_90'],
            element['creativity_rank'],
            element['creativity_rank_type'],
            element['form_rank'],
            element['form_rank_type'],
            element['ict_index_rank'],
            element['ict_index_rank_type'],
            element['influence_rank'],
            element['influence_rank_type'],
            element['now_cost_rank'],
            element['now_cost_rank_type'],
            element['points_per_game_rank'],
            element['points_per_game_rank_type'],
            element['selected_rank'],
            element['selected_rank_type'],
            element['threat_rank'],
            element['threat_rank_type'],
            self._safe_int(element['corners_and_indirect_freekicks_order']),
            element['corners_and_indirect_freekicks_text'],
            self._safe_int(element['direct_freekicks_order']),
            element['direct_freekicks_text'],
            self._safe_int(element['penalties_order']),
            element['penalties_text']
        )
    
    @staticmethod
    def _safe_float(value):
        """Safely convert value to float."""
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def _safe_int(value):
        """Safely convert value to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def update_current_team_with_latest_data(self) -> None:
        """Update current_team table with latest price and predicted points from final_predictions table."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if current_team table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='current_team'
            """)
            if cursor.fetchone() is None:
                # Table doesn't exist - skip update
                return
            
            # Check if final_predictions table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='final_predictions'
            """)
            has_predictions = cursor.fetchone() is not None
            
            if not has_predictions:
                # Table doesn't exist yet - use ep_this fallback
                cursor.execute("""
                    UPDATE current_team 
                    SET 
                        price = (SELECT now_cost / 10.0 FROM elements WHERE elements.id = current_team.player_id),
                        predicted_points = (SELECT ep_this FROM elements WHERE elements.id = current_team.player_id)
                    WHERE player_id IN (SELECT id FROM elements)
                """)
            else:
                # Get the next upcoming gameweek
                cursor.execute("""
                    SELECT MIN(gameweek) 
                    FROM final_predictions
                    WHERE gameweek >= (
                        SELECT COALESCE(MAX(event), 1) FROM fixtures WHERE finished = 1
                    ) + 1
                """)
                next_gw = cursor.fetchone()[0]
                
                if next_gw is None:
                    # Fallback to ep_this if no predictions available
                    cursor.execute("""
                        UPDATE current_team 
                        SET 
                            price = (SELECT now_cost / 10.0 FROM elements WHERE elements.id = current_team.player_id),
                            predicted_points = (SELECT ep_this FROM elements WHERE elements.id = current_team.player_id)
                        WHERE player_id IN (SELECT id FROM elements)
                    """)
                else:
                    # Update price and predicted_points for existing current_team players
                    cursor.execute("""
                        UPDATE current_team 
                        SET 
                            price = (SELECT now_cost / 10.0 FROM elements WHERE elements.id = current_team.player_id),
                            predicted_points = (
                                SELECT predicted_points 
                                FROM final_predictions 
                                WHERE final_predictions.player_id = current_team.player_id 
                                AND final_predictions.gameweek = ?
                                LIMIT 1
                            )
                        WHERE player_id IN (SELECT id FROM elements)
                    """, (next_gw,))
            
            # Recalculate and update team_cost and team_points for all records
            cursor.execute("""
                UPDATE current_team 
                SET 
                    team_cost = (SELECT SUM(price) FROM current_team),
                    team_points = (SELECT SUM(predicted_points) FROM current_team WHERE is_starter = 1)
            """)
            
            conn.commit()
    
    def create_teams_table(self) -> None:
        """Create teams table with all fields from teams.csv."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop existing table to recreate with all fields
            cursor.execute("DROP TABLE IF EXISTS teams")
            
            # Create teams table with all fields from teams.csv
            cursor.execute("""
                CREATE TABLE teams (
                    id INTEGER PRIMARY KEY,
                    code INTEGER,
                    draw INTEGER,
                    form TEXT,
                    loss INTEGER,
                    name TEXT,
                    played INTEGER,
                    points INTEGER,
                    position INTEGER,
                    short_name TEXT,
                    strength INTEGER,
                    team_division TEXT,
                    unavailable BOOLEAN,
                    win INTEGER,
                    strength_overall_home INTEGER,
                    strength_overall_away INTEGER,
                    strength_attack_home INTEGER,
                    strength_attack_away INTEGER,
                    strength_defence_home INTEGER,
                    strength_defence_away INTEGER,
                    pulse_id INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def insert_teams_data(self, teams: List[Dict]) -> None:
        """Insert teams data into database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM teams")
            
            # Insert new data
            for team in teams:
                cursor.execute("""
                    INSERT INTO teams (
                        id, code, draw, form, loss, name, played, points, position,
                        short_name, strength, team_division, unavailable, win,
                        strength_overall_home, strength_overall_away,
                        strength_attack_home, strength_attack_away,
                        strength_defence_home, strength_defence_away, pulse_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    team['id'],
                    team['code'],
                    team['draw'],
                    team.get('form', ''),
                    team['loss'],
                    team['name'],
                    team['played'],
                    team['points'],
                    team['position'],
                    team['short_name'],
                    team['strength'],
                    team.get('team_division', ''),
                    team['unavailable'],
                    team['win'],
                    team['strength_overall_home'],
                    team['strength_overall_away'],
                    team['strength_attack_home'],
                    team['strength_attack_away'],
                    team['strength_defence_home'],
                    team['strength_defence_away'],
                    team['pulse_id']
                ))
            
            conn.commit()
    
    def create_fixtures_table(self) -> None:
        """Create fixtures table with all fields from fixtures.csv."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop existing table to recreate with all fields
            cursor.execute("DROP TABLE IF EXISTS fixtures")
            
            # Create fixtures table with all fields from fixtures.csv
            cursor.execute("""
                CREATE TABLE fixtures (
                    id INTEGER PRIMARY KEY,
                    code INTEGER,
                    event INTEGER,
                    finished BOOLEAN,
                    finished_provisional BOOLEAN,
                    kickoff_time TEXT,
                    minutes INTEGER,
                    provisional_start_time BOOLEAN,
                    started BOOLEAN,
                    team_a INTEGER,
                    team_a_score INTEGER,
                    team_h INTEGER,
                    team_h_score INTEGER,
                    stats TEXT,
                    team_h_difficulty INTEGER,
                    team_a_difficulty INTEGER,
                    pulse_id INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (team_a) REFERENCES teams(id),
                    FOREIGN KEY (team_h) REFERENCES teams(id)
                )
            """)
            
            conn.commit()
    
    def insert_fixtures_data(self, fixtures: List[Dict]) -> None:
        """Insert fixtures data into database."""
        import json
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM fixtures")
            
            # Insert new data
            for fixture in fixtures:
                cursor.execute("""
                    INSERT INTO fixtures (
                        id, code, event, finished, finished_provisional,
                        kickoff_time, minutes, provisional_start_time, started,
                        team_a, team_a_score, team_h, team_h_score, stats,
                        team_h_difficulty, team_a_difficulty, pulse_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fixture['id'],
                    fixture['code'],
                    fixture['event'],
                    fixture['finished'],
                    fixture['finished_provisional'],
                    fixture['kickoff_time'],
                    fixture['minutes'],
                    fixture['provisional_start_time'],
                    fixture['started'],
                    fixture['team_a'],
                    fixture.get('team_a_score'),
                    fixture['team_h'],
                    fixture.get('team_h_score'),
                    json.dumps(fixture.get('stats', [])),  # Store stats as JSON string
                    fixture['team_h_difficulty'],
                    fixture['team_a_difficulty'],
                    fixture['pulse_id']
                ))
            
            conn.commit()
    
    def create_player_gameweek_history_table(self) -> None:
        """Create table for storing historic gameweek data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_gameweek_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    season TEXT NOT NULL,
                    gw INTEGER NOT NULL,
                    element INTEGER NOT NULL,
                    name TEXT,
                    position TEXT,
                    team TEXT,
                    xP REAL,
                    assists INTEGER,
                    bonus INTEGER,
                    bps INTEGER,
                    clean_sheets INTEGER,
                    clearances_blocks_interceptions INTEGER,
                    creativity REAL,
                    defensive_contribution INTEGER,
                    expected_assists REAL,
                    expected_goal_involvements REAL,
                    expected_goals REAL,
                    expected_goals_conceded REAL,
                    fixture INTEGER,
                    goals_conceded INTEGER,
                    goals_scored INTEGER,
                    ict_index REAL,
                    influence REAL,
                    kickoff_time TEXT,
                    minutes INTEGER,
                    modified BOOLEAN,
                    opponent_team INTEGER,
                    own_goals INTEGER,
                    penalties_missed INTEGER,
                    penalties_saved INTEGER,
                    recoveries INTEGER,
                    red_cards INTEGER,
                    round INTEGER,
                    saves INTEGER,
                    selected INTEGER,
                    starts INTEGER,
                    tackles INTEGER,
                    team_a_score INTEGER,
                    team_h_score INTEGER,
                    threat REAL,
                    total_points INTEGER,
                    transfers_balance INTEGER,
                    transfers_in INTEGER,
                    transfers_out INTEGER,
                    value REAL,
                    was_home BOOLEAN,
                    yellow_cards INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(season, gw, element, fixture)
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_player_gw 
                ON player_gameweek_history(element, season, gw)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_season_gw 
                ON player_gameweek_history(season, gw)
            """)
            
            conn.commit()
    
    def insert_gameweek_data(self, season: str, gw: int, df: pd.DataFrame) -> int:
        """Insert gameweek data from DataFrame into database.
        
        Args:
            season: Season identifier (e.g., '2025-26')
            gw: Gameweek number
            df: DataFrame containing gameweek data
            
        Returns:
            Number of rows inserted
        """
        # Add season and gw columns
        df['season'] = season
        df['gw'] = gw
        
        with self.get_connection() as conn:
            # Insert data, replacing duplicates
            df.to_sql(
                'player_gameweek_history', 
                conn, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            
            # Get count of records for this season/gw
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM player_gameweek_history 
                WHERE season = ? AND gw = ?
            """, (season, gw))
            count = cursor.fetchone()[0]
            
            return count
    
    def get_player_gameweek_history(self, element_id: int, season: str = None) -> pd.DataFrame:
        """Get gameweek history for a specific player.
        
        Args:
            element_id: Player ID
            season: Optional season filter
            
        Returns:
            DataFrame with player's gameweek history
        """
        query = """
            SELECT * FROM player_gameweek_history
            WHERE element = ?
        """
        params = [element_id]
        
        if season:
            query += " AND season = ?"
            params.append(season)
        
        query += " ORDER BY season, gw"
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def load_top_performers_for_weeks(self, num_weeks: int = 3) -> pd.DataFrame:
        """Load top performers for the next N weeks from player_summary table.
        
        Note: Requires player_summary table to be populated with the correct num_weeks.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if player_summary exists and has correct num_weeks
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='player_summary'
            """)
            
            table_exists = cursor.fetchone() is not None
            needs_refresh = False
            
            if table_exists:
                cursor.execute("""
                    SELECT DISTINCT num_weeks FROM player_summary LIMIT 1
                """)
                result = cursor.fetchone()
                if not result or result[0] != num_weeks:
                    needs_refresh = True
            else:
                needs_refresh = True
            
            # Create/refresh table if needed
            if needs_refresh:
                print(f"Refreshing player_summary table with {num_weeks} weeks of predictions...")
                self.create_player_summary_table()
                count = self.populate_player_summary(num_weeks)
                print(f"Populated player_summary with {count} players")
            
            # Query from player_summary
            query = """
                SELECT 
                    name,
                    position,
                    team_name as team,
                    predicted_points
                FROM player_summary
                ORDER BY predicted_points DESC
            """
            
            df = pd.read_sql_query(query, conn)
        
        return df
    
    def create_player_summary_table(self) -> None:
        """Create player_summary table for quick access to player data with summed predictions."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop existing table to recreate
            cursor.execute("DROP TABLE IF EXISTS player_summary")
            
            # Create player_summary table
            cursor.execute("""
                CREATE TABLE player_summary (
                    player_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    position TEXT NOT NULL,
                    team INTEGER NOT NULL,
                    team_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    predicted_points REAL NOT NULL,
                    num_weeks INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (team) REFERENCES teams(id)
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_player_summary_position 
                ON player_summary(position)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_player_summary_team 
                ON player_summary(team)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_player_summary_predicted_points 
                ON player_summary(predicted_points DESC)
            """)
            
            conn.commit()
    
    def populate_player_summary(self, num_weeks: int = 3) -> int:
        """Populate player_summary table with summed predictions for next N weeks.
        
        Args:
            num_weeks: Number of weeks to sum predictions for (default: 3)
            
        Returns:
            Number of players inserted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM player_summary")
            
            # Insert aggregated player data
            cursor.execute("""
                INSERT INTO player_summary (
                    player_id, name, position, team, team_name, price, 
                    predicted_points, num_weeks
                )
                WITH next_gameweeks AS (
                    SELECT DISTINCT gameweek
                    FROM final_predictions
                    WHERE gameweek >= (
                        SELECT COALESCE(MAX(event), 1) + 1 FROM fixtures WHERE finished = 1
                    )
                    ORDER BY gameweek
                    LIMIT ?
                )
                SELECT 
                    e.id as player_id,
                    e.web_name as name,
                    e.element_type_name as position,
                    e.team,
                    t.name as team_name,
                    e.now_cost / 10.0 as price,
                    COALESCE(SUM(fp.predicted_points), 0.0) as predicted_points,
                    ? as num_weeks
                FROM elements e
                JOIN teams t ON e.team = t.id
                LEFT JOIN final_predictions fp 
                    ON e.id = fp.player_id 
                    AND fp.gameweek IN (SELECT gameweek FROM next_gameweeks)
                WHERE e.can_select = 1 
                AND e.now_cost > 0
                GROUP BY e.id, e.web_name, e.element_type_name, e.team, t.name, e.now_cost
                ORDER BY e.id
            """, (num_weeks, num_weeks))
            
            count = cursor.rowcount
            conn.commit()
            
            return count