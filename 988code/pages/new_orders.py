'''
首頁 預設顯示customer_id+name，沒有就顯示line_id
confirmed_by:帳號名稱、confirmed_at:確認時間
datetime.now()取得當前時間
'''

from .common import *
from dash import ALL
from datetime import datetime

# 載入訂單資料的函數
def get_orders():
    response = requests.get("http://127.0.0.1:8000/get_new_orders")
    if response.status_code == 200:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("回應內容不是有效的 JSON")
            return []
    else:
        print(f"API 錯誤，狀態碼：{response.status_code}")
        return []

def make_card_item(order):
    # 獲取客戶備註
    customer_notes = ""
    if order.get("customer_id"):
        try:
            notes_response = requests.get(f"http://127.0.0.1:8000/get_customer_notes/{order['customer_id']}")
            if notes_response.status_code == 200:
                notes_data = notes_response.json()
                customer_notes = notes_data.get("notes", "")
        except:
            customer_notes = ""
    
    # 卡片標題：左邊顯示客戶ID
    if order.get("customer_id"):
        title = html.Div([
            html.Span(order["customer_id"], style={
                "color": "black", 
                "fontWeight": "bold", 
                "fontSize": "0.9rem"
            }),
            html.Span(" ", style={"fontSize": "0.9rem"}),
            html.Span(order["customer_name"], style={
                "color": "#6c757d", 
                "fontSize": "0.9rem"
            })
        ], style={
            "whiteSpace": "nowrap", 
            "overflow": "hidden", 
            "textOverflow": "ellipsis",
            "paddingTop": "8px",
            "flex": "1", 
            "minWidth": "0"
        })
    else:
        title = html.Div([
            html.Span(
                order["line_id"], 
                style={
                    "fontWeight": "bold", 
                    "fontSize": "0.9rem", 
                    "color": "black",
                    "paddingTop": "8px"
                }
            )
        ], style={
            "whiteSpace": "nowrap", 
            "overflow": "hidden", 
            "textOverflow": "ellipsis",
            "flex": "1", 
            "minWidth": "0"
        })
    return dbc.Card([
        dbc.CardHeader([
            title,
            html.Div([
                dbc.Badge("新品提醒", color="danger", className="me-2 rounded-pill", style={"fontSize": "0.7rem", "padding": "4px 8px"}) if order.get("is_new_product") == "true" or order.get("is_new_product") == True else None,
                dbc.Badge("備註與歷史提醒", color="danger", className="me-2 rounded-pill", style={"fontSize": "0.7rem", "padding": "4px 8px"})
            ], style={"marginTop": "8px", "lineHeight": "1"})
        ], style={"overflow": "hidden"}),
        dbc.CardBody([
            # 對話紀錄區塊
            html.Div([
                html.Small("對話紀錄", className="text-info mb-1 d-block"),
                html.Pre(order["conversation_record"], style={"whiteSpace": "pre-wrap", "fontSize": "0.9rem"})
            ], className="mb-3"),
            html.Div(style={"borderTop": "1px solid #dee2e6", "margin": "15px 0"}),
            # 購買紀錄區塊
            html.Div([
                html.Small("購買品項", className="text-info mb-1 d-block"),
                html.Div([
                    html.Span(order.get('product_id', ''), style={"color": "black", "fontWeight": "bold", "fontSize": "0.9rem"}) if order.get('product_id') else None,
                    html.Span(" ", style={"fontSize": "0.9rem"}) if order.get('product_id') else None,
                    html.Span(order['purchase_record'], style={"fontSize": "0.9rem", "whiteSpace": "pre-wrap"})
                ], style={"whiteSpace": "pre-wrap"})
            ], className="mb-3"),
            html.Div(style={"borderTop": "1px solid #dee2e6", "margin": "15px 0"}),
            # 歷史備註區塊
            html.Div([
                html.Small("歷史備註", className="text-info mb-1 d-block"),
                html.Pre(customer_notes, style={"whiteSpace": "pre-wrap", "fontSize": "0.9rem"})
            ], className="mb-3"),
            html.Div(style={"margin": "20px 0"}),
            # 建立時間
            html.Div([
                html.Small(f"建立時間: {order['created_at'][:16].replace('T', ' ')}", className="text-muted", style={"fontSize": "0.7rem"}),
                html.Div([
                    dbc.Button("確定", id={"type": "confirm-btn", "index": order['id']}, size="sm", color="dark", outline=True, className="me-2") if order.get("status") == "0" else None,
                    dbc.Button("刪除", id={"type": "delete-btn", "index": order['id']}, size="sm", color="danger", outline=True) if order.get("status") == "0" else None
                ]) if order.get("status") == "0" else None
            ], className="d-flex justify-content-between align-items-center mt-2")
        ])
    ], style={"backgroundColor": "#f8f9fa", "border": "1px solid #dee2e6", "position": "relative"}, className="mb-3")

def get_modal_fields(customer_id, customer_name, purchase_record):
    # 不管有沒有customer_id，都顯示三個欄位
    return [
        dbc.Row([
            dbc.Label("客戶 ID", width=3),
            dbc.Col(dbc.Input(
                id="customer-id", 
                type="text",
                value=customer_id if customer_id else "",
                disabled=bool(customer_id)  # 有customer_id就禁用編輯
            ), width=9)
        ], className="mb-3"),
        dbc.Row([
            dbc.Label("客戶名稱", width=3),
            dbc.Col(dbc.Input(
                id="customer-name", 
                type="text",
                value=customer_name if customer_name else "",
                disabled=bool(customer_id)  # 有customer_id就禁用編輯
            ), width=9)
        ], className="mb-3"),
        dbc.Row([
            dbc.Label("購買品項", width=3),
            dbc.Col(dbc.Input(id="purchase-record", value=purchase_record), width=9)
        ], className="mb-3")
    ]

orders = get_orders()

layout = dbc.Container([
    success_toast("new_orders", message="訂單已確認"),
    error_toast("new_orders", message=""),
    warning_toast("new_orders", message=""),
    dcc.Store(id='user-role-store'),
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30秒更新一次
        n_intervals=0
    ),
    html.Div([
        html.Div(),  # 空的div佔位
        dbc.ButtonGroup([
            dbc.Button("全部", id="filter-all", color="primary", outline=False),
            dbc.Button("未確認", id="filter-unconfirmed", color="primary", outline=True),
            dbc.Button("已確認", id="filter-confirmed", color="primary", outline=True),
            dbc.Button("已刪除", id="filter-deleted", color="primary", outline=True)
        ])
    ], className="d-flex justify-content-between align-items-center mb-4"),
    dcc.Loading(
        id="loading-orders",
        type="dot",
        children=dbc.Row(id="orders-container", className="g-3", children=[dbc.Col(make_card_item(order), width=4) for order in orders], style={
            "maxHeight": "80vh", 
            "overflowY": "auto"
        } if len(orders) > 6 else {}),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "minHeight": "60vh"
        }
    ),
    dbc.Modal([
        dbc.ModalHeader("確認訂單", id="modal-header", style={"fontWeight": "bold", "fontSize": "24px"}),
        dbc.ModalBody(id="modal-body-content"),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-modal", color="secondary", outline=True),
            dbc.Button("確認", id="submit-confirm", color="primary")
        ])
    ], id="confirm-modal", is_open=False, centered=True),
    dbc.Modal([
        dbc.ModalHeader("確認刪除", style={"fontWeight": "bold", "fontSize": "24px"}),
        dbc.ModalBody(id="delete-modal-body", children="確定要刪除這筆訂單嗎？"),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-delete", color="secondary", outline=True),
            dbc.Button("刪除", id="submit-delete", color="danger")
        ])
    ], id="delete-modal", is_open=False)
], fluid=True)

# 定時更新訂單
@app.callback(
    Output("orders-container", "children"),
    Input('interval-component', 'n_intervals')
)
def update_orders(n):
    orders = get_orders()
    return [dbc.Col(make_card_item(order), width=4) for order in orders]

# 篩選顯示訂單和更新按鈕狀態
@app.callback(
    [Output("orders-container", "children", allow_duplicate=True),
     Output("filter-all", "outline"),
     Output("filter-unconfirmed", "outline"),
     Output("filter-confirmed", "outline"),
     Output("filter-deleted", "outline")],
    [Input("filter-all", "n_clicks"),
     Input("filter-unconfirmed", "n_clicks"),
     Input("filter-confirmed", "n_clicks"),
     Input("filter-deleted", "n_clicks")],
    prevent_initial_call=True
)
def filter_orders(all_clicks, unconfirmed_clicks, confirmed_clicks, deleted_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered[0]["prop_id"].split('.')[0]
    orders = get_orders()
    
    if triggered_id == "filter-all":
        filtered_orders = orders
        return [dbc.Col(make_card_item(order), width=4) for order in filtered_orders], False, True, True, True
    elif triggered_id == "filter-unconfirmed":
        filtered_orders = [order for order in orders if order.get("status") == "0"]
        return [dbc.Col(make_card_item(order), width=4) for order in filtered_orders], True, False, True, True
    elif triggered_id == "filter-confirmed":
        filtered_orders = [order for order in orders if order.get("status") == "1"]
        return [dbc.Col(make_card_item(order), width=4) for order in filtered_orders], True, True, False, True
    elif triggered_id == "filter-deleted":
        filtered_orders = [order for order in orders if order.get("status") == "2"]
        return [dbc.Col(make_card_item(order), width=4) for order in filtered_orders], True, True, True, False
    else:
        filtered_orders = orders
        return [dbc.Col(make_card_item(order), width=4) for order in filtered_orders], False, True, True, True

# 刪除按鈕，顯示確認刪除modal
@app.callback(
    [Output("delete-modal", "is_open"),
     Output("delete-modal-body", "children")],
    [Input({"type": "delete-btn", "index": ALL}, "n_clicks")],
    [State("delete-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_delete_modal(n_clicks_list, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    triggered_prop = ctx.triggered[0]["prop_id"]
    if not triggered_prop or "delete-btn" not in triggered_prop:
        return dash.no_update, dash.no_update
    
    triggered_value = ctx.triggered[0]["value"]
    if not triggered_value or triggered_value == 0:
        return dash.no_update, dash.no_update
    
    import json
    try:
        button_id = json.loads(triggered_prop.split('.')[0])
        order_id = button_id["index"]
    except:
        return dash.no_update, dash.no_update
    
    orders = get_orders()
    order = next((o for o in orders if str(o["id"]) == str(order_id)), None)
    if order:
        customer_info = order['customer_id'] + order['customer_name'] if order.get("customer_id") else order['line_id']
        message = f"確定要刪除訂單：{customer_info} 嗎？"
        return True, message
    
    return dash.no_update, dash.no_update

# 取消刪除
@app.callback(
    Output("delete-modal", "is_open", allow_duplicate=True),
    Input("cancel-delete", "n_clicks"),
    prevent_initial_call=True
)
def close_delete_modal(n_clicks):
    if n_clicks:
        return False
    return dash.no_update

# 確認刪除
@app.callback(
    [Output("delete-modal", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "children", allow_duplicate=True),
     Output("new_orders-error-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "children", allow_duplicate=True),
     Output("orders-container", "children", allow_duplicate=True)],
    [Input("submit-delete", "n_clicks")],
    [State("delete-modal-body", "children"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def confirm_delete(n_clicks, modal_body, user_role):
    if n_clicks:
        orders = get_orders()
        # 從modal body取得order資訊並找到order_id
        order_id = None
        for order in orders:
            customer_info = order['customer_id'] + order['customer_name'] if order.get("customer_id") else order['line_id']
            expected_message = f"確定要刪除訂單：{customer_info} 嗎？"
            if modal_body == expected_message:
                order_id = order["id"]
                break
        
        if order_id:
            current_time = datetime.now().isoformat()
            
            # 準備更新資料，只更新status為2
            update_data = {
                "status": "2",
                "updated_at": current_time
            }
            
            # 呼叫API更新資料
            try:
                update_data["user_role"] = user_role or "viewer"
                response = requests.put(f"http://127.0.0.1:8000/temp/{order_id}", json=update_data)
                if response.status_code == 200:
                    print("訂單刪除成功")
                    orders = get_orders()
                    updated_orders = [dbc.Col(make_card_item(order), width=4) for order in orders]
                    return False, True, "訂單已刪除，請查看已刪除頁面", False, False, "", updated_orders
                elif response.status_code == 403:
                    return False, False, "", False, True, "權限不足：僅限編輯者使用此功能", dash.no_update
                else:
                    print(f"API 錯誤，狀態碼：{response.status_code}")
                    return False, False, dash.no_update, True, False, "", dash.no_update
            except Exception as e:
                print(f"API 呼叫失敗：{e}")
                return False, False, dash.no_update, True, False, "", dash.no_update
        
        return False, False, dash.no_update, True, False, "", dash.no_update
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output("confirm-modal", "is_open"),
     Output("modal-body-content", "children"),
     Output("modal-header", "children")],
    [Input({"type": "confirm-btn", "index": ALL}, "n_clicks")],
    [State("confirm-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_modal(n_clicks_list, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update
    
    # 檢查是否真的是confirm-btn被點擊
    triggered_prop = ctx.triggered[0]["prop_id"]
    if not triggered_prop or "confirm-btn" not in triggered_prop:
        return dash.no_update, dash.no_update, dash.no_update
    
    # 檢查點擊值是否存在且大於0
    triggered_value = ctx.triggered[0]["value"]
    if not triggered_value or triggered_value == 0:
        return dash.no_update, dash.no_update, dash.no_update
    
    # 解析 order_id
    import json
    try:
        button_id = json.loads(triggered_prop.split('.')[0])
        order_id = button_id["index"]
    except:
        return dash.no_update, dash.no_update, dash.no_update
    
    orders = get_orders()
    # 根據 order_id 找到對應的訂單資料
    order = next((o for o in orders if str(o["id"]) == str(order_id)), None)
    if order:
        # 傳入customer_id, customer_name, purchase_record
        modal_content = get_modal_fields(
            order.get("customer_id"), 
            order.get("customer_name"), 
            order["purchase_record"]
        )
        # 設定標題
        title = f"確認訂單 - {order['customer_id'] + order['customer_name']}" if order.get("customer_id") else f"確認訂單 - {order['line_id']}"
        return True, modal_content, title
    
    return dash.no_update, dash.no_update, dash.no_update

# 訂單取消處理按鈕
@app.callback(
    Output("confirm-modal", "is_open", allow_duplicate=True),
    Input("cancel-modal", "n_clicks"),
    prevent_initial_call=True
)
def close_modal(n_clicks):
    if n_clicks:
        return False
    return dash.no_update

# modal確認送出
@app.callback(
    [Output("confirm-modal", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "children", allow_duplicate=True),
     Output("new_orders-error-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "children", allow_duplicate=True),
     Output("orders-container", "children", allow_duplicate=True)],
    [Input("submit-confirm", "n_clicks")],
    [State("customer-id", "value"),
     State("customer-name", "value"),
     State("purchase-record", "value"),
     State("modal-header", "children"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def submit_confirm(n_clicks, customer_id, customer_name, purchase_record, modal_header, user_role):
    if n_clicks:
        orders = get_orders()
        # 從 modal header 取得 order_id 和原始訂單資料
        order_id = None
        original_order = None
        for order in orders:
            expected_title = f"確認訂單 - {order['customer_id'] + order['customer_name']}" if order.get("customer_id") else f"確認訂單 - {order['line_id']}"
            if modal_header == expected_title:
                order_id = order["id"]
                original_order = order
                break
        
        if order_id and original_order:
            current_time = datetime.now().isoformat()
            
            # 準備更新資料
            update_data = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "purchase_record": purchase_record,
                "updated_at": current_time,
                "status": "1",
                "confirmed_by": "user",
                "confirmed_at": current_time
            }
            
            # 呼叫API更新資料
            try:
                update_data["user_role"] = user_role or "viewer"
                response = requests.put(f"http://127.0.0.1:8000/temp/{order_id}", json=update_data)
                if response.status_code == 200:
                    print("訂單確認成功")
                    orders = get_orders()
                    updated_orders = [dbc.Col(make_card_item(order), width=4) for order in orders]
                    return False, True, "訂單已確認，請查看已確認頁面", False, False, "", updated_orders
                elif response.status_code == 403:
                    return False, False, "", False, True, "權限不足：僅限編輯者使用此功能", dash.no_update
                else:
                    print(f"API 錯誤，狀態碼：{response.status_code}")
                    return False, False, dash.no_update, True, False, "", dash.no_update
            except Exception as e:
                print(f"API 呼叫失敗：{e}")
                return False, False, dash.no_update, True, False, "", dash.no_update
        
        return False, False, dash.no_update, True, False, "", dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update