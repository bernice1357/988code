from .common import *
from callbacks import restock_reminder_callback

# 假資料
df = pd.DataFrame([
    {"客戶ID": "AAA", "客戶名稱": "美味快餐", "預計補貨日期": "2025/4/23", "補貨品項": "白口魚150/180 10K", "上次訂購日期": "2025/4/16"},
    {"客戶ID": "BBB", "客戶名稱": "木川嶺咖啡餐飲", "預計補貨日期": "2025/4/25", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "CCC", "客戶名稱": "美齡自助餐", "預計補貨日期": "2025/4/26", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "AAA", "客戶名稱": "美味快餐", "預計補貨日期": "2025/4/23", "補貨品項": "白口魚150/180 10K", "上次訂購日期": "2025/4/16"},
    {"客戶ID": "BBB", "客戶名稱": "木川嶺咖啡餐飲", "預計補貨日期": "2025/4/25", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "CCC", "客戶名稱": "美齡自助餐", "預計補貨日期": "2025/4/26", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "AAA", "客戶名稱": "美味快餐", "預計補貨日期": "2025/4/23", "補貨品項": "白口魚150/180 10K", "上次訂購日期": "2025/4/16"},
    {"客戶ID": "BBB", "客戶名稱": "木川嶺咖啡餐飲", "預計補貨日期": "2025/4/25", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "CCC", "客戶名稱": "美齡自助餐", "預計補貨日期": "2025/4/26", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "AAA", "客戶名稱": "美味快餐", "預計補貨日期": "2025/4/23", "補貨品項": "白口魚150/180 10K", "上次訂購日期": "2025/4/16"},
    {"客戶ID": "BBB", "客戶名稱": "木川嶺咖啡餐飲", "預計補貨日期": "2025/4/25", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "CCC", "客戶名稱": "美齡自助餐", "預計補貨日期": "2025/4/26", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "AAA", "客戶名稱": "美味快餐", "預計補貨日期": "2025/4/23", "補貨品項": "白口魚150/180 10K", "上次訂購日期": "2025/4/16"},
    {"客戶ID": "BBB", "客戶名稱": "木川嶺咖啡餐飲", "預計補貨日期": "2025/4/25", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "CCC", "客戶名稱": "美齡自助餐", "預計補貨日期": "2025/4/26", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "AAA", "客戶名稱": "美味快餐", "預計補貨日期": "2025/4/23", "補貨品項": "白口魚150/180 10K", "上次訂購日期": "2025/4/16"},
    {"客戶ID": "BBB", "客戶名稱": "木川嶺咖啡餐飲", "預計補貨日期": "2025/4/25", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "CCC", "客戶名稱": "美齡自助餐", "預計補貨日期": "2025/4/26", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "AAA", "客戶名稱": "美味快餐", "預計補貨日期": "2025/4/23", "補貨品項": "白口魚150/180 10K", "上次訂購日期": "2025/4/16"},
    {"客戶ID": "BBB", "客戶名稱": "木川嶺咖啡餐飲", "預計補貨日期": "2025/4/25", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "CCC", "客戶名稱": "美齡自助餐", "預計補貨日期": "2025/4/26", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "AAA", "客戶名稱": "美味快餐", "預計補貨日期": "2025/4/23", "補貨品項": "白口魚150/180 10K", "上次訂購日期": "2025/4/16"},
    {"客戶ID": "BBB", "客戶名稱": "木川嶺咖啡餐飲", "預計補貨日期": "2025/4/25", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
    {"客戶ID": "CCC", "客戶名稱": "美齡自助餐", "預計補貨日期": "2025/4/26", "補貨品項": "薄鹽鯖魚240/280-5K", "上次訂購日期": "2025/4/17"},
])

layout = html.Div(style={"fontFamily": "sans-serif", "padding": "20px"}, children=[

    # 觸發 Offcanvas 的按鈕
    dbc.Button("搜尋條件", id="open-search-offcanvas", color="primary", className="mb-3"),
    # 篩選條件區 - Offcanvas
    dbc.Offcanvas(
        [
            dcc.DatePickerRange(
                id='date-range-picker',
                start_date='2025-05-01',
                end_date='2025-05-07',
                display_format='YYYY-MM-DD',
                className="mb-3"
            ),
            html.Div([
                html.Label("補貨品項", htmlFor="product-type", style={"fontSize": "0.9rem", "marginBottom": "4px"}),
                dbc.Input(
                    id="product-type",
                    type="text",
                    className="w-100"
                )
            ], className="mb-3"),
            html.Div([
                dbc.Button("搜尋", id="search-button", color="primary", size="sm", className="me-2"),
                dbc.Button("重置", id="reset-button", color="secondary", size="sm", className="me-2"),
                dbc.Button("關閉", id="close-offcanvas", color="outline-secondary", size="sm")
            ], className="d-flex justify-content-center", style={"position": "absolute", "bottom": "20px", "left": "20px", "right": "20px"})
        ],
        id="search-offcanvas",
        title="搜尋條件",
        is_open=False,
        placement="end",
        style={"width": "400px"}
    ),

    html.Div([
        button_table(df)
    ], style={"marginTop": "20px"}),
    
    dbc.Modal(
        id="detail-modal",
        size="xl",
        is_open=False,
        children=[
            dbc.ModalBody(id="modal-body"),
        ]
    )
])

# 控制 Offcanvas 開關的回調函數
@app.callback(
    Output("search-offcanvas", "is_open"),
    [
        Input("open-search-offcanvas", "n_clicks"),
        Input("close-offcanvas", "n_clicks"),
        Input("search-button", "n_clicks")
    ],
    prevent_initial_call=True
)
def toggle_search_offcanvas(open_clicks, close_clicks, search_clicks):
    from dash import ctx
    
    if ctx.triggered_id == "open-search-offcanvas":
        return True
    elif ctx.triggered_id in ["close-offcanvas", "search-button"]:
        return False
    return False