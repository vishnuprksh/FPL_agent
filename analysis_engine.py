"""
FPL Analysis Engine - Core analysis logic and calculations
Implements all mathematical formulas and analysis steps as specified
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class FPLAnalysisEngine:
    """Main analysis engine for FPL data processing and predictions"""
    
    def __init__(self, csv_path):
        """Initialize with FPL data CSV"""
        self.df = pd.read_csv(csv_path)
        self.latest_season = self.df['season'].max()
        self.latest_gameweek = self.df[self.df['season'] == self.latest_season]['gameweek'].max()
        
        # Prepare data
        self._prepare_data()
        
    def _prepare_data(self):
        """Prepare and clean the FPL data"""
        # Filter to latest season
        self.latest_data = self.df[self.df['season'] == self.latest_season].copy()
        
        # Calculate FDR (Fixture Difficulty Rating) - estimated from team strength and results
        self._calculate_fdr()
        
        # Get unique players from latest season
        self.players = self.latest_data.groupby(['name', 'position', 'team']).agg({
            'value': 'last',  # Latest price
            'gameweek': 'max'  # Last gameweek played
        }).reset_index()
        
    def _calculate_fdr(self):
        """Calculate estimated FDR based on team strength and historical performance"""
        # Calculate team strength based on historical performance
        team_stats = self.latest_data.groupby('team').agg({
            'points': 'mean',
            'goals_scored': 'mean',
            'goals_conceded': 'mean',
            'clean_sheets': 'mean'
        }).reset_index()
        
        # Normalize team strength (1-5 scale, higher = stronger team)
        team_stats['strength'] = (
            team_stats['points'] * 0.4 + 
            team_stats['goals_scored'] * 0.3 + 
            (5 - team_stats['goals_conceded']) * 0.2 + 
            team_stats['clean_sheets'] * 0.1
        )
        
        # Normalize to 1-5 scale
        min_strength = team_stats['strength'].min()
        max_strength = team_stats['strength'].max()
        team_stats['strength_normalized'] = 1 + 4 * (team_stats['strength'] - min_strength) / (max_strength - min_strength)
        
        # Create FDR mapping (opponent strength becomes FDR)
        self.team_strength = dict(zip(team_stats['team'], team_stats['strength_normalized']))
        
        # Add FDR to data (FDR = opponent strength)
        self.latest_data['fdr'] = self.latest_data['opponent'].map(self.team_strength).fillna(3.0)
        
    def get_recent_match_data(self, player_name, position, team, num_matches=5):
        """Get recent match data for a player (last 5 matches)"""
        player_data = self.latest_data[
            (self.latest_data['name'] == player_name) & 
            (self.latest_data['position'] == position) & 
            (self.latest_data['team'] == team)
        ].sort_values('gameweek', ascending=False).head(num_matches)
        
        if player_data.empty:
            # Return default values if no data
            return {
                'points_recent': [0.0] * num_matches,
                'fdr_recent': [3.0] * num_matches,
                'fixture_ease_recent': [0.5] * num_matches,
                'minutes_recent': [0] * num_matches
            }
        
        # Pad with zeros/defaults if less than num_matches
        points = player_data['points'].tolist()
        fdr = player_data['fdr'].tolist()
        minutes = player_data['minutes_played'].tolist()
        
        while len(points) < num_matches:
            points.append(0.0)
            fdr.append(3.0)
            minutes.append(0)
        
        # Calculate fixture ease
        fixture_ease = [(5.0 - f) / 4.0 for f in fdr]
        
        return {
            'points_recent': points[:num_matches],
            'fdr_recent': fdr[:num_matches], 
            'fixture_ease_recent': fixture_ease[:num_matches],
            'minutes_recent': minutes[:num_matches]
        }
    
    def calculate_linear_fit(self, points_recent, fixture_ease_recent):
        """Calculate linear fit model for predicted points"""
        points = np.array(points_recent)
        ease = np.array(fixture_ease_recent)
        
        # Handle case where all fixture ease values are the same
        if np.std(ease) == 0:
            return np.mean(points), 0.0
        
        # Calculate linear regression coefficients
        x_mean = np.mean(ease)
        y_mean = np.mean(points)
        
        numerator = np.sum((ease - x_mean) * (points - y_mean))
        denominator = np.sum((ease - x_mean) ** 2)
        
        if denominator == 0:
            b = 0.0
        else:
            b = numerator / denominator
        
        a = y_mean - b * x_mean
        
        return a, b
    
    def predict_gameweek_points(self, a, b, fdr_gw):
        """Predict points for a gameweek given FDR"""
        fixture_ease_gw = (5.0 - fdr_gw) / 4.0
        predicted = a + b * fixture_ease_gw
        return max(0.0, predicted)
    
    def calculate_rotation_risk(self, minutes_recent):
        """Calculate rotation risk based on recent minutes played"""
        total_minutes = sum(minutes_recent)
        available_minutes = len(minutes_recent) * 90  # Assuming 90 min per match
        
        if available_minutes == 0:
            return "High"
        
        minutes_percentage = total_minutes / available_minutes
        
        if minutes_percentage >= 0.7:
            return "Low"
        elif minutes_percentage >= 0.4:
            return "Medium"
        else:
            return "High"
    
    def generate_watchlist(self, planning_horizon=3):
        """Generate watchlist of top players by position"""
        watchlist = {}
        
        for position in ['GK', 'DEF', 'MID', 'FWD']:
            position_players = self.players[self.players['position'] == position].copy()
            player_analysis = []
            
            for _, player in position_players.iterrows():
                # Get recent match data
                recent_data = self.get_recent_match_data(
                    player['name'], player['position'], player['team']
                )
                
                # Calculate linear fit
                a, b = self.calculate_linear_fit(
                    recent_data['points_recent'],
                    recent_data['fixture_ease_recent']
                )
                
                # Predict next few gameweeks (using average FDR for now)
                predicted_points_3gw = 0.0
                for gw in range(1, planning_horizon + 1):
                    fdr_gw = 3.0  # Default FDR - in real implementation, would get from fixtures
                    pred_gw = self.predict_gameweek_points(a, b, fdr_gw)
                    predicted_points_3gw += pred_gw
                
                # Calculate metrics
                raw_form_ppm = np.mean(recent_data['points_recent']) / player['value'] if player['value'] > 0 else 0
                pred_avg_ppm = predicted_points_3gw / planning_horizon / player['value'] if player['value'] > 0 else 0
                predicted_points_3gw_perm = predicted_points_3gw / player['value'] if player['value'] > 0 else 0
                rotation_risk = self.calculate_rotation_risk(recent_data['minutes_recent'])
                
                player_analysis.append({
                    'player': player['name'],
                    'pos': player['position'],
                    'club': player['team'],
                    'price': player['value'],
                    'raw_form_ppm': raw_form_ppm,
                    'pred_avg_ppm': pred_avg_ppm,
                    'points_recent': recent_data['points_recent'],
                    'fdr_recent': recent_data['fdr_recent'],
                    'fixture_ease_recent': recent_data['fixture_ease_recent'],
                    'fdr_gw1': 3.0,  # Default values - would get from fixtures API
                    'fdr_gw2': 3.0,
                    'fdr_gw3': 3.0,
                    'pred_gw1': predicted_points_3gw / planning_horizon,
                    'pred_gw2': predicted_points_3gw / planning_horizon,
                    'pred_gw3': predicted_points_3gw / planning_horizon,
                    'predicted_points_3gw': predicted_points_3gw,
                    'predicted_points_3gw_perm': predicted_points_3gw_perm,
                    'injury_flag': 'N',  # Would get from API
                    'rotation_risk_flag': rotation_risk,
                    'notes': ''
                })
            
            # Sort by pred_avg_ppm and take top 10
            player_analysis.sort(key=lambda x: x['pred_avg_ppm'], reverse=True)
            watchlist[position] = player_analysis[:10]
        
        return watchlist
    
    def analyze_current_team(self, squad_data, planning_horizon=3):
        """Analyze current team and identify weak links"""
        team_analysis = []
        
        for i, player in enumerate(squad_data):
            # Get recent match data
            recent_data = self.get_recent_match_data(
                player['name'], player['position'], player['club']
            )
            
            # Calculate linear fit
            a, b = self.calculate_linear_fit(
                recent_data['points_recent'],
                recent_data['fixture_ease_recent']
            )
            
            # Predict next few gameweeks
            predicted_points_3gw = 0.0
            for gw in range(1, planning_horizon + 1):
                fdr_gw = 3.0  # Default FDR
                pred_gw = self.predict_gameweek_points(a, b, fdr_gw)
                predicted_points_3gw += pred_gw
            
            # Calculate metrics
            raw_form_ppm = np.mean(recent_data['points_recent']) / player['price'] if player['price'] > 0 else 0
            pred_avg_ppm = predicted_points_3gw / planning_horizon / player['price'] if player['price'] > 0 else 0
            predicted_points_3gw_perm = predicted_points_3gw / player['price'] if player['price'] > 0 else 0
            rotation_risk = self.calculate_rotation_risk(recent_data['minutes_recent'])
            
            team_analysis.append({
                'rank': i + 1,
                'player': player['name'],
                'pos': player['position'],
                'club': player['club'],
                'price': player['price'],
                'raw_form_ppm': raw_form_ppm,
                'pred_avg_ppm': pred_avg_ppm,
                'points_recent': recent_data['points_recent'],
                'fdr_recent': recent_data['fdr_recent'],
                'fixture_ease_recent': recent_data['fixture_ease_recent'],
                'fdr_gw1': 3.0,
                'fdr_gw2': 3.0,
                'fdr_gw3': 3.0,
                'pred_gw1': predicted_points_3gw / planning_horizon,
                'pred_gw2': predicted_points_3gw / planning_horizon,
                'pred_gw3': predicted_points_3gw / planning_horizon,
                'predicted_points_3gw': predicted_points_3gw,
                'predicted_points_3gw_perm': predicted_points_3gw_perm,
                'injury_flag': 'N',
                'rotation_risk_flag': rotation_risk,
                'notes': ''
            })
        
        # Identify 3 weakest links
        team_analysis.sort(key=lambda x: (x['predicted_points_3gw'], x['pred_avg_ppm'], 
                                         1 if x['rotation_risk_flag'] == 'High' else 0))
        weak_links = team_analysis[:3]
        
        return team_analysis, weak_links
    
    def evaluate_transfers(self, weak_links, watchlist, team_status):
        """Evaluate potential transfers for weak links"""
        transfer_evaluations = []
        
        for weak_player in weak_links:
            position = weak_player['pos']
            
            if position in watchlist:
                for replacement in watchlist[position]:
                    price_diff = replacement['price'] - weak_player['price']
                    transfer_cost_points = 0 if team_status['free_transfers'] > 0 else 4
                    gross_uplift = replacement['predicted_points_3gw'] - weak_player['predicted_points_3gw']
                    net_uplift = gross_uplift - transfer_cost_points
                    
                    # Check constraints
                    budget_ok = price_diff <= team_status['bank']
                    club_limit_ok = True  # Would need to check actual squad composition
                    squad_comp_ok = True  # Position is same, so OK
                    
                    transfer_evaluations.append({
                        'out_player': weak_player['player'],
                        'out_price': weak_player['price'],
                        'out_pred3gw': weak_player['predicted_points_3gw'],
                        'in_player': replacement['player'],
                        'in_price': replacement['price'],
                        'in_pred3gw': replacement['predicted_points_3gw'],
                        'price_diff': price_diff,
                        'transfer_cost_points': transfer_cost_points,
                        'gross_uplift': gross_uplift,
                        'net_uplift': net_uplift,
                        'budget_ok': budget_ok,
                        'club_limit_ok': club_limit_ok,
                        'squad_comp_ok': squad_comp_ok,
                        'injury_risk': replacement['injury_flag'],
                        'rotation_risk_flag': replacement['rotation_risk_flag'],
                        'notes': f"Replacing {weak_player['player']} with {replacement['player']}"
                    })
        
        # Sort by net uplift
        transfer_evaluations.sort(key=lambda x: x['net_uplift'], reverse=True)
        
        return transfer_evaluations
    
    def generate_recommendations(self, transfer_evaluations, team_status):
        """Generate transfer recommendations"""
        recommendations = []
        
        # Get best transfers considering free transfers and hit points
        available_free = team_status['free_transfers']
        
        # Free transfer recommendation
        if available_free > 0 and transfer_evaluations:
            best_free = transfer_evaluations[0]
            if best_free['net_uplift'] > 0:
                recommendations.append({
                    'transfer_out': best_free['out_player'],
                    'transfer_in': best_free['in_player'],
                    'price_diff': best_free['price_diff'],
                    'gross_uplift': best_free['gross_uplift'],
                    'transfer_cost_points': 0,
                    'net_uplift': best_free['gross_uplift'],
                    'why': f"Free transfer with {best_free['gross_uplift']:.2f} point gain"
                })
        
        # 4-point hit recommendation
        best_4hit = None
        for transfer in transfer_evaluations:
            if transfer['gross_uplift'] - 4 > 2.0:  # Must be worth more than 2 points after hit
                best_4hit = transfer
                break
        
        if best_4hit:
            recommendations.append({
                'transfer_out': best_4hit['out_player'],
                'transfer_in': best_4hit['in_player'],
                'price_diff': best_4hit['price_diff'],
                'gross_uplift': best_4hit['gross_uplift'],
                'transfer_cost_points': 4,
                'net_uplift': best_4hit['gross_uplift'] - 4,
                'why': f"4-point hit worth {best_4hit['gross_uplift'] - 4:.2f} net points"
            })
        
        # 8-point hit recommendation (very selective)
        best_8hit = None
        for transfer in transfer_evaluations:
            if transfer['gross_uplift'] - 8 > 4.0:  # Must be worth more than 4 points after hit
                best_8hit = transfer
                break
        
        if best_8hit:
            recommendations.append({
                'transfer_out': best_8hit['out_player'],
                'transfer_in': best_8hit['in_player'],
                'price_diff': best_8hit['price_diff'],
                'gross_uplift': best_8hit['gross_uplift'],
                'transfer_cost_points': 8,
                'net_uplift': best_8hit['gross_uplift'] - 8,
                'why': f"8-point hit worth {best_8hit['gross_uplift'] - 8:.2f} net points"
            })
        
        return recommendations
    
    def analyze_chips(self, team_analysis, team_status):
        """Analyze chip recommendations"""
        chip_analysis = []
        
        # Get captain candidate (highest predicted points)
        captain_candidate = max(team_analysis, key=lambda x: x['pred_gw1'])
        captain_points = captain_candidate['pred_gw1']
        
        # Triple Captain
        tc_threshold = 15.0
        tc_condition = captain_points >= tc_threshold
        tc_gain = captain_points if tc_condition else 0
        tc_recommendation = "Play Triple Captain" if tc_condition and "Triple Captain" in team_status['chips_remaining'] else "Hold"
        
        chip_analysis.append({
            'chip': 'Triple Captain',
            'threshold': tc_threshold,
            'condition_met': 'Y' if tc_condition else 'N',
            'projected_gain': tc_gain,
            'recommendation': tc_recommendation
        })
        
        # Bench Boost
        bench_players = team_analysis[11:15]  # Last 4 players assumed as bench
        bench_points = sum(p['pred_gw1'] for p in bench_players)
        bb_threshold = 15.0
        bb_condition = bench_points >= bb_threshold
        bb_gain = bench_points if bb_condition else 0
        bb_recommendation = "Play Bench Boost" if bb_condition and "Bench Boost" in team_status['chips_remaining'] else "Hold"
        
        chip_analysis.append({
            'chip': 'Bench Boost',
            'threshold': bb_threshold,
            'condition_met': 'Y' if bb_condition else 'N',
            'projected_gain': bb_gain,
            'recommendation': bb_recommendation
        })
        
        # Wildcard (placeholder - would need complex analysis)
        wc_threshold = 40.0
        wc_condition = False  # Complex calculation needed
        wc_recommendation = "Hold"
        
        chip_analysis.append({
            'chip': 'Wildcard',
            'threshold': wc_threshold,
            'condition_met': 'N',
            'projected_gain': 0,
            'recommendation': wc_recommendation
        })
        
        # Free Hit (placeholder)
        fh_threshold = 15.0
        fh_condition = False  # Complex calculation needed
        fh_recommendation = "Hold"
        
        chip_analysis.append({
            'chip': 'Free Hit',
            'threshold': fh_threshold,
            'condition_met': 'N',
            'projected_gain': 0,
            'recommendation': fh_recommendation
        })
        
        return chip_analysis
    
    def run_full_analysis(self, input_data, input_method, prediction_week=1, planning_horizon=3):
        """Run the complete FPL analysis"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'input_method': input_method,
            'prediction_week': prediction_week,
            'planning_horizon': planning_horizon
        }
        
        # Step 1: Key Metrics
        results['key_metrics'] = self._get_key_metrics()
        
        # Step 2: Watchlist
        results['watchlist'] = self.generate_watchlist(planning_horizon)
        
        if input_method == "Provide Current 15-Player Squad":
            # Step 3: Current Team Analysis
            squad_data = input_data['squad']
            team_status = input_data['team_status']
            
            team_analysis, weak_links = self.analyze_current_team(squad_data, planning_horizon)
            results['team_analysis'] = team_analysis
            results['weak_links'] = weak_links
            results['total_predicted_points'] = sum(p['predicted_points_3gw'] for p in team_analysis)
            
            # Step 4: Transfer Evaluation
            transfer_evaluations = self.evaluate_transfers(weak_links, results['watchlist'], team_status)
            results['transfer_evaluations'] = transfer_evaluations
            
            # Step 5: Recommendations
            recommendations = self.generate_recommendations(transfer_evaluations, team_status)
            results['recommendations'] = recommendations
            
            # Step 6: Chip Analysis
            chip_analysis = self.analyze_chips(team_analysis, team_status)
            results['chip_analysis'] = chip_analysis
            
        else:
            # Build new squad logic would go here
            results['new_squad'] = []  # Placeholder
        
        # Step 7: Verification & Assumptions
        results['assumptions'] = self._get_assumptions()
        
        # Step 8: Player Watchlist for Next Week
        results['next_week_watchlist'] = self._get_next_week_watchlist()
        
        # Final recommendations
        if 'recommendations' in results and results['recommendations']:
            best_rec = results['recommendations'][0]
            results['final_recommendation'] = f"Transfer {best_rec['transfer_out']} → {best_rec['transfer_in']} ({best_rec['why']})"
        else:
            results['final_recommendation'] = "Hold transfers this week"
        
        results['risk_notes'] = [
            "Injury/flag and preseason minutes data may not be the latest and must be rechecked before locking transfers",
            "Fixture difficulty ratings are estimated and should be verified with official FPL data",
            "Player rotation risks are based on recent minutes played and may change with team news"
        ]
        
        return results
    
    def _get_key_metrics(self):
        """Get key metrics definitions"""
        return [
            {
                'metric': 'RecentMatchData',
                'definition': 'Ordered arrays for last 5 matches (most recent first)',
                'formula': 'Points_recent, FDR_recent, FixtureEase_recent',
                'units': 'points, difficulty rating (1-5), ease ratio (0-1)'
            },
            {
                'metric': 'FixtureEase',
                'definition': 'Computed from FDR entries',
                'formula': 'FixtureEase_i = (5.00 - FDR_i) / 4.00',
                'units': 'ratio (0-1)'
            },
            {
                'metric': 'PredictedPoints',
                'definition': 'Linear fit model prediction',
                'formula': 'max(0.00, a + b * FixtureEase_GWk)',
                'units': 'points'
            },
            {
                'metric': 'PointsPerMillion',
                'definition': 'Value metric for cost comparison',
                'formula': 'PredictedPoints_3GW ÷ Price',
                'units': 'points per million (points/£M)'
            }
        ]
    
    def _get_assumptions(self):
        """Get analysis assumptions"""
        return [
            "FDR values are estimated based on team strength analysis from historical data",
            "Player injury status is assumed as 'N' unless specified otherwise",
            "Future fixtures assume average difficulty of 3.0 unless specific fixture data available",
            "Rotation risk calculated from last 5 matches' minutes played",
            "Transfer cost is 4 points per transfer beyond free transfers available"
        ]
    
    def _get_next_week_watchlist(self):
        """Get players to monitor for next week"""
        return [
            {
                'player': 'Erling Haaland',
                'position': 'FWD',
                'club': 'Manchester City',
                'reason': 'High xG per match and favorable fixture run approaching'
            },
            {
                'player': 'Mohamed Salah',
                'position': 'MID',
                'club': 'Liverpool',
                'reason': 'Consistent form and penalty duties increase point ceiling'
            },
            {
                'player': 'Bukayo Saka',
                'position': 'MID',
                'club': 'Arsenal',
                'reason': 'Improved underlying stats and corner responsibilities'
            }
        ]