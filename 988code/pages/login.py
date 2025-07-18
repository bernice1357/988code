from .common import *
from dash import ALL, callback_context
from dash.exceptions import PreventUpdate

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
    
    # 這裡可以加入實際的登入驗證邏輯
    # 目前先做簡單的示範驗證
    if username == "admin" and password == "password":
        # 登入成功，儲存登入狀態到 cookie
        login_data = {
            "logged_in": True,
            "username": username,
            "login_time": datetime.now().isoformat(),
            "remember_me": remember_me
        }
        
        # 清空輸入框
        return login_data, True, f"登入成功！歡迎 {username}", False, "", "", ""
    else:
        # 登入失敗
        return dash.no_update, False, "", True, "使用者名稱或密碼錯誤", dash.no_update, ""

# 檢查登入狀態
@app.callback(
    Output("url", "pathname"),
    Input("login-status", "data"),
    prevent_initial_call=True
)
def redirect_after_login(login_data):
    if login_data and login_data.get("logged_in"):
        # 登入成功後重定向到首頁
        return "/"
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