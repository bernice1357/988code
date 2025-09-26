# 首先載入環境變數
from env_loader import load_env_file, get_env_int
load_env_file()

import dash
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[
        dbc.themes.LUX,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
    ], suppress_callback_exceptions=True)

server = app.server  # 部署用

# 設定上傳大小限制（單位：MB，可透過 MAX_UPLOAD_SIZE_MB 環境變數調整，預設 50MB）
max_upload_size_mb = get_env_int('MAX_UPLOAD_SIZE_MB', 50)
server.config["MAX_CONTENT_LENGTH"] = max_upload_size_mb * 1024 * 1024
