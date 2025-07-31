from pages.common import *

# TODO 這邊每個排程都要有cookie

layout = html.Div([
    html.Div([

        # 排程項目容器
        html.Div([
            # 新品回購排程
            html.Div([
                html.Div([
                    html.H3("新品回購", style={
                        "fontSize": "1.4rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0"
                    }),
                    html.P("分析所有店家是否回購新品項", style={
                        "color": "#666",
                        "fontSize": "1.0rem",
                        "margin": "0.25rem 0 0 0"
                    })
                ], style={"flex": "1"}),
                dbc.Switch(
                    id="new-product-repurchase-switch",
                    value=False,
                    style={"transform": "scale(1.2)"}
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "2rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "border": "1px solid #e0e6ed",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "1.5rem"
            }),
            
            # 推薦排程
            html.Div([
                html.Div([
                    html.H3("產品/客戶推薦", style={
                        "fontSize": "1.4rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0"
                    }),
                    html.P("更新產品推薦列表", style={
                        "color": "#666",
                        "fontSize": "1.0rem",
                        "margin": "0.25rem 0 0 0"
                    })
                ], style={"flex": "1"}),
                dbc.Switch(
                    id="recommendation-switch",
                    value=False,
                    style={"transform": "scale(1.2)"}
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "2rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "border": "1px solid #e0e6ed",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "1.5rem"
            }),
            
            # 銷售排程
            html.Div([
                html.Div([
                    html.H3("銷售", style={
                        "fontSize": "1.4rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0"
                    }),
                    html.P("處理銷售相關自動化任務", style={
                        "color": "#666",
                        "fontSize": "1.0rem",
                        "margin": "0.25rem 0 0 0"
                    })
                ], style={"flex": "1"}),
                dbc.Switch(
                    id="sales-switch",
                    value=False,
                    style={"transform": "scale(1.2)"}
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "2rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "border": "1px solid #e0e6ed",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "1.5rem"
            }),
            
            # 補貨排程
            html.Div([
                html.Div([
                    html.H3("補貨", style={
                        "fontSize": "1.4rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0"
                    }),
                    html.P("自動監控庫存並處理補貨", style={
                        "color": "#666",
                        "fontSize": "1.0rem",
                        "margin": "0.25rem 0 0 0"
                    })
                ], style={"flex": "1"}),
                dbc.Switch(
                    id="restock-switch",
                    value=False,
                    style={"transform": "scale(1.2)"}
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "2rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "border": "1px solid #e0e6ed",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                "marginBottom": "1.5rem"
            })
            
        ], style={"width": "100%"})
        
    ], style={
        "padding": "2rem",
        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    })
])

# 排程開關回調函數
@app.callback(
    Output("new-product-repurchase-switch", "value"),
    Input("new-product-repurchase-switch", "value"),
    prevent_initial_call=True
)
def toggle_new_product_repurchase(value):
    # 處理新品回購排程開關
    return value

@app.callback(
    Output("recommendation-switch", "value"),
    Input("recommendation-switch", "value"),
    prevent_initial_call=True
)
def toggle_recommendation(value):
    # 處理推薦排程開關
    return value

@app.callback(
    Output("sales-switch", "value"),
    Input("sales-switch", "value"),
    prevent_initial_call=True
)
def toggle_sales(value):
    # 處理銷售排程開關
    return value

@app.callback(
    Output("restock-switch", "value"),
    Input("restock-switch", "value"),
    prevent_initial_call=True
)
def toggle_restock(value):
    # 處理補貨排程開關
    return value