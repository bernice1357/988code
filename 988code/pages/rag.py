from .common import *
from dash import callback_context
from dash.exceptions import PreventUpdate
from dash import ALL, no_update

# TODO 現在還不知道檔案要存到哪

# 從資料庫載入初始條目
def load_initial_items():
    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/get_rag_titles")
        if response.status_code == 200:
            data = response.json()
            titles = [item['title'] for item in data]
            return titles
        else:
            print(f"[ERROR] 載入RAG條目失敗: {response.status_code}")
            return []
    except Exception as e:
        print(f"[ERROR] 載入RAG條目失敗: {e}")
        return []

# 不在模組載入時執行，改為在 layout 中動態載入

# 儲存要被刪除的條目名稱
item_to_delete = None

# 儲存當前選中的條目
current_selected_item = None

# 生成檔案顯示內容的函數  
def generate_file_display_content(file_names):
    """在callback中動態生成檔案顯示內容"""
    print('file_names', file_names, type(file_names))
    if file_names and len(file_names) > 0:
        file_items = []
        for i, file_name in enumerate(file_names):
            file_icon = get_file_icon(file_name)
            file_color = get_file_color(file_name)
            
            file_item = dbc.ListGroupItem([
                html.Div([
                    html.Div([
                        html.I(className=file_icon, style={
                            "fontSize": "20px", 
                            "marginRight": "12px", 
                            "color": file_color
                        }),
                        html.Div([
                            html.H6(file_name, style={
                                "margin": "0", 
                                "color": "#212529", 
                                "fontSize": "14px",
                                "whiteSpace": "nowrap",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "maxWidth": "200px"
                            }),
                            html.Small("已存在資料庫", style={"color": "#6c757d", "fontSize": "12px"})
                        ], style={"flex": "1", "minWidth": "0"})
                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                    html.Div([
                        dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                 id={"type": "delete-existing-file-btn", "index": i})
                    ])
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
            ], style={
                "padding": "12px", 
                "marginBottom": "5px",
                "backgroundColor": "#e7f3ff",  # 淺藍色背景
                "borderColor": "#b3d9ff"
            })
            file_items.append(file_item)
        
        return [
            html.H6(f"資料庫檔案 ({len(file_names)})", 
                   style={"margin": "0 0 15px 0", "color": "#495057", "fontSize": "16px"}),
            dbc.ListGroup(file_items, flush=True)
        ]
    else:
        print("沒有檔案")
        return [html.P("尚未上傳任何檔案", style={
            "color": "#6c757d", 
            "textAlign": "center",
            "marginTop": "50px",
            "fontStyle": "italic"
        })]

layout = dbc.Container([
        # Toast 通知
        success_toast("rag", message=""),
        error_toast("rag", message=""),
    
    dcc.Loading(
        id="loading-full-page",
        type="dot",
        children=dbc.Row([
            dbc.Col([
                # 標題 + 新增按鈕
                dbc.Row(
                    justify="between",
                    className="mb-2",
                    children=[
                        dbc.Col(html.H5("知識庫條目"), width="auto", className="d-flex align-items-center"),
                        dbc.Col(dbc.Button("新增條目", id="open-modal", color="primary", size="sm"),
                                width="auto", className="d-flex justify-content-end align-items-center")
                    ]
                ),
                # 條目列表
                dbc.ListGroup(
                    id="client-list",
                    children=[],  # 初始為空，透過 callback 載入
                    style={
                        "backgroundColor": "transparent"
                    }
                )
            ], width=3),

            dbc.Col([
                html.Div(
                    id="content-area",
                    children=[],  # 初始為空
                    style={
                        "borderRadius": "6px",
                        "padding": "20px",
                        "height": "85vh",
                        "boxShadow": "rgba(0, 0, 0, 0.05) 0px 0px 0px 1px",
                        "overflow": "auto",
                        "display": "flex",
                        "flexDirection": "column"
                    }
                )
            ], width=9)
        ]),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "minHeight": "85vh"
        }
    ),

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
    ], id="modal", is_open=False, centered=True),
    
    # 刪除確認 Modal
    dbc.Modal([
        dbc.ModalHeader("確認刪除", style={"fontWeight": "bold", "fontSize": "24px", "color": "#dc3545"}),
        dbc.ModalBody([
            html.P("此操作無法復原，確定要刪除這個知識庫條目嗎？", style={"marginBottom": "0"})
        ]),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-delete-modal", color="secondary", className="me-2"),
            dbc.Button("確認刪除", id="confirm-delete-modal", color="danger")
        ])
    ], id="delete-modal", is_open=False, centered=True)
], fluid=True)

from .common import *

# 頁面載入時初始化右側內容區域
@app.callback(
    Output("content-area", "children", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call='initial_duplicate'
)
def initialize_content_area(pathname):
    # 當進入 RAG 頁面時，顯示預設訊息
    if pathname and 'rag' in pathname.lower():
        return html.Div([
            html.Div([
                html.H4("請選擇左側的知識庫條目", style={
                    "textAlign": "center",
                    "color": "#6c757d",
                    "marginTop": "50px"
                })
            ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], style={"height": "100%", "display": "flex", "flexDirection": "column"})
    return []

# 頁面載入時自動載入條目列表
@app.callback(
    Output("client-list", "children", allow_duplicate=True),
    Input("url", "pathname"),  # 當頁面路徑改變時觸發
    prevent_initial_call='initial_duplicate'  # 允許重複輸出的初始調用
)
def load_client_list(pathname):
    
    # 檢查是否為 RAG 頁面或初始載入
    if not pathname or pathname == "/" or (pathname and 'rag' in pathname.lower()):
        items = load_initial_items()
        
        result = [
            dbc.ListGroupItem(
                name, 
                id={"type": "client-item", "index": name}, 
                n_clicks=0,
                style={
                    "cursor": "pointer",
                    "backgroundColor": "white",
                    "border": "1px solid #e0e6ed",
                    "marginBottom": "8px",
                    "borderRadius": "12px",
                    "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset",
                    "fontSize": "1.2rem",
                    "color": "#000000",
                    "fontWeight": "500"
                }
            )
            for name in items
        ]
        return result
    return []

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
    Output('rag-error-toast', 'is_open', allow_duplicate=True),
    Output('rag-error-toast', 'children', allow_duplicate=True),
    Input("add-client", "n_clicks"),
    State("new-client-name", "value"),
    State("client-list", "children"),
    prevent_initial_call=True
)
def add_client(n_clicks, new_name, current_list):
    if not new_name:
        raise PreventUpdate
    
    try:
        # 準備API請求數據
        knowledge_data = {
            "title": new_name,
            "text_content": "",
            "files": None
        }
        
        # 呼叫API在資料庫新增記錄
        import requests
        response = requests.put("http://127.0.0.1:8000/put/rag/save_knowledge", json=knowledge_data)
        
        if response.status_code == 200:
            # 資料庫新增成功，更新UI
            new_item = dbc.ListGroupItem(
                new_name, 
                id={"type": "client-item", "index": new_name}, 
                n_clicks=0,
                style={
                    "cursor": "pointer",
                    "backgroundColor": "white",
                    "border": "1px solid #e0e6ed",
                    "marginBottom": "8px",
                    "borderRadius": "12px",
                    "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset",
                    "fontSize": "16px",
                    "color": "#000000",
                    "fontWeight": "500"
                }
            )
            current_list.append(new_item)
            return current_list, False, ""
        else:
            try:
                error_msg = response.json().get('detail', '新增失敗')
            except:
                error_msg = f"HTTP {response.status_code}"
            return current_list, True, f"新增失敗：{error_msg}"
            
    except Exception as e:
        print(f"[ERROR] 新增條目失敗: {e}")
        return current_list, True, f"新增條目失敗：{str(e)}"

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
    Output("database-files-list", "children"),
    Output("pending-files-list", "children"),
    Output('rag-error-toast', 'is_open'),
    Output('rag-error-toast', 'children'),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
    State("title-input", "value"),
    prevent_initial_call=True
)
def update_output(list_of_contents, list_of_names, list_of_dates, current_title):
    global uploaded_files_store
    
    # 如果沒有檔案上傳，不要更新顯示
    if list_of_contents is None:
        raise PreventUpdate
    
    error_message = ""
    show_error = False
    
    # 獲取現有資料庫檔案
    existing_db_files = []
    if current_title:
        try:
            import requests
            response = requests.get(f"http://127.0.0.1:8000/get_rag_content/{current_title}")
            if response.status_code == 200:
                content_data = response.json()
                existing_db_files = content_data.get('file_names', [])
        except Exception as e:
            print(f"[ERROR] 載入現有檔案失敗: {e}")
    
    if list_of_contents is not None:
        invalid_files = []
        for i, (contents, filename, date) in enumerate(zip(list_of_contents, list_of_names, list_of_dates)):
            if not is_allowed_file(filename):
                invalid_files.append(filename)
                continue
            
            # 檢查是否已存在相同檔名，如果存在就更新，否則新增
            existing_file_index = next((i for i, f in enumerate(uploaded_files_store) if f['filename'] == filename), -1)
            if existing_file_index >= 0:
                # 更新現有檔案
                uploaded_files_store[existing_file_index] = {
                    'filename': filename,
                    'date': date,
                    'contents': contents
                }
            else:
                # 新增檔案
                uploaded_files_store.append({
                    'filename': filename,
                    'date': date,
                    'contents': contents
                })
        
        if invalid_files:
            show_error = True
            if len(invalid_files) == 1:
                error_message = f"僅支援 .pdf、.doc、.docx、.xls、.xlsx 格式"
            else:
                error_message = f"以下檔案格式不符合要求：{', '.join(invalid_files)}，僅支援 .pdf、.doc、.docx、.xls、.xlsx 格式"
    
    # 生成檔案列表顯示 - 同時顯示資料庫檔案和新上傳檔案
    all_file_items = []
    
    # 1. 顯示資料庫中的檔案 (淺藍色背景)
    if existing_db_files:
        for i, file_name in enumerate(existing_db_files):
            file_icon = get_file_icon(file_name)
            file_color = get_file_color(file_name)
            
            file_item = dbc.ListGroupItem([
                html.Div([
                    html.Div([
                        html.I(className=file_icon, style={
                            "fontSize": "20px", 
                            "marginRight": "12px", 
                            "color": file_color
                        }),
                        html.Div([
                            html.H6(file_name, style={
                                "margin": "0", 
                                "color": "#212529", 
                                "fontSize": "14px",
                                "whiteSpace": "nowrap",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "maxWidth": "200px"
                            }),
                            html.Small("已存在資料庫", style={"color": "#6c757d", "fontSize": "12px"})
                        ], style={"flex": "1", "minWidth": "0"})
                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                    html.Div([
                        dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                 id={"type": "delete-existing-file-btn", "index": i})
                    ])
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
            ], style={
                "padding": "12px", 
                "marginBottom": "5px",
                "backgroundColor": "#e7f3ff",  # 淺藍色背景
                "borderColor": "#b3d9ff"
            })
            all_file_items.append(file_item)
    
    # 2. 顯示新上傳的檔案 (淺綠色背景)
    if uploaded_files_store:
        for i, file_info in enumerate(uploaded_files_store):
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
                            html.Small(f"新上傳 - {datetime.datetime.fromtimestamp(file_info['date']).strftime('%Y-%m-%d %H:%M:%S')}", 
                                     style={"color": "#6c757d", "fontSize": "12px"})
                        ], style={"flex": "1"})
                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                    html.Div([
                        dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                 id={"type": "delete-file-btn", "index": i})
                    ])
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
            ], style={
                "padding": "12px", 
                "marginBottom": "5px",
                "backgroundColor": "#e8f5e8",  # 淺綠色背景
                "borderColor": "#c3e6c3"
            })
            all_file_items.append(file_item)
    
    # 生成最終顯示內容
    if all_file_items:
        total_db_files = len(existing_db_files) if existing_db_files else 0
        total_new_files = len(uploaded_files_store)
        
        file_list_content = html.Div([
            html.Div([
                html.H6(f"檔案列表 (資料庫:{total_db_files} | 新上傳:{total_new_files})", 
                       style={"margin": "0 0 15px 0", "color": "#495057", "fontSize": "16px"})
            ]),
            dbc.ListGroup(all_file_items, flush=True)
        ])
    else:
        file_list_content = html.P("尚未上傳任何檔案", style={
            "color": "#6c757d", 
            "textAlign": "center",
            "marginTop": "50px",
            "fontStyle": "italic"
        })
    
    # Split content into database files and pending files
    database_files_content = []
    pending_files_content = []
    
    if existing_db_files:
        for i, file_name in enumerate(existing_db_files):
            file_icon = get_file_icon(file_name)
            file_color = get_file_color(file_name)
            
            file_item = dbc.ListGroupItem([
                html.Div([
                    html.Div([
                        html.I(className=file_icon, style={
                            "fontSize": "16px", 
                            "marginRight": "8px", 
                            "color": file_color
                        }),
                        html.Div([
                            html.H6(file_name, style={
                                "margin": "0", 
                                "color": "#212529", 
                                "fontSize": "12px",
                                "whiteSpace": "nowrap",
                                "overflow": "hidden",
                                "textOverflow": "ellipsis"
                            })
                        ], style={"flex": "1", "minWidth": "0"})
                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                    html.Div([
                        dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                 id={"type": "delete-existing-file-btn", "index": i})
                    ])
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
            ], style={"padding": "8px", "marginBottom": "3px"})
            database_files_content.append(file_item)
    
    if uploaded_files_store:
        for i, file_info in enumerate(uploaded_files_store):
            file_icon = get_file_icon(file_info['filename'])
            file_color = get_file_color(file_info['filename'])
            
            file_item = dbc.ListGroupItem([
                html.Div([
                    html.Div([
                        html.I(className=file_icon, style={
                            "fontSize": "16px", 
                            "marginRight": "8px", 
                            "color": file_color
                        }),
                        html.Div([
                            html.H6(file_info['filename'], style={
                                "margin": "0", 
                                "color": "#212529", 
                                "fontSize": "12px"
                            })
                        ], style={"flex": "1"})
                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                    html.Div([
                        dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                 id={"type": "delete-file-btn", "index": i})
                    ])
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
            ], style={"padding": "8px", "marginBottom": "3px"})
            pending_files_content.append(file_item)
    
    # Return content for both sections
    db_content = dbc.ListGroup(database_files_content, flush=True) if database_files_content else html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
    pending_content = dbc.ListGroup(pending_files_content, flush=True) if pending_files_content else html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
    
    return db_content, pending_content, show_error, error_message

# 處理刪除檔案功能
@app.callback(
    Output("pending-files-list", "children", allow_duplicate=True),
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
    Output("client-list", "children", allow_duplicate=True),
    Input({"type": "client-item", "index": ALL}, "n_clicks"),
    State({"type": "client-item", "index": ALL}, "id"),
    State("client-list", "children"),
    prevent_initial_call=True
)
def display_client_data(n_clicks_list, id_list, current_list):
    global current_selected_item
    
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
        current_selected_item = client_name
        
        # 從資料庫載入條目內容
        try:
            import requests
            response = requests.get(f"http://127.0.0.1:8000/get_rag_content/{client_name}")
            if response.status_code == 200:
                content_data = response.json()
                text_content = content_data.get('text_content', '')
                has_file = content_data.get('has_file', False)
                file_names = content_data.get('file_names', [])
            else:
                text_content = ''
                has_file = False
                file_names = []
        except Exception as e:
            print(f"[ERROR] 載入條目內容失敗: {e}")
            text_content = ''
            has_file = False
            file_names = []
        
        # 更新列表項目的樣式，設定選中狀態
        updated_list = []
        for item in current_list:
            item_name = item['props']['id']['index']
            if item_name == client_name:
                # 選中項目 - 使用淺藍色背景
                updated_item = {
                    **item,
                    'props': {
                        **item['props'],
                        'style': {
                            "cursor": "pointer",
                            "backgroundColor": "white",
                            "border": "1px solid #007bff",
                            "marginBottom": "8px",
                            "borderRadius": "12px",
                            "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset",
                            "fontSize": "1.2rem",
                            "color": "#000000",
                            "fontWeight": "500"
                        }
                    }
                }
            else:
                # 未選中項目 - 使用默認樣式
                updated_item = {
                    **item,
                    'props': {
                        **item['props'],
                        'style': {
                            "cursor": "pointer",
                            "backgroundColor": "white",
                            "border": "1px solid #e0e6ed",
                            "marginBottom": "8px",
                            "borderRadius": "12px",
                            "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset",
                            "fontSize": "1.2rem",
                            "color": "#000000",
                            "fontWeight": "500"
                        }
                    }
                }
            updated_list.append(updated_item)
        
        # Generate database files content
        db_files_content = []
        if file_names:
            for i, file_name in enumerate(file_names):
                file_icon = get_file_icon(file_name)
                file_color = get_file_color(file_name)
                
                file_item = dbc.ListGroupItem([
                    html.Div([
                        html.Div([
                            html.I(className=file_icon, style={
                                "fontSize": "16px", 
                                "marginRight": "8px", 
                                "color": file_color
                            }),
                            html.Div([
                                html.H6(file_name, style={
                                    "margin": "0", 
                                    "color": "#212529", 
                                    "fontSize": "12px",
                                    "whiteSpace": "nowrap",
                                    "overflow": "hidden",
                                    "textOverflow": "ellipsis"
                                })
                            ], style={"flex": "1", "minWidth": "0"})
                        ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                        html.Div([
                            dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                     id={"type": "delete-existing-file-btn", "index": i})
                        ])
                    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
                ], style={"padding": "8px", "marginBottom": "3px"})
                db_files_content.append(file_item)
        
        db_content = dbc.ListGroup(db_files_content, flush=True) if db_files_content else html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
        pending_content = html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
        
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
                            label="編輯文字內容",
                            tab_id="text-tab",
                            children=[
                                html.Div([
                                    dbc.Textarea(
                                        id="content-input",
                                        className="mt-3",
                                        placeholder=f"請在此輸入 {client_name} 的知識庫內容...",
                                        value=text_content,
                                        style={"height": "45vh", "resize": "none"}
                                    )
                                ])
                            ]
                        ),
                        dbc.Tab(
                            label="上傳檔案",
                            tab_id="file-tab",
                            children=[
                                html.Div([
                                    dbc.Row([
                                        # 左側：拖曳上傳區域
                                        dbc.Col([
                                            dcc.Upload(
                                                id="upload-data",
                                                children=html.Div([
                                                    html.I(className="fas fa-cloud-upload-alt", style={
                                                        "fontSize": "2.5rem",
                                                        "color": "#007bff",
                                                        "marginBottom": "1rem"
                                                    }),
                                                    html.P("拖拽檔案到此處或點擊上傳", style={
                                                        "fontSize": "1rem",
                                                        "color": "#666",
                                                        "margin": "0"
                                                    }),
                                                    html.P("支援格式：PDF、DOC、DOCX、XLS、XLSX", style={
                                                        "fontSize": "0.8rem",
                                                        "color": "#999",
                                                        "margin": "0.5rem 0 0 0"
                                                    })
                                                ], style={
                                                    "display": "flex",
                                                    "flexDirection": "column",
                                                    "alignItems": "center",
                                                    "justifyContent": "center",
                                                    "height": "100%"
                                                }),
                                                style={
                                                    "width": "100%",
                                                    "height": "45vh",
                                                    "borderWidth": "2px",
                                                    "borderStyle": "dashed",
                                                    "borderColor": "#007bff",
                                                    "borderRadius": "12px",
                                                    "textAlign": "center",
                                                    "backgroundColor": "#f8f9ff",
                                                    "cursor": "pointer",
                                                    "transition": "all 0.3s ease"
                                                },
                                                multiple=True
                                            )
                                        ], width=5),
                                        
                                        # 右側：檔案列表區域
                                        dbc.Col([
                                            # 上半部：資料庫檔案區塊
                                            html.Div([
                                                html.Div([
                                                    html.H6("已上傳檔案", style={
                                                        "margin": "0 0 10px 0", 
                                                        "color": "#495057", 
                                                        "fontSize": "14px",
                                                        "fontWeight": "600"
                                                    }),
                                                    html.Div(
                                                        id="database-files-list",
                                                        children=db_content,
                                                        style={
                                                            "height": "calc(100% - 30px)",
                                                            "overflowY": "auto"
                                                        }
                                                    )
                                                ], style={
                                                    "border": "1px solid #dee2e6",
                                                    "borderRadius": "6px",
                                                    "padding": "10px",
                                                    "backgroundColor": "white",
                                                    "height": "100%",
                                                    "display": "flex",
                                                    "flexDirection": "column"
                                                })
                                            ], style={
                                                "height": "calc(50% - 5px)",
                                                "marginBottom": "10px"
                                            }),
                                            
                                            # 下半部：待上傳檔案區塊
                                            html.Div([
                                                html.Div([
                                                    html.H6("待上傳檔案", style={
                                                        "margin": "0 0 10px 0", 
                                                        "color": "#495057", 
                                                        "fontSize": "14px",
                                                        "fontWeight": "600"
                                                    }),
                                                    html.Div(
                                                        id="pending-files-list",
                                                        children=pending_content,
                                                        style={
                                                            "height": "calc(100% - 30px)",
                                                            "overflowY": "auto"
                                                        }
                                                    )
                                                ], style={
                                                    "border": "1px solid #dee2e6",
                                                    "borderRadius": "6px",
                                                    "padding": "10px",
                                                    "backgroundColor": "white",
                                                    "height": "100%",
                                                    "display": "flex",
                                                    "flexDirection": "column"
                                                })
                                            ], style={
                                                "height": "calc(50% - 5px)"
                                            })
                                        ], width=7, style={
                                            "height": "45vh",
                                            "display": "flex",
                                            "flexDirection": "column"
                                        })
                                    ], className="g-2")
                                ], className="mt-3", style={"maxWidth": "98%", "margin": "0 auto"})
                            ]
                        )
                    ]
                )
            ], style={"flex": "1", "overflowY": "auto"}),
            # 儲存按鈕區域
            html.Div([
                dbc.Button("儲存修改內容", id="save-btn", color="success", size="sm"),
                dbc.Button(f"刪除此條目", id="delete-current-item-btn", color="danger", size="sm",
                          style={"marginLeft": "10px"})
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "paddingTop": "10px",
                "marginTop": "10px"
            })
        ], style={"height": "100%", "display": "flex", "flexDirection": "column"}), updated_list

    # 如果沒有點選任何項目，顯示提示訊息
    return html.Div([
        html.Div([
            html.H4("請選擇左側的知識庫條目", style={
                "textAlign": "center",
                "color": "#6c757d",
                "marginTop": "50px"
            })
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center"})
    ], style={"height": "100%", "display": "flex", "flexDirection": "column"}), no_update

# 處理刪除此條目按鈕點擊 - 顯示確認Modal
@app.callback(
    Output("delete-modal", "is_open", allow_duplicate=True),
    Input("delete-current-item-btn", "n_clicks"),
    State("delete-modal", "is_open"),
    State("content-area", "children"),
    prevent_initial_call=True
)
def show_delete_confirmation_modal(n_clicks, is_open, current_content):
    global item_to_delete
    
    if not n_clicks:
        raise PreventUpdate
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    # 從目前的內容區域中找到正在編輯的條目名稱
    current_item_name = None
    try:
        # 尋找title-input的值
        if current_content and 'props' in current_content:
            children = current_content['props'].get('children', [])
            for child in children:
                if isinstance(child, dict) and 'props' in child:
                    grandchildren = child['props'].get('children', [])
                    for grandchild in grandchildren:
                        if isinstance(grandchild, dict) and 'props' in grandchild:
                            if grandchild['props'].get('id') == 'title-input':
                                current_item_name = grandchild['props'].get('value', '')
                                break
    except:
        pass
    
    if not current_item_name:
        raise PreventUpdate
    
    # 儲存要刪除的條目名稱
    item_to_delete = current_item_name
    
    # 顯示確認Modal
    return True

# 處理刪除確認Modal的按鈕點擊
@app.callback(
    Output("delete-modal", "is_open", allow_duplicate=True),
    Output("client-list", "children", allow_duplicate=True),
    Output("content-area", "children", allow_duplicate=True),
    Input("confirm-delete-modal", "n_clicks"),
    Input("cancel-delete-modal", "n_clicks"),
    State("delete-modal", "is_open"),
    State("client-list", "children"),
    prevent_initial_call=True
)
def handle_delete_modal_buttons(confirm_clicks, cancel_clicks, is_open, current_list):
    global item_to_delete
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_button = ctx.triggered[0]['prop_id']
    
    # 如果點擊取消按鈕，關閉Modal
    if 'cancel-delete-modal' in triggered_button:
        item_to_delete = None
        return False, current_list, no_update
    
    # 如果點擊確認刪除按鈕
    if 'confirm-delete-modal' in triggered_button and item_to_delete:
        try:
            # 呼叫API從資料庫刪除記錄
            import requests
            response = requests.put(f"http://127.0.0.1:8000/put/rag/delete_knowledge/{item_to_delete}")
            
            if response.status_code == 200:
                # 資料庫刪除成功，從UI列表中移除選中的條目
                updated_list = []
                for item in current_list:
                    if item['props']['id']['index'] != item_to_delete:
                        updated_list.append(item)
                
                # 重置刪除狀態
                item_to_delete = None
                
                # 返回更新後的列表和默認內容區域
                default_content = html.Div([
                    html.Div([
                        html.H4("請選擇左側的知識庫條目", style={
                            "textAlign": "center",
                            "color": "#6c757d",
                            "marginTop": "50px"
                        })
                    ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center"})
                ], style={"height": "100%", "display": "flex", "flexDirection": "column"})
                
                # 關閉Modal，更新列表，返回默認內容區域
                return False, updated_list, default_content
            else:
                # 刪除失敗，保持現狀但關閉Modal
                item_to_delete = None
                return False, current_list, no_update
                
        except Exception as e:
            print(f"[ERROR] 刪除條目失敗: {e}")
            # 發生錯誤，保持現狀但關閉Modal
            item_to_delete = None
            return False, current_list, no_update
    
    raise PreventUpdate


# 處理儲存按鈕點擊
@app.callback(
    Output('rag-success-toast', 'is_open', allow_duplicate=True),
    Output('rag-success-toast', 'children', allow_duplicate=True),
    Output('rag-error-toast', 'is_open', allow_duplicate=True),
    Output('rag-error-toast', 'children', allow_duplicate=True),
    Output("database-files-list", "children", allow_duplicate=True),
    Output("pending-files-list", "children", allow_duplicate=True),
    Output("client-list", "children", allow_duplicate=True),
    Input("save-btn", "n_clicks"),
    State("title-input", "value"),
    State("content-input", "value"),
    State("client-list", "children"),
    prevent_initial_call=True
)
def handle_save_button(n_clicks, title, text_content, current_list):
    global uploaded_files_store, current_selected_item
    
    if not n_clicks:
        raise PreventUpdate
    
    if not title:
        return False, "", True, "請輸入標題", no_update, no_update, no_update
    
    try:
        # 檢查標題是否有變更，如果有變更先更新標題
        title_updated = False
        old_title = current_selected_item  # 記住原標題
        if current_selected_item and title != current_selected_item:
            import requests
            update_data = {
                "old_title": current_selected_item,
                "new_title": title
            }
            response = requests.put("http://127.0.0.1:8000/put/rag/update_title", json=update_data)
            
            if response.status_code == 200:
                title_updated = True
                current_selected_item = title
            else:
                error_msg = response.json().get('detail', '標題更新失敗')
                return False, "", True, f"標題更新失敗：{error_msg}", no_update, no_update, no_update
        
        # 準備檔案數據
        files_data = []
        if uploaded_files_store:
            for file_info in uploaded_files_store:
                files_data.append({
                    'filename': file_info['filename'],
                    'content': file_info['contents'].split(',')[1] if ',' in file_info['contents'] else file_info['contents']
                })
        
        # 準備API請求數據
        knowledge_data = {
            "title": title,
            "text_content": text_content or "",
            "files": files_data if files_data else None
        }
        
        # 呼叫API儲存內容
        import requests
        response = requests.put("http://127.0.0.1:8000/put/rag/save_knowledge", json=knowledge_data)
        
        if response.status_code == 200:
            # 清空上傳檔案暫存（因為已經儲存到資料庫）
            uploaded_files_store.clear()
            
            # 重新從資料庫載入檔案列表
            try:
                content_response = requests.get(f"http://127.0.0.1:8000/get_rag_content/{title}")
                if content_response.status_code == 200:
                    content_data = content_response.json()
                    updated_file_names = content_data.get('file_names', [])
                else:
                    updated_file_names = []
            except:
                updated_file_names = []
            
            # Generate content for database files and clear pending files
            db_files_content = []
            if updated_file_names:
                for i, file_name in enumerate(updated_file_names):
                    file_icon = get_file_icon(file_name)
                    file_color = get_file_color(file_name)
                    
                    file_item = dbc.ListGroupItem([
                        html.Div([
                            html.Div([
                                html.I(className=file_icon, style={
                                    "fontSize": "16px", 
                                    "marginRight": "8px", 
                                    "color": file_color
                                }),
                                html.Div([
                                    html.H6(file_name, style={
                                        "margin": "0", 
                                        "color": "#212529", 
                                        "fontSize": "12px",
                                        "whiteSpace": "nowrap",
                                        "overflow": "hidden",
                                        "textOverflow": "ellipsis"
                                    })
                                ], style={"flex": "1", "minWidth": "0"})
                            ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                            html.Div([
                                dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                         id={"type": "delete-existing-file-btn", "index": i})
                            ])
                        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
                    ], style={"padding": "8px", "marginBottom": "3px"})
                    db_files_content.append(file_item)
            
            db_content = dbc.ListGroup(db_files_content, flush=True) if db_files_content else html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
            pending_content = html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
            
            # 更新左側列表如果標題有變更
            updated_list = current_list
            if title_updated and old_title:
                updated_list = []
                for item in current_list:
                    if 'props' in item and 'id' in item['props']:
                        item_index = item['props']['id'].get('index')
                        if item_index == old_title:
                            # 更新選中項目的標題
                            updated_item = {
                                **item,
                                'props': {
                                    **item['props'],
                                    'children': title,
                                    'id': {"type": "client-item", "index": title},
                                    'style': {
                                        "cursor": "pointer",
                                        "backgroundColor": "white",
                                        "border": "1px solid #007bff",
                                        "marginBottom": "8px",
                                        "borderRadius": "12px",
                                        "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset",
                                        "fontSize": "1.2rem",
                                        "color": "#000000",
                                        "fontWeight": "500"
                                    }
                                }
                            }
                            updated_list.append(updated_item)
                        else:
                            updated_list.append(item)
                    else:
                        updated_list.append(item)
            
            success_msg = "知識庫內容儲存成功！"
            if title_updated:
                success_msg = "標題和內容儲存成功！"
            
            return True, success_msg, False, "", db_content, pending_content, updated_list
        else:
            error_msg = response.json().get('detail', '儲存失敗')
            return False, "", True, f"儲存失敗：{error_msg}", no_update, no_update, no_update
            
    except Exception as e:
        print(f"[ERROR] 儲存失敗: {e}")
        return False, "", True, f"儲存失敗：{str(e)}", no_update, no_update, no_update

# 處理刪除已存在檔案
@app.callback(
    Output('rag-success-toast', 'is_open', allow_duplicate=True),
    Output('rag-success-toast', 'children', allow_duplicate=True),
    Output("database-files-list", "children", allow_duplicate=True),
    Input({"type": "delete-existing-file-btn", "index": ALL}, "n_clicks"),
    State("title-input", "value"),
    State("content-input", "value"),
    prevent_initial_call=True
)
def delete_existing_file(n_clicks_list, title, text_content):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list) or not title:
        raise PreventUpdate
    
    # 找出被點擊的按鈕索引
    triggered_button = ctx.triggered[0]
    if not triggered_button["value"]:
        raise PreventUpdate
        
    # 解析出要刪除的檔案索引
    import json
    button_id = json.loads(triggered_button["prop_id"].split('.')[0])
    file_index = button_id["index"]
    
    try:
        # 呼叫API清除檔案內容
        import requests
        
        # 準備刪除指定檔案的數據
        knowledge_data = {
            "title": title,
            "text_content": text_content or "",
            "files": None,
            "delete_file_index": file_index
        }
        
        # 更新資料庫，清除file_content和file_name
        response = requests.put("http://127.0.0.1:8000/put/rag/save_knowledge", json=knowledge_data)
        
        if response.status_code == 200:
            # 重新載入檔案列表
            try:
                content_response = requests.get(f"http://127.0.0.1:8000/get_rag_content/{title}")
                if content_response.status_code == 200:
                    content_data = content_response.json()
                    updated_file_names = content_data.get('file_names', [])
                    # Generate updated database files content
                    db_files_content = []
                    if updated_file_names:
                        for i, file_name in enumerate(updated_file_names):
                            file_icon = get_file_icon(file_name)
                            file_color = get_file_color(file_name)
                            
                            file_item = dbc.ListGroupItem([
                                html.Div([
                                    html.Div([
                                        html.I(className=file_icon, style={
                                            "fontSize": "16px", 
                                            "marginRight": "8px", 
                                            "color": file_color
                                        }),
                                        html.Div([
                                            html.H6(file_name, style={
                                                "margin": "0", 
                                                "color": "#212529", 
                                                "fontSize": "12px",
                                                "whiteSpace": "nowrap",
                                                "overflow": "hidden",
                                                "textOverflow": "ellipsis"
                                            })
                                        ], style={"flex": "1", "minWidth": "0"})
                                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                                    html.Div([
                                        dbc.Button("刪除", color="danger", size="sm", outline=True, 
                                                 id={"type": "delete-existing-file-btn", "index": i})
                                    ])
                                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
                            ], style={"padding": "8px", "marginBottom": "3px"})
                            db_files_content.append(file_item)
                    
                    db_content = dbc.ListGroup(db_files_content, flush=True) if db_files_content else html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
                    return True, "檔案刪除成功！", db_content
                else:
                    db_content = html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
                return True, "檔案刪除成功！", db_content
            except:
                db_content = html.P("無檔案", style={"color": "#6c757d", "textAlign": "center", "margin": "20px 0"})
                return True, "檔案刪除成功！", db_content
        else:
            # 刪除失敗，保持現狀
            raise PreventUpdate
            
    except Exception as e:
        print(f"[ERROR] 刪除檔案失敗: {e}")
        raise PreventUpdate