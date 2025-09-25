from dash import html
import dash_table
import dash_bootstrap_components as dbc
from fpl_agent import queries


def null_values_layout():
    null_data = queries.get_null_percentages()
    if not null_data:
        return html.Div([html.P('No null value data available')])

    columns = [{'name': k, 'id': k} for k in null_data[0].keys()]

    return dbc.Container([
        html.H2('Null Values Analysis'),
        html.A('Back to Home', href='/', className='btn btn-secondary mb-3'),
        dash_table.DataTable(
            data=null_data,
            columns=columns,
            page_size=50,
            style_table={'overflowX': 'auto'}
        )
    ], fluid=True)
