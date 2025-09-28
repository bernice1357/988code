from .common import *
from dash import ALL, callback_context
import global_vars

def get_sales_change_data():
    """從API獲取滯銷品資料"""
    try:
        response = requests.get('http://127.0.0.1:8000/get_sales_change_data')
        response.raise_for_status()
        data = response.json()
        
        # 先檢查資料是否為空
        if not data:
            # print("API 返回空資料")
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # 重新命名欄位和格式化資料
        if not df.empty:
            # 檢查必要欄位是否存在
            required_columns = ['product_id', 'product_name', 'last_month_sales', 'current_month_sales', 
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

def get_sales_change_data_by_threshold(threshold):
    """根據閾值從API獲取滯銷品資料"""
    try:
        response = requests.get(f'http://127.0.0.1:8000/get_sales_change_data_by_threshold/{threshold}')
        response.raise_for_status()
        data = response.json()
        
        # 先檢查資料是否為空
        if not data:
            # print("API 返回空資料")
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
                        html.H5("銷量異動商品: 0"),
                        html.H5("已處理: 0"),
                        html.H5("未處理: 0")
                    ])
                ])
            ], color="light", style={"height": "100%"})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("設定變化比例"),
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
                ],
                value="all",
                style={"width": "auto", "marginRight": "20px"}
            )
        ], style={"display": "flex", "alignItems": "center", "marginRight": "20px"}),
        html.Div([
            dbc.Label("商品名稱搜尋：", style={"marginRight": "10px", "marginBottom": "0"}),
            dcc.Dropdown(
                id="product-name-filter",
                options=[],  # 初始為空，會透過 callback 動態更新
                value=None,
                placeholder="搜尋商品名稱...",
                searchable=True,  # 啟用搜尋功能
                clearable=True,   # 可清除選項
                style={
                    "width": "200px",
                    "fontSize": "14px",
                    "lineHeight": "1.2"
                },
                # 設定下拉選單的樣式
                optionHeight=40,  # 每個選項的高度
                maxHeight=200     # 下拉選單最大高度
            )
        ], style={"display": "flex", "alignItems": "center"})
    ], style={"display": "flex", "alignItems": "center"}),
    
    
    # 右側：篩選按鈕
    html.Div([
        dbc.ButtonGroup([
            dbc.Button("全部商品", id="btn-all-products"),
            dbc.Button("未處理商品", id="btn-unprocessed-products"),
            dbc.Button("已處理商品", id="btn-processed-products")
        ])
    ], style={"display": "flex", "justifyContent": "flex-end"})
], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px", "marginTop": "30px"}),
    
    html.Div(
        [
            dcc.Loading(
                id="loading-sales-table",
                type="dot",
                children=html.Div(
                    id="sales-table-container",
                    style={"flex": "1 1 auto"}
                ),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "position": "fixed", 
                    "top": "50%",          
                }
            ),
            html.Div(
                id="sales-confirm-button-container",
                style={"display": "flex", "justifyContent": "flex-end", "alignItems": "center", "marginTop": "12px", "width": "100%"}
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "width": "100%"}
    ),
    
    # 商品詳情 Modal
    dbc.Modal(
        id="product-detail-modal",
        is_open=False,
        centered=True,
        size="lg",
        style={"fontSize": "16px"},
        children=[
            dbc.ModalHeader([
                dbc.ModalTitle(id="product-detail-modal-title")
            ]),
            dbc.ModalBody(id="product-detail-modal-body"),
            dbc.ModalFooter([
                dbc.Button("關閉", id="close-product-detail-modal", color="secondary")
            ])
        ]
    ),
    
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
            ]),
            dbc.ModalFooter([
                dbc.Button("取消", id="sales-modal-cancel-btn", color="secondary", className="me-2"),
                dbc.Button("確認處理", id="sales-modal-confirm-btn", color="success")
            ])
        ]
    ),
    
    success_toast("sales_change", message=""),
    error_toast("sales_change", message=""),
], className="mt-3")

# 從全域變數載入變化比例設定
@app.callback(
    Output("sales-threshold-input", "value"),
    Input("page-loaded-sales", "data"),
    prevent_initial_call=False
)
def load_saved_threshold(page_loaded):
    return global_vars.get_sales_threshold()

# 保存變化比例設定到全域變數
@app.callback(
    Output("sales-threshold-input", "value", allow_duplicate=True),
    Input("save-threshold-btn", "n_clicks"),
    State("sales-threshold-input", "value"),
    prevent_initial_call=True
)
def save_threshold_to_global(n_clicks, threshold_value):
    if n_clicks and threshold_value:
        if global_vars.set_sales_threshold(threshold_value):
            return threshold_value
    return dash.no_update

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
     Input("product-name-filter", "value")],  # 這裡現在接收的是選中的值，而不是輸入的文字
    State("sales-threshold-input", "value"),
    prevent_initial_call=False
)
def filter_sales_data(sales_data, save_clicks, filter_type, product_name_filter, threshold):
    if not sales_data:
        return []
    
    # 使用全域變數的閾值進行篩選
    current_threshold = global_vars.get_sales_threshold()
    if current_threshold:
        df_threshold = get_sales_change_data_by_threshold(current_threshold)
        if not df_threshold.empty:
            sales_data = df_threshold.to_dict('records')
    
    df = pd.DataFrame(sales_data)
    
    if 'product_id' in df.columns and '商品_ID' not in df.columns:
        df['商品_ID'] = df['product_id']
    
    # 類型篩選
    if filter_type == "increase":
        df = df[df['變化比例原始值'] > 0]
    elif filter_type == "decrease":
        df = df[df['變化比例原始值'] < 0]
    elif filter_type == "no_change":
        df = df[df['變化比例原始值'] == 0]
    
    # 商品名稱篩選 - 修改為精確匹配
    if product_name_filter:
        df = df[df['商品名稱'] == product_name_filter]  # 改為精確匹配
    
    # 只保留需要的欄位
    columns_to_keep = ['product_id', '商品_ID', '商品名稱', '上月銷量', '本月銷量', '變化比例', '變化比例原始值', '目前庫存', '狀態', '推薦客戶1', '推薦客戶1電話', '推薦客戶2', '推薦客戶2電話', '推薦客戶3', '推薦客戶3電話']
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
            html.H5("銷量異動商品: 0"),
            html.H5("已處理: 0"),
            html.H5("未處理: 0")
        ]
    
    df = pd.DataFrame(filtered_data)
    total_products = len(df)
    processed_products = len(df[df['狀態'] == '已處理'])
    unprocessed_products = len(df[df['狀態'] == '未處理'])
    
    return [
        html.H5(f"銷量異動商品: {total_products}"),
        html.H5(f"已處理: {processed_products}"),
        html.H5(f"未處理: {unprocessed_products}")
    ]

def create_custom_sales_table(df, show_checkbox=False, show_button=False, button_text="詳情", button_id_type="sales_detail_button", table_height='47vh'):
    """專門為滯銷品創建的自定義表格，可以控制標題高度和狀態背景顏色"""
    from dash import html
    
    if df.empty:
        return html.Div("暫無資料")
    
    # 自定義標題樣式
    header_style = {
        "position": "sticky",
        "top": "-1px",
        "zIndex": 2,
        'backgroundColor': '#bcd1df',
        'fontWeight': 'bold',
        'fontSize': '16px',
        'padding': '2px',              
        'height': '5px',               
        'minHeight': '5px',            
        'verticalAlign': 'middle',      
        'textAlign': 'center',
        'border': '1px solid #ccc',
        'whiteSpace': 'nowrap'
    }
    
    # 手動建立表格標題
    headers = []
    if show_checkbox:
        headers.append(html.Th('', style={**header_style, 'width': '50px'}))
    
    for col in df.columns:
        headers.append(html.Th(col, style=header_style))
    
    if show_button:
        headers.append(html.Th('操作', style={**header_style, 'width': '100px'}))
    
    # 建立表格主體
    rows = []
    for i, row in df.iterrows():
        row_cells = []
        if show_checkbox:
            row_cells.append(html.Td(
                dcc.Checklist(
                    id={'type': 'status-checkbox', 'index': i},
                    options=[{'label': '', 'value': i}],
                    value=[]
                ), style={'textAlign': 'center', 'padding': '8px'}
            ))
        
        for col in df.columns:
            # 只有狀態欄位需要特殊背景顏色
            if col == '狀態':
                if row[col] == '已處理':
                    cell_bg_color = '#d4edda'  # 淺綠色背景
                elif row[col] == '未處理':
                    cell_bg_color = '#f8d7da'  # 淺紅色背景
                else:
                    cell_bg_color = '#ffffff'
            else:
                cell_bg_color = '#ffffff'  # 其他欄位保持白色背景
                
            row_cells.append(html.Td(
                row[col], 
                style={
                    'padding': '8px', 
                    'textAlign': 'center',
                    'backgroundColor': cell_bg_color
                }
            ))
        
        if show_button:
            row_cells.append(html.Td(
                html.Button(
                    button_text,
                    id={'type': button_id_type, 'index': i},
                    className="btn btn-warning btn-sm"
                ), style={'textAlign': 'center', 'padding': '8px'}
            ))
        
        rows.append(html.Tr(row_cells, style={'backgroundColor': '#ffffff'}))
    
    # 建立完整表格
    table = html.Table([
        html.Thead([html.Tr(headers)]),
        html.Tbody(rows, style={'backgroundColor': '#ffffff'})
    ], style={'width': '100%', 'borderCollapse': 'collapse', 'backgroundColor': '#ffffff'})
    
    return html.Div([table], style={
        'overflowY': 'auto',
        'maxHeight': table_height,
        'border': '1px solid #ccc',
        'borderRadius': '8px',
        'backgroundColor': '#ffffff'
    })

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
        display_columns = ['商品_ID', '商品名稱', '上月銷量', '本月銷量', '變化比例', '目前庫存', '狀態']
        # 確保所有欄位都存在
        available_columns = [col for col in display_columns if col in df.columns]
        df_display = df[available_columns].copy()
        
        if df_display.empty:
            return html.Div("暫無資料")
        
        # 使用自定義表格函數
        return create_custom_sales_table(
            df_display, 
            show_checkbox=show_checkbox, 
            show_button=True,
            button_text="詳情",
            button_id_type="sales_detail_button",
            table_height="47vh"
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

# 顯示商品詳情 Modal
@app.callback(
    [Output('product-detail-modal', 'is_open'),
     Output('product-detail-modal-title', 'children'),
     Output('product-detail-modal-body', 'children')],
    [Input({'type': 'sales_detail_button', 'index': ALL}, 'n_clicks'),
     Input('close-product-detail-modal', 'n_clicks')],
    [State("filtered-sales-data", "data"),
     State("btn-all-products", "n_clicks"),
     State("btn-unprocessed-products", "n_clicks"),
     State("btn-processed-products", "n_clicks"),
     State('product-detail-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_product_detail_modal(detail_clicks, close_clicks, filtered_data, btn_all, btn_unprocessed, btn_processed, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return False, "", ""
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    # 關閉 modal
    if 'close-product-detail-modal' in trigger_id:
        return False, "", ""
    
    # 打開 modal - 詳情按鈕被點擊
    if 'sales_detail_button' in trigger_id and any(detail_clicks) and filtered_data:
        # 從觸發的 prop_id 中解析按鈕索引
        import json
        try:
            json_part = trigger_id.split('.')[0]
            button_info = json.loads(json_part)
            button_index = button_info['index']
        except:
            return False, "", ""
        
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
            
            # Modal 標題
            modal_title = f"{row_data['商品名稱']} - 推薦客戶"
            
            # Modal 內容 - 只顯示推薦客戶
            modal_body = html.Div([
                html.Div([
                    html.Div([
                        html.P([
                            html.Strong(f"客戶 {i}: "),
                            row_data.get(f'推薦客戶{i}', '未設定'),
                            html.Br(),
                            html.Small(f"電話: {row_data.get(f'推薦客戶{i}電話', '未設定')}", 
                                        style={"color": "#666"})
                        ], style={"marginBottom": "15px", "padding": "10px", "backgroundColor": "#f8f9fa", "borderRadius": "5px"})
                        for i in [1, 2, 3] 
                        if row_data.get(f'推薦客戶{i}', '未設定') != '未設定'
                    ]) if any(row_data.get(f'推薦客戶{i}', '未設定') != '未設定' for i in [1, 2, 3])
                    else html.Div([
                        html.P("暫無推薦客戶", style={
                            "color": "#666", 
                            "fontStyle": "italic", 
                            "textAlign": "center",
                            "padding": "20px",
                            "backgroundColor": "#f8f9fa",
                            "borderRadius": "5px"
                        })
                    ])
                ])
            ])
            
            return True, modal_title, modal_body
    
    return False, "", ""

# 修正後的處理確認已處理邏輯
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
     State("btn-all-products", "n_clicks"),
     State("btn-unprocessed-products", "n_clicks"),
     State("btn-processed-products", "n_clicks")],
    prevent_initial_call=True
)
def confirm_sales_processed(modal_confirm_clicks, checkbox_values, filtered_data, btn_all, btn_unprocessed, btn_processed):
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
        # 重要：需要重新應用與表格顯示相同的篩選邏輯
        df = pd.DataFrame(filtered_data)
        
        # 根據按鈕狀態篩選資料（與display_sales_table相同的邏輯）
        if btn_unprocessed and not btn_all and not btn_processed:
            df = df[df['狀態'] == '未處理']
        elif btn_processed and not btn_all and not btn_unprocessed:
            df = df[df['狀態'] == '已處理']
        # 如果是全部商品，則不需額外篩選
        
        # 重置索引，確保索引從0開始連續（與表格顯示一致）
        df = df.reset_index(drop=True)
        
        # 根據重置後的索引獲取正確的 product_id
        product_ids = []
        for index in selected_indices:
            if index < len(df):
                product_ids.append(df.iloc[index]['product_id'])
        
        if not product_ids:
            return False, "", True, "無法獲取選中商品的ID", dash.no_update, False
        
        # 新增：實際呼叫 API 更新資料庫
        success_count = 0
        failed_products = []
        
        for product_id in product_ids:
            try:
                # 呼叫新的 API 更新 sales_change_table 的 status
                response = requests.put(
                    f'http://127.0.0.1:8000/update_sales_change_status_by_id',
                    json={
                        "product_id": product_id,
                        "status": True,
                        "user_role": "editor"
                    }
                )
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    failed_products.append(product_id)
                    
            except Exception as e:
                print(f"更新 {product_id} 失敗: {e}")
                failed_products.append(product_id)
        
        if failed_products:
            error_msg = f"部分商品更新失敗: {', '.join(failed_products)}"
            return True, f"成功處理 {success_count} 項，失敗 {len(failed_products)} 項", True, error_msg, True, False
        else:
            return True, f"成功處理 {success_count} 項滯銷商品", False, "", True, False
        
    except Exception as e:
        return False, "", True, f"處理失敗：{e}", dash.no_update, False

# 同時也需要修正顯示處理確認 Modal 的邏輯
@app.callback(
    [Output('sales-process-confirm-modal', 'is_open'),
     Output('selected-products-info', 'children')],
    [Input('sales_confirm_btn', 'n_clicks'),
     Input('sales-modal-cancel-btn', 'n_clicks')],
    [State({'type': 'status-checkbox', 'index': ALL}, 'value'),
     State("filtered-sales-data", "data"),
     State("btn-all-products", "n_clicks"),
     State("btn-unprocessed-products", "n_clicks"),
     State("btn-processed-products", "n_clicks"),
     State('sales-process-confirm-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_sales_process_modal(confirm_clicks, cancel_clicks, checkbox_values, filtered_data, btn_all, btn_unprocessed, btn_processed, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return False, ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'sales_confirm_btn' and confirm_clicks:
        # 獲取選中的商品
        selected_indices = []
        for i, values in enumerate(checkbox_values):
            if values:
                selected_indices.extend(values)
        
        if selected_indices and filtered_data:
            # 重要：需要重新應用與表格顯示相同的篩選邏輯
            df = pd.DataFrame(filtered_data)
            
            # 根據按鈕狀態篩選資料（與display_sales_table和confirm_sales_processed相同的邏輯）
            if btn_unprocessed and not btn_all and not btn_processed:
                df = df[df['狀態'] == '未處理']
            elif btn_processed and not btn_all and not btn_unprocessed:
                df = df[df['狀態'] == '已處理']
            # 如果是全部商品，則不需額外篩選
            
            # 重置索引，確保索引從0開始連續（與表格顯示一致）
            df = df.reset_index(drop=True)
            
            # 根據重置後的索引獲取正確的商品名稱
            selected_products = []
            for index in selected_indices:
                if index < len(df):
                    selected_products.append(df.iloc[index]['商品名稱'])
            
            # 顯示選中的商品
            product_info = html.Div([
                html.H6(f"將處理以下 {len(selected_products)} 項商品：", style={"marginBottom": "10px"}),
                html.Ul([html.Li(product) for product in selected_products])
            ])
            
            return True, product_info
    
    elif button_id == 'sales-modal-cancel-btn':
        return False, ""
    
    return is_open, dash.no_update
    
# 更新商品名稱下拉選單選項
@app.callback(
    Output("product-name-filter", "options"),
    Input("sales-change-data", "data"),
    prevent_initial_call=False
)
def update_product_name_options(sales_data):
    if not sales_data:
        return []
    
    df = pd.DataFrame(sales_data)
    if df.empty or '商品名稱' not in df.columns:
        return []
    
    # 獲取所有唯一的商品名稱
    product_names = df['商品名稱'].unique()
    
    # 轉換為下拉選單選項格式
    options = [{"label": "全部商品", "value": ""}]  # 空值代表全部商品
    product_options = []
    for name in sorted(product_names):
        product_options.append({"label": name, "value": name})

    options.extend(product_options)
    return options

# 管理按鈕樣式的 callback
@app.callback(
    [Output("btn-all-products", "style"),
     Output("btn-unprocessed-products", "style"),
     Output("btn-processed-products", "style")],
    [Input("btn-all-products", "n_clicks"),
     Input("btn-unprocessed-products", "n_clicks"),
     Input("btn-processed-products", "n_clicks")],
    prevent_initial_call=False
)
def update_product_button_styles(btn_all, btn_unprocessed, btn_processed):
    ctx = callback_context
    active_button = None

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        active_button = button_id
    else:
        # 預設狀態為全部商品
        active_button = "btn-all-products"

    # 定義按鈕樣式
    default_style = {
        "backgroundColor": "transparent",
        "color": "#000000",
        "border": "2px solid #000000"
    }

    active_style = {
        "backgroundColor": "#000000",
        "color": "#ffffff",
        "border": "2px solid #000000"
    }

    # 根據活動按鈕返回對應樣式
    all_style = active_style if active_button == "btn-all-products" else default_style
    unprocessed_style = active_style if active_button == "btn-unprocessed-products" else default_style
    processed_style = active_style if active_button == "btn-processed-products" else default_style

    return all_style, unprocessed_style, processed_style
