from .common import *
import requests
from datetime import datetime
from dash import callback_context, ALL
from dash.exceptions import PreventUpdate

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[

    dcc.Store(id='customer-data-store'),
    success_toast("repurchase_reminder"),
    error_toast("repurchase_reminder"),

    html.Div([
        html.Div([
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
        dbc.ButtonGroup([
            dbc.Button("全部客戶", outline=True, id="btn-all-customers", color="primary"),
            dbc.Button("未提醒客戶", outline=True, id="btn-unreminded-customers", color="primary"),
            dbc.Button("已提醒客戶", outline=True, id="btn-reminded-customers", color="primary")
        ])
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px", "marginTop": "20px"}),

    html.Div([
        html.Div(id="repurchase-table-container"),
    ],style={"marginTop": "10px"}),

])

@app.callback(
    [Output("repurchase-table-container", "children"),
     Output("customer-data-store", "data"),
     Output("repurchase_reminder-error-toast", "is_open", allow_duplicate=True),
     Output("repurchase_reminder-error-toast", "children", allow_duplicate=True)],
    [Input("reminder-confirm-button", "n_clicks"),
     Input("btn-all-customers", "n_clicks"),
     Input("btn-unreminded-customers", "n_clicks"),
     Input("btn-reminded-customers", "n_clicks")],
    [State("inactive-days-input", "value")],
    prevent_initial_call=True
)
def load_repurchase_data(reminder_btn, btn_all, btn_unreminded, btn_reminded, days_input):
    ctx = callback_context
    
    # 如果沒有任何按鈕被觸發，或者搜尋按鈕被按下但沒有輸入天數，則不執行
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # 如果是搜尋按鈕被觸發，但沒有輸入天數，則不執行
    if button_id == 'reminder-confirm-button' and (not days_input or days_input <= 0):
        return html.Div(), [], True, "請輸入有效的天數"
    
    try:
        # 如果沒有輸入天數，返回空結果
        if not days_input or days_input <= 0:
            return html.Div(), [], False, ""
            
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
            
            # 判斷按鈕篩選
            show_checkbox = False  # 預設不顯示勾選框
            
            if button_id == 'btn-unreminded-customers':
                display_df = display_df[display_df['提醒狀態'] == '未提醒']
                show_checkbox = True  # 只有未提醒客戶才顯示勾選框
            elif button_id == 'btn-reminded-customers':
                display_df = display_df[display_df['提醒狀態'] == '已提醒']
                show_checkbox = False  # 已提醒客戶不顯示勾選框
            
            # 根據是否顯示勾選框來決定是否傳入 show_checkbox 參數
            if show_checkbox:
                table_component = custom_table(
                    display_df, 
                    show_checkbox=True, 
                    show_button=True, 
                    button_text="編輯備註",
                    sticky_columns=["提醒狀態", "客戶ID"],
                )
            else:
                table_component = custom_table(
                    display_df, 
                    show_button=True, 
                    button_text="編輯備註",
                    sticky_columns=["提醒狀態", "客戶ID"],
                )
            
            return table_component, df.to_dict('records'), False, ""
        else:
            return html.Div("無法載入資料", style={"color": "red"}), [], True, f"無法載入資料，API code: {response.status_code}"
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Exception details: {error_details}")
        return html.Div(f"載入資料時發生錯誤: {str(e)}\n詳細錯誤: {error_details}", style={"color": "red", "whiteSpace": "pre-wrap"}), [], True, f"載入資料時發生錯誤: {str(e)}"

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