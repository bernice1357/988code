from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from dash import ALL

tab_content = html.Div([
    html.Div([
        dbc.Button(
            "選擇分析目標",
            id="filter-settings-button",
            color="primary",
            style={"marginRight": "20px"},
            outline=True
        ),
        dbc.Button(
            "生成圖表",
            id="item-generate-chart-button",
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
                        id="item-start-date",
                        style={"width": "115px", "marginRight": "10px"}
                    ),
                    html.Span("→", style={"marginRight": "15px", "marginLeft": "5px", "fontSize": "20px"}),
                    dbc.Input(
                        type="month",
                        value="2025-07",
                        id="item-end-date",
                        style={"width": "115px"}
                    )
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),
                
                html.Hr(),
                
                html.H6("新增產品", style={"marginBottom": "10px", "fontWeight": "bold"}),
                dbc.RadioItems(
                    id="item-radio-options",
                    options=[
                        {"label": "類別", "value": "category"},
                        {"label": "子類別", "value": "subcategory"},
                        {"label": "品項", "value": "item"}
                    ],
                    inline=True,
                    style={"marginBottom": "10px"}
                ),
                html.Div([
                    dcc.Dropdown(
                        id="item-dropdown",
                        placeholder="請選擇",
                        style={"width": "300px", "marginRight": "10px"}
                    ),
                    dbc.Button("新增", id="item-confirm-add-item", color="primary", size="sm", style={"width": "60px"})
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),
                
                html.Hr(),
                
                html.H6("已選產品", style={"marginBottom": "10px", "fontWeight": "bold"}),
                html.Div(id="item-badges-container", children=[], style={"display": "flex", "flexWrap": "wrap", "gap": "5px", "minHeight": "30px", "maxWidth": "100%", "overflow": "hidden"})
            ], style={"maxWidth": "550px", "padding": "15px"})
        ], id="filter-settings-popover", target="filter-settings-button", placement="bottom-start", trigger="click", hide_arrow=False
        , style={
            "maxWidth": "600px",
            "padding": "0px"
        }),
        
        html.Div([
            html.H4("銷售分析圖表", style={"textAlign": "center", "marginBottom": "20px"}),
            html.Div(id="item-selected-items-container", children=[], style={"marginTop": "20px"})
        ], style={
            "border": "1px solid #ddd",
            "borderRadius": "8px",
            "padding": "20px",
            "marginTop": "10px",
            "height": "60vh"
        })
    ], style={"position": "relative"}),
    
], className="mt-3")

# 根據 radio 選項改輸入框，並排除已選項目
@app.callback(
    [Output("item-dropdown", "options"),
     Output("item-dropdown", "placeholder")],
    [Input("item-radio-options", "value"),
     Input("item-badges-container", "children")]
)
def update_dropdown(selected_type, current_badges):
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
    
    if selected_type == "category":
        response = requests.get("http://127.0.0.1:8000/get_category")
        if response.status_code == 200:
            data = response.json()
            options = [{"label": item["category"], "value": item["category"]} 
                      for item in data if item["category"] not in selected_items]
        else:
            options = []
        return options, "選擇類別"
    elif selected_type == "subcategory":
        response = requests.get("http://127.0.0.1:8000/get_subcategory")
        if response.status_code == 200:
            data = response.json()
            options = [{"label": item["subcategory"], "value": item["subcategory"]} 
                      for item in data if item["subcategory"] not in selected_items]
        else:
            options = []
        return options, "選擇子類別"
    elif selected_type == "item":
        response = requests.get("http://127.0.0.1:8000/get_name_zh")
        if response.status_code == 200:
            data = response.json()
            options = [{"label": item["name_zh"], "value": item["name_zh"]} 
                      for item in data if item["name_zh"] not in selected_items]
        else:
            options = []
        return options, "選擇品項"
    else:
        return [], "請選擇"
    
@app.callback(
    [Output('item-badges-container', 'children'),
     Output('item-dropdown', 'value')],
    Input('item-confirm-add-item', 'n_clicks'),
    [Input({'type': 'item-badge-close', 'index': ALL}, 'n_clicks')],
    State('item-radio-options', 'value'),
    State('item-dropdown', 'value'),
    State('item-badges-container', 'children'),
    prevent_initial_call=True
)
def update_badges(n_clicks, close_clicks, radio_value, dropdown_value, current_badges):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_badges or [], dash.no_update
    
    # 獲取觸發的按鈕
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'item-confirm-add-item' and n_clicks and radio_value and dropdown_value:
        # 創建新的Badge
        badge_id = f"badge_{len(current_badges or [])}"
        new_badge = html.Div([
            html.Span(f"{dropdown_value}", style={"marginRight": "8px"}),
            html.Button(
                "×",
                id={'type': 'item-badge-close', 'index': badge_id},
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
            "marginBottom": "4px",
            "maxWidth": "calc(100% - 16px)",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "whiteSpace": "nowrap"
        })
        
        # 將新Badge添加到現有badges中
        if current_badges is None:
            current_badges = []
        
        current_badges.append(new_badge)
        return current_badges, None  # 清空 dropdown 選中值
    
    elif 'item-badge-close' in button_id:
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