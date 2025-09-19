from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from callbacks.export_callback import create_export_callback, add_download_component
from dash import ALL, callback_context

# 配送日轉換函數
def convert_delivery_schedule_to_chinese(schedule_str):
    if not schedule_str or schedule_str.strip() == "":
        return ""
    
    number_to_chinese = {
        "1": "一", "2": "二", "3": "三", "4": "四",
        "5": "五", "6": "六", "7": "日"
    }
    
    try:
        # 分割數字並轉換為中文
        numbers = [num.strip() for num in schedule_str.split(',') if num.strip()]
        chinese_days = [number_to_chinese.get(num, num) for num in numbers]
        return ','.join(chinese_days)
    except:
        return schedule_str

def convert_delivery_schedule_to_numbers(chinese_str):
    if not chinese_str:
        return ""
    
    chinese_to_number = {
        "一": "1", "二": "2", "三": "3", "四": "4",
        "五": "5", "六": "6", "日": "7"
    }
    
    try:
        # 處理列表格式 (來自 checklist)
        if isinstance(chinese_str, list):
            chinese_days = chinese_str
        else:
            # 處理字符串格式
            chinese_days = [day.strip() for day in chinese_str.split(',') if day.strip()]
        
        # 按照順序排列數字
        day_order = ["1", "2", "3", "4", "5", "6", "7"]
        numbers = [chinese_to_number.get(day, day) for day in chinese_days]
        # 按照星期順序排列
        sorted_numbers = [num for num in day_order if num in numbers]
        return ','.join(sorted_numbers)
    except:
        return ""

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
    dcc.Store(id="missing-data-filter", data=False),
    dcc.Store(id="customer-data", data=[]),
    dcc.Store(id="pagination-info", data={}),  # 新增
    dcc.Store(id="current-page", data=1),      # 新增
    dcc.Store(id="user-role-store"),
    dcc.Store(id="current-table-data", data=[]),
    add_download_component("customer_data"),  # 加入下載元件
    html.Div([
        # 左邊：搜尋條件和篩選按鈕
        html.Div([
            search_customers["trigger_button"],
            dbc.Button("缺少電話地址", 
                    id="missing-data-filter-button", 
                    n_clicks=0, 
                    outline=True, 
                    color="warning",
                    style={"marginLeft": "10px"}),
            html.Small("缺失地址警告：會導致該店家無法顯示在每日配送清單上", 
                   id="missing-data-warning",  # 新增 id
                   style={
                       "marginLeft": "15px", 
                       "color": "#dc3545", 
                       "fontWeight": "bold",
                       "alignSelf": "center"
                   })
        ], style={"display": "flex", "alignItems": "center"}),
        
        # 右邊：匯出按鈕
        html.Div([
            dbc.Button("匯出列表資料", 
                    id="customer_data-export-button", 
                    n_clicks=0, 
                    outline=True, 
                    color="primary")
        ], style={"display": "flex", "alignItems": "center"})
    ], className="mb-3 d-flex justify-content-between align-items-center"),


    search_customers["offcanvas"],
    dcc.Loading(
        id="loading-customer-table",
        type="dot",
        children=html.Div(id="customer-table-container"),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "position": "fixed", 
            "top": "50%",          
        }
    ),

    html.Div(id="pagination-controls-bottom", className="mt-3 d-flex justify-content-center align-items-center"),
    dbc.Modal(
        id="customer_data_modal",
        is_open=False,
        size="xl",
        centered=True,
        style={"fontSize": "18px"},
        children=[
            dbc.ModalHeader("客戶資訊", style={"fontWeight": "bold", "fontSize": "24px"}),
            dbc.ModalBody([
                dbc.Form([
                    html.Div([
                        dbc.Label("客戶名稱", html_for="input-customer-name", className="form-label", style={"fontSize": "14px"}),
                        dbc.Input(id="input-customer-name", type="text", style={"width": "500px"})
                    ], className="mb-3"),
                    html.Div([
                        dbc.Label("客戶ID", html_for="input-customer-id", className="form-label", style={"fontSize": "14px"}),
                        dbc.Input(id="input-customer-id", type="text", style={"width": "500px"})
                    ], className="mb-3"),
                    html.Div([
                        dbc.Label("電話", html_for="input-customer-phone", className="form-label", style={"fontSize": "14px"}),
                        dbc.Input(id="input-customer-phone", type="text", style={"width": "500px"})
                    ], className="mb-3"),
                    html.Div([
                        dbc.Label("客戶地址", html_for="input-customer-address", className="form-label", style={"fontSize": "14px"}),
                        dbc.Input(id="input-customer-address", type="text", style={"width": "500px"})
                    ], className="mb-3"),
                    html.Div([
                        dbc.Label("每週配送日", className="form-label", style={"fontSize": "14px"}),
                        dcc.Checklist(
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
                        )
                    ], className="mb-3"),
                    html.Div([
                        dbc.Label("備註", html_for="input-notes", className="form-label", style={"fontSize": "14px"}),
                        dbc.Textarea(id="input-notes", rows=3, style={"width": "500px"})
                    ], className="mb-3")
                ])
            ], id="customer_data_modal_body"),
            dbc.ModalFooter([
                dbc.Button("取消", id="input-customer-cancel", color="secondary", className="me-2"),
                dbc.Button("儲存", id="input-customer-save", color="primary")
            ])
        ]
    ),
    success_toast("customer_data", message=""),
    error_toast("customer_data", message=""),
    warning_toast("customer_data", message=""),
])

register_offcanvas_callback(app, "customer_data")


# 註冊匯出功能 - 使用當前表格資料
create_export_callback(app, "customer_data", "current-table-data", "客戶資料")

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

# 載入客戶資料的 callback - 修正版
@app.callback(
    [Output("customer-data", "data"),
     Output("pagination-info", "data"),
     Output('customer_data-error-toast', 'is_open'),
     Output('customer_data-error-toast', 'children')],
    [Input("page-loaded", "data"),
     Input("current-page", "data"),
     Input("customer_data-customer-id", "value"),
     Input("customer_data-customer-name", "value")],
    prevent_initial_call=False
)
def load_customer_data(page_loaded, current_page, selected_customer_id, selected_customer_name):
    current_page = current_page or 1

    try:
        triggered_inputs = {item['prop_id'].split('.')[0] for item in callback_context.triggered} if callback_context.triggered else set()
        if triggered_inputs & {"customer_data-customer-id", "customer_data-customer-name"}:
            current_page = 1

        params = {
            "page": current_page,
            "page_size": 50
        }
        if selected_customer_id:
            params["customer_id"] = selected_customer_id
        if selected_customer_name:
            params["customer_name"] = selected_customer_name

        response = requests.get(
            "http://127.0.0.1:8000/get_customer_data",
            params=params
        )
        if response.status_code == 200:
            try:
                result = response.json()
                customer_data = result.get("data", [])
                pagination_info = result.get("pagination", {})
                return customer_data, pagination_info, False, ""
            except requests.exceptions.JSONDecodeError:
                return [], {}, True, "回傳內容不是有效的 JSON"
        else:
            return [], {}, True, f"資料載入失敗，狀態碼：{response.status_code}"
    except Exception as e:
        return [], {}, True, f"載入資料時發生錯誤：{e}"
@app.callback(
    [Output("customer-table-container", "children", allow_duplicate=True),
     Output("current-table-data", "data", allow_duplicate=True),
     Output("missing-data-filter-button", "style", allow_duplicate=True),
     Output("missing-data-warning", "style", allow_duplicate=True)],
    [Input("customer-data", "data"),
     Input("customer_data-customer-id", "value"),
     Input("customer_data-customer-name", "value"),
     Input("missing-data-filter", "data")],
    prevent_initial_call=True
)

def display_customer_table(customer_data, selected_customer_id, selected_customer_name, missing_filter):
    if not customer_data:
        return html.Div("暫無資料"), [], {"display": "block"}, {"display": "block"}
    
    try:
        # 確保 customer_data 是正確的格式
        if isinstance(customer_data, dict):
            # 如果是分頁格式，取出 data 部分
            if 'data' in customer_data:
                customer_data = customer_data['data']
            else:
                # 如果是單一字典，轉換為列表
                customer_data = [customer_data]
        
        # 檢查是否為空
        if not customer_data:
            return html.Div("暫無資料"), [], {"display": "block"}, {"display": "block"}
        
        # 創建 DataFrame
        df = pd.DataFrame(customer_data)
        
    except Exception as e:
        print(f"DataFrame 創建錯誤: {e}")
        return html.Div("資料格式錯誤"), [], {"display": "block"}, {"display": "block"}
    
    # 篩選邏輯
    
    df = df.rename(columns={
            "customer_id": "客戶ID",
            "customer_name": "客戶名稱",
            "phone_number": "電話",
            "address": "客戶地址",
            "delivery_schedule": "每週配送日",
            "transaction_date": "最新交易日期",
            "notes": "備註"
        })
    
    # 轉換配送日數字為中文字
    if "每週配送日" in df.columns:
        df["每週配送日"] = df["每週配送日"].apply(convert_delivery_schedule_to_chinese)
    
    # 檢查是否有缺失資料
    missing_phone = df["電話"].isna() | (df["電話"] == "") | (df["電話"] == "None")
    missing_address = df["客戶地址"].isna() | (df["客戶地址"] == "") | (df["客戶地址"] == "None")
    has_missing_data = (missing_phone | missing_address).any()
    
    # 根據是否有缺失資料決定按鈕和警告的顯示
    button_style = {"display": "none"} if not has_missing_data else {"marginLeft": "10px"}
    warning_style = {"display": "none"} if not has_missing_data else {
        "marginLeft": "15px", 
        "color": "#dc3545", 
        "fontWeight": "bold",
        "alignSelf": "center"
    }
    
    # 缺失資料篩選邏輯 - 移除重複計算
    if missing_filter:
        df = df[missing_phone | missing_address]
    
    # 其他篩選條件
    if selected_customer_id:
        df = df[df['客戶ID'] == selected_customer_id]
    
    if selected_customer_name:
        df = df[df['客戶名稱'] == selected_customer_name]

    # 重置索引，讓按鈕index從0開始連續
    df = df.reset_index(drop=True)

    
    # 新增警告訊息欄位
    if missing_filter and not df.empty:
        warnings = []
        for idx, row in df.iterrows():
            warning_msg = []
            if pd.isna(row["電話"]) or row["電話"] == "" or row["電話"] == "None":
                warning_msg.append("缺少電話")
            if pd.isna(row["客戶地址"]) or row["客戶地址"] == "" or row["客戶地址"] == "None":
                warning_msg.append("缺少地址")
            warnings.append(" & ".join(warning_msg))
        df["警告"] = warnings
    
    # 儲存當前表格資料供匯出使用
    current_table_data = df.to_dict('records')
    
    # 如果是缺失資料篩選模式，在表格上方顯示警告訊息
    if missing_filter and not df.empty:
        table_component = html.Div([
            custom_table(
                df,
                button_text="編輯客戶資料",
                button_id_type="customer_data_button",
                show_button=True,
                sticky_columns=['客戶ID']
            )
        ])
    else:
        table_component = custom_table(
            df,
            button_text="編輯客戶資料",
            button_id_type="customer_data_button",
            show_button=True,
            sticky_columns=['客戶ID']
        )
    
    return table_component, current_table_data, button_style, warning_style

@app.callback(
    Output('customer_data_modal', 'is_open'),
    Output('input-customer-name', 'value'),
    Output('input-customer-id', 'value'),
    Output('input-customer-phone', 'value'),
    Output('input-customer-address', 'value'),
    Output('input-delivery-schedule', 'value'),
    Output('input-notes', 'value'),
    Input({'type': 'customer_data_button', 'index': ALL}, 'n_clicks'),
    [State("customer-data", "data"),
     State("customer_data-customer-id", "value"),
     State("customer_data-customer-name", "value"),
     State("missing-data-filter", "data")],  # 新增這個 State
    prevent_initial_call=True
)
def handle_edit_button_click(n_clicks, customer_data, selected_customer_id, selected_customer_name, missing_filter):  # 新增 missing_filter 參數
    if not any(n_clicks):
        return False, "", "", "", "", "", ""
    
    ctx = callback_context
    if not ctx.triggered:
        return False, "", "", "", "", "", ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_index = eval(button_id)['index']
    
    # 重新篩選資料，確保 index 對應正確
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
    
    # 轉換配送日數字為中文字 (與顯示邏輯保持一致)
    if "每週配送日" in df.columns:
        df["每週配送日"] = df["每週配送日"].apply(convert_delivery_schedule_to_chinese)
    
    # 修改這段 - 直接使用參數
    if missing_filter:
        missing_phone = df["電話"].isna() | (df["電話"] == "") | (df["電話"] == "None")
        missing_address = df["客戶地址"].isna() | (df["客戶地址"] == "") | (df["客戶地址"] == "None")
        df = df[missing_phone | missing_address]
    
    if selected_customer_id:
        df = df[df['客戶ID'] == selected_customer_id]
    
    if selected_customer_name:
        df = df[df['客戶名稱'] == selected_customer_name]
    
    # 重置索引，確保連續性
    df = df.reset_index(drop=True)
    
    if button_index < len(df):
        row_data = df.iloc[button_index]
        
        # 處理每週配送日的資料格式
        # 注意：這裡的 row_data 來自顯示表格，已經是中文格式
        delivery_schedule = row_data['每週配送日']
        if isinstance(delivery_schedule, str) and delivery_schedule:
            delivery_schedule_list = [day.strip() for day in delivery_schedule.split(',')]
        else:
            delivery_schedule_list = []
        
        return (True, 
                row_data['客戶名稱'], 
                row_data['客戶ID'], 
                row_data['電話'], 
                row_data['客戶地址'], 
                delivery_schedule_list,
                row_data['備註'])
    else:
        return False, "", "", "", "", "", ""

@app.callback(
    Output('customer_data_modal', 'is_open', allow_duplicate=True),
    Output('customer_data-success-toast', 'is_open'),
    Output('customer_data-success-toast', 'children'),
    Output('customer_data-error-toast', 'is_open', allow_duplicate=True),
    Output('customer_data-error-toast', 'children', allow_duplicate=True),
    Output('customer_data-warning-toast', 'is_open'),
    Output('customer_data-warning-toast', 'children'),
    Output("customer-data", "data", allow_duplicate=True),
    Input('input-customer-save', 'n_clicks'),
    State('input-customer-name', 'value'),
    State('input-customer-id', 'value'),
    State('input-customer-phone', 'value'),
    State('input-customer-address', 'value'),
    State('input-delivery-schedule', 'value'),
    State('input-notes', 'value'),
    State({'type': 'customer_data_button', 'index': ALL}, 'n_clicks'),
    State("customer-data", "data"),
    State("current-page", "data"),
    State("customer_data-customer-id", "value"),
    State("customer_data-customer-name", "value"),
    State("user-role-store", "data"),
    prevent_initial_call=True
)
def save_customer_data(save_clicks, customer_name, customer_id, phone_number, address, delivery_schedule, notes, button_clicks, customer_data, current_page, selected_customer_id, selected_customer_name, user_role):
    if not save_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    ctx = callback_context
    button_index = None
    
    for i, clicks in enumerate(button_clicks):
        if clicks:
            button_index = i
            break
    
    if button_index is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # 重新篩選資料，確保 index 對應正確
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
    
    # 重置索引，確保連續性
    df = df.reset_index(drop=True)
    
    if button_index >= len(df):
        return dash.no_update, False, "", True, "找不到對應的客戶資料", False, "", dash.no_update
    
    row_data = df.iloc[button_index]
    original_id = row_data['客戶ID']
    
    # 處理多選框的值，將中文轉換為數字再存入資料庫
    delivery_schedule_str = convert_delivery_schedule_to_numbers(delivery_schedule)
    
    update_data = {
        "customer_name": customer_name,
        "customer_id": customer_id,
        "phone_number": phone_number,
        "address": address,
        "delivery_schedule": delivery_schedule_str,
        "notes": notes
    }
    
    try:
        update_data["user_role"] = user_role or "viewer"
        response = requests.put(f"http://127.0.0.1:8000/customer/{original_id}", json=update_data)
        if response.status_code == 200:
            # 重新載入資料 - 使用實際的當前頁面
            try:
                current_page = current_page or 1  # 使用實際頁面
                reload_params = {
                    "page": current_page,
                    "page_size": 50
                }
                if selected_customer_id:
                    reload_params["customer_id"] = selected_customer_id
                if selected_customer_name:
                    reload_params["customer_name"] = selected_customer_name
                reload_response = requests.get("http://127.0.0.1:8000/get_customer_data", params=reload_params)
                if reload_response.status_code == 200:
                    reload_result = reload_response.json()
                    updated_customer_data = reload_result.get("data", [])
                    return False, True, "客戶資料更新成功！", False, "", False, "", updated_customer_data
                else:
                    return False, True, "客戶資料更新成功！", False, "", False, "", customer_data
            except:
                return False, True, "客戶資料更新成功！", False, "", False, "", customer_data
        elif response.status_code == 403:
            return dash.no_update, False, "", False, "", True, "權限不足：僅限編輯者使用此功能", dash.no_update
        else:
            return dash.no_update, False, "", True, f"API 呼叫錯誤，狀態碼：{response.status_code}", False, "", dash.no_update
    except Exception as e:
        return dash.no_update, False, "", True, f"資料載入時發生錯誤：{e}", False, "", dash.no_update

@app.callback(
    Output('customer_data_modal', 'is_open', allow_duplicate=True),
    Input('input-customer-cancel', 'n_clicks'),
    prevent_initial_call=True
)
def close_modal(cancel_clicks):
    if cancel_clicks:
        return False
    return dash.no_update

# 缺失資料篩選切換
@app.callback(
    Output("missing-data-filter", "data"),
    Output("missing-data-filter-button", "children"),
    Output("missing-data-filter-button", "color"),
    Input("missing-data-filter-button", "n_clicks"),
    State("missing-data-filter", "data"),
    State("customer-data", "data"),
    prevent_initial_call=True
)
def toggle_missing_data_filter(n_clicks, current_filter, customer_data):
    if n_clicks:
        # 檢查是否還有缺失資料
        if customer_data:
            df = pd.DataFrame(customer_data)
            missing_phone = df["phone_number"].isna() | (df["phone_number"] == "") | (df["phone_number"] == "None")
            missing_address = df["address"].isna() | (df["address"] == "") | (df["address"] == "None")
            has_missing_data = (missing_phone | missing_address).any()
            
            # 如果沒有缺失資料，不允許切換到篩選模式
            if not has_missing_data:
                return False, "缺失資料篩選", "warning"
        
        new_filter = not current_filter
        if new_filter:
            return new_filter, "顯示全部客戶", "success"
        else:
            return new_filter, "缺失資料篩選", "warning"
    return current_filter, "缺失資料篩選", "warning"

# 分頁控制 callback - 只保留底部
@app.callback(
    Output("pagination-controls-bottom", "children"),
    Input("pagination-info", "data")
)
def update_pagination_controls(pagination_info):
    if not pagination_info:
        return ""
    
    current_page = pagination_info.get("current_page", 1)
    total_pages = pagination_info.get("total_pages", 1)
    total_count = pagination_info.get("total_count", 0)
    has_prev = pagination_info.get("has_prev", False)
    has_next = pagination_info.get("has_next", False)
    
    controls = html.Div([
        dbc.ButtonGroup([
            dbc.Button("◀ 上一頁", 
                      id="prev-page-btn", 
                      disabled=not has_prev,
                      outline=True,
                      color="primary"),
            dbc.Button(f"第 {current_page} 頁 / 共 {total_pages} 頁",
                      disabled=True,
                      color="light"),
            dbc.Button("下一頁 ▶", 
                      id="next-page-btn", 
                      disabled=not has_next,
                      outline=True,
                      color="primary")
        ]),
        html.Span(f"共 {total_count} 筆資料", 
                 className="ms-3",
                 style={"alignSelf": "center", "color": "#666"})
    ], style={"display": "flex", "alignItems": "center"})
    
    return controls

# 分頁按鈕點擊處理
@app.callback(
    Output("current-page", "data"),
    [Input("prev-page-btn", "n_clicks"),
     Input("next-page-btn", "n_clicks")],
    [State("current-page", "data"),
     State("pagination-info", "data")],
    prevent_initial_call=True
)
def handle_pagination_clicks(prev_clicks, next_clicks, current_page, pagination_info):
    ctx = callback_context
    if not ctx.triggered:
        return current_page or 1

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "prev-page-btn" and pagination_info.get("has_prev"):
        return max(1, current_page - 1)
    elif button_id == "next-page-btn" and pagination_info.get("has_next"):
        return min(pagination_info.get("total_pages", 1), current_page + 1)

    return current_page

@app.callback(
    Output("current-page", "data", allow_duplicate=True),
    [Input("customer_data-customer-id", "value"),
     Input("customer_data-customer-name", "value")],
    prevent_initial_call=True
)
def reset_current_page_on_search(customer_id, customer_name):
    return 1
