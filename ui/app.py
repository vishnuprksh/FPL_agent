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

# Default team
def get_default_team():
    """Return default team structure."""
    return {
        "team": [
            {
                "position": "GK",
                "players": [
                    {"id": 101, "name": "Kelleher", "team": 5, "is_starter": True},
                    {"id": 470, "name": "Dúbravka", "team": 3, "is_starter": False}
                ]
            },
            {
                "position": "DEF",
                "players": [
                    {"id": 113, "name": "Van den Berg", "team": 5, "is_starter": True},
                    {"id": 403, "name": "Gvardiol", "team": 13, "is_starter": True},
                    {"id": 568, "name": "Pedro Porro", "team": 18, "is_starter": True},
                    {"id": 291, "name": "Tarkowski", "team": 9, "is_starter": True},
                    {"id": 370, "name": "Frimpong", "team": 12, "is_starter": False}
                ]
            },
            {
                "position": "MID",
                "players": [
                    {"id": 82, "name": "Semenyo", "team": 4, "is_starter": True},
                    {"id": 580, "name": "Johnson", "team": 18, "is_starter": True},
                    {"id": 384, "name": "Gakpo", "team": 12, "is_starter": True},
                    {"id": 582, "name": "Kudus", "team": 18, "is_starter": True},
                    {"id": 325, "name": "Smith Rowe", "team": 10, "is_starter": False}
                ]
            },
            {
                "position": "FWD",
                "players": [
                    {"id": 430, "name": "Haaland", "team": 13, "is_starter": True},
                    {"id": 525, "name": "Wood", "team": 16, "is_starter": True},
                    {"id": 311, "name": "Beto", "team": 9, "is_starter": False}
                ]
            }
        ]
    }

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
    dcc.Store(id='team-store', data=get_default_team()),
    
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
            dbc.Button("Reset to Default Team", id='reset-button', color="secondary", className="mt-3"),
            html.Div(id='edit-message', className="mt-2")
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
                    {'name': 'Team', 'id': 'team'},
                    {'name': 'Price (£m)', 'id': 'price', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': 'Predicted Points', 'id': 'predicted_points', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Starter', 'id': 'is_starter', 'type': 'text'}
                ],
                style_data_conditional=[
                    {'if': {'filter_query': '{is_starter} = true'}, 'backgroundColor': '#d4edda'},
                    {'if': {'filter_query': '{is_starter} = false'}, 'backgroundColor': '#f8f9fa'}
                ],
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'minWidth': '100px',
                    'maxWidth': '180px',
                    'whiteSpace': 'normal'
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'name'}, 'width': '30%'},
                    {'if': {'column_id': 'team'}, 'width': '15%', 'textAlign': 'center'},
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
    Input('player-to-replace-dropdown', 'value'),
    State('team-store', 'data')
)
def update_replacement_options(selected_player_id, team_data):
    """Update replacement dropdown based on selected player."""
    if not selected_player_id or not team_data:
        return []
    
    team_df = team_json_to_dataframe(team_data)
    selected_player = team_df[team_df['id'] == selected_player_id].iloc[0]
    position = selected_player['position']
    current_team_ids = team_df['id'].tolist()
    
    # Get available players of same position not in team
    available = all_players[
        (all_players['position'] == position) &
        (~all_players['id'].isin(current_team_ids))
    ].copy()
    
    # Sort by predicted points
    available = available.sort_values('predicted_points', ascending=False)
    
    replacement_options = [
        {
            'label': f"{row['name']} (Team {row['team']}) - £{row['price']:.1f}m, {row['predicted_points']:.2f}pts",
            'value': row['id']
        }
        for _, row in available.head(50).iterrows()
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
    """Replace a player in the team."""
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
    
    # Validate team constraint
    team_counts = team_df['team'].value_counts().to_dict()
    if new_player['team'] != old_player['team']:
        team_counts[old_player['team']] = team_counts.get(old_player['team'], 0) - 1
        team_counts[new_player['team']] = team_counts.get(new_player['team'], 0) + 1
        if team_counts.get(new_player['team'], 0) > 3:
            return team_data, dbc.Alert(
                f"❌ Cannot make transfer: Would have {team_counts[new_player['team']]} players from team {new_player['team']} (max 3)",
                color="danger"
            )
    
    # Make the replacement
    new_team_data = {'team': []}
    for pos_data in team_data['team']:
        new_pos_data = {'position': pos_data['position'], 'players': []}
        for player in pos_data['players']:
            if player['id'] == old_player_id:
                new_pos_data['players'].append({
                    'id': int(new_player['id']),
                    'name': new_player['name'],
                    'team': int(new_player['team']),
                    'is_starter': player.get('is_starter', True)
                })
            else:
                new_pos_data['players'].append(player)
        new_team_data['team'].append(new_pos_data)
    
    message = dbc.Alert(
        f"✅ Replaced {old_player['name']} with {new_player['name']} (Cost: £{cost_change:+.1f}m)",
        color="success"
    )
    
    return new_team_data, message

@callback(
    Output('team-store', 'data', allow_duplicate=True),
    Input('reset-button', 'n_clicks'),
    prevent_initial_call=True
)
def reset_team(n_clicks):
    """Reset team to default."""
    if not n_clicks:
        return dash.no_update
    return get_default_team()

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
                        f" ({transfer['out']['position']}) - Team {transfer['out']['team']}",
                        html.Br(),
                        f"£{transfer['out']['price']:.1f}m, {transfer['out']['predicted_points']:.2f} pts"
                    ])
                ], width=6),
                dbc.Col([
                    html.H5("IN:", className="text-success"),
                    html.P([
                        html.Strong(f"{transfer['in']['name']}"),
                        f" ({transfer['in']['position']}) - Team {transfer['in']['team']}",
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
