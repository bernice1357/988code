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

index_content = html.Div([
    # Hero Section
    html.Div([
        # Navigation
        html.Div([
            html.Div([
                html.Span("988 廚房智慧管理系統", style={"color": "white", "fontSize": "1.5rem", "fontWeight": "bold"}),
                html.Div([
                    dbc.Button("登入", href="/login", style={
                        "background": "transparent", 
                        "border": "1px solid white", 
                        "color": "white",
                        "borderRadius": "25px",
                        "padding": "8px 20px"
                    })
                ])
            ], style={
                "display": "flex", 
                "justifyContent": "space-between", 
                "alignItems": "center",
                "padding": "20px 40px"
            })
        ]),
        
        # Hero Content
        html.Div([
            html.Div([
                html.H1("打造智慧商業解決方案", style={
                    "color": "white",
                    "fontSize": "4rem",
                    "fontWeight": "bold",
                    "lineHeight": "1.1",
                    "marginBottom": "20px",
                    "maxWidth": "600px"
                }),
                html.P("專業的B2B管理系統，提供庫存管理、銷貨預測、客戶管理與銷售分析等全方位解決方案。", style={
                    "color": "rgba(255,255,255,0.8)",
                    "fontSize": "1.2rem",
                    "marginBottom": "30px",
                    "maxWidth": "500px"
                }),
                dbc.Button("立即開始使用", href="/login", style={
                    "background": "transparent",
                    "border": "1px solid white",
                    "color": "white",
                    "borderRadius": "25px",
                    "padding": "12px 30px",
                    "fontSize": "1rem"
                })
            ], style={"maxWidth": "50%"}),
            
            # Decorative Elements - Parallel 3D Bars
            html.Div([
                # 橙紅色條塊 - 頂部 - 水平
                html.Div(style={
                    "width": "calc(40vh + 75px)",
                    "height": "150px",
                    "background": "linear-gradient(135deg, #ff6b35 0%, #ff4757 50%, #c44569 100%)",
                    "position": "absolute",
                    "top": "calc(25vh - 150px)",
                    "right": "0px",
                    "borderRadius": "0 20px 0 0",
                    "boxShadow": "0 20px 60px rgba(255, 107, 53, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)"
                }),
                # 大橙紅色球體
                html.Div(style={
                    "width": "150px",
                    "height": "150px",
                    "borderRadius": "50%",
                    "background": "radial-gradient(circle at 25% 25%, #fff3cd, #ffa502 40%, #ff6b35 70%, #c44569 100%)",
                    "position": "absolute",
                    "top": "calc(25vh - 150px)",
                    "right": "40vh",
                    "boxShadow": "0 25px 50px rgba(255, 107, 53, 0.5), inset -10px -10px 20px rgba(196, 69, 105, 0.3), inset 10px 10px 20px rgba(255, 255, 255, 0.2)",
                    "zIndex": "2"
                }),
                
                # 黃色條塊 - 中間（短版）- 水平
                html.Div(style={
                    "width": "calc(40vh - 75px)",
                    "height": "150px",
                    "background": "linear-gradient(135deg, #feca57 0%, #ff9ff3 50%, #f368e0 100%)",
                    "position": "absolute",
                    "top": "25vh",
                    "right": "0px",
                    "boxShadow": "0 20px 60px rgba(254, 202, 87, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)"
                }),
                # 大黃色球體
                html.Div(style={
                    "width": "150px",
                    "height": "150px",
                    "borderRadius": "50%",
                    "background": "radial-gradient(circle at 25% 25%, #fff9e6, #ffd700 30%, #feca57 60%, #f368e0 100%)",
                    "position": "absolute",
                    "top": "25vh",
                    "right": "calc(40vh - 150px)",
                    "boxShadow": "0 25px 50px rgba(254, 202, 87, 0.5), inset -10px -10px 20px rgba(243, 104, 224, 0.3), inset 10px 10px 20px rgba(255, 255, 255, 0.2)",
                    "zIndex": "2"
                }),
                
                # 青綠色條塊 - 底部 - 水平
                html.Div(style={
                    "width": "calc(40vh + 75px)",
                    "height": "150px",
                    "background": "linear-gradient(135deg, #48cae4 0%, #0096c7 50%, #023e8a 100%)",
                    "position": "absolute",
                    "top": "calc(25vh + 150px)",
                    "right": "0px",
                    "borderRadius": "0 0 20px 0",
                    "boxShadow": "0 20px 60px rgba(72, 202, 228, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)"
                }),
                # 大青綠色球體
                html.Div(style={
                    "width": "150px",
                    "height": "150px",
                    "borderRadius": "50%",
                    "background": "radial-gradient(circle at 25% 25%, #e0f7ff, #48cae4 30%, #0096c7 60%, #023e8a 100%)",
                    "position": "absolute",
                    "top": "calc(25vh + 150px)",
                    "right": "40vh",
                    "boxShadow": "0 25px 50px rgba(72, 202, 228, 0.5), inset -10px -10px 20px rgba(2, 62, 138, 0.3), inset 10px 10px 20px rgba(255, 255, 255, 0.2)",
                    "zIndex": "2"
                }),
                
                # 白色圓環
                html.Div(style={
                    "width": "140px",
                    "height": "140px",
                    "borderRadius": "50%",
                    "background": "radial-gradient(circle at 30% 30%, #ffffff, #f8f9fa)",
                    "position": "absolute",
                    "top": "calc(25vh + 5px)",
                    "right": "40vh",
                    "boxShadow": "0 20px 60px rgba(0,0,0,0.15), inset 0 5px 20px rgba(255, 255, 255, 0.8), inset 0 -5px 20px rgba(0, 0, 0, 0.1)",
                    "zIndex": "4"
                }),
                
                # 綠色圓圈
                html.Div(style={
                    "width": "80px",
                    "height": "80px",
                    "borderRadius": "50%",
                    "background": "radial-gradient(circle at 30% 30%, #2ed573, #17a2b8)",
                    "position": "absolute",
                    "top": "calc(25vh + 35px)",
                    "right": "calc(40vh + 30px)",
                    "boxShadow": "inset 0 5px 10px rgba(255, 255, 255, 0.3), inset 0 -5px 10px rgba(23, 162, 184, 0.3)",
                    "zIndex": "5"
                })
            ], style={
                "position": "absolute",
                "top": "0",
                "right": "0",
                "width": "50%",
                "height": "100%",
                "overflow": "hidden"
            })
        ], style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "padding": "100px 40px",
            "minHeight": "70vh",
            "position": "relative"
        })
    ], style={
        "background": "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        "borderRadius": "20px",
        "margin": "20px",
        "overflow": "hidden",
        "position": "relative"
    }),
    
    # What we do Section
    html.Div([
        html.Div([
            html.H2("我們提供什麼服務？", style={
                "textAlign": "center",
                "fontSize": "2.5rem",
                "fontWeight": "bold",
                "color": "#333",
                "marginBottom": "20px"
            }),
            html.P("988廚房智慧管理系統為您的企業提供完整的數位化解決方案，從庫存控制到銷售分析，讓您的業務營運更加高效智慧。", 
                   style={
                       "textAlign": "center",
                       "color": "#666",
                       "fontSize": "1.1rem",
                       "maxWidth": "600px",
                       "margin": "0 auto 60px"
                   })
        ]),
        
        # Service Cards
        html.Div([
            # 庫存管理 Card
            html.Div([
                html.Div([
                    html.H4("庫存管理", style={"color": "white", "marginBottom": "10px"}),
                    html.P("智慧追蹤商品庫存狀況，自動提醒補貨時機，確保營運順暢無虞。", 
                           style={"color": "rgba(255,255,255,0.8)", "fontSize": "0.9rem"})
                ], style={"padding": "30px"})
            ], style={
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "borderRadius": "15px",
                "width": "250px",
                "height": "200px",
                "position": "relative",
                "overflow": "hidden"
            }),
            
            # 客戶管理 Card
            html.Div([
                html.Div([
                    html.H4("客戶管理", style={"color": "white", "marginBottom": "10px"}),
                    html.P("完整的客戶資料管理，追蹤交易記錄與消費習慣，提升客戶服務品質。", 
                           style={"color": "rgba(255,255,255,0.8)", "fontSize": "0.9rem"})
                ], style={"padding": "30px"})
            ], style={
                "background": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                "borderRadius": "15px",
                "width": "250px",
                "height": "200px",
                "position": "relative",
                "overflow": "hidden"
            }),
            
            # 銷售分析 Card
            html.Div([
                html.Div([
                    html.H4("銷售分析", style={"color": "white", "marginBottom": "10px"}),
                    html.P("深度數據分析與視覺化報表，洞察市場趨勢，制定精準營銷策略。", 
                           style={"color": "rgba(255,255,255,0.8)", "fontSize": "0.9rem"})
                ], style={"padding": "30px"})
            ], style={
                "background": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                "borderRadius": "15px",
                "width": "250px",
                "height": "200px",
                "position": "relative",
                "overflow": "hidden"
            }),
            
            # 銷貨預測 Card
            html.Div([
                html.Div([
                    html.H4("銷貨預測", style={"color": "white", "marginBottom": "10px"}),
                    html.P("運用智慧演算法分析歷史數據，預測未來銷售趨勢，協助決策規劃。", 
                           style={"color": "rgba(255,255,255,0.8)", "fontSize": "0.9rem"})
                ], style={"padding": "30px"})
            ], style={
                "background": "linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)",
                "borderRadius": "15px",
                "width": "250px",
                "height": "200px",
                "position": "relative",
                "overflow": "hidden"
            })
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "gap": "30px",
            "flexWrap": "wrap"
        })
    ], style={"padding": "80px 40px"}),
    
])

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