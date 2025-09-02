"""
FPL Analysis - Legacy analysis module
This file is maintained for compatibility but the main analysis is now in fpl_analyst.py
"""

import pandas as pd
import numpy as np
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from analysis_engine import FPLAnalysisEngine
    from report_generator import ReportGenerator
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required files are in the same directory")

def main():
    """Main function for command-line usage"""
    print("FPL Analyst Tool")
    print("================")
    print()
    print("For the full interactive experience, please run:")
    print("streamlit run fpl_analyst.py")
    print()
    
    # Basic demo analysis
    try:
        engine = FPLAnalysisEngine('fpl_data.csv')
        print("✅ FPL data loaded successfully")
        print(f"📊 Dataset: {engine.df.shape[0]} records from {engine.df['season'].min()} to {engine.df['season'].max()}")
        print(f"🎯 Latest season: {engine.latest_season} (up to GW {engine.latest_gameweek})")
        print()
        
        # Generate a sample watchlist
        print("Generating sample watchlist...")
        watchlist = engine.generate_watchlist(planning_horizon=3)
        
        print("\n🔍 Top 3 players by position (by predicted points per million):")
        for position in ['GK', 'DEF', 'MID', 'FWD']:
            if position in watchlist and watchlist[position]:
                print(f"\n{position}:")
                for i, player in enumerate(watchlist[position][:3], 1):
                    print(f"  {i}. {player['player']} ({player['club']}) - £{player['price']:.1f}M - {player['predicted_points_3gw_perm']:.2f} pts/£M")
        
        print("\n" + "="*50)
        print("For detailed analysis, transfer recommendations, and chip advice,")
        print("please use the Streamlit interface: streamlit run fpl_analyst.py")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Please ensure fpl_data.csv is available in the current directory")

if __name__ == "__main__":
    main()