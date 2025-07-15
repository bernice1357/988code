from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from dash import ALL

tab_content = html.Div([
    html.Div([
        dbc.Input(
            type="month",
            value="2025-07",
            id="area-start-date",
            style={"width": "140px", "display": "inline-block", "marginRight": "10px"}
        ),
        html.Span("→", style={"marginRight": "10px", "fontSize": "30px"}),
        dbc.Input(
            type="month",
            value="2025-07",
            id="area-end-date",
            style={"width": "140px", "display": "inline-block", "marginRight": "20px"}
        ),
        
        dbc.Button(
            "+新增地區",
            id="area-add-button",
            color="info",
            style={"marginLeft": "15px"}
        ),
        html.Div(id="area-badges-container", children=[], style={"display": "flex", "alignItems": "center", "marginLeft": "10px", "flexWrap": "wrap", "gap": "5px"}),
        html.Div(id="area-confirm-button-container", style={"display": "flex", "alignItems": "center", "marginLeft": "auto"})
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px", "marginTop": "30px"}),
    
    html.Div([
        dbc.Popover([
            dcc.Dropdown(
                id="area-dropdown",
                placeholder="請選擇地區",
                style={"marginBottom": "10px"}
            ),
            dbc.Button("新增", id="area-confirm-add-area", color="primary", size="sm")
        ], id="area-popover-form", target="area-add-button", placement="bottom-start", trigger="click", style={"width": "350px", "backgroundColor": "#f8f9fa", "border": "1px solid #dee2e6", "boxShadow": "0 4px 8px rgba(0,0,0,0.1)", "padding": "15px"}, hide_arrow=True),
        
        dbc.Button(
            "生成圖表",
            id="area-generate-chart-button",
            color="success",
            style={"marginTop": "15px", "marginBottom": "15px"}
        ),
        
        html.Div([
            html.H4("銷售分析圖表", style={"textAlign": "center", "marginBottom": "20px"}),
            html.Div(id="area-selected-items-container", children=[], style={"marginTop": "20px"})
        ], style={
            "border": "1px solid #ddd",
            "borderRadius": "8px",
            "padding": "20px",
            "marginTop": "10px",
            "height": "60vh"
        })
    ], style={"position": "relative"}),
    
], className="mt-3")

# 載入地區選項
@app.callback(
    Output("area-dropdown", "options"),
    Input("area-add-button", "n_clicks")
)
def update_dropdown(_):
    response = requests.get("http://127.0.0.1:8000/get_region")
    if response.status_code == 200:
        data = response.json()
        options = [{"label": item["region"], "value": item["region"]} for item in data]
    else:
        options = []
    return options
    
@app.callback(
    Output('area-badges-container', 'children'),
    Input('area-confirm-add-area', 'n_clicks'),
    [Input({'type': 'area-badge-close', 'index': ALL}, 'n_clicks')],
    State('area-dropdown', 'value'),
    State('area-badges-container', 'children'),
    prevent_initial_call=True
)
def update_badges(n_clicks, close_clicks, dropdown_value, current_badges):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_badges or []
    
    # 獲取觸發的按鈕
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'area-confirm-add-area' and n_clicks and dropdown_value:
        # 創建新的Badge
        badge_id = f"badge_{len(current_badges or [])}"
        new_badge = html.Div([
            html.Span(f"{dropdown_value}", style={"marginRight": "8px"}),
            html.Button(
                "×",
                id={'type': 'area-badge-close', 'index': badge_id},
                style={
                    "background": "none",
                    "border": "none",
                    "color": "#6c757d",
                    "fontSize": "16px",
                    "fontWeight": "bold",
                    "cursor": "pointer",
                    "padding": "0",
                    "marginLeft": "4px"
                }
            )
        ], style={
            "display": "inline-flex",
            "alignItems": "center",
            "fontSize": "0.9rem",
            "borderRadius": "50px",
            "padding": "8px 16px",
            "border": "1px solid #dee2e6",
            "color": "#495057",
            "backgroundColor": "#f8f9fa",
            "marginRight": "8px",
            "marginBottom": "4px"
        })
        
        # 將新Badge添加到現有badges中
        if current_badges is None:
            current_badges = []
        
        current_badges.append(new_badge)
        return current_badges
    
    elif 'area-badge-close' in button_id:
        # 刪除對應的Badge
        if current_badges:
            clicked_badge_id = eval(button_id)['index']
            updated_badges = []
            for i, badge in enumerate(current_badges):
                badge_id = f"badge_{i}"
                if badge_id != clicked_badge_id:
                    updated_badges.append(badge)
            return updated_badges
    
    return current_badges or []