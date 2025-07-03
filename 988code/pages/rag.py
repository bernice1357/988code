from dash import html, dcc, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
# import dash_quill  # 加上這行
from callbacks import rag_callback
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