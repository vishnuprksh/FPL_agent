#!/usr/bin/env python3
"""
Dash UI for FPL Transfer Optimizer

Interactive web interface to view current team, make changes, and optimize transfers.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import pandas as pd
from fpl_agent import FPLTransferOptimizer, FPLDatabase
import argparse
import sys
import os

# Import the squad optimizer
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from create_best_team import FPLSquadOptimizer

# Constants
DB_PATH = "/workspaces/FPL_agent/data/fpl_agent.db"
POSITION_LIMITS = {'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}
BUDGET = 100.0

# Global variable for num_weeks (will be set from command line args)
NUM_WEEKS = 3

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Load available players
db = FPLDatabase(DB_PATH)
all_players = db.load_player_data(num_weeks=NUM_WEEKS)

# Load team names mapping
with db.get_connection() as conn:
    teams_df = pd.read_sql_query("SELECT DISTINCT team, team_name FROM elements ORDER BY team", conn)
    team_id_to_name = dict(zip(teams_df['team'], teams_df['team_name']))
    team_name_to_id = dict(zip(teams_df['team_name'], teams_df['team']))

# Load team from database
def load_team_from_db():
    """Load current team from database or return empty team structure."""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if current_team table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='current_team'
            """)
            
            if not cursor.fetchone():
                print("No current_team table found. Creating optimized team...")
                return create_optimal_team()
            
            # Load team data
            team_df = pd.read_sql_query("""
                SELECT player_id, player_name, position, team_id, is_starter
                FROM current_team
                ORDER BY 
                    CASE position 
                        WHEN 'GK' THEN 1 
                        WHEN 'DEF' THEN 2 
                        WHEN 'MID' THEN 3 
                        WHEN 'FWD' THEN 4 
                    END,
                    is_starter DESC
            """, conn)
            
            if team_df.empty:
                print("current_team table is empty. Creating optimized team...")
                return create_optimal_team()
            
            # Convert to team structure
            team_structure = {"team": []}
            for position in ['GK', 'DEF', 'MID', 'FWD']:
                pos_players = team_df[team_df['position'] == position]
                if not pos_players.empty:
                    team_structure["team"].append({
                        "position": position,
                        "players": [
                            {
                                "id": int(row['player_id']),
                                "name": row['player_name'],
                                "team": int(row['team_id']),
                                "is_starter": bool(row['is_starter'])
                            }
                            for _, row in pos_players.iterrows()
                        ]
                    })
            
            return team_structure
            
    except Exception as e:
        print(f"Error loading team from database: {e}")
        return {"team": []}

def create_optimal_team():
    """Create an optimal team using the FPL Squad Optimizer."""
    try:
        # Refresh all_players data to ensure we have latest predictions
        global all_players
        all_players = db.load_player_data(num_weeks=NUM_WEEKS)
        print(f"Refreshed player data: {len(all_players)} players loaded")
        
        print(f"Running squad optimizer with {NUM_WEEKS} weeks of predictions...")
        optimizer = FPLSquadOptimizer(DB_PATH, epsilon=0.001, num_weeks=NUM_WEEKS)
        results = optimizer.solve()
        
        # Convert optimizer results to team structure
        squad_df = results['squad']
        starting_df = results['starting_xi']
        
        # Save to database
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop existing current_team table completely to ensure clean slate
            cursor.execute("DROP TABLE IF EXISTS current_team")
            
            # Create current_team table fresh
            cursor.execute("""
                CREATE TABLE current_team (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    player_name TEXT,
                    position TEXT,
                    team_id INTEGER,
                    team_name TEXT,
                    price REAL,
                    predicted_points REAL,
                    is_starter BOOLEAN,
                    saved_at TIMESTAMP,
                    team_cost REAL,
                    team_points REAL
                )
            """)
            
            # Get team names
            teams_df = pd.read_sql_query("SELECT DISTINCT team, team_name FROM elements ORDER BY team", conn)
            team_id_to_name_local = dict(zip(teams_df['team'], teams_df['team_name']))
            
            total_cost = squad_df['price'].sum()
            total_points = starting_df['predicted_points'].sum()
            
            # Insert new team data
            for _, row in squad_df.iterrows():
                is_starter = row['id'] in starting_df['id'].values
                cursor.execute("""
                    INSERT INTO current_team (
                        player_id, player_name, position, team_id, team_name,
                        price, predicted_points, is_starter, saved_at,
                        team_cost, team_points
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['id']), row['name'], row['position'], int(row['team']),
                    team_id_to_name_local.get(row['team'], f"Team {row['team']}"),
                    row['price'], row['predicted_points'],
                    is_starter, timestamp, total_cost, total_points
                ))
            
            conn.commit()
        
        print(f"✅ Optimized team created and saved! Cost: £{total_cost:.1f}m, Points: {total_points:.2f}")
        
        # Return team structure
        team_structure = {"team": []}
        for position in ['GK', 'DEF', 'MID', 'FWD']:
            pos_players = squad_df[squad_df['position'] == position]
            if not pos_players.empty:
                team_structure["team"].append({
                    "position": position,
                    "players": [
                        {
                            "id": int(row['id']),
                            "name": row['name'],
                            "team": int(row['team']),
                            "is_starter": bool(row['id'] in starting_df['id'].values)
                        }
                        for _, row in pos_players.iterrows()
                    ]
                })
        
        return team_structure
        
    except Exception as e:
        print(f"Error creating optimal team: {e}")
        import traceback
        traceback.print_exc()
        return {"team": []}

def team_json_to_dataframe(team_json):
    """Convert team JSON to DataFrame with enriched data.
    
    Note: predicted_points comes from all_players DataFrame, which contains
    the SUM of predictions for the next NUM_WEEKS gameweeks.
    """
    if not team_json or not team_json.get('team'):
        return pd.DataFrame(columns=['id', 'name', 'position', 'team', 'team_name', 'price', 'predicted_points', 'is_starter'])
    
    players_list = []
    for pos_data in team_json['team']:
        position = pos_data['position']
        for player in pos_data['players']:
            player_info = all_players[all_players['id'] == player['id']]
            if not player_info.empty:
                player_row = player_info.iloc[0]
                players_list.append({
                    'id': player['id'],
                    'name': player_row['name'],
                    'position': position,
                    'team': player_row['team'],
                    'team_name': team_id_to_name.get(player_row['team'], f"Team {player_row['team']}"),
                    'price': player_row['price'],
                    'predicted_points': player_row['predicted_points'],  # Sum of next NUM_WEEKS
                    'is_starter': player.get('is_starter', True)
                })
            else:
                print(f"Warning: Player ID {player['id']} not found in all_players DataFrame")
    
    if not players_list:
        return pd.DataFrame(columns=['id', 'name', 'position', 'team', 'team_name', 'price', 'predicted_points', 'is_starter'])
    
    return pd.DataFrame(players_list)

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("⚽ FPL Transfer Optimizer", className="text-center my-4"),
            html.Hr()
        ])
    ]),
    
    # Store for team data
    dcc.Store(id='team-store', data=load_team_from_db()),
    dcc.Interval(id='interval-reload', interval=1000, n_intervals=0, max_intervals=1),
    dcc.Store(id='copy-notification', data=''),
    
    # Team Display Section
    dbc.Row([
        dbc.Col([
            html.H3("Current Team", className="mb-3"),
            dbc.Button("🔄 Create Optimal Team", id='create-optimal-button', color="secondary", className="mb-3"),
            html.Div(id='team-summary', className="mb-3"),
            html.Div(id='team-display')
        ], width=12)
    ]),
    
    # Replace Player Section
    dbc.Row([
        dbc.Col([
            html.H3("Replace Player", className="mt-4 mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Select Player to Replace:"),
                    dcc.Dropdown(id='player-to-replace-dropdown', placeholder="Select player...")
                ], width=6),
                dbc.Col([
                    html.Label("Replace With:"),
                    dcc.Dropdown(id='replacement-player-dropdown', placeholder="Select replacement...")
                ], width=6)
            ]),
            dbc.Button("Replace Player", id='replace-button', color="primary", className="mt-3"),
            html.Div(id='edit-message', className="mt-2")
        ], width=12)
    ]),
    
    # Substitute Player Section
    dbc.Row([
        dbc.Col([
            html.H3("Substitute Player", className="mt-4 mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Remove from Starting XI:"),
                    dcc.Dropdown(id='player-to-bench-dropdown', placeholder="Select starting player...")
                ], width=6),
                dbc.Col([
                    html.Label("Add to Starting XI:"),
                    dcc.Dropdown(id='player-to-start-dropdown', placeholder="Select bench player...")
                ], width=6)
            ]),
            dbc.Button("Substitute Player", id='substitute-button', color="warning", className="mt-3"),
            html.Div(id='substitute-message', className="mt-2")
        ], width=12)
    ]),
    
    # Save Section
    dbc.Row([
        dbc.Col([
            html.Hr(className="my-4"),
            dbc.Button("Save Team to Database", id='save-team-button', color="info", size="lg", className="w-100"),
            html.Div(id='save-message', className="mt-3")
        ], width=12)
    ]),
    
    # LLM Analysis Section
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.H3("AI-Powered Team Analysis", className="mb-3"),
            html.P("Copy the prompt with your team data to use with your favourite LLM (ChatGPT, Claude, etc.)", className="text-muted"),
            dbc.Row([
                dbc.Col([
                    html.Label("Prompt + Team Data (Ready to Copy):", className="fw-bold"),
                    dcc.Textarea(
                        id='llm-combined-export',
                        placeholder="Combined prompt and team data will appear here...",
                        style={'width': '100%', 'height': '400px', 'fontFamily': 'monospace', 'fontSize': '12px'}
                    )
                ], width=12)
            ])
        ], width=12)
    ]),
    
    # Optimize Section
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.H3("Transfer Suggestions", className="mb-3"),
            dbc.Button("Optimize Transfers", id='optimize-button', color="success", size="lg", className="mb-3"),
            html.Div(id='optimization-results')
        ], width=12)
    ])
], fluid=True, className="p-4")

@callback(
    Output('team-store', 'data', allow_duplicate=True),
    Input('interval-reload', 'n_intervals'),
    prevent_initial_call='initial_duplicate'
)
def reload_team_on_startup(n):
    """Reload team from database when page loads or refreshes."""
    return load_team_from_db()

@callback(
    Output('team-store', 'data', allow_duplicate=True),
    Input('create-optimal-button', 'n_clicks'),
    prevent_initial_call=True
)
def create_new_optimal_team(n_clicks):
    """Create a new optimal team when button is clicked."""
    if not n_clicks:
        return dash.no_update
    
    print("User requested new optimal team...")
    return create_optimal_team()

@callback(
    Output('team-summary', 'children'),
    Output('team-display', 'children'),
    Output('player-to-replace-dropdown', 'options'),
    Output('player-to-bench-dropdown', 'options'),
    Output('player-to-start-dropdown', 'options'),
    Input('team-store', 'data')
)
def update_team_display(team_data):
    """Update the team display when team data changes."""
    if not team_data:
        return "", "", [], [], []
    
    team_df = team_json_to_dataframe(team_data)
    
    # Handle empty team
    if team_df.empty:
        return dbc.Alert("No team loaded. Please create a team first.", color="warning"), "", [], [], []
    
    total_cost = team_df['price'].sum()
    starting_points = team_df[team_df['is_starter']]['predicted_points'].sum()
    
    # Summary
    summary = dbc.Alert([
        html.H5(f"Total Cost: £{total_cost:.1f}m / £{BUDGET:.1f}m", className="mb-1"),
        html.H5(f"Starting XI Points (next {NUM_WEEKS} weeks): {starting_points:.2f}", className="mb-0")
    ], color="info")
    
    # Create tables by position
    tables = []
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        pos_df = team_df[team_df['position'] == position].copy()
        if not pos_df.empty:
            pos_df = pos_df.sort_values('is_starter', ascending=False)
            tables.append(html.H5(f"{position} ({len(pos_df)}/{POSITION_LIMITS[position]})", className="mt-3"))
            tables.append(dash_table.DataTable(
                data=pos_df.to_dict('records'),
                columns=[
                    {'name': 'Name', 'id': 'name'},
                    {'name': 'Team', 'id': 'team_name'},
                    {'name': 'Price (£m)', 'id': 'price', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': f'Predicted Points ({NUM_WEEKS}w)', 'id': 'predicted_points', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Starter', 'id': 'is_starter', 'type': 'text'}
                ],
                style_data_conditional=[
                    {'if': {'filter_query': '{is_starter} = true'}, 'backgroundColor': '#c3f0ca'},
                    {'if': {'filter_query': '{is_starter} = false'}, 'backgroundColor': "#7fd5ba"}
                ],
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'minWidth': '100px',
                    'maxWidth': '180px',
                    'whiteSpace': 'normal'
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'name'}, 'width': '25%'},
                    {'if': {'column_id': 'team_name'}, 'width': '20%', 'textAlign': 'left'},
                    {'if': {'column_id': 'price'}, 'width': '20%', 'textAlign': 'right'},
                    {'if': {'column_id': 'predicted_points'}, 'width': '25%', 'textAlign': 'right'},
                    {'if': {'column_id': 'is_starter'}, 'width': '10%', 'textAlign': 'center'}
                ],
                style_header={
                    'backgroundColor': '#007bff',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'padding': '12px'
                },
                style_table={'overflowX': 'auto'}
            ))
    
    # Dropdown options for player replacement
    all_player_options = [
        {'label': f"{row['name']} ({row['position']}) - £{row['price']:.1f}m", 'value': row['id']}
        for _, row in team_df.iterrows()
    ]
    
    # Dropdown options for starting XI players (to bench)
    starting_players = [
        {'label': f"{row['name']} ({row['position']}) - £{row['price']:.1f}m", 'value': row['id']}
        for _, row in team_df[team_df['is_starter']].iterrows()
    ]
    
    # Dropdown options for bench players (to start)
    bench_players = [
        {'label': f"{row['name']} ({row['position']}) - £{row['price']:.1f}m", 'value': row['id']}
        for _, row in team_df[~team_df['is_starter']].iterrows()
    ]
    
    return summary, html.Div(tables), all_player_options, starting_players, bench_players

@callback(
    Output('replacement-player-dropdown', 'options'),
    Input('player-to-replace-dropdown', 'value'),
    State('team-store', 'data')
)
def update_replacement_options(selected_player_id, team_data):
    """Update replacement dropdown to show all available players from any position."""
    if not team_data:
        return []
    
    team_df = team_json_to_dataframe(team_data)
    current_team_ids = team_df['id'].tolist()
    
    # Get all available players not in current team
    available = all_players[
        ~all_players['id'].isin(current_team_ids)
    ].copy()
    
    # Sort by position then price
    available = available.sort_values(['position', 'price'], ascending=[True, True])
    
    replacement_options = [
        {
            'label': f"{row['name']} ({row['position']}) - {team_id_to_name.get(row['team'], 'Unknown')} - £{row['price']:.1f}m, {row['predicted_points']:.2f}pts ({NUM_WEEKS}w)",
            'value': row['id']
        }
        for _, row in available.iterrows()
    ]
    
    return replacement_options

@callback(
    Output('team-store', 'data', allow_duplicate=True),
    Output('edit-message', 'children'),
    Input('replace-button', 'n_clicks'),
    State('player-to-replace-dropdown', 'value'),
    State('replacement-player-dropdown', 'value'),
    State('team-store', 'data'),
    prevent_initial_call=True
)
def replace_player(n_clicks, old_player_id, new_player_id, team_data):
    """Replace a player in the team, allowing cross-position transfers."""
    if not n_clicks or not old_player_id or not new_player_id:
        return team_data, ""
    
    team_df = team_json_to_dataframe(team_data)
    old_player = team_df[team_df['id'] == old_player_id].iloc[0]
    new_player = all_players[all_players['id'] == new_player_id].iloc[0]
    
    # Validate budget
    cost_change = new_player['price'] - old_player['price']
    new_total_cost = team_df['price'].sum() + cost_change
    
    if new_total_cost > BUDGET:
        return team_data, dbc.Alert(
            f"❌ Cannot make transfer: Would exceed budget by £{new_total_cost - BUDGET:.1f}m",
            color="danger"
        )
    
    # Validate position limits
    position_counts = team_df['position'].value_counts().to_dict()
    if new_player['position'] != old_player['position']:
        position_counts[old_player['position']] = position_counts.get(old_player['position'], 0) - 1
        position_counts[new_player['position']] = position_counts.get(new_player['position'], 0) + 1
        
        for pos, limit in POSITION_LIMITS.items():
            if position_counts.get(pos, 0) > limit:
                return team_data, dbc.Alert(
                    f"⚠️ Cannot make transfer: Would have {position_counts[pos]} {pos} players (max {limit})",
                    color="warning"
                )
            if position_counts.get(pos, 0) < (2 if pos == 'GK' else 0):
                return team_data, dbc.Alert(
                    f"⚠️ Cannot make transfer: Would have {position_counts.get(pos, 0)} {pos} players (min {2 if pos == 'GK' else 1})",
                    color="warning"
                )
    
    # Validate team constraint
    team_counts = team_df['team'].value_counts().to_dict()
    if new_player['team'] != old_player['team']:
        team_counts[old_player['team']] = team_counts.get(old_player['team'], 0) - 1
        team_counts[new_player['team']] = team_counts.get(new_player['team'], 0) + 1
        if team_counts.get(new_player['team'], 0) > 3:
            return team_data, dbc.Alert(
                f"⚠️ Cannot make transfer: Would have {team_counts[new_player['team']]} players from {team_id_to_name.get(new_player['team'], 'team')} (max 3 per team)",
                color="warning"
            )
    
    # Rebuild team structure with new player
    # Remove old player from team_df and add new player
    team_df = team_df[team_df['id'] != old_player_id]
    new_player_row = {
        'id': int(new_player['id']),
        'name': new_player['name'],
        'position': new_player['position'],
        'team': int(new_player['team']),
        'team_name': team_id_to_name.get(new_player['team'], f"Team {new_player['team']}"),
        'price': new_player['price'],
        'predicted_points': new_player['predicted_points'],
        'is_starter': old_player['is_starter']  # Keep starter status
    }
    team_df = pd.concat([team_df, pd.DataFrame([new_player_row])], ignore_index=True)
    
    # Rebuild team structure
    new_team_data = {'team': []}
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        pos_players = team_df[team_df['position'] == position]
        if not pos_players.empty:
            new_team_data['team'].append({
                'position': position,
                'players': [
                    {
                        'id': int(row['id']),
                        'name': row['name'],
                        'team': int(row['team']),
                        'is_starter': bool(row['is_starter'])
                    }
                    for _, row in pos_players.iterrows()
                ]
            })
    
    message = dbc.Alert(
        f"✅ Replaced {old_player['name']} ({old_player['position']}) with {new_player['name']} ({new_player['position']}) | Cost: £{cost_change:+.1f}m",
        color="success"
    )
    
    return new_team_data, message

@callback(
    Output('team-store', 'data', allow_duplicate=True),
    Output('substitute-message', 'children'),
    Input('substitute-button', 'n_clicks'),
    State('player-to-bench-dropdown', 'value'),
    State('player-to-start-dropdown', 'value'),
    State('team-store', 'data'),
    prevent_initial_call=True
)
def substitute_player(n_clicks, starter_id, bench_id, team_data):
    """Substitute a starting player with a bench player, allowing cross-position subs if restrictions allow."""
    if not n_clicks or not starter_id or not bench_id:
        return team_data, ""
    
    team_df = team_json_to_dataframe(team_data)
    starter = team_df[team_df['id'] == starter_id].iloc[0]
    bench = team_df[team_df['id'] == bench_id].iloc[0]
    
    # Verify one is starter and one is bench
    if not starter['is_starter']:
        return team_data, dbc.Alert(
            "⚠️ Player selected for benching is not in the starting XI",
            color="warning"
        )
    
    if bench['is_starter']:
        return team_data, dbc.Alert(
            "⚠️ Player selected to start is already in the starting XI",
            color="warning"
        )
    
    # No position limit validation needed for substitution (same players stay on team)
    # Only starter status changes, not positions or total count
    
    # Swap starter status between the two players
    starter_status = team_df.loc[team_df['id'] == starter_id, 'is_starter'].values[0]
    bench_status = team_df.loc[team_df['id'] == bench_id, 'is_starter'].values[0]
    team_df.loc[team_df['id'] == starter_id, 'is_starter'] = bench_status
    team_df.loc[team_df['id'] == bench_id, 'is_starter'] = starter_status
    
    # Rebuild team structure
    new_team_data = {'team': []}
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        pos_players = team_df[team_df['position'] == position]
        if not pos_players.empty:
            new_team_data['team'].append({
                'position': position,
                'players': [
                    {
                        'id': int(row['id']),
                        'name': row['name'],
                        'team': int(row['team']),
                        'is_starter': bool(row['is_starter'])
                    }
                    for _, row in pos_players.iterrows()
                ]
            })
    
    message = dbc.Alert(
        f"✅ Substituted {starter['name']} with {bench['name']} in starting XI",
        color="success"
    )
    
    return new_team_data, message

@callback(
    Output('save-message', 'children'),
    Input('save-team-button', 'n_clicks'),
    State('team-store', 'data'),
    prevent_initial_call=True
)
def save_team_to_db(n_clicks, team_data):
    """Save current team to database."""
    if not n_clicks or not team_data:
        return ""
    
    try:
        from datetime import datetime
        import sqlite3
        
        team_df = team_json_to_dataframe(team_data)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create current_team table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS current_team (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    player_name TEXT,
                    position TEXT,
                    team_id INTEGER,
                    team_name TEXT,
                    price REAL,
                    predicted_points REAL,
                    is_starter BOOLEAN,
                    saved_at TIMESTAMP,
                    team_cost REAL,
                    team_points REAL
                )
            """)
            
            total_cost = team_df['price'].sum()
            total_points = team_df[team_df['is_starter']]['predicted_points'].sum()
            
            # Delete existing team data
            cursor.execute("DELETE FROM current_team")
            
            # Insert new team data
            for _, row in team_df.iterrows():
                cursor.execute("""
                    INSERT INTO current_team (
                        player_id, player_name, position, team_id, team_name,
                        price, predicted_points, is_starter, saved_at,
                        team_cost, team_points
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['id'], row['name'], row['position'], row['team'],
                    row['team_name'], row['price'], row['predicted_points'],
                    row['is_starter'], timestamp, total_cost, total_points
                ))
            
            conn.commit()
        
        return dbc.Alert(
            f"✅ Team saved successfully at {timestamp}! Total Cost: £{total_cost:.1f}m, Starting XI Points: {total_points:.2f}",
            color="success"
        )
        
    except Exception as e:
        return dbc.Alert(f"❌ Error saving team: {str(e)}", color="danger")

@callback(
    Output('optimization-results', 'children'),
    Input('optimize-button', 'n_clicks'),
    State('team-store', 'data'),
    prevent_initial_call=True
)
def optimize_transfers(n_clicks, team_data):
    """Run transfer optimization on current team to get top 5 transfers."""
    if not n_clicks:
        return ""
    
    try:
        optimizer = FPLTransferOptimizer(DB_PATH)
        result = optimizer.find_best_transfer(team_data, num_weeks=NUM_WEEKS)
        
        if result['no_transfer_recommended']:
            return dbc.Alert([
                html.H4("🚫 No Transfers Recommended", className="mb-3"),
                html.P("Your current team is already optimal or no beneficial transfers available within budget.")
            ], color="info")
        
        transfers = result['best_transfers']
        transfer_cards = []
        
        for idx, transfer in enumerate(transfers, 1):
            card = dbc.Card([
                dbc.CardHeader(f"Transfer #{idx}", className="bg-primary text-white"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6("OUT:", className="text-danger fw-bold"),
                            html.P([
                                html.Strong(f"{transfer['out']['name']}"),
                                html.Br(),
                                f"({transfer['out']['position']}) - {team_id_to_name.get(transfer['out']['team'], 'Unknown')}",
                                html.Br(),
                                f"£{transfer['out']['price']:.1f}m, {transfer['out']['predicted_points']:.2f} pts ({NUM_WEEKS}w)"
                            ], className="mb-0 small")
                        ], width=6),
                        dbc.Col([
                            html.H6("IN:", className="text-success fw-bold"),
                            html.P([
                                html.Strong(f"{transfer['in']['name']}"),
                                html.Br(),
                                f"({transfer['in']['position']}) - {team_id_to_name.get(transfer['in']['team'], 'Unknown')}",
                                html.Br(),
                                f"£{transfer['in']['price']:.1f}m, {transfer['in']['predicted_points']:.2f} pts ({NUM_WEEKS}w)"
                            ], className="mb-0 small")
                        ], width=6)
                    ]),
                    html.Hr(className="my-2"),
                    dbc.Row([
                        dbc.Col([
                            html.P([
                                html.Strong("💰 Cost: "),
                                f"£{transfer['cost_change']:+.1f}m"
                            ], className="mb-1 small")
                        ], width=6),
                        dbc.Col([
                            html.P([
                                html.Strong("📈 Gain: "),
                                f"{transfer['points_gain']:+.2f} pts ({NUM_WEEKS}w)"
                            ], className="mb-0 small")
                        ], width=6)
                    ])
                ])
            ], className="mb-2")
            transfer_cards.append(card)
        
        return dbc.Container([
            html.H4("✅ Top 5 Transfer Recommendations", className="mb-3 text-success"),
            html.Div(transfer_cards)
        ], fluid=True)
        
    except Exception as e:
        return dbc.Alert(f"❌ Error: {str(e)}", color="danger")

@callback(
    Output('llm-combined-export', 'value'),
    Input('team-store', 'data')
)
def update_combined_export(team_data):
    """Update combined prompt + team data export (all players including bench)."""
    if not team_data or not team_data.get('team'):
        return ""
    
    import json
    
    # Include all players (starting XI and bench)
    team_json = json.dumps(team_data, indent=2)
    
    prompt = """Analyse the following team for FPL for the game week ahead,
Based on the upcoming week fixture, fitness, rotation risk, player form, opponent strength, position and strategies recalculate the predicted points of the team.
Based on the recalculated data, suggest whether to HOLD, or SELL each player in the team. If have to SELL, suggest the best replacement player considering budge and team constraints.

---

TEAM DATA (JSON):
"""
    
    return prompt + "\n" + team_json

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run FPL Transfer Optimizer UI')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument(
        '--weeks',
        type=int,
        default=3,
        help='Number of weeks to consider for predictions (default: 3)'
    )
    args = parser.parse_args()
    
    # Update NUM_WEEKS from command line argument
    NUM_WEEKS = args.weeks
    
    # Reload players with the specified number of weeks
    all_players = db.load_player_data(num_weeks=NUM_WEEKS)
    
    print(f"Starting FPL Transfer Optimizer UI with {NUM_WEEKS} weeks of predictions...")
    print(f"Loaded {len(all_players)} players with predictions")
    print(f"Sample predicted points: {all_players['predicted_points'].describe()}")
    
    app.run(debug=args.debug, host='0.0.0.0', port=8050)
