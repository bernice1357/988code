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
                        type="date",
                        value="2025-07-01",
                        id="area-start-date",
                        style={"width": "150px", "marginRight": "10px"}
                    ),
                    html.Span("→", style={"marginRight": "15px", "marginLeft": "5px", "fontSize": "20px"}),
                    dbc.Input(
                        type="date",
                        value="2025-07-31",
                        id="area-end-date",
                        style={"width": "150px"}
                    )
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),
                
                html.Hr(),
                
                html.H6("新增地區", style={"marginBottom": "10px", "fontWeight": "bold"}),
                
                # 縣市選擇行
                html.Div([
                    dcc.Dropdown(
                        id="county-dropdown",
                        placeholder="請選擇縣市",
                        style={"width": "280px", "marginRight": "10px"}
                    ),
                    dbc.Button("新增縣市", id="county-confirm-add", color="primary", size="sm", style={"width": "80px"})
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}),
                
                # 地區選擇行
                html.Div([
                    dcc.Dropdown(
                        id="area-dropdown",
                        placeholder="請選擇地區",
                        style={"width": "280px", "marginRight": "10px"}
                    ),
                    dbc.Button("新增地區", id="area-confirm-add-area", color="primary", size="sm", style={"width": "80px"})
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                
                html.Hr(),
                html.H6("已選地區", style={"marginBottom": "10px", "fontWeight": "bold"}),
                html.Div(id="area-badges-container", children=[], style={"display": "flex", "flexWrap": "wrap", "gap": "5px", "minHeight": "30px", "maxWidth": "100%", "overflow": "hidden"})
            ], style={"maxWidth": "550px", "padding": "15px"})
        ], id="area-filter-settings-popover", target="area-filter-settings-button", placement="bottom-start", trigger="legacy", hide_arrow=False, style={
            "maxWidth": "600px",
            "padding": "0px"
        }),
        
        html.Div([
            html.Div(id="area-selected-items-container", children=[], style={"marginTop": "5px"})
        ], style={
            "border": "1px solid #ddd",
            "borderRadius": "8px",
            "padding": "20px",
            "marginTop": "10px",
            "height": "66vh"
        })
    ], style={"position": "relative"}),
    
], className="mt-3")

# 載入縣市選項並排除已選項目
@app.callback(
    Output("county-dropdown", "options"),
    [Input("area-filter-settings-button", "n_clicks"),
     Input("area-badges-container", "children")]
)
def update_county_dropdown(n_clicks, current_badges):
    # 提取已選的縣市項目
    selected_counties = []
    if current_badges:
        for badge in current_badges:
            if badge and 'props' in badge:
                area_type = badge['props'].get('data-area-type')
                if area_type == 'county':  # 只提取縣市類型的 badge
                    if 'children' in badge['props']:
                        children = badge['props']['children']
                        if isinstance(children, list) and len(children) > 0:
                            span_content = children[0]
                            if 'props' in span_content and 'children' in span_content['props']:
                                selected_counties.append(span_content['props']['children'])
    
    response = requests.get("http://127.0.0.1:8000/get_county")
    if response.status_code == 200:
        data = response.json()
        options = [{"label": item["county"], "value": item["county"]} 
                  for item in data if item["county"] not in selected_counties]
    else:
        options = []
    return options

# 根據縣市選擇載入地區選項並排除已選項目
@app.callback(
    [Output("area-dropdown", "options"),
     Output("area-dropdown", "value", allow_duplicate=True)],
    [Input("county-dropdown", "value"),
     Input("area-badges-container", "children")],
    prevent_initial_call=True
)
def update_area_dropdown(selected_county, current_badges):
    # 提取已選的地區項目
    selected_districts = []
    if current_badges:
        for badge in current_badges:
            if badge and 'props' in badge:
                area_type = badge['props'].get('data-area-type')
                if area_type == 'district':  # 只提取地區類型的 badge
                    if 'children' in badge['props']:
                        children = badge['props']['children']
                        if isinstance(children, list) and len(children) > 0:
                            span_content = children[0]
                            if 'props' in span_content and 'children' in span_content['props']:
                                selected_districts.append(span_content['props']['children'])
    
    if not selected_county:
        return [], None
    
    response = requests.get(f"http://127.0.0.1:8000/get_region?county={selected_county}")
    if response.status_code == 200:
        data = response.json()
        # 排除已選的地區
        options = [{"label": item["region"], "value": item["region"]} 
                  for item in data if item["region"] not in selected_districts]
    else:
        options = []
    return options, None
    
@app.callback(
    [Output('area-badges-container', 'children'),
     Output('county-dropdown', 'value'),
     Output('area-dropdown', 'value', allow_duplicate=True)],
    [Input('county-confirm-add', 'n_clicks'),
     Input('area-confirm-add-area', 'n_clicks'),
     Input({'type': 'area-badge-close', 'index': ALL}, 'n_clicks')],
    [State('county-dropdown', 'value'),
     State('area-dropdown', 'value'),
     State('area-badges-container', 'children')],
    prevent_initial_call=True
)
def update_badges(county_add_clicks, area_add_clicks, close_clicks, county_value, area_value, current_badges):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_badges or [], dash.no_update, dash.no_update
    
    # 獲取觸發的按鈕
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'county-confirm-add' and county_add_clicks and county_value:
        # 新增縣市 Badge
        badge_id = f"badge_{len(current_badges or [])}"
        display_text = county_value
        new_badge = html.Div([
            html.Span(display_text, style={"marginRight": "8px"}),
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
        ], 
        **{'data-area-type': 'county', 'data-area-name': county_value},
        style={
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
        return current_badges, None, dash.no_update  # 清空縣市下拉，保持地區下拉不變
        
    elif button_id == 'area-confirm-add-area' and area_add_clicks and area_value:
        # 新增地區 Badge
        badge_id = f"badge_{len(current_badges or [])}"
        display_text = area_value
        new_badge = html.Div([
            html.Span(display_text, style={"marginRight": "8px"}),
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
        ], 
        **{'data-area-type': 'district', 'data-area-name': area_value},
        style={
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
        return current_badges, dash.no_update, None  # 保持縣市下拉不變，清空地區下拉
    
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
            return updated_badges, dash.no_update, dash.no_update
    
    return current_badges or [], dash.no_update, dash.no_update