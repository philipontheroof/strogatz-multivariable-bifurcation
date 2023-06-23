import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State, MATCH, ALL, ClientsideFunction
import json

import plotly.graph_objs as go
import numpy as np
import random

x, r = np.meshgrid(np.arange(-10, 10, 0.05), np.arange(-10, 10, 0.05))
h = x**3 - r*x

# Calculate the slope of h with respect to x
slope = np.gradient(h, axis=1)

stability = np.where(slope < 0, 0, 1)

# Create a custom color scale with transparency
custom_colorscale = [
    [0, 'rgba(0, 0, 255, 0.4)'],
    [1, 'rgba(255, 0, 0, 0.6)'],
]

# Create a plotly surface plot
surface = go.Surface(x=r, y=h, z=x, surfacecolor=stability, showscale=False, colorscale=custom_colorscale,
                     contours=dict(x=dict(show=True, color='grey', width=1),
                                   y=dict(show=True, color='grey', width=1),
                                   z=dict(show=True, color='grey', width=1),
                                   )
                     )

fig = go.Figure(data=[surface])

# Calculate axis lengths based on data ranges
x_length = 20
y_length = 30
z_length = 10
mean = np.mean([x_length, y_length, z_length])

# Define the aspect ratio based on data ranges
aspect_ratio = dict(x=x_length/mean, y=y_length/mean, z=z_length/mean)

fig.update_scenes(
    aspectmode='manual',
    aspectratio=aspect_ratio,
    xaxis_title="r",  # Custom label for x axis
    yaxis_title="h",  # Custom label for y axis
    zaxis_title="x",  # Custom label for z axis
    xaxis_showgrid=False,  # Disable x axis grid lines
    yaxis_showgrid=False,  # Disable y axis grid lines
    zaxis_showgrid=False,   # Disable z axis grid lines
    xaxis=dict(range=[-10, 10]),
    yaxis=dict(range=[-15, 15]),
    zaxis=dict(range=[-5, 5]),
    # Set the camera projection type to orthographic
    camera=dict(projection=dict(type='orthographic')),
)


def rk4_one_step(f, y, t, dt):
    k1 = f(t, y)
    k2 = f(t + dt / 2, y + k1 * dt / 2)
    k3 = f(t + dt / 2, y + k2 * dt / 2)
    k4 = f(t + dt, y + k3 * dt)

    dy = (k1 + 2 * k2 + 2 * k3 + k4) * dt / 6
    y = y + dy

    return t + dt, y


def func(t, y, r, h):
    R = r*y - y**3 + h
    return R


x_initial = 0.0
x = x_initial
t_initial = 0.0
t = t_initial
dt = 0.05
n = 5

is_noise_active = False

app = dash.Dash(__name__,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server = app.server


fx = np.linspace(-5, 5, 100)
DEfig = go.Figure(data=[go.Scatter(x=[-5, 5], y=[0, 0], mode="lines",
                                   line=dict(color="black", width=3), showlegend=False),
                        go.Scatter(x=fx, y=(10*fx - fx**3), mode="lines",
                                   marker=dict(color="blue"), showlegend=False),
                        go.Scatter(x=[x], y=[0], mode="markers",
                                   marker=dict(color="red"), showlegend=False),
                        ], layout=dict(xaxis=dict(title='position'), yaxis=dict(title='velocity')))

app.layout = html.Div(children=[
    html.H1("Strogatz 3.6: Imperfect Bifurcations and Catastrophes",
            style={"textAlign": "center"}),

    html.Div(
        children=[
            html.H3("derivative function and time-varying position",
                    style={"textAlign": "center"}),

            dcc.Graph(id="live-graph", figure=DEfig),

            html.Div(children=[html.Div([html.Button("Reset", id="reset-button", n_clicks=0)], style={"display": "inline-block", "margin-right": "10px"}),
                               html.Div([html.Button(
                                   "Add Noise", id="noise-button", n_clicks=0)], style={"display": "inline-block", "margin-bottom": "15px"}),
                               ]),
            html.Div([
                html.P("Sliders:", style={"textAlign": "center"}),
                html.Label('r:', style={"margin-right": "5px"}),
                dcc.Slider(id='r-slider', min=-10, max=10, value=10, step=0.1, updatemode='drag',
                           marks={i: str(i) for i in range(-10, 11)}),
                html.Br(),
                html.Label(
                    'h:', style={"margin-top": "15px", "margin-right": "5px"}),
                dcc.Slider(id='h-slider', min=-10, max=10, value=0, step=0.1, updatemode='drag',
                           marks={i: str(i) for i in range(-10, 11)}),
            ], style={"margin-bottom": "15px", "textAlign": "center"}
            ),

            dcc.Interval(id="graph-update", interval=dt*1000, n_intervals=0),

            html.Hr(),

            html.H3("bifurcation diagram:", style={
                    "textAlign": "center"}),
            html.P("The red surface means stable equilibrium and the blue surface means unstable equilibrium.",
                   style={"textAlign": "center"}),

            html.Div(children=[
                dcc.Graph(figure=fig),
            ]),
        ],
        style={"max-width": "70%", "margin": "0 auto"})
])

app.clientside_callback(
    ClientsideFunction(namespace='clientside',
                       function_name='update_noise_button_label'),
    Output("noise-button", "children"),
    [Input("noise-button", "n_clicks")],
)

app.clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_graph'),
    Output("live-graph", "figure"),
    [
        Input('graph-update', 'n_intervals'),
        Input("r-slider", "value"),
        Input("h-slider", "value"),
        Input("noise-button", "n_clicks")
    ],
    [State("reset-button", "n_clicks"), State("live-graph", "figure")],
)

app.clientside_callback(
    ClientsideFunction(namespace='clientside',
                       function_name='reset_simulation'),
    Output("reset-button", "n_clicks"),
    [Input("reset-button", "n_clicks")],
)

if __name__ == "__main__":
    app.run_server()
