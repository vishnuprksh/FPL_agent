"""Dash application entrypoint.

Provides `run_dash()` which constructs a Dash app and returns the Flask server
so it can be served alongside or instead of the existing Flask app.
"""
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from flask import Flask

from fpl_agent import queries


def create_dash_app(server: Flask = None):
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    app = Dash(__name__, server=server, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

    app.layout = dbc.Container([
        dcc.Location(id='url', refresh=False),
        html.H1('Fantasy Premier League Data Viewer', className='my-4 text-center'),
        dbc.Row([
            dbc.Col(dbc.Button('Players', href='/players', color='primary', className='me-2'), width='auto'),
            dbc.Col(dbc.Button('Teams', href='/teams', color='secondary', className='me-2'), width='auto'),
            dbc.Col(dbc.Button('Null Values', href='/null-values', color='info'), width='auto'),
        ], justify='center'),
        html.Hr(),
        html.Div(id='page-content')
    ], fluid=True)

    # Simple page router
    @app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
    def display_page(pathname):
        if pathname == '/players':
            from fpl_agent.ui.players import players_layout
            return players_layout()
        if pathname and pathname.startswith('/player/') and pathname.endswith('/history'):
            # path like /player/123/history
            player_id = pathname.split('/')[2]
            from fpl_agent.ui.player_history import player_history_layout
            return player_history_layout(player_id)
        if pathname == '/teams':
            from fpl_agent.ui.teams import teams_layout
            return teams_layout()
        if pathname == '/null-values':
            from fpl_agent.ui.null_values import null_values_layout
            return null_values_layout()
        # default home
        from fpl_agent.ui.home import home_layout
        return home_layout()

    return app


def main(host='127.0.0.1', port=8050, debug=True):
    # Create a standalone Flask server for Dash
    server = Flask(__name__)
    app = create_dash_app(server=server)
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()