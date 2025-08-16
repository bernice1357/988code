from .common import *
from components.table import custom_table
import requests
from datetime import datetime, date
import pandas as pd
import calendar
import dash
from dash import ALL, callback_context, no_update
from dash.dependencies import Input, Output, State

# 空的初始資料框架
daily_forecast_df = pd.DataFrame([])

def create_calendar_widget(selected_date=None):
    """創建日曆組件"""
    if selected_date is None:
        selected_date = date.today()
    
    # 獲取當前月份的日曆資訊
    year = selected_date.year
    month = selected_date.month
    
    # 創建日曆格子
    cal = calendar.monthcalendar(year, month)
    
    # 月份導航
    month_nav = html.Div([
        dbc.Button("‹", id="daily-prev-month-btn", color="light", size="sm", style={"marginRight": "10px"}),
        html.Span(f"{year}年{month}月", style={"fontSize": "16px", "fontWeight": "bold"}),
        dbc.Button("›", id="daily-next-month-btn", color="light", size="sm", style={"marginLeft": "10px"})
    ], style={"textAlign": "center", "marginBottom": "10px"})
    
    # 星期標題
    weekday_headers = html.Div([
        html.Div("日", style={"width": "14.28%", "textAlign": "center", "fontWeight": "bold", "padding": "5px"}),
        html.Div("一", style={"width": "14.28%", "textAlign": "center", "fontWeight": "bold", "padding": "5px"}),
        html.Div("二", style={"width": "14.28%", "textAlign": "center", "fontWeight": "bold", "padding": "5px"}),
        html.Div("三", style={"width": "14.28%", "textAlign": "center", "fontWeight": "bold", "padding": "5px"}),
        html.Div("四", style={"width": "14.28%", "textAlign": "center", "fontWeight": "bold", "padding": "5px"}),
        html.Div("五", style={"width": "14.28%", "textAlign": "center", "fontWeight": "bold", "padding": "5px"}),
        html.Div("六", style={"width": "14.28%", "textAlign": "center", "fontWeight": "bold", "padding": "5px"})
    ], style={"display": "flex", "backgroundColor": "#f8f9fa", "borderBottom": "1px solid #dee2e6"})
    
    # 日曆格子
    calendar_rows = []
    for week in cal:
        week_divs = []
        for day in week:
            if day == 0:
                # 空白日期
                week_divs.append(
                    html.Div("", style={
                        "width": "14.28%", 
                        "height": "35px", 
                        "border": "1px solid #dee2e6",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center"
                    })
                )
            else:
                # 檢查是否為選中日期
                is_selected = (day == selected_date.day and 
                             month == selected_date.month and 
                             year == selected_date.year)
                
                day_style = {
                    "width": "14.28%", 
                    "height": "35px", 
                    "border": "1px solid #dee2e6",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "cursor": "pointer",
                    "backgroundColor": "#007bff" if is_selected else "white",
                    "color": "white" if is_selected else "black"
                }
                
                week_divs.append(
                    html.Div(str(day), 
                        id={"type": "daily-calendar-day", "index": f"{year}-{month:02d}-{day:02d}"},
                        style=day_style
                    )
                )
        
        calendar_rows.append(
            html.Div(week_divs, style={"display": "flex"})
        )
    
    return html.Div([
        month_nav,
        weekday_headers,
        html.Div(calendar_rows)
    ], style={
        "border": "1px solid #dee2e6",
        "backgroundColor": "white",
        "borderRadius": "4px"
    })

def create_summary_card(title, count, style_props=None):
    """創建統計卡片"""
    base_style = {
        "backgroundColor": "#f8f9fa",
        "padding": "15px",
        "borderRadius": "4px",
        "border": "1px solid #dee2e6",
        "textAlign": "center"
    }
    if style_props:
        base_style.update(style_props)
    
    return html.Div([
        html.H6(title, style={"margin": "0", "fontSize": "14px", "color": "#6c757d"}),
        html.H4(str(count), style={"margin": "5px 0 0 0", "fontSize": "24px", "fontWeight": "bold"})
    ], style=base_style)

def calculate_column_width(content_list, min_width=100, max_width=300):
    """計算欄位的最適寬度"""
    if not content_list:
        return min_width
    
    # 計算內容的最大字元長度，中文字元算2個字元
    max_content_length = 0
    for content in content_list:
        content_str = str(content)
        # 計算實際顯示寬度（中文字元較寬）
        display_length = 0
        for char in content_str:
            if ord(char) > 127:  # 中文字元
                display_length += 2
            else:  # 英文字元
                display_length += 1
        max_content_length = max(max_content_length, display_length)
    
    # 根據字元數計算像素寬度，每個英文字元約10px，加上padding
    calculated_width = max_content_length * 10 + 40  # 40px為padding和邊距
    
    # 限制在最小和最大寬度之間
    return max(min_width, min(max_width, calculated_width))

def create_default_delivery_table():
    """創建預設的配送表格"""
    return html.Div([
        # 表格標題
        html.Div([
            html.Div("客戶ID", style={
                "width": "250px", "fontWeight": "bold", "padding": "10px", 
                "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
            }),
            html.Div("客戶名稱", style={
                "width": "280px", "fontWeight": "bold", "padding": "10px", 
                "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
            }),
            html.Div("商品名稱", style={
                "flex": "1", "fontWeight": "bold", "padding": "10px", 
                "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
            }),
            html.Div("狀態", style={
                "width": "120px", "fontWeight": "bold", "padding": "10px", 
                "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
            }),
            html.Div("數量", style={
                "width": "80px", "fontWeight": "bold", "padding": "10px", 
                "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
            })
        ], style={"display": "flex"}),
        
        # 無資料時的提示
        html.Div([
            html.Div("請選擇日期查看配送資料", style={
                "textAlign": "center", 
                "padding": "40px", 
                "color": "#6c757d",
                "fontSize": "16px"
            })
        ])
    ], style={
        "border": "1px solid #dee2e6",
        "backgroundColor": "white",
        "borderRadius": "4px",
        "maxHeight": "500px",
        "overflowY": "auto"
    })

tab_content = html.Div([
    # 上半部：日曆和統計資訊
    dbc.Row([
        # 日曆區域
        dbc.Col([
            # 預測日期標題
            html.Div([
                html.Label("預測日期：", style={"fontSize": "16px", "fontWeight": "bold", "marginBottom": "10px"})
            ]),
            
            # 日曆組件
            html.Div(id="daily-calendar-container", children=[
                create_calendar_widget()
            ])
        ], width=6),
        
        # 統計資訊區域
        dbc.Col([
            # 動態統計標題
            html.Div(id="daily-statistics-title", children=[
                html.H6("統計叫貨", style={"fontSize": "16px", "fontWeight": "bold", "marginBottom": "15px"})
            ]),
            
            # 統計卡片容器
            html.Div(id="daily-statistics-container", children=[
                create_summary_card("預計叫貨客戶", "15位"),
                html.Div(style={"height": "10px"}),
                create_summary_card("總銷售量", "0箱"),
                html.Div(style={"height": "10px"}),
                
                # 主要商品預測銷量輸入框
                html.Div([
                    html.Label("主要商品預測銷量：", style={"fontSize": "14px", "marginBottom": "5px"}),
                    dbc.Input(
                        placeholder="輸入商品名稱或數量...",
                        style={"width": "100%"}
                    )
                ]),
                
                # 商品銷量詳情區域
                html.Div(id="daily-product-sales-detail", style={"marginTop": "15px"})
            ])
        ], width=6)
    ], style={"marginBottom": "30px"}),
    
    # 下半部：配送名單
    dbc.Row([
        dbc.Col([
            # 配送名單標題和篩選
            html.Div([
                html.Div([
                    html.H5("配送名單", style={
                        "margin": "0",
                        "fontSize": "18px",
                        "fontWeight": "bold"
                    })
                ], style={"flex": "1"}),
                
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button("全部", color="outline-primary", size="sm", id="daily-filter-all"),
                        dbc.Button("已確認配送", color="outline-success", size="sm", id="daily-filter-confirmed"),
                        dbc.Button("預計配送", color="outline-warning", size="sm", id="daily-filter-pending")
                    ])
                ])
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "marginBottom": "15px"
            }),
            
            # 配送名單表格
            html.Div(id="daily-delivery-list-container", children=[
                create_default_delivery_table()
            ])
        ], width=12)
    ]),
    
    # 隱藏的資料儲存區
    dcc.Store(id="daily-forecast-data", data=[]),
    dcc.Store(id="daily-selected-date", data=date.today().strftime("%Y-%m-%d"))
], style={
    "padding": "20px",
    "minHeight": "500px"
})

# 定義回調函數註冊器
def register_daily_delivery_callbacks(app):
    """註冊每日配送預測頁面的回調函數"""
    
    # 日曆日期點擊事件
    @app.callback(
        [Output("daily-selected-date", "data"),
         Output("daily-calendar-container", "children")],
        [Input({"type": "daily-calendar-day", "index": ALL}, "n_clicks")],
        [State("daily-selected-date", "data")],
        prevent_initial_call=True
    )
    def handle_calendar_click(n_clicks_list, current_date):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update
        
        # 檢查是否有日期被點擊
        if not n_clicks_list or all(clicks is None or clicks == 0 for clicks in n_clicks_list):
            return no_update, no_update
        
        # 取得觸發的組件ID
        triggered_prop_id = ctx.triggered[0]['prop_id']
        
        # 解析組件ID
        try:
            if '{"index":' in triggered_prop_id:
                # 找到 index 值
                start = triggered_prop_id.find('"index":"') + 9
                end = triggered_prop_id.find('"', start)
                clicked_date = triggered_prop_id[start:end]
                
                # 驗證日期格式
                selected_date_obj = datetime.strptime(clicked_date, "%Y-%m-%d").date()
                calendar_widget = create_calendar_widget(selected_date_obj)
                
                return clicked_date, calendar_widget
        except Exception as e:
            print(f"Error parsing date: {e}")
            
        return no_update, no_update
    
    # 月份導航
    @app.callback(
        [Output("daily-calendar-container", "children", allow_duplicate=True),
         Output("daily-selected-date", "data", allow_duplicate=True)],
        [Input("daily-prev-month-btn", "n_clicks"),
         Input("daily-next-month-btn", "n_clicks")],
        [State("daily-selected-date", "data")],
        prevent_initial_call=True
    )
    def navigate_month(prev_clicks, next_clicks, current_date):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update
        
        # 檢查觸發的按鈕
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # 防止因為重新渲染導致的誤觸發
        if triggered_id == 'daily-prev-month-btn':
            if not prev_clicks or prev_clicks == 0:
                return no_update, no_update
        elif triggered_id == 'daily-next-month-btn':
            if not next_clicks or next_clicks == 0:
                return no_update, no_update
        else:
            return no_update, no_update
        
        try:
            current_date_obj = datetime.strptime(current_date, "%Y-%m-%d").date()
        except:
            current_date_obj = date.today()
        
        if triggered_id == 'daily-prev-month-btn':
            # 上一個月
            if current_date_obj.month == 1:
                new_date = current_date_obj.replace(year=current_date_obj.year - 1, month=12, day=1)
            else:
                new_date = current_date_obj.replace(month=current_date_obj.month - 1, day=1)
        elif triggered_id == 'daily-next-month-btn':
            # 下一個月
            if current_date_obj.month == 12:
                new_date = current_date_obj.replace(year=current_date_obj.year + 1, month=1, day=1)
            else:
                new_date = current_date_obj.replace(month=current_date_obj.month + 1, day=1)
        else:
            return no_update, no_update
        
        calendar_widget = create_calendar_widget(new_date)
        return calendar_widget, new_date.strftime("%Y-%m-%d")
    
    # 根據選中日期更新統計資訊
    @app.callback(
        [Output("daily-statistics-title", "children"),
         Output("daily-statistics-container", "children")],
        Input("daily-selected-date", "data"),
        prevent_initial_call=False
    )
    def update_statistics(selected_date):
        try:
            # 解析選中的日期
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            month = selected_date_obj.month
            day = selected_date_obj.day
            date_str = f"{month}月{day}號"
        except Exception as e:
            print(f"Date parsing error: {e}")
            selected_date_obj = date.today()
            month = selected_date_obj.month
            day = selected_date_obj.day
            date_str = f"{month}月{day}號"
        
        # 動態標題
        title = html.H6(f"{date_str}統計叫貨", style={"fontSize": "16px", "fontWeight": "bold", "marginBottom": "15px"})
        
        # 初始化預設值
        total_customers = 0
        total_quantity = 0
        product_details = []
        
        try:
            # 獲取該日期的統計資料
            params = {'delivery_date': selected_date}
            response = requests.get("http://127.0.0.1:8000/get_delivery_schedule_filtered", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # 計算統計數據
                total_customers = len(set(item.get('customer_id', '') for item in data if item.get('customer_id')))
                total_quantity = sum(int(item.get('quantity', 0)) for item in data if item.get('quantity') and str(item.get('quantity')).isdigit())
                
                # 按商品統計銷量
                product_stats = {}
                for item in data:
                    product_name = item.get('product_name', '未知商品')
                    try:
                        quantity = int(item.get('quantity', 0)) if item.get('quantity') else 0
                    except (ValueError, TypeError):
                        quantity = 0
                    
                    if product_name and quantity > 0:
                        if product_name in product_stats:
                            product_stats[product_name] += quantity
                        else:
                            product_stats[product_name] = quantity
                
                # 排序商品統計（按銷量降序）
                sorted_products = sorted(product_stats.items(), key=lambda x: x[1], reverse=True)
                
                # 創建商品銷量詳情
                if sorted_products:
                    product_details.append(
                        html.H6("商品銷量詳情：", style={"fontSize": "14px", "fontWeight": "bold", "marginBottom": "8px"})
                    )
                    for product_name, quantity in sorted_products[:5]:  # 只顯示前5名
                        display_name = product_name[:20] + "..." if len(product_name) > 20 else product_name
                        product_details.append(
                            html.Div([
                                html.Span(display_name, style={"fontSize": "12px", "color": "#666"}),
                                html.Span(f": {quantity}箱", style={"fontSize": "12px", "fontWeight": "bold", "float": "right"})
                            ], style={"marginBottom": "4px", "overflow": "hidden"})
                        )
                
        except Exception as e:
            print(f"API call error: {e}")
            # 如果是今天的日期且API出錯，使用預設值
            today_str = date.today().strftime("%Y-%m-%d")
            if selected_date == today_str:
                total_customers = 15
        
        # 創建統計卡片和詳情
        statistics_content = [
            create_summary_card("預計叫貨客戶", f"{total_customers}位"),
            html.Div(style={"height": "10px"}),
            create_summary_card("總銷售量", f"{total_quantity}箱"),
            html.Div(style={"height": "10px"}),
            
            # 主要商品預測銷量輸入框
            html.Div([
                html.Label("主要商品預測銷量：", style={"fontSize": "14px", "marginBottom": "5px"}),
                dbc.Input(
                    placeholder="輸入商品名稱或數量...",
                    style={"width": "100%"}
                )
            ]),
            
            # 商品銷量詳情
            html.Div(product_details, style={"marginTop": "15px"})
        ]
        
        return title, statistics_content
    
    # 載入配送資料（根據選中的日期和篩選條件）
    @app.callback(
        Output("daily-delivery-list-container", "children"),
        [Input("daily-selected-date", "data"),
         Input("daily-filter-all", "n_clicks"),
         Input("daily-filter-confirmed", "n_clicks"),
         Input("daily-filter-pending", "n_clicks")],
        prevent_initial_call=True
    )
    def update_delivery_list(selected_date, all_clicks, confirmed_clicks, pending_clicks):
        ctx = callback_context
        filter_type = "all"
        
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id == "daily-filter-confirmed":
                filter_type = "confirmed"
            elif button_id == "daily-filter-pending":
                filter_type = "pending"
        
        try:
            # 根據 selected_date 從 API 獲取資料
            params = {'delivery_date': selected_date}
            response = requests.get("http://127.0.0.1:8000/get_delivery_schedule_filtered", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # 根據篩選類型過濾資料
                if filter_type == "confirmed":
                    data = [item for item in data if item.get('status') == 'confirmed']
                elif filter_type == "pending":
                    data = [item for item in data if item.get('status') == 'pending']
                
                # 計算自動調整的欄位寬度
                customer_ids = [item.get('customer_id', '') for item in data]
                customer_names = [item.get('customer_name', '') for item in data]
                
                customer_id_width = calculate_column_width(customer_ids, min_width=200, max_width=350)
                customer_name_width = calculate_column_width(customer_names, min_width=220, max_width=400)
                
                # 如果沒有資料，使用預設寬度
                if not data:
                    customer_id_width = 250
                    customer_name_width = 280
                
                # 初始化表格行列表
                table_rows = []
                
                # 表格標題
                table_rows.append(
                    html.Div([
                        html.Div("客戶ID", style={
                            "width": f"{customer_id_width}px", "fontWeight": "bold", "padding": "10px", 
                            "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
                        }),
                        html.Div("客戶名稱", style={
                            "width": f"{customer_name_width}px", "fontWeight": "bold", "padding": "10px", 
                            "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
                        }),
                        html.Div("商品名稱", style={
                            "flex": "1", "fontWeight": "bold", "padding": "10px", 
                            "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
                        }),
                        html.Div("狀態", style={
                            "width": "120px", "fontWeight": "bold", "padding": "10px", 
                            "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
                        }),
                        html.Div("數量", style={
                            "width": "80px", "fontWeight": "bold", "padding": "10px", 
                            "backgroundColor": "#e9ecef", "border": "1px solid #dee2e6", "textAlign": "center"
                        })
                    ], style={"display": "flex"})
                )
                
                # 資料行
                if data:  # 只有當有資料時才生成資料行
                    for item in data:
                        status_text = "已確認配送" if item.get('status') == 'confirmed' else "預計配送"
                        status_bg = "#d4edda" if item.get('status') == 'confirmed' else "#fff3cd"
                        status_color = "#155724" if item.get('status') == 'confirmed' else "#856404"
                        
                        table_rows.append(
                            html.Div([
                                html.Div(item.get('customer_id', ''), style={
                                    "width": f"{customer_id_width}px", "padding": "10px", "border": "1px solid #dee2e6",
                                    "textAlign": "center", "color": "#007bff"
                                }),
                                html.Div(item.get('customer_name', ''), style={
                                    "width": f"{customer_name_width}px", "padding": "10px", "border": "1px solid #dee2e6",
                                    "textAlign": "center", "color": "#007bff"
                                }),
                                html.Div(item.get('product_name', ''), style={
                                    "flex": "1", "padding": "10px", "border": "1px solid #dee2e6",
                                    "textAlign": "left", "color": "#007bff"
                                }),
                                html.Div(status_text, style={
                                    "width": "120px", "padding": "10px", "border": "1px solid #dee2e6",
                                    "textAlign": "center", "backgroundColor": status_bg, "color": status_color
                                }),
                                html.Div(str(item.get('quantity', '')), style={
                                    "width": "80px", "padding": "10px", "border": "1px solid #dee2e6",
                                    "textAlign": "center", "color": "#007bff"
                                })
                            ], style={"display": "flex"})
                        )
                else:
                    # 如果沒有資料，在表格標題後顯示提示訊息
                    table_rows.append(
                        html.Div([
                            html.Div("暫無配送資料", style={
                                "textAlign": "center", 
                                "padding": "40px", 
                                "color": "#6c757d",
                                "fontSize": "16px",
                                "width": "100%",
                                "border": "1px solid #dee2e6",
                                "borderTop": "none"
                            })
                        ])
                    )
                
                return html.Div(table_rows, style={
                    "border": "1px solid #dee2e6",
                    "backgroundColor": "white",
                    "borderRadius": "4px",
                    "maxHeight": "500px",
                    "overflowY": "auto"
                })
            else:
                # API 返回錯誤狀態碼
                return create_default_delivery_table()
            
        except Exception as e:
            print(f"Error loading delivery data: {e}")
            # 發生異常時返回預設表格
            return create_default_delivery_table()
        
        # 如果沒有進入 try 塊，返回預設表格
        return create_default_delivery_table()

# 如果能找到 app 變數就直接註冊（向後兼容）
try:
    if 'app' in globals() and app is not None:
        register_daily_delivery_callbacks(app)
except NameError:
    pass
except Exception as e:
    pass