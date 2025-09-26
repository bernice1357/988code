import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.LUX,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
    ], 
    suppress_callback_exceptions=True,
    title="988廚房智慧管理系統",  # 設定瀏覽器分頁標題
    assets_folder="assets"  # 確保 assets 資料夾被正確識別
)

# 使用正確的圖片路徑
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>988廚房智慧管理系統</title>
        <link rel="icon" type="image/png" href="/assets/images/icon.png">
        <link rel="icon" type="image/png" sizes="32x32" href="/assets/images/icon.png">
        <link rel="icon" type="image/png" sizes="16x16" href="/assets/images/icon.png">
        <meta name="description" content="專業的B2B管理解決方案，讓您的業務更智慧、更高效">
        <meta name="keywords" content="廚房管理,智慧系統,庫存管理,客戶管理,銷售分析">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

server = app.server  # 部署用