from .common import *
from callbacks import sales_callback

layout = html.Div([
    # 頂部按鈕區域
    html.Div([
        dbc.Button("篩選條件", id="open-offcanvas", n_clicks=0, color="primary", className="me-2"),
        dbc.Button("匯出", id="export-button", n_clicks=0, color="success")
    ], className="mb-3 d-flex"),
    
    # Offcanvas 組件
    dbc.Offcanvas(
        html.Div([
            # 日期區間
            html.Div([
                html.Label("日期區間", style={"fontSize": "0.9rem", "marginBottom": "5px"}),
                dcc.DatePickerRange(
                    id='date-range-picker',
                    start_date='2025-05-01',
                    end_date='2025-05-07',
                    display_format='YYYY-MM-DD',
                    style={"width": "100%"}
                )
            ], className="mb-3"),
            
            # 客戶 ID
            html.Div([
                html.Label("地區", htmlFor="region-dropdown", style={"fontSize": "0.9rem", "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="region-dropdown",
                    options=[
                        {"label": "全部", "value": "all"},
                        {"label": "北部", "value": "north"},
                        {"label": "中部", "value": "central"},
                        {"label": "南部", "value": "south"},
                        {"label": "東部", "value": "east"}
                    ],
                    placeholder="請選擇地區",
                    className="w-100"
                )
            ], className="mb-3"),
            
            # 商品類別
            html.Div([
                html.Label("商品類別", htmlFor="product-type", style={"fontSize": "0.9rem", "marginBottom": "4px"}),
                dbc.Input(
                    id="product-type",
                    type="text",
                    className="w-100"
                )
            ], className="mb-3"),
            
            # 按鈕群組 - 只保留搜尋和重置按鈕
            html.Div([
                dbc.Button("搜尋", id="search-button", n_clicks=0, color="primary", className="me-2"),
                dbc.Button("重置", id="reset-button", n_clicks=0, color="secondary")
            ], className="d-flex justify-content-center", style={"position": "absolute", "bottom": "20px", "left": "20px", "right": "20px"})
        ]),
        id="offcanvas",
        title="篩選條件",
        is_open=False,
        placement="end"  # 可以選擇 "start", "end", "top", "bottom"
    )
])

