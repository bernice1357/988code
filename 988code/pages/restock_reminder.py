from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from components.table import custom_table
import requests
import plotly.graph_objects as go
from dash import ctx
import dash_bootstrap_components as dbc

# TODO 差預計補貨日期欄位

# 信心度顏色映射函數
def get_confidence_color(confidence_level):
    """根據信心度返回對應的顏色"""
    colors = {
        'HIGH': '#28a745',    # 綠色
        'MEDIUM': '#ffc107',  # 橙色
        'LOW': '#dc3545'      # 紅色
    }
    if confidence_level:
        return colors.get(confidence_level.upper(), '#000000')  # 預設黑色
    return '#000000'

def calculate_restock_column_width(df, col):
    """計算補貨表格欄位的最適寬度"""
    # 計算標題寬度 (padding: 4px 8px = 16px)
    # 考慮中文字符較寬的問題
    col_str = str(col)
    char_width = sum(14 if ord(c) > 127 else 8 for c in col_str)  # 中文14px, 英文8px
    header_width = char_width + 16
    
    # 計算內容最大寬度
    max_content_width = 0
    for value in df[col]:
        value_str = str(value)
        value_char_width = sum(14 if ord(c) > 127 else 8 for c in value_str)  # 中文14px, 英文8px
        content_width = value_char_width + 16  # padding: 4px 8px = 16px
        max_content_width = max(max_content_width, content_width)
    
    # 取標題和內容的最大值，左右各加5px（總共15px），再加5px buffer，加2px邊框
    calculated_width = max(header_width, max_content_width) + 22
    return calculated_width

def create_restock_table(df, customer_index_start=0):
    """創建補貨提醒表格"""
    if df.empty:
        return html.Div("無資料"), pd.DataFrame()
    
    # 重設索引以確保 custom_table 正常運作
    df_reset = df.reset_index(drop=True)
    
    # 選擇要顯示的欄位（移除客戶名稱，加入商品名稱）
    display_columns = ['客戶ID', '預計補貨日期', '商品ID', '商品名稱', '預估數量', '信心度']
    df_display = df_reset[display_columns].copy()
    
    # 計算每個欄位的動態寬度
    column_widths = {}
    for col in display_columns:
        column_widths[col] = calculate_restock_column_width(df_display, col)
    
    # 客戶ID為固定列，需要特殊處理
    customer_id_width = column_widths['客戶ID']
    
    # 使用 custom_table 但需要手動創建以支援信心度顏色和特定 checkbox ID
    rows = []
    
    for i, row in df_display.iterrows():
        row_cells = []
        
        # Checkbox 欄位
        customer_id = row.get('客戶ID', '')
        row_index = i
        checkbox_key = f"{customer_id}-{row_index}"
        
        checkbox_cell = html.Td(
            dcc.Checklist(
                id={'type': 'restock-checkbox', 'customer_id': customer_id, 'row_index': row_index},
                options=[{'label': '', 'value': checkbox_key}],
                value=[],
                style={'margin': '0px'}
            ),
            style={
                'padding': '4px 8px',
                'textAlign': 'center',
                'fontSize': '16px',
                'height': '50px',
                'minWidth': '50px',
                'maxWidth': '50px',
                'position': 'sticky',
                'left': '0px',
                'zIndex': 90,  # 提高z-index
                'backgroundColor': '#edf7ff',
                'border': '1px solid #ccc',
                'boxShadow': '2px 0 5px rgba(0,0,0,0.1)'
            }
        )
        row_cells.append(checkbox_cell)
        
        # 客戶ID (sticky, 固定欄位) - 第一個欄位
        customer_id_cell = html.Td(
            str(customer_id),
            style={
                'padding': '4px 8px',
                'textAlign': 'center',
                'border': '1px solid #ccc',
                'fontSize': '16px',
                'height': '50px',
                'whiteSpace': 'nowrap',
                'position': 'sticky',
                'left': '50px',
                'zIndex': 89,  # 提高z-index
                'backgroundColor': '#edf7ff',
                'width': f'{customer_id_width}px',
                'minWidth': f'{customer_id_width}px',
                'maxWidth': f'{customer_id_width}px'
            }
        )
        row_cells.append(customer_id_cell)
        
        # 不再需要 popover 功能
        
        # 其他欄位（按順序：預計補貨日期、商品ID、商品名稱、預估數量）
        other_columns = ['預計補貨日期', '商品ID', '商品名稱', '預估數量']
        
        for col in other_columns:
            col_width = column_widths[col]
            cell = html.Td(
                str(row.get(col, '')),
                style={
                    'padding': '4px 8px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc',
                    'fontSize': '16px',
                    'height': '50px',
                    'whiteSpace': 'nowrap',
                    'backgroundColor': 'white',
                    'width': f'{col_width}px',
                    'minWidth': f'{col_width}px'
                }
            )
            row_cells.append(cell)
        
        # 信心度欄位 (帶顏色)
        confidence_level = row.get('信心度', '')
        confidence_color = get_confidence_color(confidence_level)
        confidence_width = column_widths['信心度']
        confidence_cell = html.Td(
            str(confidence_level),
            style={
                'padding': '4px 8px',
                'textAlign': 'center',
                'border': '1px solid #ccc',
                'fontSize': '16px',
                'height': '50px',
                'whiteSpace': 'nowrap',
                'backgroundColor': 'white',
                'width': f'{confidence_width}px',
                'minWidth': f'{confidence_width}px',
                'color': confidence_color,
                'fontWeight': 'bold'
            }
        )
        row_cells.append(confidence_cell)
        
        # 操作按鈕欄位
        button_cell = html.Td(
            html.Button(
                "查看歷史補貨紀錄",
                id={'type': 'view-button', 'index': customer_index_start + i},
                n_clicks=0,
                className="btn btn-warning btn-sm",
                style={'fontSize': '16px'}
            ),
            style={
                'padding': '4px 8px',
                'textAlign': 'center',
                'border': '1px solid #ccc',
                'fontSize': '16px',
                'height': '50px',
                'whiteSpace': 'nowrap',
                'position': 'sticky',
                'right': '0px',
                'zIndex': 88,  # 提高z-index
                'backgroundColor': 'white',
                'boxShadow': '-2px 0 5px rgba(0,0,0,0.1)',
                'width': '160px',
                'minWidth': '160px'
            }
        )
        row_cells.append(button_cell)
        
        # 添加行
        rows.append(html.Tr(row_cells, style={'backgroundColor': 'white'}))
    
    # 創建表格標頭
    headers = [
        html.Th('', style={
            "position": "sticky",
            "top": "0px",
            "left": "0px",
            "zIndex": 100,  # 提高z-index
            'backgroundColor': '#bcd1df',
            'fontWeight': 'bold',
            'fontSize': '16px',
            'padding': '4px 8px',
            'textAlign': 'center',
            'border': '1px solid #ccc',
            'width': '50px',
            'boxShadow': '2px 0 5px rgba(0,0,0,0.1)'
        }),
        html.Th('客戶ID', style={
            "position": "sticky",
            "top": "0px",
            "left": "50px",
            "zIndex": 99,  # 提高z-index
            'backgroundColor': '#bcd1df',
            'fontWeight': 'bold',
            'fontSize': '16px',
            'padding': '4px 8px',
            'textAlign': 'center',
            'border': '1px solid #ccc',
            'width': f'{customer_id_width}px',
            'minWidth': f'{customer_id_width}px'
        })
    ]
    
    # 其他標頭（按新的順序）
    other_header_columns = ['預計補貨日期', '商品ID', '商品名稱', '預估數量', '信心度']
    
    for header_text in other_header_columns:
        col_width = column_widths[header_text]
        headers.append(html.Th(header_text, style={
            "position": "sticky",
            "top": "0px",
            "zIndex": 50,  # 提高z-index
            'backgroundColor': '#bcd1df',
            'fontWeight': 'bold',
            'fontSize': '16px',
            'padding': '4px 8px',
            'textAlign': 'center',
            'border': '1px solid #ccc',
            'width': f'{col_width}px',
            'minWidth': f'{col_width}px'
        }))
    
    # 操作欄標頭
    headers.append(html.Th('操作', style={
        "position": "sticky",
        "top": "0px",
        "right": "0px",
        "zIndex": 98,  # 提高z-index
        'backgroundColor': '#bcd1df',
        'fontWeight': 'bold',
        'fontSize': '16px',
        'padding': '4px 8px',
        'textAlign': 'center',
        'border': '1px solid #ccc',
        'whiteSpace': 'nowrap',
        'boxShadow': '-2px 0 5px rgba(0,0,0,0.1)',
        'width': '160px',
        'minWidth': '160px'
    }))
    
    # 創建完整表格
    table = html.Table([
        html.Thead([html.Tr(headers)]),
        html.Tbody(rows)
    ], style={
        "width": "max-content",
        "minWidth": "100%",
        "borderCollapse": "collapse",
        'border': '1px solid #ccc'
    })

    table_div = html.Div([
        html.Div([table], style={
            'overflowX': 'auto',
            'overflowY': 'auto',
            'maxHeight': '76vh',
            'minHeight': '76vh',
            'position': 'relative',
            'width': '100%',
            'contain': 'layout'
        })
    ], style={
        'width': '100%',
        'maxWidth': '100%',
        'position': 'relative'
    })
    
    return table_div, df_reset

# offcanvas
product_input_fields = [
    {
        "id": "customer-id", 
        "label": "客戶ID",
        "type": "dropdown"
    },
    {
        "id": "prediction-date", 
        "label": "預計補貨日期",
        "type": "date"
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
    # 儲存checkbox選擇狀態 - 只在搜尋條件改變時更新
    dcc.Store(id="checkbox-state-store", data={}),
    # 儲存選中的項目資訊
    dcc.Store(id="selected-items-store", data=[]),
    
    # 觸發 Offcanvas 的按鈕和確認狀態按鈕
    html.Div([
        restock_offcanvas["trigger_button"],
        dbc.Button(
            "確認補貨狀態",
            id="confirm-status-btn",
            color="success",
            style={"marginLeft": "10px", "display": "none"}  # 預設隱藏
        ),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}),
    
    error_toast("restock-reminder", message=""),
    success_toast("restock-reminder", message=""),
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
                    dbc.Button("確認", id="confirm-status-btn-final", color="success", className="me-2", disabled=True),
                    dbc.Button("取消", id="close-confirm-modal-btn", color="secondary")
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

# 重新載入資料的輔助函數
def reload_table_data():
    """重新載入表格資料並返回表格內容和資料"""
    try:
        response = requests.get('http://127.0.0.1:8000/get_restock_data')
        if response.status_code != 200:
            return None, [], True, "無法獲取資料"
        
        data = response.json()
        df = pd.DataFrame(data)
        
        if df.empty:
            return html.Div("無資料", className="text-center text-muted", style={"padding": "50px"}), [], False, ""
        
        # 重新命名欄位
        df = df.rename(columns={
            'prediction_id': '預測ID',
            'customer_id': '客戶ID',
            'customer_name': '客戶名稱',
            'phone_number': '電話號碼',
            'product_id': '商品ID',
            'product_name': '商品名稱',
            'prediction_date': '預計補貨日期',
            'estimated_quantity': '預估數量',
            'confidence_level': '信心度'
        })
        
        # 按預計補貨日期和客戶名稱排序
        df = df.sort_values(['預計補貨日期', '客戶名稱'], ascending=[True, True])
        
        # 按預計補貨日期和客戶名稱排序
        df = df.sort_values(['預計補貨日期', '客戶名稱'], ascending=[True, True])
        
        # 創建一般表格（不用 accordion 分組）
        table, all_records = create_restock_table(df, 0)
        
        # 將記錄轉換為 modal 使用的格式
        records_for_modal = []
        for _, row in all_records.iterrows():
            record_for_modal = {
                '客戶ID': row.get('客戶ID', ''),
                '客戶名稱': row.get('客戶名稱', '')
            }
            records_for_modal.append(record_for_modal)
        
        return table, records_for_modal, False, ""
    
    except Exception as e:
        print(f"[ERROR] 載入資料時發生錯誤: {e}")
        return None, [], True, f"載入資料失敗: {str(e)}"

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
                'prediction_id': '預測ID',
                'customer_id': '客戶ID',
                'customer_name': '客戶名稱',
                'phone_number': '電話號碼',
                'product_id': '商品ID',
                'product_name': '商品名稱',
                'prediction_date': '預計補貨日期',
                'estimated_quantity': '預估數量',
                'confidence_level': '信心度'
            })
            
            # 按預計補貨日期和客戶名稱排序
            df = df.sort_values(['預計補貨日期', '客戶名稱'], ascending=[True, True])
            
            # 創建一般表格（不用 accordion 分組）
            table, all_records = create_restock_table(df, 0)
            
            # 將記錄轉換為 modal 使用的格式
            records_for_modal = []
            for _, row in all_records.iterrows():
                record_for_modal = {
                    '客戶ID': row.get('客戶ID', ''),
                    '客戶名稱': row.get('客戶名稱', '')
                }
                records_for_modal.append(record_for_modal)
            
            return table, records_for_modal, False, ""
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

# 控制確認狀態按鈕的顯示
@app.callback(
    Output("confirm-status-btn", "style"),
    Input({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "value"),
    prevent_initial_call=True
)
def toggle_confirm_button(checkbox_values):
    # 檢查是否有任何checkbox被選中
    has_selection = False
    if checkbox_values:
        for checkbox_value in checkbox_values:
            # checkbox_value 是陣列，檢查是否非空
            if checkbox_value and len(checkbox_value) > 0:
                has_selection = True
                break
    
    if has_selection:
        return {"marginLeft": "10px", "display": "block"}
    else:
        return {"marginLeft": "10px", "display": "none"}



# 打開確認狀態Modal
@app.callback(
    [Output("confirm-status-modal", "is_open"),
     Output("confirm-status-content", "children"),
     Output("selected-items-store", "data")],
    [Input("confirm-status-btn", "n_clicks"),
     Input("close-confirm-modal-btn", "n_clicks")],
    [State({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "value"),
     State({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "id"),
     State("checkbox-state-store", "data"),
     State("restock_reminder-customer-id", "value"),
     State("restock_reminder-prediction-date", "value")],
    prevent_initial_call=True
)
def toggle_confirm_status_modal(open_clicks, close_clicks, checkbox_values, checkbox_ids, checkbox_state, customer_search_value, date_search_value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, ""
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "confirm-status-btn":
        # 先更新Store狀態 - 保存當前畫面的checkbox狀態到Store
        current_checkbox_state = checkbox_state.copy() if checkbox_state else {}
        if checkbox_values and checkbox_ids:
            for i, checkbox_value in enumerate(checkbox_values):
                if i < len(checkbox_ids):
                    customer_id = checkbox_ids[i]['customer_id']
                    row_index = checkbox_ids[i]['row_index']
                    checkbox_key = f"{customer_id}-{row_index}"
                    # checkbox_value 是陣列，檢查是否包含 checkbox_key
                    is_checked = checkbox_key in (checkbox_value or [])
                    current_checkbox_state[checkbox_key] = is_checked
                    # if is_checked:
                        # print(f"[DEBUG] 勾選的項目: {checkbox_key}")  # 暫時註解
                    # print(f"[DEBUG] checkbox_ids[{i}]: customer_id={customer_id}, row_index={row_index}, checkbox_value={checkbox_value}")  # 暫時註解
        
        # print(f"[DEBUG] 總共有 {sum(current_checkbox_state.values())} 個項目被勾選")  # 暫時註解
        # print(f"[DEBUG] 所有 checkbox 狀態: {current_checkbox_state}")  # 暫時註解
        
        # 獲取被選中的項目資訊 - 從Store中的所有勾選狀態收集
        selected_items = []
        
        # 重新獲取最新的資料
        try:
            response = requests.get('http://127.0.0.1:8000/get_restock_data')
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                
                # 重新命名欄位
                df = df.rename(columns={
                    'prediction_id': '預測ID',
                    'customer_id': '客戶ID',
                    'customer_name': '客戶名稱',
                    'phone_number': '電話號碼',
                    'product_id': '商品ID',
                    'product_name': '商品名稱',
                    'prediction_date': '預計補貨日期',
                    'estimated_quantity': '預估數量',
                    'confidence_level': '信心度'
                })
                
                # 應用相同的搜尋條件篩選
                if customer_search_value:
                    df = df[df['客戶ID'] == customer_search_value]
                
                if date_search_value:
                    df = df[df['預計補貨日期'] == date_search_value]
                
                # 如果篩選後沒有資料，直接返回空的 selected_items
                if df.empty:
                    selected_items = []
                else:
                    # 按預計補貨日期和客戶名稱排序（與主要顯示邏輯一致）
                    df = df.sort_values(['預計補貨日期', '客戶名稱'], ascending=[True, True])
                    df_reset = df.reset_index(drop=True)
                    
                    # 根據Store中的勾選狀態收集所有選中的項目
                    if current_checkbox_state:
                        for row_index, (_, row) in enumerate(df_reset.iterrows()):
                            customer_id = row.get('客戶ID', '')
                            checkbox_key = f"{customer_id}-{row_index}"
                            if current_checkbox_state.get(checkbox_key, False):  # 如果這個項目被勾選
                                selected_items.append({
                                    '預測ID': row.get('預測ID', ''),
                                    '客戶ID': customer_id,
                                    '商品ID': row.get('商品ID', ''),
                                    '商品名稱': row.get('商品名稱', ''),
                                    '預測日期': row.get('預計補貨日期', ''),
                                    '預估數量': row.get('預估數量', ''),
                                    '信心度': row.get('信心度', '')
                                })
                        
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
                                {'label': '已補貨', 'value': 'fulfilled'},
                                {'label': '已取消', 'value': 'cancelled'}
                            ],
                            value=None,
                            inline=True,
                            style={'display': 'flex', 'justify-content': 'center', 'gap': '15px'}
                        )
                    ], style={
                        'padding': '10px', 
                        'text-align': 'center', 
                        'border-bottom': '1px solid #eee',
                        'position': 'sticky',
                        'left': '0px',
                        'zIndex': 2,
                        'backgroundColor': 'white',
                        'boxShadow': '2px 0 5px rgba(0,0,0,0.1)',
                        'minWidth': '180px'
                    }),
                    html.Td(str(item['客戶ID']), style={'padding': '10px', 'text-align': 'center', 'border-bottom': '1px solid #eee', 'white-space': 'nowrap'}),
                    html.Td(str(item['商品ID']), style={'padding': '10px', 'text-align': 'center', 'border-bottom': '1px solid #eee', 'white-space': 'nowrap'}),
                    html.Td(str(item['商品名稱']), style={'padding': '10px', 'text-align': 'center', 'border-bottom': '1px solid #eee', 'white-space': 'nowrap'}),
                    html.Td(str(item['預測日期']), style={'padding': '10px', 'text-align': 'center', 'border-bottom': '1px solid #eee', 'white-space': 'nowrap'}),
                    html.Td(str(item['預估數量']), style={'padding': '10px', 'text-align': 'center', 'border-bottom': '1px solid #eee', 'white-space': 'nowrap'}),
                    html.Td(str(item['信心度']), style={'padding': '10px', 'text-align': 'center', 'border-bottom': '1px solid #eee', 'white-space': 'nowrap', 'color': get_confidence_color(item['信心度']), 'fontWeight': 'bold'})
                ], style={'background-color': 'white'})
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
                                    'border-bottom': '1px solid #ddd',
                                    'white-space': 'nowrap',
                                    'position': 'sticky',
                                    'top': '0px',
                                    'left': '0px',
                                    'zIndex': 3,
                                    'boxShadow': '2px 0 5px rgba(0,0,0,0.1)'
                                }),
                                html.Th('客戶ID', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border-bottom': '1px solid #ddd', 'white-space': 'nowrap', 'position': 'sticky', 'top': '0px', 'zIndex': 2}),
                                html.Th('商品ID', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border-bottom': '1px solid #ddd', 'white-space': 'nowrap', 'position': 'sticky', 'top': '0px', 'zIndex': 2}),
                                html.Th('商品名稱', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border-bottom': '1px solid #ddd', 'white-space': 'nowrap', 'position': 'sticky', 'top': '0px', 'zIndex': 2}),
                                html.Th('預計補貨日期', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border-bottom': '1px solid #ddd', 'white-space': 'nowrap', 'position': 'sticky', 'top': '0px', 'zIndex': 2}),
                                html.Th('預估數量', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border-bottom': '1px solid #ddd', 'white-space': 'nowrap', 'position': 'sticky', 'top': '0px', 'zIndex': 2}),
                                html.Th('信心度', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border-bottom': '1px solid #ddd', 'white-space': 'nowrap', 'position': 'sticky', 'top': '0px', 'zIndex': 2})
                            ])
                        ]),
                        html.Tbody(table_rows)
                    ], style={
                        'border-collapse': 'collapse', 
                        'width': '1200px', 
                        'position': 'relative'
                    })
                ], style={
                    'overflow-x': 'auto', 
                    'overflow-y': 'auto',
                    'marginBottom': '20px', 
                    'min-height': '25vh', 
                    'max-height': '60vh',
                    'border': '1px solid #dee2e6',
                    'border-radius': '0.375rem',
                    'position': 'relative'
                }),
                html.Hr(),
                html.P("請為每個項目選擇補貨狀態，然後點選「確認」按鈕", style={"marginTop": "20px"})
            ])
        else:
            content = html.Div([
                html.P("未找到選中的項目，請重新選擇。", style={"color": "red"})
            ])
            selected_items = []
        
        return True, content, selected_items
    elif button_id == "close-confirm-modal-btn":
        return False, "", dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update

# 控制確認按鈕的啟用狀態
@app.callback(
    Output("confirm-status-btn-final", "disabled"),
    Input({"type": "status-radio", "index": dash.ALL}, "value"),
    prevent_initial_call=True
)
def toggle_confirm_button(radio_values):
    # 檢查是否所有 RadioItems 都已選擇
    if not radio_values:
        return True  # 沒有任何 RadioItems 時保持 disabled
    
    # 檢查是否每個 RadioItem 都有值（不是 None）
    all_selected = all(value is not None for value in radio_values)
    return not all_selected  # 如果全部選擇則啟用（disabled=False），否則保持禁用

# 設置確認按鈕的載入狀態
@app.callback(
    Output("confirm-status-btn-final", "loading"),
    Input("confirm-status-btn-final", "n_clicks"),
    prevent_initial_call=True
)
def set_loading_state(n_clicks):
    if n_clicks:
        return True
    return dash.no_update

# 處理確認狀態按鈕
@app.callback(
    [Output("confirm-status-modal", "is_open", allow_duplicate=True),
     Output("restock-reminder-success-toast", "is_open"),
     Output("restock-reminder-success-toast", "children"),
     Output("restock-reminder-error-toast", "is_open", allow_duplicate=True),
     Output("restock-reminder-error-toast", "children", allow_duplicate=True),
     Output("table-container", "children", allow_duplicate=True),
     Output("table-data-store", "data", allow_duplicate=True),
     Output("confirm-status-btn-final", "loading", allow_duplicate=True)],
    Input("confirm-status-btn-final", "n_clicks"),
    [State({"type": "status-radio", "index": dash.ALL}, "value"),
     State("selected-items-store", "data")],
    prevent_initial_call=True
)
def handle_final_confirm(confirm_clicks, radio_values, selected_items_from_store):
    if confirm_clicks:
        try:
            # 直接使用從 Store 中獲取的選中項目
            selected_items = selected_items_from_store or []
            
            # 處理每個項目的狀態
            success_count = 0
            failed_count = 0
            
            for idx, status in enumerate(radio_values):
                if status and idx < len(selected_items):
                    item = selected_items[idx]
                    prediction_id = item['預測ID']
                    print(f"[DEBUG] 處理項目 {idx}: prediction_id={prediction_id}, status={status}, type={type(prediction_id)}")
                    
                    # 確保 prediction_id 是整數
                    if isinstance(prediction_id, str):
                        try:
                            prediction_id = int(prediction_id)
                        except ValueError:
                            print(f"[ERROR] 無法轉換 prediction_id 為整數: {prediction_id}")
                            failed_count += 1
                            continue
                    
                    try:
                        # 調用 API 更新狀態
                        payload = {
                            'prediction_id': prediction_id,
                            'prediction_status': status,
                            'user_role': 'editor'
                        }
                        print(f"[DEBUG] 發送 API 請求: {payload}")
                        
                        update_response = requests.put(
                            'http://127.0.0.1:8000/update_restock_prediction_status',
                            json=payload,
                            timeout=30  # 加上逾時設定
                        )
                        
                        print(f"[DEBUG] API 回應狀態碼: {update_response.status_code}")
                        if update_response.status_code != 200:
                            print(f"[DEBUG] API 回應內容: {update_response.text}")
                        
                        if update_response.status_code == 200:
                            success_count += 1
                        else:
                            failed_count += 1
                            
                    except requests.exceptions.Timeout:
                        print(f"[ERROR] API 請求逾時: prediction_id={prediction_id}")
                        failed_count += 1
                    except Exception as api_error:
                        print(f"[ERROR] API 調用失敗: {api_error}")
                        failed_count += 1
            
            # 先關閉 modal 並顯示 toast，然後重新載入資料
            if failed_count == 0:
                # 重新載入表格資料
                refreshed_table, refreshed_data, error_flag, error_msg = reload_table_data()
                return False, True, f"成功更新 {success_count} 筆記錄", False, "", refreshed_table, refreshed_data, False
            elif success_count == 0:
                return False, False, "", True, f"更新失敗，請洽資訊人員", dash.no_update, dash.no_update, False
            else:
                # 重新載入表格資料
                refreshed_table, refreshed_data, error_flag, error_msg = reload_table_data()
                return False, True, f"成功更新 {success_count} 筆，失敗 {failed_count} 筆", False, "", refreshed_table, refreshed_data, False
            
        except Exception as e:
            print(f"[ERROR] 處理確認狀態時發生錯誤: {e}")
            return False, False, "", True, f"處理過程中發生錯誤: {str(e)}", dash.no_update, dash.no_update, False
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# 輕量的checkbox同步機制 - 只在需要時更新Store
@app.callback(
    Output("checkbox-state-store", "data", allow_duplicate=True),
    Input({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "value"),
    [State({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "id"),
     State("checkbox-state-store", "data"),
     State("restock_reminder-customer-id", "value"),
     State("restock_reminder-prediction-date", "value")],
    prevent_initial_call=True
)
def sync_checkbox_to_store_on_change(checkbox_values, checkbox_ids, current_state, customer_search_value, date_search_value):
    # 只有在沒有搜尋條件時才同步，避免與搜尋callback衝突
    if customer_search_value or date_search_value:
        return dash.no_update
    
    # 更新Store中的checkbox狀態
    updated_state = current_state.copy() if current_state else {}
    
    if checkbox_values and checkbox_ids:
        for i, checkbox_value in enumerate(checkbox_values):
            if i < len(checkbox_ids):
                customer_id = checkbox_ids[i]['customer_id']
                row_index = checkbox_ids[i]['row_index']
                checkbox_key = f"{customer_id}-{row_index}"
                # checkbox_value 是陣列，檢查是否包含 checkbox_key
                updated_state[checkbox_key] = checkbox_key in (checkbox_value or [])
    
    return updated_state

register_offcanvas_callback(app, "restock_reminder")

# 搜尋功能callback
@app.callback(
    [Output("table-container", "children", allow_duplicate=True),
     Output("checkbox-state-store", "data", allow_duplicate=True)],
    [Input("restock_reminder-customer-id", "value"),
     Input("restock_reminder-prediction-date", "value")],
    [State({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "value"),
     State({"type": "restock-checkbox", "customer_id": dash.ALL, "row_index": dash.ALL}, "id"),
     State("checkbox-state-store", "data")],
    prevent_initial_call=True
)
def update_accordion_with_search(selected_customer_id, selected_date, checkbox_values, checkbox_ids, current_checkbox_state):
    # 先保存當前的checkbox狀態到Store
    updated_checkbox_state = current_checkbox_state.copy() if current_checkbox_state else {}
    
    # 更新Store中的checkbox狀態
    if checkbox_values and checkbox_ids:
        for i, checkbox_value in enumerate(checkbox_values):
            if i < len(checkbox_ids):
                customer_id = checkbox_ids[i]['customer_id']
                row_index = checkbox_ids[i]['row_index']
                checkbox_key = f"{customer_id}-{row_index}"
                # checkbox_value 是陣列，檢查是否包含 checkbox_key
                updated_checkbox_state[checkbox_key] = checkbox_key in (checkbox_value or [])
    
    # 重新獲取數據並重建 accordion
    try:
        response = requests.get('http://127.0.0.1:8000/get_restock_data')
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            # 如果有搜尋條件，過濾資料
            if selected_customer_id:
                df = df[df['customer_id'] == selected_customer_id]
            
            if selected_date:
                df = df[df['prediction_date'] == selected_date]
            
            if df.empty:
                return html.Div("無符合條件的資料", className="text-center text-muted", style={"padding": "50px"}), updated_checkbox_state
            
            # 重新命名欄位
            df = df.rename(columns={
                'prediction_id': '預測ID',
                'customer_id': '客戶ID',
                'customer_name': '客戶名稱',
                'phone_number': '電話號碼',
                'product_id': '商品ID',
                'product_name': '商品名稱',
                'prediction_date': '預計補貨日期',
                'estimated_quantity': '預估數量',
                'confidence_level': '信心度'
            })
            
            # 按預計補貨日期和客戶名稱排序
            df = df.sort_values(['預計補貨日期', '客戶名稱'], ascending=[True, True])
            
            # 顯示所有資料
            
            # 創建一般表格
            table, _ = create_restock_table(df, 0)
            
            return table, updated_checkbox_state
        else:
            return html.Div("無法載入資料"), updated_checkbox_state
    except Exception as e:
        return html.Div(f"載入錯誤: {str(e)}"), updated_checkbox_state

