from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
from callbacks.export_callback import create_export_callback, add_download_component
import requests
import pandas as pd
import urllib.parse
from dash import ALL


# TODO 新增狀態radio搜尋條件

# offcanvas
product_input_fields = [
    {
        "id": "inventory_id", 
        "label": "商品類別",
        "type": "dropdown",
        "options": []
    },
    {
        "id": "subcategory_id",
        "label": "商品群組",
        "type": "dropdown",
        "options": []
    }
]
inventory_components = create_search_offcanvas(
    page_name="product_inventory",
    input_fields=product_input_fields,
)

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[
    dcc.Store(id="page-loaded", data=True),
    dcc.Store(id="inventory-data", data=[]),
    dcc.Store(id="current-table-data", data=[]),  # 新增：儲存當前表格顯示的資料
    dcc.Store(id="management-mode", data=False),
    dcc.Store(id="modal-table-data", data=[]),
    add_download_component("product_inventory"),  # 加入下載元件
    html.Div([
        html.Div([
            # 新增：創建新產品按鈕
            dbc.Button("創建新產品", 
                    id="create-new-product-btn", 
                    n_clicks=0, 
                    color="success", 
                    outline=True,
                    className="me-2"),  # 右邊距
            inventory_components["trigger_button"]
        ], className="d-flex align-items-center"),
        html.Div([
            dbc.Button("匯出列表資料", id="product_inventory-export-button", n_clicks=0, color="primary", outline=True)
        ], className="d-flex align-items-center")
    ], className="mb-3 d-flex justify-content-between align-items-center"),
    inventory_components["offcanvas"],
    dcc.Loading(
        id="loading-inventory-table",
        type="dot",
        children=html.Div(id="inventory-table-container"),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "position": "fixed", 
            "top": "50%",          
        }
    ),
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle(id="inventory-modal-title"),
            html.Span(id="edit-mode-indicator", children="編輯模式", style={"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"})
        ], id="modal-header"),
        dbc.ModalBody(id="inventory-modal-body"),
        dbc.ModalFooter([
            dbc.Button("刪除品項", id="delete-group-button", n_clicks=0, color="danger", className="me-2", style={"display": "none"}),
            dbc.Button("編輯品項", id="manage-group-button", n_clicks=0, color="primary", className="me-2"),
            html.Div([
                dbc.Button("儲存", id="save-changes-button", n_clicks=0, color="success", className="me-2", style={"display": "none"}),
                dbc.Button("關閉", id="close-modal", n_clicks=0)
            ], className="ms-auto d-flex")
        ], id="modal-footer"),
    ], id="group-items-modal", is_open=False, size="xl", centered=True, className="", style={"--bs-modal-bg": "white"}),
    # 刪除確認 Modal
    dbc.Modal(
        id="delete-confirm-modal",
        is_open=False,
        backdrop="static",
        keyboard=False,
        centered=True,
        className="custom-delete-modal",
        style={"z-index": "1060"},
        children=[
            dbc.ModalHeader(
                dbc.ModalTitle("確定刪除品項", id="delete-confirm-modal-title"),
                style={
                    "background-color": "#f8f9fa",
                    "border-bottom": "2px solid #dc3545",
                    "font-weight": "bold",
                    "color": "#dc3545"
                }
            ),
            dbc.ModalBody(
                [
                    html.P(
                        "您確定要刪除以下品項嗎？此操作無法復原。",
                        style={
                            "color": "red",
                            "fontWeight": "bold",
                            "margin-bottom": "15px",
                            "text-align": "center"
                        }
                    ),
                    html.Div(
                        id="delete-items-list",
                        style={
                            "background-color": "#fff3cd",
                            "border": "1px solid #ffeaa7",
                            "border-radius": "5px",
                            "padding": "10px",
                            "margin-top": "10px",
                            "font-weight": "bold",
                            "color": "black"
                        }
                    )
                ],
                style={
                    "padding": "20px",
                    "background-color": "#ffffff"
                }
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "取消",
                        id="delete-cancel-button",
                        n_clicks=0,
                        color="secondary",
                        className="me-2",
                        style={"min-width": "80px"}
                    ),
                    dbc.Button(
                        "確認刪除",
                        id="delete-confirm-button",
                        n_clicks=0,
                        color="danger",
                        style={"min-width": "80px"}
                    )
                ],
                style={
                    "background-color": "#f8f9fa",
                    "border-top": "1px solid #dee2e6",
                    "justify-content": "center",
                    "gap": "10px"
                }
            )
        ]
    ),
    # 創建新產品 Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("創建新產品", id="inventory-new-product-modal-title")
        ]),
        dbc.ModalBody([
            dbc.Row([
                # 左側欄位
                dbc.Col([
                    # 產品ID
                    dbc.Row([
                        dbc.Label("產品ID", width=4),
                        dbc.Col(dbc.Input(id="inventory-new-product-id", type="text", placeholder="請輸入產品編號"), width=8)
                    ], className="mb-3"),
                    # 倉庫ID
                    dbc.Row([
                        dbc.Label("倉庫ID", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-warehouse-id", type="text", placeholder="請輸入倉庫id"),
                            dbc.Tooltip("例如：本倉、物料倉", target="inventory-new-product-warehouse-id", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 產品中文名稱
                    dbc.Row([
                        dbc.Label("產品名稱", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-name-zh", type="text", placeholder="請輸入產品名稱"),
                            dbc.Tooltip("請輸入完整的產品名稱", target="inventory-new-product-name-zh", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 類別
                    dbc.Row([
                        dbc.Label("類別", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-category", type="text", placeholder="請輸入類別"),
                            dbc.Tooltip("例如：消耗品、其他類、白帶魚", target="inventory-new-product-category", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 子類別
                    dbc.Row([
                        dbc.Label("子類別", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-subcategory", type="text", placeholder="請輸入子類別"),
                            dbc.Tooltip("例如：白帶魚切塊、白帶魚片、禮盒", target="inventory-new-product-subcategory", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 規格
                    dbc.Row([
                        dbc.Label("規格", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-specification", type="text", placeholder="請輸入產品規格"),
                            dbc.Tooltip("例如：12K、150/200", target="inventory-new-product-specification", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                ], width=6),
                
                # 右側欄位
                dbc.Col([
                    # 包裝原料
                    dbc.Row([
                        dbc.Label("包裝原料", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-package-raw", type="text", placeholder="請輸入包裝原料"),
                            dbc.Tooltip("例如：10K/箱、500g/包", target="inventory-new-product-package-raw", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 處理方式
                    dbc.Row([
                        dbc.Label("處理方式", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-process-type", type="text", placeholder="請輸入處理方式"),
                            dbc.Tooltip("例如：單尾、無骨", target="inventory-new-product-process-type", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 庫存量
                    dbc.Row([
                        dbc.Label("庫存量", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-stock-quantity", type="number", placeholder="請輸入庫存量", min=0),
                            dbc.Tooltip("請輸入初始庫存數量", target="inventory-new-product-stock-quantity", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 單位
                    dbc.Row([
                        dbc.Label("單位", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-unit", type="text", placeholder="請輸入單位"),
                            dbc.Tooltip("例如：公斤、套、包、尾", target="inventory-new-product-unit", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 供應商ID
                    dbc.Row([
                        dbc.Label("供應商ID", width=4),
                        dbc.Col([
                            dbc.Input(id="inventory-new-product-supplier-id", type="text", placeholder="請輸入供應商id"),
                            dbc.Tooltip("例如：集和、寶田", target="inventory-new-product-supplier-id", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 狀態
                    dbc.Row([
                        dbc.Label("狀態", width=4),
                        dbc.Col([
                            html.Div([
                                dcc.Dropdown(
                                    id="inventory-new-product-is-active",
                                    options=[
                                        {"label": "啟用 (Active)", "value": "active"},
                                        {"label": "停用 (Inactive)", "value": "inactive"}
                                    ],
                                    placeholder="請選擇狀態",
                                    value="active"  # 默認啟用
                                )
                            ], title="選擇產品是否啟用：啟用表示可正常使用，停用表示暫時不可使用")
                        ], width=8)
                    ], className="mb-3"),
                ], width=6)
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="inventory-cancel-product-btn", color="secondary", className="me-2"),
            dbc.Button("創建產品", id="inventory-save-new-product-btn", color="primary"),
        ])
    ], id="inventory-new-product-modal", is_open=False, backdrop="static", keyboard=False, size="xl"),
    success_toast("product_inventory", message=""),
    error_toast("product_inventory", message=""),
    warning_toast("product_inventory", message=""),
    dcc.Store(id='user-role-store'),
])

register_offcanvas_callback(app, "product_inventory")

# 註冊匯出功能 - 使用當前表格資料
create_export_callback(app, "product_inventory", "current-table-data", "商品庫存資料")

# 載入商品類別資料的 callback
@app.callback(
    Output("product_inventory-inventory_id", "options"),
    Input("page-loaded", "data"),
    prevent_initial_call=False
)
def load_category_options(page_loaded):
    try:
        response = requests.get("http://127.0.0.1:8000/get_category")
        if response.status_code == 200:
            category_data = response.json()
            category_options = [{"label": item["category"], "value": item["category"]} for item in category_data]
            return category_options
        else:
            return []
    except:
        return []

# 載入庫存資料的 callback
@app.callback(
    Output("inventory-data", "data"),
    Input("page-loaded", "data"),
    prevent_initial_call=False
)
def load_inventory_data(page_loaded):
    try:
        response = requests.get("http://127.0.0.1:8000/get_inventory_data")
        if response.status_code == 200:
            inventory_data = response.json()
            return inventory_data
        else:
            return []
    except:
        return []

# 顯示庫存表格的 callback
@app.callback(
    [Output("inventory-table-container", "children"),
     Output("current-table-data", "data")],  # 新增：同時更新當前表格資料
    [Input("inventory-data", "data"),
     Input("product_inventory-inventory_id", "value"),
     Input("product_inventory-subcategory_id", "value")],
    prevent_initial_call=False
)
def display_inventory_table(inventory_data, selected_category, selected_subcategory):
    if not inventory_data:
        return html.Div("暫無資料"), []
    
    # 篩選邏輯
    df = pd.DataFrame(inventory_data)
    
    if selected_category:
        df = df[df['category'] == selected_category]
    
    if selected_subcategory:
        df = df[df['subcategory'] == selected_subcategory]

    # 重置索引，讓按鈕index從0開始連續
    df = df.reset_index(drop=True)

    # 轉換 updated_at 欄位格式
    if 'updated_at' in df.columns:
        df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime("%Y-%m-%d %H:%M")

    # 重新排列欄位順序並重新命名
    display_df = df[['category', 'subcategory', 'total_stock_quantity', 'updated_at']]
    display_df.columns = ["類別", "商品群組", "總庫存量", "最後更新日期"]
    
    # 儲存當前表格資料供匯出使用
    current_table_data = display_df.to_dict('records')
    
    table_component = custom_table(
        display_df,
        button_text="查看群組品項",
        button_id_type="inventory_data_button",
        show_button=True,
    )
    
    return table_component, current_table_data

# 處理按鈕點擊開啟modal
@app.callback(
    [Output("group-items-modal", "is_open"),
     Output("inventory-modal-title", "children")],
    [Input({"type": "inventory_data_button", "index": ALL}, "n_clicks"),
     Input("close-modal", "n_clicks")],
    [State("group-items-modal", "is_open"),
     State("inventory-data", "data"),
     State("product_inventory-inventory_id", "value"),
     State("product_inventory-subcategory_id", "value")],
    prevent_initial_call=True
)
def handle_modal_open(button_clicks, close_clicks, is_open, inventory_data, selected_category, selected_subcategory):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"]
    trigger_value = ctx.triggered[0]["value"]
    
    if "close-modal" in trigger_id:
        return False, ""
    
    if "inventory_data_button" in trigger_id and trigger_value and trigger_value > 0:
        try:
            # 從trigger_id中提取index
            import re
            match = re.search(r'"index":(\d+)', trigger_id)
            if match:
                row_index = int(match.group(1))
                
                # 重新篩選資料，確保 index 對應正確
                df = pd.DataFrame(inventory_data)
                if selected_category:
                    df = df[df['category'] == selected_category]
                if selected_subcategory:
                    df = df[df['subcategory'] == selected_subcategory]
                
                # 重置索引，確保連續性
                df = df.reset_index(drop=True)
                filtered_data = df.to_dict('records')
                
                if filtered_data and row_index < len(filtered_data):
                    subcategory = filtered_data[row_index]['subcategory']
                    return True, f"商品群組：{subcategory}"
                    
        except Exception as e:
            print(f"Modal open error: {e}")
    
    return dash.no_update, dash.no_update

# 重置管理模式當modal關閉時
@app.callback(
    [Output("management-mode", "data", allow_duplicate=True),
     Output("manage-group-button", "style", allow_duplicate=True),
     Output("save-changes-button", "style", allow_duplicate=True),
     Output("edit-mode-indicator", "style", allow_duplicate=True),
     Output("delete-group-button", "style", allow_duplicate=True),
     Output("modal-table-data", "data", allow_duplicate=True)],
    Input("group-items-modal", "is_open"),
    prevent_initial_call=True
)
def reset_management_mode(is_open):
    if not is_open:
        return False, {"display": "inline-block"}, {"display": "none"}, {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}, {"display": "none"}, []
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# 當 modal 打開時載入群組品項資料並儲存到 store
@app.callback(
    [Output("inventory-modal-body", "children"),
     Output("modal-table-data", "data")],
    [Input("group-items-modal", "is_open"),
     Input("management-mode", "data")],
    [State("inventory-modal-title", "children"),
     State("modal-table-data", "data")],
    prevent_initial_call=True
)
def load_group_items(is_open, management_mode, modal_title, stored_data):
    if not is_open or not modal_title or "商品群組：" not in modal_title:
        return html.Div("暫無資料"), []
    
    subcategory = modal_title.replace("商品群組：", "")
    
    # 如果是第一次開啟 modal 或 stored_data 為空，則重新從 API 載入資料
    if not stored_data:
        try:
            encoded_subcategory = urllib.parse.quote(subcategory, safe='')
            response = requests.get(f"http://127.0.0.1:8000/get_subcategory_items/{encoded_subcategory}")
            if response.status_code == 200:
                group_items_data = response.json()
                if not group_items_data:
                    return html.Div("暫無資料"), []
                
                # 將資料轉換為 DataFrame 並儲存
                df = pd.DataFrame(group_items_data)
                df.columns = ["商品ID", "商品名稱", "庫存量", "存放地點", "最後更新日期"]
                
                # 日期格式轉換
                if "最後更新日期" in df.columns:
                    df["最後更新日期"] = pd.to_datetime(df["最後更新日期"]).dt.strftime("%Y-%m-%d %H:%M")
                
                stored_data = df.to_dict('records')
            else:
                return html.Div("暫無資料"), []
        except:
            return html.Div("載入資料時發生錯誤"), []
    
    # 使用儲存的資料
    if management_mode:
        # 管理模式：顯示帶有商品群組選擇下拉選單的表格
        # 取得該商品群組所屬的類別
        category = None
        try:
            inventory_response = requests.get("http://127.0.0.1:8000/get_inventory_data")
            if inventory_response.status_code == 200:
                inventory_data = inventory_response.json()
                for item in inventory_data:
                    if item.get('subcategory') == subcategory:
                        category = item.get('category')
                        break
        except:
            pass
        
        # 取得該類別下的所有商品群組選項
        subcategory_options = []
        if category:
            try:
                encoded_category = urllib.parse.quote(category, safe="")
                subcategory_response = requests.get(f"http://127.0.0.1:8000/get_subcategories_of_category/{encoded_category}")
                if subcategory_response.status_code == 200:
                    subcategory_data = subcategory_response.json()
                    subcategories = subcategory_data.get('subcategories', [])
                    subcategory_options = [{"label": item, "value": item} for item in subcategories]
                    # 新增一個選項讓使用者可以輸入新的商品群組
                    subcategory_options.append({"label": "➕ 新增商品群組", "value": "__add_new__"})
            except Exception as e:
                print(f"取得商品群組選項時發生錯誤: {e}")
                subcategory_options = [{"label": subcategory, "value": subcategory}]
        
        # 建立管理表格
        table_header = html.Thead([
            html.Tr([
                html.Th("商品ID", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Th("商品名稱", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Th("原始商品群組", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Th("新商品群組", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"})
            ])
        ])
        
        table_rows = []
        for i, item in enumerate(stored_data):
            row = html.Tr([
                html.Td(item.get("商品ID", ""), style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Td(item.get("商品名稱", ""), style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Td(subcategory, style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Td([
                    dcc.Dropdown(
                        id={"type": "subcategory-change-dropdown", "index": i},
                        options=subcategory_options,
                        value=subcategory,
                        clearable=False,
                        style={"minWidth": "200px", "height": "36px"}
                    ),
                    dbc.Input(
                        id={"type": "new-subcategory-input", "index": i},
                        placeholder="輸入新商品群組名稱",
                        style={"display": "none", "marginTop": "5px", "height": "36px"}
                    )
                ], style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"})
            ], style={"height": "60px", "minHeight": "60px"})
            table_rows.append(row)
        
        table_body = html.Tbody(table_rows)
        
        table_container = html.Div([
            dbc.Table([table_header, table_body], 
                     striped=True, 
                     bordered=True, 
                     hover=True,
                     responsive=False,
                     className="mb-0",
                     style={"width": "100%", "tableLayout": "fixed"})
        ], style={"minHeight": "200px", "maxHeight": "500px", "overflowY": "auto", "width": "100%"})
        
        return table_container, stored_data
    else:
        # 查看模式：顯示原始的品項資料表格
        df = pd.DataFrame(stored_data)
        
        # 手動建立表格以更好控制行高
        table_header = html.Thead([
            html.Tr([
                html.Th("商品ID", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Th("商品名稱", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Th("庫存量", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Th("存放地點", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Th("最後更新日期", style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"})
            ])
        ])
        
        table_rows = []
        for _, item in df.iterrows():
            row = html.Tr([
                html.Td(item.get("商品ID", ""), style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Td(item.get("商品名稱", ""), style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Td(item.get("庫存量", ""), style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Td(item.get("存放地點", ""), style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"}),
                html.Td(item.get("最後更新日期", ""), style={"height": "60px", "minHeight": "60px", "padding": "12px", "verticalAlign": "middle"})
            ], style={"height": "60px", "minHeight": "60px"})
            table_rows.append(row)
        
        table_body = html.Tbody(table_rows)
        
        table_container = html.Div([
            dbc.Table([table_header, table_body], 
                     striped=True, 
                     bordered=True, 
                     hover=True,
                     responsive=False,
                     className="mb-0",
                     style={"width": "100%", "tableLayout": "fixed"})
        ], style={"minHeight": "200px", "maxHeight": "500px", "overflowY": "auto", "width": "100%"})
        
        return table_container, stored_data

# 管理商品群組按鈕切換模式並更新按鈕文字
@app.callback(
    [Output("management-mode", "data"),
     Output("manage-group-button", "style"),
     Output("save-changes-button", "style"),
     Output("edit-mode-indicator", "style"),
     Output("delete-group-button", "style")],
    Input("manage-group-button", "n_clicks"),
    State("management-mode", "data"),
    prevent_initial_call=True
)
def toggle_management_mode(n_clicks, current_mode):
    if n_clicks:
        new_mode = not current_mode
        if new_mode:
            # 切換到管理模式 - 隱藏編輯品項按鈕，顯示儲存和刪除按鈕
            edit_button_style = {"display": "none"}
            save_button_style = {"display": "inline-block"}
            delete_button_style = {"display": "inline-block"}
            edit_indicator_style = {"display": "inline", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}
        else:
            # 切換回查看模式
            edit_button_style = {"display": "inline-block"}
            save_button_style = {"display": "none"}
            delete_button_style = {"display": "none"}
            edit_indicator_style = {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}
        return new_mode, edit_button_style, save_button_style, edit_indicator_style, delete_button_style
    return current_mode, {"display": "inline-block"}, {"display": "none"}, {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}, {"display": "none"}

# 處理儲存變更 - 修正版本，確保資料重新載入
@app.callback(
    [Output("group-items-modal", "is_open", allow_duplicate=True),
     Output("product_inventory-success-toast", "is_open", allow_duplicate=True),
     Output("product_inventory-success-toast", "children", allow_duplicate=True),
     Output("product_inventory-error-toast", "is_open", allow_duplicate=True),
     Output("product_inventory-error-toast", "children", allow_duplicate=True),
     Output("product_inventory-warning-toast", "is_open", allow_duplicate=True),
     Output("product_inventory-warning-toast", "children", allow_duplicate=True),
     Output("inventory-data", "data", allow_duplicate=True),  # 重新載入庫存資料
     Output("modal-table-data", "data", allow_duplicate=True)],  # 清空modal資料
    Input("save-changes-button", "n_clicks"),
    [State({"type": "subcategory-change-dropdown", "index": ALL}, "value"),
     State({"type": "new-subcategory-input", "index": ALL}, "value"),
     State("modal-table-data", "data"),
     State("inventory-modal-title", "children"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def save_changes(n_clicks, dropdown_values, input_values, stored_data, modal_title, user_role):
    print(f"[DEBUG] save_changes called with n_clicks={n_clicks}")
    
    if not n_clicks or n_clicks == 0:
        print("[DEBUG] No clicks, returning no_update")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if not modal_title or "商品群組：" not in modal_title:
        print(f"[DEBUG] Invalid modal_title: {modal_title}")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    original_subcategory = modal_title.replace("商品群組：", "")
    print(f"[DEBUG] Processing subcategory: {original_subcategory}")
    
    try:
        success_count = 0
        total_updates = 0
        
        # 逐一處理每個品項的變更
        for i, (dropdown_value, input_value) in enumerate(zip(dropdown_values, input_values)):
            if i < len(stored_data):
                item_id = stored_data[i].get("商品ID", "")
                if not item_id:
                    continue
                
                # 確定新的商品群組名稱
                new_subcategory = None
                if dropdown_value == "__add_new__" and input_value and input_value.strip():
                    new_subcategory = input_value.strip()
                elif dropdown_value and dropdown_value != "__add_new__":
                    new_subcategory = dropdown_value
                
                # 如果商品群組有變更且新商品群組有效
                if new_subcategory and new_subcategory != original_subcategory:
                    total_updates += 1
                    print(f"[DEBUG] Updating item {item_id}: {original_subcategory} -> {new_subcategory}")
                    
                    update_payload = {
                        "item_id": item_id,
                        "new_subcategory": new_subcategory,
                        "user_role": user_role or "viewer"
                    }
                    
                    response = requests.put(
                        "http://127.0.0.1:8000/product_master/update_subcategory",
                        json=update_payload
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                        print(f"[DEBUG] 成功更新品項 {item_id} 的商品群組: {original_subcategory} -> {new_subcategory}")
                    elif response.status_code == 403:
                        print(f"[DEBUG] 權限不足錯誤")
                        return False, False, "", False, "", True, "權限不足：僅限編輯者使用此功能", dash.no_update, dash.no_update
                    else:
                        print(f"[DEBUG] 更新品項 {item_id} 失敗: {response.text}")
        
        # 重新從API載入最新的庫存資料 - 不管是否有更新都重新載入
        updated_inventory_data = []
        try:
            print("[DEBUG] 開始重新載入庫存資料")
            reload_response = requests.get("http://127.0.0.1:8000/get_inventory_data")
            if reload_response.status_code == 200:
                updated_inventory_data = reload_response.json()
                print(f"[DEBUG] 成功重新載入庫存資料，共 {len(updated_inventory_data)} 筆")
            else:
                print(f"[DEBUG] 重新載入庫存資料失敗: {reload_response.status_code}")
                # 即使載入失敗，也返回空列表，這會觸發 display_inventory_table
                updated_inventory_data = []
        except Exception as reload_error:
            print(f"[DEBUG] 重新載入庫存資料時發生錯誤: {reload_error}")
            updated_inventory_data = []
        
        if total_updates > 0:
            success_msg = f"共完成 {success_count}/{total_updates} 項品項更新"
            print(f"[DEBUG] 成功訊息: {success_msg}")
            # 關閉modal，顯示成功訊息，重新載入資料，清空modal資料
            return False, True, success_msg, False, "", False, "", updated_inventory_data, []
        else:
            info_msg = "沒有發現需要更新的品項"
            print(f"[DEBUG] 資訊訊息: {info_msg}")
            # 即使沒有更新，也重新載入資料來刷新顯示
            return False, True, info_msg, False, "", False, "", updated_inventory_data, []
        
    except Exception as e:
        error_msg = f"儲存變更時發生錯誤: {e}"
        print(f"[DEBUG] 錯誤: {error_msg}")
        return False, False, "", True, error_msg, False, "", dash.no_update, dash.no_update

# 處理下拉選單變更，顯示/隱藏新商品群組輸入框
@app.callback(
    [Output({"type": "new-subcategory-input", "index": ALL}, "style"),
     Output({"type": "new-subcategory-input", "index": ALL}, "value")],
    Input({"type": "subcategory-change-dropdown", "index": ALL}, "value"),
    prevent_initial_call=True
)
def toggle_new_subcategory_input(dropdown_values):
    styles = []
    values = []
    
    for value in dropdown_values:
        if value == "__add_new__":
            styles.append({"display": "block", "marginTop": "5px", "height": "36px"})
            values.append("")
        else:
            styles.append({"display": "none", "marginTop": "5px", "height": "36px"})
            values.append("")
    
    return styles, values

# 處理刪除按鈕點擊 - 開啟確認 Modal
@app.callback(
    [Output("delete-confirm-modal", "is_open"),
     Output("delete-items-list", "children")],
    [Input("delete-group-button", "n_clicks"),
     Input("delete-cancel-button", "n_clicks")],
    [State("delete-confirm-modal", "is_open"),
     State("modal-table-data", "data"),
     State("inventory-modal-title", "children")],
    prevent_initial_call=True
)
def handle_delete_button(delete_clicks, cancel_clicks, is_open, stored_data, modal_title):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_value = ctx.triggered[0]["value"]

    if trigger_id == "delete-cancel-button" and cancel_clicks:
        return False, dash.no_update

    if trigger_id == "delete-group-button" and delete_clicks and trigger_value > 0:
        if not stored_data or not modal_title or "商品群組：" not in modal_title:
            return dash.no_update, dash.no_update

        subcategory = modal_title.replace("商品群組：", "")

        # 建立要刪除的品項列表
        items_list = []
        items_list.append(html.H6(f"商品群組：{subcategory}", style={"color": "#dc3545", "marginBottom": "10px"}))

        for item in stored_data:
            product_id = item.get("商品ID", "")
            product_name = item.get("商品名稱", "")
            if product_id:
                items_list.append(
                    html.Div([
                        html.Strong(f"• {product_id}"),
                        html.Span(f" - {product_name}", style={"marginLeft": "10px"})
                    ], style={"marginBottom": "5px"})
                )

        items_list.append(html.Hr(style={"margin": "10px 0"}))
        items_list.append(html.P(f"共計 {len(stored_data)} 個品項將被刪除", style={"fontWeight": "bold", "color": "#dc3545"}))

        return True, items_list

    return dash.no_update, dash.no_update

# 執行刪除確認
@app.callback(
    [Output("delete-confirm-modal", "is_open", allow_duplicate=True),
     Output("group-items-modal", "is_open", allow_duplicate=True),
     Output("product_inventory-success-toast", "is_open", allow_duplicate=True),
     Output("product_inventory-success-toast", "children", allow_duplicate=True),
     Output("product_inventory-error-toast", "is_open", allow_duplicate=True),
     Output("product_inventory-error-toast", "children", allow_duplicate=True),
     Output("inventory-data", "data", allow_duplicate=True)],
    Input("delete-confirm-button", "n_clicks"),
    [State("modal-table-data", "data"),
     State("inventory-modal-title", "children"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def execute_delete(n_clicks, stored_data, modal_title, user_role):
    if not n_clicks or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if not stored_data or not modal_title or "商品群組：" not in modal_title:
        return False, dash.no_update, False, "", True, "無效的品項資料", dash.no_update

    subcategory = modal_title.replace("商品群組：", "")

    try:
        success_count = 0
        total_deletes = 0
        failed_items = []

        for item in stored_data:
            product_id = item.get("商品ID", "")
            if not product_id:
                continue

            total_deletes += 1

            # 準備刪除請求
            delete_payload = {
                "product_id": product_id,
                "user_role": user_role or "viewer"
            }

            # 呼叫刪除 API
            response = requests.delete(
                "http://127.0.0.1:8000/product/delete",
                json=delete_payload
            )

            if response.status_code == 200:
                success_count += 1
                print(f"[DEBUG] 成功刪除品項 {product_id}")
            elif response.status_code == 403:
                return False, dash.no_update, False, "", True, "權限不足：僅限編輯者使用此功能", dash.no_update
            else:
                failed_items.append(product_id)
                print(f"[DEBUG] 刪除品項 {product_id} 失敗: {response.text}")

        # 重新載入庫存資料
        updated_inventory_data = []
        try:
            reload_response = requests.get("http://127.0.0.1:8000/get_inventory_data")
            if reload_response.status_code == 200:
                updated_inventory_data = reload_response.json()
                print(f"[DEBUG] 成功重新載入庫存資料，共 {len(updated_inventory_data)} 筆")
            else:
                print(f"[DEBUG] 重新載入庫存資料失敗: {reload_response.status_code}")
                updated_inventory_data = []
        except Exception as reload_error:
            print(f"[DEBUG] 重新載入庫存資料時發生錯誤: {reload_error}")
            updated_inventory_data = []

        # 準備結果訊息
        if failed_items:
            if success_count > 0:
                error_msg = f"部分刪除成功：{success_count}/{total_deletes} 項。失敗項目：{', '.join(failed_items)}"
                return False, False, False, "", True, error_msg, updated_inventory_data
            else:
                error_msg = f"刪除失敗，失敗項目：{', '.join(failed_items)}"
                return False, dash.no_update, False, "", True, error_msg, dash.no_update
        else:
            success_msg = f"成功刪除 {success_count} 個品項"
            return False, False, True, success_msg, False, "", updated_inventory_data

    except Exception as e:
        error_msg = f"刪除品項時發生錯誤: {str(e)}"
        print(f"[DEBUG] 錯誤: {error_msg}")
        return False, dash.no_update, False, "", True, error_msg, dash.no_update

# 更新搜尋條件的商品群組選項
@app.callback(
    Output("product_inventory-subcategory_id", "options"),
    Input("product_inventory-inventory_id", "value"),
)
def update_subcategory_options(selected_category):
    if not selected_category:
        return []
    
    try:
        encoded_category = urllib.parse.quote(selected_category, safe="")
        response = requests.get(f"http://127.0.0.1:8000/get_subcategories_of_category/{encoded_category}")
        if response.status_code == 200:
            subcategory_data = response.json()
            subcategories = subcategory_data.get('subcategories', [])
            return [{"label": item, "value": item} for item in subcategories]
        else:
            return []
    except Exception as e:
        print(f"發生錯誤: {e}")
        return []
    
# 開啟創建新產品 Modal
@app.callback(
    Output("inventory-new-product-modal", "is_open"),
    [Input("create-new-product-btn", "n_clicks"),
     Input("inventory-cancel-product-btn", "n_clicks")],
    [State("inventory-new-product-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_new_product_modal(create_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "create-new-product-btn" and create_clicks:
        return True
    elif button_id == "inventory-cancel-product-btn" and cancel_clicks:
        return False
    
    return is_open

# 創建新產品
@app.callback(
    [Output("inventory-new-product-modal", "is_open", allow_duplicate=True),
     Output("product_inventory-success-toast", "is_open", allow_duplicate=True),
     Output("product_inventory-success-toast", "children", allow_duplicate=True),
     Output("product_inventory-error-toast", "is_open", allow_duplicate=True),
     Output("product_inventory-error-toast", "children", allow_duplicate=True),
     Output("inventory-data", "data", allow_duplicate=True)],  # 重新載入庫存資料
    Input("inventory-save-new-product-btn", "n_clicks"),
    [State("inventory-new-product-id", "value"),
     State("inventory-new-product-warehouse-id", "value"),
     State("inventory-new-product-name-zh", "value"),
     State("inventory-new-product-category", "value"),
     State("inventory-new-product-subcategory", "value"),
     State("inventory-new-product-specification", "value"),
     State("inventory-new-product-package-raw", "value"),
     State("inventory-new-product-process-type", "value"),
     State("inventory-new-product-stock-quantity", "value"),
     State("inventory-new-product-unit", "value"),
     State("inventory-new-product-supplier-id", "value"),
     State("inventory-new-product-is-active", "value"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def create_new_product(n_clicks, product_id, warehouse_id, name_zh, category, subcategory,
                      specification, package_raw, process_type, stock_quantity, unit, supplier_id, is_active, user_role):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # 驗證必填欄位
    if not all([product_id, warehouse_id, name_zh, category, subcategory]):
        return (dash.no_update, False, "", True, "請填寫所有必填欄位（產品ID、倉庫ID、產品名稱、類別、子類別）", 
                dash.no_update)
    
    try:
        # 準備產品資料
        product_data = {
            "product_id": product_id.strip(),
            "warehouse_id": warehouse_id.strip(),
            "name_zh": name_zh.strip(),
            "category": category.strip(),
            "subcategory": subcategory.strip(),
            "specification": specification.strip() if specification else "",
            "package_raw": package_raw.strip() if package_raw else "",
            "process_type": process_type.strip() if process_type else "",
            "unit": unit.strip() if unit else "",
            "supplier_id": supplier_id.strip() if supplier_id else "",
            "is_active": is_active if is_active else "active",
            "stock_quantity": stock_quantity if stock_quantity is not None else 0,
            "total_quantity": stock_quantity if stock_quantity is not None else 0,
            "user_role": user_role or "viewer"
        }
        
        # 呼叫 API 創建產品
        response = requests.post("http://127.0.0.1:8000/product/create", json=product_data)
        
        if response.status_code == 200:
            # 重新載入庫存資料
            try:
                inventory_response = requests.get("http://127.0.0.1:8000/get_inventory_data")
                if inventory_response.status_code == 200:
                    updated_inventory_data = inventory_response.json()
                else:
                    updated_inventory_data = dash.no_update
            except:
                updated_inventory_data = dash.no_update
            
            return (False, True, f"產品 {product_id} 創建成功！", False, "", updated_inventory_data)
        else:
            error_detail = response.json().get("detail", "創建失敗")
            return (dash.no_update, False, "", True, f"創建產品失敗：{error_detail}", dash.no_update)
            
    except Exception as e:
        return (dash.no_update, False, "", True, f"創建產品時發生錯誤：{str(e)}", dash.no_update)

# 重置 Modal 表單欄位
@app.callback(
    [Output("inventory-new-product-id", "value"),
     Output("inventory-new-product-warehouse-id", "value"),
     Output("inventory-new-product-name-zh", "value"),
     Output("inventory-new-product-category", "value"),
     Output("inventory-new-product-subcategory", "value"),
     Output("inventory-new-product-specification", "value"),
     Output("inventory-new-product-package-raw", "value"),
     Output("inventory-new-product-process-type", "value"),
     Output("inventory-new-product-stock-quantity", "value"),
     Output("inventory-new-product-unit", "value"),
     Output("inventory-new-product-supplier-id", "value"),
     Output("inventory-new-product-is-active", "value")],
    Input("inventory-new-product-modal", "is_open"),
    prevent_initial_call=True
)
def reset_product_form(is_open):
    if is_open:
        # Modal 開啟時不重置
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    else:
        # Modal 關閉時重置所有欄位
        return "", "", "", "", "", "", "", "", "", "", "", "active"