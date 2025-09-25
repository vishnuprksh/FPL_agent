from dash import html, dcc
import dash_table
import dash_bootstrap_components as dbc
from fpl_agent import queries


def players_layout():
    # Use default columns from queries.get_players
    players = queries.get_players()
    if not players:
        return html.Div([html.P('No players found')])

    columns = [{'name': k, 'id': k} for k in players[0].keys()]

    # Add a link column by constructing an extra column in the data
    for p in players:
        pid = p.get('id') or p.get('player_code')
        p['history_link'] = f"/player/{pid}/history"

    columns.append({'name': 'History', 'id': 'history_link', 'presentation': 'markdown'})

    return dbc.Container([
        html.H2('Players'),
        dcc.Link('Back to Home', href='/', className='btn btn-secondary mb-3'),
        dash_table.DataTable(
            data=players,
            columns=columns,
            page_size=20,
            style_table={'overflowX': 'auto'},
            markdown_options={"html": True}
        )
    ], fluid=True)
