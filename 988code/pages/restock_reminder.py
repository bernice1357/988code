from .common import *
from callbacks import restock_reminder_callback
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
import requests
import plotly.graph_objects as go
from dash import ctx

# offcanvas
product_input_fields = [
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
restock_offcanvas = create_search_offcanvas(
    page_name="buy_new_item",
    input_fields=product_input_fields,
)

layout = html.Div(style={"fontFamily": "sans-serif", "padding": "20px"}, children=[

    # 儲存初始載入標記
    dcc.Store(id="page-loaded", data=True),
    # 儲存表格資料
    dcc.Store(id="table-data-store", data=[]),
    # 儲存客戶資訊
    dcc.Store(id="customer-info-store", data={}),
    
    # 觸發 Offcanvas 的按鈕
    create_error_toast("restock-reminder", message=""),
    restock_offcanvas["trigger_button"],
    restock_offcanvas["offcanvas"],
    html.Div(id="table-container", style={"marginTop": "20px"}),
    
    dbc.Modal(
        id="detail-modal",
        size="xl",
        is_open=False,
        centered=True,
        children=[
            dbc.ModalBody(id="modal-body"),
        ]
    ),
    
    # 下載提示 toast
    create_info_toast(
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
                'product_name': '補貨品項',
                'transaction_date': '上次訂貨日期'
            })
            table_content = button_table(df, button_text="查看歷史補貨紀錄")
            return table_content, df.to_dict('records'), False, ""
        else:
            error_msg = f"API 請求失敗：{response.status_code}"
            return html.Div(), [], True, error_msg
    except Exception as ex:
        error_msg = f"API 請求錯誤：{ex}"
        return html.Div(), [], True, error_msg

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