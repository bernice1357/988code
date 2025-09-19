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
    dcc.Store(id="user-role-store"),
    dcc.Store(id="current-table-data", data=[]),
    # 快取組件
    dcc.Store(id="customer-cache-store", data={
        'customer_data': [],
        'cached_at': None,
        'cache_version': 1
    }),
    # 增量更新檢查
    dcc.Interval(
        id='update-checker-interval',
        interval=30000,  # 每30秒檢查一次更新
        n_intervals=0,
        disabled=False
    ),
    dcc.Store(id='last-update-time', data=None),
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

# 載入客戶資料的 callback（含快取機制和批次載入）
@app.callback(
    Output("customer-data", "data"),
    Output("customer-cache-store", "data"),
    Output("last-update-time", "data"),
    Output('customer_data-error-toast', 'is_open'),
    Output('customer_data-error-toast', 'children'),
    Input("page-loaded", "data"),
    State("customer-cache-store", "data"),
    prevent_initial_call=False
)
def load_customer_data_with_cache(page_loaded, cache_data):
    from datetime import datetime
    current_time = datetime.now()
    
    # 檢查快取是否有效（5分鐘內）
    if cache_data and cache_data.get('cached_at'):
        try:
            cached_time = datetime.fromisoformat(cache_data['cached_at'])
            cache_age_seconds = (current_time - cached_time).total_seconds()
            if cache_age_seconds < 300:  # 5分鐘
                print(f"[CACHE] 使用快取資料，快取年齡: {cache_age_seconds:.1f}秒")
                return cache_data['customer_data'], cache_data, current_time.isoformat(), False, ""
        except (ValueError, TypeError) as e:
            print(f"[CACHE] 快取時間解析錯誤: {e}")
    
    # 快取過期或無快取，重新載入所有資料
    print("[API] 重新載入客戶資料（全部）")
    try:
        # 載入所有資料（不使用分頁）
        response = requests.get("http://127.0.0.1:8000/get_customer_data")
        
        if response.status_code == 200:
            try:
                result = response.json()
                customer_data = result['data']
                
                # 更新快取
                new_cache = {
                    'customer_data': customer_data,
                    'cached_at': current_time.isoformat(),
                    'cache_version': cache_data.get('cache_version', 1) + 1 if cache_data else 1
                }
                
                print(f"[CACHE] 已快取 {len(customer_data)} 筆客戶資料")
                return customer_data, new_cache, current_time.isoformat(), False, ""
                
            except requests.exceptions.JSONDecodeError:
                # API 失敗且有舊快取，使用舊快取
                if cache_data and cache_data.get('customer_data'):
                    print("[CACHE] API 解析失敗，使用舊快取")
                    return cache_data['customer_data'], cache_data, current_time.isoformat(), True, "API 回應格式錯誤，使用快取資料"
                return [], cache_data, current_time.isoformat(), True, "回應內容不是有效的 JSON"
        else:
            # API 失敗且有舊快取，使用舊快取
            if cache_data and cache_data.get('customer_data'):
                print(f"[CACHE] API 失敗 ({response.status_code})，使用舊快取")
                return cache_data['customer_data'], cache_data, current_time.isoformat(), True, f"資料載入失敗 (狀態碼：{response.status_code})，使用快取資料"
            return [], cache_data, current_time.isoformat(), True, f"資料載入失敗，狀態碼：{response.status_code}"
    except Exception as e:
        # 網路錯誤且有舊快取，使用舊快取
        if cache_data and cache_data.get('customer_data'):
            print(f"[CACHE] 網路錯誤，使用舊快取: {e}")
            return cache_data['customer_data'], cache_data, current_time.isoformat(), True, f"網路連接失敗，使用快取資料: {str(e)}"
        return [], cache_data, current_time.isoformat(), True, f"載入資料時發生錯誤：{e}"

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
    State("customer_data-customer-id", "value"),
    State("customer_data-customer-name", "value"),
    State("user-role-store", "data"),
    prevent_initial_call=True
)
def save_customer_data(save_clicks, customer_name, customer_id, phone_number, address, delivery_schedule, notes, button_clicks, customer_data, selected_customer_id, selected_customer_name, user_role):
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
            # 重新載入資料
            try:
                reload_response = requests.get("http://127.0.0.1:8000/get_customer_data")
                if reload_response.status_code == 200:
                    updated_customer_data = reload_response.json()
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

# 當客戶資料被修改時，自動清空快取
@app.callback(
    Output("customer-cache-store", "data", allow_duplicate=True),
    Input("customer_data-success-toast", "is_open"),  # 成功保存後觸發
    State("customer-cache-store", "data"),
    prevent_initial_call=True
)
def invalidate_cache_on_save(toast_open, cache_data):
    if toast_open:  # 有資料更新
        print("[CACHE] 資料更新，清空快取")
        from datetime import datetime
        return {
            'customer_data': [],
            'cached_at': None,
            'cache_version': cache_data.get('cache_version', 1) + 1 if cache_data else 1
        }
    return dash.no_update


# 增量更新檢查 callback
@app.callback(
    Output("customer-data", "data", allow_duplicate=True),
    Output("customer-cache-store", "data", allow_duplicate=True),
    Output("last-update-time", "data", allow_duplicate=True),
    Input("update-checker-interval", "n_intervals"),
    State("customer-data", "data"),
    State("customer-cache-store", "data"),
    State("last-update-time", "data"),
    prevent_initial_call=True
)
def check_for_updates(n_intervals, current_data, cache_data, last_update):
    if not current_data or not last_update:
        return dash.no_update, dash.no_update, dash.no_update
    
    try:
        from datetime import datetime
        print(f"[UPDATE] 檢查增量更新，上次更新時間: {last_update}")
        
        params = {'last_update': last_update}
        response = requests.get("http://127.0.0.1:8000/get_customer_updates", params=params)
        
        if response.status_code == 200:
            result = response.json()
            updates = result['updates']
            
            if updates:
                print(f"[UPDATE] 發現 {len(updates)} 筆資料更新")
                
                # 更新現有資料
                updated_data = current_data.copy()
                for update in updates:
                    # 找到對應的記錄並更新
                    for i, record in enumerate(updated_data):
                        if record['customer_id'] == update['customer_id']:
                            # 更新現有記錄，保留原有的欄位結構
                            updated_record = record.copy()
                            updated_record.update({
                                'customer_name': update['customer_name'],
                                'phone_number': update['phone_number'],
                                'address': update['address'],
                                'delivery_schedule': update['delivery_schedule'],
                                'notes': update['notes'],
                                'transaction_date': update['transaction_date']
                            })
                            updated_data[i] = updated_record
                            break
                    else:
                        # 新記錄，添加到列表
                        updated_data.append(update)
                
                # 更新快取
                new_cache = cache_data.copy() if cache_data else {}
                new_cache['customer_data'] = updated_data
                new_cache['cached_at'] = datetime.now().isoformat()
                
                return updated_data, new_cache, result['last_update_time']
            else:
                print("[UPDATE] 沒有新的資料更新")
                
    except Exception as e:
        print(f"[ERROR] 檢查更新失敗: {e}")
    
    return dash.no_update, dash.no_update, dash.no_update

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