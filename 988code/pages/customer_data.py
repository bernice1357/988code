from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from dash import ALL, callback_context

# 呼叫API
response = requests.get("http://127.0.0.1:8000/get_customer_data")
if response.status_code == 200:
    try:
        df = response.json()
        df = pd.DataFrame(df)
        df = df.rename(columns={
                "customer_id": "客戶ID",
                "customer_name": "客戶名稱",
                "address": "客戶地址",
                "delivery_schedule": "每週配送日",
                "transaction_date": "最新交易日期",
                "notes": "備註"
            })
    except requests.exceptions.JSONDecodeError:
        print("回應內容不是有效的 JSON")
else:
    print(f"get_customer_data API 錯誤，狀態碼：{response.status_code}")

# offcanvas
product_input_fields = [
    {
        "id": "customer-id", 
        "label": "客戶ID",
        "type": "dropdown"
    }
]
search_customers = create_search_offcanvas(
    page_name="customer_data",
    input_fields=product_input_fields
)

layout = html.Div(style={"fontFamily": "sans-serif", "padding": "20px"}, children=[
    # 篩選條件區
    html.Div([
        search_customers["trigger_button"],
        dbc.Button("匯出", id="export-button", n_clicks=0, color="success")
    ], className="mb-3 d-flex justify-content-between align-items-center"),
    search_customers["offcanvas"],
    html.Div([
        button_table(
            df,
            button_text="編輯客戶資料",
            button_id_type="customer_data_button",
            address_columns=["客戶地址"],
        )
    ],style={"marginTop": "20px"}),
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
                    dbc.Label("備註", width=3),
                    dbc.Col(dbc.Textarea(id="input-notes", rows=3), width=9)
                ], className="mb-3"),
            ], id="customer_data_modal_body"),
            dbc.ModalFooter([
                dbc.Button("取消", id="input-customer-cancel", color="secondary", className="me-2"),
                dbc.Button("儲存", id="input-customer-save", color="primary")
            ])
        ]
    )
])

register_offcanvas_callback(app, "customer_data")

@app.callback(
    Output('customer_data_modal', 'is_open'),
    Output('input-customer-name', 'value'),
    Output('input-customer-id', 'value'),
    Output('input-customer-address', 'value'),
    Output('input-notes', 'value'),
    Input({'type': 'customer_data_button', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_edit_button_click(n_clicks):
    if not any(n_clicks):
        return False, "", "", "", ""
    
    ctx = callback_context
    if not ctx.triggered:
        return False, "", "", "", ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_index = eval(button_id)['index']
    
    row_data = df.iloc[button_index]
    
    return (True, 
            row_data['客戶名稱'], 
            row_data['客戶ID'], 
            row_data['客戶地址'], 
            row_data['備註'])

@app.callback(
    Output('customer_data_modal', 'is_open', allow_duplicate=True),
    Input('input-customer-save', 'n_clicks'),
    State('input-customer-name', 'value'),
    State('input-customer-id', 'value'),
    State('input-customer-address', 'value'),
    State('input-notes', 'value'),
    State({'type': 'customer_data_button', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def save_customer_data(save_clicks, customer_name, customer_id, address, notes, button_clicks):
    if not save_clicks:
        return dash.no_update
    
    ctx = callback_context
    button_index = None
    
    for i, clicks in enumerate(button_clicks):
        if clicks:
            button_index = i
            break
    
    if button_index is None:
        return dash.no_update
    
    row_data = df.iloc[button_index]
    original_id = row_data.name
    
    update_data = {
        "customer_name": customer_name,
        "customer_id": customer_id,
        "address": address,
        "notes": notes
    }
    
    try:
        response = requests.put(f"http://127.0.0.1:8000/customer/{original_id}", json=update_data)
        if response.status_code == 200:
            return False
        else:
            print(f"更新失敗，狀態碼：{response.status_code}")
            return dash.no_update
    except Exception as e:
        print(f"API 呼叫錯誤：{e}")
        return dash.no_update

@app.callback(
    Output('customer_data_modal', 'is_open', allow_duplicate=True),
    Input('cancel-button', 'n_clicks'),
    prevent_initial_call=True
)
def close_modal(cancel_clicks):
    if cancel_clicks:
        return False
    return dash.no_update