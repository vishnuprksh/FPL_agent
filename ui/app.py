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

# Constants
DB_PATH = "/workspaces/FPL_agent/data/fpl_agent.db"
POSITION_LIMITS = {'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}
BUDGET = 100.0

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Load available players
db = FPLDatabase(DB_PATH)
all_players = db.load_player_data()

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
                return {"team": []}
            
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
                return {"team": []}
            
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

def team_json_to_dataframe(team_json):
    """Convert team JSON to DataFrame with enriched data."""
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
                    'predicted_points': player_row['predicted_points'],
                    'is_starter': player.get('is_starter', True)
                })
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
    
    # Team Display Section
    dbc.Row([
        dbc.Col([
            html.H3("Current Team", className="mb-3"),
            html.Div(id='team-summary', className="mb-3"),
            html.Div(id='team-display')
        ], width=12)
    ]),
    
    # Edit Team Section
    dbc.Row([
        dbc.Col([
            html.H3("Modify Team", className="mt-4 mb-3"),
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
            dbc.Button("Replace Player", id='replace-button', color="primary", className="mt-3 me-2"),
            dbc.Button("Remove Player", id='remove-button', color="danger", className="mt-3 me-2"),
            dbc.Button("Save Team to Database", id='save-team-button', color="info", className="mt-3"),
            html.Div(id='edit-message', className="mt-2"),
            html.Div(id='remove-message', className="mt-2"),
            html.Div(id='save-message', className="mt-2"),
            
            html.Hr(className="my-4"),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Add New Player:"),
                    dcc.Dropdown(id='player-to-add-dropdown', placeholder="Select player to add...")
                ], width=8),
                dbc.Col([
                    dbc.Button("Add Player", id='add-button', color="success", className="mt-4"),
                ], width=4)
            ]),
            html.Div(id='add-message', className="mt-2")
        ], width=12)
    ]),
    
    # Optimize Section
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.H3("Transfer Optimization", className="mb-3"),
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
    Output('team-summary', 'children'),
    Output('team-display', 'children'),
    Output('player-to-replace-dropdown', 'options'),
    Input('team-store', 'data')
)
def update_team_display(team_data):
    """Update the team display when team data changes."""
    if not team_data:
        return "", "", []
    
    team_df = team_json_to_dataframe(team_data)
    total_cost = team_df['price'].sum()
    starting_points = team_df[team_df['is_starter']]['predicted_points'].sum()
    
    # Summary
    summary = dbc.Alert([
        html.H5(f"Total Cost: £{total_cost:.1f}m / £{BUDGET:.1f}m", className="mb-1"),
        html.H5(f"Starting XI Points: {starting_points:.2f}", className="mb-0")
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
                    {'name': 'Predicted Points', 'id': 'predicted_points', 'type': 'numeric', 'format': {'specifier': '.2f'}},
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
    player_options = [
        {'label': f"{row['name']} ({row['position']}) - £{row['price']:.1f}m", 'value': row['id']}
        for _, row in team_df.iterrows()
    ]
    
    return summary, html.Div(tables), player_options

@callback(
    Output('replacement-player-dropdown', 'options'),
    Output('player-to-add-dropdown', 'options'),
    Input('player-to-replace-dropdown', 'value'),
    State('team-store', 'data')
)
def update_replacement_options(selected_player_id, team_data):
    """Update replacement dropdown to show all available players from any position."""
    if not team_data:
        return [], []
    
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
            'label': f"{row['name']} ({row['position']}) - {team_id_to_name.get(row['team'], 'Unknown')} - £{row['price']:.1f}m, {row['predicted_points']:.2f}pts",
            'value': row['id']
        }
        for _, row in available.iterrows()
    ]
    
    # Same options for adding players
    return replacement_options, replacement_options

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
    Output('remove-message', 'children'),
    Input('remove-button', 'n_clicks'),
    State('player-to-replace-dropdown', 'value'),
    State('team-store', 'data'),
    prevent_initial_call=True
)
def remove_player(n_clicks, player_id, team_data):
    """Remove a player from the team temporarily."""
    if not n_clicks or not player_id:
        return team_data, ""
    
    team_df = team_json_to_dataframe(team_data)
    player_to_remove = team_df[team_df['id'] == player_id].iloc[0]
    
    # Check minimum position requirements
    position_counts = team_df['position'].value_counts().to_dict()
    new_count = position_counts.get(player_to_remove['position'], 0) - 1
    
    # GK must have at least 1, others can go to 0
    if player_to_remove['position'] == 'GK' and new_count < 1:
        return team_data, dbc.Alert(
            "⚠️ Cannot remove player: Must have at least 1 goalkeeper in the team",
            color="warning"
        )
    
    # Remove player from team
    team_df = team_df[team_df['id'] != player_id]
    
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
        f"🗑️ Removed {player_to_remove['name']} ({player_to_remove['position']}) from team | New squad size: {len(team_df)}/15",
        color="info"
    )
    
    return new_team_data, message

@callback(
    Output('team-store', 'data', allow_duplicate=True),
    Output('add-message', 'children'),
    Input('add-button', 'n_clicks'),
    State('player-to-add-dropdown', 'value'),
    State('team-store', 'data'),
    prevent_initial_call=True
)
def add_player(n_clicks, player_id, team_data):
    """Add a new player to the team."""
    if not n_clicks or not player_id:
        return team_data, ""
    
    team_df = team_json_to_dataframe(team_data)
    player_to_add = all_players[all_players['id'] == player_id].iloc[0]
    
    # Validate budget
    new_total_cost = team_df['price'].sum() + player_to_add['price']
    if new_total_cost > BUDGET:
        return team_data, dbc.Alert(
            f"⚠️ Cannot add player: Would exceed budget by £{new_total_cost - BUDGET:.1f}m",
            color="warning"
        )
    
    # Validate position limits
    position_counts = team_df['position'].value_counts().to_dict()
    new_count = position_counts.get(player_to_add['position'], 0) + 1
    
    if new_count > POSITION_LIMITS[player_to_add['position']]:
        return team_data, dbc.Alert(
            f"⚠️ Cannot add player: Would have {new_count} {player_to_add['position']} players (max {POSITION_LIMITS[player_to_add['position']]})",
            color="warning"
        )
    
    # Validate team constraint
    team_counts = team_df['team'].value_counts().to_dict()
    new_team_count = team_counts.get(player_to_add['team'], 0) + 1
    
    if new_team_count > 3:
        return team_data, dbc.Alert(
            f"⚠️ Cannot add player: Would have {new_team_count} players from {team_id_to_name.get(player_to_add['team'], 'team')} (max 3 per team)",
            color="warning"
        )
    
    # Validate squad size
    if len(team_df) >= 15:
        return team_data, dbc.Alert(
            "⚠️ Cannot add player: Squad is already full (15/15 players)",
            color="warning"
        )
    
    # Add player to team
    new_player_row = {
        'id': int(player_to_add['id']),
        'name': player_to_add['name'],
        'position': player_to_add['position'],
        'team': int(player_to_add['team']),
        'team_name': team_id_to_name.get(player_to_add['team'], f"Team {player_to_add['team']}"),
        'price': player_to_add['price'],
        'predicted_points': player_to_add['predicted_points'],
        'is_starter': False  # New players start on bench
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
        f"✅ Added {player_to_add['name']} ({player_to_add['position']}) - £{player_to_add['price']:.1f}m | New squad size: {len(team_df)}/15",
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
    """Run transfer optimization on current team."""
    if not n_clicks:
        return ""
    
    try:
        optimizer = FPLTransferOptimizer(DB_PATH)
        result = optimizer.find_best_transfer(team_data)
        
        if result['no_transfer_recommended']:
            return dbc.Alert([
                html.H4("🚫 No Transfer Recommended", className="mb-3"),
                html.P("Your current team is already optimal or no beneficial transfers available within budget.")
            ], color="info")
        
        transfer = result['best_transfer']
        
        return dbc.Alert([
            html.H4("✅ Recommended Transfer", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.H5("OUT:", className="text-danger"),
                    html.P([
                        html.Strong(f"{transfer['out']['name']}"),
                        f" ({transfer['out']['position']}) - {team_id_to_name.get(transfer['out']['team'], 'Unknown')}",
                        html.Br(),
                        f"£{transfer['out']['price']:.1f}m, {transfer['out']['predicted_points']:.2f} pts"
                    ])
                ], width=6),
                dbc.Col([
                    html.H5("IN:", className="text-success"),
                    html.P([
                        html.Strong(f"{transfer['in']['name']}"),
                        f" ({transfer['in']['position']}) - {team_id_to_name.get(transfer['in']['team'], 'Unknown')}",
                        html.Br(),
                        f"£{transfer['in']['price']:.1f}m, {transfer['in']['predicted_points']:.2f} pts"
                    ])
                ], width=6)
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.P([
                        html.Strong("💰 Cost Change: "),
                        f"£{transfer['cost_change']:+.1f}m"
                    ])
                ], width=6),
                dbc.Col([
                    html.P([
                        html.Strong("📈 Points Gain: "),
                        f"{transfer['points_gain']:+.2f} pts"
                    ])
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    html.P([
                        html.Strong("🎯 New Total Points: "),
                        f"{transfer['new_total_points']:.2f}"
                    ])
                ], width=6),
                dbc.Col([
                    html.P([
                        html.Strong("💵 New Total Cost: "),
                        f"£{transfer['new_total_cost']:.1f}m"
                    ])
                ], width=6)
            ])
        ], color="success")
        
    except Exception as e:
        return dbc.Alert(f"❌ Error: {str(e)}", color="danger")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
