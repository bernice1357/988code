'''
首頁
'''

from .common import *

# 呼叫API
response = requests.get("http://127.0.0.1:8000/get_new_orders")
if response.status_code == 200:
    try:
        orders = response.json()
    except requests.exceptions.JSONDecodeError:
        print("回應內容不是有效的 JSON")
else:
    print(f"API 錯誤，狀態碼：{response.status_code}")

def make_card_item(order):
    # 卡片標題：左邊顯示客戶ID
    title = html.Div([
        html.Span(order["customer_line_id"], style={"fontWeight": "bold"})
    ])

    return dbc.Card([
        dbc.CardHeader(title),
        dbc.CardBody([
            # 對話紀錄區塊
            html.Div([
                html.Small("對話紀錄", className="text-muted mb-1 d-block text-primary"),
                html.Pre(order["conversation_record"], style={"whiteSpace": "pre-wrap", "fontSize": "0.9rem"})
            ], className="mb-3"),

            html.Div(style={"borderTop": "1px solid #dee2e6", "margin": "15px 0"}),

            # 購買紀錄區塊
            html.Div([
                html.Small("購買解析", className="text-muted mb-1 d-block text-primary"),
                html.Pre(order["purchase_record"], style={"whiteSpace": "pre-wrap", "fontSize": "0.9rem"})
            ], className="mb-3"),

            html.Div([
                dbc.Button("確定", size="sm", color="dark", outline=True),
                dbc.Button("刪除", size="sm", color="danger", outline=True)
            ], className="d-flex justify-content-end mt-2")
        ]),
        html.Div([
            dbc.Badge("新品提醒", color="danger", className="me-4 rounded-pill"),
            dbc.Badge("備註與歷史提醒", color="danger", className="me-4 rounded-pill")
        ], style={
            "position": "absolute",
            "top": "10px",
            "right": "10px"
        })
    ], style={"backgroundColor": "#f8f9fa", "border": "1px solid #dee2e6", "position": "relative"}, className="mb-3")

layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Line Bot 訂單"),
                dbc.CardBody([
                    html.H2("4", className="card-title text-primary"),  # 可用 len(orders)
                    html.P("等待處理的訂單", className="card-text")
                ])
            ], color="success", className="mb-4"),
            width=6,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Line Bot 客服問題"),
                dbc.CardBody([
                    html.H2("2", className="card-title text-primary"),
                    html.P("等待處理的客戶訊息", className="card-text")
                ])
            ], color="warning", className="mb-4"),
            width=6,
        )
    ]),
    html.H4("新進訂單", className="mt-4 mb-2 text-secondary"),
    dbc.Row([
        dbc.Col(make_card_item(order), width=4) for order in orders
    ], className="g-3")
], fluid=True)