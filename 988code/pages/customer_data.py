from .common import *

# 呼叫API
response = requests.get("http://127.0.0.1:8000/get_customer_data")
if response.status_code == 200:
    try:
        df = response.json()
        df = pd.DataFrame(df)
        df = df.rename(columns={
                "customer_id": "客戶ID",
                "customer_name": "客戶名稱",
                "address": "地址",
                "updated_date": "最後更新日期",
                "notes": "產品名稱"
            })
    except requests.exceptions.JSONDecodeError:
        print("回應內容不是有效的 JSON")
else:
    print(f"get_customer_data API 錯誤，狀態碼：{response.status_code}")

# df = pd.DataFrame([
#     {"客戶ID": "C001", "客戶名稱": "美味快餐", "地址": "台北市中山區南京東路100號", "最後更新日期": "2025/6/20", "產品名稱": "白口魚150/180 10K"},
#     {"客戶ID": "C002", "客戶名稱": "幸福餐館", "地址": "新北市板橋區文化路50號", "最後更新日期": "2025/6/21", "產品名稱": "秋刀魚L級 20K"},
#     {"客戶ID": "C003", "客戶名稱": "小吃天堂", "地址": "台中市西屯區河南路三段66號", "最後更新日期": "2025/6/22", "產品名稱": "鯖魚片 5K"},
#     {"客戶ID": "C004", "客戶名稱": "阿忠海產", "地址": "高雄市鼓山區裕誠路120號", "最後更新日期": "2025/6/23", "產品名稱": "鮭魚切片 8K"},
#     {"客戶ID": "C005", "客戶名稱": "鱻味料理", "地址": "基隆市仁愛區孝三路8號", "最後更新日期": "2025/6/24", "產品名稱": "紅魽魚頭 3K"}
# ])

layout = html.Div(style={"fontFamily": "sans-serif", "padding": "20px"}, children=[
    # 篩選條件區
    html.Div(
        dbc.Row(
            [
                # 客戶 ID 輸入欄
                dbc.Col(
                    dbc.Input(
                        id="customer-id-input",
                        placeholder="客戶 ID",
                        type="text",
                        className="w-100"
                    ),
                    width="auto"
                ),
                # 匯入按鈕
                dbc.Col(
                    dbc.Button("匯入 ERP 客戶資料", id="import-button", n_clicks=0, color="primary"),
                    width="auto"
                ),
                # 匯出按鈕
                dbc.Col(
                    dbc.Button("匯出列表客戶資料", id="export-button", n_clicks=0, color="secondary"),
                    width="auto"
                ),
            ],
            className="g-2",
            align="center",
            justify="start",
            style={"marginBottom": "10px"}
        )
    ),
    html.Div([
        customer_table(df)
    ],style={"marginTop": "20px"}),
    dbc.Modal(
        id="detail-modal",
        size="xl",
        is_open=False,
        children=[
            dbc.ModalBody(id="modal-body"),
        ]
    )
])