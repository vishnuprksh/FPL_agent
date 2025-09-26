from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from fpl_agent import queries


def players_layout():
    """Return the players page layout.

    This layout includes a search input (debounced) and a DataTable with an id
    so a callback can update its `data` property with filtered results.
    """
    # Use default columns from queries.get_players
    players = queries.get_players()
    if not players:
        return html.Div([html.P('No players found')])

    columns = [{'name': k, 'id': k} for k in players[0].keys()]

    # Add a button column by constructing an extra column in the data
    for p in players:
        pid = p.get('id') or p.get('player_code')
        p['history_link'] = f'<a href="/player/{pid}/history" class="btn btn-primary btn-sm">View History</a>'

    columns.append({'name': 'History', 'id': 'history_link', 'type': 'text', 'presentation': 'markdown'})

    return dbc.Container([
        html.H2('Players'),
        dcc.Link('Back to Home', href='/', className='btn btn-secondary mb-3'),
        # Search input for filtering players. debounce=True triggers callback after typing pauses or on Enter.
        dcc.Input(id='players-search', placeholder='Search players by name or team...', type='text', debounce=True, className='form-control mb-3'),
        dash_table.DataTable(
            id='players-table',
            data=players,
            columns=columns,
            page_size=25,
            style_table={'overflowX': 'auto'},
            markdown_options={"html": True}
        )
    ], fluid=True)
