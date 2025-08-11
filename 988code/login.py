from pages.common import *
from dash import ALL, callback_context, clientside_callback, ClientsideFunction
import requests
from datetime import datetime
import json
import time

layout = html.Div([
    dcc.Location(id='login-redirect', refresh=True),
    html.Div(id='hidden-role', style={'display': 'none'}),
    # 主要容器
    html.Div([
        # 左側背景區域 - 現代化設計
        html.Div([
            # 彩色條塊和球體裝飾
            html.Div([
                # 紫色條塊 - 左邊1/3
                html.Div(style={
                    "width": "200px",
                    "height": "40vh",
                    "background": "linear-gradient(180deg, #4703b7 0%, #3d0399 100%)",
                    "position": "absolute",
                    "left": "calc((100% - 600px) / 2)",
                    "top": "0px"
                }),
                # 紫色球體
                html.Div(style={
                    "width": "200px",
                    "height": "200px",
                    "borderRadius": "50%",
                    "background": "radial-gradient(circle at 25% 25%, #E5CCFF, #7209B7 40%, #4703b7 70%, #3d0399 100%)",
                    "position": "absolute",
                    "left": "calc((100% - 600px) / 2)",
                    "top": "calc(40vh - 100px)",
                    "boxShadow": "0 25px 50px rgba(71, 3, 183, 0.5), inset -10px -10px 20px rgba(61, 3, 153, 0.3), inset 10px 10px 20px rgba(255, 255, 255, 0.2)",
                    "zIndex": "2"
                }),
                
                # 藍色條塊 - 中間1/3
                html.Div(style={
                    "width": "200px",
                    "height": "60vh",
                    "background": "linear-gradient(180deg, #0464f3 0%, #0344c4 100%)",
                    "position": "absolute",
                    "left": "calc(((100% - 600px) / 2) + 200px)",
                    "top": "0px"
                }),
                # 藍色球體
                html.Div(style={
                    "width": "200px",
                    "height": "200px",
                    "borderRadius": "50%",
                    "background": "radial-gradient(circle at 25% 25%, #B3D9FF, #0464f3 40%, #0344c4 70%, #022e9a 100%)",
                    "position": "absolute",
                    "left": "calc(((100% - 600px) / 2) + 200px)",
                    "top": "calc(60vh - 100px)",
                    "boxShadow": "0 25px 50px rgba(4, 100, 243, 0.5), inset -10px -10px 20px rgba(2, 46, 154, 0.3), inset 10px 10px 20px rgba(255, 255, 255, 0.2)",
                    "zIndex": "2"
                }),
                
                # 綠色條塊 - 右邊1/3
                html.Div(style={
                    "width": "200px",
                    "height": "30vh", 
                    "background": "linear-gradient(180deg, #83e100 0%, #6bb800 100%)",
                    "position": "absolute",
                    "left": "calc(((100% - 600px) / 2) + 400px)",
                    "top": "0px"
                }),
                # 綠色球體
                html.Div(style={
                    "width": "200px",
                    "height": "200px",
                    "borderRadius": "50%",
                    "background": "radial-gradient(circle at 25% 25%, #E8FFB3, #9EE433 40%, #83e100 70%, #6bb800 100%)",
                    "position": "absolute",
                    "left": "calc(((100% - 600px) / 2) + 400px)",
                    "top": "calc(30vh - 100px)",
                    "boxShadow": "0 25px 50px rgba(131, 225, 0, 0.5), inset -10px -10px 20px rgba(107, 184, 0, 0.3), inset 10px 10px 20px rgba(255, 255, 255, 0.2)",
                    "zIndex": "2"
                })
            ], style={
                "position": "absolute",
                "top": "0",
                "left": "0",
                "width": "100%",
                "height": "100%"
            }),
            
            # 文字內容
            html.Div([
                html.H1("988廚房", 
                    style={
                        "color": "white", 
                        "fontSize": "3rem", 
                        "fontWeight": "bold",
                        "lineHeight": "1.1",
                        "marginBottom": "0.5rem",
                        "textShadow": "0 2px 10px rgba(0,0,0,0.3)"
                    }),
                html.H2("智慧管理系統",
                    style={
                        "color": "white", 
                        "fontSize": "2rem", 
                        "fontWeight": "300",
                        "lineHeight": "1.2",
                        "marginBottom": "1rem",
                        "textShadow": "0 2px 10px rgba(0,0,0,0.3)"
                    }),
                html.P("專業的B2B管理解決方案，讓您的業務更智慧、更高效",
                    style={
                        "color": "rgba(255,255,255,0.9)", 
                        "fontSize": "1.1rem",
                        "lineHeight": "1.5",
                        "textShadow": "0 1px 5px rgba(0,0,0,0.3)"
                    })
            ], style={
                "position": "absolute",
                "bottom": "4rem",
                "left": "3rem",
                "right": "3rem",
                "zIndex": "2"
            })
        ], style={
            "width": "50%",
            "height": "100vh",
            "background": "#1F2937",
            "position": "relative",
            "overflow": "hidden"
        }),
        
        # 右側登入區域
        html.Div([
            # Logo區域
            html.Div([
                html.Img(src="/assets/images/logo.png", style={
                    "height": "40px",
                    "maxWidth": "200px"
                })
            ], style={"textAlign": "center", "marginBottom": "3rem", "paddingTop": "2rem"}),
            
            html.Div([
                # 登入表單
                html.Div([
                    html.H2("歡迎回來", style={
                        "fontSize": "2.5rem",
                        "fontWeight": "300",
                        "color": "#333",
                        "marginBottom": "0.5rem"
                    }),
                    html.P("請輸入您的帳號和密碼以存取您的帳戶", style={
                        "color": "#666",
                        "marginBottom": "2.5rem",
                        "fontSize": "1rem"
                    }),
                    
                    # 帳號輸入
                    html.Div([
                        html.Label("帳號", style={
                            "display": "block",
                            "marginBottom": "0.5rem",
                            "color": "#333",
                            "fontSize": "0.95rem",
                            "fontWeight": "500"
                        }),
                        dbc.Input(
                            id="username-input",
                            type="text",
                            placeholder="請輸入您的帳號",
                            style={
                                "border": "1px solid #e0e0e0",
                                "borderRadius": "8px",
                                "padding": "0.75rem 1.25rem",
                                "fontSize": "1rem",
                                "marginBottom": "1.5rem",
                                "backgroundColor": "#f8f9fa",
                                "width": "100%"
                            }
                        )
                    ]),
                    
                    # Password輸入
                    html.Div([
                        html.Label("密碼", style={
                            "display": "block",
                            "marginBottom": "0.5rem",
                            "color": "#333",
                            "fontSize": "0.95rem",
                            "fontWeight": "500"
                        }),
                        dbc.Input(
                            id="password-input",
                            type="password",
                            placeholder="請輸入您的密碼",
                            style={
                                "border": "1px solid #e0e0e0",
                                "borderRadius": "8px",
                                "padding": "0.75rem 1.25rem",
                                "fontSize": "1rem",
                                "marginBottom": "2rem",
                                "backgroundColor": "#f8f9fa",
                                "width": "100%"
                            }
                        )
                    ]),
                    

                    
                    # 登入按鈕
                    dbc.Button(
                        "登入",
                        id="login-submit-btn",
                        style={
                            "width": "100%",
                            "backgroundColor": "#000",
                            "border": "none",
                            "borderRadius": "8px",
                            "padding": "0.75rem",
                            "fontSize": "1rem",
                            "fontWeight": "500",
                            "marginBottom": "2rem"
                        }
                    )
                    
                ], style={"maxWidth": "550px", "margin": "0 auto"})
                
            ], style={
                "padding": "2rem",
                "height": "calc(100vh - 120px)",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center"
            })
        ], style={
            "width": "50%",
            "backgroundColor": "white",
            "position": "relative"
        })
        
    ], style={
        "display": "flex",
        "height": "100vh",
        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    }),
    
    # Toast 通知
    success_toast("login", message=""),
    error_toast("login", message=""),
    
], style={"margin": "0", "padding": "0"})

# 登入處理
@app.callback(
    [Output("login-success-toast", "is_open"),
     Output("login-success-toast", "children"),
     Output("login-error-toast", "is_open"),
     Output("login-error-toast", "children"),
     Output("username-input", "value"),
     Output("password-input", "value"),
     Output("login_status", "data"),
     Output("login-redirect", "href")],
    Input("login-submit-btn", "n_clicks"),
    [State("username-input", "value"),
     State("password-input", "value")],
    prevent_initial_call=True
)
def handle_login(btn_clicks, username, password):
    # 檢查是否有任何觸發
    if not btn_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # 驗證輸入
    if not username or not password:
        return False, "", True, "請輸入使用者名稱和密碼", dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        # 呼叫登入 API
        response = requests.post("http://127.0.0.1:8000/login", 
                               json={"username": username, "password": password})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                # 登入成功，取得 role
                user_data = result.get("user", {})
                role = user_data.get("role")
                full_name = user_data.get("full_name")
                
                # 建立登入狀態字典，包含 role 和過期時間（現在時間+2小時）
                from datetime import datetime, timedelta
                exp_time = datetime.now() + timedelta(hours=2)
                login_data = {
                    "role": role,
                    "exp": exp_time.strftime("%Y-%m-%d %H:%M:%S")  # 時間格式字串
                }
                
                # 清空輸入框並跳轉頁面
                welcome_message = f"登入成功！歡迎 {full_name}"
                
                return True, welcome_message, False, "", "", "", login_data, "/new_orders"
            else:
                # 登入失敗
                error_message = result.get("message", "登入失敗")
                return False, "", True, error_message, dash.no_update, "", dash.no_update, dash.no_update
        else:
            return False, "", True, "帳號或密碼錯誤", dash.no_update, "", dash.no_update, dash.no_update
            
    except requests.exceptions.RequestException as e:
        return False, "", True, f"登入 API 請求錯誤: {e}", dash.no_update, "", dash.no_update, dash.no_update
    except Exception as e:
        return False, "", True, f"登入處理錯誤: {e}", dash.no_update, "", dash.no_update, dash.no_update