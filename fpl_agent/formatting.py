"""
Formatting utilities for displaying FPL results.
"""

from typing import Dict


class FPLFormatter:
    """Formatter for FPL results and recommendations."""
    
    @staticmethod
    def format_squad_results(results: Dict) -> str:
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
    
    @staticmethod
    def format_transfer_recommendation(result: Dict) -> str:
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
    
    @staticmethod
    def format_top_performers(df, positions=['GK', 'DEF', 'MID', 'FWD'], top_n=3, weeks=1) -> str:
        """Format top performers by position."""
        period = f"Next {weeks} Weeks" if weeks > 1 else "This Week"
        output = []
        output.append(f"Top {top_n} Performers by Position ({period})")
        output.append("=" * 50)
        
        for pos in positions:
            pos_df = df[df['position'] == pos].head(top_n)
            if not pos_df.empty:
                output.append(f"\n{pos}:")
                for _, player in pos_df.iterrows():
                    output.append(f"  {player['name']} ({player['team']}) - {player['predicted_points']:.2f} pts")
            else:
                output.append(f"\n{pos}: No data available")
        
        return "\n".join(output)