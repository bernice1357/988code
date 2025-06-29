from dash import html, dcc, Input, Output, callback, ctx
import dash_bootstrap_components as dbc

def create_search_offcanvas(
    page_name,
    input_fields=None,
    title="搜尋條件",
    button_text="搜尋條件",
    width="400px",
    placement="end",
    show_date_picker=True
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
    - show_date_picker: 是否顯示日期選擇器
    """
    
    # 根據頁面名稱生成唯一 ID
    offcanvas_id = f"{page_name}-search-offcanvas"
    button_id = f"{page_name}-open-search-offcanvas"
    search_button_id = f"{page_name}-search-button"
    reset_button_id = f"{page_name}-reset-button"
    date_picker_id = f"{page_name}-date-range-picker"
    
    if input_fields is None:
        input_fields = []
    
    # 建立 Offcanvas 內容
    offcanvas_children = []
    
    # 日期選擇器 (可選)
    if show_date_picker:
        offcanvas_children.append(
            html.Div([
                html.Label("日期範圍", style={"fontSize": "0.9rem", "marginBottom": "4px"}),
                html.Div(
                    dcc.DatePickerRange(
                        id=date_picker_id,
                        start_date='2025-05-01',
                        end_date='2025-05-07',
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
            ], className="mb-3")
        )
    
    # 動態生成輸入框 (確保使用完整的 field_id)
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
        else:
            component = dbc.Input(
                id=field_id,
                type=field.get("type", "text"),
                placeholder=field.get("placeholder", ""),
                className="w-100"
            )
        
        field_div.children.append(component)
        offcanvas_children.append(field_div)
    
    # 按鈕區域
    button_div = html.Div([
        dbc.Button("搜尋", id=search_button_id, color="primary", size="sm", className="me-2"),
        dbc.Button("重置", id=reset_button_id, color="secondary", size="sm")
    ], className="d-flex justify-content-center", style={"position": "absolute", "bottom": "20px", "left": "20px", "right": "20px"})
    
    offcanvas_children.append(button_div)
    
    # 觸發按鈕
    trigger_button = dbc.Button(
        button_text, 
        id=button_id, 
        color="primary", 
        className="mb-3"
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
            "search_button_id": search_button_id,
            "reset_button_id": reset_button_id,
            "date_picker_id": date_picker_id
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
    search_button_id = f"{page_name}-search-button"
    
    @app.callback(
        Output(offcanvas_id, "is_open"),
        [
            Input(button_id, "n_clicks"),
            Input(search_button_id, "n_clicks")
        ],
        prevent_initial_call=True
    )
    def toggle_search_offcanvas(open_clicks, search_clicks):
        if ctx.triggered_id == button_id:
            return True
        elif ctx.triggered_id == search_button_id:
            return False
        return False

# 使用範例：

# 在產品頁面 (product.py)
# from search_offcanvas import create_search_offcanvas, register_offcanvas_callback
# 
# product_input_fields = [
#     {
#         "id": "product-type",
#         "label": "補貨品項",
#         "placeholder": "請輸入補貨品項",
#         "type": "text"
#     },
#     {
#         "id": "customer-id", 
#         "label": "客戶ID",
#         "placeholder": "請輸入客戶ID",
#         "type": "text"
#     },
#     {
#         "id": "status",
#         "label": "狀態",
#         "placeholder": "請選擇狀態",
#         "type": "dropdown",
#         "options": [
#             {"label": "進行中", "value": "active"},
#             {"label": "已完成", "value": "completed"},
#             {"label": "已取消", "value": "cancelled"}
#         ]
#     }
# ]
# 
# product_components = create_search_offcanvas(
#     page_name="product",
#     input_fields=product_input_fields,
#     title="產品搜尋條件",
#     button_text="產品搜尋"
# )
# 
# layout = html.Div([
#     product_components["trigger_button"],
#     product_components["offcanvas"],
#     # 其他頁面內容...
# ])
# 
# register_offcanvas_callback(app, "product")

# 在訂單頁面 (order.py)
# from search_offcanvas import create_search_offcanvas, register_offcanvas_callback
# 
# order_input_fields = [
#     {
#         "id": "order-id",
#         "label": "訂單編號",
#         "placeholder": "請輸入訂單編號",
#         "type": "text"
#     }
# ]
# 
# order_components = create_search_offcanvas(
#     page_name="order",
#     input_fields=order_input_fields,
#     title="訂單搜尋條件",
#     button_text="訂單搜尋",
#     show_date_picker=False
# )
# 
# layout = html.Div([
#     order_components["trigger_button"],
#     order_components["offcanvas"],
#     # 其他頁面內容...
# ])
# 
# register_offcanvas_callback(app, "order")