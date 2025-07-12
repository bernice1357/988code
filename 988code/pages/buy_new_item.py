"""
要用temp_customer_records
"""

from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
import requests
import pandas as pd
from datetime import datetime, date

def get_new_item_orders():
    """從API獲取新品訂單資料"""
    try:
        response = requests.get('http://127.0.0.1:8000/get_new_item_orders')
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        
        # 重新命名欄位和格式化時間
        if not df.empty:
            df = df.rename(columns={
                'customer_id': '客戶 ID',
                'customer_name': '客戶名稱',
                'purchase_record': '購買品項',
                'created_at': '購買時間'
            })
            
            # 格式化購買時間
            df['購買時間'] = pd.to_datetime(df['購買時間']).dt.strftime('%Y-%m-%d %H:%M')
        
        return df
    except requests.exceptions.RequestException as e:
        # TODO 這裡改成toast顯示
        print(f"API請求失敗: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"資料處理失敗: {e}")
        return pd.DataFrame()

# 獲取資料
df = get_new_item_orders()

# offcanvas
product_input_fields = [
    {
        "id": "date-picker", 
        "label": "新品購買日期區間",
        "type": "date_range"
    },
    {
        "id": "customer-id", 
        "label": "客戶ID",
        "type": "dropdown"
    },
    {
        "id": "product-type",
        "label": "商品類別",
        "type": "dropdown"
    },
]
product_components = create_search_offcanvas(
    page_name="buy_new_item",
    input_fields=product_input_fields
)

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[

    # 篩選條件區
    html.Div([
        product_components["trigger_button"],
        dbc.Button("匯出", id="export-button", n_clicks=0, color="success")
    ], className="mb-3 d-flex justify-content-between align-items-center"),

    product_components["offcanvas"],

    html.Div([
        custom_table(df)
    ], id="table-container", style={"marginTop": "20px"}),
])

register_offcanvas_callback(app, "buy_new_item")

# 日期篩選條件
@app.callback(
    Output("table-container", "children", allow_duplicate=True),
    [Input("buy_new_item-date-picker", "start_date"),  # 正確的ID
     Input("buy_new_item-date-picker", "end_date"),    # 正確的ID
     Input("buy_new_item-customer-id", "value"),
     Input("buy_new_item-product-type", "value")],
    prevent_initial_call=True
)
def update_table_with_filters(start_date, end_date, customer_id, product_type):
    # 重新獲取原始資料
    filtered_df = get_new_item_orders()
    
    if filtered_df.empty:
        return custom_table(filtered_df)
    
    # 日期篩選 - 必須同時有開始和結束日期
    if start_date and end_date:
        # 轉換購買時間為datetime格式，格式: "2024-01-15 10:30"
        filtered_df['購買時間_datetime'] = pd.to_datetime(filtered_df['購買時間'], format='%Y-%m-%d %H:%M')
        
        # 設定日期範圍
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # 包含結束日期整天
        
        # 篩選日期範圍
        filtered_df = filtered_df[
            (filtered_df['購買時間_datetime'] >= start_datetime) & 
            (filtered_df['購買時間_datetime'] <= end_datetime)
        ]
        
        # 移除輔助欄位
        filtered_df = filtered_df.drop(columns=['購買時間_datetime'])
    
    # 客戶ID篩選
    if customer_id:
        filtered_df = filtered_df[filtered_df['客戶 ID'] == customer_id]
    
    # 商品類別篩選
    if product_type:
        filtered_df = filtered_df[filtered_df['購買品項'].str.contains(product_type, na=False)]
    
    return custom_table(filtered_df)