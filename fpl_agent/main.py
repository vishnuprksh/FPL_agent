#!/usr/bin/env python3
"""
FPL Agent - Load elements data from FPL API to SQLite database
"""

import json
import sqlite3
import urllib.request
from pathlib import Path
from typing import Dict, List


def fetch_fpl_data() -> Dict:
    """Fetch FPL bootstrap data from API."""
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        raise Exception(f"Failed to fetch FPL data: {e}")


def create_database(db_path: Path) -> None:
    """Create SQLite database and elements table."""
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
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
    conn.close()


def insert_elements_data(db_path: Path, elements: List[Dict], teams: List[Dict]) -> None:
    """Insert elements data into database."""
    conn = sqlite3.connect(db_path)
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
    
    # Helper function to safely convert values
    def safe_float(value):
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def safe_int(value):
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
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
        """, (
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
            safe_float(element['points_per_game']),
            safe_float(element['selected_by_percent']),
            safe_float(element['form']),
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
            safe_float(element['influence']),
            safe_float(element['creativity']),
            safe_float(element['threat']),
            safe_float(element['ict_index']),
            element['status'],
            element['transfers_in'],
            element['transfers_out'],
            element['transfers_in_event'],
            element['transfers_out_event'],
            safe_float(element['expected_goals']),
            safe_float(element['expected_assists']),
            safe_float(element['expected_goal_involvements']),
            safe_float(element['expected_goals_conceded']),
            element['can_select'],
            element['can_transact'],
            safe_int(element['chance_of_playing_next_round']),
            safe_int(element['chance_of_playing_this_round']),
            element['code'],
            element['cost_change_event'],
            element['cost_change_event_fall'],
            element['cost_change_start'],
            element['cost_change_start_fall'],
            element['dreamteam_count'],
            safe_float(element['ep_next']),
            safe_float(element['ep_this']),
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
            safe_int(element['squad_number']),
            safe_float(element['value_form']),
            safe_float(element['value_season']),
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
            safe_int(element['corners_and_indirect_freekicks_order']),
            element['corners_and_indirect_freekicks_text'],
            safe_int(element['direct_freekicks_order']),
            element['direct_freekicks_text'],
            safe_int(element['penalties_order']),
            element['penalties_text']
        ))
    
    conn.commit()
    conn.close()


def main():
    """Main function to load FPL elements data."""
    # Define database path
    db_path = Path("data/fpl_agent.db")
    
    print("Fetching FPL data...")
    fpl_data = fetch_fpl_data()
    
    print("Creating database...")
    create_database(db_path)
    
    print("Loading elements data...")
    elements = fpl_data.get('elements', [])
    teams = fpl_data.get('teams', [])
    insert_elements_data(db_path, elements, teams)
    
    print(f"Successfully loaded {len(elements)} players to {db_path}")


if __name__ == "__main__":
    main()
