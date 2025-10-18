#!/usr/bin/env python3
"""
FPL Transfer Optimizer

Suggests the best single transfer to maximize points for the current gameweek.
Takes a current team and evaluates all possible single transfers.
"""

import sqlite3
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json


class FPLTransferOptimizer:
    """Optimizer for suggesting single player transfers in FPL."""
    
    def __init__(self, db_path: str):
        """
        Initialize the transfer optimizer.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.players_df = None
        
    def load_player_data(self) -> pd.DataFrame:
        """Load player data from the SQLite database."""
        query = """
        SELECT 
            id,
            web_name as name,
            element_type_name as position,
            team,
            now_cost / 10.0 as price,  -- Convert from tenths to millions
            ep_this as predicted_points
        FROM elements 
        WHERE can_select = 1 
        AND ep_this IS NOT NULL 
        AND now_cost > 0
        ORDER BY id
        """
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn)
        
        # Handle any missing predicted points
        df['predicted_points'] = df['predicted_points'].fillna(0.0)
        
        return df
    
    def parse_current_team(self, team_json: Dict) -> pd.DataFrame:
        """Parse current team from JSON format into DataFrame."""
        current_players = []
        
        for position_data in team_json['team']:
            position = position_data['position']
            for player in position_data['players']:
                current_players.append({
                    'id': player['id'],
                    'name': player['name'], 
                    'position': position,
                    'team': player['team'],
                    'is_starter': player.get('is_starter', True)
                })
        
        current_team_df = pd.DataFrame(current_players)
        
        # Get price and predicted_points from database for current team players
        if not current_team_df.empty:
            # Load database to validate against
            database_df = self.load_player_data()
            
            # Check for player IDs that don't exist in database
            missing_ids = set(current_team_df['id']) - set(database_df['id'])
            if missing_ids:
                raise ValueError(f"Player IDs not found in database: {sorted(list(missing_ids))}")
            
            # Merge with database to get missing fields
            merged_df = current_team_df.merge(
                database_df[['id', 'name', 'position', 'team', 'price', 'predicted_points']], 
                on='id', 
                how='left',
                suffixes=('_input', '_db')
            )
            
            # Check for mismatched data between input and database
            mismatches = []
            
            # Check name mismatches
            name_mismatches = merged_df[merged_df['name_input'] != merged_df['name_db']]
            if not name_mismatches.empty:
                for _, row in name_mismatches.iterrows():
                    mismatches.append(f"Player ID {row['id']}: name mismatch - input: '{row['name_input']}', database: '{row['name_db']}'")
            
            # Check position mismatches
            position_mismatches = merged_df[merged_df['position_input'] != merged_df['position_db']]
            if not position_mismatches.empty:
                for _, row in position_mismatches.iterrows():
                    mismatches.append(f"Player ID {row['id']}: position mismatch - input: '{row['position_input']}', database: '{row['position_db']}'")
            
            # Check team mismatches
            team_mismatches = merged_df[merged_df['team_input'] != merged_df['team_db']]
            if not team_mismatches.empty:
                for _, row in team_mismatches.iterrows():
                    mismatches.append(f"Player ID {row['id']}: team mismatch - input: {row['team_input']}, database: {row['team_db']}")
            
            if mismatches:
                raise ValueError(f"Data mismatches found between input team and database:\n" + "\n".join(mismatches))
            
            # Use database values (more reliable)
            current_team_df = merged_df[['id', 'name_db', 'position_db', 'team_db', 'is_starter', 'price', 'predicted_points']].copy()
            current_team_df.rename(columns={
                'name_db': 'name',
                'position_db': 'position', 
                'team_db': 'team'
            }, inplace=True)
            
            # Check for any remaining missing values
            missing_price = current_team_df['price'].isna().sum()
            missing_points = current_team_df['predicted_points'].isna().sum()
            
            if missing_price > 0 or missing_points > 0:
                raise ValueError(f"Missing data in database - Price: {missing_price} players, Predicted points: {missing_points} players")
        
        return current_team_df
    
    def validate_team_constraints(self, team_df: pd.DataFrame) -> bool:
        """Validate that the team meets FPL constraints."""
        # Check squad size
        if len(team_df) != 15:
            print(f"Invalid squad size: {len(team_df)} (should be 15)")
            return False
        
        # Check position requirements
        position_counts = team_df['position'].value_counts()
        required_positions = {'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}
        
        for pos, required in required_positions.items():
            if position_counts.get(pos, 0) != required:
                print(f"Invalid {pos} count: {position_counts.get(pos, 0)} (should be {required})")
                return False
        
        # Check team limits (max 3 per team)
        team_counts = team_df['team'].value_counts()
        if any(count > 3 for count in team_counts):
            print(f"Too many players from same team: {team_counts[team_counts > 3].to_dict()}")
            return False
        
        # Check budget
        total_cost = team_df['price'].sum()
        if total_cost > 100.0:
            print(f"Budget exceeded: £{total_cost:.1f}m (max £100.0m)")
            return False
        
        return True
    
    def calculate_team_points(self, team_df: pd.DataFrame) -> float:
        """Calculate total predicted points for starting XI."""
        starters = team_df[team_df['is_starter'] == True]
        return starters['predicted_points'].sum()
    
    def find_best_transfer(self, current_team_json: Dict) -> Dict:
        """Find the best single transfer to maximize points."""
        # Load all available players first
        self.players_df = self.load_player_data()
        
        # Parse current team (this now uses the loaded player data)
        current_team = self.parse_current_team(current_team_json)
        
        # Validate current team
        if not self.validate_team_constraints(current_team):
            raise ValueError("Current team violates FPL constraints")
        
        current_points = self.calculate_team_points(current_team)
        current_cost = current_team['price'].sum()
        available_budget = 100.0 - current_cost
        
        print(f"Current team points: {current_points:.2f}")
        print(f"Current cost: £{current_cost:.1f}m")
        print(f"Available budget: £{available_budget:.1f}m")
        
        best_transfer = None
        best_points_gain = 0
        
        # Try removing each player and replacing with a better option
        for idx, current_player in current_team.iterrows():
            current_id = current_player['id']
            current_pos = current_player['position']
            current_team_name = current_player['team']
            current_price = current_player['price']
            current_pred_points = current_player['predicted_points']
            is_starter = current_player['is_starter']
            
            # Skip if not a starter (bench optimization is different)
            if not is_starter:
                continue
            
            # Find available replacements of same position
            available_players = self.players_df[
                (self.players_df['position'] == current_pos) &
                (~self.players_df['id'].isin(current_team['id']))  # Not already in team
            ].copy()
            
            # Check budget constraint for each replacement
            for _, replacement in available_players.iterrows():
                price_diff = replacement['price'] - current_price
                
                # Skip if too expensive
                if price_diff > available_budget:
                    continue
                
                # Create temporary team with the transfer
                temp_team = current_team.copy()
                temp_team.loc[idx, 'id'] = replacement['id']
                temp_team.loc[idx, 'name'] = replacement['name']
                temp_team.loc[idx, 'team'] = replacement['team']
                temp_team.loc[idx, 'price'] = replacement['price']
                temp_team.loc[idx, 'predicted_points'] = replacement['predicted_points']
                
                # Check team constraint (max 3 from same team)
                if replacement['team'] != current_team_name:
                    team_counts = temp_team['team'].value_counts()
                    if team_counts.get(replacement['team'], 0) > 3:
                        continue
                
                # Calculate points improvement
                points_gain = replacement['predicted_points'] - current_pred_points
                
                if points_gain > best_points_gain:
                    best_points_gain = points_gain
                    best_transfer = {
                        'out': {
                            'id': current_id,
                            'name': current_player['name'],
                            'position': current_pos,
                            'team': current_team_name,
                            'price': current_price,
                            'predicted_points': current_pred_points
                        },
                        'in': {
                            'id': replacement['id'],
                            'name': replacement['name'],
                            'position': current_pos,
                            'team': replacement['team'],
                            'price': replacement['price'],
                            'predicted_points': replacement['predicted_points']
                        },
                        'points_gain': points_gain,
                        'cost_change': price_diff,
                        'new_total_points': current_points + points_gain,
                        'new_total_cost': current_cost + price_diff
                    }
        
        return {
            'current_team_points': current_points,
            'current_team_cost': current_cost,
            'best_transfer': best_transfer,
            'no_transfer_recommended': best_transfer is None
        }
    
    def format_transfer_recommendation(self, result: Dict) -> str:
        """Format the transfer recommendation for display."""
        output = []
        output.append("=" * 60)
        output.append("FPL TRANSFER RECOMMENDATION")
        output.append("=" * 60)
        
        output.append(f"Current Team Points: {result['current_team_points']:.2f}")
        output.append(f"Current Team Cost: £{result['current_team_cost']:.1f}m")
        
        if result['no_transfer_recommended']:
            output.append("\n🚫 NO TRANSFER RECOMMENDED")
            output.append("Your current team is already optimal or no beneficial transfers available within budget.")
        else:
            transfer = result['best_transfer']
            output.append(f"\n✅ RECOMMENDED TRANSFER")
            output.append(f"OUT: {transfer['out']['name']} ({transfer['out']['position']}) - Team {transfer['out']['team']}")
            output.append(f"     £{transfer['out']['price']:.1f}m, {transfer['out']['predicted_points']:.2f} pts")
            output.append(f"IN:  {transfer['in']['name']} ({transfer['in']['position']}) - Team {transfer['in']['team']}")
            output.append(f"     £{transfer['in']['price']:.1f}m, {transfer['in']['predicted_points']:.2f} pts")
            output.append(f"")
            output.append(f"💰 Cost Change: £{transfer['cost_change']:+.1f}m")
            output.append(f"📈 Points Gain: {transfer['points_gain']:+.2f} pts")
            output.append(f"🎯 New Total Points: {transfer['new_total_points']:.2f}")
            output.append(f"💵 New Total Cost: £{transfer['new_total_cost']:.1f}m")
        
        return "\n".join(output)


def get_dummy_team() -> Dict:
    """Return a dummy current team for testing."""
    return {
        "team": [
            {
                "position": "GK",
                "players": [
                    {"id": 101, "name": "Kelleher", "team": 5, "is_starter": True},
                    {"id": 470, "name": "Dúbravka", "team": 3, "is_starter": False}
                ]
            },
            {
                "position": "DEF",
                "players": [
                    {"id": 113, "name": "Van den Berg", "team": 5, "is_starter": True},
                    {"id": 403, "name": "Gvardiol", "team": 13, "is_starter": True},
                    {"id": 568, "name": "Pedro Porro", "team": 18, "is_starter": True},
                    {"id": 291, "name": "Tarkowski", "team": 9, "is_starter": True},
                    {"id": 370, "name": "Frimpong", "team": 12, "is_starter": False}
                ]
            },
            {
                "position": "MID",
                "players": [
                    {"id": 82, "name": "Semenyo", "team": 4, "is_starter": True},
                    {"id": 580, "name": "Johnson", "team": 18, "is_starter": True},
                    {"id": 384, "name": "Gakpo", "team": 12, "is_starter": True},
                    {"id": 582, "name": "Kudus", "team": 18, "is_starter": True},
                    {"id": 325, "name": "Smith Rowe", "team": 10, "is_starter": False}
                ]
            },
            {
                "position": "FWD",
                "players": [
                    {"id": 430, "name": "Haaland", "team": 13, "is_starter": True},
                    {"id": 525, "name": "Wood", "team": 16, "is_starter": True},
                    {"id": 311, "name": "Beto", "team": 9, "is_starter": False}
                ]
            }
        ]
    }


def main():
    """Main function to run the FPL transfer optimization."""
    db_path = "/workspaces/FPL_agent/data/fpl_agent.db"
    
    # Get dummy team (in future, this will be user input)
    current_team = get_dummy_team()
    
    # Create optimizer
    optimizer = FPLTransferOptimizer(db_path)
    
    try:
        # Find best transfer
        print("Analyzing current team and finding best transfer...")
        result = optimizer.find_best_transfer(current_team)
        
        # Display recommendation
        print(optimizer.format_transfer_recommendation(result))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()