# 首先載入環境變數
from env_loader import load_env_file
load_env_file()

import dash
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[
        dbc.themes.LUX,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
    ], suppress_callback_exceptions=True)

server = app.server  # 部署用