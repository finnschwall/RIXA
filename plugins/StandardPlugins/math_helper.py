import pandas as pd
import sympy
import numpy as np
import plotly.express as px
from plugins.api import *
import plotly.graph_objects as go
@plugin_init(name="math_helper", call_architecture="functional")
def data(ctx, config, meta_config):
    pass

@data.plugin_method(help="Plot 2D function. Use x and y as names")
@argument('function')
@option('--res', default=40, help='Total number of generated points per axis', type=int)
@option('-xs', "--xstart", default=-5, help='Start of x range', type=float)
@option('-xe', "--xend", default=5, help='End of x range', type=float)
@option('-ys', "--ystart", default=-5, help='Start of y range', type=float)
@option('-ye', "--yend", default=5, help='End of y range', type=float)
def plot3D(api, function=None, res=40, xstart=-5, xend=5, ystart=-5,yend=5):
    if not function:
        api.display_message("No function supplied", 5, "danger")
        return
    expr = sympy.sympify(function)
    res = res * 1j
    lambd_expr = sympy.lambdify(list(expr.free_symbols), expr)
    x, y = np.mgrid[xstart:xend:res, ystart:yend:res]
    z = lambd_expr(x, y)
    fig = go.Figure(data=[go.Surface(x=x, y=y, z=z)])
    html = fig.to_html(include_plotlyjs=False, include_mathjax=False, full_html=False)

    api.display_html(html)


@data.plugin_method(help="Line plot. Use x as the name for the variable.")
@argument('function')
@option('--res', default=30, help='Total number of generated points', type=int)
@option('-xs', "--xstart", default=-5, help='Start of x range', type=float)
@option('-xe', "--xend", default=5, help='Start of x range', type=float)
def plot(api, function=None, res=50, xstart=-5, xend=5):

    if not function:
        api.display_notification("No function supplied", 5, "danger")
        return
    res = res
    start = xstart
    end = xend
    expr = sympy.sympify(function)
    lambd_expr = sympy.lambdify(list(expr.free_symbols), expr)
    x = np.linspace(start, end, res)
    y = lambd_expr(x)
    fig = px.line(x=x, y=y)
    html = fig.to_html(include_plotlyjs=False, include_mathjax=False, full_html=False)
    api.display(html=html)