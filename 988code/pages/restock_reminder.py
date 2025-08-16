from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
import requests
import plotly.graph_objects as go
from dash import ctx
import dash_bootstrap_components as dbc

# TODO 差預計補貨日期欄位

# offcanvas
product_input_fields = [
    {
        "id": "customer-id", 
        "label": "客戶ID",
        "type": "dropdown"
    },
]
restock_offcanvas = create_search_offcanvas(
    page_name="restock_reminder",
    input_fields=product_input_fields,
)

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[
        # 儲存初始載入標記
        dcc.Store(id="page-loaded", data=True),
    # 儲存表格資料
    dcc.Store(id="table-data-store", data=[]),
    # 儲存客戶資訊
    dcc.Store(id="customer-info-store", data={}),
    # 儲存checkbox選擇狀態 - 不受搜尋條件影響的全域狀態
    dcc.Store(id="checkbox-state-store", data={}),
    
    # 觸發 Offcanvas 的按鈕和確認狀態按鈕
    html.Div([
        restock_offcanvas["trigger_button"],
        dbc.Button(
            "確認狀態",
            id="confirm-status-btn",
            color="success",
            style={"marginLeft": "10px", "display": "none"}  # 預設隱藏
        ),
        html.Div(
            id="selection-count-display",
            style={"marginLeft": "20px", "fontSize": "16px", "fontWeight": "bold", "color": "#28a745"}
        )
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}),
    
    error_toast("restock-reminder", message=""),
    restock_offcanvas["offcanvas"],
    dcc.Loading(
        id="loading-restock-table",
        type="dot",
        children=html.Div(id="table-container", style={"marginTop": "20px"}),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "position": "fixed", 
            "top": "50%",          
        }
    ),
    
    dbc.Modal(
        id="detail-modal",
        size="xl",
        is_open=False,
        centered=True,
        style={
            "maxWidth": "95vw",
            "minWidth": "95vw"
        },
        children=[
            dbc.ModalBody(id="modal-body"),
        ]
    ),
    
    # 確認狀態的Modal
    dbc.Modal(
        id="confirm-status-modal",
        size="xl",
        is_open=False,
        centered=True,
        style={
            "maxWidth": "95vw",
            "minWidth": "95vw"
        },
        children=[
            dbc.ModalHeader(dbc.ModalTitle("確認補貨狀態")),
            dbc.ModalBody([
                html.Div(id="confirm-status-content"),
                html.Div([
                    dbc.Button("確認", id="confirm-status-btn-final", color="success", className="me-2"),
                    dbc.Button("關閉", id="close-confirm-modal-btn", color="secondary")
                ], className="d-flex justify-content-end mt-3")
            ])
        ]
    ),
    
    # 下載提示 toast
    info_toast(
        "restock-download",
        message="正在準備下載圖表，請稍候..."
    ),
])

# 載入數據的 callback
@app.callback(
    [Output("table-container", "children"),
     Output("table-data-store", "data"),
     Output("restock-reminder-error-toast", "is_open"),
     Output("restock-reminder-error-toast", "children")],
    Input("page-loaded", "data"),
    prevent_initial_call=False
)
def load_data_and_handle_errors(page_loaded):
    try:
        e=10000
        response = requests.get('http://127.0.0.1:8000/get_restock_data')
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            # 重新命名欄位
            df = df.rename(columns={
                'customer_id': '客戶ID',
                'customer_name': '客戶名稱',
                'phone_number': '電話號碼',
                'product_id': '商品ID',
                'product_name': '商品名稱',
                'prediction_date': '預計補貨日期',
                'estimated_quantity': '預估數量',
                'confidence_level': '信心度'
            })
            
            # 按客戶ID分組數據
            customer_groups = df.groupby(['客戶ID', '客戶名稱', '電話號碼'])
            
            # 創建Accordion
            accordions = []
            all_records = []  # 用於存儲所有記錄，給modal使用
            
            customer_index = 0
            for (customer_id, customer_name, phone_number), group in customer_groups:
                # 按預測日期排序
                group = group.sort_values('預計補貨日期', ascending=False)
                
                # 建立標題（初始載入時不會有選中項目） 
                title_text = html.Span([
                    html.Span(customer_id, style={'color': 'black', 'fontWeight': 'bold'}),
                    html.Span(' '),
                    html.Span(customer_name, style={'color': 'black'}),
                    html.Span(f' ({phone_number})', style={'color': 'black'})
                ])
                
                # 建立accordion內容 - 表格標題
                table_header = html.Div([
                    html.Div('選擇', style={'font-weight': 'bold', 'flex': '0 0 60px', 'border-right': '1px solid #ddd', 'padding': '10px', 'border-left': '1px solid #ddd', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('商品ID', style={'font-weight': 'bold', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('商品名稱', style={'font-weight': 'bold', 'flex': '2', 'border-right': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('預計補貨日期', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('預估數量', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('信心度', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('操作', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1', 'padding': '10px', 'border-right': '1px solid #ddd', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'})
                ], style={'display': 'flex', 'background-color': '#f8f9fa', 'border-top': '1px solid #ddd', 'border-bottom': '1px solid #ddd', 'align-items': 'center'})
                
                # 建立資料行
                table_rows = []
                row_index = 0
                for _, row in group.iterrows():
                    # 將每行資料加入all_records供modal使用
                    record_for_modal = {
                        '客戶ID': customer_id,
                        '客戶名稱': customer_name
                    }
                    all_records.append(record_for_modal)
                    
                    # 創建唯一的checkbox ID
                    checkbox_id = f"checkbox-{customer_id}-{row_index}"
                    
                    table_row = html.Div([
                        html.Div([
                            dcc.Checklist(
                                id={'type': 'restock-checkbox', 'customer_id': customer_id, 'row_index': row_index},
                                options=[{'label': '', 'value': f"{customer_id}-{row_index}"}],
                                value=[],
                                style={'margin': '0'}
                            )
                        ], style={'flex': '0 0 60px', 'border-right': '1px solid #ddd', 'border-left': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('商品ID', '')), style={'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('商品名稱', '')), style={'flex': '2', 'border-right': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('預計補貨日期', '')), style={'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('預估數量', '')), style={'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('信心度', '')), style={'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div([
                            dbc.Button("查看歷史補貨紀錄", 
                                     id={'type': 'view-button', 'index': customer_index},
                                     color="warning",
                                     size="sm",
                                     n_clicks=0,
                                     style={'fontSize': '16px', 'whiteSpace': 'nowrap'})
                        ], style={'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'})
                    ], style={'display': 'flex', 'background-color': 'white', 'border-bottom': '1px solid #ddd', 'align-items': 'center', 'min-height': '50px'})
                    
                    table_rows.append(table_row)
                    row_index += 1
                
                # 可滾動的內容區域
                scrollable_content = html.Div([
                    # 固定標題，為滾動條預留空間
                    html.Div([
                        table_header
                    ], style={
                        'position': 'sticky',
                        'top': '0',
                        'z-index': '10',
                        'background-color': 'white',
                        'padding-right': '17px'  # 預留滾動條寬度
                    }),
                    # 滾動內容區域
                    html.Div(table_rows, style={
                        'max-height': '400px',
                        'overflow-y': 'auto',
                        'background-color': 'white'
                    })
                ], style={'background-color': 'white'})
                
                # 建立 Accordion Item with dynamic title
                accordion_item = dbc.AccordionItem(
                    scrollable_content,
                    title=title_text,
                    item_id=f'accordion-{customer_id}'
                )
                
                accordions.append(accordion_item)
                customer_index += 1
            
            # 創建 Accordion 容器
            accordion_container = html.Div([
                dbc.Accordion(accordions, id='restock-accordion', start_collapsed=True)
            ], style={'marginTop': '20px'})
            
            return accordion_container, all_records, False, ""
        else:
            error_msg = f"API 請求失敗：{response.status_code}"
            return html.Div(), [], True, error_msg
    except Exception as ex:
        error_msg = f"API 請求錯誤：{ex}"
        return html.Div(), [], True, error_msg

# 載入客戶ID選項
@app.callback(
    Output("restock_reminder-customer-id", "options"),
    Input("page-loaded", "data"),
    prevent_initial_call=False
)
def load_customer_options(page_loaded):
    try:
        response = requests.get('http://127.0.0.1:8000/get_restock_customer_ids')
        if response.status_code == 200:
            data = response.json()
            customer_ids = data['customer_ids']
            options = [{"label": customer_id, "value": customer_id} for customer_id in customer_ids]
            return options
        else:
            return []
    except Exception as ex:
        return []

# 抓 modal 歷史紀錄
@app.callback(
    [Output("modal-body", "children"),
     Output("detail-modal", "is_open"),
     Output("customer-info-store", "data")],
    Input({"type": "view-button", "index": dash.ALL}, "n_clicks"),
    State("table-data-store", "data"),
    prevent_initial_call=True
)
def show_detail_modal(view_clicks, table_data):
    triggered = ctx.triggered_id
    
    is_all_zero = all(v == 0 for v in view_clicks)
    if not is_all_zero and triggered is not None:
        idx = triggered["index"]
        row = table_data[idx]
        customer_id = row['客戶ID']
        customer_name = row['客戶名稱']
        
        # 儲存客戶資訊到 store
        customer_info = {
            'customer_id': customer_id,
            'customer_name': customer_name
        }
        
        # 呼叫新的 API 獲取歷史資料
        try:
            response = requests.get(f'http://127.0.0.1:8000/get_restock_history/{customer_id}')
            if response.status_code == 200:
                history_data = response.json()
                history_df = pd.DataFrame(history_data)
                
                # 假設 API 回傳的資料有 date 欄位
                if not history_df.empty and 'transaction_date' in history_df.columns:
                    history_df['transaction_date'] = pd.to_datetime(history_df['transaction_date'])
                    
                    # 建立時間軸圖表
                    fig = go.Figure()
                    
                    # 添加時間點
                    fig.add_trace(go.Scatter(
                        x=history_df['transaction_date'],
                        y=[1] * len(history_df),  # 所有點放在同一條水平線上
                        mode="markers+text",
                        text=[f"{d.strftime('%Y')}<br>{d.strftime('%m-%d')}" for d in history_df['transaction_date']],
                        textposition="top center",
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=[d.strftime('%Y-%m-%d') for d in history_df['transaction_date']],
                        marker=dict(size=12, color="#564dff", symbol="circle"),
                        name="補貨日期"
                    ))
                    
                    # 添加連線
                    fig.add_trace(go.Scatter(
                        x=history_df['transaction_date'],
                        y=[1] * len(history_df),
                        mode="lines",
                        line=dict(color="#564dff", width=2),
                        showlegend=False
                    ))
                    
                    # 計算圖表寬度
                    data_count = len(history_df)
                    # 每個點間距約80px，確保有足夠空間
                    chart_width = max(800, data_count * 80)
                    
                    # 根據圖表寬度判斷是否需要滾動（modal 寬度大約1200px）
                    modal_width = 1200
                    scrollable = chart_width > modal_width
                    
                    # 設定圖表樣式
                    fig.update_layout(
                        showlegend=False,
                        xaxis=dict(
                            type='date',
                            tickmode='linear',
                            dtick='M1',  # 每月一個刻度
                            showticklabels=True,
                            tickformat='%Y/%m',  # 只顯示年/月格式
                            showgrid=True,
                            gridcolor="lightgray",
                            gridwidth=1
                        ),
                        yaxis=dict(showticklabels=False, range=[-0.2, 2.5]),
                        height=300,
                        width=chart_width,
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        margin=dict(l=20, r=20, t=50, b=50)
                    )
                    
                    if scrollable:
                        timeline_chart = html.Div([
                            dcc.Graph(figure=fig, id="timeline-chart", style={"width": f"{chart_width}px"}, config={'displayModeBar': False}),
                            dcc.Download(id="download-chart")
                        ], style={"overflowX": "auto", "width": "100%"})
                    else:
                        timeline_chart = html.Div([
                            dcc.Graph(figure=fig, id="timeline-chart", style={"width": f"{chart_width}px"}, config={'displayModeBar': False}),
                            dcc.Download(id="download-chart")
                        ])
                else:
                    timeline_chart = html.Div("無歷史資料", style={"textAlign": "center", "padding": "20px"})
            else:
                timeline_chart = html.Div("無法載入歷史資料", style={"textAlign": "center", "padding": "20px"})
        except Exception as e:
            timeline_chart = html.Div(f"載入錯誤: {str(e)}", style={"textAlign": "center", "padding": "20px"})
        
        content = html.Div([
            html.H2(f"{customer_id} - {customer_name} 歷史補貨紀錄", style={"textAlign": "center"}),
            html.Hr(),
            timeline_chart,
            html.Hr(),
            html.Div([
                dbc.Button("下載圖表", id="download-chart-btn", color="primary", style={"marginRight": "10px"}),
                dbc.Button("關閉", id="close-modal", n_clicks=0, color="secondary")
            ], style={"textAlign": "center"})
        ])
        
        return content, True, customer_info
    
    return dash.no_update, False, dash.no_update

# 下載圖表
@app.callback(
    [Output("download-chart", "data"),
     Output("restock-download-info-toast", "is_open")],
    Input("download-chart-btn", "n_clicks"),
    [State("timeline-chart", "figure"),
     State("detail-modal", "is_open"),
     State("customer-info-store", "data")],
    prevent_initial_call=True
)
def download_chart(n_clicks, figure, modal_open, customer_info):
    if n_clicks and figure and modal_open:
        if ctx.triggered_id == "download-chart-btn":
            try:
                import plotly.io as pio
                
                # 從 store 取得客戶資訊
                customer_id = customer_info.get('customer_id', '客戶')
                customer_name = customer_info.get('customer_name', '')
                
                # 組合檔名
                filename = f"{customer_id} - {customer_name} 歷史補貨紀錄.png"
                width = figure['layout']['width']
                img_bytes = pio.to_image(figure, format="png", width=width, height=300, scale=2)
                return dcc.send_bytes(img_bytes, filename), False
            except Exception as e:
                print(f"錯誤: {e}")
                return dash.no_update, False
    
    return dash.no_update, False

# 顯示下載中 toast
@app.callback(
    Output("restock-download-info-toast", "is_open", allow_duplicate=True),
    Input("download-chart-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_download_toast(n_clicks):
    if n_clicks:
        return True
    return dash.no_update

# 關閉 modal callback
@app.callback(
    Output("detail-modal", "is_open", allow_duplicate=True),
    Input("close-modal", "n_clicks"),
    prevent_initial_call=True
)
def close_modal(n_clicks):
    if n_clicks > 0:
        return False
    return dash.no_update

# 控制確認狀態按鈕的顯示和選擇數量顯示
@app.callback(
    [Output("confirm-status-btn", "style"),
     Output("selection-count-display", "children")],
    Input("checkbox-state-store", "data"),
    prevent_initial_call=True
)
def toggle_confirm_button_and_count_display(checkbox_state):
    # 從Store計算被選中的項目數量
    selected_count = 0
    if checkbox_state:
        for is_selected in checkbox_state.values():
            if is_selected:
                selected_count += 1
    
    if selected_count > 0:
        button_style = {"marginLeft": "10px", "display": "block"}
        count_text = f"已選擇 {selected_count} 個品項"
    else:
        button_style = {"marginLeft": "10px", "display": "none"}
        count_text = ""
    
    return button_style, count_text

# 同步checkbox狀態到全域Store
@app.callback(
    Output("checkbox-state-store", "data"),
    Input({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "value"),
    [State({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "id"),
     State("checkbox-state-store", "data")],
    prevent_initial_call=True
)
def sync_checkbox_state_to_store(checkbox_values, checkbox_ids, current_state):
    # 保留現有狀態，只更新當前畫面上的checkbox
    checkbox_state = current_state.copy() if current_state else {}
    
    if checkbox_values and checkbox_ids:
        for i, checkbox_value in enumerate(checkbox_values):
            if i < len(checkbox_ids):
                customer_id = checkbox_ids[i]['customer_id']
                row_index = checkbox_ids[i]['row_index']
                checkbox_key = f"{customer_id}-{row_index}"
                checkbox_state[checkbox_key] = bool(checkbox_value)
    
    return checkbox_state


# 打開確認狀態Modal
@app.callback(
    [Output("confirm-status-modal", "is_open"),
     Output("confirm-status-content", "children")],
    [Input("confirm-status-btn", "n_clicks"),
     Input("close-confirm-modal-btn", "n_clicks")],
    [State({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "value"),
     State("table-data-store", "data")],
    prevent_initial_call=True
)
def toggle_confirm_status_modal(open_clicks, close_clicks, checkbox_values, table_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, ""
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "confirm-status-btn":
        # 獲取被選中的項目資訊
        selected_items = []
        
        # 重新獲取最新的資料
        try:
            response = requests.get('http://127.0.0.1:8000/get_restock_data')
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                
                # 重新命名欄位
                df = df.rename(columns={
                    'customer_id': '客戶ID',
                    'customer_name': '客戶名稱',
                    'phone_number': '電話號碼',
                    'product_id': '商品ID',
                    'product_name': '商品名稱',
                    'prediction_date': '預計補貨日期',
                    'estimated_quantity': '預估數量',
                    'confidence_level': '信心度'
                })
                
                # 按客戶ID分組數據
                customer_groups = df.groupby(['客戶ID', '客戶名稱', '電話號碼'])
                
                # 遍歷checkbox值，找出被選中的項目
                checkbox_index = 0
                for (customer_id, customer_name, phone_number), group in customer_groups:
                    group = group.sort_values('預計補貨日期', ascending=False)
                    row_index = 0
                    
                    for _, row in group.iterrows():
                        if checkbox_index < len(checkbox_values) and checkbox_values[checkbox_index]:
                            # 這個checkbox被選中了
                            selected_items.append({
                                '客戶ID': customer_id,
                                '客戶名稱': customer_name,
                                '商品ID': row.get('商品ID', ''),
                                '商品名稱': row.get('商品名稱', ''),
                                '預測日期': row.get('預測日期', ''),
                                '預估數量': row.get('預估數量', ''),
                                '信心度': row.get('信心度', '')
                            })
                        checkbox_index += 1
                        row_index += 1
                        
        except Exception as e:
            print(f"[ERROR] 獲取選中項目時出錯: {e}")
        
        # 建立modal內容
        if selected_items:
            # 建立表格行
            table_rows = []
            for idx, item in enumerate(selected_items):
                table_row = html.Tr([
                    html.Td([
                        dcc.RadioItems(
                            id={'type': 'status-radio', 'index': idx},
                            options=[
                                {'label': '已補貨', 'value': 'restocked'},
                                {'label': '已取消', 'value': 'cancelled'}
                            ],
                            value=None,
                            inline=True,
                            style={'display': 'flex', 'justify-content': 'center', 'gap': '15px'}
                        )
                    ], style={
                        'padding': '10px', 
                        'text-align': 'center', 
                        'border': '1px solid #ddd',
                        'position': 'sticky',
                        'left': '0px',
                        'zIndex': 2,
                        'backgroundColor': 'white',
                        'boxShadow': '2px 0 5px rgba(0,0,0,0.1)',
                        'minWidth': '180px'
                    }),
                    html.Td(str(item['客戶ID']), style={'padding': '10px', 'text-align': 'center', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                    html.Td(str(item['客戶名稱']), style={'padding': '10px', 'text-align': 'center', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                    html.Td(str(item['商品ID']), style={'padding': '10px', 'text-align': 'center', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                    html.Td(str(item['商品名稱']), style={'padding': '10px', 'text-align': 'center', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                    html.Td(str(item['預測日期']), style={'padding': '10px', 'text-align': 'center', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                    html.Td(str(item['預估數量']), style={'padding': '10px', 'text-align': 'center', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                    html.Td(str(item['信心度']), style={'padding': '10px', 'text-align': 'center', 'border': '1px solid #ddd', 'white-space': 'nowrap'})
                ])
                table_rows.append(table_row)
            
            content = html.Div([
                html.Div([
                    html.Table([
                        html.Thead([
                            html.Tr([
                                html.Th('狀態', style={
                                    'font-weight': 'bold', 
                                    'padding': '10px', 
                                    'text-align': 'center', 
                                    'background-color': '#f8f9fa', 
                                    'border': '1px solid #ddd', 
                                    'white-space': 'nowrap',
                                    'position': 'sticky',
                                    'left': '0px',
                                    'zIndex': 3,
                                    'boxShadow': '2px 0 5px rgba(0,0,0,0.1)'
                                }),
                                html.Th('客戶ID', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                                html.Th('客戶名稱', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                                html.Th('商品ID', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                                html.Th('商品名稱', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                                html.Th('預測日期', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                                html.Th('預估數量', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border': '1px solid #ddd', 'white-space': 'nowrap'}),
                                html.Th('信心度', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border': '1px solid #ddd', 'white-space': 'nowrap'})
                            ])
                        ]),
                        html.Tbody(table_rows)
                    ], style={'border-collapse': 'collapse', 'width': '1200px', 'position': 'relative'})
                ], style={'overflow-x': 'auto', 'marginBottom': '20px', 'min-height': '25vh', 'max-height': '65vh', 'overflow-y': 'auto'}),
                html.Hr(),
                html.P("請為每個項目選擇狀態，然後點選「確認」按鈕", style={"marginTop": "20px"})
            ])
        else:
            content = html.Div([
                html.P("未找到選中的項目，請重新選擇。", style={"color": "red"})
            ])
        
        return True, content
    elif button_id == "close-confirm-modal-btn":
        return False, ""
    
    return dash.no_update, dash.no_update

# 處理確認狀態按鈕
@app.callback(
    Output("confirm-status-modal", "is_open", allow_duplicate=True),
    Input("confirm-status-btn-final", "n_clicks"),
    State({"type": "status-radio", "index": dash.ALL}, "value"),
    prevent_initial_call=True
)
def handle_final_confirm(confirm_clicks, radio_values):
    if confirm_clicks:
        # 處理每個項目的狀態
        for idx, status in enumerate(radio_values):
            if status:
                if status == 'restocked':
                    print(f"[DEBUG] 項目 {idx} 標記為已補貨")
                elif status == 'cancelled':
                    print(f"[DEBUG] 項目 {idx} 標記為已取消")
                # TODO: 實際的API調用來更新狀態
        
        # 執行操作後關閉modal
        return False
    return dash.no_update

register_offcanvas_callback(app, "restock_reminder")

# 搜尋功能callback - 整合到主要的accordion更新callback中
@app.callback(
    Output("restock-accordion", "children", allow_duplicate=True),
    [Input("restock_reminder-customer-id", "value"),
     Input("checkbox-state-store", "data")],
    [State("table-data-store", "data")],
    prevent_initial_call=True
)
def update_accordion_with_search_and_selection(selected_customer_id, checkbox_state, table_data):
    # 從Store狀態統計每個客戶的選中數量
    customer_counts = {}
    if checkbox_state:
        for checkbox_key, is_selected in checkbox_state.items():
            if is_selected:
                customer_id = checkbox_key.split('-')[0]
                if customer_id not in customer_counts:
                    customer_counts[customer_id] = 0
                customer_counts[customer_id] += 1

    # 重新獲取數據並重建 accordion
    try:
        response = requests.get('http://127.0.0.1:8000/get_restock_data')
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            # 如果有搜尋條件，過濾資料
            if selected_customer_id:
                df = df[df['customer_id'] == selected_customer_id]
            
            if df.empty:
                return []
            
            # 重新命名欄位
            df = df.rename(columns={
                'customer_id': '客戶ID',
                'customer_name': '客戶名稱',
                'phone_number': '電話號碼',
                'product_id': '商品ID',
                'product_name': '商品名稱',
                'prediction_date': '預計補貨日期',
                'estimated_quantity': '預估數量',
                'confidence_level': '信心度'
            })
            
            # 按客戶ID分組數據
            customer_groups = df.groupby(['客戶ID', '客戶名稱', '電話號碼'])
            
            # 創建Accordion
            accordions = []
            customer_index = 0
            for (customer_id, customer_name, phone_number), group in customer_groups:
                # 按預測日期排序
                group = group.sort_values('預計補貨日期', ascending=False)
                
                # 建立標題
                title_text = html.Span([
                    html.Span(customer_id, style={'color': 'black', 'fontWeight': 'bold'}),
                    html.Span(' '),
                    html.Span(customer_name, style={'color': 'black'}),
                    html.Span(f' ({phone_number})', style={'color': 'black'})
                ])
                
                # 建立accordion內容 - 表格標題
                table_header = html.Div([
                    html.Div('選擇', style={'font-weight': 'bold', 'flex': '0 0 60px', 'border-right': '1px solid #ddd', 'padding': '10px', 'border-left': '1px solid #ddd', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('商品ID', style={'font-weight': 'bold', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('商品名稱', style={'font-weight': 'bold', 'flex': '2', 'border-right': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('預計補貨日期', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('預估數量', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('信心度', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                    html.Div('操作', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1', 'padding': '10px', 'border-right': '1px solid #ddd', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'})
                ], style={'display': 'flex', 'background-color': '#f8f9fa', 'border-top': '1px solid #ddd', 'border-bottom': '1px solid #ddd', 'align-items': 'center'})
                
                # 建立資料行
                table_rows = []
                row_index = 0
                for _, row in group.iterrows():
                    # 從Store檢查此項目是否被選中
                    checkbox_key = f"{customer_id}-{row_index}"
                    checkbox_checked = []
                    if checkbox_state and checkbox_state.get(checkbox_key, False):
                        checkbox_checked = [checkbox_key]
                    
                    table_row = html.Div([
                        html.Div([
                            dcc.Checklist(
                                id={'type': 'restock-checkbox', 'customer_id': customer_id, 'row_index': row_index},
                                options=[{'label': '', 'value': f"{customer_id}-{row_index}"}],
                                value=checkbox_checked,
                                style={'margin': '0'}
                            )
                        ], style={'flex': '0 0 60px', 'border-right': '1px solid #ddd', 'border-left': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('商品ID', '')), style={'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('商品名稱', '')), style={'flex': '2', 'border-right': '1px solid #ddd', 'padding': '10px', 'text-align': 'center', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('預計補貨日期', '')), style={'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('預估數量', '')), style={'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div(str(row.get('信心度', '')), style={'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        html.Div([
                            dbc.Button("查看歷史補貨紀錄", 
                                     id={'type': 'view-button', 'index': customer_index},
                                     color="warning",
                                     size="sm",
                                     n_clicks=0,
                                     style={'fontSize': '16px', 'whiteSpace': 'nowrap'})
                        ], style={'text-align': 'center', 'flex': '1', 'border-right': '1px solid #ddd', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'})
                    ], style={'display': 'flex', 'background-color': 'white', 'border-bottom': '1px solid #ddd', 'align-items': 'center', 'min-height': '50px'})
                    
                    table_rows.append(table_row)
                    row_index += 1
                
                # 可滾動的內容區域
                scrollable_content = html.Div([
                    html.Div([
                        table_header
                    ], style={
                        'position': 'sticky',
                        'top': '0',
                        'z-index': '10',
                        'background-color': 'white',
                        'padding-right': '17px'
                    }),
                    html.Div(table_rows, style={
                        'max-height': '400px',
                        'overflow-y': 'auto',
                        'background-color': 'white'
                    })
                ], style={'background-color': 'white'})
                
                # 建立 Accordion Item 
                accordion_item = dbc.AccordionItem(
                    scrollable_content,
                    title=title_text,
                    item_id=f'accordion-{customer_id}'
                )
                
                accordions.append(accordion_item)
                customer_index += 1
            
            return accordions
        else:
            return []
    except Exception as e:
        return []

