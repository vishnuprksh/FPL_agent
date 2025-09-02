#!/usr/bin/env python3
"""
FPL Analyst Tool - Main Streamlit UI Application
Provides UI and scripts for comprehensive FPL transfer and chip recommendations
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import analysis modules (will be created)
from analysis_engine import FPLAnalysisEngine
from report_generator import ReportGenerator

def main():
    st.set_page_config(
        page_title="FPL Analyst Tool",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("⚽ FPL Analyst Tool")
    st.markdown("**Strict, Step-by-Step Transfer + Chip Recommendation System**")
    
    # Initialize session state
    if 'analysis_engine' not in st.session_state:
        try:
            st.session_state.analysis_engine = FPLAnalysisEngine('fpl_data.csv')
        except Exception as e:
            st.error(f"Error loading FPL data: {str(e)}")
            return
    
    # Sidebar configuration
    st.sidebar.header("Analysis Configuration")
    
    # Input method selection
    input_method = st.sidebar.radio(
        "Select Input Method:",
        ["Build New Squad from Watchlist", "Provide Current 15-Player Squad"],
        help="Choose how you want to provide your team data"
    )
    
    # Optional parameters
    st.sidebar.subheader("Analysis Parameters")
    prediction_week = st.sidebar.number_input("Prediction Week", min_value=1, max_value=38, value=1)
    planning_horizon = st.sidebar.number_input("Planning Horizon (GWs)", min_value=1, max_value=10, value=3)
    
    # Main content area
    if input_method == "Build New Squad from Watchlist":
        show_squad_builder()
    else:
        show_squad_input()
    
    # Analysis execution
    if st.button("🔍 Run FPL Analysis", type="primary"):
        run_analysis(input_method, prediction_week, planning_horizon)

def show_squad_builder():
    """Show interface for building a new squad from watchlist"""
    st.header("Build New Squad from Watchlist")
    
    col1, col2 = st.columns(2)
    
    with col1:
        budget = st.number_input("Total Budget (£M)", min_value=50.0, max_value=150.0, value=100.0, step=0.1)
        
    with col2:
        max_players_per_club = st.number_input("Max Players per Club", min_value=1, max_value=5, value=3)
    
    # Position constraints
    st.subheader("Squad Formation")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        num_gk = st.number_input("Goalkeepers", min_value=1, max_value=3, value=2)
    with col2:
        num_def = st.number_input("Defenders", min_value=3, max_value=7, value=5)
    with col3:
        num_mid = st.number_input("Midfielders", min_value=2, max_value=8, value=5)
    with col4:
        num_fwd = st.number_input("Forwards", min_value=1, max_value=5, value=3)
    
    total_players = num_gk + num_def + num_mid + num_fwd
    if total_players != 15:
        st.warning(f"Total players must be 15. Current total: {total_players}")
    
    st.session_state.squad_config = {
        'budget': budget,
        'max_per_club': max_players_per_club,
        'formation': {'GK': num_gk, 'DEF': num_def, 'MID': num_mid, 'FWD': num_fwd}
    }

def show_squad_input():
    """Show interface for inputting current squad"""
    st.header("Current 15-Player Squad Input")
    
    # Team status inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bank = st.number_input("Bank (£M)", min_value=0.0, max_value=50.0, value=0.0, step=0.1)
    with col2:
        free_transfers = st.number_input("Free Transfers Available", min_value=0, max_value=5, value=1)
    with col3:
        remaining_chips = st.multiselect(
            "Chips Remaining",
            ["Triple Captain", "Bench Boost", "Wildcard", "Free Hit"],
            default=["Triple Captain", "Bench Boost", "Wildcard", "Free Hit"]
        )
    
    # Squad input methods
    input_type = st.radio("Squad Input Method:", ["Manual Entry", "CSV Upload", "Text Import"])
    
    if input_type == "Manual Entry":
        show_manual_squad_entry()
    elif input_type == "CSV Upload":
        show_csv_upload()
    else:
        show_text_import()
    
    st.session_state.team_status = {
        'bank': bank,
        'free_transfers': free_transfers,
        'chips_remaining': remaining_chips
    }

def show_manual_squad_entry():
    """Show manual squad entry interface"""
    st.subheader("Manual Squad Entry")
    
    # Initialize squad in session state
    if 'current_squad' not in st.session_state:
        st.session_state.current_squad = []
    
    # Squad entry form
    with st.form("squad_entry"):
        positions = ["GK", "DEF", "MID", "FWD"]
        
        for i in range(15):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                player_name = st.text_input(f"Player {i+1} Name", key=f"name_{i}")
            with col2:
                position = st.selectbox(f"Position", positions, key=f"pos_{i}")
            with col3:
                club = st.text_input(f"Club", key=f"club_{i}")
            with col4:
                price = st.number_input(f"Price (£M)", min_value=3.5, max_value=15.0, value=4.0, step=0.1, key=f"price_{i}")
        
        if st.form_submit_button("Save Squad"):
            squad = []
            for i in range(15):
                if st.session_state[f"name_{i}"]:
                    squad.append({
                        'name': st.session_state[f"name_{i}"],
                        'position': st.session_state[f"pos_{i}"],
                        'club': st.session_state[f"club_{i}"],
                        'price': st.session_state[f"price_{i}"]
                    })
            st.session_state.current_squad = squad
            st.success(f"Squad saved with {len(squad)} players!")

def show_csv_upload():
    """Show CSV upload interface"""
    st.subheader("CSV Upload")
    
    uploaded_file = st.file_uploader("Choose CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("Uploaded data preview:")
            st.dataframe(df.head())
            
            # Validate required columns
            required_cols = ['name', 'position', 'club', 'price']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
            else:
                st.session_state.current_squad = df[required_cols].to_dict('records')
                st.success(f"Squad loaded with {len(df)} players!")
                
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")

def show_text_import():
    """Show text import interface"""
    st.subheader("Text Import")
    
    st.markdown("**Format:** Player Name, Position, Club, Price (one per line)")
    st.markdown("**Example:** Mohamed Salah, MID, Liverpool, 12.8")
    
    squad_text = st.text_area("Paste squad data:", height=300)
    
    if st.button("Parse Squad Data") and squad_text:
        try:
            squad = []
            lines = squad_text.strip().split('\n')
            
            for line in lines:
                if line.strip():
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 4:
                        squad.append({
                            'name': parts[0],
                            'position': parts[1],
                            'club': parts[2],
                            'price': float(parts[3])
                        })
            
            st.session_state.current_squad = squad
            st.success(f"Squad parsed with {len(squad)} players!")
            st.dataframe(pd.DataFrame(squad))
            
        except Exception as e:
            st.error(f"Error parsing squad data: {str(e)}")

def run_analysis(input_method, prediction_week, planning_horizon):
    """Run the FPL analysis and generate report"""
    
    try:
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize analysis engine
        engine = st.session_state.analysis_engine
        
        status_text.text("Initializing analysis...")
        progress_bar.progress(10)
        
        # Prepare input data
        if input_method == "Build New Squad from Watchlist":
            if 'squad_config' not in st.session_state:
                st.error("Please configure squad parameters first!")
                return
            input_data = st.session_state.squad_config
        else:
            if 'current_squad' not in st.session_state or not st.session_state.current_squad:
                st.error("Please provide your current squad first!")
                return
            if 'team_status' not in st.session_state:
                st.error("Please provide team status information!")
                return
            input_data = {
                'squad': st.session_state.current_squad,
                'team_status': st.session_state.team_status
            }
        
        # Run analysis
        status_text.text("Running FPL analysis...")
        progress_bar.progress(30)
        
        analysis_results = engine.run_full_analysis(
            input_data=input_data,
            input_method=input_method,
            prediction_week=prediction_week,
            planning_horizon=planning_horizon
        )
        
        progress_bar.progress(80)
        status_text.text("Generating report...")
        
        # Generate markdown report
        report_gen = ReportGenerator()
        markdown_report = report_gen.generate_report(analysis_results)
        
        # Save report to file
        with open('FPL_analysis.md', 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        # Display results
        st.success("✅ Analysis completed successfully!")
        
        # Show download button
        st.download_button(
            label="📁 Download FPL_analysis.md",
            data=markdown_report,
            file_name="FPL_analysis.md",
            mime="text/markdown"
        )
        
        # Display key results
        st.subheader("Analysis Summary")
        
        if 'final_recommendation' in analysis_results:
            st.markdown(f"**Recommended Action:** {analysis_results['final_recommendation']}")
        
        if 'risk_notes' in analysis_results:
            st.markdown("**Risk Notes:**")
            for note in analysis_results['risk_notes']:
                st.markdown(f"- {note}")
        
        # Show the markdown content
        st.subheader("Generated Analysis Report")
        st.markdown(markdown_report)
        
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()