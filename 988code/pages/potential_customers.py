from .common import *
from callbacks import potential_customers_callback

df=pd.DataFrame([])

layout = html.Div(style={"fontFamily": "sans-serif", "padding": "20px"}, children=[

    # 篩選條件區
    html.Div([
        dbc.InputGroup(
            [dbc.InputGroupText("商品名稱"), dbc.Input(id="product_name")],
            className="mb-3 w-25",                            
            size="sm",
            style={"marginRight": "10px"},
        ),
        dbc.InputGroup(
            [dbc.InputGroupText("規格 (選填)"), dbc.Input(id="spec")],
            className="mb-3 w-25",                            
            size="sm",
            style={"marginRight": "10px"},
        ),
        dbc.Button("搜尋", id="search-button", n_clicks=0, style={"marginRight": "10px"}, className="btn btn-secondary"),
        dbc.Button("匯出列表客戶資料", id="export-button", n_clicks=0, style={"marginRight": "10px"}, className="btn btn-success"),
    ], style={"display": "flex", "alignItems": "center"}),
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
                    'backgroundColor': '#d2f8d2',  # 勾選後的顏色
                    'border': '1px solid #00aa00',
                },
            ]
        )   
    ],style={"marginTop": "20px"}),
    dbc.Modal(
        id="detail-modal",
        size="xl",
        is_open=False,
        children=[
            dbc.ModalBody(id="modal-body"),
        ]
    )
])