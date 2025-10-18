"""
Validation utilities for FPL teams and constraints.
"""

import pandas as pd
from typing import Dict


class FPLValidator:
    """Validator for FPL team constraints and rules."""
    
    @staticmethod
    def validate_team_constraints(team_df: pd.DataFrame) -> bool:
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
    
    @staticmethod
    def calculate_team_points(team_df: pd.DataFrame) -> float:
        """Calculate total predicted points for starting XI."""
        starters = team_df[team_df['is_starter'] == True]
        return starters['predicted_points'].sum()
    
    @staticmethod
    def parse_current_team(team_json: Dict, database_df: pd.DataFrame) -> pd.DataFrame:
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