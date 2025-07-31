from dash import html, dcc, Input, Output
from pages.common import *
import dash_bootstrap_components as dbc
from app import app
import login
import page_after_login

# 判斷哪些是

app.layout = html.Div([
    dcc.Location(id='index-url', refresh=False),
    html.Div(id='index-page-content'),
    # 添加 Store 來存儲從 cookie 讀取的 role
    dcc.Store(id='current-user-role', data=None),
])

index_content = dbc.Container([
    # 頂部導航區域，包含登入按鈕
    dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Button("登入", color="primary", href="/login", size="sm")
            ], className="d-flex justify-content-end mb-4")
        ])
    ]),
    
    # Logo 和系統標題
    html.Div([
        html.Div(
            html.A(
                html.Img(src="/assets/images/logo.png", style={"width": "200px", "height": "auto", "margin-bottom": "20px"}),
                href="/",
                style={"text-decoration": "none"}
            )
        ),
        html.H1("銷貨預測系統", className="text-center mb-4", style={"color": "#2c3e50"})
    ], className="text-center"),
    
    # 系統簡介
    html.P("這是一個全方位的業務管理系統，提供完整的訂單管理、客戶資料管理、庫存管理等功能。", 
           className="text-center mb-5", style={"font-size": "1.2rem", "color": "#6c757d"}),
    
    # 主要功能區塊
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-chart-line fa-3x mb-3", style={"color": "#007bff"}),
                    html.H4("銷貨預測", className="card-title"),
                    html.P("運用AI技術分析歷史銷售數據，提供準確的銷售預測，協助制定最佳的庫存與銷售策略。", 
                           className="card-text")
                ], className="text-center")
            ], className="h-100")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-database fa-3x mb-3", style={"color": "#28a745"}),
                    html.H4("數據管理", className="card-title"),
                    html.P("集中管理客戶資料、產品資訊與訂單記錄，提供完整的資料視覺化與分析工具。", 
                           className="card-text")
                ], className="text-center")
            ], className="h-100")
        ], width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-boxes fa-3x mb-3", style={"color": "#ffc107"}),
                    html.H4("庫存管理", className="card-title"),
                    html.P("即時監控庫存狀況，自動預警庫存不足，優化進貨時機與數量，降低庫存成本。", 
                           className="card-text")
                ], className="text-center")
            ], className="h-100")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-users fa-3x mb-3", style={"color": "#dc3545"}),
                    html.H4("客戶分析", className="card-title"),
                    html.P("深度分析客戶購買行為與偏好，建立客戶標籤與分群，提升行銷效果與客戶滿意度。", 
                           className="card-text")
                ], className="text-center")
            ], className="h-100")
        ], width=6),
    ], className="mb-5"),
    
    # 開始使用區塊
    dbc.Card([
        dbc.CardBody([
            html.H3("立即開始使用", className="text-center mb-3"),
            html.P("登入系統，體驗智能化的銷貨預測與管理功能", className="text-center mb-4"),
            html.Div([
                dbc.Button("立即登入", color="primary", size="lg", href="/login")
            ], className="text-center")
        ])
    ], className="mb-5", style={"background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "color": "white"}),
    
    # 底部資訊
    html.Hr(className="mt-5"),
    html.Div([
        html.P("© 2025 管理系統 - 版本 1.0", className="text-center text-muted")
    ])
], style={"padding": "40px 20px"})

# clientside callback 讀取 cookie 並存到 Store
app.clientside_callback(
    """
    function(pathname) {
        function getCookie(name) {
            const value = "; " + document.cookie;
            const parts = value.split("; " + name + "=");
            if (parts.length === 2) return parts.pop().split(";").shift();
            return null;
        }
        return getCookie("userRole");
    }
    """,
    Output('current-user-role', 'data'),
    Input('index-url', 'pathname')
)

# 修改後的 callback，根據 pathname 和 user_role 決定頁面內容
@app.callback(
    [Output('index-page-content', 'children'),
     Output('index-url', 'pathname', allow_duplicate=True)],
    [Input('index-url', 'pathname'),
     Input('current-user-role', 'data')],
    prevent_initial_call=True
)
def display_index_page(pathname, user_role):
    if pathname == '/': # 首頁
        # 如果有 userRole cookie (editor 或 viewer)，跳到登入後頁面
        if user_role in ['editor', 'viewer']:
            return page_after_login.layout, '/page_after_login'
        else:
            # 沒有 cookie，顯示首頁
            return index_content, dash.no_update
    elif pathname == '/login': # 登入頁
        # 如果已經有 userRole cookie，直接跳到登入後頁面
        if user_role in ['editor', 'viewer']:
            return page_after_login.layout, '/page_after_login'
        else:
            # 沒有 cookie，顯示登入頁
            return login.layout, dash.no_update
    else: # 其他路徑（如 /page_after_login）
        # 如果有 userRole cookie，顯示登入後頁面
        if user_role in ['editor', 'viewer']:
            return page_after_login.layout, dash.no_update
        else:
            # 沒有 cookie，回到首頁並改變 URL
            return index_content, '/'
    
app.clientside_callback(
    """
    function(role) {
        if (role) {
            // 設定 cookie，2小時後失效
            const expirationTime = new Date();
            expirationTime.setTime(expirationTime.getTime() + (2 * 60 * 60 * 1000)); // 2小時
            const expires = "expires=" + expirationTime.toUTCString();
            document.cookie = "userRole=" + role + ";" + expires + ";path=/";
            console.log("Cookie set: userRole=" + role);
        }
        return "";
    }
    """,
    Output("cookie-setter", "children"),
    Input("user-role-store", "data"),
    prevent_initial_call=True
)

if __name__ == '__main__':
    app.run(debug=True)