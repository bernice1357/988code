from pages.common import *
from dash import ALL, callback_context, clientside_callback, ClientsideFunction
import requests
from datetime import datetime
import json

layout = html.Div([
    dcc.Location(id='login-redirect', refresh=True),
    html.Div(id='hidden-role', style={'display': 'none'}),
    # 主要容器
    html.Div([
        # 左側背景區域
        html.Div([
            html.Div([
                html.H1("The important thing is not to stop questioning.", 
                    style={
                        "color": "white", 
                        "fontSize": "2.5rem", 
                        "fontWeight": "bold",
                        "lineHeight": "1.1",
                        "marginBottom": "1rem"
                    }),
                html.P("—— Albert Einstein",
                    style={
                        "color": "rgba(255,255,255,0.8)", 
                        "fontSize": "1rem",
                        "lineHeight": "1.5"
                    })
            ], style={
                "position": "absolute",
                "bottom": "3rem",
                "left": "3rem",
                "right": "3rem"
            })
        ], style={
            "width": "50%",
            "height": "100vh",
            "background": "linear-gradient(135deg, rgba(41,100,138,0.8) 0%, rgba(58,124,168,0.7) 30%, rgba(79,172,254,0.6) 60%, rgba(255,215,0,0.5) 100%)",
            "position": "relative",
            "backgroundImage": "url('/assets/images/milad-fakurian-oU-qoEjNnHM-unsplash.jpg')",
            "backgroundSize": "cover",
            "backgroundPosition": "center",
            "backgroundRepeat": "no-repeat",
            "backgroundSize": "cover",
            "backgroundPosition": "center"
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
    
    # 用來觸發設定 cookie 的 Store
    dcc.Store(id='user-role-store', data=None),
    
    # 添加 cookie-setter 元素
    html.Div(id='cookie-setter', style={'display': 'none'}),
    
], style={"margin": "0", "padding": "0"})

# 登入處理
@app.callback(
    [Output("login-success-toast", "is_open"),
     Output("login-success-toast", "children"),
     Output("login-error-toast", "is_open"),
     Output("login-error-toast", "children"),
     Output("username-input", "value"),
     Output("password-input", "value"),
     Output("user-role-store", "data"),
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
                
                # 清空輸入框並跳轉頁面
                welcome_message = f"登入成功！歡迎 {full_name}"
                
                return True, welcome_message, False, "", "", "", role, "/new_orders"
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