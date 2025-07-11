from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container([
    # 歡迎標題
    html.H1("歡迎使用管理系統", className="text-center mb-4", style={"color": "#2c3e50"}),
    
    # 系統簡介
    dbc.Card([
        dbc.CardBody([
            html.H4("系統功能概覽", className="card-title"),
            html.P("這是一個全方位的業務管理系統，提供完整的訂單管理、客戶資料管理、庫存管理等功能。", 
                   className="card-text")
        ])
    ], className="mb-4"),
    
    # 功能快捷入口
    html.H3("快速入口", className="mb-3"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("新進訂單", className="card-title"),
                    html.P("查看和管理最新訂單", className="card-text"),
                    dbc.Button("前往", color="primary", href="/new_orders", size="sm")
                ])
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("客戶資料管理", className="card-title"),
                    html.P("管理客戶資訊和聯絡方式", className="card-text"),
                    dbc.Button("前往", color="primary", href="/customer_data", size="sm")
                ])
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("銷售分析", className="card-title"),
                    html.P("查看銷售數據和趨勢分析", className="card-text"),
                    dbc.Button("前往", color="primary", href="/sales_analysis", size="sm")
                ])
            ])
        ], width=4),
    ], className="mb-4"),
    
    # 統計數據區塊
    html.H3("系統統計", className="mb-3"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("156", className="text-center", style={"color": "#007bff"}),
                    html.P("本月新訂單", className="text-center text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("1,234", className="text-center", style={"color": "#28a745"}),
                    html.P("活躍客戶", className="text-center text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("98%", className="text-center", style={"color": "#ffc107"}),
                    html.P("庫存充足率", className="text-center text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("89", className="text-center", style={"color": "#dc3545"}),
                    html.P("待處理提醒", className="text-center text-muted")
                ])
            ])
        ], width=3),
    ]),
    
    # 底部資訊
    html.Hr(className="mt-5"),
    html.Div([
        html.P("© 2025 管理系統 - 版本 1.0", className="text-center text-muted")
    ])
], style={"padding": "20px"})