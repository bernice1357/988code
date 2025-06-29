from .common import *

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

tab1_content = html.Div([
    dbc.Card([
        dbc.CardHeader("摘要分析"),
        dbc.CardBody([
            html.H5(f"不活躍客戶: {total_customers}"),
            html.H5(f"已處理: {processed_customers}"),
            html.H5(f"未處理: {unprocessed_customers}")
        ])
    ], color="light"),
    html.Div([
        html.Div([
            dbc.ButtonGroup([
                dbc.Button("全部客戶", id="btn-all-customers", color="primary"),
                dbc.Button("未處理客戶", id="btn-unprocessed-customers", color="secondary")
            ])
        ], style={"display": "flex", "justifyContent": "flex-end", "marginBottom": "20px"}),
        html.Div(id="customer-table", children=[
            html.Div(dash_table.DataTable(
                id='customer-data-table',
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                row_selectable=False,
                selected_rows=[],
                row_deletable=False,
                style_table={
                    'overflowX': 'auto',
                    'border': '1px solid #ccc'
                },
                style_cell={
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc'
                },
                style_header={
                    'backgroundColor': '#fbe8a6',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f9f9f9',
                    },
                    {
                        'if': {'state': 'active'},
                        'backgroundColor': '#e6f7ff',
                    },
                    {
                        'if': {'state': 'selected'},
                        'backgroundColor': '#d2f8d2',
                        'border': '1px solid #00aa00',
                    },
                    {
                        'if': {'filter_query': '{狀態} = 未處理', 'column_id': '狀態'},
                        'color': 'red',
                    },
                    {
                        'if': {'filter_query': '{狀態} = 已處理', 'column_id': '狀態'},
                        'color': 'green',
                    },
                ]
            ), style={
                'overflowY': 'auto',
                'maxHeight': '60vh',
                'minHeight': '60vh',
                'display': 'block',
            })
        ])
    ], style={"marginTop": "20px"}),
], className="mt-3")

tab2_content = html.Div([
    html.H4("滯銷品分析"),
    html.P("這是滯銷品分析的內容區"),
    dbc.Button("點我查看分析結果", color="danger")
], className="mt-3")

tabs = dbc.Tabs(
    [
        dbc.Tab(tab1_content, label="不活躍客戶"),
        dbc.Tab(tab2_content, label="滯銷品分析")
    ],
    className="my-tabs",
)

layout = dbc.Container([
    tabs
], fluid=True)

@app.callback(
    Output('customer-table', 'children'),
    [Input('btn-all-customers', 'n_clicks'),
     Input('btn-unprocessed-customers', 'n_clicks')]
)
def update_table(btn_all, btn_unprocessed):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        filtered_df = df
        show_checkbox = False
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'btn-unprocessed-customers':
            filtered_df = df[df['狀態'] == '未處理']
            show_checkbox = True
        else:
            filtered_df = df
            show_checkbox = False
    
    return html.Div(dash_table.DataTable(
        id='customer-data-table',
        columns=[{"name": i, "id": i} for i in filtered_df.columns],
        data=filtered_df.to_dict('records'),
        row_selectable="multi" if show_checkbox else False,
        selected_rows=[],
        style_table={
            'overflowX': 'auto',
            'border': '1px solid #ccc'
        },
        style_cell={
            'padding': '8px 12px',
            'textAlign': 'center',
            'border': '1px solid #ccc'
        },
        style_header={
            'backgroundColor': '#fbe8a6',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f9f9f9',
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': '#e6f7ff',
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': '#d2f8d2',
                'border': '1px solid #00aa00',
            },
            {
                'if': {'filter_query': '{狀態} = 未處理', 'column_id': '狀態'},
                'color': 'red',
            },
            {
                'if': {'filter_query': '{狀態} = 已處理', 'column_id': '狀態'},
                'color': 'green',
            },
        ]
    ), style={
        'overflowY': 'auto',
        'maxHeight': '60vh',
        'minHeight': '60vh',
        'display': 'block',
    })

@app.callback(
    Output('customer-data-table', 'selected_rows'),
    [Input('customer-data-table', 'selected_rows')],
    [State('customer-data-table', 'data')]
)
def filter_selectable_rows(selected_rows, data):
    if selected_rows is None:
        return []
    
    # 只保留未處理狀態的選擇
    valid_selections = []
    for row_idx in selected_rows:
        if row_idx < len(data) and data[row_idx]['狀態'] == '未處理':
            valid_selections.append(row_idx)
    
    return valid_selections