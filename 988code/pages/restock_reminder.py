from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from components.table import custom_table
import requests
import re
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

def get_optimized_column_widths():
    """獲取優化的固定欄位寬度，避免重複計算"""
    return {
        '客戶ID': 100,
        '預計補貨日期': 120,
        '商品ID': 120,
        '商品名稱': 200,
        '預估數量': 100,
        '信心度': 80
    }

def create_loading_skeleton():
    """創建載入骨架畫面"""
    skeleton_rows = []
    for i in range(10):  # 顯示10行骨架
        skeleton_cells = []
        # Checkbox 欄位
        skeleton_cells.append(html.Td(
            html.Div(style={
                'width': '20px', 'height': '20px', 
                'backgroundColor': '#e0e0e0', 
                'borderRadius': '3px',
                'margin': 'auto'
            }),
            style={'padding': '8px', 'textAlign': 'center', 'width': '50px'}
        ))
        
        # 其他欄位
        widths = [100, 120, 120, 200, 100, 80, 100]
        for width in widths:
            skeleton_cells.append(html.Td(
                html.Div(style={
                    'width': f'{width-20}px', 'height': '16px',
                    'backgroundColor': '#e0e0e0',
                    'borderRadius': '4px',
                    'margin': 'auto'
                }),
                style={'padding': '8px', 'textAlign': 'center', 'width': f'{width}px'}
            ))
        
        skeleton_rows.append(html.Tr(skeleton_cells))
    
    return html.Div([
        html.Table([
            html.Tbody(skeleton_rows)
        ], className="table table-striped", style={'marginBottom': '0px'}),
        html.Div("載入中...", style={'textAlign': 'center', 'padding': '20px', 'color': '#6c757d'})
    ])

def filter_history_by_product(history_df, product_id, product_name):
    """依照商品資訊過濾歷史補貨資料"""
    if history_df is None or history_df.empty:
        return history_df

    df = history_df.copy()
    product_id_value = str(product_id).strip().lower() if product_id else ""
    product_name_value = str(product_name).strip() if product_name else ""

    if product_id_value and 'product_id' in df.columns:
        comparison = df['product_id'].astype(str).str.strip().str.lower()
        filtered = df[comparison == product_id_value]
        if not filtered.empty:
            return filtered

    if product_name_value and 'product_name' in df.columns:
        name_series = df['product_name'].astype(str).str.strip()
        name_casefold = name_series.str.casefold()
        search_candidates = [product_name_value]
        if ' ' in product_name_value:
            search_candidates.append(product_name_value.split(' ', 1)[1].strip())
        search_candidates = [candidate for candidate in search_candidates if candidate]
        search_candidates = list(dict.fromkeys(search_candidates))

        for candidate in search_candidates:
            candidate_casefold = candidate.casefold()
            exact_mask = name_casefold == candidate_casefold
            filtered = df[exact_mask]
            if not filtered.empty:
                return filtered

        for candidate in search_candidates:
            escaped = re.escape(candidate)
            partial_mask = name_series.str.contains(escaped, case=False, na=False)
            filtered = df[partial_mask]
            if not filtered.empty:
                return filtered

        for candidate in search_candidates:
            candidate_casefold = candidate.casefold()
            reverse_mask = name_casefold.apply(lambda x: bool(x) and x in candidate_casefold)
            filtered = df[reverse_mask]
            if not filtered.empty:
                return filtered

    return df

def sanitize_filename_component(value):
    """將檔名不支援的字元替換為底線"""
    if not value:
        return ""
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', str(value))
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    return sanitized

def create_restock_table(df, customer_index_start=0):
    """創建補貨提醒表格 - 優化版本"""
    if df.empty:
        return html.Div("無資料"), pd.DataFrame()
    
    # 重設索引以確保 custom_table 正常運作
    df_reset = df.reset_index(drop=True)
    
    # 選擇要顯示的欄位（移除客戶名稱，加入商品名稱）
    display_columns = ['客戶ID', '預計補貨日期', '商品ID', '商品名稱', '預估數量', '信心度']
    df_display = df_reset[display_columns].copy()
    
    # 使用優化的固定寬度
    column_widths = get_optimized_column_widths()
    customer_id_width = column_widths['客戶ID']
    
    # 使用優化的表格創建邏輯
    rows = []
    
    # 預定義樣式以減少重複創建
    base_cell_style = {
        'padding': '8px 12px',
        'border': '1px solid #ddd',
        'fontSize': '14px',
        'height': '45px',
        'whiteSpace': 'nowrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    }
    
    checkbox_style = {
        **base_cell_style,
        'textAlign': 'center',
        'width': '50px',
        'position': 'sticky',
        'left': '0px',
        'zIndex': 90,
        'backgroundColor': '#f8f9fa'
    }
    
    sticky_style = {
        **base_cell_style,
        'position': 'sticky',
        'left': '50px',
        'zIndex': 89,
        'backgroundColor': '#f8f9fa',
        'fontWeight': 'bold'
    }
    
    for i, row in df_display.iterrows():
        row_cells = []
        
        # 簡化的 Checkbox 欄位
        customer_id = row.get('客戶ID', '')
        checkbox_cell = html.Td(
            dcc.Checklist(
                id={'type': 'restock-checkbox', 'customer_id': customer_id, 'row_index': i},
                options=[{'label': '', 'value': f"{customer_id}-{i}"}],
                value=[],
                style={'margin': '0px'}
            ),
            style=checkbox_style
        )
        row_cells.append(checkbox_cell)
        
        # 客戶ID (sticky 欄位)
        customer_id_cell = html.Td(
            str(customer_id),
            style={**sticky_style, 'width': f'{customer_id_width}px'}
        )
        row_cells.append(customer_id_cell)
        
        # 其他欄位（優化迴圈）
        other_columns = ['預計補貨日期', '商品ID', '商品名稱', '預估數量']
        for col in other_columns:
            cell = html.Td(
                str(row.get(col, '')),
                style={**base_cell_style, 'width': f'{column_widths[col]}px', 'textAlign': 'center'}
            )
            row_cells.append(cell)
        
        # 信心度欄位 (帶顏色)
        confidence_level = row.get('信心度', '')
        confidence_color = get_confidence_color(confidence_level)
        confidence_cell = html.Td(
            str(confidence_level),
            style={
                **base_cell_style,
                'width': f'{column_widths["信心度"]}px',
                'textAlign': 'center',
                'color': confidence_color,
                'fontWeight': 'bold'
            }
        )
        row_cells.append(confidence_cell)
        
        # 簡化的操作按鈕
        button_cell = html.Td(
            html.Button(
                "查看歷史補貨紀錄",
                id={'type': 'view-button', 'index': customer_index_start + i},
                className="btn btn-warning btn-sm",
                style={
                    'fontSize': '16px'
                }
            ),
            style={**base_cell_style, 'width': '100px', 'textAlign': 'center'}
        )
        row_cells.append(button_cell)
        
        # 添加行
        rows.append(html.Tr(row_cells, style={'backgroundColor': 'white'}))
    
    # 創建表格標頭
    headers = [
        html.Th('', style={
            "position": "sticky",
            "top": "-1px",
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
            "top": "-1px",
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
            "top": "-1px",
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
        "top": "-1px",
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
        html.Thead([html.Tr(headers)], style={
            'margin': '0',
            'padding': '0',
            'lineHeight': '1',
            "borderSpacing": "0",
            "borderCollapse": "collapse"
        }),
        html.Tbody(rows, style={
            'margin': '0',
            'padding': '0'
        })
    ], style={
        "width": "max-content",
        "minWidth": "100%",
        "borderCollapse": "collapse",
        'border': '1px solid #ccc',
        'margin': '0',
        'padding': '0',
        "borderSpacing": "0px",
        "border": "none"
    })

    table_div = html.Div([
    html.Div([table], style={
            'overflowX': 'auto',
            'overflowY': 'auto',
            'maxHeight': '76vh',
            'minHeight': '76vh',
            'position': 'relative',
            'width': '100%',
            'contain': 'layout',
            'margin': '0',
            'padding': '0'
        })
    ], style={
        'width': '100%',
        'maxWidth': '100%',
        'position': 'relative',
        'border': '2px solid #dee2e6',
        'borderRadius': '8px',
        'padding': '0',
        'margin': '0',
        'lineHeight': '0',
        'fontSize': '0',
        'boxSizing': 'border-box',
        'background': 'white'
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
            "取消補貨狀態",
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
            dbc.ModalHeader(dbc.ModalTitle("取消補貨狀態")),
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
                '客戶名稱': row.get('客戶名稱', ''),
                '商品ID': row.get('商品ID', ''),
                '商品名稱': row.get('商品名稱', ''),
                '預計補貨日期': row.get('預計補貨日期', '')
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
    # 立即返回載入骨架，提供即時反饋
    if page_loaded is None:
        return create_loading_skeleton(), [], False, ""
    
    try:
        # 使用分頁參數載入數據
        response = requests.get('http://127.0.0.1:8000/get_restock_data', 
                              params={'limit': 50, 'offset': 0}, 
                              timeout=10)  # 添加超時
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', [])
            
            if not data:
                return html.Div("暫無資料", style={'textAlign': 'center', 'padding': '50px'}), [], False, ""
            
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
            
            # 創建優化的表格
            table, all_records = create_restock_table(df, 0)
            
            # 簡化 modal 記錄準備
            records_for_modal = [
                {
                    '客戶ID': row.get('客戶ID', ''),
                    '客戶名稱': row.get('客戶名稱', ''),
                    '商品ID': row.get('商品ID', ''),
                    '商品名稱': row.get('商品名稱', ''),
                    '預計補貨日期': row.get('預計補貨日期', '')
                }
                for _, row in all_records.iterrows()
            ]
            
            return table, records_for_modal, False, ""
        else:
            error_msg = f"API 請求失敗：{response.status_code}"
            return html.Div(f"載入失敗: {error_msg}", style={'textAlign': 'center', 'padding': '50px', 'color': 'red'}), [], True, error_msg
    except requests.exceptions.Timeout:
        error_msg = "請求超時，請稍後再試"
        return html.Div(error_msg, style={'textAlign': 'center', 'padding': '50px', 'color': 'orange'}), [], True, error_msg
    except Exception as ex:
        error_msg = f"載入錯誤：{str(ex)}"
        return html.Div(error_msg, style={'textAlign': 'center', 'padding': '50px', 'color': 'red'}), [], True, error_msg

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
    
    # 檢查是否有觸發事件且不是初始化
    if not triggered or not view_clicks:
        return dash.no_update, False, dash.no_update
    
    # 檢查觸發的按鈕是否真的被點擊（n_clicks > 0）
    if triggered is not None:
        idx = triggered["index"]
        # 確保對應的按鈕確實有被點擊
        if (idx < len(view_clicks) and view_clicks[idx] is not None and view_clicks[idx] > 0):
            row = table_data[idx]
            customer_id = row['客戶ID']
            customer_name = row['客戶名稱']
            product_id = row.get('商品ID', '')
            product_name = row.get('商品名稱', '')

            product_id_str = str(product_id).strip() if product_id else ""
            product_name_str = str(product_name).strip() if product_name else ""
            product_label = " ".join(part for part in [product_id_str, product_name_str] if part)

            customer_info = {
                'customer_id': customer_id,
                'customer_name': customer_name,
                'product_id': product_id_str,
                'product_name': product_name_str
            }

            try:
                params = {}
                if product_id_str:
                    params['product_id'] = product_id_str
                response = requests.get(f'http://127.0.0.1:8000/get_restock_history/{customer_id}', params=params if params else None)
                if response.status_code == 200:
                    history_data = response.json()
                    history_df = pd.DataFrame(history_data)

                    filtered_df = filter_history_by_product(history_df, product_id_str, product_name_str)

                    if filtered_df.empty:
                        label_for_message = product_label or "該品項"
                        timeline_chart = html.Div(f"{label_for_message} 目前沒有歷史補貨紀錄", style={"textAlign": "center", "padding": "20px"})
                    elif 'transaction_date' not in filtered_df.columns:
                        timeline_chart = html.Div("歷史資料缺少日期欄位", style={"textAlign": "center", "padding": "20px"})
                    else:
                        filtered_df = filtered_df.copy()
                        filtered_df['transaction_date'] = pd.to_datetime(filtered_df['transaction_date'])

                        fig = go.Figure()

                        fig.add_trace(go.Scatter(
                            x=filtered_df['transaction_date'],
                            y=[1] * len(filtered_df),
                            mode="markers+text",
                            text=[f"{d.strftime('%Y')}<br>{d.strftime('%m-%d')}" for d in filtered_df['transaction_date']],
                            textposition="top center",
                            hovertemplate='<b>%{customdata[0]}</b><br>' +
                                        '商品：%{customdata[1]}<br>' +
                                        '數量：%{customdata[2]}<br>' +
                                        '<extra></extra>',
                            customdata=[[d.strftime('%Y-%m-%d'), record.get('product_name', product_name_str), record.get('quantity', '')]
                                        for d, (_, record) in zip(filtered_df['transaction_date'], filtered_df.iterrows())],
                            marker=dict(size=12, color="#564dff", symbol="circle"),
                            name="補貨紀錄"
                        ))

                        fig.add_trace(go.Scatter(
                            x=filtered_df['transaction_date'],
                            y=[1] * len(filtered_df),
                            mode="lines",
                            line=dict(color="#564dff", width=2),
                            showlegend=False
                        ))

                        data_count = len(filtered_df)
                        chart_width = max(800, data_count * 80)

                        modal_width = 1200
                        scrollable = chart_width > modal_width
                        min_date = filtered_df['transaction_date'].min()
                        max_date = filtered_df['transaction_date'].max()

                        initial_range = [min_date - pd.Timedelta(days=5), max_date + pd.Timedelta(days=5)]

                        fig.update_layout(
                            showlegend=False,
                            xaxis=dict(
                                type='date',
                                tickmode='linear',
                                dtick='M1',
                                showticklabels=True,
                                tickformat='%Y/%m',
                                showgrid=True,
                                gridcolor="lightgray",
                                gridwidth=1,
                                range=initial_range
                            ),
                            yaxis=dict(showticklabels=False, range=[-0.2, 2.5]),
                            height=300,
                            width=chart_width,
                            plot_bgcolor="white",
                            paper_bgcolor="white",
                            margin=dict(l=20, r=20, t=50, b=50)
                        )
                        scroll_container_style = {
                            'overflowX': 'auto',
                            'width': '100%',
                            'maxWidth': '100%',
                            'paddingBottom': '10px',
                            'display': 'block'
                        }
                        if not scrollable:
                            scroll_container_style.update({'display': 'flex', 'justifyContent': 'center'})
                        timeline_chart = html.Div([
                            dcc.Graph(
                                figure=fig,
                                id='timeline-chart',
                                style={'width': f"{chart_width}px", 'maxWidth': '100%'},
                                config={'displayModeBar': False}
                            ),
                            dcc.Download(id='download-chart'),
                            html.Script(f"""
                                setTimeout(function() {{
                                    var chartDiv = document.getElementById('timeline-chart');
                                    if (chartDiv) {{
                                        var scrollContainer = chartDiv.closest('[data-role=\"history-scroll\"]');
                                        if (scrollContainer) {{
                                            var chartWidth = {chart_width};
                                            var containerWidth = scrollContainer.clientWidth;
                                            var scrollPosition = Math.max(0, chartWidth - containerWidth + 100);
                                            scrollContainer.scrollLeft = scrollPosition;
                                        }}
                                    }}
                                }}, 500);
                            """)
                        ], style=scroll_container_style, **{'data-role': 'history-scroll'})
                else:
                    timeline_chart = html.Div("無法載入歷史資料", style={"textAlign": "center", "padding": "20px"})
            except Exception as e:
                timeline_chart = html.Div(f"載入錯誤: {str(e)}", style={"textAlign": "center", "padding": "20px"})

            title = f"{customer_id} - {customer_name} 歷史補貨紀錄"
            if product_label:
                title = f"{title} ({product_label})"

            content = html.Div([
                html.H2(title, style={"textAlign": "center"}),
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

                info = customer_info or {}
                customer_id = info.get('customer_id', '客戶')
                customer_name = info.get('customer_name', '')
                product_id = info.get('product_id', '')
                product_name = info.get('product_name', '')
                product_label = " ".join(part for part in [product_id, product_name] if part)

                safe_customer_id = sanitize_filename_component(customer_id) or '客戶'
                safe_customer_name = sanitize_filename_component(customer_name)
                safe_product_label = sanitize_filename_component(product_label)

                filename_parts = [safe_customer_id]
                if safe_customer_name:
                    filename_parts.append(safe_customer_name)
                if safe_product_label:
                    filename_parts.append(safe_product_label)

                filename = " - ".join(filename_parts + ['歷史補貨紀錄']) + ".png"

                width = figure.get('layout', {}).get('width', 800)
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
     State("table-data-store", "data"),
     State("restock_reminder-customer-id", "value"),
     State("restock_reminder-prediction-date", "value")],
    prevent_initial_call=True
)
def toggle_confirm_status_modal(open_clicks, close_clicks, checkbox_values, checkbox_ids, table_data, customer_search_value, date_search_value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", []
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "confirm-status-btn":
        
        # 直接從當前的 checkbox 狀態收集選中的項目
        selected_items = []
        
        if checkbox_values and checkbox_ids and table_data:
            for i, checkbox_value in enumerate(checkbox_values):
                if i < len(checkbox_ids) and i < len(table_data):
                    # 檢查這個 checkbox 是否被選中
                    customer_id = checkbox_ids[i]['customer_id']
                    row_index = checkbox_ids[i]['row_index']
                    checkbox_key = f"{customer_id}-{row_index}"
                    
                    # checkbox_value 是陣列，檢查是否包含 checkbox_key
                    is_checked = checkbox_key in (checkbox_value or [])
                    
                    if is_checked:
                        # 從 table_data 中獲取對應的資料
                        row_data = table_data[i]
                        selected_item = {
                            '預測ID': row_data.get('預測ID', ''),
                            '客戶ID': row_data.get('客戶ID', ''),
                            '商品ID': row_data.get('商品ID', ''),
                            '商品名稱': row_data.get('商品名稱', ''),
                            '預計補貨日期': row_data.get('預計補貨日期', ''),
                            # 移除了 '預估數量' 和 '信心度'
                        }
                        selected_items.append(selected_item)
                        
        
        
        
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
                                {'label': '確認取消', 'value': 'cancelled'}
                            ],
                            value='cancelled',  # 預設選中
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
                    # 修復：加入預計補貨日期欄位 ↓
                    html.Td(str(item['預計補貨日期']), style={'padding': '10px', 'text-align': 'center', 'border-bottom': '1px solid #eee', 'white-space': 'nowrap'})
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
                                html.Th('預計補貨日期', style={'font-weight': 'bold', 'padding': '10px', 'text-align': 'center', 'background-color': '#f8f9fa', 'border-bottom': '1px solid #ddd', 'white-space': 'nowrap', 'position': 'sticky', 'top': '0px', 'zIndex': 2})
                                # 移除了 '預估數量' 和 '信心度' 的表頭
                            ])
                        ]),
                        html.Tbody(table_rows)
                    ], style={
                        'border-collapse': 'collapse', 
                        'width': '800px',  # 調整表格寬度，因為少了兩個欄位
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
                html.P("即將取消以下補貨提醒，點選「確認」按鈕執行", style={"marginTop": "20px"})
            ])
        else:
            content = html.Div([
                html.P("未找到選中的項目，請重新選擇。", style={"color": "red"})
            ])
            selected_items = []
        
        return True, content, selected_items
    elif button_id == "close-confirm-modal-btn":
        return False, "", []
    
    return dash.no_update, dash.no_update, dash.no_update

# 控制確認按鈕的啟用狀態
@app.callback(
    Output("confirm-status-btn-final", "disabled"),
    Input({"type": "status-radio", "index": dash.ALL}, "value"),
    prevent_initial_call=True
)
def toggle_confirm_button(radio_values):
    # 由於預設都已選中 'cancelled'，所以直接啟用按鈕
    return False

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
                        
                        
                        update_response = requests.put(
                            'http://127.0.0.1:8000/update_restock_prediction_status',
                            json=payload,
                            timeout=30  # 加上逾時設定
                        )
                        
                        
                        
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
     Output("table-data-store", "data", allow_duplicate=True),  # 新增：同時更新 table-data-store
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
    
    # 重新獲取數據並重建表格
    try:
        response = requests.get('http://127.0.0.1:8000/get_restock_data')
        if response.status_code == 200:
            result = response.json()
            # 處理新的分頁回應格式
            data = result.get('data', []) if isinstance(result, dict) else result
            df = pd.DataFrame(data)
            
            # 如果有搜尋條件，過濾資料
            if selected_customer_id:
                df = df[df['customer_id'] == selected_customer_id]
            
            if selected_date:
                df = df[df['prediction_date'] == selected_date]
            
            if df.empty:
                return (html.Div("無符合條件的資料", className="text-center text-muted", style={"padding": "50px"}), 
                       [], updated_checkbox_state)
            
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
            
            # 創建表格
            table, filtered_records = create_restock_table(df, 0)
            
            # 準備 table-data-store 的資料（與 load_data_and_handle_errors 格式一致）
            records_for_store = []
            for _, row in filtered_records.iterrows():
                record_for_store = {
                    '預測ID': row.get('預測ID', ''),
                    '客戶ID': row.get('客戶ID', ''),
                    '客戶名稱': row.get('客戶名稱', ''),
                    '商品ID': row.get('商品ID', ''),
                    '商品名稱': row.get('商品名稱', ''),
                    '預計補貨日期': row.get('預計補貨日期', ''),
                    '預估數量': row.get('預估數量', ''),
                    '信心度': row.get('信心度', '')
                }
                records_for_store.append(record_for_store)
            
            return table, records_for_store, updated_checkbox_state
        else:
            return (html.Div("無法載入資料"), [], updated_checkbox_state)
    except Exception as e:
        print(f"[ERROR] 搜尋時載入資料錯誤: {e}")
        return (html.Div(f"載入錯誤: {str(e)}"), [], updated_checkbox_state)

