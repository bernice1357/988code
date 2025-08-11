from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from dash import ALL

# TODO 地區選項還沒放

tab_content = html.Div([
    html.Div([
        dbc.Button(
            "選擇分析目標",
            id="area-filter-settings-button",
            color="primary",
            style={"marginRight": "20px"},
            outline=True
        ),
        dbc.Button(
            "生成圖表",
            id="area-generate-chart-button",
            color="success",
            outline=True
        )
    ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "20px", "marginTop": "30px"}),
    
    html.Div([
        dbc.Popover([
            html.Div([
                html.H6("日期範圍", style={"marginBottom": "10px", "fontWeight": "bold"}),
                html.Div([
                    dbc.Input(
                        type="month",
                        value="2025-07",
                        id="area-start-date",
                        style={"width": "115px", "marginRight": "10px"}
                    ),
                    html.Span("→", style={"marginRight": "15px", "marginLeft": "5px", "fontSize": "20px"}),
                    dbc.Input(
                        type="month",
                        value="2025-07",
                        id="area-end-date",
                        style={"width": "115px"}
                    )
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),
                
                html.Hr(),
                
                html.H6("新增地區", style={"marginBottom": "10px", "fontWeight": "bold"}),
                html.Div([
                    dcc.Dropdown(
                        id="area-dropdown",
                        placeholder="請選擇地區",
                        style={"width": "300px", "marginRight": "10px"}
                    ),
                    dbc.Button("新增", id="area-confirm-add-area", color="primary", size="sm", style={"width": "60px"})
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                
                html.Hr(),
                
                html.H6("已選地區", style={"marginBottom": "10px", "fontWeight": "bold"}),
                html.Div(id="area-badges-container", children=[], style={"display": "flex", "flexWrap": "wrap", "gap": "5px", "minHeight": "30px", "maxWidth": "100%", "overflow": "hidden"})
            ], style={"maxWidth": "550px", "padding": "15px"})
        ], id="area-filter-settings-popover", target="area-filter-settings-button", placement="bottom-start", trigger="click", hide_arrow=False, style={
            "maxWidth": "600px",
            "padding": "0px"
        }),
        
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

# 載入地區選項並排除已選項目
@app.callback(
    Output("area-dropdown", "options"),
    [Input("area-filter-settings-button", "n_clicks"),
     Input("area-badges-container", "children")]
)
def update_dropdown(n_clicks, current_badges):
    # 提取已選項目的文字
    selected_items = []
    if current_badges:
        for badge in current_badges:
            if badge and 'props' in badge and 'children' in badge['props']:
                children = badge['props']['children']
                if isinstance(children, list) and len(children) > 0:
                    span_content = children[0]
                    if 'props' in span_content and 'children' in span_content['props']:
                        selected_items.append(span_content['props']['children'])
    
    response = requests.get("http://127.0.0.1:8000/get_region")
    if response.status_code == 200:
        data = response.json()
        options = [{"label": item["region"], "value": item["region"]} 
                  for item in data if item["region"] not in selected_items]
    else:
        options = []
    return options
    
@app.callback(
    [Output('area-badges-container', 'children'),
     Output('area-dropdown', 'value')],
    Input('area-confirm-add-area', 'n_clicks'),
    [Input({'type': 'area-badge-close', 'index': ALL}, 'n_clicks')],
    State('area-dropdown', 'value'),
    State('area-badges-container', 'children'),
    prevent_initial_call=True
)
def update_badges(n_clicks, close_clicks, dropdown_value, current_badges):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_badges or [], dash.no_update
    
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
        return current_badges, None  # 清空 dropdown 選中值
    
    elif 'area-badge-close' in button_id:
        # 刪除對應的Badge
        if current_badges:
            clicked_badge_id = eval(button_id)['index']
            updated_badges = []
            for badge in current_badges:
                # 檢查這個 badge 的關閉按鈕 ID 是否匹配
                if (badge and 'props' in badge and 'children' in badge['props'] and
                    isinstance(badge['props']['children'], list) and len(badge['props']['children']) > 1):
                    close_button = badge['props']['children'][1]
                    if ('props' in close_button and 'id' in close_button['props'] and
                        close_button['props']['id']['index'] != clicked_badge_id):
                        updated_badges.append(badge)
                else:
                    updated_badges.append(badge)
            return updated_badges, dash.no_update
    
    return current_badges or [], dash.no_update