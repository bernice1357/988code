from .common import *
from dash import ALL, callback_context

def get_sales_change_data():
    """從API獲取滯銷品資料"""
    try:
        response = requests.get('http://127.0.0.1:8000/get_sales_change_data')
        response.raise_for_status()
        data = response.json()
        
        # 先檢查資料是否為空
        if not data:
            print("API 返回空資料")
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # 重新命名欄位和格式化資料
        if not df.empty:
            # 檢查必要欄位是否存在
            required_columns = ['product_name', 'last_month_sales', 'current_month_sales', 
                                  'change_percentage', 'stock_quantity', 'status']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"缺少必要欄位: {missing_columns}")
                return pd.DataFrame()
            
            df = df.rename(columns={
                'product_name': '商品名稱',
                'last_month_sales': '上月銷量',
                'current_month_sales': '本月銷量',
                'change_percentage': '變化比例原始值',
                'stock_quantity': '目前庫存',
                'recommended_customer_1': '推薦客戶1',
                'recommended_customer_1_phone': '推薦客戶1電話',
                'recommended_customer_2': '推薦客戶2',
                'recommended_customer_2_phone': '推薦客戶2電話',
                'recommended_customer_3': '推薦客戶3',
                'recommended_customer_3_phone': '推薦客戶3電話',
                'status': '狀態原始值'
            })
            
            # 格式化變化比例
            df['變化比例'] = df['變化比例原始值'].apply(
                lambda x: f"{abs(x):.1f}%" if pd.notna(x) and x != 0 else "0%"
            )
            
            # 轉換處理狀態為中文
            df['狀態'] = df['狀態原始值'].map({True: '已處理', False: '未處理', 1: '已處理', 0: '未處理'})
            
            # 處理推薦客戶欄位 - 確保這些欄位存在
            customer_fields = [
                ('推薦客戶1', '推薦客戶1電話'),
                ('推薦客戶2', '推薦客戶2電話'), 
                ('推薦客戶3', '推薦客戶3電話')
            ]
            
            for customer_col, phone_col in customer_fields:
                if customer_col not in df.columns:
                    df[customer_col] = '未設定'
                if phone_col not in df.columns:
                    df[phone_col] = '未設定'
                    
                # 處理空值和 None
                df[customer_col] = df[customer_col].fillna('未設定').replace('', '未設定')
                df[phone_col] = df[phone_col].fillna('未設定').replace('', '未設定')
            
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"API請求失敗: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"資料處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

tab_content = html.Div([
    dcc.Store(id="page-loaded-sales", data=True),
    dcc.Store(id="sales-change-data", data=[]),
    dcc.Store(id="filtered-sales-data", data=[]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("摘要分析"),
                dbc.CardBody([
                    html.Div(id="sales-stats-container", children=[
                        html.H5("滯銷品品數: 0"),
                        html.H5("已處理: 0"),
                        html.H5("未處理: 0")
                    ])
                ])
            ], color="light", style={"height": "100%"})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("設定滯銷品變化比例"),
                dbc.CardBody([
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText("銷量變化比例 >="),
                            dbc.Input(type="number", placeholder="輸入比例", id="sales-threshold-input", min=1, value=50),
                            dbc.InputGroupText("%")
                        ], style={"flex": "1", "marginRight": "10px"}),
                        dbc.Button("儲存", color="primary", id="save-threshold-btn")
                    ], style={"display": "flex", "alignItems": "center"})
                ])
            ], color="light", style={"height": "100%"})
        ], width=6)
    ], className="h-100"),
    
    html.Div([
    # 左側：篩選功能
    html.Div([
        html.Div([
            dbc.Label("銷量變化類型：", style={"marginRight": "10px", "marginBottom": "0"}),
            dbc.Select(
                id="filter-type-select",
                options=[
                    {"label": "全部商品", "value": "all"},
                    {"label": "銷量上升", "value": "increase"},
                    {"label": "銷量下降", "value": "decrease"},
                    {"label": "銷量無變化", "value": "no_change"}
                ],
                value="all",
                style={"width": "150px", "marginRight": "20px"}
            )
        ], style={"display": "flex", "alignItems": "center", "marginRight": "20px"}),
        html.Div([
            dbc.Label("商品名稱搜尋：", style={"marginRight": "10px", "marginBottom": "0"}),
            dbc.Input(
                id="product-name-filter",
                type="text",
                placeholder="搜尋商品名稱...",
                style={"width": "200px"}
            )
        ], style={"display": "flex", "alignItems": "center"})
    ], style={"display": "flex", "alignItems": "center"}),
    
    # 中間：確認按鈕
    html.Div([
        html.Div(id="sales-confirm-button-container", style={"display": "flex", "alignItems": "center"})
    ], style={"display": "flex", "alignItems": "center"}),
    
    # 右側：篩選按鈕
    html.Div([
        dbc.ButtonGroup([
            dbc.Button("全部商品", outline=True, id="btn-all-products", color="primary"),
            dbc.Button("未處理商品", outline=True, id="btn-unprocessed-products", color="primary"),
            dbc.Button("已處理商品", outline=True, id="btn-processed-products", color="primary")
        ])
    ], style={"display": "flex", "justifyContent": "flex-end"})
], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px", "marginTop": "30px"}),
    
    html.Div(id="sales-table-container"),
    
    # 向下拉式詳情區域
    html.Div(id="product-detail-dropdown", style={
        "marginTop": "10px",
        "border": "1px solid #ddd",
        "borderRadius": "8px",
        "backgroundColor": "#f8f9fa",
        "padding": "20px",
        "display": "none"
    }),
    
    # 處理確認 Modal
    dbc.Modal(
        id="sales-process-confirm-modal",
        is_open=False,
        centered=True,
        style={"fontSize": "18px"},
        children=[
            dbc.ModalHeader("確認處理滯銷商品", style={"fontWeight": "bold", "fontSize": "24px"}),
            dbc.ModalBody([
                html.Div(id="selected-products-info", style={"marginBottom": "20px"}),
                dbc.Row([
                    dbc.Label("處理人員", width=3),
                    dbc.Col(dbc.Input(
                        id="sales-modal-processor-name",
                        type="text",
                        placeholder="輸入處理人員姓名",
                        value="系統管理員"
                    ), width=9)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Label("處理時間", width=3),
                    dbc.Col(html.Div(id="sales-process-datetime", style={"padding": "8px", "backgroundColor": "#f8f9fa", "border": "1px solid #ced4da", "borderRadius": "4px"}), width=9)
                ], className="mb-3"),
            ]),
            dbc.ModalFooter([
                dbc.Button("取消", id="sales-modal-cancel-btn", color="secondary", className="me-2"),
                dbc.Button("確認處理", id="sales-modal-confirm-btn", color="success")
            ])
        ]
    ),
    
    create_success_toast("sales_change", message=""),
    create_error_toast("sales_change", message=""),
], className="mt-3")

# 載入滯銷品資料的 callback
@app.callback(
    Output("sales-change-data", "data"),
    Input("page-loaded-sales", "data"),
    prevent_initial_call=False
)
def load_sales_change_data(page_loaded):
    df_data = get_sales_change_data()
    return df_data.to_dict('records')

# 處理閾值篩選、搜尋篩選和資料更新
@app.callback(
    Output("filtered-sales-data", "data"),
    [Input("sales-change-data", "data"),
     Input("save-threshold-btn", "n_clicks"),
     Input("filter-type-select", "value"),
     Input("product-name-filter", "value")],
    State("sales-threshold-input", "value"),
    prevent_initial_call=False
)
def filter_sales_data(sales_data, save_clicks, filter_type, product_name_filter, threshold):
    if not sales_data:
        return []
    
    df = pd.DataFrame(sales_data)
    
    # 閾值篩選
    if threshold and save_clicks:
        df = df[df['變化比例原始值'].abs() >= threshold]
    
    # 類型篩選
    if filter_type == "increase":
        df = df[df['變化比例原始值'] > 0]
    elif filter_type == "decrease":
        df = df[df['變化比例原始值'] < 0]
    elif filter_type == "no_change":
        df = df[df['變化比例原始值'] == 0]
    
    # 商品名稱篩選
    if product_name_filter:
        df = df[df['商品名稱'].str.contains(product_name_filter, na=False, case=False)]
    
    # 只保留需要的欄位
    columns_to_keep = ['商品名稱', '上月銷量', '本月銷量', '變化比例', '變化比例原始值', '目前庫存', '狀態', '推薦客戶1', '推薦客戶1電話', '推薦客戶2', '推薦客戶2電話', '推薦客戶3', '推薦客戶3電話']
    df = df[columns_to_keep]
    
    # 確保所有需要的欄位都存在
    df = df[[col for col in columns_to_keep if col in df.columns]]

    return df.to_dict('records')

# 更新統計資訊
@app.callback(
    Output("sales-stats-container", "children"),
    Input("filtered-sales-data", "data")
)
def update_sales_stats(filtered_data):
    if not filtered_data:
        return [
            html.H5("滯銷品品數: 0"),
            html.H5("已處理: 0"),
            html.H5("未處理: 0")
        ]
    
    df = pd.DataFrame(filtered_data)
    total_products = len(df)
    processed_products = len(df[df['狀態'] == '已處理'])
    unprocessed_products = len(df[df['狀態'] == '未處理'])
    
    return [
        html.H5(f"滯銷品品數: {total_products}"),
        html.H5(f"已處理: {processed_products}"),
        html.H5(f"未處理: {unprocessed_products}")
    ]

# 表格顯示的 callback
@app.callback(
    Output("sales-table-container", "children"),
    [Input("filtered-sales-data", "data"),
     Input("btn-all-products", "n_clicks"),
     Input("btn-unprocessed-products", "n_clicks"),
     Input("btn-processed-products", "n_clicks")],
    prevent_initial_call=False
)
def display_sales_table(filtered_data, btn_all, btn_unprocessed, btn_processed):
    try:
        if not filtered_data:
            return html.Div("暫無資料")
        
        # 轉換為 DataFrame
        df = pd.DataFrame(filtered_data)
        
        if df.empty:
            return html.Div("暫無資料")
        
        # 根據按鈕狀態篩選資料
        ctx = callback_context
        show_checkbox = False
        
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id == 'btn-unprocessed-products':
                df = df[df['狀態'] == '未處理']
                show_checkbox = True
            elif button_id == 'btn-processed-products':
                df = df[df['狀態'] == '已處理']
                show_checkbox = False
            # else: 顯示全部商品
        
        # 重置索引，讓按鈕index從0開始連續
        df = df.reset_index(drop=True)
        
        # 應用顏色樣式到變化比例欄位
        def apply_percentage_style(row):
            try:
                original_value = row.get('變化比例原始值', 0)
                display_text = row.get('變化比例', '0%')
                
                if pd.isna(original_value) or original_value == 0:
                    return str(display_text)
                elif original_value > 0:
                    color = 'green'  # 正數（上升）顯示綠色
                elif original_value < 0:
                    color = 'red'    # 負數（下降）顯示紅色
                else:
                    color = 'black'  # 零或無變化顯示黑色
                    
                return html.Span(str(display_text), style={'color': color, 'fontWeight': 'bold'})
            except Exception as e:
                return str(row.get('變化比例', '0%'))
        
        # 只在有變化比例欄位時才應用樣式
        if '變化比例' in df.columns and '變化比例原始值' in df.columns:
            df['變化比例'] = df.apply(apply_percentage_style, axis=1)
        
        # 只保留表格顯示的欄位
        display_columns = ['商品名稱', '上月銷量', '本月銷量', '變化比例', '目前庫存', '狀態']
        # 確保所有欄位都存在
        available_columns = [col for col in display_columns if col in df.columns]
        df_display = df[available_columns].copy()
        
        if df_display.empty:
            return html.Div("暫無資料")
        
        # 使用原本的 custom_table 函數
        table = custom_table(
            df_display, 
            show_checkbox=show_checkbox, 
            show_button=True,
            button_text="詳情",
            button_id_type="sales_detail_button"
        )
        
        return html.Div(
            children=[table],
            style={
                "maxHeight": "40vh",              # 螢幕高度的40%
                "overflowY": "hidden",              # 垂直滾動
                "overflowX": "auto",              # 水平滾動
                "border": "1px solid #dee2e6",    # 邊框
                "borderRadius": "0.375rem",       # 圓角
                "backgroundColor": "white"        # 背景色
            }
        )
    
    except Exception as e:
        return html.Div(f"表格顯示錯誤: {str(e)}")

# 顯示確認已處理按鈕
@app.callback(
    Output('sales-confirm-button-container', 'children'),
    [Input({'type': 'status-checkbox', 'index': ALL}, 'value')]
)
def show_sales_confirm_button(checkbox_values):
    selected_rows = []
    for i, values in enumerate(checkbox_values):
        if values:  # 如果checkbox被選中
            selected_rows.extend(values)
    
    if selected_rows and len(selected_rows) > 0:
        return dbc.Button("確認已處理", id="sales_confirm_btn", color="success")
    else:
        return html.Div()

# 顯示向下拉式詳情
@app.callback(
    [Output('product-detail-dropdown', 'style'),
     Output('product-detail-dropdown', 'children')],
    [Input({'type': 'sales_detail_button', 'index': ALL}, 'n_clicks')],
    [State("filtered-sales-data", "data"),
     State("btn-all-products", "n_clicks"),
     State("btn-unprocessed-products", "n_clicks"),
     State("btn-processed-products", "n_clicks")],
    prevent_initial_call=True
)
def toggle_product_detail_dropdown(detail_clicks, filtered_data, btn_all, btn_unprocessed, btn_processed):
    if not any(detail_clicks) or not filtered_data:
        return {"display": "none"}, ""
    
    # 找到被點擊的按鈕索引
    ctx = callback_context
    if not ctx.triggered:
        return {"display": "none"}, ""

    # 從觸發的 prop_id 中解析按鈕索引
    triggered_prop_id = ctx.triggered[0]['prop_id']
    import json
    try:
        json_part = triggered_prop_id.split('.')[0]
        button_info = json.loads(json_part)
        button_index = button_info['index']
    except:
        return {"display": "none"}, ""
    
    if button_index is not None:
        # 重新篩選資料，確保 index 對應正確
        df = pd.DataFrame(filtered_data)
        
        # 根據當前的按鈕狀態篩選
        if btn_unprocessed and not btn_all and not btn_processed:
            df = df[df['狀態'] == '未處理']
        elif btn_processed and not btn_all and not btn_unprocessed:
            df = df[df['狀態'] == '已處理']
        
        df = df.reset_index(drop=True)
        
        if button_index < len(df):
            row_data = df.iloc[button_index]
            
            # 根據原始值決定顏色
            original_value = row_data['變化比例原始值']
            if pd.isna(original_value):
                percentage_color = "#000"
            elif original_value > 0:
                percentage_color = "#28a745"  # 綠色
            elif original_value < 0:
                percentage_color = "#dc3545"  # 紅色
            else:
                percentage_color = "#000"     # 黑色
            
            # 商品詳情內容
            detail_content = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H5(f"{row_data['商品名稱']}", style={"color": "#2c3e50", "marginBottom": "20px"}),
                        dbc.Row([
                            dbc.Col([
                                html.P([html.Strong("上月銷量: "), f"{row_data['上月銷量']}箱"]),
                                html.P([html.Strong("本月銷量: "), f"{row_data['本月銷量']}箱"]),
                            ], width=6),
                            dbc.Col([
                                html.P([html.Strong("變化比例: "), 
                                        html.Span(row_data['變化比例'], 
                                                 style={"color": percentage_color, "fontWeight": "bold"})]),
                                html.P([html.Strong("目前庫存: "), f"{row_data['目前庫存']}箱"]),
                            ], width=6)
                        ])
                    ], width=8),
                    dbc.Col([
                        html.H6("推薦客戶", style={"marginBottom": "15px"}),
                        html.Div([
                            html.Div([
                                html.P([
                                    html.Strong(f"客戶 {i}: "),
                                    row_data.get(f'推薦客戶{i}', '未設定'),
                                    html.Br(),
                                    html.Small(f"電話: {row_data.get(f'推薦客戶{i}電話', '未設定')}", 
                                                style={"color": "#666"})
                                ], style={"marginBottom": "10px"})
                                for i in [1, 2, 3] 
                                if row_data.get(f'推薦客戶{i}', '未設定') != '未設定'
                            ]) if any(row_data.get(f'推薦客戶{i}', '未設定') != '未設定' for i in [1, 2, 3])
                            else html.P("暫無推薦客戶", style={"color": "#666", "fontStyle": "italic"})
                        ])
                    ], width=4)
                ]),
                html.Hr(),
                html.Div([
                    dbc.Button("收起", id="close-detail-btn", color="secondary", size="sm")
                ], style={"textAlign": "right"})
            ])
            
            return {
                "marginTop": "10px",
                "border": "1px solid #ddd",
                "borderRadius": "8px",
                "backgroundColor": "#f8f9fa",
                "padding": "20px",
                "display": "block"
            }, detail_content
    
    return {"display": "none"}, ""

# 收起詳情
@app.callback(
    Output('product-detail-dropdown', 'style', allow_duplicate=True),
    Input('close-detail-btn', 'n_clicks'),
    prevent_initial_call=True
)
def close_detail_dropdown(close_clicks):
    if close_clicks:
        return {"display": "none"}
    return dash.no_update

# 顯示處理確認 Modal
@app.callback(
    [Output('sales-process-confirm-modal', 'is_open'),
     Output('selected-products-info', 'children'),
     Output('sales-process-datetime', 'children')],
    [Input('sales_confirm_btn', 'n_clicks'),
     Input('sales-modal-cancel-btn', 'n_clicks')],
    [State({'type': 'status-checkbox', 'index': ALL}, 'value'),
     State("filtered-sales-data", "data"),
     State('sales-process-confirm-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_sales_process_modal(confirm_clicks, cancel_clicks, checkbox_values, filtered_data, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return False, "", ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'sales_confirm_btn' and confirm_clicks:
        # 獲取選中的商品
        selected_indices = []
        for i, values in enumerate(checkbox_values):
            if values:
                selected_indices.extend(values)
        
        if selected_indices and filtered_data:
            df = pd.DataFrame(filtered_data)
            selected_products = [df.iloc[index]['商品名稱'] for index in selected_indices if index < len(df)]
            
            # 顯示選中的商品
            product_info = html.Div([
                html.H6(f"將處理以下 {len(selected_products)} 項商品：", style={"marginBottom": "10px"}),
                html.Ul([html.Li(product) for product in selected_products])
            ])
            
            # 顯示當前時間
            from datetime import datetime
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return True, product_info, current_time
    
    elif button_id == 'sales-modal-cancel-btn':
        return False, "", ""
    
    return is_open, dash.no_update, dash.no_update

# 處理確認已處理的邏輯
@app.callback(
    [Output('sales_change-success-toast', 'is_open'),
     Output('sales_change-success-toast', 'children'),
     Output('sales_change-error-toast', 'is_open'),
     Output('sales_change-error-toast', 'children'),
     Output("page-loaded-sales", "data", allow_duplicate=True),
     Output('sales-process-confirm-modal', 'is_open', allow_duplicate=True)],
    Input('sales-modal-confirm-btn', 'n_clicks'),
    [State({'type': 'status-checkbox', 'index': ALL}, 'value'),
     State("filtered-sales-data", "data"),
     State("sales-modal-processor-name", "value")],
    prevent_initial_call=True
)
def confirm_sales_processed(modal_confirm_clicks, checkbox_values, filtered_data, processor_name):
    if not modal_confirm_clicks:
        return False, "", False, "", dash.no_update, dash.no_update
    
    # 獲取選中的商品
    selected_indices = []
    for i, values in enumerate(checkbox_values):
        if values:
            selected_indices.extend(values)
    
    if not selected_indices or not filtered_data:
        return False, "", True, "沒有選擇任何商品", dash.no_update, False
    
    try:
        df = pd.DataFrame(filtered_data)
        product_names = [df.iloc[index]['商品名稱'] for index in selected_indices if index < len(df)]
        
        success_count = len(product_names)
        
        return True, f"成功處理 {success_count} 項滯銷商品", False, "", True, False
        
    except Exception as e:
        return False, "", True, f"處理失敗：{e}", dash.no_update, False