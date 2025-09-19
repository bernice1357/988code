import dash_bootstrap_components as dbc
from dash import dcc, html
from components.toast import success_toast, error_toast, warning_toast

layout = html.Div([
    # Toast 通知
    success_toast("import_data", message=""),
    error_toast("import_data", message=""),
    warning_toast("import_data", message=""),
    
    
    # 新增產品創建相關的 Toast
    success_toast("create_product_import", message=""),
    error_toast("create_product_import", message=""),
    warning_toast("create_product_import", message=""),

    # 進度更新觸發器（隱藏）
    dcc.Interval(
        id='progress-interval',
        interval=500,  # 每500毫秒更新一次
        n_intervals=0,
        disabled=True
    ),
    
    # 存儲匯入會話狀態
    dcc.Store(id='import-session-store', data={'session_id': 0, 'total_records': 0, 'status': 'waiting', 'deleted_count': 0, 'inserted_count': 0}),
    dcc.Store(id='user-role-store'),
    
    dcc.Store(id='current-file-store', data={}),

    # 新增：存儲缺失產品資料
    dcc.Store(id='missing-products-store', data=[]),

    
    # 新增產品創建 Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("創建新產品", id="new-product-modal-title")
        ]),
        dbc.ModalBody([
            dbc.Row([
                # 左側欄位
                dbc.Col([
                    # 產品ID
                    dbc.Row([
                        dbc.Label("產品ID", width=4),
                        dbc.Col(dbc.Input(id="new-product-id", type="text", disabled=True), width=8)
                    ], className="mb-3"),
                    # 倉庫ID
                    dbc.Row([
                        dbc.Label("倉庫ID", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-warehouse-id", type="text", placeholder="請輸入倉庫id"),
                            dbc.Tooltip("例如：本倉、物料倉", target="new-product-warehouse-id", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 產品中文名稱
                    dbc.Row([
                        dbc.Label("產品名稱", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-name-zh", type="text", placeholder="請輸入產品名稱"),
                            dbc.Tooltip("請輸入完整的產品名稱", target="new-product-name-zh", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 類別
                    dbc.Row([
                        dbc.Label("類別", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-category", type="text", placeholder="請輸入類別"),
                            dbc.Tooltip("例如：消耗品、其他類、白帶魚", target="new-product-category", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 子類別
                    dbc.Row([
                        dbc.Label("子類別", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-subcategory", type="text", placeholder="請輸入子類別"),
                            dbc.Tooltip("例如：白帶魚切塊、白帶魚片、禮盒", target="new-product-subcategory", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 規格
                    dbc.Row([
                        dbc.Label("規格", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-specification", type="text", placeholder="請輸入產品規格"),
                            dbc.Tooltip("例如：12K、150/200", target="new-product-specification", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                ], width=6),
                
                # 右側欄位
                dbc.Col([
                    # 包裝原料
                    dbc.Row([
                        dbc.Label("包裝原料", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-package-raw", type="text", placeholder="請輸入包裝原料"),
                            dbc.Tooltip("例如：10K/箱、500g/包", target="new-product-package-raw", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 處理方式
                    dbc.Row([
                        dbc.Label("處理方式", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-process-type", type="text", placeholder="請輸入處理方式"),
                            dbc.Tooltip("例如：單尾、無骨", target="new-product-process-type", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 單位
                    dbc.Row([
                        dbc.Label("單位", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-unit", type="text", placeholder="請輸入單位"),
                            dbc.Tooltip("例如：公斤、套、包、尾", target="new-product-unit", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 供應商ID
                    dbc.Row([
                        dbc.Label("供應商ID", width=4),
                        dbc.Col([
                            dbc.Input(id="new-product-supplier-id", type="text", placeholder="請輸入供應商id"),
                            dbc.Tooltip("例如：集和、寶田", target="new-product-supplier-id", placement="top")
                        ], width=8)
                    ], className="mb-3"),
                    # 狀態
                    dbc.Row([
                        dbc.Label("狀態", width=4),
                        dbc.Col([
                            html.Div([
                                dcc.Dropdown(
                                    id="new-product-is-active",
                                    options=[
                                        {"label": "啟用 (Active)", "value": "active"},
                                        {"label": "停用 (Inactive)", "value": "inactive"}
                                    ],
                                    placeholder="請選擇狀態"
                                )
                            ], title="選擇產品是否啟用：啟用表示可正常使用，停用表示暫時不可使用")
                        ], width=8)
                    ], className="mb-3"),
                ], width=6)
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("跳過此產品", id="skip-product-btn", color="secondary", className="me-2"),
            dbc.Button("儲存產品", id="save-new-product-btn", color="primary"),
            dbc.Button("批量跳過全部", id="skip-all-products-btn", color="warning", className="me-2", style={"display": "none"}),
            dbc.Button("完成並匯入", id="finish-product-import-btn", color="success", style={"display": "none"})
        ])
    ], id="new-product-modal", is_open=False, backdrop="static", keyboard=False, size="xl"),


    # 全螢幕載入遮罩
    html.Div([
        html.Div([
            html.Div([
                dcc.Loading(
                    id="fullscreen-loading",
                    type="circle",
                    color="#007bff",
                    children=html.Div(),
                    style={
                        "transform": "scale(2)",
                        "marginBottom": "2rem"
                    }
                ),
                html.H3("正在匯入資料...", style={
                    "color": "white",
                    "textAlign": "center",
                    "marginBottom": "1rem",
                    "fontWeight": "600"
                }),
                html.P("請稍候，系統正在處理您的檔案", style={
                    "color": "#ccc",
                    "textAlign": "center",
                    "fontSize": "1.1rem",
                    "marginBottom": "1.5rem"
                }),
                
                # 進度顯示區域
                html.Div([
                    # 進度條
                    html.Div([
                        html.Div([
                            html.Div(id="progress-bar", style={
                                "width": "0%",
                                "height": "100%",
                                "backgroundColor": "#007bff",
                                "borderRadius": "4px",
                                "transition": "width 0.3s ease",
                                "position": "relative"
                            })
                        ], style={
                            "width": "100%",
                            "height": "8px",
                            "backgroundColor": "rgba(255, 255, 255, 0.2)",
                            "borderRadius": "4px",
                            "overflow": "hidden",
                            "marginBottom": "1rem"
                        })
                    ]),
                    
                    # 處理狀態文字
                    html.Div([
                        html.Span(id="progress-status", children="正在解析檔案...", style={
                            "color": "#ccc",
                            "fontSize": "0.9rem",
                            "marginBottom": "0.5rem",
                            "display": "block"
                        }),
                        html.Span(id="progress-count", children="", style={
                            "color": "#007bff",
                            "fontSize": "1rem",
                            "fontWeight": "500"
                        })
                    ], style={
                        "textAlign": "center"
                    })
                ], style={
                    "width": "100%",
                    "marginBottom": "1.5rem"
                }),
                html.Div([
                    html.I(className="fas fa-exclamation-triangle", style={
                        "color": "#ffc107",
                        "fontSize": "1.2rem",
                        "marginRight": "0.5rem"
                    }),
                    html.Span("請勿離開此畫面，以免資料遺失", style={
                        "color": "#ffc107",
                        "fontSize": "1rem",
                        "fontWeight": "500"
                    })
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "backgroundColor": "rgba(255, 193, 7, 0.1)",
                    "border": "1px solid rgba(255, 193, 7, 0.3)",
                    "borderRadius": "6px",
                    "padding": "0.8rem 1.5rem",
                    "marginTop": "1rem"
                })
            ], style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "justifyContent": "center",
                "backgroundColor": "rgba(0, 0, 0, 0.8)",
                "padding": "3rem",
                "borderRadius": "12px",
                "minWidth": "300px"
            })
        ], style={
            "position": "fixed",
            "top": "0",
            "left": "0",
            "width": "100vw",
            "height": "100vh",
            "backgroundColor": "rgba(0, 0, 0, 0.7)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "zIndex": "9999",
            "backdropFilter": "blur(5px)"
        })
    ], id="fullscreen-overlay", style={"display": "none"}),
    
    html.Div([
        # 左側邊欄
        html.Div([
            
            # 銷貨資料項目
            html.Div([
                html.Div([
                    html.H4("銷貨資料", style={
                        "fontSize": "1.2rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0 0 0.25rem 0"
                    }),
                    html.P("匯入銷售交易記錄檔案", style={
                        "color": "#333",
                        "fontSize": "0.9rem",
                        "margin": "0"
                    })
                ])
            ], id="sales-item", style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "1.2rem",
                "backgroundColor": "white",
                "borderRadius": "8px",
                "border": "1px solid #e0e6ed",
                "marginBottom": "0.8rem",
                "cursor": "pointer",
                "transition": "all 0.2s ease",
                "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset"
            }),
            
            # 庫存資料項目
            html.Div([
                html.Div([
                    html.H4("庫存資料", style={
                        "fontSize": "1.2rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0 0 0.25rem 0"
                    }),
                    html.P("匯入商品庫存狀況檔案", style={
                        "color": "#333",
                        "fontSize": "0.9rem",
                        "margin": "0"
                    })
                ])
            ], id="inventory-item", style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "1.2rem",
                "backgroundColor": "white",
                "borderRadius": "8px",
                "border": "1px solid #e0e6ed",
                "marginBottom": "0.8rem",
                "cursor": "pointer",
                "transition": "all 0.2s ease",
                "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset"
            }),
            # line.zip資料項目
            html.Div([
                html.Div([
                    html.H4("line聊天記錄", style={
                        "fontSize": "1.2rem",
                        "fontWeight": "500",
                        "color": "#333",
                        "margin": "0 0 0.25rem 0"
                    }),
                    html.P("匯入line聊天記錄", style={
                        "color": "#333",
                        "fontSize": "0.9rem",
                        "margin": "0"
                    })
                ])
            ], id="line-zip-item", style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "1.2rem",
                "backgroundColor": "white",
                "borderRadius": "8px",
                "border": "1px solid #e0e6ed",
                "marginBottom": "0.8rem",
                "cursor": "pointer",
                "transition": "all 0.2s ease",
                "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset"
            })
            
        ], style={
            "width": "350px",
            "height": "85vh",
            "backgroundColor": "white",
            "padding": "1.5rem",
            "borderRight": "1px solid #e0e6ed",
            "overflow": "hidden"
        }),
        
        # 右側上傳檔案區域
        html.Div([
            html.Div([
                html.Div(id='current-data-type', children="請選擇資料類型", style={
                    "fontSize": "1.5rem",
                    "fontWeight": "600",
                    "color": "#333",
                    "marginBottom": "1rem"
                }),
                # 左右排列區域
                html.Div([
                    # 左側：上傳檔案區域
                    html.Div([
                        dcc.Upload(
                            id='import-upload-data',
                            children=html.Div([
                                html.I(id="upload-icon", className="fas fa-cloud-upload-alt", style={
                                    "fontSize": "2.5rem",
                                    "color": "#007bff",
                                    "marginBottom": "1rem"
                                }),
                                html.P(id="upload-text-main", children="拖拽檔案到此處或點擊上傳", style={
                                    "fontSize": "1rem",
                                    "color": "#666",
                                    "margin": "0"
                                }),
                                html.P(id="upload-text-sub", children="支援.xlsx, .xls檔案", style={
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
                                "height": "100vh",
                                "borderWidth": "2px",
                                "borderStyle": "dashed",
                                "borderColor": "#007bff",
                                "borderRadius": "12px",
                                "textAlign": "center",
                                "backgroundColor": "#f8f9ff",
                                "cursor": "pointer",
                                "transition": "all 0.3s ease"
                            },
                            multiple=False,
                            disabled=True  # 初始狀態為禁用
                        )
                    ], style={"width": "40%"}),
                    
                    # 右側：檔案列表區域
                    html.Div([
                        html.Div(id='import-output-data-upload', style={
                            "height": "65vh",
                            "overflowY": "auto",
                            "border": "1px solid #dee2e6",
                            "borderRadius": "6px",
                            "padding": "15px",
                            "backgroundColor": "#ffffff"
                        })
                    ], style={"width": "58%"})
                    
                ], style={
                    "display": "flex",
                    "gap": "2%",
                    "alignItems": "flex-start"
                }),
                
                # 儲存按鈕區域
                html.Div([
                    dbc.Button("匯入上傳檔案", 
                              id="save-current-files-btn",
                              color="success",
                              size="sm",
                              disabled=True,  # 初始狀態為禁用
                              style={
                                  "width": "200px",
                                  "whiteSpace": "nowrap",
                                  "fontSize": "1rem",
                                  "backgroundColor": "#6c757d",
                                  "borderColor": "#6c757d",
                                  "cursor": "not-allowed",
                                  "opacity": "0.6"
                              })
                ], style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "paddingTop": "1rem",
                    "marginTop": "auto"
                })
            ], style={
                "padding": "1rem",
                "backgroundColor": "white",
                "borderRadius": "12px",
                "height": "calc(85vh - 2rem)",
                "display": "flex",
                "flexDirection": "column"
            })
        ], style={
            "flex": "1",
            "padding": "1rem",
            "backgroundColor": "#ffffff",
            "height": "85vh",
            "overflow": "hidden"
        })
        
    ], style={
        "display": "flex",
        "height": "85vh",
        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "overflow": "hidden"
    })
], style={
    "height": "85vh",
    "overflow": "hidden",
    "margin": "0",
    "padding": "0"
})

# 導入回調函數
from callbacks import import_data_callbacks