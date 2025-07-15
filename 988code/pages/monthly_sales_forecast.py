from .common import *
from components.table import custom_table

monthly_forecast_df = pd.DataFrame([
    {
        "商品名稱": "白雪魚冷凍280/320-A ",
        "類別": "白雪魚",
        "預測銷量": "15箱"
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
                            {"label": "白雪魚", "value": "白雪魚"},
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
        
        # 使用 custom_table 組件
        custom_table(
            df=monthly_forecast_df,
            show_checkbox=True,
            show_button=True
        )
    ], style={
        "backgroundColor": "white",
        "border": "1px solid #dee2e6",
        "borderRadius": "4px",
        "overflow": "hidden"
    })
], style={
    "backgroundColor": "#f5f5f5",
    "padding": "20px",
    "minHeight": "500px"
})