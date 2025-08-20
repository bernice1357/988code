from .common import *
from callbacks.export_callback import add_download_component
import datetime
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from components.table import custom_table
import urllib.parse
import time
import os

df=pd.DataFrame([])

# 專門為潛在客戶頁面定制的表格函數，可以自定義欄位寬度
def custom_table_for_potential_customers(df, show_button=False, sticky_columns=None, table_height='50vh'):
    from components.table import custom_table
    from dash import html
    
    if sticky_columns is None:
        sticky_columns = []
    
    # 自定義寬度設定
    custom_widths = {
        "客戶名稱": 250,  # 變寬
        "客戶ID": 80      # 變窄
    }
    
    # 暫時修改 calculate_column_width 函數
    original_calculate = None
    try:
        # 動態修改 custom_table 內的計算邏輯
        def custom_calculate_column_width(col):
            if col in custom_widths:
                return custom_widths[col]
            # 其他欄位使用原本的計算方式
            header_width = len(str(col)) * 12 + 24
            max_content_width = 0
            for value in df[col]:
                content_width = len(str(value)) * 10 + 24
                max_content_width = max(max_content_width, content_width)
            calculated_width = max(header_width, max_content_width) + 20
            return max(100, min(300, calculated_width))
        
        # 調用原本的 custom_table 但使用自定義寬度
        import components.table as table_module
        original_calculate = table_module.custom_table.__code__
        
        # 直接返回修改過的表格
        return create_custom_table_with_widths(df, show_button, sticky_columns, table_height, custom_widths)
        
    except Exception as e:
        # 如果出錯，使用原本的 custom_table
        return custom_table(df, show_button=show_button, sticky_columns=sticky_columns, table_height=table_height)

def create_custom_table_with_widths(df, show_button, sticky_columns, table_height, custom_widths):
    from dash import html
    
    # 計算欄位寬度
    def calculate_column_width(col):
        if col in custom_widths:
            return custom_widths[col]
        # 其他欄位使用原本的計算方式
        header_width = len(str(col)) * 12 + 24
        max_content_width = 0
        for value in df[col]:
            content_width = len(str(value)) * 10 + 24
            max_content_width = max(max_content_width, content_width)
        calculated_width = max(header_width, max_content_width) + 20
        return max(100, min(300, calculated_width))
    
    # 計算所有浮空欄位的寬度
    sticky_widths = {}
    for col in sticky_columns:
        sticky_widths[col] = calculate_column_width(col)
    
    rows = []
    for i, row in df.iterrows():
        row_cells = []
        sticky_col_data = []
        normal_col_data = []
        
        for col in ([col for col in df.columns if col in sticky_columns] + 
                   [col for col in df.columns if col not in sticky_columns]) if sticky_columns else df.columns:
            cell_style = {
                'padding': '8px 12px',
                'textAlign': 'center',
                'border': '1px solid #ccc',
                'fontSize': '16px',
                'height': '50px',
                'whiteSpace': 'nowrap',
                'backgroundColor': 'white'
            }
            
            if col in sticky_columns:
                sticky_index = sticky_columns.index(col)
                left_offset = sum(sticky_widths[sticky_columns[j]] for j in range(sticky_index))
                
                cell_style.update({
                    'position': 'sticky',
                    'left': f'{left_offset}px',
                    'zIndex': 2,
                    'backgroundColor': "#edf7ff",
                    'width': f'{sticky_widths[col]}px',
                    'minWidth': f'{sticky_widths[col]}px',
                    'maxWidth': f'{sticky_widths[col]}px'
                })
                
                sticky_col_data.append(html.Td(row[col], style=cell_style))
            else:
                normal_col_data.append(html.Td(row[col], style=cell_style))
        
        row_cells.extend(sticky_col_data + normal_col_data)
        rows.append(html.Tr(row_cells, style={'backgroundColor': 'white'}))

    table = html.Table([
        html.Thead([
            html.Tr([
                html.Th(col, style={
                    "position": "sticky",
                    "top": "0px",
                    "left": f'{sum(sticky_widths[sticky_columns[j]] for j in range(sticky_columns.index(col)))}px' if col in sticky_columns else 'auto',
                    "zIndex": 3 if col in sticky_columns else 1,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc',
                    'whiteSpace': 'nowrap',
                    'width': f'{sticky_widths[col]}px' if col in sticky_columns else 'auto',
                    'minWidth': f'{sticky_widths[col]}px' if col in sticky_columns else 'auto',
                    'maxWidth': f'{sticky_widths[col]}px' if col in sticky_columns else 'auto',
                }) for col in df.columns
            ])
        ]),
        html.Tbody(rows)
    ], style={"width": "100%", "borderCollapse": "collapse", 'border': '1px solid #ccc'})

    return html.Div([table], style={
        'overflowY': 'auto',
        'overflowX': 'auto',
        'maxHeight': table_height,
        'minHeight': table_height,
        'display': 'block',
        'position': 'relative',
    })

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[

    dcc.Store(id='potential-customers-data-store'),
    add_download_component("potential_customers"),  # 加入下載元件
    dcc.Store(id='progress-task-store'),  # 儲存當前任務ID
    
    # 進度更新間隔器
    dcc.Interval(
        id='progress-interval',
        interval=1000,  # 每秒更新一次
        n_intervals=0,
        disabled=True  # 初始為禁用狀態
    ),

    html.Div([
        html.Div([
            html.Span("搜尋品項名稱", style={"marginRight": "10px"}),
            dcc.Dropdown(
                id="search-dropdown",
                options=[],
                placeholder="請選擇品項",
                style={"width": "300px", "marginRight": "10px"}
            ),
            dbc.Button("送出", id="submit-button", color="primary", className="me-2"),
            html.Div([
                dbc.Button("匯出列表資料", id="potential_customers-export-button", n_clicks=0, color="primary", outline=True)
            ], style={"marginLeft": "auto"})
        ], className="d-flex align-items-center")
    ], className="mb-3"),

    html.Div(style={"borderBottom": "1px solid #dee2e6"}),

    html.Div([
        html.Div(id="potential-customers-table-container"),
    ], style={"marginTop": "10px"}),
    
    # 進度顯示 Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("潛在客戶分析進度")),
        dbc.ModalBody([
            html.Div([
                html.H6(id="progress-current-step", children="初始化中..."),
                dbc.Progress(
                    id="progress-bar",
                    value=0,
                    striped=True,
                    animated=True,
                    style={"height": "25px", "marginBottom": "15px"}
                ),
                html.Div([
                    html.H6("分析進度訊息：", style={"marginBottom": "10px"}),
                    html.Div(
                        id="progress-messages",
                        style={
                            "height": "200px",
                            "overflowY": "scroll",
                            "border": "1px solid #ddd",
                            "padding": "10px",
                            "backgroundColor": "#f8f9fa",
                            "fontFamily": "monospace",
                            "fontSize": "12px"
                        }
                    )
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("關閉", id="progress-close-button", className="ms-auto", disabled=False)
        ])
    ], 
    id="progress-modal", 
    is_open=False, 
    backdrop="static",  # 防止點擊背景關閉
    keyboard=False,     # 防止按ESC關閉
    size="lg",
    style={"width": "800px", "maxWidth": "90vw"}
    ),

])

@app.callback(
    [Output('search-dropdown', 'options'),
     Output('search-dropdown', 'placeholder')],
    Input('search-dropdown', 'id')
)
def update_product_dropdown_options(dropdown_id):
    try:
        response = requests.get("http://127.0.0.1:8000/get_name_zh")
        if response.status_code == 200:
            data = response.json()
            options = [{"label": item["name_zh"], "value": item["name_zh"]} for item in data]
            return options, "選擇品項"
        else:
            return [], "請選擇"
    except Exception as e:
        print(f"[ERROR] update_product_dropdown_options: {e}")
        return [], "請選擇"

# 啟動分析並顯示進度Modal的回調
@app.callback(
    [Output("progress-modal", "is_open"),
     Output("progress-interval", "disabled"),
     Output("progress-task-store", "data")],
    [Input("submit-button", "n_clicks")],
    [State("search-dropdown", "value")],
    prevent_initial_call=True
)
def start_analysis_with_progress(submit_btn, dropdown_value):
    if not dropdown_value:
        return False, True, None
    
    print(f"開始分析產品: {dropdown_value}")
    
    # 啟動分析API (在背景執行)
    import threading
    import urllib.parse
    
    def run_analysis():
        try:
            # 清除舊的進度檔案
            progress_file_path = "C:/Users/user/Desktop/988/988code/988code/potential_customer_finder/progress.json"
            if os.path.exists(progress_file_path):
                os.remove(progress_file_path)
            
            encoded_product_name = urllib.parse.quote(dropdown_value)
            analysis_url = f"http://127.0.0.1:8000/get_potential_customers_analysis/{encoded_product_name}"
            print(f"呼叫分析API: {analysis_url}")
            response = requests.get(analysis_url)
            print(f"分析API調用結果: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"分析完成，任務ID: {result.get('task_id')}")
            else:
                print(f"API調用失敗: {response.text}")
        except Exception as e:
            print(f"分析API調用錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    # 在背景線程中啟動分析
    analysis_thread = threading.Thread(target=run_analysis)
    analysis_thread.daemon = True
    analysis_thread.start()
    
    # 啟動進度視窗並開始監控
    # 不需要生成task_id，讓backend決定
    return True, False, {"product_name": dropdown_value, "analysis_started": True, "start_time": time.time()}

# 分析完成後處理結果的回調
@app.callback(
    [Output("potential-customers-table-container", "children"),
     Output("potential-customers-data-store", "data"),
     Output("progress-close-button", "disabled")],
    [Input("progress-interval", "n_intervals")],
    [State("progress-task-store", "data"),
     State("progress-modal", "is_open")],
    prevent_initial_call=True
)
def load_potential_customers_data(n_intervals, task_data, modal_open):
    if not task_data or not modal_open:
        return dash.no_update, dash.no_update, dash.no_update
    
    # 檢查是否有進度信息
    try:
        progress_response = requests.get("http://127.0.0.1:8000/get_current_analysis_progress")
        if progress_response.status_code == 200:
            progress_info = progress_response.json()
            
            # 如果分析完成，從詳細結果API獲取完整數據
            if progress_info.get("status") == "completed":
                product_name = task_data["product_name"]
                
                # 調用詳細結果API來獲取完整的客戶資料
                try:
                    # 使用查詢參數，避免URL路徑編碼問題
                    details_url = "http://127.0.0.1:8000/get_potential_customers_details"
                    details_response = requests.get(details_url, params={"product_name": product_name})
                    
                    if details_response.status_code == 200:
                        analysis_result = details_response.json()
                    else:
                        # 如果詳細API失敗，使用進度信息中的基本結果
                        analysis_result = progress_info.get("analysis_result")
                except Exception as e:
                    print(f"獲取詳細結果失敗: {e}")
                    # 如果詳細API失敗，使用進度信息中的基本結果
                    analysis_result = progress_info.get("analysis_result")
                
                if analysis_result:
                    
                    # 檢查各種客戶資料
                    can_process_customers = analysis_result.get('can_process_customers', [])
                    purchased_customers = analysis_result.get('purchased_customers', [])
                    potential_customers = analysis_result.get('potential_customers', [])
                    cannot_process_customers = analysis_result.get('cannot_process_customers', [])
                    classification_stats = analysis_result.get('classification_stats', {})
                    
                    # 建立綜合統計資訊
                    stats_component = html.Div([
                        html.H5(f"潛在客戶分析結果 - {product_name}"),
                        html.Div([
                            html.Div([
                                html.H6("統計摘要", style={"marginBottom": "10px"}),
                                html.P([
                                    f"總搜尋結果: {analysis_result.get('results_count', 0)} 個 | ",
                                    f"曾詢問客戶: {classification_stats.get('can_process_count', 0)} 個 | ",
                                    f"已購買客戶: {classification_stats.get('purchased_count', 0)} 個 | ",
                                    f"潛在需求客戶: {classification_stats.get('potential_count', 0)} 個 | ",
                                    f"無法處理: {classification_stats.get('cannot_process_count', 0)} 個"
                                ])
                            ], style={"marginBottom": "15px"}),
                        ])
                    ], style={"marginBottom": "20px", "padding": "15px", "backgroundColor": "#f8f9fa", "borderRadius": "5px"})
                    
                    # 組合顯示所有客戶類型 (按優先級排序：潛在需求 > 曾詢問 > 已購買 > 無法處理)
                    combined_data = []
                    
                    # 按優先級添加所有有數據的客戶類型
                    if potential_customers and len(potential_customers) > 0:
                        combined_data.extend(potential_customers)
                    if can_process_customers and len(can_process_customers) > 0:
                        combined_data.extend(can_process_customers)
                    if purchased_customers and len(purchased_customers) > 0:
                        combined_data.extend(purchased_customers)
                    if cannot_process_customers and len(cannot_process_customers) > 0:
                        combined_data.extend(cannot_process_customers)
                    
                    if combined_data:
                        # 已移除標題顯示，不需要生成title_parts和table_title
                        # 建立客戶資料的 DataFrame，並優化欄位顯示（integrated_customers格式）
                        df_data = []
                        for item in combined_data:
                            # 處理客戶名稱格式化 - 移除日期前綴
                            raw_customer_name = item.get('customer_name', '')
                            # 分割並移除前面的日期部分（格式：20240423_20250710_屏東市_虹美廚房）
                            name_parts = raw_customer_name.split('_')
                            if len(name_parts) >= 4:
                                # 移除前兩個日期部分，保留地區和店名
                                formatted_customer_name = '_'.join(name_parts[2:])
                            else:
                                formatted_customer_name = raw_customer_name
                            
                            # 處理對話內容，添加懸停提示和換行支援
                            # 優先使用 conversation_content（integrated_customers.json 標準欄位），備用 message_content
                            full_content = item.get('conversation_content', '') or item.get('message_content', '')
                            
                            # 將 \n 轉換為實際換行顯示
                            if '\n' in full_content:
                                # 如果有換行符，將內容分行顯示
                                content_lines = full_content.split('\n')
                                content_display = html.Div([
                                    html.Div(line) for line in content_lines
                                ], style={
                                    'whiteSpace': 'pre-wrap',  # 保持換行和空格
                                    'wordBreak': 'break-word'  # 長詞換行
                                })
                            else:
                                # 沒有換行符的情況，使用原本邏輯但增加長度
                                short_content = full_content[:200] + "..." if len(full_content) > 200 else full_content
                                content_display = html.Span(
                                    short_content,
                                    title=full_content,  # 原生HTML title屬性提供懸停提示
                                    style={
                                        'cursor': 'help' if len(full_content) > 200 else 'default',
                                        'borderBottom': '1px dotted #6c757d' if len(full_content) > 200 else 'none',
                                        'whiteSpace': 'pre-wrap',
                                        'wordBreak': 'break-word'
                                    }
                                )
                            
                            processed_item = {
                                "客戶名稱": formatted_customer_name,
                                "客戶ID": item.get('customer_id', ''),
                                "客戶類型": item.get('customer_type', ''),
                                "對話內容": content_display,
                                "最後購買/詢問日期": item.get('last_activity_date', '').split(' ')[0] if item.get('last_activity_date') else '',
                                "詢問次數": str(item.get('inquiry_count', 0))
                            }
                            df_data.append(processed_item)
                        
                        df = pd.DataFrame(df_data)
                        
                        # 使用 custom_table 顯示結果，設定sticky欄位
                        table_component = html.Div([
                            stats_component,
                            # 移除詳細標題：html.H6(table_title, style={"marginBottom": "15px", "color": "#495057", "fontWeight": "600"}),
                            html.Div([  # 添加防滾動穿透的容器
                                custom_table_for_potential_customers(
                                    df, 
                                    show_button=False,  # 移除操作按鈕
                                    sticky_columns=["客戶名稱"],  # 只固定客戶名稱欄位，避免重疊
                                    table_height='50vh'  # 固定表格高度
                                )
                            ], style={
                                "overscrollBehavior": "contain"  # 防止滾動穿透
                            })
                        ])
                        
                        return table_component, analysis_result, False  # 啟用關閉按鈕
                    else:
                        # 沒有任何客戶資料，只顯示統計資訊
                        return html.Div([
                            stats_component,
                            html.Div([
                                html.H6("分析完成"),
                                html.P("未找到具體的客戶資料，但已完成分析統計。"),
                                html.P("請檢查上方的統計摘要了解詳細情況。")
                            ], style={"textAlign": "center", "padding": "20px"})
                        ]), analysis_result, False  # 啟用關閉按鈕
                else:
                    return html.Div(f"API 錯誤: {response.status_code}", style={"color": "red", "padding": "20px", "textAlign": "center"}), [], False
    
    except Exception as e:
        return html.Div(f"載入資料時發生錯誤: {str(e)}", style={"color": "red", "padding": "20px", "textAlign": "center"}), [], False
    
    # 如果分析還在進行中，不更新結果
    return dash.no_update, dash.no_update, dash.no_update

# 更新進度的回調
@app.callback(
    [Output("progress-current-step", "children"),
     Output("progress-bar", "value"),
     Output("progress-messages", "children"),
     Output("progress-close-button", "disabled", allow_duplicate=True),
     Output("progress-modal", "is_open", allow_duplicate=True),
     Output("progress-interval", "disabled", allow_duplicate=True)],
    [Input("progress-interval", "n_intervals")],
    [State("progress-modal", "is_open"),
     State("progress-current-step", "children")],
    prevent_initial_call=True
)
def update_progress(n_intervals, modal_open, current_step_state):
    if not modal_open:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        response = requests.get("http://127.0.0.1:8000/get_current_analysis_progress")
        if response.status_code == 200:
            progress_info = response.json()
            
            current_step = progress_info.get("current_step", "初始化中...")
            percentage = progress_info.get("percentage", 0)
            task_status = progress_info.get("status", "")
            messages = progress_info.get("messages", [])
            
            # 智能狀態管理 - 避免不必要的重置
            if task_status == "no_task":
                # 如果之前已經完成分析，保持完成狀態
                if current_step_state == "分析完成":
                    return "分析完成", 100, [html.Div("分析已完成，您可以關閉此視窗")], False, dash.no_update, dash.no_update
                # 如果之前已經在分析中（不是初始狀態），保持當前狀態，避免跳回初始狀態
                elif current_step_state and current_step_state not in ["等待分析開始...", "初始化中..."]:
                    # 保持上一次的狀態，不重置
                    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                else:
                    # 真正的等待開始狀態（初次載入）
                    return "等待分析開始...", 0, [html.Div("正在啟動分析...")], True, dash.no_update, dash.no_update
            
            # 如果任務已完成，顯示完成狀態並自動關閉Modal
            if task_status == "completed" or percentage >= 100:
                current_step = "分析完成"
                percentage = 100
                close_button_disabled = False
                
                # 檢查是否首次完成（從非完成狀態轉為完成）
                if current_step_state != "分析完成":
                    # 首次顯示完成狀態，準備在下一次間隔後關閉
                    return current_step, percentage, [html.Div("分析已完成，視窗即將自動關閉...")], close_button_disabled, dash.no_update, dash.no_update
                else:
                    # 已經在完成狀態，現在自動關閉Modal
                    return current_step, percentage, [html.Div("分析完成")], close_button_disabled, False, True  # 關閉modal並禁用interval
            elif task_status == "running":
                # 任務正在執行中，禁用關閉按鈕
                close_button_disabled = True
            else:
                # 其他狀態，根據百分比決定
                close_button_disabled = percentage < 100
            
            # 格式化消息顯示
            message_elements = []
            for msg in messages[-10:]:  # 只顯示最近10條消息
                time_str = msg.get("time", "")
                text = msg.get("message", "")
                message_elements.append(html.Div(f"[{time_str}] {text}"))
            
            return current_step, percentage, message_elements, close_button_disabled, dash.no_update, dash.no_update
        else:
            return "無法獲取進度信息", 0, [html.Div("連接錯誤")], False, dash.no_update, dash.no_update
    
    except Exception as e:
        return f"錯誤: {str(e)}", 0, [html.Div(f"錯誤: {str(e)}")], False, dash.no_update, dash.no_update

# 關閉進度Modal的回調
@app.callback(
    [Output("progress-modal", "is_open", allow_duplicate=True),
     Output("progress-interval", "disabled", allow_duplicate=True)],
    [Input("progress-close-button", "n_clicks")],
    prevent_initial_call=True
)
def close_progress_modal(close_clicks):
    if close_clicks:
        return False, True
    return dash.no_update, dash.no_update

register_offcanvas_callback(app, "potential_customers")

# 潛在客戶CSV匯出功能
@app.callback(
    Output("potential_customers-download", "data"),
    Input("potential_customers-export-button", "n_clicks"),
    State("potential-customers-data-store", "data"),
    prevent_initial_call=True
)
def export_potential_customers_csv(n_clicks, stored_data):
    """匯出潛在客戶資料為CSV格式"""
    if n_clicks and stored_data:
        try:
            print(f"匯出按鈕被點擊，stored_data keys: {stored_data.keys() if stored_data else 'None'}")
            
            # 從儲存的資料中提取不同類型的客戶
            combined_data = []
            
            # 收集所有類型的客戶資料
            for key in ['potential_customers', 'can_process_customers', 'purchased_customers', 'cannot_process_customers']:
                customers = stored_data.get(key, [])
                if customers:
                    print(f"找到 {key}: {len(customers)} 筆")
                    combined_data.extend(customers)
            
            if not combined_data:
                print("沒有找到任何客戶資料")
                return None
            
            print(f"總共收集到 {len(combined_data)} 筆客戶資料")
            
            # 轉換為 DataFrame 並處理資料格式
            processed_data = []
            for item in combined_data:
                # 處理客戶名稱格式化 - 移除日期前綴
                raw_customer_name = item.get('customer_name', '')
                name_parts = raw_customer_name.split('_')
                if len(name_parts) >= 4:
                    formatted_customer_name = '_'.join(name_parts[2:])
                else:
                    formatted_customer_name = raw_customer_name
                
                # 處理對話內容（完整內容，不截斷）
                full_content = item.get('conversation_content', '') or item.get('message_content', '')
                
                processed_record = {
                    '客戶名稱': formatted_customer_name,
                    '客戶ID': item.get('customer_id', ''),
                    '客戶類型': item.get('customer_type', ''),
                    '對話內容': full_content,  # 完整內容
                    '詢問日期': item.get('inquiry_date', ''),
                    '詢問次數': item.get('inquiry_count', '')
                }
                processed_data.append(processed_record)
            
            # 轉換為 DataFrame
            df = pd.DataFrame(processed_data)
            
            if not df.empty:
                # 生成帶時間戳的檔案名稱
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"潛在客戶列表_{timestamp}.csv"
                
                print(f"準備匯出 {len(df)} 筆記錄到 {filename}")
                
                # 匯出為 CSV（使用BIG-5編碼以支援Windows Excel正確顯示中文）
                return dcc.send_data_frame(
                    df.to_csv, 
                    filename, 
                    index=False,
                    encoding='big5'  # BIG-5 encoding for Windows Excel compatibility
                )
        
        except Exception as e:
            print(f"匯出CSV時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    return None