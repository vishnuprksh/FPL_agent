"""
Transfer optimization for suggesting best player transfers.
"""

import pandas as pd
from typing import Dict
from .database import FPLDatabase
from .validation import FPLValidator


class FPLTransferOptimizer:
    """Optimizer for suggesting single player transfers in FPL."""
    
    def __init__(self, db_path: str):
        """
        Initialize the transfer optimizer.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db = FPLDatabase(db_path)
        self.validator = FPLValidator()
        self.players_df = None
        
    def find_best_transfer(self, current_team_json: Dict) -> Dict:
        """Find the best single transfer to maximize points."""
        # Load all available players first
        self.players_df = self.db.load_player_data()
        
        # Parse current team (this now uses the loaded player data)
        current_team = self.validator.parse_current_team(current_team_json, self.players_df)
        
        # Validate current team
        if not self.validator.validate_team_constraints(current_team):
            raise ValueError("Current team violates FPL constraints")
        
        current_points = self.validator.calculate_team_points(current_team)
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