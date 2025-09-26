"""
Calculation functions for player performance predictions using linear regression.

This module provides functions to predict player performance based on historical
fixture difficulty and total points scored in recent matches.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import sqlite3
from datetime import datetime
from fpl_agent.database_connection import get_connection


def get_current_gameweek_context(season: str = '2025-26'):
    """
    Get the current gameweek context for predictions.
    
    Args:
        season: Season to check
        
    Returns:
        dict with current_gw, next_gws, and training_range info
    """
    conn = get_connection()
    
    # Find the latest gameweek with data
    query = """
    SELECT MAX(round) as latest_gw
    FROM player_history 
    WHERE season = ?
    """
    
    result = pd.read_sql_query(query, conn, params=(season,))
    conn.close()
    
    latest_gw = result['latest_gw'].iloc[0] if len(result) > 0 and result['latest_gw'].iloc[0] is not None else 0
    
    # Next 3 gameweeks to predict
    next_gws = [latest_gw + 1, latest_gw + 2, latest_gw + 3]
    
    # For training, we want the last 10 gameweeks before the prediction gameweeks
    # But we need to ensure we don't go below gameweek 1
    training_start_gw = max(1, latest_gw - 9)  # -9 because latest_gw is included (10 total)
    training_end_gw = latest_gw
    
    return {
        'current_gw': latest_gw,
        'next_gws': next_gws,
        'training_start_gw': training_start_gw,
        'training_end_gw': training_end_gw,
        'season': season
    }


def get_player_recent_history(player_code: int, num_matches: int = 10, season: str = '2025-26'):
    """
    Retrieve the most recent match history for a player based on actual gameweeks.
    
    Args:
        player_code: Unique player code
        num_matches: Number of recent matches to retrieve
        season: Season to look for data
        
    Returns:
        DataFrame with recent match history including fixture_difficulty, total_points, round, and match_number
    """
    # Get current gameweek context
    gw_context = get_current_gameweek_context(season)
    
    conn = get_connection()
    
    # Get matches from the training range (last 10 gameweeks before prediction)
    query = """
    SELECT fixture_difficulty, total_points, round
    FROM player_history 
    WHERE player_code = ? AND season = ? AND total_points IS NOT NULL
    AND round >= ? AND round <= ?
    ORDER BY round DESC 
    LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=(
        player_code, season, 
        gw_context['training_start_gw'], 
        gw_context['training_end_gw'], 
        num_matches
    ))
    
    if len(df) > 0:
        # Add match number feature relative to the prediction gameweeks
        # Most recent match gets the highest number, older matches get lower numbers
        df = df.reset_index(drop=True)
        df['match_number'] = gw_context['training_end_gw'] - df['round'] + 1
        # Sort by round ascending so match_number increases with time
        df = df.sort_values('round').reset_index(drop=True)
    
    conn.close()
    
    return df


def fit_linear_model(player_code: int, num_matches: int = 10, season: str = '2025-26'):
    """
    Fit a linear regression model to predict total_points based on fixture_difficulty and match_number.
    
    Args:
        player_code: Unique player code
        num_matches: Number of recent matches to use for training
        season: Season to look for data
        
    Returns:
        dict with model, r2_score, and number of matches used
    """
    history_df = get_player_recent_history(player_code, num_matches, season)
    
    if len(history_df) < 3:
        # Need at least 3 data points for multiple linear regression with 2 features
        return None
    
    # Prepare features (fixture difficulty and match number) and target
    X = history_df[['fixture_difficulty', 'match_number']].values
    y = history_df['total_points'].values
    
    # Fit linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R² score
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    return {
        'model': model,
        'r2_score': r2,
        'matches_used': len(history_df),
        'feature_data': X,
        'target_data': y
    }


def predict_next_matches(player_code: int, fdr_values: list = [3, 3, 3], season: str = '2025-26'):
    """
    Predict total points for the next matches using the fitted linear model.
    Uses both fixture difficulty and gameweek number as features.
    
    Args:
        player_code: Unique player code
        fdr_values: List of fixture difficulty ratings for next matches
        season: Season to look for training data
        
    Returns:
        dict with predictions and model info
    """
    # Get current gameweek context
    gw_context = get_current_gameweek_context(season)
    
    model_info = fit_linear_model(player_code, season=season)
    
    if model_info is None:
        return None
    
    model = model_info['model']
    
    # Predict for each fixture difficulty using the actual next gameweeks
    predictions = []
    for i, fdr in enumerate(fdr_values):
        next_gw = gw_context['next_gws'][i]  # Actual gameweek number (6, 7, 8)
        # Use the gameweek number relative to training end
        match_number = next_gw - gw_context['training_end_gw']  # This will be 1, 2, 3 for GW6, 7, 8
        pred = model.predict([[fdr, match_number]])[0]
        # Ensure prediction is not negative
        pred = max(0, pred)
        predictions.append(round(pred, 2))
    
    return {
        'predictions': predictions,
        'total_predicted': round(sum(predictions), 2),
        'r2_score': model_info['r2_score'],
        'matches_used': model_info['matches_used'],
        'predicted_gameweeks': gw_context['next_gws'],
        'training_gameweeks': f"GW{gw_context['training_start_gw']}-{gw_context['training_end_gw']}"
    }


def get_all_active_players(season: str = '2025-26'):
    """
    Get all active players with their names and team information.
    Excludes managers (element_type = 5) to only include actual players.
    For seasons where player metadata doesn't exist, uses the previous season's data.
    
    Args:
        season: Season to look for players
        
    Returns:
        DataFrame with player_code, player_name, and team info
    """
    conn = get_connection()
    
    # First, try to get players from the specified season
    query_current = """
    SELECT DISTINCT p.player_code, 
           p.first_name || ' ' || p.second_name as player_name,
           t.name as team_name
    FROM players p
    LEFT JOIN teams t ON p.team = t.id
    WHERE p.season = ? AND p.player_code IS NOT NULL 
    AND p.element_type IN (1, 2, 3, 4)
    """
    
    df = pd.read_sql_query(query_current, conn, params=(season,))
    
    # If no players found in the current season, use previous season's data
    # but only for players who have match history in the current season
    if len(df) == 0:
        # Determine previous season
        if season == '2025-26':
            prev_season = '2024-25'
        elif season == '2024-25':
            prev_season = '2023-24'
        else:
            prev_season = '2024-25'  # Default fallback
        
        query_with_history = """
        SELECT DISTINCT p.player_code, 
               p.first_name || ' ' || p.second_name as player_name,
               t.name as team_name
        FROM players p
        LEFT JOIN teams t ON p.team = t.id
        WHERE p.season = ? AND p.player_code IS NOT NULL 
        AND p.element_type IN (1, 2, 3, 4)
        AND p.player_code IN (
            SELECT DISTINCT player_code 
            FROM player_history 
            WHERE season = ?
        )
        """
        
        df = pd.read_sql_query(query_with_history, conn, params=(prev_season, season))
    
    conn.close()
    
    return df


def generate_all_predictions(season: str = '2025-26', fdr_values: list = [3, 3, 3]):
    """
    Generate predictions for all active players and store in the database.
    
    Args:
        season: Season to generate predictions for
        fdr_values: List of fixture difficulty ratings for next matches
        
    Returns:
        Number of successful predictions generated
    """
    players_df = get_all_active_players(season)
    conn = get_connection()
    c = conn.cursor()
    
    # Clear existing predictions for this season
    c.execute('DELETE FROM predictions WHERE season = ?', (season,))
    
    successful_predictions = 0
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for _, player_row in players_df.iterrows():
        player_code = player_row['player_code']
        player_name = player_row['player_name']
        team_name = player_row['team_name']
        
        try:
            prediction_result = predict_next_matches(player_code, fdr_values, season)
            
            if prediction_result is not None:
                predictions = prediction_result['predictions']
                total_pred = prediction_result['total_predicted']
                r2 = prediction_result['r2_score']
                matches_used = prediction_result['matches_used']
                
                # Insert prediction into database
                c.execute('''INSERT OR REPLACE INTO predictions 
                           (player_code, player_name, team_name, 
                            predicted_gw1_points, predicted_gw2_points, predicted_gw3_points,
                            total_predicted_points, model_r2_score, matches_used, 
                            prediction_date, season)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (player_code, player_name, team_name,
                          predictions[0], predictions[1], predictions[2],
                          total_pred, r2, matches_used, current_date, season))
                
                successful_predictions += 1
                
        except Exception as e:
            print(f"Error predicting for player {player_name} (code: {player_code}): {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Generated {successful_predictions} predictions out of {len(players_df)} players")
    return successful_predictions


def get_predictions_summary(season: str = '2025-26', limit: int = 1000):
    """
    Retrieve prediction results from the database.
    Only includes actual players (excludes managers).
    
    Args:
        season: Season to get predictions for
        limit: Maximum number of results to return
        
    Returns:
        DataFrame with prediction results sorted by total predicted points
    """
    conn = get_connection()
    
    query = """
    SELECT pred.player_code, pred.player_name, pred.team_name, 
           pred.predicted_gw1_points, pred.predicted_gw2_points, pred.predicted_gw3_points,
           pred.total_predicted_points, pred.model_r2_score, pred.matches_used, pred.prediction_date
    FROM predictions pred
    JOIN players p ON pred.player_code = p.player_code
    WHERE pred.season = ? AND p.element_type IN (1, 2, 3, 4)
    ORDER BY pred.total_predicted_points DESC
    LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=(season, limit))
    conn.close()
    
    return df


def clean_manager_predictions(season: str = '2025-26'):
    """
    Remove manager predictions from the predictions table.
    Managers have element_type = 5 and shouldn't be included in predictions.
    
    Args:
        season: Season to clean predictions for
        
    Returns:
        Number of manager predictions removed
    """
    conn = get_connection()
    c = conn.cursor()
    
    # Find and count manager predictions
    count_query = """
    SELECT COUNT(*) FROM predictions pred 
    JOIN players p ON pred.player_code = p.player_code 
    WHERE pred.season = ? AND p.element_type = 5
    """
    
    c.execute(count_query, (season,))
    manager_count = c.fetchone()[0]
    
    # Remove manager predictions
    delete_query = """
    DELETE FROM predictions 
    WHERE season = ? AND player_code IN (
        SELECT player_code FROM players WHERE element_type = 5
    )
    """
    
    c.execute(delete_query, (season,))
    conn.commit()
    conn.close()
    
    print(f"Removed {manager_count} manager predictions from the database")
    return manager_count