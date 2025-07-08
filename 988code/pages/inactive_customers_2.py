from .common import *

# 示例滯銷商品資料
product_df = pd.DataFrame([
    {
        "商品名稱": "藍牙耳機 Pro",
        "上月銷量": 15,
        "本月銷量": 3,
        "下降比例": "-80%",
        "目前庫存": 25,
        "詳細": "查看",
        "狀態": "未處理"
    },
    {
        "商品名稱": "智慧手環",
        "上月銷量": 20,
        "本月銷量": 8,
        "下降比例": "-60%",
        "目前庫存": 15,
        "詳細": "查看",
        "狀態": "已處理"
    },
    {
        "商品名稱": "無線充電器",
        "上月銷量": 12,
        "本月銷量": 2,
        "下降比例": "-83%",
        "目前庫存": 40,
        "詳細": "查看",
        "狀態": "未處理"
    }
])

# 計算統計變數
total_products = len(product_df)
processed_products = len(product_df[product_df['狀態'] == '已處理'])
unprocessed_products = len(product_df[product_df['狀態'] == '未處理'])

tab_content = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("摘要分析"),
                dbc.CardBody([
                    html.H5(f"滯銷商品: {total_products}"),
                    html.H5(f"已處理: {processed_products}"),
                    html.H5(f"未處理: {unprocessed_products}")
                ])
            ], color="light", style={"height": "100%"})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("設定滯銷商品銷量下降比例"),
                dbc.CardBody([
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText("銷量下降比例 >="),
                            dbc.Input(type="number", placeholder="輸入天數", id="slow-moving-days-input", min=1),
                            dbc.InputGroupText("天")
                        ], style={"flex": "1", "marginRight": "10px"}),
                        dbc.Button("儲存", color="primary", id="save-slow-moving-days-btn")
                    ], style={"display": "flex", "alignItems": "center"})
                ])
            ], color="light", style={"height": "100%"})
        ], width=6)
    ], className="h-100"),
    html.Div([
        html.Div(id="slow-moving-confirm-button-container", style={"display": "flex", "alignItems": "center"}),
        html.Div([
            dbc.ButtonGroup([
                dbc.Button("全部商品", outline=True, id="btn-all-products", color="primary"),
                dbc.Button("未處理商品", outline=True, id="btn-unprocessed-products", color="primary")
            ])
        ], style={"display": "flex", "justifyContent": "flex-end"})
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px", "marginTop": "30px"}),
    html.Div(id="product-table", children=[
        html.Div(dash_table.DataTable(
            id='product-data-table',
            columns=[{"name": i, "id": i} for i in product_df.columns],
            data=product_df.to_dict('records'),
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
                'backgroundColor': '#bcd1df',
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
    ], style={"marginTop": "20px"}),
], className="mt-3")

@app.callback(
    Output('product-table', 'children'),
    [Input('btn-all-products', 'n_clicks'),
     Input('btn-unprocessed-products', 'n_clicks')]
)
def update_product_table(btn_all, btn_unprocessed):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        filtered_df = product_df
        show_checkbox = False
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'btn-unprocessed-products':
            filtered_df = product_df[product_df['狀態'] == '未處理']
            show_checkbox = True
        else:
            filtered_df = product_df
            show_checkbox = False
    
    return html.Div(dash_table.DataTable(
        id='product-data-table',
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
            'backgroundColor': '#bcd1df',
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
    Output('product-data-table', 'selected_rows'),
    [Input('product-data-table', 'selected_rows')],
    [State('product-data-table', 'data')]
)
def filter_selectable_product_rows(selected_rows, data):
    if selected_rows is None:
        return []
    
    # 只保留未處理狀態的選擇
    valid_selections = []
    for row_idx in selected_rows:
        if row_idx < len(data) and data[row_idx]['狀態'] == '未處理':
            valid_selections.append(row_idx)
    
    return valid_selections

@app.callback(
    Output('slow-moving-confirm-button-container', 'children'),
    [Input('product-data-table', 'selected_rows')]
)
def show_slow_moving_confirm_button(selected_rows):
    if selected_rows and len(selected_rows) > 0:
        return dbc.Button("確認已處理", id="confirm-processed-products-btn", color="success")
    else:
        return html.Div()