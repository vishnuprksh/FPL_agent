from dash import html
import dash_table
import dash_bootstrap_components as dbc
from fpl_agent import queries


def teams_layout():
    teams = queries.get_teams()
    if not teams:
        return html.Div([html.P('No teams found')])

    columns = [{'name': k, 'id': k} for k in teams[0].keys()]

    return dbc.Container([
        html.H2('Teams'),
        dcc.Link('Back to Home', href='/', className='btn btn-secondary mb-3'),
        dash_table.DataTable(
            data=teams,
            columns=columns,
            page_size=20,
            style_table={'overflowX': 'auto'}
        )
    ], fluid=True)
