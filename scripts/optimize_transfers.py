#!/usr/bin/env python3
"""
FPL Transfer Optimizer

Suggests the best single transfer to maximize points for the current gameweek.
Takes a current team and evaluates all possible single transfers.
"""

from fpl_agent import FPLTransferOptimizer, FPLFormatter
from typing import Dict


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
        formatter = FPLFormatter()
        print(formatter.format_transfer_recommendation(result))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()