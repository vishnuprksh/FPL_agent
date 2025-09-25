from dash import html
import dash_table
import dash_bootstrap_components as dbc
from fpl_agent import queries


def player_history_layout(player_id):
    history = queries.get_player_history(player_id)
    if not history:
        return dbc.Container([html.H2(f'Player {player_id} - History'), html.P('No history data available')])

    columns = [{'name': k, 'id': k} for k in history[0].keys()]

    return dbc.Container([
        html.H2(f"{history[0].get('web_name', 'Player')} - Gameweek History"),
        html.A('Back to Players', href='/players', className='btn btn-secondary mb-3'),
        dash_table.DataTable(
            data=history,
            columns=columns,
            page_size=20,
            style_table={'overflowX': 'auto'}
        )
    ], fluid=True)
