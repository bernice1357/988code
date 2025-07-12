from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback, register_reset_callback
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
            inventory_components["trigger_button"]
        ], className="d-flex align-items-center"),
        html.Div([
            dbc.Button("匯入 ERP 庫存資料", id="import-erp-button", n_clicks=0, color="info", className="me-2"),
            dbc.Button("匯出列表資料", id="product_inventory-export-button", n_clicks=0, color="success")
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
])

register_offcanvas_callback(app, "product_inventory")

# 註冊重置功能
register_reset_callback(app, "product_inventory", ["inventory_id", "subcategory_id"])

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
     Output("modal-table-data", "data", allow_duplicate=True)],
    Input("group-items-modal", "is_open"),
    prevent_initial_call=True
)
def reset_management_mode(is_open):
    if not is_open:
        return False, {"display": "inline-block"}, {"display": "none"}, {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}, []
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
     Output("edit-mode-indicator", "style")],
    Input("manage-group-button", "n_clicks"),
    State("management-mode", "data"),
    prevent_initial_call=True
)
def toggle_management_mode(n_clicks, current_mode):
    if n_clicks:
        new_mode = not current_mode
        if new_mode:
            # 切換到管理模式 - 隱藏編輯品項按鈕
            edit_button_style = {"display": "none"}
            save_button_style = {"display": "inline-block"}
            edit_indicator_style = {"display": "inline", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}
        else:
            # 切換回查看模式
            edit_button_style = {"display": "inline-block"}
            save_button_style = {"display": "none"}
            edit_indicator_style = {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}
        return new_mode, edit_button_style, save_button_style, edit_indicator_style
    return current_mode, {"display": "inline-block"}, {"display": "none"}, {"display": "none", "color": "red", "fontWeight": "bold", "marginLeft": "20px"}

# 處理儲存變更
@app.callback(
    Output("group-items-modal", "is_open", allow_duplicate=True),
    Input("save-changes-button", "n_clicks"),
    [State({"type": "subcategory-change-dropdown", "index": ALL}, "value"),
     State({"type": "new-subcategory-input", "index": ALL}, "value"),
     State("modal-table-data", "data"),
     State("inventory-modal-title", "children")],
    prevent_initial_call=True
)
def save_changes(n_clicks, dropdown_values, input_values, stored_data, modal_title):
    if not n_clicks or n_clicks == 0:
        return dash.no_update
    
    if not modal_title or "商品群組：" not in modal_title:
        return dash.no_update
    
    original_subcategory = modal_title.replace("商品群組：", "")
    
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
                    
                    update_payload = {
                        "item_id": item_id,
                        "new_subcategory": new_subcategory
                    }
                    
                    response = requests.put(
                        "http://127.0.0.1:8000/product_master/update_subcategory",
                        json=update_payload
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                        print(f"成功更新品項 {item_id} 的商品群組: {original_subcategory} -> {new_subcategory}")
                    else:
                        print(f"更新品項 {item_id} 失敗: {response.text}")
        
        if total_updates > 0:
            print(f"共完成 {success_count}/{total_updates} 項品項更新")
        else:
            print("沒有發現需要更新的品項")
        
        # 關閉 modal，讓使用者回到主表格看到更新
        return False
        
    except Exception as e:
        print(f"儲存變更時發生錯誤: {e}")
        return dash.no_update

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