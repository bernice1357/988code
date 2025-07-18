from .common import *
import requests
from datetime import datetime
from dash import callback_context, ALL
from dash.exceptions import PreventUpdate

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[

    dcc.Store(id='customer-data-store'),
    dcc.Store(id='current-edit-index'),  # 新增：儲存目前編輯的索引
    success_toast("repurchase_reminder"),
    error_toast("repurchase_reminder"),

    # 編輯備註的Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("編輯備註")),
        dbc.ModalBody([
            html.Div(id="edit-customer-info", style={"marginBottom": "15px"}),
            dbc.Label("備註內容:"),
            dbc.Textarea(
                id="edit-note-textarea",
                placeholder="請輸入備註內容...",
                style={"width": "100%", "height": "100px"}
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-edit-button", className="me-2", color="secondary"),
            dbc.Button("儲存", id="save-edit-button", color="primary")
        ])
    ], id="edit-note-modal", is_open=False, size="lg", centered=True),

    html.Div([
        html.Div([
            html.Span("設定回購提醒天數", style={"marginRight": "10px"}),
            dbc.InputGroup([
                dbc.Input(type="number", placeholder="輸入天數", id="inactive-days-input", min=1, style={"width": "120px"}),
                dbc.InputGroupText("天")
            ], style={"width": "auto", "marginRight": "10px"}),
            dbc.Button("搜尋", id="reminder-confirm-button", color="primary", className="me-2"),
            html.Div([
                dbc.Button("匯出列表資料", id="export-button", n_clicks=0, color="info", outline=True)
            ], style={"marginLeft": "auto"})
        ], className="d-flex align-items-center")
    ], className="mb-3"),

    html.Div(style={"borderBottom": "1px solid #dee2e6"}),

    html.Div([
        html.Div(id="confirm-reminded-button-container"),  # 用於動態顯示按鈕
        html.Div(id="button-group-container", style={"display": "none"})  # 初始隱藏
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px", "marginTop": "20px"}),

    html.Div([
        html.Div(id="repurchase-table-container"),
    ],style={"marginTop": "10px"}),

])

@app.callback(
    [Output("repurchase-table-container", "children"),
     Output("customer-data-store", "data"),
     Output("button-group-container", "children"),
     Output("button-group-container", "style"),
     Output("repurchase_reminder-error-toast", "is_open", allow_duplicate=True),
     Output("repurchase_reminder-error-toast", "children", allow_duplicate=True)],
    [Input("reminder-confirm-button", "n_clicks")],
    [State("inactive-days-input", "value")],
    prevent_initial_call=True
)
def load_repurchase_data(reminder_btn, days_input):
    if not days_input or days_input <= 0:
        return html.Div(), [], html.Div(), {"display": "none"}, True, "請輸入有效的天數"
    
    try:
        response = requests.get(f"http://127.0.0.1:8000/get_repurchase_reminders/{days_input}")
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df.columns = ["id", "提醒狀態", "客戶ID", "客戶名稱", "新品購買品項", "上次購買日期", "過期天數", "備註"]
            
            # 轉換布林值為中文顯示
            df["提醒狀態"] = df["提醒狀態"].map({True: "已提醒", False: "未提醒"})
            
            # 轉換上次購買日期格式（去掉秒數）
            df["上次購買日期"] = pd.to_datetime(df["上次購買日期"]).dt.strftime("%Y/%m/%d %H:%M")
            
            # 保留id欄位但不顯示，只傳遞需要顯示的欄位
            display_df = df[["提醒狀態", "客戶ID", "客戶名稱", "新品購買品項", "上次購買日期", "過期天數", "備註"]]
            
            # 建立按鈕組
            button_group = dbc.ButtonGroup([
                dbc.Button("全部客戶", outline=True, id="btn-all-customers", color="primary"),
                dbc.Button("未提醒客戶", outline=True, id="btn-unreminded-customers", color="primary"),
                dbc.Button("已提醒客戶", outline=True, id="btn-reminded-customers", color="primary")
            ])
            
            # 預設顯示全部客戶
            table_component = custom_table(
                display_df, 
                show_button=True, 
                button_text="編輯備註",
                button_id_type="repurchase-note-btn",
                sticky_columns=["提醒狀態", "客戶ID"],
            )
            
            return table_component, df.to_dict('records'), button_group, {"display": "block"}, False, ""
        else:
            return html.Div("無法載入資料", style={"color": "red"}), [], html.Div(), {"display": "none"}, True, f"無法載入資料，API code: {response.status_code}"
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Exception details: {error_details}")
        return html.Div(f"載入資料時發生錯誤: {str(e)}\n詳細錯誤: {error_details}", style={"color": "red", "whiteSpace": "pre-wrap"}), [], html.Div(), {"display": "none"}, True, f"載入資料時發生錯誤: {str(e)}"

# 處理篩選按鈕點擊
@app.callback(
    [Output("repurchase-table-container", "children", allow_duplicate=True),
     Output("customer-data-store", "data", allow_duplicate=True)],
    [Input("btn-all-customers", "n_clicks"),
     Input("btn-unreminded-customers", "n_clicks"),
     Input("btn-reminded-customers", "n_clicks")],
    [State("customer-data-store", "data")],
    prevent_initial_call=True
)
def filter_customers(btn_all, btn_unreminded, btn_reminded, stored_data):
    ctx = callback_context
    
    if not ctx.triggered or not stored_data:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    df = pd.DataFrame(stored_data)
    display_df = df[["提醒狀態", "客戶ID", "客戶名稱", "新品購買品項", "上次購買日期", "過期天數", "備註"]]
    
    # 判斷按鈕篩選
    show_checkbox = False
    
    if button_id == 'btn-unreminded-customers':
        display_df = display_df[display_df['提醒狀態'] == '未提醒']
        show_checkbox = True
    elif button_id == 'btn-reminded-customers':
        display_df = display_df[display_df['提醒狀態'] == '已提醒']
        show_checkbox = False
    
    # 根據是否顯示勾選框來決定是否傳入 show_checkbox 參數
    if show_checkbox:
        table_component = custom_table(
            display_df, 
            show_checkbox=True, 
            show_button=True, 
            button_text="編輯備註",
            button_id_type="repurchase-note-btn",
            sticky_columns=["提醒狀態", "客戶ID"],
        )
    else:
        table_component = custom_table(
            display_df, 
            show_button=True, 
            button_text="編輯備註",
            button_id_type="repurchase-note-btn",
            sticky_columns=["提醒狀態", "客戶ID"],
        )
    
    return table_component, stored_data

@app.callback(
    Output('confirm-reminded-button-container', 'children'),
    [Input({'type': 'status-checkbox', 'index': ALL}, 'value')]
)
def show_confirm_button(checkbox_values):
    selected_rows = []
    for i, values in enumerate(checkbox_values):
        if values:  # 如果checkbox被選中
            selected_rows.extend(values)
    
    if selected_rows and len(selected_rows) > 0:
        return dbc.Button("確認已提醒", id="confirm-reminded-button", color="success", className="me-2")
    else:
        return html.Div()

@app.callback(
    [Output("repurchase-table-container", "children", allow_duplicate=True),
     Output("customer-data-store", "data", allow_duplicate=True),
     Output("repurchase_reminder-success-toast", "is_open", allow_duplicate=True),
     Output("repurchase_reminder-success-toast", "children", allow_duplicate=True),
     Output("repurchase_reminder-error-toast", "is_open", allow_duplicate=True),
     Output("repurchase_reminder-error-toast", "children", allow_duplicate=True)],
    [Input("confirm-reminded-button", "n_clicks")],
    [State({'type': 'status-checkbox', 'index': ALL}, 'value'),
     State("customer-data-store", "data"),
     State("inactive-days-input", "value")],
    prevent_initial_call=True
)
def update_reminded_status(n_clicks, checkbox_values, stored_data, days_input):
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    
    try:
        # 找出被勾選的列索引
        selected_indices = []
        for i, values in enumerate(checkbox_values):
            if values:  # 如果checkbox被選中
                selected_indices.extend(values)
        
        if not selected_indices:
            raise PreventUpdate
        
        # 從stored_data中找出對應的id
        selected_ids = []
        df = pd.DataFrame(stored_data)
        
        for index in selected_indices:
            if index < len(df):
                selected_ids.append(int(df.iloc[index]['id']))
        
        # 發送PUT API請求更新提醒狀態
        for id in selected_ids:
            response = requests.put(f"http://127.0.0.1:8000/update_repurchase_reminder/{id}")
            if response.status_code != 200:
                print(f"更新ID {id} 失敗: {response.status_code}")
        
        # 重新載入資料
        response = requests.get(f"http://127.0.0.1:8000/get_repurchase_reminders/{days_input}")
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df.columns = ["id", "提醒狀態", "客戶ID", "客戶名稱", "新品購買品項", "上次購買日期", "過期天數", "備註"]
            
            # 轉換布林值為中文顯示
            df["提醒狀態"] = df["提醒狀態"].map({True: "已提醒", False: "未提醒"})
            
            # 轉換上次購買日期格式（去掉秒數）
            df["上次購買日期"] = pd.to_datetime(df["上次購買日期"]).dt.strftime("%Y/%m/%d %H:%M")
            
            # 篩選未提醒客戶（因為按鈕只在未提醒頁面顯示）
            display_df = df[df['提醒狀態'] == '未提醒'][["提醒狀態", "客戶ID", "客戶名稱", "新品購買品項", "上次購買日期", "過期天數", "備註"]]
            
            table_component = custom_table(
                display_df, 
                show_checkbox=True, 
                show_button=True, 
                button_text="編輯備註",
                button_id_type="repurchase-note-btn",
                sticky_columns=["提醒狀態", "客戶ID"],
            )
            
            return table_component, df.to_dict('records'), True, "訂單狀態更改為已確認", False, ""
        else:
            return html.Div(), stored_data, False, "", True, f"無法重新載入資料，API code: {response.status_code}"
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Exception details: {error_details}")
        # 返回錯誤訊息但保持原有資料
        return html.Div(f"更新失敗: {str(e)}", style={"color": "red"}), stored_data, False, "", True, f"更新失敗: {str(e)}"

# 處理編輯備註按鈕點擊，打開Modal
@app.callback(
    [Output("edit-note-modal", "is_open"),
     Output("edit-customer-info", "children"),
     Output("edit-note-textarea", "value"),
     Output("current-edit-index", "data")],
    [Input({'type': 'repurchase-note-btn', 'index': ALL}, 'n_clicks'),
     Input("cancel-edit-button", "n_clicks"),
     Input("save-edit-button", "n_clicks")],
    [State("customer-data-store", "data"),
     State({'type': 'repurchase-note-btn', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def handle_edit_note_modal(edit_clicks, cancel_clicks, save_clicks, stored_data, edit_clicks_state):
    ctx = callback_context
    
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id']
    
    # 取消按鈕或儲存按鈕被點擊，關閉modal
    if "cancel-edit-button" in button_id or "save-edit-button" in button_id:
        return False, html.Div(), "", None
    
    # 編輯按鈕被點擊
    if "repurchase-note-btn" in button_id:
        # 檢查是否真的有點擊（避免初始狀態觸發）
        if ctx.triggered[0]['value'] is None or ctx.triggered[0]['value'] == 0:
            raise PreventUpdate
            
        # 從觸發的按鈕ID中解析索引
        import json
        triggered_prop_id = ctx.triggered[0]['prop_id']
        # 解析出 {"index": X, "type": "repurchase-note-btn"}.n_clicks 中的 X
        start = triggered_prop_id.find('"index":') + len('"index":')
        end = triggered_prop_id.find(',', start)
        if end == -1:
            end = triggered_prop_id.find('}', start)
        clicked_index = int(triggered_prop_id[start:end])
        
        if stored_data and clicked_index < len(stored_data):
            df = pd.DataFrame(stored_data)
            customer_info = df.iloc[clicked_index]
            
            # 顯示客戶資訊
            info_display = html.Div([
                html.Div(f"客戶: {customer_info['客戶名稱']} (ID: {customer_info['客戶ID']})"),
                html.Div(f"新品購買品項: {customer_info['新品購買品項']}")
            ])
            
            return True, info_display, customer_info.get('備註', ''), clicked_index
    
    raise PreventUpdate

# 處理備註儲存
@app.callback(
    [Output("repurchase-table-container", "children", allow_duplicate=True),
     Output("customer-data-store", "data", allow_duplicate=True),
     Output("edit-note-modal", "is_open", allow_duplicate=True),
     Output("repurchase_reminder-success-toast", "is_open", allow_duplicate=True),
     Output("repurchase_reminder-success-toast", "children", allow_duplicate=True),
     Output("repurchase_reminder-error-toast", "is_open", allow_duplicate=True),
     Output("repurchase_reminder-error-toast", "children", allow_duplicate=True)],
    [Input("save-edit-button", "n_clicks")],
    [State("edit-note-textarea", "value"),
     State("customer-data-store", "data"),
     State("current-edit-index", "data"),
     State("inactive-days-input", "value")],
    prevent_initial_call=True
)
def save_note_edit(save_clicks, textarea_value, stored_data, edit_index, days_input):
    if save_clicks is None or save_clicks == 0:
        raise PreventUpdate
    
    try:
        if edit_index is None or not stored_data:
            return html.Div(), stored_data, False, False, "", True, "無法找到要編輯的資料"
        
        df = pd.DataFrame(stored_data)
        customer_id = df.iloc[edit_index]['id']
        
        # 調用API更新備註
        response = requests.put(
            f"http://127.0.0.1:8000/update_repurchase_note/{customer_id}", 
            json={"repurchase_note": textarea_value or ""}
        )
        
        if response.status_code != 200:
            return html.Div(), stored_data, False, False, "", True, f"API更新失敗: {response.status_code}"
        
        # 重新載入資料
        response = requests.get(f"http://127.0.0.1:8000/get_repurchase_reminders/{days_input}")
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df.columns = ["id", "提醒狀態", "客戶ID", "客戶名稱", "新品購買品項", "上次購買日期", "過期天數", "備註"]
            
            # 轉換布林值為中文顯示
            df["提醒狀態"] = df["提醒狀態"].map({True: "已提醒", False: "未提醒"})
            
            # 轉換上次購買日期格式（去掉秒數）
            df["上次購買日期"] = pd.to_datetime(df["上次購買日期"]).dt.strftime("%Y/%m/%d %H:%M")
            
            # 保留原有的篩選邏輯，重新生成表格
            display_df = df[["提醒狀態", "客戶ID", "客戶名稱", "新品購買品項", "上次購買日期", "過期天數", "備註"]]
            
            table_component = custom_table(
                display_df, 
                show_button=True, 
                button_text="編輯備註",
                button_id_type="repurchase-note-btn",
                sticky_columns=["提醒狀態", "客戶ID"],
            )
            
            return table_component, df.to_dict('records'), False, True, "備註已更新", False, ""
        else:
            return html.Div(), stored_data, False, False, "", True, f"無法重新載入資料: {response.status_code}"
        
    except Exception as e:
        print(f"Exception in save_note_edit: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(), stored_data, False, False, "", True, f"儲存失敗: {str(e)}"