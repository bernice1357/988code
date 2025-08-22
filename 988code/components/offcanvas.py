from dash import html, dcc, Input, Output, callback, ctx, dash
import dash_bootstrap_components as dbc

# 全局变量存储各页面的字段配置
_page_fields = {}

def create_search_offcanvas(
    page_name,
    input_fields=None,
    title="搜尋條件",
    button_text="搜尋條件",
    width="400px",
    placement="end"
):
    """
    创建通用搜索 Offcanvas 组件
    
    参数:
    - page_name: 页面名称，用于生成唯一的 ID
    - input_fields: 输入框列表，格式为 [{"id": "field-id", "label": "欄位名稱", "placeholder": "提示文字", "type": "text"}]
    - title: Offcanvas 标题
    - button_text: 触发按钮文字
    - width: Offcanvas 宽度
    - placement: Offcanvas 位置 ("start", "end", "top", "bottom")
    """
    
    # 根据页面名称生成唯一 ID
    offcanvas_id = f"{page_name}-search-offcanvas"
    button_id = f"{page_name}-open-search-offcanvas"
    reset_button_id = f"{page_name}-reset-button"
    
    if input_fields is None:
        input_fields = []
    
    # 存储页面的字段配置，供重置功能使用
    _page_fields[page_name] = input_fields
    
    # 建立 Offcanvas 内容
    offcanvas_children = []
    
    # 动态生成输入框
    for field in input_fields:
        field_id = f"{page_name}-{field['id']}" if not field['id'].startswith(page_name) else field['id']
        field_div = html.Div([
            html.Label(
                field.get("label", ""), 
                htmlFor=field_id, 
                style={"fontSize": "0.9rem", "marginBottom": "4px"}
            )
        ], className="mb-3")
        
        # 根据类型创建不同的输入组件
        if field.get("type") == "dropdown":
            component = dcc.Dropdown(
                id=field_id,
                options=field.get("options", []),
                placeholder=field.get("placeholder", ""),
                className="w-100"
            )
        elif field.get("type") == "date_range":
            # 为开始和结束日期创建唯一的 ID
            start_id = f"{field_id}-start"
            end_id = f"{field_id}-end"
            
            component = html.Div([
                # 开始日期
                html.Div([
                    dbc.Input(
                        type="date",
                        value=field.get("start_date", ""),
                        id=start_id,
                        min="1900-01-01",
                        max="2100-12-31",
                        style={"width": "130px"}
                    ),
                    dbc.FormFeedback(
                        "開始日期不能晚於結束日期",
                        type="invalid",
                        id=f"{start_id}-feedback"
                    )
                ]),
                
                html.Span("→", style={
                    "margin": "0 8px", 
                    "fontSize": "18px", 
                    "verticalAlign": "middle",
                    "color": "#6c757d"
                }),
                
                # 结束日期  
                html.Div([
                    dbc.Input(
                        type="date",
                        value=field.get("end_date", ""),
                        id=end_id,
                        min="1900-01-01",
                        max="2100-12-31",
                        style={"width": "130px"}
                    ),
                    dbc.FormFeedback(
                        "結束日期不能早於開始日期", 
                        type="invalid",
                        id=f"{end_id}-feedback"
                    )
                ]),
                
            ], style={
                "display": "flex", 
                "alignItems": "center", 
                "justifyContent": "center", 
                "width": "100%",
                "gap": "4px"
            })
        else:
            component = dbc.Input(
                id=field_id,
                type=field.get("type", "text"),
                placeholder=field.get("placeholder", ""),
                className="w-100"
            )
        
        field_div.children.append(component)
        offcanvas_children.append(field_div)
    
    # 按钮区域 - 重置按钮字体放大
    button_div = html.Div([
        dbc.Button(
            "重置", 
            id=reset_button_id, 
            color="secondary", 
            size="sm",
            style={"fontSize": "1rem"}  # 放大字体
        )
    ], className="d-flex justify-content-center", style={"position": "absolute", "bottom": "20px", "left": "20px", "right": "20px"})
    
    offcanvas_children.append(button_div)
    
    # 触发按钮
    trigger_button = dbc.Button(
        button_text, 
        id=button_id, 
        color="primary"
    )
    
    # Offcanvas
    offcanvas = dbc.Offcanvas(
        offcanvas_children,
        id=offcanvas_id,
        title=title,
        is_open=False,
        placement=placement,
        style={"width": width}
    )
    
    return {
        "trigger_button": trigger_button,
        "offcanvas": offcanvas,
        "ids": {
            "offcanvas_id": offcanvas_id,
            "button_id": button_id,
            "reset_button_id": reset_button_id
        }
    }

def register_offcanvas_callback(
    app,
    page_name
):
    """
    注册 Offcanvas 的所有回调函数，包括开关和重置功能
    
    参数:
    - app: Dash app 实例
    - page_name: 页面名称
    """
    
    offcanvas_id = f"{page_name}-search-offcanvas"
    button_id = f"{page_name}-open-search-offcanvas"
    reset_button_id = f"{page_name}-reset-button"
    
    # 获取该页面的字段配置
    input_fields = _page_fields.get(page_name, [])
    
    # 注册开关 Offcanvas 的回调
    @app.callback(
        Output(offcanvas_id, "is_open"),
        Input(button_id, "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_search_offcanvas(open_clicks):
        if open_clicks:
            return True
        return False
    
    # 如果有字段配置，则注册重置功能的回调
    if input_fields:
        # 根据 input_fields 自动生成所有字段的 outputs
        outputs = []
        
        for field in input_fields:
            field_id = f"{page_name}-{field['id']}" if not field['id'].startswith(page_name) else field['id']
            
            # 根据字段类型处理
            if field.get("type") == "date_range":
                # 日期范围字段有两个输入框
                start_id = f"{field_id}-start"
                end_id = f"{field_id}-end"
                outputs.extend([Output(start_id, "value"), Output(end_id, "value")])
            else:
                # 一般字段
                outputs.append(Output(field_id, "value"))
        
        # 只有当有输出字段时才注册重置回调
        if outputs:
            @app.callback(
                outputs,
                Input(reset_button_id, "n_clicks"),
                prevent_initial_call=True
            )
            def reset_all_fields(reset_clicks):
                if reset_clicks:
                    # 返回所有字段的默认值
                    default_values = []
                    
                    for field in input_fields:
                        if field.get("type") == "date_range":
                            # 日期范围字段返回两个空值
                            default_values.extend(["", ""])
                        elif field.get("type") == "dropdown":
                            # 下拉框返回 None
                            default_values.append(None)
                        else:
                            # 其他字段返回空字符串
                            default_values.append("")
                    
                    return default_values
                
                # 如果没有点击重置按钮，返回当前值（dash.no_update）
                return [dash.no_update] * len(outputs)