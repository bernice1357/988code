from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from callbacks.export_callback import create_export_callback, add_download_component
import requests
import pandas as pd
from datetime import datetime, date
import dash

# TODO 照時間排序

# offcanvas
product_input_fields = [
    {
        "id": "date-picker", 
        "label": "新品購買日期區間",
        "type": "date_range",
        "start_date": "",  # 覆蓋預設值為空
        "end_date": ""     # 覆蓋預設值為空
    },
    {
        "id": "customer-id", 
        "label": "客戶ID",
        "type": "dropdown",
        "options": [],  # 初始為空，會透過 callback 動態載入
        "placeholder": "請選擇客戶"
    },
]
product_components = create_search_offcanvas(
    page_name="buy_new_item",
    input_fields=product_input_fields
)

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[
    dcc.Store(id="buy_new_item-page-loaded", data=True),
    dcc.Store(id="buy_new_item-data", data=[]),
    dcc.Store(id="buy_new_item-current-table-data", data=[]),  # 儲存當前表格顯示的資料
    dcc.Store(id="buy_new_item-date-validation", data={"is_valid": True, "message": ""}),  # 新增日期驗證狀態
    dcc.Store(id="buy_new_item-sort-state", data={"column": "購買時間", "ascending": False}),  # 排序狀態存儲
    add_download_component("buy_new_item"),  # 加入下載元件

    # 篩選條件區
    html.Div([
        product_components["trigger_button"],
        dbc.Button("匯出列表資料", id="buy_new_item-export-button", n_clicks=0, color="primary", outline=True)
    ], className="mb-3 d-flex justify-content-between align-items-center"),

    product_components["offcanvas"],

    dcc.Loading(
        id="loading-buy-new-item-table",
        type="dot",
        children=html.Div(id="buy_new_item-table-container", style={"marginTop": "20px"}),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "position": "fixed", 
            "top": "50%",          
        }
    ),
    error_toast("buy_new_item"),
])

register_offcanvas_callback(app, "buy_new_item")

# 註冊匯出功能 - 使用當前表格資料
create_export_callback(app, "buy_new_item", "buy_new_item-current-table-data", "新品購買資料")

# 日期驗證 callback
@app.callback(
    [Output("buy_new_item-date-validation", "data"),
     Output("buy_new_item-date-picker-start", "invalid"),
     Output("buy_new_item-date-picker-end", "invalid")],
    [Input("buy_new_item-date-picker-start", "value"),
     Input("buy_new_item-date-picker-end", "value")],
    prevent_initial_call=False
)
def validate_date_range(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        error_msg = f"結束日期不能早於開始日期"
        return {"is_valid": False, "message": error_msg}, True, True
    else:
        return {"is_valid": True, "message": ""}, False, False

# 載入客戶ID選項的 callback
@app.callback(
    Output("buy_new_item-customer-id", "options", allow_duplicate=True),
    Input("buy_new_item-page-loaded", "data"),
    prevent_initial_call=True
)
def load_customer_options(page_loaded):
    try:
        response = requests.get('http://127.0.0.1:8000/get_new_item_customers')
        
        if response.status_code != 200:
            return []
            
        data = response.json()
        options = [{"label": f"{item['customer_id']} - {item['customer_name']}", "value": item['customer_id']} for item in data]
        return options
        
    except requests.exceptions.RequestException as e:
        print(f"載入客戶選項失敗: {e}")
        return []
    except Exception as e:
        print(f"處理客戶選項失敗: {e}")
        return []

# 載入新品購買資料的 callback
@app.callback(
    Output("buy_new_item-data", "data"),
    Input("buy_new_item-page-loaded", "data"),
    prevent_initial_call=False
)
def load_new_item_data(page_loaded):
    try:
        response = requests.get('http://127.0.0.1:8000/get_new_item_orders')
        
        if response.status_code != 200:
            return []
            
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"API請求失敗: {e}")
        return []
    except Exception as e:
        print(f"資料處理失敗: {e}")
        return []

# 載入客戶選項的獨立 callback - 使用不同的觸發條件
@app.callback(
    Output("buy_new_item-customer-id", "options"),
    Input("buy_new_item-data", "data"),  # 改用資料載入完成作為觸發條件
    prevent_initial_call=False
)
def load_customer_options(data):
    try:
        response = requests.get('http://127.0.0.1:8000/get_new_item_customers')
        
        if response.status_code != 200:
            print(f"API回應狀態碼: {response.status_code}")
            return []
            
        customer_data = response.json()
        
        if not customer_data:
            return []
        
        # 提取所有客戶ID並去重
        customer_ids = list(set([item['customer_id'] for item in customer_data if 'customer_id' in item]))
        
        # 建立選項列表
        options = [{"label": customer_id, "value": customer_id} for customer_id in sorted(customer_ids)]
        
        return options
        
    except requests.exceptions.RequestException as e:
        print(f"載入客戶選項失敗: {e}")
        return []
    except Exception as e:
        print(f"處理客戶選項失敗: {e}")
        return []

# 顯示篩選後的表格
@app.callback(
    [Output("buy_new_item-table-container", "children"),
     Output("buy_new_item-current-table-data", "data"),  # 同時更新當前表格資料
     Output('buy_new_item-error-toast', 'is_open'),
     Output('buy_new_item-error-toast', 'children')],
    [Input("buy_new_item-data", "data"),
     Input("buy_new_item-date-picker-start", "value"),
     Input("buy_new_item-date-picker-end", "value"),
     Input("buy_new_item-customer-id", "value"),
     Input("buy_new_item-sort-state", "data")],
    prevent_initial_call=False
)
def display_filtered_table(data, start_date, end_date, customer_id, sort_state):
    
    if not data:
        return html.Div("暫無資料"), [], False, ""
    
    # 轉換為 DataFrame
    filtered_df = pd.DataFrame(data)
    
    # 重新命名欄位和格式化時間
    if not filtered_df.empty:
        filtered_df = filtered_df.rename(columns={
            'customer_id': '客戶 ID',
            'customer_name': '客戶名稱',
            'purchase_record': '購買品項',
            'created_at': '購買時間'
        })
        
        # 格式化購買時間
        filtered_df['購買時間'] = pd.to_datetime(filtered_df['購買時間']).dt.strftime('%Y-%m-%d %H:%M')
    
    # 日期篩選 - 只有在同時有開始和結束日期時才進行篩選
    if start_date and end_date:
        
        # 轉換購買時間為datetime格式，格式: "2024-01-15 10:30"
        filtered_df['購買時間_datetime'] = pd.to_datetime(filtered_df['購買時間'], format='%Y-%m-%d %H:%M')
        
        # 設定日期範圍
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # 包含結束日期整天
        
        # 篩選日期範圍
        before_filter = len(filtered_df)
        filtered_df = filtered_df[
            (filtered_df['購買時間_datetime'] >= start_datetime) & 
            (filtered_df['購買時間_datetime'] <= end_datetime)
        ]
        
        # 移除輔助欄位
        filtered_df = filtered_df.drop(columns=['購買時間_datetime'])
    
    # 客戶ID篩選
    if customer_id:
        before_filter = len(filtered_df)
        filtered_df = filtered_df[filtered_df['客戶 ID'] == customer_id]
    
    # 排序處理
    if sort_state and sort_state.get("column") in filtered_df.columns:
        sort_column = sort_state["column"]
        ascending = sort_state.get("ascending", True)
        
        # 如果是購買時間欄位，需要轉換為datetime進行排序
        if sort_column == "購買時間":
            filtered_df['購買時間_sort'] = pd.to_datetime(filtered_df['購買時間'])
            filtered_df = filtered_df.sort_values('購買時間_sort', ascending=ascending)
            filtered_df = filtered_df.drop(columns=['購買時間_sort'])
        else:
            filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)
    
    # 重置索引，讓按鈕index從0開始連續
    filtered_df = filtered_df.reset_index(drop=True)
    
    # 儲存當前表格資料供匯出使用
    current_table_data = filtered_df.to_dict('records')
    
    # 呼叫 custom_table 並指定可排序的欄位
    table_component = custom_table(filtered_df, sortable_columns=["客戶 ID", "購買時間"], sort_state=sort_state)
    
    return table_component, current_table_data, False, ""

# 處理排序按鈕點擊
@app.callback(
    Output("buy_new_item-sort-state", "data"),
    [Input({"type": "sort-button", "column": "客戶 ID"}, "n_clicks"),
     Input({"type": "sort-button", "column": "購買時間"}, "n_clicks")],
    State("buy_new_item-sort-state", "data"),
    prevent_initial_call=True
)
def handle_sort_button_click(customer_id_clicks, purchase_time_clicks, current_sort_state):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_sort_state
    
    # 判斷是哪個按鈕被點擊
    triggered_prop = ctx.triggered[0]["prop_id"]
    if "客戶 ID" in triggered_prop:
        clicked_column = "客戶 ID"
    elif "購買時間" in triggered_prop:
        clicked_column = "購買時間"
    else:
        return current_sort_state
    
    # 如果點擊的是同一欄位，則切換排序方向
    if current_sort_state.get("column") == clicked_column:
        new_ascending = not current_sort_state.get("ascending", True)
    else:
        # 如果點擊不同欄位，則預設為升序
        new_ascending = True
    
    return {
        "column": clicked_column,
        "ascending": new_ascending
    }