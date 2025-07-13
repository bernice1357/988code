from .common import *
from dash import ALL

df = pd.DataFrame([
    {
        "客戶名稱": "王小明",
        "最後訂單日期": "2024-03-15",
        "最後訂購商品": "無線耳機",
        "地址": "台北市大安區忠孝東路100號",
        "電話": "02-1234-5678",
        "不活躍天數": 106,
        "狀態": "未處理"
    },
    {
        "客戶名稱": "李美華",
        "最後訂單日期": "2024-02-28",
        "最後訂購商品": "手機保護殼",
        "地址": "新北市板橋區中山路88號",
        "電話": "02-8765-4321",
        "不活躍天數": 122,
        "狀態": "已處理"
    },
    {
        "客戶名稱": "陳志強",
        "最後訂單日期": "2024-01-20",
        "最後訂購商品": "藍牙喇叭",
        "地址": "台中市西屯區台灣大道200號",
        "電話": "04-5555-6666",
        "不活躍天數": 161,
        "狀態": "未處理"
    }
])

# 計算統計變數
total_customers = len(df)
processed_customers = len(df[df['狀態'] == '已處理'])
unprocessed_customers = len(df[df['狀態'] == '未處理'])

# 計算可選取的行（只有未處理的）
selectable_rows = [i for i, row in df.iterrows() if row['狀態'] == '未處理']

tab_content = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("摘要分析"),
                dbc.CardBody([
                    html.H5(f"不活躍客戶: {total_customers}"),
                    html.H5(f"已處理: {processed_customers}"),
                    html.H5(f"未處理: {unprocessed_customers}")
                ])
            ], color="light", style={"height": "100%"})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("設定不活躍客戶天數"),
                dbc.CardBody([
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText("不活躍天數 >="),
                            dbc.Input(type="number", placeholder="輸入天數", id="inactive-days-input", min=1),
                            dbc.InputGroupText("天")
                        ], style={"flex": "1", "marginRight": "10px"}),
                        dbc.Button("儲存", color="primary", id="save-days-btn")
                    ], style={"display": "flex", "alignItems": "center"})
                ])
            ], color="light", style={"height": "100%"})
        ], width=6)
    ], className="h-100"),
    html.Div([
        html.Div(id="confirm-button-container", style={"display": "flex", "alignItems": "center"}),
        html.Div([
            dbc.ButtonGroup([
                dbc.Button("全部客戶", outline=True, id="btn-all-customers", color="primary"),
                dbc.Button("未處理客戶", outline=True, id="btn-unprocessed-customers", color="primary"),
                dbc.Button("已處理客戶", outline=True, id="btn-processed-customers", color="primary")
            ])
        ], style={"display": "flex", "justifyContent": "flex-end"})
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px", "marginTop": "30px"}),
    html.Div(id="customer-table", children=[
        custom_table(df, show_checkbox=False)
    ], style={"marginTop": "20px"}),
], className="mt-3")

@app.callback(
    Output('customer-table', 'children'),
    [Input('btn-all-customers', 'n_clicks'),
     Input('btn-unprocessed-customers', 'n_clicks'),
     Input('btn-processed-customers', 'n_clicks')]
)
def update_table(btn_all, btn_unprocessed, btn_processed):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        filtered_df = df
        show_checkbox = False
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'btn-unprocessed-customers':
            filtered_df = df[df['狀態'] == '未處理']
            show_checkbox = True
        elif button_id == 'btn-processed-customers':
            filtered_df = df[df['狀態'] == '已處理']
            show_checkbox = False
        else:
            filtered_df = df
            show_checkbox = False
    
    return custom_table(filtered_df, show_checkbox=show_checkbox)

@app.callback(
    Output('confirm-button-container', 'children'),
    [Input({'type': 'status-checkbox', 'index': ALL}, 'value')]
)
def show_confirm_button(checkbox_values):
    selected_rows = []
    for i, values in enumerate(checkbox_values):
        if values:  # 如果checkbox被選中
            selected_rows.extend(values)
    
    if selected_rows and len(selected_rows) > 0:
        return dbc.Button("確認已處理", id="inactive_customers_confirm_btn", color="success")
    else:
        return html.Div()