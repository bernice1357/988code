import dash
from dash import Input, Output, State, no_update, ALL, callback_context
import datetime
import base64
import io
import tempfile
import os
import requests
import dash_bootstrap_components as dbc
import pandas as pd
from pages.common import *

# 導入必要的模組
import logging

# 在文件開頭新增縣市區域對應字典
CITY_DISTRICT_MAP = {
    "台北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],
    "新北市": ["萬里區", "金山區", "板橋區", "汐止區", "深坑區", "石碇區", "瑞芳區", "平溪區", "雙溪區", "貢寮區", "新店區", "坪林區", "烏來區", "永和區", "中和區", "土城區", "三峽區", "樹林區", "鶯歌區", "三重區", "新莊區", "泰山區", "林口區", "蘆洲區", "五股區", "八里區", "淡水區", "三芝區", "石門區"],
    "桃園市": ["中壢區", "平鎮區", "龍潭區", "楊梅區", "新屋區", "觀音區", "桃園區", "龜山區", "八德區", "大溪區", "復興區", "大園區", "蘆竹區"],
    "台中市": ["中區", "東區", "南區", "西區", "北區", "北屯區", "西屯區", "南屯區", "太平區", "大里區", "霧峰區", "烏日區", "豐原區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "潭子區", "大雅區", "神岡區", "大肚區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "左鎮區", "玉井區", "楠西區", "南化區", "仁德區", "關廟區", "龍崎區", "官田區", "麻豆區", "佳里區", "西港區", "七股區", "將軍區", "學甲區", "北門區", "新營區", "後壁區", "白河區", "東山區", "六甲區", "下營區", "柳營區", "鹽水區", "善化區", "大內區", "山上區", "新市區", "安定區"],
    "高雄市": ["新興區", "前金區", "苓雅區", "鹽埕區", "鼓山區", "旗津區", "前鎮區", "三民區", "楠梓區", "小港區", "左營區", "仁武區", "大社區", "岡山區", "路竹區", "阿蓮區", "田寮區", "燕巢區", "橋頭區", "梓官區", "彌陀區", "永安區", "湖內區", "鳳山區", "大寮區", "林園區", "鳥松區", "大樹區", "旗山區", "美濃區", "六龜區", "內門區", "杉林區", "甲仙區", "桃源區", "那瑪夏區", "茂林區", "茄萣區"],
    "宜蘭縣": ["宜蘭市", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "羅東鎮", "三星鄉", "大同鄉", "五結鄉", "冬山鄉", "蘇澳鎮", "南澳鄉"],
    "新竹縣": ["竹北市", "湖口鄉", "新豐鄉", "新埔鎮", "關西鎮", "芎林鄉", "寶山鄉", "竹東鎮", "五峰鄉", "橫山鄉", "尖石鄉", "北埔鄉", "峨眉鄉"],
    "苗栗縣": ["竹南鎮", "頭份市", "三灣鄉", "南庄鄉", "獅潭鄉", "後龍鎮", "通霄鎮", "苑裡鎮", "苗栗市", "造橋鄉", "頭屋鄉", "公館鄉", "大湖鄉", "泰安鄉", "銅鑼鄉", "三義鄉", "西湖鄉", "卓蘭鎮"],
    "彰化縣": ["彰化市", "芬園鄉", "花壇鄉", "秀水鄉", "鹿港鎮", "福興鄉", "線西鄉", "和美鎮", "伸港鄉", "員林市", "社頭鄉", "永靖鄉", "埔心鄉", "溪湖鎮", "大村鄉", "埔鹽鄉", "田中鎮", "北斗鎮", "田尾鄉", "埔頭鄉", "溪州鄉", "竹塘鄉", "二林鎮", "大城鄉", "芳苑鄉", "二水鄉"],
    "南投縣": ["南投市", "中寮鄉", "草屯鎮", "國姓鄉", "埔里鎮", "仁愛鄉", "名間鄉", "集集鎮", "水里鄉", "魚池鄉", "信義鄉", "竹山鎮", "鹿谷鄉"],
    "雲林縣": ["斗南鎮", "大埤鄉", "虎尾鎮", "土庫鎮", "褒忠鄉", "東勢鄉", "台西鄉", "崙背鄉", "麥寮鄉", "斗六市", "林內鄉", "古坑鄉", "莿桐鄉", "西螺鎮", "二崙鄉", "北港鎮", "水林鄉", "口湖鄉", "四湖鄉", "元長鄉"],
    "嘉義縣": ["太保市", "朴子市", "布袋鎮", "大林鎮", "民雄鄉", "中埔鄉", "大埔鄉", "水上鄉", "鹿草鄉", "東石鄉", "六腳鄉", "新港鄉", "溪口鄉", "義竹鄉", "番路鄉", "梅山鄉", "竹崎鄉", "阿里山鄉"],
    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮", "三地門鄉", "霧台鄉", "瑪家鄉", "九如鄉", "里港鄉", "高樹鄉", "鹽埔鄉", "長治鄉", "麟洛鄉", "竹田鄉", "內埔鄉", "萬丹鄉", "泰武鄉", "來義鄉", "萬巒鄉", "崁頂鄉", "新園鄉", "新埤鄉", "南州鄉", "林邊鄉", "琉球鄉", "佳冬鄉", "枋寮鄉", "枋山鄉", "春日鄉", "獅子鄉", "車城鄉", "牡丹鄉", "滿州鄉"],
    "台東縣": ["台東市", "綠島鄉", "蘭嶼鄉", "延平鄉", "卑南鄉", "鹿野鄉", "關山鎮", "海端鄉", "池上鄉", "東河鄉", "成功鎮", "長濱鄉", "太麻里鄉", "金峰鄉", "大武鄉", "達仁鄉"],
    "花蓮縣": ["花蓮市", "新城鄉", "秀林鄉", "吉安鄉", "壽豐鄉", "鳳林鎮", "光復鄉", "豐濱鄉", "瑞穗鄉", "萬榮鄉", "玉里鎮", "卓溪鄉", "富里鄉"],
    "澎湖縣": ["馬公市", "西嶼鄉", "望安鄉", "七美鄉", "白沙鄉", "湖西鄉"],
    "金門縣": ["金沙鎮", "金湖鎮", "金寧鄉", "金城鎮", "烈嶼鄉", "烏坵鄉（代管）"],
    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"]
}

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 服務器配置
API_BASE_URL = "http://127.0.0.1:8000"  # 假設 FastAPI 在 8000 端口運行

# 全域變數來儲存當前選中的資料類型
current_data_type = None

# 儲存已上傳檔案的變數 - 每個資料類型可存多個檔案
uploaded_files_store = {
    "customer": [],
    "sales": [],
    "inventory": []
}

def get_file_icon(filename):
    """根據檔案副檔名返回對應的 Font Awesome 圖示類別"""
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if extension == 'csv':
        return "fas fa-file-csv"
    elif extension in ['xls', 'xlsx']:
        return "fas fa-file-excel"
    else:
        return "fas fa-file"

def get_file_color(filename):
    """根據檔案類型返回對應的顏色"""
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if extension == 'csv':
        return "#28a745"
    elif extension in ['xls', 'xlsx']:
        return "#107c41"
    else:
        return "#495057"

def validate_file_columns(contents, filename, data_type):
    """驗證上傳檔案的欄位是否與資料表匹配"""
    try:
        # 定義各資料類型所需的欄位
        required_columns = {
            "customer": ["customer_id", "customer_name", "phone_number", "address", "delivery_schedule", "notes"],
            "sales": ["transaction_date", "customer_id", "customer_name", "product_id", "product_name", "quantity", "unit_price", "total_amount"],
            "inventory": ["product_id", "product_name", "category", "subcategory", "warehouse_id", "stock_quantity", "unit_price", "updated_at"]
        }
        
        if data_type not in required_columns:
            return False, f"未知的資料類型: {data_type}"
        
        expected_columns = set(required_columns[data_type])
        
        # 解析檔案內容
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            # 嘗試讀取檔案
            if filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(decoded))
            else:
                return False, "不支援的檔案格式"
            
            # 檢查欄位
            actual_columns = set(df.columns.tolist())
            
            # 檢查是否有遺漏的必要欄位
            missing_columns = expected_columns - actual_columns
            # 檢查是否有多餘的欄位
            extra_columns = actual_columns - expected_columns
            
            if missing_columns or extra_columns:
                error_msg = f"檔案 '{filename}' 欄位不匹配："
                if missing_columns:
                    error_msg += f"\n缺少欄位：{', '.join(sorted(missing_columns))}"
                if extra_columns:
                    error_msg += f"\n多餘欄位：{', '.join(sorted(extra_columns))}"
                error_msg += f"\n預期欄位：{', '.join(sorted(expected_columns))}"
                return False, error_msg
            
            return True, "欄位驗證通過"
            
        except Exception as e:
            return False, f"讀取檔案失敗：{str(e)}"
            
    except Exception as e:
        return False, f"驗證過程發生錯誤：{str(e)}"

# 新增：轉換配送日程為數字字符串的函數
def convert_delivery_schedule_to_numbers(schedule_list):
    """將配送日程列表轉換為數字字符串"""
    if not schedule_list:
        return ""
    return ','.join(schedule_list)

# 側邊欄項目點擊回調
@app.callback(
    [Output("customer-item", "style"),
     Output("sales-item", "style"), 
     Output("inventory-item", "style"),
     Output("current-data-type", "children")],
    [Input("customer-item", "n_clicks"),
     Input("sales-item", "n_clicks"),
     Input("inventory-item", "n_clicks")],
    prevent_initial_call=True
)
def update_sidebar_selection(customer_clicks, sales_clicks, inventory_clicks):
    global current_data_type
    ctx = dash.callback_context
    if not ctx.triggered:
        return [no_update] * 4
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # 基本樣式
    base_style = {
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
    }
    
    # 選中樣式
    selected_style = base_style.copy()
    selected_style.update({
        "border": "1px solid #2196f3",
        "boxShadow": "rgb(204, 219, 232) 3px 3px 6px 0px inset, rgba(255, 255, 255, 0.5) -3px -3px 6px 1px inset"
    })
    
    # 返回樣式列表
    styles = [base_style, base_style, base_style]
    title = "請選擇資料類型"
    
    if button_id == "customer-item":
        styles[0] = selected_style
        title = "客戶資料上傳"
        current_data_type = "customer"
    elif button_id == "sales-item":
        styles[1] = selected_style
        title = "銷貨資料上傳"
        current_data_type = "sales"
    elif button_id == "inventory-item":
        styles[2] = selected_style
        title = "庫存資料上傳"
        current_data_type = "inventory"
    
    return styles + [title]

# 控制上傳區域狀態的回調
@app.callback(
    [Output('import-upload-data', 'disabled'),
     Output('import-upload-data', 'style'),
     Output('upload-icon', 'style'),
     Output('upload-text-main', 'children'),
     Output('upload-text-main', 'style'),
     Output('upload-text-sub', 'children'),
     Output('upload-text-sub', 'style')],
    [Input('current-data-type', 'children')],
    prevent_initial_call=False
)
def update_upload_area_state(current_title):
    global current_data_type
    
    # 如果沒有選擇資料類型，禁用上傳
    if current_data_type is None or current_title == "請選擇資料類型":
        # 禁用狀態的樣式
        disabled_style = {
            "width": "100%",
            "height": "65vh",
            "borderWidth": "2px",
            "borderStyle": "dashed",
            "borderColor": "#ccc",
            "borderRadius": "12px",
            "textAlign": "center",
            "backgroundColor": "#f5f5f5",
            "cursor": "not-allowed",
            "transition": "all 0.3s ease",
            "opacity": "0.6"
        }
        
        disabled_icon_style = {
            "fontSize": "3rem",
            "color": "#999",
            "marginBottom": "1rem"
        }
        
        disabled_text_main_style = {
            "fontSize": "1.1rem",
            "color": "#999",
            "margin": "0"
        }
        
        disabled_text_sub_style = {
            "fontSize": "0.9rem",
            "color": "#bbb",
            "margin": "0.5rem 0 0 0"
        }
        
        return (
            True,  # disabled
            disabled_style,
            disabled_icon_style,
            "請先選擇左側的資料類型",
            disabled_text_main_style,
            "選擇後即可上傳檔案",
            disabled_text_sub_style
        )
    else:
        # 啟用狀態的樣式
        enabled_style = {
            "width": "100%",
            "height": "65vh",
            "borderWidth": "2px",
            "borderStyle": "dashed",
            "borderColor": "#007bff",
            "borderRadius": "12px",
            "textAlign": "center",
            "backgroundColor": "#f8f9ff",
            "cursor": "pointer",
            "transition": "all 0.3s ease",
            "opacity": "1"
        }
        
        enabled_icon_style = {
            "fontSize": "3rem",
            "color": "#007bff",
            "marginBottom": "1rem"
        }
        
        enabled_text_main_style = {
            "fontSize": "1.1rem",
            "color": "#666",
            "margin": "0"
        }
        
        enabled_text_sub_style = {
            "fontSize": "0.9rem",
            "color": "#999",
            "margin": "0.5rem 0 0 0"
        }
        
        return (
            False,  # disabled
            enabled_style,
            enabled_icon_style,
            "拖拽檔案到此處或點擊上傳",
            enabled_text_main_style,
            "支援.xlsx, .xls檔案",
            enabled_text_sub_style
        )

# 控制儲存按鈕狀態的回調
@app.callback(
    [Output("save-current-files-btn", "disabled"),
     Output("save-current-files-btn", "style")],
    [Input("current-data-type", "children"),
     Input("import-output-data-upload", "children")],
    prevent_initial_call=False
)
def update_save_button_state(current_title, file_display):
    global current_data_type, uploaded_files_store
    
    # 檢查是否選擇了資料類型且有檔案
    has_selection = current_data_type is not None and current_title != "請選擇資料類型"
    has_file = len(uploaded_files_store.get(current_data_type, [])) > 0 if current_data_type else False
    
    if has_selection and has_file:
        # 啟用狀態
        enabled_style = {
            "width": "200px",
            "whiteSpace": "nowrap",
            "fontSize": "1rem",
            "backgroundColor": "#28a745",
            "borderColor": "#28a745",
            "color": "white",
            "cursor": "pointer",
            "opacity": "1"
        }
        return False, enabled_style
    else:
        # 禁用狀態
        disabled_style = {
            "width": "200px",
            "whiteSpace": "nowrap",
            "fontSize": "1rem",
            "backgroundColor": "#6c757d",
            "borderColor": "#6c757d",
            "color": "white",
            "cursor": "not-allowed",
            "opacity": "0.6"
        }
        return True, disabled_style

# 檔案上傳回調函數
@app.callback(
    [Output('import-output-data-upload', 'children'),
     Output('import-upload-data', 'contents'),
     Output('import_data-error-toast', 'is_open', allow_duplicate=True),
     Output('import_data-error-toast', 'children', allow_duplicate=True)],
    Input('import-upload-data', 'contents'),
    State('import-upload-data', 'filename'),
    State('import-upload-data', 'last_modified'),
    prevent_initial_call=True
)
def update_upload_output(contents, filename, last_modified):
    global current_data_type, uploaded_files_store
    
    if contents is not None:
        if current_data_type is None:
            return html.Div([
                html.Span("請先從左側選擇要匯入的資料類型", style={
                    "color": "#856404",
                    "fontWeight": "500",
                    "fontSize": "1rem"
                })
            ], style={
                "textAlign": "center",
                "padding": "1rem"
            }), None, False, ""
        
        # 檢查檔案格式
        if filename:
            extension = filename.lower().split('.')[-1] if '.' in filename else ''
            if extension not in ['xls', 'xlsx']:
                return html.Div([
                    html.Span("不支援的檔案格式，僅支援.xlsx, .xls檔案", style={
                        "color": "#dc3545",
                        "fontWeight": "500",
                        "fontSize": "1rem"
                    })
                ], style={
                    "textAlign": "center",
                    "padding": "1rem"
                }), None, True, "不支援的檔案格式，僅支援.xlsx, .xls檔案"
            
            # 檢查檔案欄位是否匹配 (暫時關閉驗證)
            is_valid, validation_message = validate_file_columns(contents, filename, current_data_type)
            if False:  # 暫時關閉驗證
                # 只顯示 error toast，不改變檔案列表顯示
                current_files = uploaded_files_store.get(current_data_type, []) if current_data_type else []
                if current_files:
                    file_items = []
                    for i, file_info in enumerate(current_files):
                        file_icon = get_file_icon(file_info['filename'])
                        file_color = get_file_color(file_info['filename'])
                        
                        file_item = html.Div([
                            html.Div([
                                html.I(className=file_icon, style={
                                    "fontSize": "20px", 
                                    "marginRight": "12px", 
                                    "color": file_color
                                }),
                                html.Div([
                                    html.H6(file_info['filename'], style={
                                        "margin": "0", 
                                        "color": "#212529", 
                                        "fontSize": "14px"
                                    }),
                                    html.Small(f"新上傳 - {datetime.datetime.fromtimestamp(file_info['date']).strftime('%Y-%m-%d %H:%M:%S')}", 
                                             style={"color": "#6c757d", "fontSize": "12px"})
                                ], style={"flex": "1"})
                            ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                            html.Div([
                                html.Button("刪除", 
                                           id={"type": "delete-file-btn", "index": i, "data_type": current_data_type},
                                           style={
                                               "background": "none",
                                               "border": "1px solid #dc3545",
                                               "color": "#dc3545",
                                               "padding": "4px 8px",
                                               "borderRadius": "4px",
                                               "fontSize": "12px",
                                               "cursor": "pointer"
                                           })
                            ])
                        ], style={
                            "display": "flex", 
                            "justifyContent": "space-between", 
                            "alignItems": "center",
                            "padding": "12px",
                            "marginBottom": "5px",
                            "backgroundColor": "#f8f9fa",
                            "borderRadius": "6px",
                            "border": "1px solid #e0e6ed"
                        })
                        file_items.append(file_item)
                    
                    return html.Div([
                        html.H6(f"已上傳檔案 ({len(current_files)})", 
                               style={"margin": "0 0 15px 0", "color": "#495057", "fontSize": "16px"}),
                        html.Div(file_items)
                    ]), None, True, validation_message
                else:
                    return html.Div([
                        html.Span("尚未上傳任何檔案", style={
                            "color": "#6c757d",
                            "fontStyle": "italic",
                            "fontSize": "1rem"
                        })
                    ], style={
                        "textAlign": "center",
                        "padding": "2rem"
                    }), None, True, validation_message
            
            # 累積檔案模式 - 檢查是否已存在相同檔名，如果存在就更新，否則新增
            current_files = uploaded_files_store[current_data_type]
            existing_file_index = next((i for i, f in enumerate(current_files) if f['filename'] == filename), -1)
            if existing_file_index >= 0:
                # 更新現有檔案
                current_files[existing_file_index] = {
                    'filename': filename,
                    'date': last_modified,
                    'contents': contents
                }
            else:
                # 新增檔案
                current_files.append({
                    'filename': filename,
                    'date': last_modified,
                    'contents': contents
                })
    
    # 生成檔案列表顯示 - 多檔案模式
    current_files = uploaded_files_store.get(current_data_type, []) if current_data_type else []
    
    if current_files:
        type_names = {
            "customer": "客戶資料",
            "sales": "銷貨資料",
            "inventory": "庫存資料"
        }
        type_name = type_names.get(current_data_type, "資料")
        
        file_items = []
        for i, file_info in enumerate(current_files):
            file_icon = get_file_icon(file_info['filename'])
            file_color = get_file_color(file_info['filename'])
            
            file_item = html.Div([
                html.Div([
                    html.I(className=file_icon, style={
                        "fontSize": "20px", 
                        "marginRight": "12px", 
                        "color": file_color
                    }),
                    html.Div([
                        html.H6(file_info['filename'], style={
                            "margin": "0", 
                            "color": "#212529", 
                            "fontSize": "14px"
                        }),
                        html.Small(f"新上傳 - {datetime.datetime.fromtimestamp(file_info['date']).strftime('%Y-%m-%d %H:%M:%S')}", 
                                 style={"color": "#6c757d", "fontSize": "12px"})
                    ], style={"flex": "1"})
                ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                html.Div([
                    html.Button("刪除", 
                               id={"type": "delete-file-btn", "index": i, "data_type": current_data_type},
                               style={
                                   "background": "none",
                                   "border": "1px solid #dc3545",
                                   "color": "#dc3545",
                                   "padding": "4px 8px",
                                   "borderRadius": "4px",
                                   "fontSize": "12px",
                                   "cursor": "pointer"
                               })
                ])
            ], style={
                "display": "flex", 
                "justifyContent": "space-between", 
                "alignItems": "center",
                "padding": "12px",
                "marginBottom": "5px",
                "backgroundColor": "#f8f9fa",
                "borderColor": "#e0e6ed",
                "borderRadius": "6px",
                "border": "1px solid #e0e6ed"
            })
            file_items.append(file_item)
        
        return html.Div([
            html.H6(f"已上傳檔案 ({len(current_files)})", 
                   style={"margin": "0 0 15px 0", "color": "#495057", "fontSize": "16px"}),
            html.Div(file_items)
        ]), None, False, ""
    else:
        return html.Div([
            html.Span("尚未上傳任何檔案", style={
                "color": "#6c757d",
                "fontStyle": "italic",
                "fontSize": "1rem"
            })
        ], style={
            "textAlign": "center",
            "padding": "2rem"
        }), None, False, ""

# 處理刪除檔案功能
@app.callback(
    Output('import-output-data-upload', 'children', allow_duplicate=True),
    Input({"type": "delete-file-btn", "index": ALL, "data_type": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def delete_file(n_clicks_list):
    global uploaded_files_store, current_data_type
    
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return no_update
    
    # 解析被點擊的按鈕資訊
    triggered_prop_id = ctx.triggered[0]["prop_id"]
    if ctx.triggered[0]["value"]:
        import json
        triggered_id = json.loads(triggered_prop_id.split('.')[0])
        file_index = triggered_id['index']
        data_type = triggered_id['data_type']
        
        # 刪除對應的檔案（多檔案模式）
        if data_type in uploaded_files_store and 0 <= file_index < len(uploaded_files_store[data_type]):
            uploaded_files_store[data_type].pop(file_index)
        
        # 重新生成當前資料類型的檔案顯示
        current_files = uploaded_files_store.get(current_data_type, []) if current_data_type else []
        
        if current_files:
            type_names = {
                "customer": "客戶資料",
                "sales": "銷貨資料",
                "inventory": "庫存資料"
            }
            type_name = type_names.get(current_data_type, "資料")
            
            file_items = []
            for i, file_info in enumerate(current_files):
                file_icon = get_file_icon(file_info['filename'])
                file_color = get_file_color(file_info['filename'])
                
                file_item = html.Div([
                    html.Div([
                        html.I(className=file_icon, style={
                            "fontSize": "20px", 
                            "marginRight": "12px", 
                            "color": file_color
                        }),
                        html.Div([
                            html.H6(file_info['filename'], style={
                                "margin": "0", 
                                "color": "#212529", 
                                "fontSize": "14px"
                            }),
                            html.Small(f"新上傳 - {datetime.datetime.fromtimestamp(file_info['date']).strftime('%Y-%m-%d %H:%M:%S')}", 
                                     style={"color": "#6c757d", "fontSize": "12px"})
                        ], style={"flex": "1"})
                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                    html.Div([
                        html.Button("刪除", 
                                   id={"type": "delete-file-btn", "index": i, "data_type": current_data_type},
                                   style={
                                       "background": "none",
                                       "border": "1px solid #dc3545",
                                       "color": "#dc3545",
                                       "padding": "4px 8px",
                                       "borderRadius": "4px",
                                       "fontSize": "12px",
                                       "cursor": "pointer"
                                   })
                    ])
                ], style={
                    "display": "flex", 
                    "justifyContent": "space-between", 
                    "alignItems": "center",
                    "padding": "12px",
                    "marginBottom": "5px",
                    "backgroundColor": "#f8f9fa",
                    "borderColor": "#e0e6ed",
                    "borderRadius": "6px",
                    "border": "1px solid #e0e6ed"
                })
                file_items.append(file_item)
            
            return html.Div([
                html.H6(f"已上傳檔案 ({len(current_files)})", 
                       style={"margin": "0 0 15px 0", "color": "#495057", "fontSize": "16px"}),
                html.Div(file_items)
            ])
        else:
            return html.Div([
                html.Span("尚未上傳任何檔案", style={
                    "color": "#6c757d",
                    "fontStyle": "italic",
                    "fontSize": "1rem"
                })
            ], style={
                "textAlign": "center",
                "padding": "2rem"
            })
    
    return no_update

# 當選擇不同資料類型時，更新檔案列表顯示
@app.callback(
    Output('import-output-data-upload', 'children', allow_duplicate=True),
    Input('current-data-type', 'children'),
    prevent_initial_call=True
)
def update_file_list_on_selection(current_title):
    global uploaded_files_store, current_data_type
    
    # 根據當前選中的資料類型顯示對應的檔案
    current_files = uploaded_files_store.get(current_data_type, []) if current_data_type else []
    
    if current_files:
        type_names = {
            "customer": "客戶資料",
            "sales": "銷貨資料",
            "inventory": "庫存資料"
        }
        type_name = type_names.get(current_data_type, "資料")
        
        file_items = []
        for i, file_info in enumerate(current_files):
            file_icon = get_file_icon(file_info['filename'])
            file_color = get_file_color(file_info['filename'])
            
            file_item = html.Div([
                html.Div([
                    html.I(className=file_icon, style={
                        "fontSize": "20px", 
                        "marginRight": "12px", 
                        "color": file_color
                    }),
                    html.Div([
                        html.H6(file_info['filename'], style={
                            "margin": "0", 
                            "color": "#212529", 
                            "fontSize": "14px"
                        }),
                        html.Small(f"新上傳 - {datetime.datetime.fromtimestamp(file_info['date']).strftime('%Y-%m-%d %H:%M:%S')}", 
                                 style={"color": "#6c757d", "fontSize": "12px"})
                    ], style={"flex": "1"})
                ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
                html.Div([
                    html.Button("刪除", 
                               id={"type": "delete-file-btn", "index": i, "data_type": current_data_type},
                               style={
                                   "background": "none",
                                   "border": "1px solid #dc3545",
                                   "color": "#dc3545",
                                   "padding": "4px 8px",
                                   "borderRadius": "4px",
                                   "fontSize": "12px",
                                   "cursor": "pointer"
                               })
                ])
            ], style={
                "display": "flex", 
                "justifyContent": "space-between", 
                "alignItems": "center",
                "padding": "12px",
                "marginBottom": "5px",
                "backgroundColor": "#f8f9fa",
                "borderColor": "#e0e6ed",
                "borderRadius": "6px",
                "border": "1px solid #e0e6ed"
            })
            file_items.append(file_item)
        
        return html.Div([
            html.H6(f"已上傳檔案 ({len(current_files)})", 
                   style={"margin": "0 0 15px 0", "color": "#495057", "fontSize": "16px"}),
            html.Div(file_items)
        ])
    else:
        return html.Div([
            html.Span("尚未上傳任何檔案", style={
                "color": "#6c757d",
                "fontStyle": "italic",
                "fontSize": "1rem"
            })
        ], style={
            "textAlign": "center",
            "padding": "2rem"
        })

# 控制全螢幕載入遮罩的回調函數
@app.callback(
    [Output("fullscreen-overlay", "style"),
     Output("import-session-store", "data")],
    Input("save-current-files-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_loading_overlay(n_clicks):
    if n_clicks:
        # 顯示全螢幕載入遮罩，創建新的會話ID並設置為開始狀態
        # 每次點擊都會創建新的會話，確保進度條正確重置
        new_session = {
            'session_id': n_clicks, 
            'total_records': 0, 
            'status': 'processing', 
            'deleted_count': 0, 
            'inserted_count': 0
        }
        return {"display": "block"}, new_session
    return {"display": "none"}, {'session_id': 0, 'total_records': 0, 'status': 'waiting', 'deleted_count': 0, 'inserted_count': 0}

# 進度條更新回調函數
@app.callback(
    [Output("progress-bar", "style"),
     Output("progress-status", "children"),
     Output("progress-count", "children")],
    [Input("import-session-store", "data")],
    prevent_initial_call=True
)
def update_progress(session_data):
    # 獲取當前會話的狀態
    total_records = session_data.get('total_records', 0)
    processing_status = session_data.get('status', 'waiting')
    deleted_count = session_data.get('deleted_count', 0)
    inserted_count = session_data.get('inserted_count', 0)
    
    if processing_status == 'waiting':
        # 等待開始
        progress_style = {
            "width": "0%",
            "height": "100%",
            "backgroundColor": "#007bff",
            "borderRadius": "4px",
            "transition": "width 0.3s ease",
            "position": "relative"
        }
        return progress_style, "準備開始...", ""
    
    elif processing_status == 'processing':
        # 正在處理中
        progress_style = {
            "width": "50%",
            "height": "100%",
            "backgroundColor": "#007bff",
            "borderRadius": "4px",
            "transition": "width 0.3s ease",
            "position": "relative"
        }
        return progress_style, "正在處理檔案...", "請稍候，正在匯入資料"
    
    elif processing_status == 'completed':
        # 完成狀態
        progress_style = {
            "width": "100%",
            "height": "100%",
            "backgroundColor": "#28a745",
            "borderRadius": "4px",
            "transition": "width 0.3s ease",
            "position": "relative"
        }
        
        # 顯示實際處理結果
        if inserted_count > 0:
            count_text = f"刪除 {deleted_count} 筆，新增 {inserted_count} 筆記錄"
        else:
            count_text = "處理完成"
            
        return progress_style, "處理完成！", count_text
    
    elif processing_status == 'error':
        # 錯誤狀態
        progress_style = {
            "width": "100%",
            "height": "100%",
            "backgroundColor": "#dc3545",
            "borderRadius": "4px",
            "transition": "width 0.3s ease",
            "position": "relative"
        }
        return progress_style, "處理失敗", "請檢查檔案格式或聯絡管理員"
    
    else:
        # 預設狀態
        progress_style = {
            "width": "0%",
            "height": "100%",
            "backgroundColor": "#007bff",
            "borderRadius": "4px",
            "transition": "width 0.3s ease",
            "position": "relative"
        }
        return progress_style, "準備開始...", ""

# 處理銷貨資料匯入的輔助函數
def process_sales_import(current_files, session_data, user_role):
    """處理銷貨資料匯入的輔助函數"""
    try:
        total_records_processed = 0
        processing_results = []
        
        # 處理多個檔案
        for file_info in current_files:
            filename = file_info['filename']
            contents = file_info['contents']
            
            # 檢查是否為 Excel 文件
            if filename.lower().endswith(('.xlsx', '.xls')):
                # 解碼 base64 內容
                content_type, content_string = contents.split(',')
                decoded_content = base64.b64decode(content_string)
                
                try:
                    # 準備檔案和表單資料上傳到 API
                    files = {
                        'file': (filename, decoded_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    }
                    data = {
                        'user_role': user_role or 'viewer'
                    }
                    
                    # 呼叫 API 處理檔案
                    api_url = f"{API_BASE_URL}/import/sales"
                    logger.info(f"正在處理檔案: {filename}")
                    response = requests.post(api_url, files=files, data=data, timeout=300)
                    
                    logger.info(f"API 回應狀態碼: {response.status_code}")
                    logger.info(f"API 回應內容: {response.text}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"解析後的回應: {result}")
                        
                        if result.get('success'):
                            deleted_count = result.get('deleted_count', 0)
                            inserted_count = result.get('inserted_count', 0)
                            total_records_processed += inserted_count
                            
                            # 更新會話數據為完成狀態，包含實際處理結果
                            session_data['status'] = 'completed'
                            session_data['total_records'] = inserted_count
                            session_data['deleted_count'] = deleted_count
                            session_data['inserted_count'] = inserted_count
                            
                            status_message = f"刪除 {deleted_count} 筆舊記錄，新增 {inserted_count} 筆交易記錄"
                            processing_results.append(f"{filename}: {status_message}")
                            logger.info(f"檔案 {filename} 處理成功: {status_message}")
                        else:
                            error_msg = result.get('message', 'API 處理失敗')
                            processing_results.append(f"{filename}: {error_msg}")
                            logger.error(f"檔案 {filename} 處理失敗: {error_msg}")
                            # 設置錯誤狀態
                            session_data['status'] = 'error'
                    else:
                        try:
                            error_detail = response.json().get('detail', '未知錯誤')
                        except:
                            error_detail = response.text if response.content else '服務器無回應'
                        processing_results.append(f"{filename}: API 錯誤 (狀態碼 {response.status_code}) - {error_detail}")
                        logger.error(f"API 錯誤: 狀態碼 {response.status_code}, 內容: {error_detail}")
                        # 設置錯誤狀態
                        session_data['status'] = 'error'
                    
                except requests.exceptions.RequestException as e:
                    processing_results.append(f"{filename}: 網路錯誤 - {str(e)}")
                    # 設置錯誤狀態
                    session_data['status'] = 'error'
                except Exception as e:
                    processing_results.append(f"{filename}: 處理錯誤 - {str(e)}")
                    # 設置錯誤狀態
                    session_data['status'] = 'error'
            else:
                processing_results.append(f"{filename}: 跳過 (非 Excel 檔案)")
        
        # 顯示處理結果
        logger.info(f"處理結果彙總: 總處理記錄數 = {total_records_processed}")
        logger.info(f"處理結果詳情: {processing_results}")
        
        if total_records_processed > 0:
            success_details = f"銷貨資料處理完成，共處理 {total_records_processed} 筆記錄"
            success_message = f"✅ 成功處理銷貨資料檔案！{success_details}\n\n詳細結果:\n" + "\n".join(processing_results)
            return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                   True, success_message, False, "", False, "", [], {}, False)
        else:
            # 檢查是否有錯誤訊息
            error_files = [result for result in processing_results if any(keyword in result for keyword in ['錯誤', '失敗', '跳過'])]
            if error_files:
                error_message = "\n".join(error_files)
                return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                       False, "", True, error_message, False, "", [], {}, False)
            else:
                success_message = f"已上傳 {len(current_files)} 個銷貨資料檔案，但未處理任何記錄。請檢查檔案格式或內容。"
                return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                       True, success_message, False, "", False, "", [], {}, False)
        
    except Exception as e:
        error_message = f"處理銷貨資料時發生錯誤: {str(e)}"
        return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
               False, "", True, error_message, False, "", [], {}, False)

# 新增：儲存當前檔案並檢查客戶的回調函數
@app.callback(
    [Output("save-current-files-btn", "children", allow_duplicate=True),
     Output("save-current-files-btn", "disabled", allow_duplicate=True),
     Output("fullscreen-overlay", "style", allow_duplicate=True),
     Output("import-session-store", "data", allow_duplicate=True),
     Output("import_data-success-toast", "is_open"),
     Output("import_data-success-toast", "children"),
     Output("import_data-error-toast", "is_open"),
     Output("import_data-error-toast", "children"),
     Output("import_data-warning-toast", "is_open"),
     Output("import_data-warning-toast", "children"),
     Output("missing-customers-store", "data"),
     Output("current-file-store", "data"),
     Output("new-customer-modal", "is_open")],
    [Input("save-current-files-btn", "n_clicks")],
    [State("import-session-store", "data"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def save_current_files(n_clicks, session_data, user_role):
    global uploaded_files_store, current_data_type
    
    if n_clicks and current_data_type:
        current_files = uploaded_files_store.get(current_data_type, [])
        
        if current_files:
            type_names = {
                "customer": "客戶資料",
                "sales": "銷貨資料", 
                "inventory": "庫存資料"
            }
            type_name = type_names.get(current_data_type, "資料")
            
            # 特別處理銷貨資料 - 先檢查客戶
            if current_data_type == "sales":
                try:
                    # 只處理第一個檔案進行客戶檢查
                    file_info = current_files[0]
                    filename = file_info['filename']
                    contents = file_info['contents']
                    
                    # 檢查是否為 Excel 文件
                    if filename.lower().endswith(('.xlsx', '.xls')):
                        # 解碼 base64 內容
                        content_type, content_string = contents.split(',')
                        decoded_content = base64.b64decode(content_string)
                        
                        try:
                            # 準備檔案和表單資料上傳到客戶檢查 API
                            files = {
                                'file': (filename, decoded_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                            }
                            data = {
                                'user_role': user_role or 'viewer'
                            }
                            
                            # 呼叫客戶檢查 API
                            api_url = f"{API_BASE_URL}/import/sales/check-customers"
                            logger.info(f"正在檢查客戶: {filename}")
                            response = requests.post(api_url, files=files, data=data, timeout=300)
                            
                            logger.info(f"客戶檢查 API 回應狀態碼: {response.status_code}")
                            logger.info(f"客戶檢查 API 回應內容: {response.text}")
                            
                            if response.status_code == 200:
                                result = response.json()
                                logger.info(f"客戶檢查解析後的回應: {result}")
                                
                                if result.get('success'):
                                    missing_customers = result.get('missing_customers', [])
                                    
                                    if missing_customers:
                                        # 有缺失客戶，打開創建客戶 Modal
                                        logger.info(f"發現 {len(missing_customers)} 個缺失客戶: {missing_customers}")
                                        
                                        # 存儲缺失客戶和當前文件信息
                                        file_store_data = {
                                            'filename': filename,
                                            'contents': contents,
                                            'current_files': current_files
                                        }
                                        
                                        return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                                               False, "", False, "", False, "", missing_customers, file_store_data, True)
                                    else:
                                        # 沒有缺失客戶，直接繼續匯入流程
                                        logger.info("所有客戶都已存在，直接進行匯入")
                                        # 這裡直接呼叫原有的匯入邏輯
                                        return process_sales_import(current_files, session_data, user_role)
                                else:
                                    error_msg = result.get('message', '客戶檢查失敗')
                                    return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                                           False, "", True, error_msg, False, "", [], {}, False)
                            elif response.status_code == 403:
                                # 權限不足錯誤
                                return ("匯入上傳檔案", True, {"display": "none"}, session_data, 
                                       False, "", False, "", True, "權限不足：僅限編輯者使用此功能", [], {}, False)
                            else:
                                try:
                                    error_detail = response.json().get('detail', '未知錯誤')
                                except:
                                    error_detail = response.text if response.content else '服務器無回應'
                                error_msg = f"客戶檢查失敗 (狀態碼 {response.status_code}) - {error_detail}"
                                return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                                       False, "", True, error_msg, False, "", [], {}, False)
                            
                        except requests.exceptions.RequestException as e:
                            error_msg = f"網路錯誤 - {str(e)}"
                            return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                                   False, "", True, error_msg, False, "", [], {}, False)
                        except Exception as e:
                            error_msg = f"處理錯誤 - {str(e)}"
                            return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                                   False, "", True, error_msg, False, "", [], {}, False)
                    else:
                        error_msg = f"跳過非 Excel 檔案: {filename}"
                        return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                               False, "", True, error_msg, False, "", [], {}, False)
                
                except Exception as e:
                    error_message = f"處理銷貨資料時發生錯誤: {str(e)}"
                    return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                           False, "", True, error_message, False, "", [], {}, False)
            else:
                # 其他資料類型的一般處理
                success_message = f"成功匯入 {len(current_files)} 個{type_name}檔案"
                return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                       True, success_message, False, "", False, "", [], {}, False)
        else:
            # 沒有檔案，顯示錯誤 toast
            error_message = "沒有檔案可匯入，請先上傳檔案"
            return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
                   False, "", True, error_message, False, "", [], {}, False)
    else:
        # 沒有選擇資料類型，顯示錯誤 toast
        error_message = "請先選擇資料類型"
        return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
               False, "", True, error_message, False, "", [], {}, False)

# 新增：客戶創建 Modal 相關回調函數

# 客戶 Modal 顯示邏輯 - 設置當前客戶資訊
@app.callback(
    [Output("new-customer-modal-title", "children"),
     Output("new-customer-id", "value"),
     Output("new-customer-name", "value"),
     Output("new-customer-phone", "value"),
     Output("new-customer-address", "value"),
     Output("new-customer-delivery-schedule", "value"),
     Output("new-customer-notes", "value"),
     Output("skip-all-customers-btn", "style"),
     Output("finish-and-import-btn", "style")],
    [Input("missing-customers-store", "data"),
     Input("new-customer-modal", "is_open")],
    prevent_initial_call=True
)
def setup_customer_modal(missing_customers, is_open):
    if is_open and missing_customers:
        current_customer = missing_customers[0]
        total_customers = len(missing_customers)
        
        # 根據客戶數量決定是否顯示批量控制
        show_batch = total_customers > 1
        skip_all_style = {"display": "inline-block"} if show_batch else {"display": "none"}
        finish_style = {"display": "none"}  # 初始時隱藏完成按鈕
        
        title = f"創建新客戶 ({1}/{total_customers})" if show_batch else "創建新客戶"
        
        return (title, current_customer, "", "", "", [], "", 
               skip_all_style, finish_style)
    
    return ("創建新客戶", "", "", "", "", [], "", 
           {"display": "none"}, {"display": "none"})


# 根據選擇的縣市更新區域選項
@app.callback(
    [Output("new-customer-district", "options"),
     Output("new-customer-district", "value")],
    Input("new-customer-city", "value"),
    prevent_initial_call=True
)
def update_district_options(selected_city):
    if not selected_city:
        return [], None
    
    districts = CITY_DISTRICT_MAP.get(selected_city, [])
    district_options = [{"label": district, "value": district} for district in districts]
    
    return district_options, None

@app.callback(
    [Output("missing-customers-store", "data", allow_duplicate=True),
     Output("new-customer-modal", "is_open", allow_duplicate=True),
     Output("create_customer_import-success-toast", "is_open"),
     Output("create_customer_import-success-toast", "children"),
     Output("create_customer_import-error-toast", "is_open"),
     Output("create_customer_import-error-toast", "children")],
    [Input("save-new-customer-btn", "n_clicks")],
    [State("new-customer-id", "value"),
     State("new-customer-name", "value"),
     State("new-customer-phone", "value"),
     State("new-customer-address", "value"),
     State("new-customer-city", "value"), 
     State("new-customer-district", "value"),  
     State("new-customer-delivery-schedule", "value"),
     State("new-customer-notes", "value"),
     State("missing-customers-store", "data")],
    prevent_initial_call=True
)
def save_new_customer(n_clicks, customer_id, customer_name, phone, address, city, district, delivery_schedule, notes, missing_customers):
    if not n_clicks or not customer_id:
        return no_update, no_update, False, "", False, ""
    
    # 驗證必填欄位
    if not customer_name or not customer_name.strip():
        return no_update, no_update, False, "", True, "客戶名稱為必填欄位"
    
    # 準備客戶資料
    delivery_schedule_str = convert_delivery_schedule_to_numbers(delivery_schedule)
    
    customer_data = {
        "customer_id": customer_id.strip(),
        "customer_name": customer_name.strip(),
        "phone_number": phone.strip() if phone else "",
        "address": address.strip() if address else "",
        "city": city.strip() if city else "",  
        "district": district.strip() if district else "",  
        "delivery_schedule": delivery_schedule_str,
        "notes": notes.strip() if notes else "",
        "is_enabled": 1  # 新增預設值
    }
    
    try:
        # 呼叫創建客戶 API
        api_url = f"{API_BASE_URL}/customer/create"
        response = requests.post(api_url, json=customer_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                # 客戶創建成功，從缺失列表中移除
                updated_missing_customers = [cid for cid in missing_customers if cid != customer_id]
                
                if updated_missing_customers:
                    # 還有其他客戶需要創建，繼續顯示 Modal
                    success_msg = f"客戶 {customer_id} 創建成功！還剩 {len(updated_missing_customers)} 個客戶需要創建。"
                    return updated_missing_customers, True, True, success_msg, False, ""
                else:
                    # 所有客戶都已創建完成，關閉 Modal
                    success_msg = f"客戶 {customer_id} 創建成功！所有客戶已創建完成，請重新點擊匯入按鈕。"
                    return [], False, True, success_msg, False, ""
            else:
                error_msg = result.get('message', '創建客戶失敗')
                return no_update, no_update, False, "", True, error_msg
        else:
            try:
                error_detail = response.json().get('detail', '未知錯誤')
            except:
                error_detail = response.text if response.content else '服務器無回應'
            error_msg = f"創建客戶失敗 (狀態碼 {response.status_code}) - {error_detail}"
            return no_update, no_update, False, "", True, error_msg
        
    except requests.exceptions.RequestException as e:
        error_msg = f"網路錯誤 - {str(e)}"
        return no_update, no_update, False, "", True, error_msg
    except Exception as e:
        error_msg = f"處理錯誤 - {str(e)}"
        return no_update, no_update, False, "", True, error_msg

# 跳過當前客戶
@app.callback(
    [Output("missing-customers-store", "data", allow_duplicate=True),
     Output("new-customer-modal", "is_open", allow_duplicate=True),
     Output("create_customer_import-warning-toast", "is_open"),
     Output("create_customer_import-warning-toast", "children")],
    [Input("skip-customer-btn", "n_clicks")],
    [State("new-customer-id", "value"),
     State("missing-customers-store", "data")],
    prevent_initial_call=True
)
def skip_current_customer(n_clicks, customer_id, missing_customers):
    if not n_clicks or not customer_id:
        return no_update, no_update, False, ""
    
    # 從缺失列表中移除當前客戶
    updated_missing_customers = [cid for cid in missing_customers if cid != customer_id]
    
    if updated_missing_customers:
        # 還有其他客戶需要處理，繼續顯示 Modal
        warning_msg = f"已跳過客戶 {customer_id}，還剩 {len(updated_missing_customers)} 個客戶需要處理。"
        return updated_missing_customers, True, True, warning_msg
    else:
        # 所有客戶都已處理完成，關閉 Modal
        warning_msg = f"已跳過客戶 {customer_id}，所有客戶已處理完成。注意：跳過的客戶可能導致匯入失敗。"
        return [], False, True, warning_msg

# 跳過所有剩餘客戶
@app.callback(
    [Output("missing-customers-store", "data", allow_duplicate=True),
     Output("new-customer-modal", "is_open", allow_duplicate=True),
     Output("create_customer_import-warning-toast", "is_open", allow_duplicate=True),
     Output("create_customer_import-warning-toast", "children", allow_duplicate=True)],
    [Input("skip-all-customers-btn", "n_clicks")],
    [State("missing-customers-store", "data")],
    prevent_initial_call=True
)
def skip_all_customers(n_clicks, missing_customers):
    if not n_clicks:
        return no_update, no_update, False, ""
    
    skipped_count = len(missing_customers)
    warning_msg = f"已跳過所有 {skipped_count} 個客戶。注意：跳過的客戶可能導致匯入失敗。"
    
    return [], False, True, warning_msg

# 完成並匯入（當所有客戶都處理完成時）
@app.callback(
    [Output("save-current-files-btn", "children", allow_duplicate=True),
     Output("save-current-files-btn", "disabled", allow_duplicate=True),
     Output("fullscreen-overlay", "style", allow_duplicate=True),
     Output("import-session-store", "data", allow_duplicate=True),
     Output("import_data-success-toast", "is_open", allow_duplicate=True),
     Output("import_data-success-toast", "children", allow_duplicate=True),
     Output("import_data-error-toast", "is_open", allow_duplicate=True),
     Output("import_data-error-toast", "children", allow_duplicate=True),
     Output("new-customer-modal", "is_open", allow_duplicate=True)],
    [Input("finish-and-import-btn", "n_clicks")],
    [State("current-file-store", "data"),
     State("import-session-store", "data"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def finish_and_import(n_clicks, file_store_data, session_data, user_role):
    if not n_clicks or not file_store_data:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    # 獲取存儲的檔案資訊
    current_files = file_store_data.get('current_files', [])
    
    if current_files:
        # 執行銷貨資料匯入
        result = process_sales_import(current_files, session_data, user_role)
        # 關閉 Modal
        return result + (False,)
    else:
        error_msg = "未找到要匯入的檔案資訊"
        return ("匯入上傳檔案", False, {"display": "none"}, session_data, 
               False, "", True, error_msg, False)
    
