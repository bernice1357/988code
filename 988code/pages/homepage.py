'''
首頁 預設顯示customer_id+name，沒有就顯示line_id
confirmed_by:帳號名稱、confirmed_at:確認時間
datetime.now()取得當前時間
'''

from .common import *
from dash import ALL
from datetime import datetime

# 呼叫API
response = requests.get("http://127.0.0.1:8000/get_new_orders")
if response.status_code == 200:
    try:
        orders = response.json()
    except requests.exceptions.JSONDecodeError:
        print("回應內容不是有效的 JSON")
else:
    print(f"API 錯誤，狀態碼：{response.status_code}")

def make_card_item(order):
    # 卡片標題：左邊顯示客戶ID
    title = html.Div([
        html.Span(
            order["customer_id"] + order["customer_name"] if order.get("customer_id") else order["line_id"], 
            style={"fontWeight": "bold", "fontSize": "0.9rem"}
        )
    ])
    return dbc.Card([
        dbc.CardHeader(title),
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
                html.Pre(order["purchase_record"], style={"whiteSpace": "pre-wrap", "fontSize": "0.9rem"})
            ], className="mb-3"),
            # 建立時間
            html.Div([
                html.Small(f"建立時間: {order['created_at'][:16].replace('T', ' ')}", className="text-muted", style={"fontSize": "0.7rem"}),
                html.Div([
                    dbc.Button("確定", id={"type": "confirm-btn", "index": order['id']}, size="sm", color="dark", outline=True),
                    dbc.Button("刪除", id={"type": "delete-btn", "index": order['id']}, size="sm", color="danger", outline=True)
                ])
            ], className="d-flex justify-content-between align-items-center mt-2")
        ]),
        html.Div([
            dbc.Badge("新品提醒", color="danger", className="me-4 rounded-pill") if order["is_new_product"] == "true" else None,
            dbc.Badge("備註與歷史提醒", color="danger", className="me-4 rounded-pill")
        ], style={
            "position": "absolute",
            "top": "10px",
            "right": "10px"
        })
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

layout = dbc.Container([
    dbc.Toast(
        "訂單已刪除",
        id="success-toast",
        header="系統通知",
        is_open=False,
        dismissable=True,
        duration=5000,
        style={"position": "fixed", "top": 20, "right": 20, "width": 350, "zIndex": 9999}
    ),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Line Bot 訂單"),
                dbc.CardBody([
                    html.H2("4", className="card-title text-primary"),  # 可用 len(orders)
                    html.P("等待處理的訂單", className="card-text")
                ])
            ], color="success", className="mb-4"),
            width=6,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Line Bot 客服問題"),
                dbc.CardBody([
                    html.H2("2", className="card-htitle text-primary"),
                    html.P("等待處理的客戶訊息", className="card-text")
                ])
            ], color="warning", className="mb-4"),
            width=6,
        )
    ]),
    html.Div([
        html.H4("新進訂單", className="mt-4 mb-4 text-secondary"),
        dbc.ButtonGroup([
            dbc.Button("全部", id="filter-all", color="primary", outline=False),
            dbc.Button("未確認", id="filter-unconfirmed", color="primary", outline=True),
            dbc.Button("已確認", id="filter-confirmed", color="primary", outline=True),
            dbc.Button("已刪除", id="filter-deleted", color="primary", outline=True)
        ])
    ], className="d-flex justify-content-between align-items-center"),
    dbc.Row(id="orders-container", className="g-3", children=[dbc.Col(make_card_item(order), width=4) for order in orders], style={
        "maxHeight": "550px", 
        "overflowY": "auto"
    } if len(orders) > 6 else {}),
    dbc.Modal([
        dbc.ModalHeader(id="modal-header", children="確認訂單"),
        dbc.ModalBody(id="modal-body-content"),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-modal", color="secondary", outline=True),
            dbc.Button("確認", id="submit-confirm", color="primary")
        ])
    ], id="confirm-modal", is_open=False),
    dbc.Modal([
        dbc.ModalHeader("確認刪除"),
        dbc.ModalBody(id="delete-modal-body", children="確定要刪除這筆訂單嗎？"),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-delete", color="secondary", outline=True),
            dbc.Button("刪除", id="submit-delete", color="danger")
        ])
    ], id="delete-modal", is_open=False)
], fluid=True)

# 篩選顯示訂單和更新按鈕狀態
@app.callback(
    [Output("orders-container", "children"),
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
     Output("success-toast", "children", allow_duplicate=True)],
    [Input("submit-delete", "n_clicks")],
    [State("delete-modal-body", "children")],
    prevent_initial_call=True
)
def confirm_delete(n_clicks, modal_body):
    if n_clicks:
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
                response = requests.put(f"http://127.0.0.1:8000/customer/{order_id}", json=update_data)
                if response.status_code == 200:
                    print("訂單刪除成功")
                    return False, "訂單已刪除"  # 關閉 modal，設定 toast 內容
                else:
                    print(f"API 錯誤，狀態碼：{response.status_code}")
            except Exception as e:
                print(f"API 呼叫失敗：{e}")
        
        return False, dash.no_update  # 關閉 modal
    return dash.no_update, dash.no_update
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
     Output("success-toast", "children", allow_duplicate=True)],
    [Input("submit-confirm", "n_clicks")],
    [State("customer-id", "value"),
     State("customer-name", "value"),
     State("purchase-record", "value"),
     State("modal-header", "children")],
    prevent_initial_call=True
)
def submit_confirm(n_clicks, customer_id, customer_name, purchase_record, modal_header):
    if n_clicks:
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
                response = requests.put(f"http://127.0.0.1:8000/customer/{order_id}", json=update_data)
                if response.status_code == 200:
                    print("訂單確認成功")
                    return False, "訂單已確認"  # 關閉 modal，設定 toast 內容
                else:
                    print(f"API 錯誤，狀態碼：{response.status_code}")
            except Exception as e:
                print(f"API 呼叫失敗：{e}")
        
        return False, dash.no_update  # 關閉 modal
    
    return dash.no_update, dash.no_update