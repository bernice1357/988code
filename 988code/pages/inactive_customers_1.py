from .common import *
from dash import ALL, callback_context

tab_content = html.Div([
    dcc.Store(id="page-loaded-inactive", data=True),
    dcc.Store(id="inactive-customers-data", data=[]),
    dcc.Store(id="filtered-inactive-data", data=[]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("摘要分析"),
                dbc.CardBody([
                    html.Div(id="inactive-stats-container", children=[
                        html.H5("不活躍客戶: 0"),
                        html.H5("已處理: 0"),
                        html.H5("未處理: 0")
                    ])
                ])
            ], color="light", style={"height": "100%"})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("設定不活躍客戶天數"),
                dbc.CardBody([
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText("不活躍天數 >="),
                            dbc.Input(type="number", placeholder="輸入天數", id="inactive-days-input", min=1),
                            dbc.InputGroupText("天")
                        ], style={"flex": "1", "marginRight": "10px"}),
                        dbc.Button("儲存", color="primary", id="save-days-btn")
                    ], style={"display": "flex", "alignItems": "center"})
                ])
            ], color="light", style={"height": "100%"})
        ], width=6)
    ], className="h-100"),
    
    html.Div([
        html.Div([
            html.Div(id="confirm-button-container", style={"display": "flex", "alignItems": "center"})
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            dbc.ButtonGroup([
                dbc.Button("全部客戶", outline=True, id="btn-all-customers", color="primary"),
                dbc.Button("未處理客戶", outline=True, id="btn-unprocessed-customers", color="primary"),
                dbc.Button("已處理客戶", outline=True, id="btn-processed-customers", color="primary")
            ])
        ], style={"display": "flex", "justifyContent": "flex-end"})
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px", "marginTop": "30px"}),
    
    html.Div(id="inactive-customer-table-container"),
    
    # 處理確認 Modal
    dbc.Modal(
        id="process-confirm-modal",
        is_open=False,
        centered=True,
        style={"fontSize": "18px"},
        children=[
            dbc.ModalHeader("確認處理不活躍客戶", style={"fontWeight": "bold", "fontSize": "24px"}),
            dbc.ModalBody([
                html.Div(id="selected-customers-info", style={"marginBottom": "20px"}),
                dbc.Row([
                    dbc.Label("處理人員", width=3),
                    dbc.Col(dbc.Input(
                        id="modal-processor-name",
                        type="text",
                        placeholder="輸入處理人員姓名",
                        value="系統管理員"
                    ), width=9)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Label("處理時間", width=3),
                    dbc.Col(html.Div(id="process-datetime", style={"padding": "8px", "backgroundColor": "#f8f9fa", "border": "1px solid #ced4da", "borderRadius": "4px"}), width=9)
                ], className="mb-3"),
            ]),
            dbc.ModalFooter([
                dbc.Button("取消", id="modal-cancel-btn", color="secondary", className="me-2"),
                dbc.Button("確認處理", id="modal-confirm-btn", color="success")
            ])
        ]
    ),
    
    create_success_toast("inactive_customers", message=""),
    create_error_toast("inactive_customers", message=""),
], className="mt-3")

# 載入不活躍客戶資料的 callback
@app.callback(
    Output("inactive-customers-data", "data"),
    Input("page-loaded-inactive", "data"),
    prevent_initial_call=False
)
def load_inactive_customers_data(page_loaded):
    try:
        response = requests.get("http://127.0.0.1:8000/get_inactive_customers")
        if response.status_code == 200:
            try:
                inactive_data = response.json()
                return inactive_data
            except requests.exceptions.JSONDecodeError:
                print("回應內容不是有效的 JSON")
                return []
        else:
            print(f"get_inactive_customers API 錯誤，狀態碼：{response.status_code}")
            return []
    except Exception as e:
        print(f"載入不活躍客戶資料時發生錯誤：{e}")
        return []

# 處理天數篩選和資料更新
@app.callback(
    Output("filtered-inactive-data", "data"),
    [Input("inactive-customers-data", "data"),
     Input("save-days-btn", "n_clicks")],
    State("inactive-days-input", "value"),
    prevent_initial_call=False
)
def filter_inactive_data(inactive_data, save_clicks, min_days):
    if not inactive_data:
        return []
    
    # 轉換為 DataFrame 並重新命名欄位
    df = pd.DataFrame(inactive_data)
    if not df.empty:
        df = df.rename(columns={
            'customer_name': '客戶名稱',
            'last_order_date': '最後訂單日期',
            'last_product': '最後訂購商品',
            'inactive_days': '不活躍天數',
            'processed': '狀態原始值'
        })
        
        # 轉換處理狀態為中文
        df['狀態'] = df['狀態原始值'].map({True: '已處理', False: '未處理'})
        
        # 格式化日期
        if '最後訂單日期' in df.columns:
            df['最後訂單日期'] = pd.to_datetime(df['最後訂單日期']).dt.strftime('%Y-%m-%d')
        
        # 天數篩選
        if min_days and save_clicks:
            df = df[df['不活躍天數'] >= min_days]
        
        # 只保留需要的欄位
        columns_to_keep = ['客戶名稱', '最後訂單日期', '最後訂購商品', '不活躍天數', '狀態']
        df = df[columns_to_keep]
    
    return df.to_dict('records')

# 更新統計資訊
@app.callback(
    Output("inactive-stats-container", "children"),
    Input("filtered-inactive-data", "data")
)
def update_stats(filtered_data):
    if not filtered_data:
        return [
            html.H5("不活躍客戶: 0"),
            html.H5("已處理: 0"),
            html.H5("未處理: 0")
        ]
    
    df = pd.DataFrame(filtered_data)
    total_customers = len(df)
    processed_customers = len(df[df['狀態'] == '已處理'])
    unprocessed_customers = len(df[df['狀態'] == '未處理'])
    
    return [
        html.H5(f"不活躍客戶: {total_customers}"),
        html.H5(f"已處理: {processed_customers}"),
        html.H5(f"未處理: {unprocessed_customers}")
    ]

# 顯示表格的 callback
@app.callback(
    Output("inactive-customer-table-container", "children"),
    [Input("filtered-inactive-data", "data"),
     Input("btn-all-customers", "n_clicks"),
     Input("btn-unprocessed-customers", "n_clicks"),
     Input("btn-processed-customers", "n_clicks")]
)
def display_inactive_customer_table(filtered_data, btn_all, btn_unprocessed, btn_processed):
    if not filtered_data:
        return html.Div("暫無資料")
    
    # 轉換為 DataFrame
    df = pd.DataFrame(filtered_data)
    
    # 判斷按鈕篩選
    ctx = callback_context
    show_checkbox = False
    
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'btn-unprocessed-customers':
            df = df[df['狀態'] == '未處理']
            show_checkbox = True
        elif button_id == 'btn-processed-customers':
            df = df[df['狀態'] == '已處理']
            show_checkbox = False
        # else: 顯示全部客戶
    
    # 重置索引，讓按鈕index從0開始連續
    df = df.reset_index(drop=True)
    
    return custom_table(df, show_checkbox=show_checkbox, show_button=False)

# 顯示確認已處理按鈕
@app.callback(
    Output('confirm-button-container', 'children'),
    [Input({'type': 'status-checkbox', 'index': ALL}, 'value')]
)
def show_confirm_button(checkbox_values):
    selected_rows = []
    for i, values in enumerate(checkbox_values):
        if values:  # 如果checkbox被選中
            selected_rows.extend(values)
    
    if selected_rows and len(selected_rows) > 0:
        return dbc.Button("確認已處理", id="inactive_customers_confirm_btn", color="success")
    else:
        return html.Div()

# 顯示處理確認 Modal
@app.callback(
    [Output('process-confirm-modal', 'is_open'),
     Output('selected-customers-info', 'children'),
     Output('process-datetime', 'children')],
    [Input('inactive_customers_confirm_btn', 'n_clicks'),
     Input('modal-cancel-btn', 'n_clicks')],
    [State({'type': 'status-checkbox', 'index': ALL}, 'value'),
     State("filtered-inactive-data", "data"),
     State('process-confirm-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_process_modal(confirm_clicks, cancel_clicks, checkbox_values, filtered_data, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return False, "", ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'inactive_customers_confirm_btn' and confirm_clicks:
        # 獲取選中的客戶
        selected_indices = []
        for i, values in enumerate(checkbox_values):
            if values:
                selected_indices.extend(values)
        
        if selected_indices and filtered_data:
            df = pd.DataFrame(filtered_data)
            selected_customers = [df.iloc[index]['客戶名稱'] for index in selected_indices if index < len(df)]
            
            # 顯示選中的客戶
            customer_info = html.Div([
                html.H6(f"將處理以下 {len(selected_customers)} 位客戶：", style={"marginBottom": "10px"}),
                html.Ul([html.Li(customer) for customer in selected_customers])
            ])
            
            # 顯示當前時間
            from datetime import datetime
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return True, customer_info, current_time
    
    elif button_id == 'modal-cancel-btn':
        return False, "", ""
    
    return is_open, dash.no_update, dash.no_update

# 處理確認已處理的邏輯
@app.callback(
    [Output('inactive_customers-success-toast', 'is_open'),
     Output('inactive_customers-success-toast', 'children'),
     Output('inactive_customers-error-toast', 'is_open'),
     Output('inactive_customers-error-toast', 'children'),
     Output("page-loaded-inactive", "data", allow_duplicate=True),
     Output('process-confirm-modal', 'is_open', allow_duplicate=True)],
    Input('modal-confirm-btn', 'n_clicks'),
    [State({'type': 'status-checkbox', 'index': ALL}, 'value'),
     State("filtered-inactive-data", "data"),
     State("modal-processor-name", "value")],
    prevent_initial_call=True
)
def confirm_processed(modal_confirm_clicks, checkbox_values, filtered_data, processor_name):
    if not modal_confirm_clicks:
        return False, "", False, "", dash.no_update, dash.no_update
    
    # 獲取選中的客戶
    selected_indices = []
    for i, values in enumerate(checkbox_values):
        if values:
            selected_indices.extend(values)
    
    if not selected_indices or not filtered_data:
        return False, "", True, "沒有選擇任何客戶", dash.no_update, False
    
    try:
        df = pd.DataFrame(filtered_data)
        
        customer_names = [df.iloc[index]['客戶名稱'] for index in selected_indices if index < len(df)]

        update_data = {
            "customer_names": customer_names,
            "processed": True,
            "processed_by": processor_name or "系統管理員"
        }

        response = requests.put("http://127.0.0.1:8000/inactive_customers/batch_update", json=update_data)
        
        if response.status_code == 200:
            result = response.json()
            success_count = result.get('success_count', len(customer_names))
            return True, f"成功處理 {success_count} 位客戶", False, "", True, False
        else:
            return False, "", True, f"API 調用失敗，狀態碼：{response.status_code}", dash.no_update, False
        
    except Exception as e:
        return False, "", True, f"處理失敗：{e}", dash.no_update, False