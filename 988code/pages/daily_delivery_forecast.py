from .common import *
from components.table import custom_table
import requests
from datetime import datetime, date
import pandas as pd

# 空的初始資料框架
daily_forecast_df = pd.DataFrame([])

tab_content = html.Div([
    # 控制面板
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.Label("預測日期：", style={"marginRight": "10px", "fontWeight": "normal"}),
                    dbc.Input(
                        type="date",
                        value=date.today().strftime("%Y-%m-%d"),
                        id="daily-forecast-date",
                        style={"width": "140px", "display": "inline-block", "marginRight": "20px"}
                    )
                ], style={"display": "inline-block", "marginRight": "30px"}),
                
                html.Div([
                    html.Label("商品類別：", style={"marginRight": "10px", "fontWeight": "normal"}),
                    dbc.Select(
                        options=[
                            {"label": "全部類別", "value": "全部類別"}
                        ],
                        value="全部類別",
                        id="daily-category-select",
                        style={"width": "120px", "display": "inline-block", "marginRight": "20px"}
                    )
                ], style={"display": "inline-block", "marginRight": "30px"}),
                
                dbc.Button(
                    "更新",
                    color="success",
                    id="update-daily-forecast-btn",
                    style={"backgroundColor": "#28a745", "borderColor": "#28a745"}
                )
            ], style={
                "backgroundColor": "#e8e8e8",
                "padding": "15px",
                "marginBottom": "20px",
                "display": "flex",
                "alignItems": "center",
                "flexWrap": "wrap"
            })
        ])
    ]),
    
    # 每日配送預測詳情區域
    html.Div([
        html.H5("配送名單", style={
            "backgroundColor": "#f8f9fa",
            "padding": "10px 15px",
            "margin": "0",
            "borderBottom": "1px solid #dee2e6",
            "fontWeight": "bold",
            "fontSize": "16px"
        }),
        
        # 資料表格區域
        html.Div(id="daily-forecast-table-container", children=[
            html.Div("請點擊「更新」按鈕載入資料", style={
                "textAlign": "center",
                "padding": "50px",
                "color": "#6c757d"
            })
        ])
    ], style={
        "backgroundColor": "white",
        "border": "1px solid #dee2e6",
        "borderRadius": "4px",
        "overflow": "hidden",
        "height": "65vh"
    }),
    
    # 隱藏的資料儲存區
    dcc.Store(id="daily-forecast-data", data=[]),
], style={
    "padding": "20px",
    "minHeight": "500px"
})

# 定義回調函數註冊器
def register_daily_delivery_callbacks(app):
    """註冊每日配送預測頁面的回調函數"""
    
    # 載入商品類別選項
    @app.callback(
        Output("daily-category-select", "options"),
        Input("page-loaded", "data"),
        prevent_initial_call=False
    )
    def load_category_options(page_loaded):
        try:
            response = requests.get("http://127.0.0.1:8000/get_category")
            if response.status_code == 200:
                categories = response.json()
                options = [{"label": "全部類別", "value": "全部類別"}]
                for cat in categories:
                    if cat.get("category"):
                        options.append({"label": cat["category"], "value": cat["category"]})
                return options
            else:
                return [{"label": "全部類別", "value": "全部類別"}]
        except Exception as e:
            return [{"label": "全部類別", "value": "全部類別"}]

    # 更新預測資料
    @app.callback(
        [Output("daily-forecast-data", "data"),
         Output("daily-forecast-table-container", "children")],
        [Input("update-daily-forecast-btn", "n_clicks")],
        [State("daily-forecast-date", "value"),
         State("daily-category-select", "value")],
        prevent_initial_call=True
    )
    def update_forecast_data(n_clicks, selected_date, selected_category):
        if not n_clicks:
            return [], html.Div("請點擊「更新」按鈕載入資料", style={
                "textAlign": "center",
                "padding": "50px",
                "color": "#6c757d"
            })
        
        try:
            # 構建查詢參數
            params = {}
            if selected_date:
                params['delivery_date'] = selected_date
            if selected_category and selected_category != "全部類別":
                params['category'] = selected_category
            
            # 發送 API 請求
            response = requests.get("http://127.0.0.1:8000/get_delivery_schedule_filtered", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data:
                    return [], html.Div("沒有找到符合條件的資料", style={
                        "textAlign": "center",
                        "padding": "50px",
                        "color": "#6c757d"
                    })
                
                # 轉換為 DataFrame 並重新命名欄位 - 適配現有表結構
                df = pd.DataFrame(data)
                
                # 根據現有表結構重新映射欄位
                df = df.rename(columns={
                    "customer_id": "客戶ID",
                    "customer_name": "客戶名稱", 
                    "product_name": "商品名稱",
                    "status": "狀態",
                    "quantity": "數量",
                    "delivery_date": "配送日期",
                    "category": "類別",
                    "amount": "金額",
                    "source_order_id": "來源訂單ID"
                })
                
                # 處理狀態顯示
                if '狀態' in df.columns:
                    df['狀態'] = df['狀態'].map({
                        'order': '訂單',
                        'pending': '待配送',
                        'confirmed': '已確認',
                        'delivered': '已配送',
                        'cancelled': '已取消'
                    }).fillna('訂單')
                
                # 格式化配送日期
                if '配送日期' in df.columns:
                    df['配送日期'] = pd.to_datetime(df['配送日期']).dt.strftime('%Y-%m-%d')
                
                # 格式化金額
                if '金額' in df.columns:
                    df['金額'] = df['金額'].fillna(0).astype(int)
                
                # 選擇要顯示的欄位 - 根據現有表結構調整
                display_columns = ['客戶ID', '客戶名稱', '商品名稱', '狀態', '數量', '金額', '配送日期']
                if '類別' in df.columns:
                    display_columns.append('類別')
                
                # 確保所有欄位都存在
                available_columns = [col for col in display_columns if col in df.columns]
                df_display = df[available_columns]
                
                # 創建表格
                table_component = custom_table(
                    df=df_display,
                    show_checkbox=True,
                    show_button=True,
                    button_text="編輯",
                    button_id_type="daily_forecast_button",
                    sticky_columns=['客戶ID', '客戶名稱']
                )
                
                return data, table_component
            else:
                error_msg = f"API 錯誤: {response.status_code}"
                return [], html.Div(error_msg, style={
                    "textAlign": "center",
                    "padding": "50px",
                    "color": "#dc3545"
                })
                
        except Exception as e:
            error_msg = f"載入資料時發生錯誤: {str(e)}"
            return [], html.Div(error_msg, style={
                "textAlign": "center",
                "padding": "50px",
                "color": "#dc3545"
            })

# 如果能找到 app 變數就直接註冊（向後兼容）
try:
    if 'app' in globals() and app is not None:
        register_daily_delivery_callbacks(app)
except NameError:
    pass
except Exception as e:
    pass