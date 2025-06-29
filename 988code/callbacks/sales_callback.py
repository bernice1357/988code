from .common import *

@app.callback(
    Output("offcanvas", "is_open"),
    [Input("open-offcanvas", "n_clicks")],
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open