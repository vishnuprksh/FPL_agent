#!/usr/bin/env python3
"""
FPL Squad Optimizer using Integer Linear Programming (ILP)

Creates an optimal 15-player FPL squad that maximizes predicted points for the 
starting 11 while keeping bench players as cheap as possible.
"""

import sqlite3
import pandas as pd
from ortools.linear_solver import pywraplp
from typing import Dict, List, Tuple, Optional


class FPLSquadOptimizer:
    """Integer Linear Program solver for FPL squad optimization."""
    
    def __init__(self, db_path: str, epsilon: float = 0.001):
        """
        Initialize the optimizer.
        
        Args:
            db_path: Path to the SQLite database
            epsilon: Weight for bench cost penalty (should be small)
        """
        self.db_path = db_path
        self.epsilon = epsilon
        self.solver = None
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
        
        print(f"Loaded {len(df)} players from database")
        print(f"Position distribution: {df['position'].value_counts().to_dict()}")
        
        return df
    
    def create_optimization_model(self) -> pywraplp.Solver:
        """Create and configure the ILP model."""
        self.players_df = self.load_player_data()
        n_players = len(self.players_df)
        
        # Create solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            raise RuntimeError("Could not create solver")
        
        # Decision variables
        squad = {}  # squad_i ∈ {0,1} - player i in 15-man squad
        start = {}  # start_i ∈ {0,1} - player i in starting 11
        
        for i in range(n_players):
            squad[i] = solver.IntVar(0, 1, f'squad_{i}')
            start[i] = solver.IntVar(0, 1, f'start_{i}')
        
        # Objective: Maximize predicted points of starting 11, minimize bench cost
        objective = solver.Objective()
        for i in range(n_players):
            predicted_points = self.players_df.iloc[i]['predicted_points']
            price = self.players_df.iloc[i]['price']
            
            # Primary: maximize starting XI points
            objective.SetCoefficient(start[i], predicted_points)
            
            # Secondary: minimize bench cost (squad - start = bench players)
            objective.SetCoefficient(squad[i], -self.epsilon * price)
            objective.SetCoefficient(start[i], self.epsilon * price)
        
        objective.SetMaximization()
        
        # CONSTRAINTS
        
        # 1. Squad size = 15
        solver.Add(solver.Sum([squad[i] for i in range(n_players)]) == 15)
        
        # 2. Starting XI size = 11
        solver.Add(solver.Sum([start[i] for i in range(n_players)]) == 11)
        
        # 3. Link constraints: start_i <= squad_i
        for i in range(n_players):
            solver.Add(start[i] <= squad[i])
        
        # 4. Squad position requirements (exact)
        positions = ['GK', 'DEF', 'MID', 'FWD']
        squad_requirements = {'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}
        
        for pos in positions:
            pos_players = self.players_df[self.players_df['position'] == pos].index
            solver.Add(
                solver.Sum([squad[i] for i in pos_players]) == squad_requirements[pos]
            )
        
        # 5. Starting XI position bounds
        gk_players = self.players_df[self.players_df['position'] == 'GK'].index
        def_players = self.players_df[self.players_df['position'] == 'DEF'].index
        mid_players = self.players_df[self.players_df['position'] == 'MID'].index
        fwd_players = self.players_df[self.players_df['position'] == 'FWD'].index
        
        solver.Add(solver.Sum([start[i] for i in gk_players]) == 1)
        solver.Add(solver.Sum([start[i] for i in def_players]) >= 3)
        solver.Add(solver.Sum([start[i] for i in def_players]) <= 5)
        solver.Add(solver.Sum([start[i] for i in mid_players]) >= 3)
        solver.Add(solver.Sum([start[i] for i in mid_players]) <= 5)
        solver.Add(solver.Sum([start[i] for i in fwd_players]) >= 1)
        solver.Add(solver.Sum([start[i] for i in fwd_players]) <= 3)
        
        # 6. Team cap: max 3 players from any team
        teams = self.players_df['team'].unique()
        for team in teams:
            team_players = self.players_df[self.players_df['team'] == team].index
            if len(team_players) > 0:
                solver.Add(solver.Sum([squad[i] for i in team_players]) <= 3)
        
        # 7. Budget constraint: total cost <= 100.0
        solver.Add(
            solver.Sum([
                squad[i] * self.players_df.iloc[i]['price'] 
                for i in range(n_players)
            ]) <= 100.0
        )
        
        self.solver = solver
        self.squad_vars = squad
        self.start_vars = start
        
        return solver
    
    def solve(self) -> Dict:
        """Solve the optimization problem and return results."""
        if not self.solver:
            self.create_optimization_model()
        
        print("Solving optimization problem...")
        status = self.solver.Solve()
        
        if status != pywraplp.Solver.OPTIMAL:
            if status == pywraplp.Solver.INFEASIBLE:
                raise RuntimeError("Problem is infeasible - no valid solution exists")
            elif status == pywraplp.Solver.UNBOUNDED:
                raise RuntimeError("Problem is unbounded")
            else:
                raise RuntimeError(f"Solver failed with status: {status}")
        
        # Extract solution
        squad_indices = []
        start_indices = []
        
        for i in range(len(self.players_df)):
            if self.squad_vars[i].solution_value() > 0.5:
                squad_indices.append(i)
            if self.start_vars[i].solution_value() > 0.5:
                start_indices.append(i)
        
        squad_players = self.players_df.iloc[squad_indices].copy()
        start_players = self.players_df.iloc[start_indices].copy()
        bench_players = squad_players[~squad_players.index.isin(start_indices)].copy()
        
        # Calculate metrics
        total_predicted_points = start_players['predicted_points'].sum()
        total_cost = squad_players['price'].sum()
        bench_cost = bench_players['price'].sum()
        objective_value = self.solver.Objective().Value()
        
        return {
            'squad': squad_players,
            'starting_xi': start_players,
            'bench': bench_players,
            'total_predicted_points': total_predicted_points,
            'total_cost': total_cost,
            'bench_cost': bench_cost,
            'objective_value': objective_value,
            'epsilon': self.epsilon
        }
    
    def format_results(self, results: Dict) -> str:
        """Format the optimization results for display."""
        output = []
        output.append("=" * 60)
        output.append("FPL SQUAD OPTIMIZATION RESULTS")
        output.append("=" * 60)
        
        # Summary
        output.append(f"\nOBJECTIVE VALUE: {results['objective_value']:.6f}")
        output.append(f"EPSILON (bench penalty): {results['epsilon']}")
        output.append(f"TOTAL PREDICTED POINTS (Starting XI): {results['total_predicted_points']:.2f}")
        output.append(f"TOTAL SQUAD COST: £{results['total_cost']:.1f}m")
        output.append(f"BENCH COST: £{results['bench_cost']:.1f}m")
        
        # Starting XI
        output.append(f"\n{'='*30} STARTING XI {'='*30}")
        start_by_pos = results['starting_xi'].groupby('position')
        for pos in ['GK', 'DEF', 'MID', 'FWD']:
            if pos in start_by_pos.groups:
                players = start_by_pos.get_group(pos)
                output.append(f"\n{pos} ({len(players)}):")
                for _, player in players.iterrows():
                    output.append(
                        f"  {player['name']:20} (Team {player['team']:2}) "
                        f"£{player['price']:4.1f}m  {player['predicted_points']:5.2f}pts"
                    )
        
        # Bench
        output.append(f"\n{'='*35} BENCH {'='*35}")
        bench_by_pos = results['bench'].groupby('position')
        for pos in ['GK', 'DEF', 'MID', 'FWD']:
            if pos in bench_by_pos.groups:
                players = bench_by_pos.get_group(pos)
                output.append(f"\n{pos} ({len(players)}):")
                for _, player in players.iterrows():
                    output.append(
                        f"  {player['name']:20} (Team {player['team']:2}) "
                        f"£{player['price']:4.1f}m  {player['predicted_points']:5.2f}pts"
                    )
        
        # Full squad summary
        output.append(f"\n{'='*25} FULL SQUAD SUMMARY {'='*25}")
        squad_by_pos = results['squad'].groupby('position')
        for pos in ['GK', 'DEF', 'MID', 'FWD']:
            if pos in squad_by_pos.groups:
                players = squad_by_pos.get_group(pos)
                total_cost = players['price'].sum()
                total_points = players['predicted_points'].sum()
                output.append(f"{pos}: {len(players)} players, £{total_cost:.1f}m, {total_points:.2f}pts")
        
        return "\n".join(output)


def main():
    """Main function to run the FPL squad optimization."""
    db_path = "/workspaces/FPL_agent/data/fpl_agent.db"
    
    # Create optimizer
    optimizer = FPLSquadOptimizer(db_path, epsilon=0.001)
    
    try:
        # Solve the optimization problem
        results = optimizer.solve()
        
        # Display results
        print(optimizer.format_results(results))
        
        # Validation
        print(f"\n{'='*25} VALIDATION {'='*25}")
        squad = results['squad']
        start = results['starting_xi']
        
        print(f"Squad size: {len(squad)} (should be 15)")
        print(f"Starting XI size: {len(start)} (should be 11)")
        print(f"Squad positions: {squad['position'].value_counts().to_dict()}")
        print(f"Starting positions: {start['position'].value_counts().to_dict()}")
        print(f"Teams with 3+ players: {squad.groupby('team').size()[squad.groupby('team').size() >= 3].to_dict()}")
        print(f"Budget used: £{squad['price'].sum():.1f}m / £100.0m")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nPossible solutions:")
        print("- Increase budget constraint")
        print("- Relax team cap (allow more than 3 players per team)")
        print("- Check data quality (missing predicted points, prices)")


if __name__ == "__main__":
    main()