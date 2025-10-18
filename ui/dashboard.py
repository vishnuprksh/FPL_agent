"""
FPL Agent Dashboard

A web-based dashboard for managing and viewing FPL data using the fpl_agent library.
Features include database updates and comprehensive table viewing functionality.
"""

import dash
from dash import dcc, html, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import traceback

# Import FPL agent modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpl_agent.database import queries
from fpl_agent.database.update import load_historic_data, load_teams_data, load_fixture_data
from fpl_agent.models.core import init_db


class FPLDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.initialize_database()
        self.setup_layout()
        self.setup_callbacks()
    
    def initialize_database(self):
        """Initialize the database if it doesn't exist."""
        try:
            init_db()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"⚠️ Warning during database initialization: {e}")
            print("Database will be created when first update is performed.")
        
    def setup_layout(self):
        """Set up the dashboard layout with navigation and content areas."""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("FPL Agent Dashboard", className="text-center mb-4"),
                    html.Hr(),
                ], width=12)
            ]),
            
            # Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Database Management")),
                        dbc.CardBody([
                            dbc.Alert([
                                html.Strong("First Time Setup: "),
                                "If this is your first time using the dashboard, click 'Update Database' to download and populate FPL data."
                            ], color="info", dismissable=True),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        "Update Database", 
                                        id="update-btn", 
                                        color="primary", 
                                        className="me-2"
                                    ),
                                    dbc.Button(
                                        "Refresh Tables", 
                                        id="refresh-btn", 
                                        color="secondary"
                                    ),
                                ], width=8),
                                dbc.Col([
                                    dbc.Label("Season:"),
                                    dbc.Select(
                                        id="season-select",
                                        options=[
                                            {"label": "2025-26", "value": "2025-26"},
                                            {"label": "2024-25", "value": "2024-25"},
                                            {"label": "2023-24", "value": "2023-24"},
                                        ],
                                        value="2025-26",
                                        className="mb-2"
                                    ),
                                ], width=4),
                            ]),
                            html.Div(id="update-status", className="mt-3"),
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Table Selection
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Data Viewer")),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Select Table:"),
                                    dbc.Select(
                                        id="table-select",
                                        options=[
                                            {"label": "Players (Seasonal)", "value": "players"},
                                            {"label": "Teams", "value": "teams"},
                                            {"label": "Player History", "value": "player_history"},
                                            {"label": "Fixtures", "value": "fixtures"},
                                            {"label": "Null Percentages", "value": "null_percentages"},
                                        ],
                                        value="players",
                                        className="mb-3"
                                    ),
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Records to Show:"),
                                    dbc.Select(
                                        id="limit-select",
                                        options=[
                                            {"label": "50", "value": 50},
                                            {"label": "100", "value": 100},
                                            {"label": "250", "value": 250},
                                            {"label": "All", "value": 0},
                                        ],
                                        value=100,
                                        className="mb-3"
                                    ),
                                ], width=6),
                            ]),
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Data Display Area
            dbc.Row([
                dbc.Col([
                    html.Div(id="table-container"),
                ], width=12)
            ]),
            
            # Footer
            html.Hr(),
            html.Footer([
                html.P(
                    f"FPL Agent Dashboard - Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    className="text-center text-muted"
                )
            ])
        ], fluid=True)
    
    def setup_callbacks(self):
        """Set up all dashboard callbacks for interactivity."""
        
        @self.app.callback(
            Output('update-status', 'children'),
            Input('update-btn', 'n_clicks'),
            State('season-select', 'value'),
            prevent_initial_call=True
        )
        def update_database(n_clicks, season):
            """Handle database update operations."""
            if n_clicks is None:
                return ""
            
            try:
                # Initialize database first
                init_db()
                
                status_messages = []
                
                # Update teams data
                status_messages.append(
                    dbc.Alert("Updating teams data...", color="info", dismissable=False)
                )
                teams_count = load_teams_data(season)
                status_messages.append(
                    dbc.Alert(f"✅ Updated {teams_count} teams", color="success", dismissable=True)
                )
                
                # Update historic data (players and history)
                status_messages.append(
                    dbc.Alert("Updating player data...", color="info", dismissable=False)
                )
                load_historic_data(season)
                status_messages.append(
                    dbc.Alert("✅ Updated player data", color="success", dismissable=True)
                )
                
                # Update fixtures
                status_messages.append(
                    dbc.Alert("Updating fixtures...", color="info", dismissable=False)
                )
                load_fixture_data(season)
                status_messages.append(
                    dbc.Alert("✅ Updated fixtures", color="success", dismissable=True)
                )
                
                status_messages.append(
                    dbc.Alert(
                        f"🎉 Database update completed successfully for season {season}!", 
                        color="success", 
                        dismissable=True
                    )
                )
                
                return html.Div(status_messages)
                
            except Exception as e:
                error_msg = f"❌ Error updating database: {str(e)}"
                error_details = traceback.format_exc()
                print(f"Database update error: {error_details}")
                
                return html.Div([
                    dbc.Alert(error_msg, color="danger", dismissable=True),
                    dbc.Alert([
                        html.Strong("Error Details: "),
                        html.Pre(str(e), style={"white-space": "pre-wrap", "font-size": "12px"})
                    ], color="warning", dismissable=True)
                ])
        
        @self.app.callback(
            Output('table-container', 'children'),
            [Input('table-select', 'value'),
             Input('limit-select', 'value'),
             Input('refresh-btn', 'n_clicks')],
            prevent_initial_call=False
        )
        def update_table_display(selected_table, limit, refresh_clicks):
            """Update the table display based on selection."""
            try:
                # Initialize database if needed
                init_db()
                
                if selected_table == "players":
                    data = queries.get_players()
                    title = "Players (Seasonal Data)"
                elif selected_table == "teams":
                    data = queries.get_teams()
                    title = "Teams"
                elif selected_table == "player_history":
                    # Get a sample of player history
                    from fpl_agent.database.connection import get_connection
                    conn = get_connection()
                    query = "SELECT * FROM player_history LIMIT 1000"
                    df = pd.read_sql_query(query, conn)
                    conn.close()
                    data = df.to_dict('records')
                    title = "Player History"
                elif selected_table == "fixtures":
                    from fpl_agent.database.connection import get_connection
                    conn = get_connection()
                    query = "SELECT * FROM fixtures LIMIT 1000"
                    df = pd.read_sql_query(query, conn)
                    conn.close()
                    data = df.to_dict('records')
                    title = "Fixtures"
                elif selected_table == "null_percentages":
                    data = queries.get_null_percentages()
                    title = "Null Value Analysis"
                else:
                    return dbc.Alert("Please select a table to view", color="warning")
                
                if not data:
                    return dbc.Card([
                        dbc.CardHeader(html.H4(title)),
                        dbc.CardBody([
                            dbc.Alert([
                                html.H5("No Data Available", className="alert-heading"),
                                html.P("The database appears to be empty."),
                                html.Hr(),
                                html.P("Click the 'Update Database' button above to populate the database with FPL data.", className="mb-0")
                            ], color="info")
                        ])
                    ])
                
                # Apply limit if specified
                if limit > 0:
                    data = data[:limit]
                
                # Create data table
                df = pd.DataFrame(data)
                
                # Handle potential issues with data types
                for col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str)
                
                table = dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{"name": col, "id": col} for col in df.columns],
                    page_size=20,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontFamily': 'Arial',
                        'fontSize': '12px'
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    sort_action="native",
                    filter_action="native",
                    export_format="csv",
                )
                
                # Add summary statistics
                summary = html.Div([
                    html.H6(f"Total Records: {len(data)}"),
                    html.H6(f"Columns: {len(df.columns)}"),
                    html.Hr(),
                ])
                
                return dbc.Card([
                    dbc.CardHeader(html.H4(title)),
                    dbc.CardBody([
                        summary,
                        table
                    ])
                ])
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a database-related error
                if "no such table" in error_msg.lower() or "database" in error_msg.lower():
                    return dbc.Card([
                        dbc.CardHeader(html.H4("Database Not Ready")),
                        dbc.CardBody([
                            dbc.Alert([
                                html.H5("Database Error", className="alert-heading"),
                                html.P("The database tables haven't been created yet or are corrupted."),
                                html.Hr(),
                                html.P("Please click the 'Update Database' button to initialize and populate the database with FPL data.", className="mb-0")
                            ], color="warning")
                        ])
                    ])
                else:
                    return dbc.Alert(f"Error loading table data: {error_msg}", color="danger")
    
    def run(self, debug=True, host='0.0.0.0', port=8050):
        """Run the dashboard application."""
        print(f"Starting FPL Agent Dashboard on http://{host}:{port}")
        self.app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    dashboard = FPLDashboard()
    dashboard.run()