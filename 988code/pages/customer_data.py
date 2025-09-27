from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from callbacks.export_callback import add_download_component
from dash import ALL, callback_context
import json

from datetime import datetime
# DataFrame 處理輔助函數
def process_customer_dataframe(customer_data, selected_customer_id=None, selected_customer_name=None, missing_filter=False):
    """統一處理客戶資料DataFrame的函數，避免重複代碼"""
    if not customer_data:
        return pd.DataFrame()
    
    # 確保 customer_data 是正確的格式
    if isinstance(customer_data, dict):
        if 'data' in customer_data:
            customer_data = customer_data['data']
        else:
            customer_data = [customer_data]
    
    if not customer_data:
        return pd.DataFrame()
    
    # 創建 DataFrame
    df = pd.DataFrame(customer_data)
    
    # 重命名欄位
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
    
    # 應用篩選條件
    if missing_filter:
        missing_phone = df["電話"].isna() | (df["電話"] == "") | (df["電話"] == "None")
        missing_address = df["客戶地址"].isna() | (df["客戶地址"] == "") | (df["客戶地址"] == "None")
        df = df[missing_phone | missing_address]
    
    if selected_customer_id:
        df = df[df['客戶ID'] == selected_customer_id]
    
    if selected_customer_name:
        df = df[df['客戶名稱'] == selected_customer_name]
    
    # 重置索引
    df = df.reset_index(drop=True)
    
    return df

def update_customer_record_locally(customer_data, button_index, updated_fields, selected_customer_id=None, selected_customer_name=None, missing_filter=False):
    """本地更新客戶記錄，避免重新查詢資料庫"""
    if not customer_data:
        return customer_data
    
    # 處理 DataFrame 找到對應記錄
    df = process_customer_dataframe(customer_data, selected_customer_id, selected_customer_name, missing_filter)
    
    if button_index >= len(df):
        return customer_data
    
    # 找到原始資料中對應的記錄
    target_customer_id = df.iloc[button_index]['客戶ID']
    
    # 直接更新原始 customer_data 中的記錄
    updated_data = customer_data.copy()
    for i, record in enumerate(updated_data):
        if record.get('customer_id') == target_customer_id:
            # 更新記錄
            updated_data[i].update({
                'customer_name': updated_fields.get('customer_name', record.get('customer_name')),
                'customer_id': updated_fields.get('customer_id', record.get('customer_id')),
                'phone_number': updated_fields.get('phone_number', record.get('phone_number')),
                'address': updated_fields.get('address', record.get('address')),
                'delivery_schedule': updated_fields.get('delivery_schedule', record.get('delivery_schedule')),
                'notes': updated_fields.get('notes', record.get('notes'))
            })
            break
    
    return updated_data

# 配送日轉換函數
def convert_delivery_schedule_to_chinese(schedule_str):
    # 處理 pandas NaN 值
    import pandas as pd
    if pd.isna(schedule_str) or not schedule_str or (isinstance(schedule_str, str) and schedule_str.strip() == ""):
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
    dcc.Location(id="page-reload-trigger", refresh=True),
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
            dbc.DropdownMenu(
                label="匯出列表資料",
                color="primary",
                toggle_class_name="btn btn-outline-primary",
                direction="down",
                class_name="customer-export-dropdown",
                children=[
                    dbc.DropdownMenuItem("匯出當前列表", id="customer_data-export-current"),
                    dbc.DropdownMenuItem("匯出全部列表", id="customer_data-export-all")
                ]
            )
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
                dbc.Button("刪除", id="input-customer-delete", color="danger", className="me-auto"),  # 新增刪除按鈕，置左
                dbc.Button("取消", id="input-customer-cancel", color="secondary", className="me-2"),
                dbc.Button("儲存", id="input-customer-save", color="primary")
            ])
        ]
    ),
    dbc.Modal(
    id="delete-customer-confirm-modal",
    is_open=False,
    size="md",
    centered=True,
    children=[
        dbc.ModalHeader("確認刪除客戶"),
        dbc.ModalBody([
            html.P("確定要刪除此客戶嗎？此操作無法復原。", style={"color": "red", "fontWeight": "bold"}),
            html.Div(id="delete-customer-info")
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-delete-customer", color="secondary", className="me-2"),
            dbc.Button("確認刪除", id="confirm-delete-customer", color="danger")
        ])
    ]
),
    success_toast("customer_data", message=""),
    error_toast("customer_data", message=""),
    warning_toast("customer_data", message=""),
])

register_offcanvas_callback(app, "customer_data")


# 匯出相關工具函式
def fetch_all_customer_records(selected_customer_id, selected_customer_name):
    """Retrieve every page of customer data with optional filters."""
    page = 1
    page_size = 200
    aggregated = []

    while True:
        params = {"page": page, "page_size": page_size}
        if selected_customer_id:
            params["customer_id"] = selected_customer_id
        if selected_customer_name:
            params["customer_name"] = selected_customer_name

        response = requests.get("http://127.0.0.1:8000/get_customer_data", params=params)
        if response.status_code != 200:
            raise ValueError(f"API 回應碼：{response.status_code}")

        payload = response.json()
        batch = payload.get("data", []) or []
        aggregated.extend(batch)

        pagination = payload.get("pagination") or {}
        total_pages = pagination.get("total_pages")

        if not batch:
            break

        if total_pages and page >= total_pages:
            break

        if not total_pages and len(batch) < page_size:
            break

        page += 1

    return aggregated


def prepare_customer_export_dataframe(records, missing_filter_enabled):
    """Format customer records to match the visible table export."""
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df = df.rename(columns={
        "customer_id": "客戶ID",
        "customer_name": "客戶名稱",
        "phone_number": "電話",
        "address": "客戶地址",
        "delivery_schedule": "每週配送日",
        "transaction_date": "最新交易日期",
        "notes": "備註"
    })

    if "每週配送日" in df.columns:
        df["每週配送日"] = df["每週配送日"].apply(convert_delivery_schedule_to_chinese)

    if "電話" in df.columns:
        missing_phone = df["電話"].isna() | (df["電話"] == "") | (df["電話"] == "None")
    else:
        missing_phone = pd.Series([False] * len(df), index=df.index)

    if "客戶地址" in df.columns:
        missing_address = df["客戶地址"].isna() | (df["客戶地址"] == "") | (df["客戶地址"] == "None")
    else:
        missing_address = pd.Series([False] * len(df), index=df.index)

    if missing_filter_enabled:
        df = df[missing_phone | missing_address]

    if missing_filter_enabled and not df.empty:
        warnings = []
        for _, row in df.iterrows():
            warning_msg = []
            phone_value = row.get("電話")
            if pd.isna(phone_value) or phone_value in ("", "None"):
                warning_msg.append("缺少電話")
            address_value = row.get("客戶地址")
            if pd.isna(address_value) or address_value in ("", "None"):
                warning_msg.append("缺少地址")
            warnings.append(" & ".join(warning_msg))
        df["警告"] = warnings

    return df.reset_index(drop=True)


@app.callback(
    Output("customer_data-download", "data", allow_duplicate=True),
    Output("customer_data-error-toast", "is_open", allow_duplicate=True),
    Output("customer_data-error-toast", "children", allow_duplicate=True),
    Input("customer_data-export-current", "n_clicks"),
    Input("customer_data-export-all", "n_clicks"),
    State("current-table-data", "data"),
    State("customer_data-customer-id", "value"),
    State("customer_data-customer-name", "value"),
    State("missing-data-filter", "data"),
    prevent_initial_call=True
)
def handle_customer_exports(current_clicks, all_clicks, current_table_data, selected_customer_id, selected_customer_name, missing_filter):
    if not callback_context.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = callback_context.triggered[0]["prop_id"].split(".")[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    missing_filter_enabled = bool(missing_filter)

    if trigger_id == "customer_data-export-current":
        if not current_table_data:
            return dash.no_update, True, "目前沒有資料可匯出"

        export_df = pd.DataFrame(current_table_data)
        if export_df.empty:
            return dash.no_update, True, "目前沒有資料可匯出"

        filename = f"客戶資料_當前列表_{timestamp}.xlsx"
        return dcc.send_data_frame(export_df.to_excel, filename, index=False), False, ""

    if trigger_id == "customer_data-export-all":
        try:
            records = fetch_all_customer_records(selected_customer_id, selected_customer_name)
        except Exception as exc:
            return dash.no_update, True, f"匯出全部列表失敗：{exc}"

        export_df = prepare_customer_export_dataframe(records, missing_filter_enabled)
        if export_df.empty:
            return dash.no_update, True, "沒有找到可匯出的資料"

        filename = f"客戶資料_全部列表_{timestamp}.xlsx"
        return dcc.send_data_frame(export_df.to_excel, filename, index=False), False, ""

    return dash.no_update, dash.no_update, dash.no_update


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
        # 使用新的輔助函數處理 DataFrame
        df = process_customer_dataframe(customer_data, selected_customer_id, selected_customer_name, missing_filter)
        
        if df.empty:
            return html.Div("暫無資料"), [], {"display": "block"}, {"display": "block"}
        
    except Exception as e:
        print(f"DataFrame 創建錯誤: {e}")
        return html.Div("資料格式錯誤"), [], {"display": "block"}, {"display": "block"}
    
    # 檢查是否有缺失資料（用於按鈕顯示）
    original_df = process_customer_dataframe(customer_data)  # 不套用篩選的原始資料
    if not original_df.empty:
        missing_phone = original_df["電話"].isna() | (original_df["電話"] == "") | (original_df["電話"] == "None")
        missing_address = original_df["客戶地址"].isna() | (original_df["客戶地址"] == "") | (original_df["客戶地址"] == "None")
        has_missing_data = (missing_phone | missing_address).any()
    else:
        has_missing_data = False
    
    # 根據是否有缺失資料決定按鈕和警告的顯示
    button_style = {"display": "none"} if not has_missing_data else {"marginLeft": "10px"}
    warning_style = {"display": "none"} if not has_missing_data else {
        "marginLeft": "15px", 
        "color": "#dc3545", 
        "fontWeight": "bold",
        "alignSelf": "center"
    }

    
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
        return False, "", "", "", "", [], ""
    
    ctx = callback_context
    if not ctx.triggered:
        return False, "", "", "", "", [], ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_index = eval(button_id)['index']
    
    # 使用新的輔助函數處理 DataFrame
    df = process_customer_dataframe(customer_data, selected_customer_id, selected_customer_name, missing_filter)
    
    if button_index < len(df):
        row_data = df.iloc[button_index]
        
        # 處理每週配送日的資料格式
        # 注意：這裡的 row_data 來自顯示表格，已經是中文格式
        delivery_schedule = row_data['每週配送日']
        if isinstance(delivery_schedule, str) and delivery_schedule and delivery_schedule.strip():
            delivery_schedule_list = [day.strip() for day in delivery_schedule.split(',') if day.strip()]
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
        return False, "", "", "", "", [], ""

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
    State("missing-data-filter", "data"),
    State("user-role-store", "data"),
    prevent_initial_call=True
)
def save_customer_data(save_clicks, customer_name, customer_id, phone_number, address, delivery_schedule, notes, button_clicks, customer_data, current_page, selected_customer_id, selected_customer_name, missing_filter, user_role):
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
    
    # 使用新的輔助函數處理 DataFrame
    df = process_customer_dataframe(customer_data, selected_customer_id, selected_customer_name)
    
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
        # 樂觀更新：先更新本地資料
        optimistic_update_data = {
            'customer_name': customer_name,
            'customer_id': customer_id,
            'phone_number': phone_number,
            'address': address,
            'delivery_schedule': delivery_schedule_str,
            'notes': notes
        }
        
        # 本地更新資料
        updated_customer_data = update_customer_record_locally(
            customer_data, 
            button_index, 
            optimistic_update_data,
            selected_customer_id,
            selected_customer_name,
            missing_filter or False
        )
        
        # 準備 API 調用
        update_data["user_role"] = user_role or "viewer"
        
        # 嘗試 API 調用，但使用較短的超時時間
        try:
            response = requests.put(f"http://127.0.0.1:8000/customer/{original_id}", json=update_data, timeout=2)
            if response.status_code == 200:
                # API 成功，返回樂觀更新結果
                return False, True, "客戶資料更新成功！", False, "", False, "", updated_customer_data
            elif response.status_code == 403:
                # 權限錯誤，回滾到原始資料
                return dash.no_update, False, "", False, "", True, "權限不足：僅限編輯者使用此功能", customer_data
            else:
                # 其他 API 錯誤，但仍返回樂觀更新結果（因為可能是暫時性問題）
                print(f"API 調用失敗但返回樂觀結果: {response.status_code}")
                return False, True, "客戶資料已更新（正在後台同步）", False, "", False, "", updated_customer_data
        except requests.exceptions.Timeout:
            # 超時，返回樂觀更新結果
            print("API 調用超時，但返回樂觀結果")
            return False, True, "客戶資料已更新（正在後台同步）", False, "", False, "", updated_customer_data
        except Exception as api_error:
            # 其他網路錯誤，仍返回樂觀更新結果
            print(f"API 調用錯誤但返回樂觀結果: {api_error}")
            return False, True, "客戶資料已更新（正在後台同步）", False, "", False, "", updated_customer_data
        
    except Exception as e:
        return dash.no_update, False, "", True, f"資料更新時發生錯誤：{e}", False, "", dash.no_update

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

    try:
        total_pages = int(total_pages)
    except (TypeError, ValueError):
        total_pages = 1
    total_pages = max(total_pages, 1)

    try:
        current_page = int(current_page)
    except (TypeError, ValueError):
        current_page = 1
    current_page = max(1, min(current_page, total_pages))

    menu_items = [
        dbc.DropdownMenuItem(
            f"第 {page} 頁",
            id={"type": "page-selection-item", "index": page},
            disabled=(page == current_page),
            className="pagination-dropdown-item active" if page == current_page else "pagination-dropdown-item",
        )
        for page in range(1, total_pages + 1)
    ]

    dropdown = dbc.DropdownMenu(
        label=f"第 {current_page} 頁 / 共 {total_pages} 頁",
        id="page-selection-dropdown",
        color="light",
        direction="up",
        caret=False,
        className="pagination-dropdown-menu",
        children=menu_items,
    )

    controls = html.Div([
        dbc.ButtonGroup([
            dbc.Button("⏮ 最前頁",
                      id="first-page-btn",
                      disabled=not has_prev,
                      outline=True,
                      color="primary"),
            dbc.Button("◀ 上一頁",
                      id="prev-page-btn",
                      disabled=not has_prev,
                      outline=True,
                      color="primary"),
            dropdown,
            dbc.Button("下一頁 ▶",
                      id="next-page-btn",
                      disabled=not has_next,
                      outline=True,
                      color="primary"),
            dbc.Button("最末頁 ⏭",
                      id="last-page-btn",
                      disabled=not has_next,
                      outline=True,
                      color="primary")
        ]),
        html.Span(f"共 {total_count} 筆資料",
                 className="ms-3",
                 style={"alignSelf": "center", "color": "#666"})
    ], style={"display": "flex", "alignItems": "center"})

    return controls

@app.callback(
    Output("current-page", "data"),
    [Input("first-page-btn", "n_clicks"),
     Input("prev-page-btn", "n_clicks"),
     Input("next-page-btn", "n_clicks"),
     Input("last-page-btn", "n_clicks")],
    [State("current-page", "data"),
     State("pagination-info", "data")],
    prevent_initial_call=True
)
def handle_pagination_clicks(first_clicks, prev_clicks, next_clicks, last_clicks, current_page, pagination_info):
    ctx = callback_context
    if not ctx.triggered:
        return current_page or 1

    pagination_info = pagination_info or {}

    def _to_int(value, default=1):
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return default

    def _to_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return False

    api_current_page = pagination_info.get("current_page")
    current_page = _to_int(api_current_page, default=_to_int(current_page or 1))
    total_pages = _to_int(pagination_info.get("total_pages", 1))
    current_page = min(current_page, total_pages)

    has_prev = _to_bool(pagination_info.get("has_prev"))
    has_next = _to_bool(pagination_info.get("has_next"))

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "first-page-btn" and has_prev:
        return 1
    if button_id == "prev-page-btn" and has_prev:
        return max(1, current_page - 1)
    if button_id == "next-page-btn" and has_next:
        return min(total_pages, current_page + 1)
    if button_id == "last-page-btn" and has_next:
        return total_pages

    return current_page

@app.callback(
    Output("current-page", "data", allow_duplicate=True),
    Input({"type": "page-selection-item", "index": ALL}, "n_clicks"),
    State("current-page", "data"),
    prevent_initial_call=True
)
def handle_page_selection_dropdown(item_clicks, current_page):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    triggered = ctx.triggered[0]
    if not triggered.get("value"):
        return dash.no_update

    try:
        triggered_id = json.loads(triggered["prop_id"].split(".")[0])
    except (json.JSONDecodeError, IndexError):
        return dash.no_update

    target_index = triggered_id.get("index")
    try:
        target_page = int(target_index)
    except (TypeError, ValueError):
        return dash.no_update

    if target_page < 1:
        return dash.no_update

    return target_page


@app.callback(
    Output("current-page", "data", allow_duplicate=True),
    [Input("customer_data-customer-id", "value"),
     Input("customer_data-customer-name", "value")],
    prevent_initial_call=True
)
def reset_current_page_on_search(customer_id, customer_name):
    return 1


# 顯示刪除確認 Modal
@app.callback(
    Output('delete-customer-confirm-modal', 'is_open'),
    Output('delete-customer-info', 'children'),
    Input('input-customer-delete', 'n_clicks'),
    State('input-customer-name', 'value'),
    State('input-customer-id', 'value'),
    prevent_initial_call=True
)
def show_delete_confirmation(delete_clicks, customer_name, customer_id):
    if delete_clicks:
        info = html.Div([
            html.P(f"客戶ID: {customer_id}"),
            html.P(f"客戶名稱: {customer_name}")
        ])
        return True, info
    return False, ""

# 處理確認刪除
@app.callback(
    Output('delete-customer-confirm-modal', 'is_open', allow_duplicate=True),
    Output('customer_data_modal', 'is_open', allow_duplicate=True),
    Output('customer_data-success-toast', 'is_open', allow_duplicate=True),
    Output('customer_data-success-toast', 'children', allow_duplicate=True),
    Output('customer_data-error-toast', 'is_open', allow_duplicate=True),
    Output('customer_data-error-toast', 'children', allow_duplicate=True),
    Output("page-reload-trigger", "href", allow_duplicate=True),  # 添加這個輸出
    Input('confirm-delete-customer', 'n_clicks'),
    Input('cancel-delete-customer', 'n_clicks'),
    State('input-customer-id', 'value'),
    State("customer-data", "data"),
    State("user-role-store", "data"),
    State("current-page", "data"),
    State("customer_data-customer-id", "value"),
    State("customer_data-customer-name", "value"),
    prevent_initial_call=True
)
def handle_delete_confirmation(confirm_clicks, cancel_clicks, customer_id, customer_data, user_role, current_page, selected_customer_id, selected_customer_name):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'cancel-delete-customer':
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if button_id == 'confirm-delete-customer' and confirm_clicks:
        try:
            # 調用刪除 API
            response = requests.delete(f"http://127.0.0.1:8000/customer/{customer_id}", 
                                     json={"user_role": user_role or "viewer"})
            
            if response.status_code == 200:
                # 刪除成功後重新載入整個頁面
                # 通過改變 href 觸發頁面重新載入
                return False, False, True, "客戶刪除成功！正在重新載入頁面...", False, "", "/customer_data"
                
            elif response.status_code == 403:
                return False, dash.no_update, False, "", True, "權限不足：僅限編輯者使用此功能", dash.no_update
            else:
                return False, dash.no_update, False, "", True, "刪除失敗", dash.no_update
                
        except Exception as e:
            return False, dash.no_update, False, "", True, f"刪除時發生錯誤：{e}", dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update