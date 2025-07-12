from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
import requests

product_input_fields = [
    {
        "id": "customer-id", 
        "label": "客戶ID",
        "type": "dropdown"
    },
    {
        "id": "product-type",
        "label": "商品類別",
        "type": "dropdown"
    },
]

repurchase_reminder_components = create_search_offcanvas(
    page_name="repurchase_reminder",
    input_fields=product_input_fields
)

layout = html.Div(style={"fontFamily": "sans-serif"}, children=[

    html.Div([
        html.Div([
            repurchase_reminder_components["trigger_button"],
            html.Div([
                # TODO 要問數值要存哪
                dbc.Button("回購提醒時間", id="reminder-setting-button", n_clicks=0, color="primary", outline=True, className="ms-2"),
                dbc.Popover([
                    dbc.InputGroup([
                        dbc.Input(type="number", placeholder="輸入天數", id="inactive-days-input", min=1, style={"width": "50px", "fontSize": "0.875rem"}),
                        dbc.InputGroupText("天", style={"fontSize": "0.875rem"})
                    ], style={"marginBottom": "10px"}),
                    dbc.Button("確定", id="reminder-confirm-button", color="primary", size="sm")
                ], target="reminder-setting-button", trigger="click", placement="bottom-start", style={"padding": "15px", "width": "300px"})
            ], style={"display": "inline-block"}),
            dbc.Button("匯出列表資料", id="export-button", n_clicks=0, color="success", className="ms-auto")
        ], className="d-flex align-items-center")
    ], className="mb-3"),

    repurchase_reminder_components["offcanvas"],

    html.Div([
        html.Div(id="repurchase-table-container"),
    ],style={"marginTop": "10px"}),

])

@app.callback(
    Output("repurchase-table-container", "children"),
    Input("repurchase-table-container", "id")
)
def load_repurchase_data(_):
    try:
        response = requests.get("http://127.0.0.1:8000/get_repurchase_data")
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            print(df)
            df.columns = ["客戶ID", "客戶名稱", "新品購買品項", "上次購買日期", "過期天數", "備註", "提醒狀態"]
            
            # 轉換布林值為中文顯示
            df["提醒狀態"] = df["提醒狀態"].map({True: "已提醒", False: "未提醒"})
            
            return custom_table(df, show_checkbox=True, show_button=True, button_text="查看")
        else:
            return html.Div("無法載入資料", style={"color": "red"})
    except Exception as e:
        return html.Div(f"載入資料時發生錯誤: {str(e)}", style={"color": "red"})

register_offcanvas_callback(app, "repurchase_reminder")