from dash import html, dcc, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
import dash_mdxeditor as dme

initial_items = ["商品價目表", "六月特價商品"]

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            # 標題 + 新增按鈕
            dbc.Row(
                justify="between",
                className="mb-2",
                children=[
                    dbc.Col(html.H5("知識庫條目"), width="auto", className="d-flex align-items-center"),
                    dbc.Col(dbc.Button("➕ 新增", id="open-modal", color="primary", size="sm"),
                            width="auto", className="d-flex justify-content-end align-items-center")
                ]
            ),
            # 條目列表
            dbc.ListGroup(
                id="client-list",
                children=[
                    dbc.ListGroupItem(name, id={"type": "client-item", "index": name}, n_clicks=0)
                    for name in initial_items
                ],
                style={
                    "cursor": "pointer",
                    "backgroundColor": "#ced4da",
                    "borderRadius": "6px",
                    "boxShadow": "2px 2px 6px rgba(0,0,0,0.2)"
                }
            )
        ], width=3),

        dbc.Col([
            html.Div([
                html.Div(
                    id="content-area",
                    children=[
                        html.Div([
                            html.H4("請選擇左側的知識庫條目", style={
                                "textAlign": "center",
                                "color": "#6c757d",
                                "marginTop": "50px"
                            })
                        ])
                    ],
                    style={
                        "border": "2px solid #6c757d",
                        "borderRadius": "6px",
                        "padding": "20px",
                        "height": "75vh",
                        "backgroundColor": "#adb5bd",
                        "boxShadow": "0 0 10px rgba(0, 0, 0, 0.1)",
                        "overflow": "auto",
                        "marginBottom": "10px"
                    }
                ),
                html.Div([
                    dbc.Button("儲存", id="save-btn", color="success", className="me-2"),
                    dbc.Button("取消", id="cancel-btn", color="secondary")
                ], style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "padding": "10px"
                })
            ])
        ], width=9)
    ]),

    # Modal 彈窗
    dbc.Modal([
        dbc.ModalHeader("新增客戶", style={"fontWeight": "bold", "fontSize": "24px"}),
        dbc.ModalBody([
            dbc.Input(id="new-client-name", placeholder="輸入客戶名稱", type="text")
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="close-modal", color="secondary", className="me-2"),
            dbc.Button("新增", id="add-client", color="primary")
        ])
    ], id="modal", is_open=False, centered=True)
], fluid=True)

from .common import *

@app.callback(
    Output("modal", "is_open"),
    Output("new-client-name", "value"),  # 新增這個輸出來清空輸入框
    Input("open-modal", "n_clicks"),
    Input("close-modal", "n_clicks"),
    Input("add-client", "n_clicks"),
    State("modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(open_click, close_click, add_click, is_open):
    triggered = callback_context.triggered_id
    if triggered in ["open-modal", "close-modal", "add-client"]:
        # 當關閉 modal 時清空輸入框
        return not is_open, ""
    return is_open, ""

# 新增客戶到 ListGroup
@app.callback(
    Output("client-list", "children"),
    Input("add-client", "n_clicks"),
    State("new-client-name", "value"),
    State("client-list", "children"),
    prevent_initial_call=True
)
def add_client(n_clicks, new_name, current_list):
    if not new_name:
        raise PreventUpdate
    # 正確設定新項目的 id 格式，讓它能被點擊回調函數識別
    new_item = dbc.ListGroupItem(
        new_name, 
        id={"type": "client-item", "index": new_name}, 
        n_clicks=0
    )
    current_list.append(new_item)
    return current_list

# 新增這個回調函數來控制內容編輯區域的展開/收合
@app.callback(
    Output("content-collapse", "is_open"),
    Input("toggle-content-collapse", "n_clicks"),
    State("content-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_content_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output("content-area", "children"),
    Input({"type": "client-item", "index": ALL}, "n_clicks"),
    State({"type": "client-item", "index": ALL}, "id"),
    prevent_initial_call=True
)
def display_client_data(n_clicks_list, id_list):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # 取得觸發的具體項目
    triggered_prop_id = ctx.triggered[0]["prop_id"]
    
    # 解析出被點擊的項目索引
    if triggered_prop_id != ".":
        # 從 triggered 中解析出實際被點擊的項目
        import json
        triggered_id = json.loads(triggered_prop_id.split('.')[0])
        client_name = triggered_id['index']
        
        # 返回編輯界面
        return html.Div([
            html.H4("標題", id="content-title", style={
                "borderBottom": "1px solid #6c757d",
                "paddingBottom": "10px",
                "marginBottom": "10px",
                "color": "#212529"
            }),
            dbc.Input(
                id="title-input",
                placeholder="請輸入標題...",
                type="text",
                value=client_name,  # 預設顯示客戶名稱作為標題
                style={"marginBottom": "20px"}
            ),
            html.H4("知識庫內容", id="content-title", style={
                "borderBottom": "1px solid #6c757d",
                "paddingBottom": "10px",
                "marginBottom": "10px",
                "color": "#212529"
            }),
            dbc.Button("✏️ 編輯內容", id="toggle-content-collapse", color="primary", size="sm", className="mb-2"),
            dbc.Collapse(
                children=[
                    dbc.Textarea(
                        id="content-input",
                        className="mb-3",
                        placeholder=f"請在此輸入 {client_name} 的知識庫內容...",
                        style={"height": "50vh"}
                    )
                ],
                id="content-collapse",
                is_open=False  # 預設收合
            ),
            dbc.Row([
                dbc.Col([
                    dbc.Button("儲存", color="success", className="me-2"),
                    dbc.Button("取消", color="secondary")
                ])
            ])
        ])

    # 如果沒有點選任何項目，顯示提示訊息
    return html.Div([
        html.H4("請選擇左側的知識庫條目", style={
            "textAlign": "center",
            "color": "#6c757d",
            "marginTop": "50px"
        })
    ])