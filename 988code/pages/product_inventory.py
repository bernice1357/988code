from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
import requests
import pandas as pd
import urllib.parse
from dash import ALL

# TODO 再來要改新增商品群組

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
    show_date_picker=False
)

layout = html.Div(style={"fontFamily": "sans-serif", "padding": "20px"}, children=[
    dcc.Store(id="page-loaded", data=True),
    dcc.Store(id="inventory-data", data=[]),
    dcc.Store(id="management-mode", data=False),
    dcc.Store(id="modal-table-data", data=[]),
    html.Div([
        html.Div([
            inventory_components["trigger_button"],
            dbc.Button("管理商品群組", id="manage-product-group-button", n_clicks=0, color="primary", outline=True, className="ms-2")
        ], className="d-flex align-items-center"),
        html.Div([
            dbc.Button("匯入 ERP 庫存資料", id="import-erp-button", n_clicks=0, color="info", className="me-2"),
            dbc.Button("匯出列表資料", id="export-button", n_clicks=0, color="success")
        ], className="d-flex align-items-center")
    ], className="mb-3 d-flex justify-content-between align-items-center"),
    inventory_components["offcanvas"],
    html.Div(id="inventory-table-container"),
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle(id="inventory-modal-title"),
            html.Span(id="edit-mode-indicator", children="編輯模式", style={"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"})
        ], id="modal-header"),
        dbc.ModalBody(id="inventory-modal-body"),
        dbc.ModalFooter([
            dbc.Button("編輯品項", id="manage-group-button", n_clicks=0, color="primary", className="me-2"),
            html.Div([
                dbc.Button("儲存", id="save-changes-button", n_clicks=0, color="success", className="me-2", style={"display": "none"}),
                dbc.Button("關閉", id="close-modal", n_clicks=0)
            ], className="ms-auto d-flex")
        ], id="modal-footer"),
    ], id="group-items-modal", is_open=False, size="xl", centered=True, className="", style={"--bs-modal-bg": "white"}),
    
    # 管理商品群組 Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("管理商品群組")
        ]),
        dbc.ModalBody([
            # 類別選擇區域
            html.Div([
                html.Label("選擇類別", className="form-label fw-bold"),
                dcc.Dropdown(
                    id="manage-category-dropdown",
                    placeholder="請選擇類別",
                    clearable=False,
                    style={"width": "100%"}
                )
            ], className="mb-4"),
            
            # 商品群組管理區域
            html.Div([
                # 標題與新增按鈕
                html.Div([
                    html.H6("商品群組列表", className="mb-0"),
                    dbc.Button("+ 新增商品群組", id="add-subcategory-button", size="sm", color="success", outline=True)
                ], className="d-flex justify-content-between align-items-center mb-3"),
                
                # 商品群組列表容器 - 添加滾動樣式
                html.Div(id="subcategory-list-container", children=[
                    html.Div("請先選擇類別", className="text-muted text-center py-4")
                ], style={
                    "maxHeight": "400px",
                    "overflowY": "auto",
                    "border": "1px solid #dee2e6",
                    "borderRadius": "0.375rem",
                    "padding": "15px"
                })
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("關閉", id="close-manage-modal", color="secondary")
        ])
    ], id="manage-subcategory-modal", is_open=False, size="lg", centered=True),
])

register_offcanvas_callback(app, "product_inventory")

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
    Output("inventory-table-container", "children"),
    [Input("inventory-data", "data"),
     Input("product_inventory-inventory_id", "value"),
     Input("product_inventory-subcategory_id", "value")],
    prevent_initial_call=False
)
def display_inventory_table(inventory_data, selected_category, selected_subcategory):
    if not inventory_data:
        return html.Div("暫無資料")
    
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
    df = df[['category', 'subcategory', 'data_count', 'status', 'updated_at']]
    df.columns = ["類別", "商品群組", "規格數量", "狀態", "最後更新日期"]
    
    return button_table(
        df,
        button_text="查看群組品項",
        button_id_type="inventory_data_button",
        address_columns=[],
    )

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
     Output("manage-group-button", "children", allow_duplicate=True),
     Output("save-changes-button", "style", allow_duplicate=True),
     Output("edit-mode-indicator", "style", allow_duplicate=True),
     Output("modal-table-data", "data", allow_duplicate=True)],
    Input("group-items-modal", "is_open"),
    prevent_initial_call=True
)
def reset_management_mode(is_open):
    if not is_open:
        return False, "編輯品項", {"display": "none"}, {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}, []
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

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
                df.columns = ["商品ID", "商品名稱", "規格", "存放地點", "最後更新日期"]
                
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
            except Exception as e:
                print(f"取得商品群組選項時發生錯誤: {e}")
                subcategory_options = [{"label": subcategory, "value": subcategory}]
        
        # 建立管理表格
        table_header = html.Thead([
            html.Tr([
                html.Th("商品ID"),
                html.Th("商品名稱"),
                html.Th("原始商品群組"),
                html.Th("新商品群組")
            ])
        ])
        
        table_rows = []
        for i, item in enumerate(stored_data):
            row = html.Tr([
                html.Td(item.get("商品ID", "")),
                html.Td(item.get("商品名稱", "")),
                html.Td(subcategory),
                html.Td(
                    dcc.Dropdown(
                        id={"type": "subcategory-change-dropdown", "index": i},
                        options=subcategory_options,
                        value=subcategory,
                        clearable=False,
                        style={"minWidth": "200px"}
                    )
                )
            ])
            table_rows.append(row)
        
        table_body = html.Tbody(table_rows)
        
        return dbc.Table([table_header, table_body], 
                       striped=True, 
                       bordered=True, 
                       hover=True,
                       responsive=False,
                       className="mb-0"), stored_data
    else:
        # 查看模式：顯示原始的品項資料表格
        df = pd.DataFrame(stored_data)
        
        return dbc.Table.from_dataframe(
            df, 
            striped=True, 
            bordered=True, 
            hover=True,
            responsive=False,
            className="mb-0"
        ), stored_data

# 管理商品群組按鈕切換模式並更新按鈕文字
@app.callback(
    [Output("management-mode", "data"),
     Output("manage-group-button", "children"),
     Output("save-changes-button", "style"),
     Output("edit-mode-indicator", "style")],
    Input("manage-group-button", "n_clicks"),
    State("management-mode", "data"),
    prevent_initial_call=True
)
def toggle_management_mode(n_clicks, current_mode):
    if n_clicks:
        new_mode = not current_mode
        if new_mode:
            # 切換到管理模式
            button_text = "回到原始表格"
            save_button_style = {"display": "inline-block"}
            edit_indicator_style = {"display": "inline", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}
        else:
            # 切換回查看模式
            button_text = "編輯品項"
            save_button_style = {"display": "none"}
            edit_indicator_style = {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}
        return new_mode, button_text, save_button_style, edit_indicator_style
    return current_mode, "編輯品項", {"display": "none"}, {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}

# 開啟管理商品群組 modal
@app.callback(
    Output("manage-subcategory-modal", "is_open"),
    [Input("manage-product-group-button", "n_clicks"),
     Input("close-manage-modal", "n_clicks")],
    State("manage-subcategory-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_manage_modal(open_clicks, close_clicks, is_open):
    return not is_open

# 載入管理modal的類別選項
@app.callback(
    Output("manage-category-dropdown", "options"),
    Input("manage-subcategory-modal", "is_open"),
    prevent_initial_call=True
)
def load_manage_category_options(is_open):
    if not is_open:
        return []
    
    try:
        response = requests.get("http://127.0.0.1:8000/get_category")
        if response.status_code == 200:
            category_data = response.json()
            return [{"label": item["category"], "value": item["category"]} for item in category_data]
        else:
            return []
    except:
        return []

# 根據選擇的類別載入商品群組列表
@app.callback(
    Output("subcategory-list-container", "children"),
    Input("manage-category-dropdown", "value"),
    prevent_initial_call=True
)
def load_subcategory_list(selected_category):
    return load_subcategory_list_function(selected_category)

# 處理編輯按鈕點擊
# 處理編輯按鈕點擊
@app.callback(
    [Output({"type": "subcategory-input", "index": ALL}, "disabled"),
     Output({"type": "edit-subcategory", "index": ALL}, "children"),
     Output("subcategory-list-container", "children", allow_duplicate=True)],
    Input({"type": "edit-subcategory", "index": ALL}, "n_clicks"),
    [State({"type": "subcategory-input", "index": ALL}, "disabled"),
     State({"type": "edit-subcategory", "index": ALL}, "children"),
     State({"type": "subcategory-input", "index": ALL}, "value"),
     State("manage-category-dropdown", "value")],
    prevent_initial_call=True
)
def toggle_edit_mode(edit_clicks, current_disabled, current_texts, input_values, selected_category):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_disabled, current_texts, dash.no_update
    
    # 檢查是否有任何按鈕被點擊
    if not any(edit_clicks) or all(click is None for click in edit_clicks):
        return current_disabled, current_texts, dash.no_update
    
    # 找到被點擊的按鈕index
    trigger_id = ctx.triggered[0]["prop_id"]
    trigger_value = ctx.triggered[0]["value"]
    
    # 確保觸發值大於0（實際被點擊）
    if not trigger_value or trigger_value <= 0:
        return current_disabled, current_texts, dash.no_update
    
    import re
    match = re.search(r'"index":(\d+)', trigger_id)
    if not match:
        return current_disabled, current_texts, dash.no_update
    
    clicked_index = int(match.group(1))
    
    # 更新對應的input disabled狀態和按鈕文字
    new_disabled = current_disabled.copy()
    new_texts = current_texts.copy()
    
    if clicked_index < len(new_disabled):
        # 如果目前是編輯狀態（disabled=False），表示要完成編輯
        if not current_disabled[clicked_index]:
            # 完成編輯，需要調用API更新資料
            try:
                # 獲取原始商品群組名稱和新的商品群組名稱
                encoded_category = urllib.parse.quote(selected_category, safe="")
                response = requests.get(f"http://127.0.0.1:8000/get_subcategories_of_category/{encoded_category}")
                if response.status_code == 200:
                    subcategory_data = response.json()
                    original_subcategories = subcategory_data.get('subcategories', [])
                    
                    if clicked_index < len(original_subcategories) and clicked_index < len(input_values):
                        old_subcategory = original_subcategories[clicked_index]
                        new_subcategory = input_values[clicked_index]
                        
                        # 如果名稱有變更，調用API更新
                        if old_subcategory != new_subcategory:
                            update_payload = {
                                "old_subcategory": old_subcategory,
                                "new_subcategory": new_subcategory
                            }
                            
                            update_response = requests.put(
                                "http://127.0.0.1:8000/subcategory/batch-update",
                                json=update_payload
                            )
                            
                            if update_response.status_code == 200:
                                print(f"成功更新商品群組: {old_subcategory} -> {new_subcategory}")
                                
                                # 重新載入商品群組列表
                                updated_list = load_subcategory_list_function(selected_category)
                                
                                # 切換回查看狀態
                                new_disabled[clicked_index] = True
                                new_texts[clicked_index] = "編輯"
                                
                                return new_disabled, new_texts, updated_list
                            else:
                                print(f"更新失敗: {update_response.text}")
            except Exception as e:
                print(f"更新商品群組時發生錯誤: {e}")
        
        # 切換編輯狀態
        new_disabled[clicked_index] = not new_disabled[clicked_index]
        new_texts[clicked_index] = "編輯" if new_disabled[clicked_index] else "完成"
    
    return new_disabled, new_texts, dash.no_update

# 獨立的載入商品群組列表函數
# 獨立的載入商品群組列表函數
def load_subcategory_list_function(selected_category):
    if not selected_category:
        return html.Div("請先選擇類別", className="text-muted text-center py-4")
    
    try:
        encoded_category = urllib.parse.quote(selected_category, safe="")
        response = requests.get(f"http://127.0.0.1:8000/get_subcategories_of_category/{encoded_category}")
        if response.status_code == 200:
            subcategory_data = response.json()
            subcategories = subcategory_data.get('subcategories', [])
            
            if not subcategories:
                return html.Div("此類別暫無商品群組", className="text-muted text-center py-4")
            
            # 建立可編輯的商品群組列表
            subcategory_items = []
            for i, subcategory in enumerate(subcategories):
                item = html.Div([
                    dbc.InputGroup([
                        dbc.Input(
                            id={"type": "subcategory-input", "index": i},
                            value=subcategory,
                            placeholder="商品群組名稱",
                            disabled=True
                        ),
                        dbc.Button(
                            "編輯",
                            id={"type": "edit-subcategory", "index": i},
                            color="warning",
                            outline=True,
                            size="sm"
                        )
                    ], className="mb-2")
                ])
                subcategory_items.append(item)
            
            return html.Div(subcategory_items)
        else:
            return html.Div("載入失敗", className="text-muted text-center py-4")
    except:
        return html.Div("載入錯誤", className="text-muted text-center py-4")

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