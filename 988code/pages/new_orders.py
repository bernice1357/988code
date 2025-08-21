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
    
    # 客戶標題已移至群組標題，這裡不再需要
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                dbc.Badge("新品提醒", color="danger", className="me-2 rounded-pill", style={"fontSize": "0.7rem", "padding": "4px 8px"}) if order.get("is_new_product") == "true" or order.get("is_new_product") == True else None,
                dbc.Badge("備註與歷史提醒", color="danger", className="me-2 rounded-pill", style={"fontSize": "0.7rem", "padding": "4px 8px"})
            ], style={"lineHeight": "1"})
        ], style={"overflow": "hidden", "padding": "8px 12px"}),
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
                ], style={"whiteSpace": "pre-wrap"}),
                # 新增數量、單價、金額資訊
                html.Div([
                    html.Div([
                        html.Span("數量: ", style={"color": "#6c757d", "fontSize": "0.8rem"}),
                        html.Span(f"{order.get('quantity', 'N/A')}", style={"fontSize": "0.8rem", "fontWeight": "bold"})
                    ], style={"marginRight": "15px", "display": "inline-block"}) if order.get('quantity') is not None else None,
                    html.Div([
                        html.Span("單價: ", style={"color": "#6c757d", "fontSize": "0.8rem"}),
                        html.Span(f"NT$ {order.get('unit_price', 'N/A')}", style={"fontSize": "0.8rem", "fontWeight": "bold"})
                    ], style={"marginRight": "15px", "display": "inline-block"}) if order.get('unit_price') is not None else None,
                    html.Div([
                        html.Span("總金額: ", style={"color": "#6c757d", "fontSize": "0.8rem"}),
                        html.Span(f"NT$ {order.get('amount', 'N/A')}", style={"fontSize": "0.8rem", "fontWeight": "bold"})
                    ], style={"display": "inline-block"}) if order.get('amount') is not None else None
                ], style={"marginTop": "8px"}) if any(order.get(field) is not None for field in ['quantity', 'unit_price', 'amount']) else None
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
                html.Div([
                    dbc.Button("確定", id={"type": "confirm-btn", "index": order['id']}, size="sm", color="dark", outline=True, className="me-2") if order.get("status") == "0" else None,
                    dbc.Button("刪除", id={"type": "delete-btn", "index": order['id']}, size="sm", color="danger", outline=True) if order.get("status") == "0" else None
                ]) if order.get("status") == "0" else html.Div(),
                html.Small(f"建立時間: {order['created_at'][:16].replace('T', ' ')}", className="text-muted", style={"fontSize": "0.7rem"})
            ], className="d-flex justify-content-between align-items-center mt-2")
        ])
    ], style={"backgroundColor": "#f8f9fa", "border": "1px solid #dee2e6", "position": "relative", "marginTop": "15px"}, className="mb-3")

def get_modal_fields(customer_id, customer_name, purchase_record, product_id=None, quantity=None, unit_price=None, amount=None):
    # 不管有沒有customer_id，都顯示所有欄位
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
            dbc.Label("產品 ID", width=3),
            dbc.Col(dbc.Input(
                id="product-id", 
                type="text",
                value=product_id if product_id else ""
            ), width=9)
        ], className="mb-3"),
        dbc.Row([
            dbc.Label("購買品項", width=3),
            dbc.Col(dbc.Input(id="purchase-record", value=purchase_record), width=9)
        ], className="mb-3"),
        dbc.Row([
            dbc.Label("數量", width=3),
            dbc.Col(dbc.Input(
                id="quantity", 
                type="number",
                value=quantity if quantity else "",
                min=0,
                step=1
            ), width=9)
        ], className="mb-3"),
        dbc.Row([
            dbc.Label("單價", width=3),
            dbc.Col(dbc.Input(
                id="unit-price", 
                type="number",
                value=unit_price if unit_price else "",
                min=0,
                step=0.01
            ), width=9)
        ], className="mb-3"),
        dbc.Row([
            dbc.Label("金額", width=3),
            dbc.Col(dbc.Input(
                id="amount", 
                type="number",
                value=amount if amount else "",
                min=0,
                step=0.01
            ), width=9)
        ], className="mb-3")
    ]

def group_orders_by_customer(orders):
    """按客戶名稱分組訂單"""
    grouped = {}
    for order in orders:
        # 優先使用 customer_name，沒有的話用 line_id，都沒有就歸為未知客戶
        if order.get("customer_name"):
            customer_key = order["customer_name"]
        elif order.get("line_id"):
            customer_key = f"Line用戶: {order['line_id']}"
        else:
            customer_key = "未知客戶"
        
        if customer_key not in grouped:
            grouped[customer_key] = []
        grouped[customer_key].append(order)
    
    return grouped

def make_customer_group(customer_key, orders, group_index):
    """創建客戶群組Accordion"""
    order_count = len(orders)
    
    # 創建包含 badge 的標題
    title_content = html.Div([
        html.Span(customer_key, style={"marginRight": "10px"}),
        dbc.Badge(str(order_count), color="primary", pill=True)
    ], className="d-flex align-items-center")
    
    return dbc.AccordionItem([
        dbc.Row([
            dbc.Col(make_card_item(order), width=12, lg=6, xl=4) 
            for order in orders
        ], className="g-3")
    ], 
    title=title_content,
    item_id=f"customer-group-{group_index}"
    )

def create_grouped_orders_layout(orders):
    """創建分組後的訂單layout"""
    if not orders:
        return html.Div("暫無訂單", className="text-center text-muted", style={"padding": "50px"})
    
    grouped_orders = group_orders_by_customer(orders)
    customer_groups = []
    
    for group_index, (customer_key, customer_orders) in enumerate(grouped_orders.items()):
        customer_groups.append(make_customer_group(customer_key, customer_orders, group_index))
    
    return dbc.Accordion(customer_groups, flush=True, always_open=False)

orders = get_orders()

layout = dbc.Container([
    success_toast("new_orders", message="訂單已確認"),
    error_toast("new_orders", message=""),
    warning_toast("new_orders", message=""),
    dcc.Store(id='user-role-store'),
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
        children=html.Div(id="orders-container", children=create_grouped_orders_layout(orders), style={
            "maxHeight": "75vh", 
            "overflowY": "auto",
            "overflowX": "hidden"
        }),
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
        return create_grouped_orders_layout(filtered_orders), False, True, True, True
    elif triggered_id == "filter-unconfirmed":
        filtered_orders = [order for order in orders if order.get("status") == "0"]
        return create_grouped_orders_layout(filtered_orders), True, False, True, True
    elif triggered_id == "filter-confirmed":
        filtered_orders = [order for order in orders if order.get("status") == "1"]
        return create_grouped_orders_layout(filtered_orders), True, True, False, True
    elif triggered_id == "filter-deleted":
        filtered_orders = [order for order in orders if order.get("status") == "2"]
        return create_grouped_orders_layout(filtered_orders), True, True, True, False
    else:
        filtered_orders = orders
        return create_grouped_orders_layout(filtered_orders), False, True, True, True

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
                    updated_orders = create_grouped_orders_layout(orders)
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
        # 傳入所有需要的欄位
        modal_content = get_modal_fields(
            order.get("customer_id"), 
            order.get("customer_name"), 
            order["purchase_record"],
            order.get("product_id"),
            order.get("quantity"),
            order.get("unit_price"),
            order.get("amount")
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
     State("product-id", "value"),
     State("purchase-record", "value"),
     State("quantity", "value"),
     State("unit-price", "value"),
     State("amount", "value"),
     State("modal-header", "children"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def submit_confirm(n_clicks, customer_id, customer_name, product_id, purchase_record, quantity, unit_price, amount, modal_header, user_role):
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
                "product_id": product_id,
                "purchase_record": purchase_record,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
                "updated_at": current_time,
                "status": "1",
                "confirmed_by": "user",
                "confirmed_at": current_time
            }
            
            # 呼叫API更新資料
            try:
                update_data["user_role"] = user_role
                response = requests.put(f"http://127.0.0.1:8000/temp/{order_id}", json=update_data)
                if response.status_code == 200:
                    print("訂單確認成功")
                    
                    # 更新 order_transactions 表
                    try:
                        transaction_data = {
                            "customer_id": customer_id,
                            "product_id": product_id,
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "amount": amount,
                            "transaction_date": original_order['created_at'],
                            "user_role": user_role
                        }
                        
                        transaction_response = requests.post(f"http://127.0.0.1:8000/order_transactions", json=transaction_data)
                        if transaction_response.status_code != 200:
                            print(f"order_transactions 更新失敗，狀態碼：{transaction_response.status_code}")
                    except Exception as e:
                        print(f"order_transactions 更新異常：{str(e)}")
                    
                    orders = get_orders()
                    updated_orders = create_grouped_orders_layout(orders)
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