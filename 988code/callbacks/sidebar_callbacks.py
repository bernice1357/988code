from .common import *

@app.callback(
    Output("sidebar", "style"),
    Output("toggle-button-float", "style"),
    Output("breadcrumb", "style"),
    Output("main-content", "style"),
    Output("sidebar-toggle", "data"),
    Input("toggle-button", "n_clicks"),
    Input("toggle-button-float", "n_clicks"),
    Input("sidebar-toggle", "data"),
    prevent_initial_call=True
)
def toggle_sidebar(n1, n2, is_open):
    ctx = callback_context
    if not ctx.triggered:
        raise exceptions.PreventUpdate

    if is_open:
        return (
            {"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "0rem", "transition": "all 0.3s", "overflow": "hidden", "padding": "0", "backgroundColor": "#f0f4f8"},
            {"position": "fixed", "bottom": "20px", "left": "10px", "zIndex": "1001", "backgroundColor": "#000000", "color": "#ffffff", "border": "none", "borderRadius": "4px", "padding": "6px 10px", "fontSize": "20px", "cursor": "pointer", "display": "block"},
            {"margin": "0", "padding": "0.75rem 2rem", "backgroundColor": "#829AB1", "color": "#FFFFFF", "height": "64px", "display": "flex", "alignItems": "center", "position": "fixed", "left": "0", "right": "0", "top": "0", "zIndex": "1000", "width": "100%"},
            {"margin-left": "0", "margin-top": "64px", "padding": "2rem", "backgroundColor": "#FFFFFF", "color": "#000000"},
            False
        )
    else:
        return (
            {"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "16rem", "transition": "all 0.3s", "overflow": "hidden", "padding": "2rem 1rem", "backgroundColor": "#f0f4f8", "boxShadow": "2px 0px 8px rgba(0, 0, 0, 0.1)"},
            {"display": "none"},
            {"margin": "0", "padding": "0.75rem 2rem", "backgroundColor": "#829AB1", "color": "#FFFFFF", "height": "64px", "display": "flex", "alignItems": "center", "position": "fixed", "left": "16rem", "right": "0", "top": "0", "zIndex": "1000", "width": "calc(100% - 16rem)"},
            {"margin-left": "16rem", "margin-top": "64px", "padding": "2rem", "backgroundColor": "#FFFFFF", "color": "#000000"},
            True
        )
