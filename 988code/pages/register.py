from .common import *
from dash import ALL, callback_context
from dash.exceptions import PreventUpdate
import requests
import json

layout = dbc.Container([
    # 註冊卡片
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H3("註冊新帳號", className="text-center mb-0", style={"color": "#2c3e50"})
                ], style={"backgroundColor": "#f8f9fa"}),
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-user-plus", style={"fontSize": "4rem", "color": "#6c757d"})
                        ], className="text-center mb-4"),
                        
                        dbc.Form([
                            dbc.Row([
                                dbc.Label("使用者名稱", width=12, style={"fontWeight": "bold"}),
                                dbc.Col([
                                    dbc.Input(
                                        id="reg-username-input",
                                        type="text",
                                        placeholder="請輸入使用者名稱",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Label("電子郵件", width=12, style={"fontWeight": "bold"}),
                                dbc.Col([
                                    dbc.Input(
                                        id="reg-email-input",
                                        type="email",
                                        placeholder="請輸入電子郵件",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Label("姓名", width=12, style={"fontWeight": "bold"}),
                                dbc.Col([
                                    dbc.Input(
                                        id="reg-fullname-input",
                                        type="text",
                                        placeholder="請輸入姓名",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Label("密碼", width=12, style={"fontWeight": "bold"}),
                                dbc.Col([
                                    dbc.Input(
                                        id="reg-password-input",
                                        type="password",
                                        placeholder="請輸入密碼",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Label("確認密碼", width=12, style={"fontWeight": "bold"}),
                                dbc.Col([
                                    dbc.Input(
                                        id="reg-confirm-password-input",
                                        type="password",
                                        placeholder="請再次輸入密碼",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Label("角色", width=12, style={"fontWeight": "bold"}),
                                dbc.Col([
                                    dbc.Select(
                                        id="reg-role-select",
                                        options=[
                                            {"label": "一般使用者", "value": "user"},
                                            {"label": "管理員", "value": "admin"},
                                            {"label": "主管", "value": "manager"}
                                        ],
                                        value="user",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        "註冊",
                                        id="register-submit-btn",
                                        color="success",
                                        size="lg",
                                        className="w-100",
                                        style={"fontSize": "18px", "fontWeight": "bold"}
                                    )
                                ], width=12)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        "返回登入",
                                        id="back-to-login-btn",
                                        color="outline-primary",
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
    success_toast("register", message=""),
    error_toast("register", message=""),
    
], fluid=True, style={"backgroundColor": "#f5f5f5"})

# 註冊處理
@app.callback(
    [Output("register-success-toast", "is_open"),
     Output("register-success-toast", "children"),
     Output("register-error-toast", "is_open"),
     Output("register-error-toast", "children"),
     Output("reg-username-input", "value"),
     Output("reg-email-input", "value"),
     Output("reg-fullname-input", "value"),
     Output("reg-password-input", "value"),
     Output("reg-confirm-password-input", "value")],
    Input("register-submit-btn", "n_clicks"),
    [State("reg-username-input", "value"),
     State("reg-email-input", "value"),
     State("reg-fullname-input", "value"),
     State("reg-password-input", "value"),
     State("reg-confirm-password-input", "value"),
     State("reg-role-select", "value")],
    prevent_initial_call=True
)
def handle_register(n_clicks, username, email, full_name, password, confirm_password, role):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # 驗證輸入
    if not all([username, email, full_name, password, confirm_password]):
        return False, "", True, "請填寫所有必填欄位", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if password != confirm_password:
        return False, "", True, "密碼與確認密碼不符", dash.no_update, dash.no_update, dash.no_update, "", ""
    
    if len(password) < 6:
        return False, "", True, "密碼長度至少需要6個字元", dash.no_update, dash.no_update, dash.no_update, "", ""
    
    try:
        # 呼叫註冊 API
        register_data = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "password": password,
            "role": role
        }
        
        response = requests.post("http://127.0.0.1:8000/register", json=register_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                # 註冊成功，清空所有輸入框
                return True, "註冊成功！請使用新帳號登入", False, "", "", "", "", "", ""
            else:
                # 註冊失敗
                error_message = result.get("message", "註冊失敗")
                return False, "", True, error_message, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        elif response.status_code == 400:
            return False, "", True, "使用者名稱或電子郵件已存在", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        else:
            return False, "", True, "伺服器連接失敗", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
    except requests.exceptions.RequestException as e:
        print(f"註冊 API 請求錯誤: {e}")
        return False, "", True, "網路連接錯誤", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    except Exception as e:
        print(f"註冊處理錯誤: {e}")
        return False, "", True, "系統錯誤", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Enter 鍵註冊
@app.callback(
    Output("register-submit-btn", "n_clicks"),
    [Input("reg-username-input", "n_submit"),
     Input("reg-email-input", "n_submit"),
     Input("reg-fullname-input", "n_submit"),
     Input("reg-password-input", "n_submit"),
     Input("reg-confirm-password-input", "n_submit")],
    [State("register-submit-btn", "n_clicks")],
    prevent_initial_call=True
)
def enter_key_register(username_submit, email_submit, fullname_submit, password_submit, confirm_submit, current_clicks):
    if any([username_submit, email_submit, fullname_submit, password_submit, confirm_submit]):
        return (current_clicks or 0) + 1
    return dash.no_update

dbc.Row([
    dbc.Col([
        dbc.NavLink(
            "返回登入",
            href="/login",
            className="btn btn-outline-primary btn-lg w-100 mt-2",
            style={"fontSize": "16px", "textDecoration": "none"}
        )
    ], width=12)
])