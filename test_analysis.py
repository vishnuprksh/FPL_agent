#!/usr/bin/env python3
"""
Test script to generate a sample FPL analysis report
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis_engine import FPLAnalysisEngine
from report_generator import ReportGenerator

def create_sample_squad():
    """Create a sample 15-player squad for testing"""
    return [
        {'name': 'Jordan Pickford', 'position': 'GK', 'club': 'Everton', 'price': 4.5},
        {'name': 'Jason Steele', 'position': 'GK', 'club': 'Brighton & Hove Albion', 'price': 4.0},
        {'name': 'Virgil van Dijk', 'position': 'DEF', 'club': 'Liverpool', 'price': 6.5},
        {'name': 'Trent Alexander-Arnold', 'position': 'DEF', 'club': 'Liverpool', 'price': 7.0},
        {'name': 'Gabriel dos Santos Magalhães', 'position': 'DEF', 'club': 'Arsenal', 'price': 5.1},
        {'name': 'Lewis Dunk', 'position': 'DEF', 'club': 'Brighton & Hove Albion', 'price': 5.0},
        {'name': 'João Cancelo', 'position': 'DEF', 'club': 'Manchester City', 'price': 6.5},
        {'name': 'Mohamed Salah', 'position': 'MID', 'club': 'Liverpool', 'price': 12.8},
        {'name': 'Kevin De Bruyne', 'position': 'MID', 'club': 'Manchester City', 'price': 12.5},
        {'name': 'Cole Palmer', 'position': 'MID', 'club': 'Chelsea', 'price': 5.8},
        {'name': 'Bukayo Saka', 'position': 'MID', 'club': 'Arsenal', 'price': 8.5},
        {'name': 'Bruno Fernandes', 'position': 'MID', 'club': 'Manchester United', 'price': 8.4},
        {'name': 'Erling Haaland', 'position': 'FWD', 'club': 'Manchester City', 'price': 14.2},
        {'name': 'Darwin Núñez', 'position': 'FWD', 'club': 'Liverpool', 'price': 7.5},
        {'name': 'Ollie Watkins', 'position': 'FWD', 'club': 'Aston Villa', 'price': 9.0}
    ]

def create_sample_team_status():
    """Create sample team status"""
    return {
        'bank': 0.5,
        'free_transfers': 1,
        'chips_remaining': ['Triple Captain', 'Bench Boost', 'Wildcard', 'Free Hit']
    }

def main():
    """Generate a sample analysis report"""
    print("🎯 FPL Analyst Tool - Sample Analysis Generation")
    print("=" * 50)
    
    try:
        # Initialize analysis engine
        engine = FPLAnalysisEngine('fpl_data.csv')
        print("✅ FPL data loaded successfully")
        
        # Create sample input data
        squad_data = create_sample_squad()
        team_status = create_sample_team_status()
        
        input_data = {
            'squad': squad_data,
            'team_status': team_status
        }
        
        print("📋 Sample squad created with 15 players")
        print("💰 Team status: £0.5M bank, 1 free transfer, all chips available")
        
        # Run full analysis
        print("\n🔍 Running full FPL analysis...")
        results = engine.run_full_analysis(
            input_data=input_data,
            input_method="Provide Current 15-Player Squad",
            prediction_week=1,
            planning_horizon=3
        )
        
        print("✅ Analysis completed")
        
        # Generate markdown report
        print("📝 Generating markdown report...")
        report_gen = ReportGenerator()
        markdown_report = report_gen.generate_report(results)
        
        # Save report
        with open('FPL_analysis.md', 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print("✅ Report saved as 'FPL_analysis.md'")
        
        # Display summary
        print("\n📊 Analysis Summary:")
        print(f"   - Total predicted points (3 GWs): {results.get('total_predicted_points', 0):.2f}")
        print(f"   - Recommended action: {results.get('final_recommendation', 'N/A')}")
        print(f"   - Weak links identified: {len(results.get('weak_links', []))}")
        print(f"   - Transfer options evaluated: {len(results.get('transfer_evaluations', []))}")
        print(f"   - Recommendations provided: {len(results.get('recommendations', []))}")
        
        # Show first few lines of the report
        print("\n📄 Report Preview (first 20 lines):")
        print("-" * 50)
        lines = markdown_report.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2d}: {line}")
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        
        print("\n🎉 Sample analysis completed successfully!")
        print("📁 Full report available in: FPL_analysis.md")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()