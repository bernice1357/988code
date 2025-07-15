from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback

df=pd.DataFrame([])

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[

    # 新增的card區域
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("搜尋品項名稱"),
                    dcc.Dropdown(
                        id="search-dropdown",
                        options=[
                            {"label": "選項1", "value": "option1"},
                            {"label": "選項2", "value": "option2"},
                            {"label": "選項3", "value": "option3"}
                        ],
                        placeholder="請選擇..."
                    )
                ], width=4),
                dbc.Col([
                    dbc.Label("　"),  # 空白佔位
                    dbc.Button("送出", id="submit-button", color="primary", className="w-100")
                ], width=2)
            ])
        ])
    ], className="mb-3"),

    # 匯出按鈕區
    html.Div([
        dbc.Button("匯出列表資料", id="export-button", n_clicks=0, color="success")
    ], className="mb-3 d-flex justify-content-between align-items-center"),
    
    # 表格區域 (初始隱藏)
    html.Div([
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            row_selectable="multi",  # 可以多選
            id="result-table", 
            selected_rows=[],        # 預設沒選任何列
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
                    'backgroundColor': '#d2f8d2',  # 勾選後的顏色
                    'border': '1px solid #00aa00',
                },
            ]
        )   
    ], id="table-container", style={"marginTop": "20px", "display": "none"}),
])

register_offcanvas_callback(app, "potential_customers")