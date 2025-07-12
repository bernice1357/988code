from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from dash import ALL

tab_content = html.Div([
    html.Div([
        dcc.DatePickerRange(
            id="item-datepicker",
            start_date_placeholder_text="開始日期",
            end_date_placeholder_text="結束日期",
            display_format="YYYY-MM-DD"
        ),
        dbc.Button(
            "+新增",
            id="item-add-button",
            color="info",
            style={"marginLeft": "15px"}
        ),
        html.Div(id="item-badges-container", children=[], style={"display": "flex", "alignItems": "center", "marginLeft": "10px", "flexWrap": "wrap", "gap": "5px"}),
        html.Div(id="item-confirm-button-container", style={"display": "flex", "alignItems": "center", "marginLeft": "auto"})
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px", "marginTop": "30px"}),
    
    html.Div([
        dbc.Popover([
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
            dcc.Dropdown(
                id="item-dropdown",
                placeholder="請選擇",
                style={"marginBottom": "10px"}
            ),
            dbc.Button("新增", id="item-confirm-add-item", color="primary", size="sm")
        ], id="item-popover-form", target="item-add-button", placement="bottom-start", trigger="click", hide_arrow=True),
        
        dbc.Button(
            "生成圖表",
            id="item-generate-chart-button",
            color="success",
            style={"marginTop": "15px", "marginBottom": "15px"}
        ),
        
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

# 根據 radio 選項改輸入框
@app.callback(
    [Output("item-dropdown", "options"),
     Output("item-dropdown", "placeholder")],
    Input("item-radio-options", "value")
)
def update_dropdown(selected_type):
    if selected_type == "category":
        response = requests.get("http://127.0.0.1:8000/get_category")
        if response.status_code == 200:
            data = response.json()
            options = [{"label": item["category"], "value": item["category"]} for item in data]
        else:
            options = []
        return options, "選擇類別"
    elif selected_type == "subcategory":
        response = requests.get("http://127.0.0.1:8000/get_subcategory")
        if response.status_code == 200:
            data = response.json()
            options = [{"label": item["subcategory"], "value": item["subcategory"]} for item in data]
        else:
            options = []
        return options, "選擇子類別"
    elif selected_type == "item":
        response = requests.get("http://127.0.0.1:8000/get_name_zh")
        if response.status_code == 200:
            data = response.json()
            options = [{"label": item["name_zh"], "value": item["name_zh"]} for item in data]
        else:
            options = []
        return options, "選擇品項"
    else:
        return [], "請選擇"
    
@app.callback(
    Output('item-badges-container', 'children'),
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
        return current_badges or []
    
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
            "marginBottom": "4px"
        })
        
        # 將新Badge添加到現有badges中
        if current_badges is None:
            current_badges = []
        
        current_badges.append(new_badge)
        return current_badges
    
    elif 'item-badge-close' in button_id:
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