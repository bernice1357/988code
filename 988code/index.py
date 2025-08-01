from dash import html, dcc, Input, Output
from pages.common import *
import dash_bootstrap_components as dbc
from app import app
import login
import page_after_login
from datetime import datetime

# 判斷哪些是

app.layout = html.Div([
    dcc.Location(id='index-url', refresh=False),
    html.Div(id='index-page-content'),
    # 添加 Store 來存儲登入狀態
    dcc.Store(id='login_status', storage_type='local'),
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

# 檢查登入狀態是否有效的函數
def is_login_valid(login_status):
    if not login_status or not isinstance(login_status, dict):
        return False
    
    if 'role' not in login_status or 'exp' not in login_status:
        return False
    
    try:
        # 解析過期時間
        exp_time = datetime.strptime(login_status['exp'], "%Y-%m-%d %H:%M:%S")
        current_time = datetime.utcnow()
        
        # 檢查是否過期
        if current_time > exp_time:
            return False
        
        # 檢查 role 是否有效
        if login_status['role'] not in ['editor', 'viewer']:
            return False
        
        return True
    except:
        return False

# 修改後的 callback，根據 pathname 和 login_status 決定頁面內容
@app.callback(
    [Output('index-page-content', 'children'),
     Output('index-url', 'pathname', allow_duplicate=True),
     Output('login_status', 'data', allow_duplicate=True)],
    [Input('index-url', 'pathname'),
     Input('login_status', 'data')],
    prevent_initial_call=True
)
def display_index_page(pathname, login_status):
    # 檢查是否在登入狀態
    is_valid = is_login_valid(login_status)
    
    if pathname == '/': # 首頁
        # 如果登入有效，跳到登入後頁面
        if is_valid:
            return page_after_login.layout, '/new_orders', dash.no_update
        else:
            # 登入無效或過期，清除 localStorage 並顯示首頁
            return index_content, dash.no_update, None
    elif pathname == '/login': # 登入頁
        # 如果登入有效，直接跳到登入後頁面
        if is_valid:
            return page_after_login.layout, '/new_orders', dash.no_update
        else:
            # 登入無效，清除 localStorage 並顯示登入頁
            return login.layout, dash.no_update, None
    else: # 其他路徑（如 /page_after_login）
        # 如果登入有效，顯示登入後頁面
        if is_valid:
            return page_after_login.layout, dash.no_update, dash.no_update
        else:
            # 登入無效或過期，清除 localStorage 並回到首頁
            return index_content, '/', None

if __name__ == '__main__':
    app.run(debug=True)