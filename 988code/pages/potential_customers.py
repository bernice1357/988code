from .common import *
from callbacks import potential_customers_callback
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback

df=pd.DataFrame([])

# offcanvas
product_input_fields = [
    {
        "id": "potential_product_id", 
        "label": "商品名稱",
        "type": "dropdown"
    },
    {
        "id": "potential_spec_id", 
        "label": "規格",
        "type": "dropdown"
    }
]
potential_components = create_search_offcanvas(
    page_name="potential_customers",
    input_fields=product_input_fields,
)

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[

    # 篩選條件區
    html.Div([
        potential_components["trigger_button"],
        dbc.Button("匯出列表資料", id="export-button", n_clicks=0, color="success")
    ], className="mb-3 d-flex justify-content-between align-items-center"),
    potential_components["offcanvas"],
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
    ],style={"marginTop": "20px"}),
])

register_offcanvas_callback(app, "potential_customers")