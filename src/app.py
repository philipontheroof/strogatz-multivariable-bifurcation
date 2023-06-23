import dash
from dash import dcc
from dash import html
from dash.dependencies import Output, Input, State
import json

import plotly.graph_objs as go
import numpy as np
import random

import plotly.graph_objects as go
import numpy as np

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
    r = r*y - y**3 + h
    return r


x_initial = 0.0
x = x_initial
t_initial = 0.0
t = t_initial
dt = 0.05
n = 5

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(children=[
    dcc.Graph(id="live-graph"),

    html.Div(children=[html.Button("Reset", id="reset-button", n_clicks=0, style={"margin-right": "10px"}),
                       html.Button("Add Noise", id="noise-button", n_clicks=0)], style={"margin-bottom": "15px"}),

    html.Div(children=[html.Label('r:', style={"margin-right": "5px"}),
                       dcc.Slider(id='r-slider', min=-10, max=10, value=10, step=0.1,
                                  marks={i: str(i) for i in range(-10, 11)}),
                       html.Label(
                           'h:', style={"margin-top": "15px", "margin-right": "5px"}),
                       dcc.Slider(id='h-slider', min=-10, max=10, value=0, step=0.1,
                                  marks={i: str(i) for i in range(-10, 11)}),],
             style={"margin-bottom": "15px"}),

    dcc.Interval(id="graph-update", interval=dt*1000, n_intervals=0),

    html.Div(children=[
        dcc.Graph(figure=fig),
    ]),
])


@app.callback(
    Output("noise-button", "children"),
    [Input("noise-button", "n_clicks")],
)
def update_noise_button_label(n_clicks):
    if n_clicks % 2 == 0:
        return "Add Noise"
    else:
        return "Remove Noise"


@app.callback(
    Output("live-graph", "figure"),
    [
        Input("graph-update", "n_intervals"),
        Input("r-slider", "value"),
        Input("h-slider", "value"),
        Input("noise-button", "n_clicks")
    ],
    [State("reset-button", "n_clicks")],
    [State("live-graph", "relayoutData")],
)
def update_graph(interval, r, h, noise_clicks, reset_clicks, relayout_data):
    global x, t, dt

    def f(t, x): return func(t, x, r, h)

    fx = np.linspace(-5, 5, 100)
    fy = f(0, fx)
    for _ in range(n):
        t, x = rk4_one_step(f, x, t, dt/n)

    if noise_clicks % 2 == 1:
        x += random.gauss(0, 0.01)
    else:
        x = x

    p = go.Scatter(x=[x], y=[0], mode="markers",
                   marker=dict(color="red"), showlegend=False)
    v = go.Scatter(x=fx, y=fy, mode="lines",
                   marker=dict(color="blue"), showlegend=False)
    zero = go.Scatter(
        x=fx,
        y=[0] * len(fx),
        mode="lines",
        line=dict(color="black", width=3),
        showlegend=False,
    )

    if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
        xaxis = dict(
            range=[
                relayout_data['xaxis.range[0]'],
                relayout_data['xaxis.range[1]']
            ],
            autorange=False)
    else:
        xaxis = dict(autorange=True)

    if 'yaxis.range[0]' in relayout_data and 'yaxis.range[1]' in relayout_data:
        yaxis = dict(
            range=[
                relayout_data['yaxis.range[0]'],
                relayout_data['yaxis.range[1]']
            ],
            autorange=False)
    else:
        yaxis = dict(autorange=True)

    xaxis['title'] = 'position'
    yaxis['title'] = 'velocity'

    layout = dict(
        title={'text': f't={t:.2f}'},
        xaxis=xaxis,
        yaxis=yaxis,
    )

    return {"data": [zero, v, p], "layout": layout}


@app.callback(
    Output("reset-button", "n_clicks"),
    [Input("reset-button", "n_clicks")],
)
def reset_simulation(n_clicks):
    global x, t, x_initial, t_initial

    if n_clicks > 0:
        x = x_initial
        t = t_initial

    return 0


if __name__ == "__main__":
    app.run_server()
