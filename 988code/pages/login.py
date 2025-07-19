from .common import *
from dash import ALL, callback_context
from dash.exceptions import PreventUpdate
import requests
import json

layout = dbc.Container([
    dcc.Store(id="login-status", storage_type='local'),
    
    # 登入卡片
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H3("系統登入", className="text-center mb-0", style={"color": "#2c3e50"})
                ], style={"backgroundColor": "#f8f9fa"}),
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-user-circle", style={"fontSize": "4rem", "color": "#6c757d"})
                        ], className="text-center mb-4"),
                        
                        dbc.Form([
                            dbc.Row([
                                dbc.Label("使用者名稱", width=12, style={"fontWeight": "bold"}),
                                dbc.Col([
                                    dbc.Input(
                                        id="username-input",
                                        type="text",
                                        placeholder="請輸入使用者名稱",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Label("密碼", width=12, style={"fontWeight": "bold"}),
                                dbc.Col([
                                    dbc.Input(
                                        id="password-input",
                                        type="password",
                                        placeholder="請輸入密碼",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Checkbox(
                                        id="remember-me",
                                        label="記住我",
                                        value=False,
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        "登入",
                                        id="login-submit-btn",
                                        color="primary",
                                        size="lg",
                                        className="w-100",
                                        style={"fontSize": "18px", "fontWeight": "bold"}
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        "註冊",
                                        id="register-btn",
                                        color="outline-secondary",
                                        size="lg",
                                        className="w-100 mt-2",
                                        style={"fontSize": "16px"}
                                    )
                                ], width=12)
                            ])
                        ])
                    ])
                ], style={"padding": "2rem"})
            ], style={"boxShadow": "0 4px 8px rgba(0,0,0,0.1)", "border": "none"})
        ], width=4)
    ], justify="center", className="min-vh-100 d-flex align-items-center"),
    
    # Toast 通知
    success_toast("login", message=""),
    error_toast("login", message=""),
    
], fluid=True, style={"backgroundColor": "#f5f5f5"})

# 登入處理
@app.callback(
    [Output("login-status", "data"),
     Output("login-success-toast", "is_open"),
     Output("login-success-toast", "children"),
     Output("login-error-toast", "is_open"),
     Output("login-error-toast", "children"),
     Output("username-input", "value"),
     Output("password-input", "value")],
    Input("login-submit-btn", "n_clicks"),
    [State("username-input", "value"),
     State("password-input", "value"),
     State("remember-me", "value")],
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password, remember_me):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # 驗證輸入
    if not username or not password:
        return dash.no_update, False, "", True, "請輸入使用者名稱和密碼", dash.no_update, dash.no_update
    
    try:
        # 呼叫登入 API
        response = requests.post("http://127.0.0.1:8000/login", 
                               json={"username": username, "password": password})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                # 登入成功，儲存登入狀態到 localStorage
                user_data = result.get("user", {})
                login_data = {
                    "logged_in": True,
                    "username": user_data.get("username"),
                    "email": user_data.get("email"),
                    "full_name": user_data.get("full_name"),
                    "role": user_data.get("role"),
                    "login_time": datetime.now().isoformat(),
                    "remember_me": remember_me
                }
                
                # 清空輸入框
                welcome_message = f"登入成功！歡迎 {user_data.get('full_name', username)}"
                return login_data, True, welcome_message, False, "", "", ""
            else:
                # 登入失敗
                error_message = result.get("message", "登入失敗")
                return dash.no_update, False, "", True, error_message, dash.no_update, ""
        else:
            return dash.no_update, False, "", True, "伺服器連接失敗", dash.no_update, ""
            
    except requests.exceptions.RequestException as e:
        print(f"登入 API 請求錯誤: {e}")
        return dash.no_update, False, "", True, "網路連接錯誤", dash.no_update, ""
    except Exception as e:
        print(f"登入處理錯誤: {e}")
        return dash.no_update, False, "", True, "系統錯誤", dash.no_update, ""



# 註冊按鈕處理
# 檢查登入狀態並處理頁面導向
@app.callback(
    Output("url", "pathname"),
    [Input("login-status", "data"),
     Input("register-btn", "n_clicks")],
    prevent_initial_call=True
)
def handle_navigation(login_data, register_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "login-status" and login_data and login_data.get("logged_in"):
        # 登入成功後重定向到首頁
        return "/"
    elif trigger_id == "register-btn" and register_clicks:
        # 點擊註冊按鈕
        return "/register"
    
    return dash.no_update

# Enter 鍵登入
@app.callback(
    Output("login-submit-btn", "n_clicks"),
    [Input("username-input", "n_submit"),
     Input("password-input", "n_submit")],
    [State("login-submit-btn", "n_clicks")],
    prevent_initial_call=True
)
def enter_key_login(username_submit, password_submit, current_clicks):
    if username_submit or password_submit:
        return (current_clicks or 0) + 1
    return dash.no_update