from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback

df=pd.DataFrame([])

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[

    dcc.Store(id='potential-customers-data-store'),

    html.Div([
        html.Div([
            html.Span("搜尋品項名稱", style={"marginRight": "10px"}),
            dbc.InputGroup([
                dcc.Dropdown(
                    id="search-dropdown",
                    options=[
                        {"label": "選項1", "value": "option1"},
                        {"label": "選項2", "value": "option2"},
                        {"label": "選項3", "value": "option3"}
                    ],
                    placeholder="請選擇...",
                    style={"width": "200px"}
                )
            ], style={"width": "auto", "marginRight": "10px"}),
            dbc.Button("送出", id="submit-button", color="primary", className="me-2"),
            html.Div([
                dbc.Button("匯出列表資料", id="export-button", n_clicks=0, color="info", outline=True)
            ], style={"marginLeft": "auto"})
        ], className="d-flex align-items-center")
    ], className="mb-3"),

    html.Div(style={"borderBottom": "1px solid #dee2e6"}),

    html.Div([
        html.Div(id="potential-customers-table-container"),
    ],style={"marginTop": "10px"}),

])

@app.callback(
    [Output("potential-customers-table-container", "children"),
     Output("potential-customers-data-store", "data")],
    [Input("submit-button", "n_clicks")],
    [State("search-dropdown", "value")],
    prevent_initial_call=True
)
def load_potential_customers_data(submit_btn, dropdown_value):
    if not dropdown_value:
        return html.Div(), []
    
    # 這裡放你的API呼叫邏輯
    # try:
    #     response = requests.get(f"http://127.0.0.1:8000/get_potential_customers/{dropdown_value}")
    #     if response.status_code == 200:
    #         data = response.json()
    #         df = pd.DataFrame(data)
    #         # 處理資料...
    #         
    #         table_component = custom_table(
    #             df, 
    #             show_button=True, 
    #             button_text="操作",
    #             button_id_type="potential-customers-btn",
    #         )
    #         
    #         return table_component, df.to_dict('records')
    #     else:
    #         return html.Div("無法載入資料", style={"color": "red"}), []
    # except Exception as e:
    #     return html.Div(f"載入資料時發生錯誤: {str(e)}", style={"color": "red"}), []
    
    # 暫時的測試資料
    test_data = [
        {"客戶ID": "001", "客戶名稱": "測試客戶1", "品項": "商品A"},
        {"客戶ID": "002", "客戶名稱": "測試客戶2", "品項": "商品B"},
    ]
    df = pd.DataFrame(test_data)
    
    table_component = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        row_selectable="multi",
        id="result-table", 
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
        ]
    )
    
    return table_component, df.to_dict('records')

register_offcanvas_callback(app, "potential_customers")