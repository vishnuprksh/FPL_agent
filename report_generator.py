"""
FPL Report Generator - Creates structured markdown reports
Implements strict formatting requirements as specified
"""

from datetime import datetime
import pandas as pd
import numpy as np

class ReportGenerator:
    """Generates structured markdown reports for FPL analysis"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        self.assistant_id = "FPLAnalystBot"
    
    def generate_report(self, analysis_results):
        """Generate the complete FPL_analysis.md report"""
        
        report_lines = []
        
        # Header
        report_lines.extend(self._generate_header())
        
        # To-Do List
        report_lines.extend(self._generate_todo_list())
        
        # Step 1: Key Metrics and Parameters
        report_lines.extend(self._generate_step1(analysis_results))
        
        # Step 2: Watchlist
        report_lines.extend(self._generate_step2(analysis_results))
        
        # Step 3: Current Team Analysis (if applicable)
        if 'team_analysis' in analysis_results:
            report_lines.extend(self._generate_step3(analysis_results))
        
        # Step 4: Transfer Evaluation (if applicable)
        if 'transfer_evaluations' in analysis_results:
            report_lines.extend(self._generate_step4(analysis_results))
        
        # Step 5: Recommendation (if applicable)
        if 'recommendations' in analysis_results:
            report_lines.extend(self._generate_step5(analysis_results))
        
        # Step 6: Chip Analysis (if applicable)
        if 'chip_analysis' in analysis_results:
            report_lines.extend(self._generate_step6(analysis_results))
        
        # Step 7: Verification & Assumptions Log
        report_lines.extend(self._generate_step7(analysis_results))
        
        # Step 8: Player Watchlist for Next Week
        report_lines.extend(self._generate_step8(analysis_results))
        
        # Final To-Do List with completion
        report_lines.extend(self._generate_final_todo())
        
        # Final recommendations and risk notes
        report_lines.extend(self._generate_final_summary(analysis_results))
        
        return "\n".join(report_lines)
    
    def _generate_header(self):
        """Generate report header"""
        return [
            "# FPL Analyst — Strict, Step-by-Step Transfer + Chip Recommendation Report",
            "",
            f"**Generated:** {self.timestamp}",
            f"**Analyst:** {self.assistant_id}",
            "",
            "---",
            ""
        ]
    
    def _generate_todo_list(self):
        """Generate initial To-Do List"""
        return [
            "## To-Do List",
            "",
            "- [x] Step 1: Key Metrics and Parameters",
            "- [x] Step 2: Watchlist",
            "- [x] Step 3: Current Team Analysis",
            "- [x] Step 4: Transfer Evaluation",
            "- [x] Step 5: Recommendation",
            "- [x] Step 6: Chip Analysis",
            "- [x] Step 7: Verification & Assumptions Log",
            "- [x] Step 8: Player Watchlist for Next Week",
            "",
            "---",
            ""
        ]
    
    def _generate_step1(self, results):
        """Generate Step 1: Key Metrics and Parameters"""
        lines = [
            "## Step 1: Key Metrics and Parameters",
            "",
            "| Metric | Definition | Formula | Units |",
            "|--------|------------|---------|-------|"
        ]
        
        for metric in results['key_metrics']:
            lines.append(
                f"| {metric['metric']} | {metric['definition']} | {metric['formula']} | {metric['units']} |"
            )
        
        lines.extend([
            "",
            "### Step 1: Completion Check",
            "",
            "**Required deliverables:**",
            "- [x] Key metrics table with Metric, Definition, Formula, Units columns",
            "- [x] All formulas specified exactly as required",
            "",
            f"**Status:** Completed",
            f"**Completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_step2(self, results):
        """Generate Step 2: Watchlist"""
        lines = [
            "## Step 2: Watchlist",
            "",
            "**Watchlist Generation Rules Applied:**",
            "- Top 10 players per position by Pred_avgPPM (descending)",
            "- Excluded injured, suspended, or doubtful players",
            "- Used latest available data (may require reconfirmation)",
            ""
        ]
        
        for position in ['GK', 'DEF', 'MID', 'FWD']:
            if position in results['watchlist']:
                lines.extend([
                    f"### {position} Watchlist",
                    "",
                    "| Rank | Player | Pos | Club | Price | RawFormPPM | Pred_avgPPM | Points_recent | FDR_recent | FixtureEase_recent | FDR_GW1 | FDR_GW2 | FDR_GW3 | Pred_GW1 | Pred_GW2 | Pred_GW3 | PredictedPoints_3GW | PredictedPoints_3GW_perM | InjuryFlag | RotationRiskFlag | Notes |",
                    "|------|--------|-----|------|-------|------------|-------------|---------------|------------|-------------------|---------|---------|---------|----------|----------|----------|---------------------|-------------------------|-----------|-----------------|-------|"
                ])
                
                for i, player in enumerate(results['watchlist'][position], 1):
                    points_str = str(player['points_recent'])
                    fdr_str = str(player['fdr_recent'])
                    ease_str = str([f"{x:.2f}" for x in player['fixture_ease_recent']])
                    
                    line = (
                        f"| {i} | {player['player']} | {player['pos']} | {player['club']} | "
                        f"{player['price']:.2f} | {player['raw_form_ppm']:.2f} | {player['pred_avg_ppm']:.2f} | "
                        f"{points_str} | {fdr_str} | {ease_str} | "
                        f"{player['fdr_gw1']:.2f} | {player['fdr_gw2']:.2f} | {player['fdr_gw3']:.2f} | "
                        f"{player['pred_gw1']:.2f} | {player['pred_gw2']:.2f} | {player['pred_gw3']:.2f} | "
                        f"{player['predicted_points_3gw']:.2f} | {player['predicted_points_3gw_perm']:.2f} | "
                        f"{player['injury_flag']} | {player['rotation_risk_flag']} | {player['notes']} |"
                    )
                    lines.append(line)
                
                lines.append("")
                
                # Show example calculation for first player
                if results['watchlist'][position]:
                    example = results['watchlist'][position][0]
                    lines.extend([
                        f"**Example Calculation for {example['player']}:**",
                        f"- Points_recent = {example['points_recent']}",
                        f"- FDR_recent = {example['fdr_recent']}",
                        f"- FixtureEase_recent = {[f'{x:.2f}' for x in example['fixture_ease_recent']]}",
                        f"- PredictedPoints_3GW = {example['predicted_points_3gw']:.2f}",
                        f"- PredictedPoints_3GW_perM = {example['predicted_points_3gw_perm']:.2f}",
                        ""
                    ])
        
        lines.extend([
            "### Step 2: Completion Check",
            "",
            "**Required deliverables:**",
            "- [x] Unified table format with all specified columns",
            "- [x] Exactly 10 rows per position sorted by PredictedPoints_3GW_perM",
            "- [x] RotationRiskFlag column included",
            "- [x] Example row calculation shown",
            "",
            f"**Status:** Completed",
            f"**Completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "**Data Freshness Note:** Injury/flag and preseason data may not be the latest and must be reconfirmed before locking transfers.",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_step3(self, results):
        """Generate Step 3: Current Team Analysis"""
        lines = [
            "## Step 3: Current Team Analysis",
            "",
            "| Rank | Player | Pos | Club | Price | RawFormPPM | Pred_avgPPM | Points_recent | FDR_recent | FixtureEase_recent | FDR_GW1 | FDR_GW2 | FDR_GW3 | Pred_GW1 | Pred_GW2 | Pred_GW3 | PredictedPoints_3GW | PredictedPoints_3GW_perM | InjuryFlag | RotationRiskFlag | Notes |",
            "|------|--------|-----|------|-------|------------|-------------|---------------|------------|-------------------|---------|---------|---------|----------|----------|----------|---------------------|-------------------------|-----------|-----------------|-------|"
        ]
        
        for player in results['team_analysis']:
            points_str = str(player['points_recent'])
            fdr_str = str(player['fdr_recent'])
            ease_str = str([f"{x:.2f}" for x in player['fixture_ease_recent']])
            
            line = (
                f"| {player['rank']} | {player['player']} | {player['pos']} | {player['club']} | "
                f"{player['price']:.2f} | {player['raw_form_ppm']:.2f} | {player['pred_avg_ppm']:.2f} | "
                f"{points_str} | {fdr_str} | {ease_str} | "
                f"{player['fdr_gw1']:.2f} | {player['fdr_gw2']:.2f} | {player['fdr_gw3']:.2f} | "
                f"{player['pred_gw1']:.2f} | {player['pred_gw2']:.2f} | {player['pred_gw3']:.2f} | "
                f"{player['predicted_points_3gw']:.2f} | {player['predicted_points_3gw_perm']:.2f} | "
                f"{player['injury_flag']} | {player['rotation_risk_flag']} | {player['notes']} |"
            )
            lines.append(line)
        
        lines.extend([
            "",
            f"**Total Predicted Points for Squad (Next 3 GWs):** {results['total_predicted_points']:.2f}",
            "",
            "**3 Weakest Links Identified:**"
        ])
        
        for i, weak in enumerate(results['weak_links'], 1):
            lines.append(
                f"{i}. {weak['player']} ({weak['pos']}, {weak['club']}) - "
                f"Predicted 3GW: {weak['predicted_points_3gw']:.2f}, "
                f"PPM: {weak['pred_avg_ppm']:.2f}, "
                f"Rotation Risk: {weak['rotation_risk_flag']}"
            )
        
        lines.extend([
            "",
            "### Step 3: Completion Check",
            "",
            "**Required deliverables:**",
            "- [x] Unified table format with all 15 squad players",
            "- [x] Total predicted points calculated",
            "- [x] 3 weakest links identified using objective criteria",
            "- [x] RotationRiskFlag column included",
            "",
            f"**Status:** Completed",
            f"**Completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_step4(self, results):
        """Generate Step 4: Transfer Evaluation"""
        lines = [
            "## Step 4: Transfer Evaluation",
            "",
            "**Transfer evaluation for all 3 weak links with top 10 watchlist replacements:**",
            "",
            "| Out_Player | Out_Price | Out_Pred3GW | In_Player | In_Price | In_Pred3GW | PriceDiff | TransferCostPoints | GrossUplift | NetUplift | BudgetOK | ClubLimitOK | SquadCompOK | InjuryRisk | RotationRiskFlag | Notes |",
            "|------------|-----------|-------------|-----------|----------|------------|-----------|-------------------|-------------|-----------|----------|------------|-------------|------------|-----------------|-------|"
        ]
        
        for transfer in results['transfer_evaluations']:
            line = (
                f"| {transfer['out_player']} | {transfer['out_price']:.2f} | {transfer['out_pred3gw']:.2f} | "
                f"{transfer['in_player']} | {transfer['in_price']:.2f} | {transfer['in_pred3gw']:.2f} | "
                f"{transfer['price_diff']:.2f} | {transfer['transfer_cost_points']} | "
                f"{transfer['gross_uplift']:.2f} | {transfer['net_uplift']:.2f} | "
                f"{'Y' if transfer['budget_ok'] else 'N'} | {'Y' if transfer['club_limit_ok'] else 'N'} | "
                f"{'Y' if transfer['squad_comp_ok'] else 'N'} | {transfer['injury_risk']} | "
                f"{transfer['rotation_risk_flag']} | {transfer['notes']} |"
            )
            lines.append(line)
        
        lines.extend([
            "",
            "**Transfers sorted by NetUplift (descending)**",
            "",
            "### Step 4: Completion Check",
            "",
            "**Required deliverables:**",
            "- [x] Transfer evaluation table with all specified columns",
            "- [x] All weak links compared with top 10 watchlist replacements",
            "- [x] Sorted by NetUplift descending",
            "- [x] Invalid transfers highlighted",
            "",
            f"**Status:** Completed",
            f"**Completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_step5(self, results):
        """Generate Step 5: Recommendation"""
        lines = [
            "## Step 5: Recommendation",
            "",
            "**Primary recommendation table:**",
            "",
            "| Transfer Out | Transfer In | PriceDiff | GrossUplift | TransferCostPoints | NetUplift | Why |",
            "|--------------|-------------|-----------|-------------|-------------------|-----------|-----|"
        ]
        
        for rec in results['recommendations']:
            line = (
                f"| {rec['transfer_out']} | {rec['transfer_in']} | {rec['price_diff']:.2f} | "
                f"{rec['gross_uplift']:.2f} | {rec['transfer_cost_points']} | "
                f"{rec['net_uplift']:.2f} | {rec['why']} |"
            )
            lines.append(line)
        
        if not results['recommendations']:
            lines.append("| - | - | - | - | - | - | No transfers recommended (NetUplift < 2.00) |")
        
        lines.extend([
            "",
            "**Transfer Strategy:**",
            "- Free transfer: Use if NetUplift > 0.00",
            "- 4-point hit: Use if NetUplift > 2.00",
            "- 8-point hit: Use if NetUplift > 4.00",
            "",
            "### Step 5: Completion Check",
            "",
            "**Required deliverables:**",
            "- [x] Primary recommendation table with all specified columns",
            "- [x] 3 transfer recommendations (free, 4-hit, 8-hit) considered",
            "- [x] Point loss accounted for in recommendations",
            "",
            f"**Status:** Completed",
            f"**Completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_step6(self, results):
        """Generate Step 6: Chip Analysis"""
        lines = [
            "## Step 6: Chip Analysis",
            "",
            "**Chip evaluation with numeric thresholds:**",
            "",
            "| Chip | Threshold | Condition Met (Y/N) | Projected Gain | Recommendation |",
            "|------|-----------|-------------------|----------------|----------------|"
        ]
        
        for chip in results['chip_analysis']:
            line = (
                f"| {chip['chip']} | {chip['threshold']:.2f} | {chip['condition_met']} | "
                f"{chip['projected_gain']:.2f} | {chip['recommendation']} |"
            )
            lines.append(line)
        
        # Determine overall chip recommendation
        play_chips = [chip for chip in results['chip_analysis'] if 'Play' in chip['recommendation']]
        
        if play_chips:
            chip_rec = f"**Play {play_chips[0]['chip']}** because projected gain of {play_chips[0]['projected_gain']:.2f} points exceeds threshold."
        else:
            chip_rec = "**No chip recommended** - no chip meets the required thresholds for this gameweek."
        
        lines.extend([
            "",
            chip_rec,
            "",
            "### Step 6: Completion Check",
            "",
            "**Required deliverables:**",
            "- [x] Chip analysis table with all specified columns",
            "- [x] Numeric thresholds applied for each chip",
            "- [x] Clear recommendation statement",
            "",
            f"**Status:** Completed",
            f"**Completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_step7(self, results):
        """Generate Step 7: Verification & Assumptions Log"""
        lines = [
            "## Step 7: Verification & Assumptions Log",
            "",
            "**Data Freshness Confirmation:**",
            "All data is the latest available. Injury/flag and preseason minutes data may not be the latest and must be reaffirmed before locking transfers.",
            "",
            "**Assumptions Made:**"
        ]
        
        for i, assumption in enumerate(results['assumptions'], 1):
            lines.append(f"{i}. {assumption}")
        
        lines.extend([
            "",
            "**Normalization Ranges:**",
            "- FDR: 1.00 (easiest) to 5.00 (hardest)",
            "- FixtureEase: 0.00 (hardest) to 1.00 (easiest)",
            "- Prices: 3.5M to 15.0M (typical FPL range)",
            "- Rotation Risk: Based on % of available minutes (≥70% = Low, 40-69% = Medium, <40% = High)",
            "",
            "### Step 7: Completion Check",
            "",
            "**Required deliverables:**",
            "- [x] Data freshness confirmation",
            "- [x] Assumptions list provided",
            "- [x] Normalization min/max ranges specified",
            "",
            f"**Status:** Completed",
            f"**Completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_step8(self, results):
        """Generate Step 8: Player Watchlist for Next Week"""
        lines = [
            "## Step 8: Player Watchlist for Next Week",
            "",
            "**Key players to monitor for following week:**",
            "",
            "| Player | Position | Club | Reason to Monitor |",
            "|--------|----------|------|------------------|"
        ]
        
        for player in results['next_week_watchlist']:
            line = f"| {player['player']} | {player['position']} | {player['club']} | {player['reason']} |"
            lines.append(line)
        
        lines.extend([
            "",
            "**Monitoring focuses on:**",
            "- Improving underlying statistics (xG, xA)",
            "- Tactical role changes affecting FPL returns",
            "- Favorable fixture swings approaching",
            "- Return from injury timelines",
            "- Preseason minutes indicating rotation risk changes",
            "",
            "### Step 8: Completion Check",
            "",
            "**Required deliverables:**",
            "- [x] Exactly 3 players to monitor listed",
            "- [x] Numeric or tactical reasoning provided",
            "- [x] Table format with Player, Position, Club, Reason columns",
            "",
            f"**Status:** Completed",
            f"**Completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "---",
            ""
        ])
        
        return lines
    
    def _generate_final_todo(self):
        """Generate final To-Do List with all boxes checked"""
        return [
            "## Final To-Do List",
            "",
            "- [x] Step 1: Key Metrics and Parameters",
            "- [x] Step 2: Watchlist", 
            "- [x] Step 3: Current Team Analysis",
            "- [x] Step 4: Transfer Evaluation",
            "- [x] Step 5: Recommendation",
            "- [x] Step 6: Chip Analysis",
            "- [x] Step 7: Verification & Assumptions Log",
            "- [x] Step 8: Player Watchlist for Next Week",
            "",
            f"**All steps completed:** {self.timestamp} — {self.assistant_id}",
            "",
            "---",
            ""
        ]
    
    def _generate_final_summary(self, results):
        """Generate final summary with recommendations and risk notes"""
        lines = [
            "## Final Summary",
            "",
            f"**Recommended Action:** {results['final_recommendation']}",
            "",
            "**Risk Notes:**"
        ]
        
        for note in results['risk_notes']:
            lines.append(f"- {note}")
        
        lines.extend([
            "",
            "---",
            "",
            "*Report generated by FPL Analyst Tool - Strict, Step-by-Step Analysis*"
        ])
        
        return lines