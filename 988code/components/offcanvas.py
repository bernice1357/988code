from dash import html, dcc, Input, Output, callback, ctx, dash
import dash_bootstrap_components as dbc

# TODO 把日期改成內建的

def create_search_offcanvas(
    page_name,
    input_fields=None,
    title="搜尋條件",
    button_text="搜尋條件",
    width="400px",
    placement="end"
):
    """
    創建通用搜尋 Offcanvas 組件
    
    參數:
    - page_name: 頁面名稱，用於生成唯一的 ID
    - input_fields: 輸入框列表，格式為 [{"id": "field-id", "label": "欄位名稱", "placeholder": "提示文字", "type": "text"}]
    - title: Offcanvas 標題
    - button_text: 觸發按鈕文字
    - width: Offcanvas 寬度
    - placement: Offcanvas 位置 ("start", "end", "top", "bottom")
    """
    
    # 根據頁面名稱生成唯一 ID
    offcanvas_id = f"{page_name}-search-offcanvas"
    button_id = f"{page_name}-open-search-offcanvas"
    reset_button_id = f"{page_name}-reset-button"
    
    if input_fields is None:
        input_fields = []
    
    # 建立 Offcanvas 內容
    offcanvas_children = []
    
    # 動態生成輸入框
    for field in input_fields:
        field_id = f"{page_name}-{field['id']}" if not field['id'].startswith(page_name) else field['id']
        field_div = html.Div([
            html.Label(
                field.get("label", ""), 
                htmlFor=field_id, 
                style={"fontSize": "0.9rem", "marginBottom": "4px"}
            )
        ], className="mb-3")
        
        # 根據類型創建不同的輸入組件
        if field.get("type") == "dropdown":
            component = dcc.Dropdown(
                id=field_id,
                options=field.get("options", []),
                placeholder=field.get("placeholder", ""),
                className="w-100"
            )
        elif field.get("type") == "date_range":
            component = html.Div(
                dcc.DatePickerRange(
                    id=field_id,
                    start_date=field.get("start_date", ""),
                    end_date=field.get("end_date", ""),
                    display_format='YYYY-MM-DD',
                    style={
                        "width": "100%",
                        "color": "#495057",
                        "backgroundColor": "#fff",
                        "border": "1px solid #ced4da",
                        "borderRadius": "0.375rem"
                    }
                ),
                style={"width": "100%"}
            )
        else:
            component = dbc.Input(
                id=field_id,
                type=field.get("type", "text"),
                placeholder=field.get("placeholder", ""),
                className="w-100"
            )
        
        field_div.children.append(component)
        offcanvas_children.append(field_div)
    
    # 按鈕區域 - 重置按鈕字體放大
    button_div = html.Div([
        dbc.Button(
            "重置", 
            id=reset_button_id, 
            color="secondary", 
            size="sm",
            style={"fontSize": "1rem"}  # 放大字體
        )
    ], className="d-flex justify-content-center", style={"position": "absolute", "bottom": "20px", "left": "20px", "right": "20px"})
    
    offcanvas_children.append(button_div)
    
    # 觸發按鈕
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
    註冊 Offcanvas 的回調函數
    
    參數:
    - app: Dash app 實例
    - page_name: 頁面名稱
    """
    
    offcanvas_id = f"{page_name}-search-offcanvas"
    button_id = f"{page_name}-open-search-offcanvas"
    
    @app.callback(
        Output(offcanvas_id, "is_open"),
        Input(button_id, "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_search_offcanvas(open_clicks):
        if open_clicks:
            return True
        return False

def register_reset_callback(
    app,
    page_name,
    field_ids
):
    """
    註冊重置功能的回調函數
    
    參數:
    - app: Dash app 實例
    - page_name: 頁面名稱
    - field_ids: 需要重置的欄位 ID 列表
    """
    
    reset_button_id = f"{page_name}-reset-button"
    
    # 動態生成完整的 field_ids
    full_field_ids = []
    outputs = []
    
    for field_id in field_ids:
        full_field_id = f"{page_name}-{field_id}" if not field_id.startswith(page_name) else field_id
        full_field_ids.append(full_field_id)
        outputs.append(Output(full_field_id, "value"))
    
    @app.callback(
        outputs,
        Input(reset_button_id, "n_clicks"),
        prevent_initial_call=True
    )
    def reset_search_filters(n_clicks):
        if n_clicks:
            # 返回與欄位數量相同的 None 值
            return [None] * len(field_ids)
        return [dash.no_update] * len(field_ids)