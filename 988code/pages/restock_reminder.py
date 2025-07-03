from .common import *
from callbacks import restock_reminder_callback
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
import requests

# 從API取得資料
try:
    e=10000
    response = requests.get('http://127.0.0.1:8000/get_restock_transactions')
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
    else:
        print(f"API請求失敗: {response.status_code}")
        df = pd.DataFrame()
except Exception as e:
    print(f"API請求錯誤: {e}")
    df = pd.DataFrame()

# offcanvas
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
restock_offcanvas = create_search_offcanvas(
    page_name="buy_new_item",
    input_fields=product_input_fields,
)

layout = html.Div(style={"fontFamily": "sans-serif", "padding": "20px"}, children=[

    # 觸發 Offcanvas 的按鈕
    create_error_toast(message="API請求錯誤:"),
    restock_offcanvas["trigger_button"],
    restock_offcanvas["offcanvas"],
    html.Div([
        button_table(df, button_text="查看歷史補貨紀錄")
    ], style={"marginTop": "20px"}),
    
    dbc.Modal(
        id="detail-modal",
        size="xl",
        is_open=False,
        centered=True,
        children=[
            dbc.ModalBody(id="modal-body"),
        ]
    )
])