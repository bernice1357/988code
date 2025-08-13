from .common import *
from components.table import custom_table

# 根據圖片內容創建數據
monthly_forecast_df = pd.DataFrame([
    {
        "subcategory": "薄鹽鯖魚",
        "volatility_group": "低波動",
        "上月銷量": 0,
        "預測銷量": 7854
    },
    {
        "product_id": "FMWGUEA05",
        "product_name": "薄鹽鯖魚140/170-(有骨)A級專用-6K",
        "month_minus_1": 0,
        "prediction_level": 1291
    },
    {
        "product_id": "TUFMJEWGD",
        "product_name": "薄鹽鯖魚130/160-5K-種中清專用",
        "month_minus_1": 0,
        "prediction_level": 846
    },
    {
        "subcategory": "青花菜",
        "volatility_group": "低波動",
        "上月銷量": 0,
        "預測銷量": 3769
    },
    {
        "product_id": "FCH000002",
        "product_name": "青花菜(1K*10包)-佳慧",
        "month_minus_1": 0,
        "prediction_level": 2494
    },
    {
        "product_id": "FCH000003",
        "product_name": "青花菜(10K)-佳慧",
        "month_minus_1": 0,
        "prediction_level": 1295
    }
])

tab_content = html.Div([
    # 控制面板
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.Label("預測期間：", style={"marginRight": "10px", "fontWeight": "normal"}),
                    dbc.Input(
                        type="month",
                        value="2025-05",
                        id="monthly-forecast-period",
                        style={"width": "120px", "display": "inline-block", "marginRight": "20px"}
                    )
                ], style={"display": "inline-block", "marginRight": "30px"}),
                
                html.Div([
                    html.Label("商品類別：", style={"marginRight": "10px", "fontWeight": "normal"}),
                    dbc.Select(
                        options=[
                            {"label": "全部類別", "value": "全部類別"},
                            {"label": "薄鹽鯖魚", "value": "薄鹽鯖魚"},
                            {"label": "青花菜", "value": "青花菜"},
                            {"label": "冷凍食品", "value": "冷凍食品"},
                            {"label": "生鮮蔬果", "value": "生鮮蔬果"}
                        ],
                        value="全部類別",
                        id="monthly-category-select",
                        style={"width": "120px", "display": "inline-block", "marginRight": "20px"}
                    )
                ], style={"display": "inline-block", "marginRight": "30px"}),
                
                dbc.Button(
                    "更新預測",
                    color="success",
                    id="update-monthly-forecast-btn",
                    style={"backgroundColor": "#28a745", "borderColor": "#28a745"}
                )
            ], style={
                "backgroundColor": "#e8e8e8",
                "padding": "15px",
                "marginBottom": "20px",
                "display": "flex",
                "alignItems": "center",
                "flexWrap": "wrap"
            })
        ])
    ]),
    
    # 預測數據詳情區域
    html.Div([
        html.H5("預測數據詳情", style={
            "backgroundColor": "#f8f9fa",
            "padding": "10px 15px",
            "margin": "0",
            "borderBottom": "1px solid #dee2e6",
            "fontWeight": "bold",
            "fontSize": "16px"
        }),
        
        # 創建階層式表格顯示
        html.Div(id="monthly-forecast-table-container", children=[
            # 薄鹽鯖魚主分類
            html.Div([
                html.Div([
                    html.Div("子類別", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f8f9fa", "fontWeight": "bold"}),
                    html.Div("波動組", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f8f9fa", "fontWeight": "bold"}),
                    html.Div("上月銷量", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f8f9fa", "fontWeight": "bold"}),
                    html.Div("預測銷量", style={"flex": "1", "padding": "10px", "backgroundColor": "#f8f9fa", "fontWeight": "bold"})
                ], style={"display": "flex", "border": "1px solid #ddd"}),
                
                # 薄鹽鯖魚分類行 - 可點擊
                dbc.Button([
                    html.Div("薄鹽鯖魚", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd"}),
                    html.Div("低波動", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd"}),
                    html.Div("0", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center"}),
                    html.Div("7854", style={"flex": "1", "padding": "10px", "textAlign": "center"})
                ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none", "width": "100%", "backgroundColor": "#ffffff", "borderRadius": "0", "padding": "0"}, 
                id="mackerel-category", color="light", className="p-0"),
                
                # 薄鹽鯖魚子項目 - 默認隱藏
                html.Div([
                    # 子項目標題行
                    html.Div([
                        html.Div("子類別", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                        html.Div("product_id", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                        html.Div("product_name", style={"flex": "2", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                        html.Div("month_minus_1", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                        html.Div("prediction_level", style={"flex": "1", "padding": "10px", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"})
                    ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none"}),
                    
                    # FMWGUEA05
                    html.Div([
                        html.Div("薄鹽鯖魚", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff", "textAlign": "center"}),
                        html.Div("FMWGUEA05", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                        html.Div("薄鹽鯖魚140/170-(有骨)A級專用-6K", style={"flex": "2", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                        html.Div("0", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center", "backgroundColor": "#ffffff"}),
                        html.Div("1291", style={"flex": "1", "padding": "10px", "textAlign": "center", "backgroundColor": "#ffffff"})
                    ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none"}),
                    
                    # TUFMJEWGD
                    html.Div([
                        html.Div("薄鹽鯖魚", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff", "textAlign": "center"}),
                        html.Div("TUFMJEWGD", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                        html.Div("薄鹽鯖魚130/160-5K-種中清專用", style={"flex": "2", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                        html.Div("0", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center", "backgroundColor": "#ffffff"}),
                        html.Div("846", style={"flex": "1", "padding": "10px", "textAlign": "center", "backgroundColor": "#ffffff"})
                    ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none"})
                    
                ], id="mackerel-details", style={"display": "none"}),
                
                # 青花菜分類行 - 可點擊  
                dbc.Button([
                    html.Div("青花菜", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd"}),
                    html.Div("低波動", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd"}),
                    html.Div("0", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center"}),
                    html.Div("3769", style={"flex": "1", "padding": "10px", "textAlign": "center"})
                ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none", "width": "100%", "backgroundColor": "#ffffff", "borderRadius": "0", "padding": "0"}, 
                id="broccoli-category", color="light", className="p-0"),
                
                # 青花菜子項目 - 默認隱藏
                html.Div([
                    # 子項目標題行
                    html.Div([
                        html.Div("子類別", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                        html.Div("product_id", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                        html.Div("product_name", style={"flex": "2", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                        html.Div("month_minus_1", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                        html.Div("prediction_level", style={"flex": "1", "padding": "10px", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"})
                    ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none"}),
                    
                    # FCH000002
                    html.Div([
                        html.Div("青花菜", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff", "textAlign": "center"}),
                        html.Div("FCH000002", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                        html.Div("青花菜(1K*10包)-佳慧", style={"flex": "2", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                        html.Div("0", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center", "backgroundColor": "#ffffff"}),
                        html.Div("2494", style={"flex": "1", "padding": "10px", "textAlign": "center", "backgroundColor": "#ffffff"})
                    ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none"}),
                    
                    # FCH000003
                    html.Div([
                        html.Div("青花菜", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff", "textAlign": "center"}),
                        html.Div("FCH000003", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                        html.Div("青花菜(10K)-佳慧", style={"flex": "2", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                        html.Div("0", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center", "backgroundColor": "#ffffff"}),
                        html.Div("1295", style={"flex": "1", "padding": "10px", "textAlign": "center", "backgroundColor": "#ffffff"})
                    ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none"})
                    
                ], id="broccoli-details", style={"display": "none"})
                
            ], style={"marginBottom": "10px"})
        ])
    ], style={
        "backgroundColor": "white",
        "border": "1px solid #dee2e6",
        "borderRadius": "4px",
        "overflow": "hidden",
        "height": "65vh"
    })
], style={
    "padding": "20px",
    "minHeight": "500px"
})

# Callback for handling click events to show/hide details
@app.callback(
    [Output('mackerel-details', 'style'),
     Output('broccoli-details', 'style')],
    [Input('mackerel-category', 'n_clicks'),
     Input('broccoli-category', 'n_clicks')],
    [State('mackerel-details', 'style'),
     State('broccoli-details', 'style')],
    prevent_initial_call=True
)
def toggle_category_details(mackerel_clicks, broccoli_clicks, mackerel_style, broccoli_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    # 初始化 style 如果為 None
    if mackerel_style is None:
        mackerel_style = {"display": "none"}
    if broccoli_style is None:
        broccoli_style = {"display": "none"}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'mackerel-category':
        # 切換薄鹽鯖魚詳細資料顯示狀態
        if mackerel_style.get("display") == "none":
            mackerel_style = {"display": "block"}
        else:
            mackerel_style = {"display": "none"}
    
    elif button_id == 'broccoli-category':
        # 切換青花菜詳細資料顯示狀態
        if broccoli_style.get("display") == "none":
            broccoli_style = {"display": "block"}
        else:
            broccoli_style = {"display": "none"}
    
    return mackerel_style, broccoli_style