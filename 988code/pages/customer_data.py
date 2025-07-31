from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from dash import ALL, callback_context

# TODO MODAL可以改 Id 、名稱、地址、送貨時間、備註

# offcanvas
product_input_fields = [
    {
        "id": "customer-id", 
        "label": "客戶ID",
        "type": "dropdown",
        "options": []
    },
    {
        "id": "customer-name", 
        "label": "客戶名稱",
        "type": "dropdown",
        "options": []
    },
]
search_customers = create_search_offcanvas(
    page_name="customer_data",
    input_fields=product_input_fields,
)

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[
    dcc.Store(id="page-loaded", data=True),
    dcc.Store(id="customer-data", data=[]),
    dcc.Store(id="current-table-data", data=[]),
    # 篩選條件區
    html.Div([
        search_customers["trigger_button"],
        dbc.Button("匯出列表資料", id="export-button", n_clicks=0, outline=True, color="info")
    ], className="mb-3 d-flex justify-content-between align-items-center"),
    search_customers["offcanvas"],
    html.Div(id="customer-table-container"),
    dbc.Modal(
        id="customer_data_modal",
        is_open=False,
        style={"fontSize": "18px"},
        centered=True,
        children=[
            dbc.ModalHeader("客戶資訊", style={"fontWeight": "bold", "fontSize": "24px"}),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Label("客戶名稱", width=3),
                    dbc.Col(dbc.Input(id="input-customer-name", type="text"), width=9)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Label("客戶ID", width=3),
                    dbc.Col(dbc.Input(id="input-customer-id", type="text"), width=9)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Label("客戶地址", width=3),
                    dbc.Col(dbc.Input(id="input-customer-address", type="text"), width=9)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Label("每週配送日", width=3),
                    dbc.Col(dcc.Checklist(
                        id="input-delivery-schedule",
                        options=[
                            {"label": "一", "value": "一"},
                            {"label": "二", "value": "二"},
                            {"label": "三", "value": "三"},
                            {"label": "四", "value": "四"},
                            {"label": "五", "value": "五"},
                            {"label": "六", "value": "六"},
                            {"label": "日", "value": "日"}
                        ],
                        value=[],
                        inline=True,
                        style={"display": "flex", "gap": "15px"}
                    ), width=9)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Label("備註", width=3),
                    dbc.Col(dbc.Textarea(id="input-notes", rows=3), width=9)
                ], className="mb-3"),
            ], id="customer_data_modal_body"),
            dbc.ModalFooter([
                dbc.Button("取消", id="input-customer-cancel", color="secondary", className="me-2"),
                dbc.Button("儲存", id="input-customer-save", color="primary")
            ])
        ]
    ),
    success_toast("customer_data", message=""),
    error_toast("customer_data", message=""),
])

register_offcanvas_callback(app, "customer_data")

# 載入客戶ID選項的 callback
@app.callback(
    Output("customer_data-customer-id", "options"),
    Input("page-loaded", "data"),
    prevent_initial_call=False
)
def load_customer_id_options(page_loaded):
    try:
        response = requests.get("http://127.0.0.1:8000/get_customer_ids")
        if response.status_code == 200:
            customer_id_data = response.json()
            customer_id_options = [{"label": item["customer_id"], "value": item["customer_id"]} for item in customer_id_data]
            return customer_id_options
        else:
            return []
    except:
        return []

# 載入客戶名稱選項的 callback
@app.callback(
    Output("customer_data-customer-name", "options"),
    Input("page-loaded", "data"),
    prevent_initial_call=False
)
def load_customer_name_options(page_loaded):
    try:
        response = requests.get("http://127.0.0.1:8000/get_customer_names")
        if response.status_code == 200:
            customer_name_data = response.json()
            customer_name_options = [{"label": item["customer_name"], "value": item["customer_name"]} for item in customer_name_data]
            return customer_name_options
        else:
            return []
    except:
        return []

# 載入客戶資料的 callback
@app.callback(
    Output("customer-data", "data"),
    Input("page-loaded", "data"),
    prevent_initial_call=False
)
def load_customer_data(page_loaded):
    try:
        response = requests.get("http://127.0.0.1:8000/get_customer_data")
        if response.status_code == 200:
            try:
                customer_data = response.json()
                return customer_data
            except requests.exceptions.JSONDecodeError:
                print("回應內容不是有效的 JSON")
                return []
        else:
            print(f"get_customer_data API 錯誤，狀態碼：{response.status_code}")
            return []
    except Exception as e:
        print(f"載入客戶資料時發生錯誤：{e}")
        return []

# 顯示客戶表格的 callback
@app.callback(
    [Output("customer-table-container", "children"),
     Output("current-table-data", "data", allow_duplicate=True)],
    [Input("customer-data", "data"),
     Input("customer_data-customer-id", "value"),
     Input("customer_data-customer-name", "value")],
    prevent_initial_call=True
)
def display_customer_table(customer_data, selected_customer_id, selected_customer_name):
    if not customer_data:
        return html.Div("暫無資料"), []
    
    # 篩選邏輯
    df = pd.DataFrame(customer_data)
    df = df.rename(columns={
            "customer_id": "客戶ID",
            "customer_name": "客戶名稱",
            "phone_number": "電話",
            "address": "客戶地址",
            "delivery_schedule": "每週配送日",
            "transaction_date": "最新交易日期",
            "notes": "備註"
        })
    
    if selected_customer_id:
        df = df[df['客戶ID'] == selected_customer_id]
    
    if selected_customer_name:
        df = df[df['客戶名稱'] == selected_customer_name]

    # 重置索引，讓按鈕index從0開始連續
    df = df.reset_index(drop=True)
    
    # 儲存當前表格資料供匯出使用
    current_table_data = df.to_dict('records')
    
    table_component = custom_table(
        df,
        button_text="編輯客戶資料",
        button_id_type="customer_data_button",
        show_button=True,
        sticky_columns=['客戶ID', '客戶名稱']
    )
    
    return table_component, current_table_data

@app.callback(
    Output('customer_data_modal', 'is_open'),
    Output('input-customer-name', 'value'),
    Output('input-customer-id', 'value'),
    Output('input-customer-address', 'value'),
    Output('input-delivery-schedule', 'value'),
    Output('input-notes', 'value'),
    Input({'type': 'customer_data_button', 'index': ALL}, 'n_clicks'),
    [State("customer-data", "data"),
     State("customer_data-customer-id", "value"),
     State("customer_data-customer-name", "value")],
    prevent_initial_call=True
)
def handle_edit_button_click(n_clicks, customer_data, selected_customer_id, selected_customer_name):
    if not any(n_clicks):
        return False, "", "", "", "", ""
    
    ctx = callback_context
    if not ctx.triggered:
        return False, "", "", "", "", ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_index = eval(button_id)['index']
    
    # 重新篩選資料，確保 index 對應正確
    df = pd.DataFrame(customer_data)
    df = df.rename(columns={
            "customer_id": "客戶ID",
            "customer_name": "客戶名稱",
            "address": "客戶地址",
            "delivery_schedule": "每週配送日",
            "transaction_date": "最新交易日期",
            "notes": "備註"
        })
    
    if selected_customer_id:
        df = df[df['客戶ID'] == selected_customer_id]
    
    if selected_customer_name:
        df = df[df['客戶名稱'] == selected_customer_name]
    
    # 重置索引，確保連續性
    df = df.reset_index(drop=True)
    
    if button_index < len(df):
        row_data = df.iloc[button_index]
        
        # 處理每週配送日的資料格式
        delivery_schedule = row_data['每週配送日']
        if isinstance(delivery_schedule, str) and delivery_schedule:
            delivery_schedule_list = [day.strip() for day in delivery_schedule.split(',')]
        else:
            delivery_schedule_list = []
        
        return (True, 
                row_data['客戶名稱'], 
                row_data['客戶ID'], 
                row_data['客戶地址'], 
                delivery_schedule_list,
                row_data['備註'])
    else:
        return False, "", "", "", "", ""

@app.callback(
    Output('customer_data_modal', 'is_open', allow_duplicate=True),
    Output('customer_data-success-toast', 'is_open'),
    Output('customer_data-success-toast', 'children'),
    Output('customer_data-error-toast', 'is_open'),
    Output('customer_data-error-toast', 'children'),
    Input('input-customer-save', 'n_clicks'),
    State('input-customer-name', 'value'),
    State('input-customer-id', 'value'),
    State('input-customer-address', 'value'),
    State('input-delivery-schedule', 'value'),
    State('input-notes', 'value'),
    State({'type': 'customer_data_button', 'index': ALL}, 'n_clicks'),
    State("customer-data", "data"),
    State("customer_data-customer-id", "value"),
    State("customer_data-customer-name", "value"),
    prevent_initial_call=True
)
def save_customer_data(save_clicks, customer_name, customer_id, address, delivery_schedule, notes, button_clicks, customer_data, selected_customer_id, selected_customer_name):
    if not save_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    ctx = callback_context
    button_index = None
    
    for i, clicks in enumerate(button_clicks):
        if clicks:
            button_index = i
            break
    
    if button_index is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # 重新篩選資料，確保 index 對應正確
    df = pd.DataFrame(customer_data)
    df = df.rename(columns={
            "customer_id": "客戶ID",
            "customer_name": "客戶名稱",
            "address": "客戶地址",
            "delivery_schedule": "每週配送日",
            "transaction_date": "最新交易日期",
            "notes": "備註"
        })
    
    if selected_customer_id:
        df = df[df['客戶ID'] == selected_customer_id]
    
    if selected_customer_name:
        df = df[df['客戶名稱'] == selected_customer_name]
    
    # 重置索引，確保連續性
    df = df.reset_index(drop=True)
    
    if button_index >= len(df):
        return dash.no_update, False, "", True, "找不到對應的客戶資料"
    
    row_data = df.iloc[button_index]
    original_id = row_data['客戶ID']
    
    # 處理多選框的值，將列表轉換為字串並按順序排列
    if isinstance(delivery_schedule, list):
        # 定義順序
        day_order = ["一", "二", "三", "四", "五", "六", "日"]
        # 按照順序排列
        sorted_days = [day for day in day_order if day in delivery_schedule]
        delivery_schedule_str = ','.join(sorted_days)
    else:
        delivery_schedule_str = delivery_schedule or ""
    
    update_data = {
        "customer_name": customer_name,
        "customer_id": customer_id,
        "address": address,
        "delivery_schedule": delivery_schedule_str,
        "notes": notes
    }
    
    try:
        response = requests.put(f"http://127.0.0.1:8000/customer/{original_id}", json=update_data)
        if response.status_code == 200:
            return False, True, "客戶資料更新成功！", False, ""
        else:
            return dash.no_update, False, "", True, f"更新失敗，狀態碼：{response.status_code}"
    except Exception as e:
        return dash.no_update, False, "", True, f"API 呼叫錯誤：{e}"

@app.callback(
    Output('customer_data_modal', 'is_open', allow_duplicate=True),
    Input('input-customer-cancel', 'n_clicks'),
    prevent_initial_call=True
)
def close_modal(cancel_clicks):
    if cancel_clicks:
        return False
    return dash.no_update