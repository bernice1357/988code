from pages.common import *
import requests
import json
from datetime import datetime, timezone, timedelta
import threading
import sys
import os

# Scheduler control will be handled via API
SCHEDULER_AVAILABLE = False

# TODO 這邊每個排程都要有cookie

# 存儲排程狀態
schedule_store = dcc.Store(id='schedule-status-store')

layout = html.Div([
    schedule_store,
    html.Div([

        # 排程項目容器
        html.Div([
            # 新品回購排程
            html.Div([
                html.Div([
                    html.H3("新品回購", style={
                        "fontSize": "1.4rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0"
                    }),
                    html.P("分析所有店家是否回購新品項", style={
                        "color": "#666",
                        "fontSize": "1.0rem",
                        "margin": "0.25rem 0 0 0"
                    })
                ], style={"flex": "1"}),
                dbc.Switch(
                    id="new-product-repurchase-switch",
                    value=False,
                    style={"transform": "scale(1.2)"}
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "2rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "border": "1px solid #e0e6ed",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "1.5rem"
            }),
            
            # 推薦排程
            html.Div([
                html.Div([
                    html.H3("產品/客戶推薦", style={
                        "fontSize": "1.4rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0"
                    }),
                    html.P("更新產品推薦列表", style={
                        "color": "#666",
                        "fontSize": "1.0rem",
                        "margin": "0.25rem 0 0 0"
                    })
                ], style={"flex": "1"}),
                dbc.Switch(
                    id="recommendation-switch",
                    value=False,
                    style={"transform": "scale(1.2)"}
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "2rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "border": "1px solid #e0e6ed",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "1.5rem"
            }),
            
            # 銷售排程
            html.Div([
                html.Div([
                    html.H3("銷售", style={
                        "fontSize": "1.4rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0"
                    }),
                    html.P("處理銷售相關自動化任務", style={
                        "color": "#666",
                        "fontSize": "1.0rem",
                        "margin": "0.25rem 0 0 0"
                    })
                ], style={"flex": "1"}),
                dbc.Switch(
                    id="sales-switch",
                    value=False,
                    style={"transform": "scale(1.2)"}
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "2rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "border": "1px solid #e0e6ed",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "1.5rem"
            }),
            
            # 補貨排程
            html.Div([
                html.Div([
                    html.H3("補貨", style={
                        "fontSize": "1.4rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0"
                    }),
                    html.P("自動監控庫存並處理補貨", style={
                        "color": "#666",
                        "fontSize": "1.0rem",
                        "margin": "0.25rem 0 0 0"
                    })
                ], style={"flex": "1"}),
                dbc.Switch(
                    id="restock-switch",
                    value=False,
                    style={"transform": "scale(1.2)"}
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "2rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "border": "1px solid #e0e6ed",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "1.5rem"
            })
            
        ], style={"width": "100%"})
        
    ], style={
        "padding": "2rem",
        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    }),
    
    # 自動刷新組件
    dcc.Interval(
        id='schedule-refresh-interval',
        interval=3600*1000,  # 1小時刷新一次（3600秒）
        n_intervals=0
    )
])

# 後端API基地址配置
# 主API服務 - 一般業務功能
API_BASE_URL = "http://127.0.0.1:8000"

# Scheduler API配置 - 隔離scheduler操作到專用端口
SCHEDULER_BASE_POST = "http://127.0.0.1:9000"  # POST操作（execute, toggle, start/stop）
SCHEDULER_BASE_GET = "http://127.0.0.1:9000"   # GET查詢（tasks, status, history）

# 排程分類對應關係
SCHEDULE_MAPPING = {
    "new-product-repurchase": "customer_management",
    "recommendation": "recommendation", 
    "sales": "sales",
    "restock": "restock"
}

# 載入排程狀態的回調
@app.callback(
    [Output('schedule-status-store', 'data'),
     Output("new-product-repurchase-switch", "value"),
     Output("recommendation-switch", "value"), 
     Output("sales-switch", "value"),
     Output("restock-switch", "value")],
    [Input('schedule-refresh-interval', 'n_intervals')],
    prevent_initial_call=False
)
def load_schedule_status(n_intervals):
    """從後端載入排程狀態"""
    try:
        response = requests.get(f'{SCHEDULER_BASE_GET}/schedule/tasks')
        if response.status_code == 200:
            data = response.json().get('data', {})
            
            # 獲取各分類的開關狀態
            customer_mgmt_enabled = data.get('customer_management', {}).get('enabled', False)
            recommendation_enabled = data.get('recommendation', {}).get('enabled', False)
            sales_enabled = data.get('sales', {}).get('enabled', False)
            restock_enabled = data.get('restock', {}).get('enabled', False)
            
            return data, customer_mgmt_enabled, recommendation_enabled, sales_enabled, restock_enabled
    except Exception as e:
        print(f"Load schedule status failed: {e}")
    
    # 返回預設值
    return {}, False, False, False, False

# 新品回購排程開關
@app.callback(
    Output("new-product-repurchase-switch", "value", allow_duplicate=True),
    Input("new-product-repurchase-switch", "value"),
    prevent_initial_call=True
)
def toggle_new_product_repurchase(value):
    return toggle_schedule_category("customer_management", value)

# 推薦排程開關
@app.callback(
    Output("recommendation-switch", "value", allow_duplicate=True),
    Input("recommendation-switch", "value"),
    prevent_initial_call=True
)
def toggle_recommendation(value):
    return toggle_schedule_category("recommendation", value)

# 銷售排程開關
@app.callback(
    Output("sales-switch", "value", allow_duplicate=True),
    Input("sales-switch", "value"),
    prevent_initial_call=True
)
def toggle_sales(value):
    return toggle_schedule_category("sales", value)

# 補貨排程開關
@app.callback(
    Output("restock-switch", "value", allow_duplicate=True),
    Input("restock-switch", "value"),
    prevent_initial_call=True
)
def toggle_restock(value):
    return toggle_schedule_category("restock", value)

def toggle_schedule_category(category, value):
    """通用的排程開關函數"""
    try:
        response = requests.post(f'{SCHEDULER_BASE_POST}/schedule/toggle', 
                               json={"category": category, "enabled": value})
        if response.status_code == 200:
            status_text = 'enabled' if value else 'disabled'
            print(f"Schedule {category} {status_text}")
            
            if value:
                print(f"Schedule {category} enabled - will run at its scheduled time")
                # Show scheduled times for user reference
                show_schedule_times(category)
            else:
                print(f"Schedule {category} disabled")
            
            return value
        else:
            print(f"Toggle schedule failed: HTTP {response.status_code}")
            return not value
    except Exception as e:
        print(f"Toggle schedule failed: {e}")
        return not value

def show_schedule_times(category):
    """Show scheduled execution times for a category"""
    schedule_times = {
        'restock': [
            'Saturday 08:00 - Prophet model training',
            'Daily 22:00 - Daily prediction',
            'Daily 02:00 - Trigger health check'
        ],
        'sales': [
            'Monthly 1st 00:30 - Sales reset',
            'Monthly 1st 01:00 - Monthly prediction',
            'Daily 06:00 - Sales change check'
        ],
        'recommendation': [
            'Sunday 02:00 - Weekly recommendation update'
        ],
        'customer_management': [
            'Daily 02:30 - Inactive customer check',
            'Daily 04:00 - Repurchase reminder'
        ]
    }
    
    if category in schedule_times:
        print(f"Scheduled times for {category}:")
        for time_desc in schedule_times[category]:
            print(f"  - {time_desc}")

