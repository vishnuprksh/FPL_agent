from dash import html
import dash_bootstrap_components as dbc


def home_layout():
    return html.Div([
        dbc.Container([
            html.H2('Welcome to the FPL Data Viewer', className='my-4'),
            html.P('Use the buttons above to navigate to Players, Teams or Null Values analysis.'),
        ])
    ])
