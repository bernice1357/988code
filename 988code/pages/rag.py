from .common import *
from dash import callback_context
from dash.exceptions import PreventUpdate
from dash import ALL

initial_items = ["商品價目表", "六月特價商品"]

layout = dbc.Container([
    # 錯誤提示 Toast
    error_toast("rag", message=""),
    
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
            html.Div(
                id="content-area",
                children=[
                    html.Div([
                        html.Div([
                            html.H4("請選擇左側的知識庫條目", style={
                                "textAlign": "center",
                                "color": "#6c757d",
                                "marginTop": "50px"
                            })
                        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center"})
                    ], style={"height": "100%", "display": "flex", "flexDirection": "column"})
                ],
                style={
                    "border": "2px solid #6c757d",
                    "borderRadius": "6px",
                    "padding": "20px",
                    "height": "85vh",
                    "backgroundColor": "#e4e4e4",
                    "boxShadow": "0 0 10px rgba(0, 0, 0, 0.1)",
                    "overflow": "auto",
                    "display": "flex",
                    "flexDirection": "column"
                }
            )
        ], width=9)
    ]),

    # Modal 彈窗
    dbc.Modal([
        dbc.ModalHeader("新增條目", style={"fontWeight": "bold", "fontSize": "24px"}),
        dbc.ModalBody([
            dbc.Input(id="new-client-name", placeholder="輸入條目標題", type="text")
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
    Output("new-client-name", "value"),
    Input("open-modal", "n_clicks"),
    Input("close-modal", "n_clicks"),
    Input("add-client", "n_clicks"),
    State("modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(open_click, close_click, add_click, is_open):
    triggered = callback_context.triggered_id
    if triggered in ["open-modal", "close-modal", "add-client"]:
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
    new_item = dbc.ListGroupItem(
        new_name, 
        id={"type": "client-item", "index": new_name}, 
        n_clicks=0
    )
    current_list.append(new_item)
    return current_list

# 儲存已上傳檔案的變數（模擬全局狀態）
uploaded_files_store = []

# 檔案類型檢查和圖示判斷函數
def get_file_icon(filename):
    """根據檔案副檔名返回對應的 Font Awesome 圖示類別"""
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if extension == 'pdf':
        return "fas fa-file-alt"
    elif extension in ['doc', 'docx']:
        return "fas fa-file-alt"
    elif extension in ['xls', 'xlsx']:
        return "fas fa-file-alt"
    else:
        return "fas fa-file"

def get_file_color(filename):
    """根據檔案類型返回對應的顏色"""
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if extension == 'pdf':
        return "#dc3545"
    elif extension in ['doc', 'docx']:
        return "#2b5ce6"
    elif extension in ['xls', 'xlsx']:
        return "#107c41"
    else:
        return "#495057"

def is_allowed_file(filename):
    """檢查檔案格式是否被允許"""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.lower().split('.')[-1]
    allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx']
    return extension in allowed_extensions

# 處理檔案上傳
@app.callback(
    Output("output-data-upload", "children"),
    Output('rag-error-toast', 'is_open'),
    Output('rag-error-toast', 'children'),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
    prevent_initial_call=True
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    global uploaded_files_store
    
    error_message = ""
    show_error = False
    
    if list_of_contents is not None:
        invalid_files = []
        for i, (contents, filename, date) in enumerate(zip(list_of_contents, list_of_names, list_of_dates)):
            if not is_allowed_file(filename):
                invalid_files.append(filename)
                continue
            
            if not any(f['filename'] == filename for f in uploaded_files_store):
                uploaded_files_store.append({
                    'filename': filename,
                    'date': date,
                    'contents': contents
                })
        
        if invalid_files:
            show_error = True
            if len(invalid_files) == 1:
                error_message = f"檔案 '{invalid_files[0]}' 格式不符合要求，僅支援 .pdf、.doc、.docx、.xls、.xlsx 格式"
            else:
                error_message = f"以下檔案格式不符合要求：{', '.join(invalid_files)}，僅支援 .pdf、.doc、.docx、.xls、.xlsx 格式"
    
    # 生成檔案列表顯示
    if uploaded_files_store:
        file_items = []
        for file_info in uploaded_files_store:
            file_icon = get_file_icon(file_info['filename'])
            file_color = get_file_color(file_info['filename'])
            
            file_item = dbc.ListGroupItem([
                html.Div([
                    html.Div([
                        html.I(className=file_icon, style={
                            "fontSize": "20px", 
                            "marginRight": "12px", 
                            "color": file_color
                        }),
                        html.Div([
                            html.H6(file_info['filename'], style={"margin": "0", "color": "#212529", "fontSize": "14px"}),
                            html.Small(f"上傳時間: {datetime.datetime.fromtimestamp(file_info['date']).strftime('%Y-%m-%d %H:%M:%S')}", 
                                     style={"color": "#6c757d"})
                        ], style={"flex": "1"})
                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                    html.Div([
                        dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                 id={"type": "delete-file-btn", "index": len(file_items)})
                    ])
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
            ], style={"padding": "12px", "marginBottom": "5px"})
            file_items.append(file_item)
        
        file_list_content = html.Div([
            html.Div([
                html.H6(f"已上傳檔案 ({len(uploaded_files_store)})", 
                       style={"margin": "0 0 15px 0", "color": "#495057", "fontSize": "16px"})
            ]),
            dbc.ListGroup(file_items, flush=True)
        ])
    else:
        file_list_content = html.P("尚未上傳任何檔案", style={
            "color": "#6c757d", 
            "textAlign": "center",
            "marginTop": "50px",
            "fontStyle": "italic"
        })
    
    return file_list_content, show_error, error_message

# 處理刪除檔案功能
@app.callback(
    Output("output-data-upload", "children", allow_duplicate=True),
    Input({"type": "delete-file-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def delete_file(n_clicks_list):
    global uploaded_files_store
    
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate
    
    # 找出被點擊的刪除按鈕
    triggered_button = ctx.triggered[0]
    if triggered_button["value"]:
        # 找出被點擊按鈕的索引
        for i, n_clicks in enumerate(n_clicks_list):
            if n_clicks and n_clicks > 0:
                # 刪除對應索引的檔案
                if 0 <= i < len(uploaded_files_store):
                    uploaded_files_store.pop(i)
                break
        
        # 重新生成檔案列表
        if uploaded_files_store:
            file_items = []
            for file_info in uploaded_files_store:
                file_icon = get_file_icon(file_info['filename'])
                file_color = get_file_color(file_info['filename'])
                
                file_item = dbc.ListGroupItem([
                    html.Div([
                        html.Div([
                            html.I(className=file_icon, style={
                                "fontSize": "20px", 
                                "marginRight": "12px", 
                                "color": file_color
                            }),
                            html.Div([
                                html.H6(file_info['filename'], style={"margin": "0", "color": "#212529", "fontSize": "14px"}),
                                html.Small(f"上傳時間: {datetime.datetime.fromtimestamp(file_info['date']).strftime('%Y-%m-%d %H:%M:%S')}", 
                                         style={"color": "#6c757d"})
                            ], style={"flex": "1"})
                        ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                        html.Div([
                            dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                     id={"type": "delete-file-btn", "index": len(file_items)})
                        ])
                    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
                ], style={"padding": "12px", "marginBottom": "5px"})
                file_items.append(file_item)
            
            return html.Div([
                html.Div([
                    html.H6(f"已上傳檔案 ({len(uploaded_files_store)})", 
                           style={"margin": "0 0 15px 0", "color": "#495057", "fontSize": "16px"})
                ]),
                dbc.ListGroup(file_items, flush=True)
            ])
        else:
            return html.P("尚未上傳任何檔案", style={
                "color": "#6c757d", 
                "textAlign": "center",
                "marginTop": "50px",
                "fontStyle": "italic"
            })
    
    raise PreventUpdate

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
        import json
        triggered_id = json.loads(triggered_prop_id.split('.')[0])
        client_name = triggered_id['index']
        
        # 返回編輯界面
        return html.Div([
            html.Div([
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
                    value=client_name,
                    style={"marginBottom": "20px"}
                ),
                html.H4("知識庫內容", style={
                    "borderBottom": "1px solid #6c757d",
                    "paddingBottom": "10px",
                    "marginBottom": "10px",
                    "color": "#212529"
                }),
                # TABS 區域
                dbc.Tabs(
                    id="content-tabs",
                    active_tab="text-tab",
                    children=[
                        dbc.Tab(
                            label="📝 編輯文字內容",
                            tab_id="text-tab",
                            children=[
                                html.Div([
                                    dbc.Textarea(
                                        id="content-input",
                                        className="mt-3",
                                        placeholder=f"請在此輸入 {client_name} 的知識庫內容...",
                                        style={"height": "45vh", "resize": "none"}
                                    )
                                ])
                            ]
                        ),
                        dbc.Tab(
                            label="📁 上傳檔案",
                            tab_id="file-tab",
                            children=[
                                html.Div([
                                    # 上傳按鈕區域
                                    html.Div([
                                        dcc.Upload(
                                            id="upload-data",
                                            children=dbc.Button("📂 瀏覽檔案", color="primary", size="sm"),
                                            multiple=True
                                        ),
                                        html.Small("支援格式：.pdf、.doc、.docx、.xls、.xlsx", 
                                                 style={"color": "#6c757d", "marginLeft": "15px"})
                                    ], style={
                                        "display": "flex", 
                                        "alignItems": "center", 
                                        "marginBottom": "15px",
                                        "paddingTop": "15px"
                                    }),
                                    # 檔案列表區域
                                    html.Div(
                                        id="output-data-upload",
                                        children=[
                                            html.P("尚未上傳任何檔案", style={
                                                "color": "#6c757d", 
                                                "textAlign": "center",
                                                "marginTop": "50px",
                                                "fontStyle": "italic"
                                            })
                                        ],
                                        style={
                                            "height": "42vh",
                                            "overflowY": "auto",
                                            "border": "1px solid #dee2e6",
                                            "borderRadius": "6px",
                                            "padding": "15px",
                                            "backgroundColor": "#ffffff"
                                        }
                                    )
                                ], className="mt-3")
                            ]
                        )
                    ]
                )
            ], style={"flex": "1", "overflowY": "auto"}),
            # 儲存按鈕區域
            html.Div([
                dbc.Button("儲存", id="save-btn", color="success", size="sm")
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "paddingTop": "10px",
                "marginTop": "10px"
            })
        ], style={"height": "100%", "display": "flex", "flexDirection": "column"})

    # 如果沒有點選任何項目，顯示提示訊息
    return html.Div([
        html.Div([
            html.H4("請選擇左側的知識庫條目", style={
                "textAlign": "center",
                "color": "#6c757d",
                "marginTop": "50px"
            })
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center"})
    ], style={"height": "100%", "display": "flex", "flexDirection": "column"})