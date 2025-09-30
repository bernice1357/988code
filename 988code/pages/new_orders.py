'''
首頁 預設顯示customer_id+name，沒有就顯示line_id
confirmed_by:帳號名稱、confirmed_at:確認時間
datetime.now()取得當前時間
'''

from .common import *
from dash import ALL
from datetime import datetime

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

def get_missing_required_fields(field_pairs):
    missing_fields = []
    for label, value in field_pairs:
        if value is None:
            missing_fields.append(label)
        elif isinstance(value, str):
            if not value.strip():
                missing_fields.append(label)
        elif isinstance(value, (list, tuple, set)):
            if not value:
                missing_fields.append(label)
    return missing_fields


def build_required_field_warning(missing_fields):
    if not missing_fields:
        return ""
    return f"請填寫以下欄位：{'、'.join(missing_fields)}"

# 生成隨機客戶ID的函數
def generate_customer_id():
    import random
    import string
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

# 檢查客戶是否存在於customer表的函數
def check_customer_exists(customer_id):
    try:
        response = requests.get(f"http://127.0.0.1:8000/check_customer_exists/{customer_id}")
        if response.status_code == 200:
            data = response.json()
            return data.get("exists", False)
        return False
    except:
        return False

# 載入訂單資料的函數
def get_orders():
    response = requests.get("http://127.0.0.1:8000/get_new_orders")
    if response.status_code == 200:
        try:
            orders = response.json()
            # 過濾掉超過一天的已確認和已刪除訂單
            filtered_orders = []
            current_time = datetime.now()
            
            for order in orders:
                status = order.get("status")
                
                # 如果是未確認狀態，直接保留
                if status == "0":
                    filtered_orders.append(order)
                # 如果是已確認或已刪除狀態，檢查時間
                elif status in ["1", "2"]:
                    # 確定要檢查的時間欄位
                    if status == "1":
                        # 已確認訂單檢查確認時間
                        time_field = order.get("confirmed_at")
                    else:
                        # 已刪除訂單檢查更新時間（刪除時間）
                        time_field = order.get("updated_at")
                    
                    if time_field:
                        try:
                            # 處理時間格式
                            if 'Z' in time_field:
                                processed_time = datetime.fromisoformat(time_field.replace('Z', '+00:00'))
                            else:
                                processed_time = datetime.fromisoformat(time_field)
                            
                            # 如果時間在一天內，保留
                            if (current_time - processed_time).days < 1:
                                filtered_orders.append(order)
                        except:
                            # 如果時間解析失敗，保留訂單
                            filtered_orders.append(order)
                    else:
                        # 如果沒有時間記錄，保留訂單
                        filtered_orders.append(order)
                else:
                    # 其他狀態直接保留
                    filtered_orders.append(order)
            
            # 批量獲取客戶備註
            customer_ids = set()
            for order in filtered_orders:
                if order.get("customer_id"):
                    customer_ids.add(order["customer_id"])

            # 如果有需要查詢的客戶ID，批量查詢備註
            notes_dict = {}
            if customer_ids:
                try:
                    notes_response = requests.post(
                        "http://127.0.0.1:8000/get_customer_notes_batch",
                        json={"customer_ids": list(customer_ids)}
                    )
                    if notes_response.status_code == 200:
                        notes_dict = notes_response.json()
                        print(f"[get_orders] 批量取得 {len(notes_dict)} 筆客戶備註")
                except Exception as e:
                    print(f"[get_orders] 批量取得備註失敗: {e}")

            # 將備註附加到每個訂單
            for order in filtered_orders:
                customer_id = order.get("customer_id")
                order["customer_notes"] = notes_dict.get(customer_id, "")

            return filtered_orders
        except requests.exceptions.JSONDecodeError:
            print("回應內容不是有效的 JSON")
            return []
    else:
        print(f"API 錯誤，狀態碼：{response.status_code}")
        return []

    
<<<<<<< HEAD
def make_card_item(order, user_role=None):
    # 獲取客戶備註
    customer_notes = ""
    if order.get("customer_id"):
        try:
            notes_response = requests.get(f"http://127.0.0.1:8000/get_customer_notes/{order['customer_id']}")
            if notes_response.status_code == 200:
                notes_data = notes_response.json()
                customer_notes = notes_data.get("notes", "")
        except:
            customer_notes = ""
    
=======
def make_card_item(order):
    # 直接從 order 中讀取備註（已經在 get_orders 時附加）
    customer_notes = order.get("customer_notes", "")

>>>>>>> 773f26ea1490c3e5062f1476b3ff44a83e5f3029
    # 客戶標題已移至群組標題，這裡不再需要
    status = str(order.get("status", ""))
    base_time = order.get("created_at")
    timestamp_label = "建立時間"
    timestamp_value = base_time

    if status == "1":
        timestamp_label = "已確定時間"
        timestamp_value = order.get("confirmed_at") or order.get("updated_at") or base_time
    elif status == "2":
        timestamp_label = "已刪除時間"
        timestamp_value = order.get("deleted_at") or order.get("updated_at") or base_time

    if timestamp_value:
        timestamp_display = str(timestamp_value)[:16].replace("T", " ")
    else:
        timestamp_display = "N/A"

    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                dbc.Badge("新品提醒", color="danger", className="me-2 rounded-pill", style={"fontSize": "0.7rem", "padding": "4px 8px"}) if order.get("is_new_product") == "true" or order.get("is_new_product") == True else None,
                # 顯示標籤
                dbc.Badge({
                    "ORDER": "訂單",
                    "INQUIRY": "問題", 
                    "MIXED": "混合",
                    "OTHER": "其他"
                }.get(order.get("label"), order.get("label", "")), 
                color={
                    "ORDER": "info",
                    "INQUIRY": "warning", 
                    "MIXED": "success",
                    "OTHER": "secondary"
                }.get(order.get("label"), "info"), className="ms-2 rounded-pill", 
                style={"fontSize": "0.7rem", "padding": "4px 8px"}) if order.get("label") else None
            ], style={"lineHeight": "1"})
        ], style={"overflow": "hidden", "padding": "8px 12px"}),
        dbc.CardBody([
            # 對話紀錄區塊
            html.Div([
                html.Small("對話紀錄", className="text-info mb-1 d-block"),
                html.Pre(order["conversation_record"], style={"whiteSpace": "pre-wrap", "fontSize": "0.9rem"})
            ], className="mb-3"),
            html.Div(style={"borderTop": "1px solid #dee2e6", "margin": "15px 0"}),
            # 購買紀錄區塊
            html.Div([
                html.Small("上次購買品項", className="text-info mb-1 d-block"),
                html.Div([
                    html.Span(order.get('product_id', ''), style={"color": "black", "fontWeight": "bold", "fontSize": "0.9rem"}) if order.get('product_id') else None,
                    html.Span(" ", style={"fontSize": "0.9rem"}) if order.get('product_id') else None,
                    html.Span(order['purchase_record'], style={"fontSize": "0.9rem", "whiteSpace": "pre-wrap", "color": "black"})  # 修改這裡：新增 color: black
                ], style={"whiteSpace": "pre-wrap", "color": "black"}),  # 修改這裡：新增 color: black
                # 新增數量、單價、金額資訊
                html.Div([
                    html.Div([
                        html.Span("數量: ", style={"color": "black", "fontSize": "0.8rem"}),  # 修改這裡：改為 color: black
                        html.Span(f"{order.get('quantity', 'N/A')}", style={"fontSize": "0.8rem", "fontWeight": "bold", "color": "black"})  # 修改這裡：改為 color: black
                    ], style={"marginRight": "15px", "display": "inline-block"}) if order.get('quantity') is not None else None,
                    html.Div([
                        html.Span("單價: ", style={"color": "black", "fontSize": "0.8rem"}),  # 修改這裡：改為 color: black
                        html.Span(f"NT$ {order.get('unit_price', 'N/A')}", style={"fontSize": "0.8rem", "fontWeight": "bold", "color": "black"})  # 修改這裡：改為 color: black
                    ], style={"marginRight": "15px", "display": "inline-block"}) if order.get('unit_price') is not None else None,
                    html.Div([
                        html.Span("總金額: ", style={"color": "black", "fontSize": "0.8rem"}),  # 修改這裡：改為 color: black
                        html.Span(f"NT$ {order.get('amount', 'N/A')}", style={"fontSize": "0.8rem", "fontWeight": "bold", "color": "black"})  # 修改這裡：改為 color: black
                    ], style={"display": "inline-block"}) if order.get('amount') is not None else None
                ], style={"marginTop": "8px"}) if any(order.get(field) is not None for field in ['quantity', 'unit_price', 'amount']) else None
            ], className="mb-3"),
            html.Div(style={"borderTop": "1px solid #dee2e6", "margin": "15px 0"}),
            # Order Notes 區塊
            html.Div([
                html.Small("訊息備註", className="text-info mb-1 d-block"),
                html.Pre(order.get("order_note", ""), style={"whiteSpace": "pre-wrap", "fontSize": "0.9rem", "color": "#000000"})
            ], className="mb-3"),
            html.Div(style={"borderTop": "1px solid #dee2e6", "margin": "15px 0"}),
            # 歷史備註區塊
            html.Div([
                html.Small("歷史備註", className="text-info mb-1 d-block"),
                html.Pre(customer_notes, style={"whiteSpace": "pre-wrap", "fontSize": "0.9rem", "color": "#000000"})
            ], className="mb-3"),
            html.Div(style={"margin": "20px 0"}),
            # 建立時間
            html.Div([
                html.Div([
                    dbc.Button("確定", id={"type": "confirm-btn", "index": order['id']}, size="sm", color="dark", outline=True, className="me-2") if order.get("status") == "0" and user_role != "viewer" else None,
                    dbc.Button("刪除", id={"type": "delete-btn", "index": order['id']}, size="sm", color="danger", outline=True) if order.get("status") == "0" and user_role != "viewer" else None
                ]) if order.get("status") == "0" else html.Div(),
                html.Div([
                    html.Small(f"{timestamp_label}: {timestamp_display}", className="text-muted", style={"fontSize": "0.7rem"}),
                    # 顯示確認者資訊（僅在已確認狀態時顯示）
                    html.Small(f"確認者: {order.get('confirmed_by', '')}", className="text-muted", style={"fontSize": "0.7rem", "display": "block", "marginTop": "2px"}) if status == "1" and order.get('confirmed_by') else None
                ])
            ], className="d-flex justify-content-between align-items-center mt-2")
        ])
    ], style={"backgroundColor": "#f8f9fa", "border": "1px solid #dee2e6", "position": "relative", "marginTop": "15px"}, className="mb-3")

def get_modal_fields(customer_id, customer_name, purchase_record, product_id=None, quantity=None, unit_price=None, amount=None):
    # 獲取客戶備註
    customer_notes = ""
    if customer_id:
        try:
            notes_response = requests.get(f"http://127.0.0.1:8000/get_customer_notes/{customer_id}")
            if notes_response.status_code == 200:
                notes_data = notes_response.json()
                customer_notes = notes_data.get("notes", "")
        except:
            customer_notes = ""
    # 改為左右兩排佈局
    return dbc.Form([
        dbc.Row([
            # 左欄：客戶ID 和 客戶名稱
            dbc.Col([
                html.Div([
                    dbc.Label([
                        "客戶 ID ", 
                        html.Span("*", style={"color": "red"})
                    ], html_for="customer-id", className="form-label", style={"fontSize": "14px"}),
                    dbc.Input(
                        id="customer-id", 
                        type="text",
                        value=customer_id if customer_id else "",
                        disabled=bool(customer_id),  # 有customer_id就禁用編輯
                        style={"width": "100%"}
                    )
                ], className="mb-3"),
                html.Div([
                    dbc.Label([
                        "客戶名稱 ", 
                        html.Span("*", style={"color": "red"})
                    ], html_for="customer-name", className="form-label", style={"fontSize": "14px"}),
                    dbc.Input(
                        id="customer-name", 
                        type="text",
                        value=customer_name if customer_name else "",
                        disabled=bool(customer_id),  # 有customer_id就禁用編輯
                        style={"width": "100%"}
                    )
                ], className="mb-3"),
                html.Div([
                    dbc.Label("歷史備註", html_for="customer-notes", className="form-label", style={"fontSize": "14px"}),
                    dbc.Textarea(
                        id="customer-notes",
                        value=customer_notes,
                        rows=4,
                        placeholder="請輸入客戶備註...",
                        style={"width": "100%"}
                    )
                ], className="mb-3")
            ], width=6),
            
            # 右欄：其他欄位
            dbc.Col([
                html.Div([
                    dbc.Label([
                        "產品 ID ", 
                        html.Span("*", style={"color": "red"})
                    ], html_for="product-id", className="form-label", style={"fontSize": "14px"}),
                    dbc.Input(
                        id="product-id", 
                        type="text",
                        value=product_id if product_id else "",
                        style={"width": "100%"}
                    )
                ], className="mb-3"),
                html.Div([
                    dbc.Label([
                        "購買品項 ", 
                        html.Span("*", style={"color": "red"})
                    ], html_for="purchase-record", className="form-label", style={"fontSize": "14px"}),
                    dbc.Input(id="purchase-record", value=purchase_record, style={"width": "100%"})
                ], className="mb-3"),
                html.Div([
                    dbc.Label([
                        "數量 ", 
                        html.Span("*", style={"color": "red"})
                    ], html_for="quantity", className="form-label", style={"fontSize": "14px"}),
                    dbc.Input(
                        id="quantity", 
                        type="number",
                        value=quantity if quantity else "",
                        min=0,
                        step=1,
                        style={"width": "100%"}
                    )
                ], className="mb-3"),
                html.Div([
                    dbc.Label([
                        "單價 ", 
                        html.Span("*", style={"color": "red"})
                    ], html_for="unit-price", className="form-label", style={"fontSize": "14px"}),
                    dbc.Input(
                        id="unit-price", 
                        type="number",
                        value=unit_price if unit_price else "",
                        min=0,
                        step=0.01,
                        style={"width": "100%"}
                    )
                ], className="mb-3"),
                html.Div([
                    dbc.Label([
                        "金額 ", 
                        html.Span("*", style={"color": "red"})
                    ], html_for="amount", className="form-label", style={"fontSize": "14px"}),
                    dbc.Input(
                        id="amount", 
                        type="number",
                        value=amount if amount else "",
                        min=0,
                        step=0.01,
                        style={"width": "100%"}
                    )
                ], className="mb-3")
            ], width=6)
        ])
    ])

def group_orders_by_customer(orders):
    """按客戶名稱分組訂單"""
    grouped = {}
    for order in orders:
        # 優先使用 customer_name，沒有的話用 line_id，都沒有就歸為未知客戶
        if order.get("customer_name"):
            customer_key = order["customer_name"]
        elif order.get("line_id"):
            customer_key = f"Line用戶: {order['line_id']}"
        else:
            customer_key = "未知客戶"
        
        if customer_key not in grouped:
            grouped[customer_key] = []
        grouped[customer_key].append(order)
    
    return grouped

def make_customer_group(customer_key, orders, group_index, user_role=None):
    """創建客戶群組Accordion"""
    order_count = len(orders)
    
    # 創建包含 badge 的標題
    title_content = html.Div([
        html.Span(customer_key, style={"marginRight": "10px"}),
        dbc.Badge(str(order_count), color="primary", pill=True)
    ], className="d-flex align-items-center")
    
    return dbc.AccordionItem([
        dbc.Row([
            dbc.Col(make_card_item(order, user_role), width=12, lg=6, xl=4)
            for order in orders
        ], className="g-3")
    ],
    title=title_content,
    item_id=f"customer-group-{group_index}"
    )

def create_grouped_orders_layout(orders, user_role=None):
    """創建分組後的訂單layout"""
    if not orders:
        return html.Div("暫無訂單", className="text-center text-muted", style={"padding": "50px"})
    
    grouped_orders = group_orders_by_customer(orders)
    customer_groups = []
    
    for group_index, (customer_key, customer_orders) in enumerate(grouped_orders.items()):
        customer_groups.append(make_customer_group(customer_key, customer_orders, group_index, user_role))
    
    return dbc.Accordion(customer_groups, flush=True, always_open=False)

# 嘗試載入訂單資料，如果失敗則使用空列表
try:
    orders = get_orders()
except Exception as e:
    print(f"初始化載入訂單資料失敗: {e}")
    orders = []

layout = dbc.Container([
    success_toast("new_orders", message="訂單已確認"),
    error_toast("new_orders", message=""),
    warning_toast("new_orders", message=""),
    dcc.Store(id='user-role-store'),
    dcc.Store(id='current-order-id-store'),
    # 添加用於儲存上次檢查時間的 Store
    dcc.Store(id='last-update-check-time'),
    # 定時檢查是否有新訂單，每5秒檢查一次
    dcc.Interval(
        id='order-update-checker',
        interval=5*1000,  # 5秒檢查一次
        n_intervals=0
    ),
    html.Div([
        # 左側：新增訂單按鈕
        html.Div([
        dbc.Button(
            ["新增訂單"],
            id="add-new-order-btn",
            color="success",
            outline=True,
            size="sm",
            style={"fontWeight": "500", "fontSize": "16px", "marginRight": "15px"}
        ),
        dbc.Input(
            id="customer-search-input",
            placeholder="搜尋客戶名稱...",
            type="text",
            size="sm",
            style={"width": "250px", "display": "inline-block"}
        )
    ], style={"display": "flex", "alignItems": "center"}),

        # 右側：篩選按鈕群組
        dbc.ButtonGroup([
            dbc.Button("全部", id="filter-all", color="primary", outline=False),
            dbc.Button("未確認", id="filter-unconfirmed", color="primary", outline=True),
            dbc.Button("已確認", id="filter-confirmed", color="primary", outline=True),
            dbc.Button("已刪除", id="filter-deleted", color="primary", outline=True)
        ])
    ], className="d-flex justify-content-between align-items-center mb-4"),

    dcc.Loading(
        id="loading-orders",
        type="dot",
        children=html.Div(id="orders-container", children=create_grouped_orders_layout(orders), style={
            "maxHeight": "75vh", 
            "overflowY": "auto",
            "overflowX": "hidden"
        }),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "minHeight": "60vh"
        }
    ),
    dbc.Modal([
        dbc.ModalHeader("確認訂單", id="modal-header", style={"fontWeight": "bold", "fontSize": "24px"}),
        dbc.ModalBody(id="modal-body-content"),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-modal", color="secondary", outline=True),
            dbc.Button("確認", id="submit-confirm", color="primary")
        ])
    ], id="confirm-modal", is_open=False, size="xl", centered=True, style={"fontSize": "18px"}),
    dbc.Modal([
        dbc.ModalHeader("確認刪除", style={"fontWeight": "bold", "fontSize": "24px"}),
        dbc.ModalBody(id="delete-modal-body", children="確定要刪除這筆訂單嗎？"),
        dbc.ModalFooter([
            dbc.Button("取消", id="cancel-delete", color="secondary", outline=True),
            dbc.Button("刪除", id="submit-delete", color="danger")
        ])
    ], id="delete-modal", is_open=False),

    # **新增訂單 Modal - 在這裡添加**
    dbc.Modal([
        dbc.ModalHeader("新增訂單", style={"fontWeight": "bold", "fontSize": "24px"}),
        dbc.ModalBody([
            get_modal_fields("", "", "", None, None, None, None)
        ]),
        dbc.ModalFooter([
        html.Div([
            html.Small("* 必填欄位", className="text-danger", style={"fontSize": "12px"}),
        ], className="flex-grow-1"),
        dbc.Button("取消", id="cancel-add-order", color="secondary", outline=True),
        dbc.Button("新增", id="submit-add-order", color="success")
    ], className="d-flex align-items-center")
    ], id="add-order-modal", is_open=False, size="xl", centered=True, style={"fontSize": "18px"}),

    # 新增客戶創建 Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("創建新客戶", id="create-customer-modal-title")
        ]),
        dbc.ModalBody([
            dbc.Row([
                # 左側欄位
                dbc.Col([
                    # 客戶ID
                    dbc.Row([
                        dbc.Label([
                            "客戶ID ", 
                            html.Span("*", style={"color": "red"})
                        ], width=4),
                        dbc.Col(dbc.Input(id="new-customer-id", type="text", placeholder="請輸入客戶ID"), width=8)
                    ], className="mb-3"),
                    # 客戶名稱
                    dbc.Row([
                        dbc.Label([
                            "客戶名稱 ", 
                            html.Span("*", style={"color": "red"})
                        ], width=4),
                        dbc.Col(dbc.Input(id="new-customer-name", type="text", placeholder="請輸入客戶名稱"), width=8)
                    ], className="mb-3"),
                    # 電話號碼
                    dbc.Row([
                        dbc.Label([
                            "電話號碼 ", 
                            html.Span("*", style={"color": "red"})
                        ], width=4),
                        dbc.Col(dbc.Input(id="new-customer-phone", type="text", placeholder="請輸入電話號碼"), width=8)
                    ], className="mb-3"),
                    # 客戶地址
                    dbc.Row([
                        dbc.Label([
                            "客戶地址 ", 
                            html.Span("*", style={"color": "red"})
                        ], width=4),
                        dbc.Col(dbc.Input(id="new-customer-address", type="text", placeholder="請輸入客戶地址"), width=8)
                    ], className="mb-3"),
                ], width=6),
                
                # 右側欄位
                dbc.Col([
                    # 直轄市、縣、市
                    dbc.Row([
                        dbc.Label([
                            "直轄市、縣、市 ", 
                            html.Span("*", style={"color": "red"})
                        ], width=4),
                        dbc.Col(dcc.Dropdown(
                            id="new-customer-city",
                            options=[{"label": city, "value": city} for city in CITY_DISTRICT_MAP.keys()],
                            placeholder="請選擇直轄市縣市"
                        ), width=8)
                    ], className="mb-3"),
                    # 鄉鎮市區
                    dbc.Row([
                        dbc.Label([
                            "鄉鎮市區 ", 
                            html.Span("*", style={"color": "red"})
                        ], width=4),
                        dbc.Col(dcc.Dropdown(
                            id="new-customer-district",
                            options=[],
                            placeholder="請先選擇直轄市縣市"
                        ), width=8)
                    ], className="mb-3"),
                ], width=6)
            ]),
            
            dbc.Row([
                dbc.Label("備註", width=2),
                dbc.Col(dbc.Textarea(id="new-customer-notes", rows=3, placeholder="請輸入備註"), width=10)
            ], className="mb-3"),
            # 每週配送日放在底部，橫跨整個寬度
            dbc.Row([
                dbc.Label([
                    "每週配送日 ", 
                    html.Span("*", style={"color": "red"})
                ], width=2),
                dbc.Col(dcc.Checklist(
                    id="new-customer-delivery-schedule",
                    options=[
                        {"label": "一", "value": "1"},
                        {"label": "二", "value": "2"},
                        {"label": "三", "value": "3"},
                        {"label": "四", "value": "4"},
                        {"label": "五", "value": "5"},
                        {"label": "六", "value": "6"},
                        {"label": "日", "value": "7"}
                    ],
                    value=[],
                    inline=True,
                    style={"display": "flex", "gap": "15px"}
                ), width=10)
            ], className="mb-3"),
        ]),
        dbc.ModalFooter([
        html.Div([
            html.Small("* 必填欄位", className="text-danger", style={"fontSize": "12px"}),
        ], className="flex-grow-1"),
        dbc.Button("跳過此客戶", id="skip-customer-btn", color="secondary", className="me-2"),
        dbc.Button("儲存客戶", id="save-new-customer-btn", color="primary"),
    ], className="d-flex align-items-center")
    ], id="create-customer-modal", is_open=False, backdrop="static", keyboard=False, size="xl"),
    
    # 儲存需要創建客戶的訂單資料
    dcc.Store(id="pending-order-store"),
    dcc.Store(id="current-processing-order"),
], fluid=True)


# 篩選顯示訂單和更新按鈕狀態
@app.callback(
    [Output("orders-container", "children", allow_duplicate=True),
     Output("filter-all", "outline", allow_duplicate=True),
     Output("filter-unconfirmed", "outline", allow_duplicate=True),
     Output("filter-confirmed", "outline", allow_duplicate=True),
     Output("filter-deleted", "outline", allow_duplicate=True),
     Output("customer-search-input", "value", allow_duplicate=True)],  # 新增這行
    [Input("filter-all", "n_clicks"),
     Input("filter-unconfirmed", "n_clicks"),
     Input("filter-confirmed", "n_clicks"),
     Input("filter-deleted", "n_clicks")],
    State("user-role-store", "data"),
    prevent_initial_call=True
)
def filter_orders(all_clicks, unconfirmed_clicks, confirmed_clicks, deleted_clicks, user_role):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered[0]["prop_id"].split('.')[0]
    orders = get_orders()
    
    if triggered_id == "filter-all":
        filtered_orders = orders
        return create_grouped_orders_layout(filtered_orders, user_role), False, True, True, True, ""  # 清空搜尋框
    elif triggered_id == "filter-unconfirmed":
        filtered_orders = [order for order in orders if order.get("status") == "0"]
        return create_grouped_orders_layout(filtered_orders, user_role), True, False, True, True, ""  # 清空搜尋框
    elif triggered_id == "filter-confirmed":
        filtered_orders = [order for order in orders if order.get("status") == "1"]
        return create_grouped_orders_layout(filtered_orders, user_role), True, True, False, True, ""  # 清空搜尋框
    elif triggered_id == "filter-deleted":
        filtered_orders = [order for order in orders if order.get("status") == "2"]
        return create_grouped_orders_layout(filtered_orders, user_role), True, True, True, False, ""  # 清空搜尋框
    else:
        filtered_orders = orders
        return create_grouped_orders_layout(filtered_orders, user_role), False, True, True, True, ""  # 清空搜尋框

# 刪除按鈕，顯示確認刪除modal
@app.callback(
    [Output("delete-modal", "is_open", allow_duplicate=True),
     Output("delete-modal-body", "children", allow_duplicate=True)],
    [Input({"type": "delete-btn", "index": ALL}, "n_clicks")],
    [State("delete-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_delete_modal(n_clicks_list, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    triggered_prop = ctx.triggered[0]["prop_id"]
    if not triggered_prop or "delete-btn" not in triggered_prop:
        return dash.no_update, dash.no_update
    
    triggered_value = ctx.triggered[0]["value"]
    if not triggered_value or triggered_value == 0:
        return dash.no_update, dash.no_update
    
    import json
    try:
        button_id = json.loads(triggered_prop.split('.')[0])
        order_id = button_id["index"]
    except:
        return dash.no_update, dash.no_update
    
    orders = get_orders()
    order = next((o for o in orders if str(o["id"]) == str(order_id)), None)
    if order:
        # 修正：使用與 confirm_delete 相同的邏輯
        if order.get("customer_id") and order.get("customer_name"):
            customer_info = order['customer_id'] + order['customer_name']
        elif order.get("line_id"):
            customer_info = order['line_id']
        else:
            customer_info = "未知客戶"
        
        message = f"確定要刪除訂單：{customer_info} 嗎？"
        return True, message
    
    return dash.no_update, dash.no_update

# 取消刪除
@app.callback(
    Output("delete-modal", "is_open", allow_duplicate=True),
    Input("cancel-delete", "n_clicks"),
    prevent_initial_call=True
)
def close_delete_modal(n_clicks):
    if n_clicks:
        return False
    return dash.no_update

# 確認刪除
@app.callback(
    [Output("delete-modal", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "children", allow_duplicate=True),
     Output("new_orders-error-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "children", allow_duplicate=True),
     Output("orders-container", "children", allow_duplicate=True)],
    [Input("submit-delete", "n_clicks")],
    [State("delete-modal-body", "children"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def confirm_delete(n_clicks, modal_body, user_role):
    if n_clicks:
        print(f"收到刪除確認，modal_body: {modal_body}")  # 添加調試
        orders = get_orders()
        order_id = None
        for order in orders:
            # 使用與 toggle_delete_modal 相同的邏輯
            if order.get("customer_id") and order.get("customer_name"):
                customer_info = order['customer_id'] + order['customer_name']
            elif order.get("line_id"):
                customer_info = order['line_id']
            else:
                customer_info = "未知客戶"
            
            expected_message = f"確定要刪除訂單：{customer_info} 嗎？"
            print(f"檢查訂單ID {order['id']}: expected='{expected_message}', actual='{modal_body}'")  # 添加調試
            
            if modal_body == expected_message:
                order_id = order["id"]
                print(f"找到匹配的訂單ID: {order_id}")  # 添加調試
                break
        
        if order_id:
            print(f"準備刪除訂單ID: {order_id}")
            current_time = datetime.now().isoformat()
            
            # 準備更新資料，只更新status為2
            update_data = {
                "status": "2",
                "updated_at": current_time,
                "deleted_at": current_time
            }
            
            print(f"更新數據: {update_data}")
            
            # 呼叫API更新資料
            try:
                update_data["user_role"] = user_role or "viewer"
                response = requests.put(f"http://127.0.0.1:8000/temp/{order_id}", json=update_data)
                print(f"API回應狀態碼: {response.status_code}")
                print(f"API回應內容: {response.text}")
                
                if response.status_code == 200:
                    print("訂單刪除成功")
                    orders = get_orders()
                    updated_orders = create_grouped_orders_layout(orders, user_role)
                    return False, True, "訂單已刪除，請查看已刪除頁面", False, False, "", updated_orders
                elif response.status_code == 403:
                    return False, False, "", False, True, "權限不足：僅限編輯者使用此功能", dash.no_update
                else:
                    print(f"API 錯誤，狀態碼：{response.status_code}")
                    return False, False, dash.no_update, True, False, "", dash.no_update
            except Exception as e:
                print(f"API 呼叫失敗：{e}")
                return False, False, dash.no_update, True, False, "", dash.no_update
        else:
            print("未找到匹配的訂單ID")
            return False, False, dash.no_update, True, False, "", dash.no_update
            
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output("confirm-modal", "is_open", allow_duplicate=True),
     Output("modal-body-content", "children", allow_duplicate=True),
     Output("modal-header", "children", allow_duplicate=True),
     Output("current-order-id-store", "data", allow_duplicate=True)],
    [Input({"type": "confirm-btn", "index": ALL}, "n_clicks")],
    [State("confirm-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_modal(n_clicks_list, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update  # 新增一個 no_update

    # 檢查是否真的是confirm-btn被點擊
    triggered_prop = ctx.triggered[0]["prop_id"]
    if not triggered_prop or "confirm-btn" not in triggered_prop:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update  # 新增一個 no_update

    # 檢查點擊值是否存在且大於0
    triggered_value = ctx.triggered[0]["value"]
    if not triggered_value or triggered_value == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update  # 新增一個 no_update

    # 解析 order_id
    import json
    try:
        button_id = json.loads(triggered_prop.split('.')[0])
        order_id = button_id["index"]
    except:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update  # 新增一個 no_update

    orders = get_orders()
    # 根據 order_id 找到對應的訂單資料
    order = next((o for o in orders if str(o["id"]) == str(order_id)), None)
    if order:
        # 傳入所有需要的欄位
        modal_content = get_modal_fields(
            order.get("customer_id"), 
            order.get("customer_name"), 
            order["purchase_record"],
            order.get("product_id"),
            order.get("quantity"),
            order.get("unit_price"),
            order.get("amount")
        )
        # 設定標題
        title = "確認訂單"
        return True, modal_content, title, order_id  # 新增 order_id
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update  # 新增一個 no_update
    
    orders = get_orders()
    # 根據 order_id 找到對應的訂單資料
    order = next((o for o in orders if str(o["id"]) == str(order_id)), None)
    if order:
        # 傳入所有需要的欄位
        modal_content = get_modal_fields(
            order.get("customer_id"), 
            order.get("customer_name"), 
            order["purchase_record"],
            order.get("product_id"),
            order.get("quantity"),
            order.get("unit_price"),
            order.get("amount")
        )
        # 設定標題
        title = "確認訂單"
        return True, modal_content, title
    
    return dash.no_update, dash.no_update, dash.no_update

# 訂單取消處理按鈕
@app.callback(
    [Output("confirm-modal", "is_open", allow_duplicate=True),
     Output("create-customer-modal", "is_open", allow_duplicate=True),
     Output("pending-order-store", "data", allow_duplicate=True),
     Output("current-processing-order", "data", allow_duplicate=True)],
    Input("cancel-modal", "n_clicks"),
    [State("customer-id", "value"),
     State("customer-name", "value"),
     State("customer-notes", "value"),
     State("product-id", "value"),
     State("purchase-record", "value"),
     State("quantity", "value"),
     State("unit-price", "value"),
     State("amount", "value"),
     State("modal-header", "children"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)

def close_modal(n_clicks, customer_id, customer_name, customer_notes, product_id, purchase_record, quantity, unit_price, amount, modal_header, user_role):
    if n_clicks:
        # 直接關閉確認modal，不執行任何其他操作
        return False, False, dash.no_update, dash.no_update
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

# modal確認送出
@app.callback(
    [Output("confirm-modal", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "children", allow_duplicate=True),
     Output("new_orders-error-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "children", allow_duplicate=True),
     Output("orders-container", "children", allow_duplicate=True),
     Output("create-customer-modal", "is_open", allow_duplicate=True),  
     Output("pending-order-store", "data", allow_duplicate=True),   
     Output("current-processing-order", "data", allow_duplicate=True)],
    [Input("submit-confirm", "n_clicks")],
    [State("customer-id", "value"),
     State("customer-name", "value"),
     State("customer-notes", "value"),
     State("product-id", "value"),
     State("purchase-record", "value"),
     State("quantity", "value"),
     State("unit-price", "value"),
     State("amount", "value"),
     State("modal-header", "children"),
     State("current-order-id-store", "data"),
     State("user-role-store", "data"),
     State("login_status", "data")],
    prevent_initial_call=True
)
def submit_confirm(n_clicks, customer_id, customer_name, customer_notes, product_id, purchase_record, quantity, unit_price, amount, modal_header, current_order_id, user_role, login_status):
    if n_clicks:
        # 取得確認者名稱
        confirmed_by_user = "user"  # 預設值
        if login_status and isinstance(login_status, dict):
            # 從 login_status 中取得 full_name
            confirmed_by_user = login_status.get("full_name") or "user"
        required_fields = [
            ("客戶 ID", customer_id),
            ("客戶名稱", customer_name),
            ("產品 ID", product_id),
            ("購買品項", purchase_record),
            ("數量", quantity),
            ("單價", unit_price),
            ("金額", amount),
        ]
        missing_fields = get_missing_required_fields(required_fields)
        if missing_fields:
            warning_message = build_required_field_warning(missing_fields)
            return dash.no_update, False, dash.no_update, False, True, warning_message, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        orders = get_orders()
        order_id = current_order_id
        original_order = None

        if order_id:
            original_order = next((o for o in orders if str(o["id"]) == str(order_id)), None)
        if order_id and original_order:
            # 如果有customer_id且存在，更新客戶備註
            if customer_id and check_customer_exists(customer_id):
                try:
                    # 更新客戶備註
                    notes_update_data = {
                        "notes": customer_notes,
                        "user_role": user_role
                    }
                    notes_response = requests.put(f"http://127.0.0.1:8000/customer/{customer_id}", json=notes_update_data)
                    if notes_response.status_code != 200:
                        print(f"客戶備註更新失敗，狀態碼：{notes_response.status_code}")
                except Exception as e:
                    print(f"客戶備註更新異常：{str(e)}")
            
            # 檢查客戶是否存在於customer表中
            if customer_id:
                if not check_customer_exists(customer_id):
                    # 客戶不存在，需要創建新客戶
                    pending_order_data = {
                        "order_id": order_id,
                        "original_order": original_order,
                        "customer_id": customer_id,
                        "customer_name": customer_name,
                        "customer_notes": customer_notes,  # 新增這一行
                        "product_id": product_id,
                        "purchase_record": purchase_record,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "amount": amount,
                        "user_role": user_role,
                        "line_id": original_order.get("line_id")
                    }
                    return False, False, dash.no_update, False, False, dash.no_update, dash.no_update, True, pending_order_data, {"customer_id": customer_id, "customer_name": customer_name}
            else:
                # 如果沒有 customer_id，也需要創建新客戶
                pending_order_data = {
                    "order_id": order_id,
                    "original_order": original_order,
                    "customer_id": customer_id or "",
                    "customer_name": customer_name,
                    "customer_notes": customer_notes,  # 新增這一行
                    "product_id": product_id,
                    "purchase_record": purchase_record,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "amount": amount,
                    "user_role": user_role,
                    "line_id": original_order.get("line_id")
                }
                return False, False, dash.no_update, False, False, dash.no_update, dash.no_update, True, pending_order_data, {"customer_id": customer_id or "", "customer_name": customer_name}
            
            # 如果程式執行到這裡，表示客戶已存在，可以直接更新訂單
            current_time = datetime.now().isoformat()
            update_data = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "product_id": product_id,
                "purchase_record": purchase_record,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
                "updated_at": current_time,
                "status": "1",
                "confirmed_by": confirmed_by_user,
                "confirmed_at": current_time,
                "user_role": user_role
            }
            
            # 呼叫API更新資料
            try:
                response = requests.put(f"http://127.0.0.1:8000/temp/{order_id}", json=update_data)
                if response.status_code == 200:
                    print("訂單確認成功")
                    
                    # 更新 order_transactions 表
                    try:
                        transaction_data = {
                            "customer_id": customer_id,
                            "product_id": product_id,
                            "product_name": purchase_record,
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "amount": amount,
                            "transaction_date": original_order['created_at'],
                            "user_role": user_role
                        }
                        
                        transaction_response = requests.post(f"http://127.0.0.1:8000/order_transactions", json=transaction_data)
                        if transaction_response.status_code != 200:
                            print(f"order_transactions 更新失敗，狀態碼：{transaction_response.status_code}")
                    except Exception as e:
                        print(f"order_transactions 更新異常：{str(e)}")
                    
                    orders = get_orders()
                    updated_orders = create_grouped_orders_layout(orders, user_role)
                    return False, True, "訂單已確認，請查看已確認頁面", False, False, "", updated_orders, False, dash.no_update, dash.no_update
                elif response.status_code == 403:
                    return False, False, "", False, True, "權限不足：僅限編輯者使用此功能", dash.no_update, False, dash.no_update, dash.no_update
                else:
                    print(f"API 錯誤，狀態碼：{response.status_code}")
                    return False, False, dash.no_update, True, False, "", dash.no_update, False, dash.no_update, dash.no_update
            except Exception as e:
                print(f"API 呼叫失敗：{e}")
                return False, False, dash.no_update, True, False, "", dash.no_update, False, dash.no_update, dash.no_update
        
        return False, False, dash.no_update, True, False, "", dash.no_update, False, dash.no_update, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
# 縣市區域聯動
@app.callback(
    [Output("new-customer-district", "options", allow_duplicate=True),
     Output("new-customer-district", "value", allow_duplicate=True)],
    Input("new-customer-city", "value"),
    prevent_initial_call=True
)
def update_district_options(selected_city):
    if selected_city and selected_city in CITY_DISTRICT_MAP:
        district_options = [{"label": district, "value": district} for district in CITY_DISTRICT_MAP[selected_city]]
        return district_options, None
    return [], None



# 填入當前處理的客戶資料
@app.callback(
    [Output("new-customer-name", "value", allow_duplicate=True),
     Output("new-customer-id", "value", allow_duplicate=True)],  # 新增這個 Output
    Input("current-processing-order", "data"),
    prevent_initial_call=True
)
def set_customer_data(order_data):
    if order_data:
        customer_name = order_data.get("customer_name", "")
        customer_id = order_data.get("customer_id", "")
        return customer_name, customer_id
    return dash.no_update, dash.no_update

# 儲存新客戶
@app.callback(
    [Output("create-customer-modal", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "children", allow_duplicate=True),
     Output("new_orders-error-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "children", allow_duplicate=True),
     Output("orders-container", "children", allow_duplicate=True)],
    Input("save-new-customer-btn", "n_clicks"),
    [State("new-customer-id", "value"),
     State("new-customer-name", "value"),
     State("new-customer-phone", "value"),
     State("new-customer-address", "value"),
     State("new-customer-city", "value"),
     State("new-customer-district", "value"),
     State("new-customer-notes", "value"),
     State("new-customer-delivery-schedule", "value"),
     State("pending-order-store", "data"),
     State("user-role-store", "data"),
     State("login_status", "data")],
    prevent_initial_call=True
)
def save_new_customer(n_clicks, customer_id, customer_name, phone, address, city, district, notes, delivery_schedule, pending_order, user_role, login_status):
    if n_clicks and pending_order:
        # 取得確認者名稱
        confirmed_by_user = "user"  # 預設值
        if login_status and isinstance(login_status, dict):
            # 從 login_status 中取得 full_name
            confirmed_by_user = login_status.get("full_name") or "user"
        required_fields = [
            ("客戶ID", customer_id),
            ("客戶名稱", customer_name),
            ("電話號碼", phone),
            ("客戶地址", address),
            ("直轄市、縣市", city),
            ("鄉鎮市區", district),
            ("每週配送日", delivery_schedule),
        ]
        missing_fields = get_missing_required_fields(required_fields)
        if missing_fields:
            warning_message = build_required_field_warning(missing_fields)
            return (
                dash.no_update,
                False,
                dash.no_update,
                False,
                True,
                warning_message,
                dash.no_update,
            )

        # 實際組合完整地址
        full_address = ""
        if city:
            full_address += city
        if district:
            full_address += district
        if address:
            full_address += address
        
        # 處理配送日程
        delivery_schedule_str = ",".join(delivery_schedule) if delivery_schedule else ""
        
        # 合併新客戶表單中的備註和從訂單傳來的備註
        combined_notes = ""
        if notes:
            combined_notes += notes
        if pending_order.get("customer_notes"):
            if combined_notes:
                combined_notes += "\n" + pending_order.get("customer_notes")
            else:
                combined_notes = pending_order.get("customer_notes")
        
        # 創建新客戶的資料
        new_customer_data = {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "phone_number": phone,
            "address": full_address,
            "city": city,
            "district": district,
            "notes": combined_notes,  # 使用合併後的備註
            "delivery_schedule": delivery_schedule_str,
            "line_id": pending_order.get("line_id"),
            "user_role": user_role or "viewer"
        }
        
        try:
            # 先創建客戶
            create_response = requests.post("http://127.0.0.1:8000/create_customer", json=new_customer_data)
            if create_response.status_code == 200:
                
                # 如果有 line_id，則將對應關係儲存到 customer_line_mapping
                if pending_order.get("line_id"):
                    try:
                        mapping_data = {
                            "customer_id": customer_id,
                            "line_id": pending_order.get("line_id"),
                            "user_role": user_role or "viewer"
                        }
                        mapping_response = requests.post("http://127.0.0.1:8000/customer_line_mapping", json=mapping_data)
                        if mapping_response.status_code != 200:
                            print(f"customer_line_mapping 新增失敗，狀態碼：{mapping_response.status_code}")
                    except Exception as e:
                        print(f"customer_line_mapping 新增異常：{str(e)}")
                
                
                # 客戶創建成功，繼續處理訂單
                current_time = datetime.now().isoformat()
                
                # 檢查是否為新增訂單
                if pending_order.get("is_new_order"):
                    # 這是新增訂單，直接創建新訂單
                    new_order_data = {
                        "customer_id": customer_id,
                        "customer_name": customer_name,
                        "product_id": pending_order["product_id"],
                        "purchase_record": pending_order["purchase_record"],
                        "quantity": pending_order["quantity"],
                        "unit_price": pending_order["unit_price"],
                        "amount": pending_order["amount"],
                        "status": "1",
                        "confirmed_by": confirmed_by_user,
                        "confirmed_at": current_time,
                        "user_role": user_role or "viewer"
                    }
                    
                    response = requests.post("http://127.0.0.1:8000/create_temp_order", json=new_order_data)
                    if response.status_code == 200:
                        # 新增到 order_transactions 表
                        transaction_data = {
                            "customer_id": customer_id,
                            "product_id": pending_order["product_id"],
                            "product_name": pending_order["purchase_record"],
                            "quantity": pending_order["quantity"],
                            "unit_price": pending_order["unit_price"],
                            "amount": pending_order["amount"],
                            "transaction_date": current_time,
                            "user_role": user_role or "viewer"
                        }
                        
                        transaction_response = requests.post(f"http://127.0.0.1:8000/order_transactions", json=transaction_data)
                        
                        orders = get_orders()
                        updated_orders = create_grouped_orders_layout(orders, user_role)
                        return False, True, "新客戶創建成功，訂單已新增", False, False, "", updated_orders
                    else:
                        return dash.no_update, False, dash.no_update, True, False, "", dash.no_update
                else:
                    # 這是確認訂單，使用原有的更新邏輯
                    update_data = {
                        "customer_id": customer_id,
                        "customer_name": customer_name,
                        "product_id": pending_order["product_id"],
                        "purchase_record": pending_order["purchase_record"],
                        "quantity": pending_order["quantity"],
                        "unit_price": pending_order["unit_price"],
                        "amount": pending_order["amount"],
                        "updated_at": current_time,
                        "status": "1",
                        "confirmed_by": confirmed_by_user,
                        "confirmed_at": current_time,
                        "user_role": user_role or "viewer"
                    }
                    
                    # 更新訂單
                    response = requests.put(f"http://127.0.0.1:8000/temp/{pending_order['order_id']}", json=update_data)
                    if response.status_code == 200:
                        # 更新 order_transactions 表
                        transaction_data = {
                            "customer_id": customer_id,
                            "product_id": pending_order["product_id"],
                            "product_name": pending_order["purchase_record"],
                            "quantity": pending_order["quantity"],
                            "unit_price": pending_order["unit_price"],
                            "amount": pending_order["amount"],
                            "transaction_date": pending_order["original_order"]['created_at'],
                            "user_role": user_role or "viewer"
                        }
                        
                        transaction_response = requests.post(f"http://127.0.0.1:8000/order_transactions", json=transaction_data)
                        
                        orders = get_orders()
                        updated_orders = create_grouped_orders_layout(orders, user_role)
                        return False, True, "新客戶創建成功，訂單已確認", False, False, "", updated_orders
                    else:
                        return dash.no_update, False, dash.no_update, True, False, "", dash.no_update
            else:
                return dash.no_update, False, dash.no_update, True, False, "", dash.no_update
                
        except Exception as e:
            print(f"新客戶創建失敗：{e}")
            return dash.no_update, False, dash.no_update, True, False, "", dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# 跳過客戶創建，直接處理訂單
@app.callback(
    [Output("create-customer-modal", "is_open", allow_duplicate=True),
     Output("confirm-modal", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "children", allow_duplicate=True)],
    Input("skip-customer-btn", "n_clicks"),
    prevent_initial_call=True
)
def skip_customer_creation(n_clicks):
    if n_clicks:
        return False, False, True, "已跳過客戶創建，請重新確認訂單"
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update


# 新增：數量×單價自動計算金額
@app.callback(
    Output("amount", "value"),
    [Input("quantity", "value"),
     Input("unit-price", "value")],
    prevent_initial_call=True
)
def calculate_amount(quantity, unit_price):
    if quantity is not None and unit_price is not None:
        try:
            quantity = float(quantity) if quantity != "" else 0
            unit_price = float(unit_price) if unit_price != "" else 0
            amount = quantity * unit_price
            return round(amount, 2)
        except (ValueError, TypeError):
            return None
    return None


# 開啟新增訂單 Modal
@app.callback(
    Output("add-order-modal", "is_open", allow_duplicate=True),
    Input("add-new-order-btn", "n_clicks"),
    [State("add-order-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_add_order_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# 關閉新增訂單 Modal
@app.callback(
    Output("add-order-modal", "is_open", allow_duplicate=True),
    Input("cancel-add-order", "n_clicks"),
    prevent_initial_call=True
)
def close_add_order_modal(n_clicks):
    if n_clicks:
        return False
    return dash.no_update

# 處理新增訂單提交（您需要根據實際需求實作）
@app.callback(
    [Output("add-order-modal", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "is_open", allow_duplicate=True),
     Output("new_orders-success-toast", "children", allow_duplicate=True),
     Output("new_orders-error-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "is_open", allow_duplicate=True),
     Output("new_orders-warning-toast", "children", allow_duplicate=True),
     Output("orders-container", "children", allow_duplicate=True),
     Output("create-customer-modal", "is_open", allow_duplicate=True),
     Output("pending-order-store", "data", allow_duplicate=True),
     Output("current-processing-order", "data", allow_duplicate=True)],
    Input("submit-add-order", "n_clicks"),
    [State("customer-id", "value"),
     State("customer-name", "value"),
     State("customer-notes", "value"),
     State("product-id", "value"),
     State("purchase-record", "value"),
     State("quantity", "value"),
     State("unit-price", "value"),
     State("amount", "value"),
     State("user-role-store", "data"),
     State("login_status", "data")],
    prevent_initial_call=True
)
def submit_add_order(n_clicks, customer_id, customer_name, customer_notes, product_id, purchase_record, quantity, unit_price, amount, user_role, login_status):
    if not n_clicks:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    # 取得確認者名稱
    confirmed_by_user = "user"  # 預設值
    if login_status and isinstance(login_status, dict):
        # 從 login_status 中取得 full_name
        confirmed_by_user = login_status.get("full_name") or "user"

    required_fields = [
        ("客戶 ID", customer_id),
        ("客戶名稱", customer_name),
        ("產品 ID", product_id),
        ("購買品項", purchase_record),
        ("數量", quantity),
        ("單價", unit_price),
        ("金額", amount),
    ]
    missing_fields = get_missing_required_fields(required_fields)
    if missing_fields:
        warning_message = build_required_field_warning(missing_fields)
        return (
            dash.no_update,
            False,
            dash.no_update,
            False,
            True,
            warning_message,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    if customer_id:
        if not check_customer_exists(customer_id):
            pending_order_data = {
                "is_new_order": True,
                "customer_id": customer_id,
                "customer_name": customer_name,
                "customer_notes": customer_notes,
                "product_id": product_id,
                "purchase_record": purchase_record,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
                "user_role": user_role,
            }
            return (
                False,
                False,
                dash.no_update,
                False,
                False,
                "",
                dash.no_update,
                True,
                pending_order_data,
                {"customer_id": customer_id, "customer_name": customer_name},
            )
    else:
        pending_order_data = {
            "is_new_order": True,
            "customer_id": customer_id or "",
            "customer_name": customer_name,
            "customer_notes": customer_notes,
            "product_id": product_id,
            "purchase_record": purchase_record,
            "quantity": quantity,
            "unit_price": unit_price,
            "amount": amount,
            "user_role": user_role,
        }
        return (
            False,
            False,
            dash.no_update,
            False,
            False,
            "",
            dash.no_update,
            True,
            pending_order_data,
            {"customer_id": customer_id or "", "customer_name": customer_name},
        )

    if customer_id and customer_notes:
        try:
            notes_update_data = {"notes": customer_notes, "user_role": user_role}
            notes_response = requests.put(f"http://127.0.0.1:8000/customer/{customer_id}", json=notes_update_data)
            if notes_response.status_code != 200:
                print(f"客戶備註更新失敗，狀態碼：{notes_response.status_code}")
        except Exception as e:
            print(f"客戶備註更新異常：{str(e)}")

    new_order_data = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "product_id": product_id,
        "purchase_record": purchase_record,
        "quantity": quantity,
        "unit_price": unit_price,
        "amount": amount,
        "status": "1",
        "confirmed_by": confirmed_by_user,
        "confirmed_at": datetime.now().isoformat(),
        "user_role": user_role or "viewer",
    }

    try:
        response = requests.post("http://127.0.0.1:8000/create_temp_order", json=new_order_data)
        if response.status_code == 200:
            try:
                transaction_data = {
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "product_name": purchase_record,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "amount": amount,
                    "transaction_date": datetime.now().isoformat(),
                    "user_role": user_role,
                }
                transaction_response = requests.post("http://127.0.0.1:8000/order_transactions", json=transaction_data)
                if transaction_response.status_code != 200:
                    print(f"order_transactions 更新失敗，狀態碼：{transaction_response.status_code}")
            except Exception as e:
                print(f"order_transactions 更新異常：{str(e)}")

            orders = get_orders()
            updated_orders = create_grouped_orders_layout(orders, user_role)
            return (
                False,
                True,
                "訂單新增成功",
                False,
                False,
                "",
                updated_orders,
                False,
                dash.no_update,
                dash.no_update,
            )
        elif response.status_code == 403:
            return (
                dash.no_update,
                False,
                dash.no_update,
                True,
                False,
                "",
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )
        else:
            return (
                dash.no_update,
                False,
                dash.no_update,
                True,
                False,
                "",
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )
    except Exception as e:
        print(f"API 呼叫失敗：{e}")
        return (
            dash.no_update,
            False,
            dash.no_update,
            True,
            False,
            "",
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )


# 客戶名稱搜尋功能
@app.callback(
    Output("orders-container", "children", allow_duplicate=True),
    [Input("customer-search-input", "value")],
    [State("filter-all", "outline"),
     State("filter-unconfirmed", "outline"),
     State("filter-confirmed", "outline"),
     State("filter-deleted", "outline"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def search_customers(search_value, all_outline, unconfirmed_outline, confirmed_outline, deleted_outline, user_role):
    if not search_value:
        # 如果搜尋框為空，根據當前篩選狀態顯示所有訂單
        orders = get_orders()
        
        # 判斷當前篩選狀態
        if not all_outline:  # 全部按鈕被選中
            filtered_orders = orders
        elif not unconfirmed_outline:  # 未確認按鈕被選中
            filtered_orders = [order for order in orders if order.get("status") == "0"]
        elif not confirmed_outline:  # 已確認按鈕被選中
            filtered_orders = [order for order in orders if order.get("status") == "1"]
        elif not deleted_outline:  # 已刪除按鈕被選中
            filtered_orders = [order for order in orders if order.get("status") == "2"]
        else:
            filtered_orders = orders
        
        return create_grouped_orders_layout(filtered_orders, user_role)
    
    # 執行搜尋
    orders = get_orders()
    
    # 根據當前篩選狀態先篩選訂單
    if not all_outline:  # 全部按鈕被選中
        filtered_orders = orders
    elif not unconfirmed_outline:  # 未確認按鈕被選中
        filtered_orders = [order for order in orders if order.get("status") == "0"]
    elif not confirmed_outline:  # 已確認按鈕被選中
        filtered_orders = [order for order in orders if order.get("status") == "1"]
    elif not deleted_outline:  # 已刪除按鈕被選中
        filtered_orders = [order for order in orders if order.get("status") == "2"]
    else:
        filtered_orders = orders
    
    # 根據搜尋詞進一步篩選客戶名稱
    search_value_lower = search_value.lower()
    search_result_orders = []
    
    for order in filtered_orders:
        # 只檢查 customer_name 是否包含搜尋詞
        customer_name = order.get("customer_name", "")
        if customer_name and search_value_lower in customer_name.lower():
            search_result_orders.append(order)
    
    return create_grouped_orders_layout(search_result_orders, user_role)

# 自動檢查訂單更新的回調函數
@app.callback(
    [Output("orders-container", "children", allow_duplicate=True),
     Output("last-update-check-time", "data")],
    Input("order-update-checker", "n_intervals"),
    [State("last-update-check-time", "data"),
     State("filter-all", "outline"),
     State("filter-unconfirmed", "outline"),
     State("filter-confirmed", "outline"),
     State("filter-deleted", "outline"),
     State("customer-search-input", "value"),
     State("user-role-store", "data")],
    prevent_initial_call=True
)
def auto_check_for_updates(n_intervals, last_check_time, all_outline, unconfirmed_outline,
                          confirmed_outline, deleted_outline, search_value, user_role):
    try:
        # 調用 API 檢查是否有更新
        check_url = "http://127.0.0.1:8000/check_orders_update"
        if last_check_time:
            check_url += f"?last_check_time={last_check_time}"

        response = requests.get(check_url)
        current_time = datetime.now().isoformat()

        if response.status_code == 200:
            update_data = response.json()
            has_update = update_data.get("has_update", False)

            # 如果有更新，重新載入資料
            if has_update:
                print(f"[AUTO UPDATE] 檢測到訂單更新，重新載入資料 - 更新類型: {update_data.get('update_type')}")

                # 重新載入訂單資料
                orders = get_orders()

                # 根據當前篩選狀態過濾訂單
                if not all_outline:  # 全部按鈕被選中
                    filtered_orders = orders
                elif not unconfirmed_outline:  # 未確認按鈕被選中
                    filtered_orders = [order for order in orders if order.get("status") == "0"]
                elif not confirmed_outline:  # 已確認按鈕被選中
                    filtered_orders = [order for order in orders if order.get("status") == "1"]
                elif not deleted_outline:  # 已刪除按鈕被選中
                    filtered_orders = [order for order in orders if order.get("status") == "2"]
                else:
                    filtered_orders = orders

                # 如果有搜尋詞，進一步過濾
                if search_value:
                    search_value_lower = search_value.lower()
                    search_result_orders = []
                    for order in filtered_orders:
                        customer_name = order.get("customer_name", "")
                        if customer_name and search_value_lower in customer_name.lower():
                            search_result_orders.append(order)
                    filtered_orders = search_result_orders

                return create_grouped_orders_layout(filtered_orders, user_role), current_time
            else:
                # 沒有更新，只更新檢查時間
                return dash.no_update, current_time
        else:
            print(f"[AUTO UPDATE] API 檢查失敗，狀態碼: {response.status_code}")
            return dash.no_update, current_time

    except Exception as e:
        print(f"[AUTO UPDATE] 自動檢查更新失敗: {e}")
        return dash.no_update, datetime.now().isoformat()

# 根據用戶角色控制新增訂單按鈕顯示
@app.callback(
    Output("add-new-order-btn", "style"),
    Input("user-role-store", "data"),
    prevent_initial_call=True
)
def control_add_button_visibility(user_role):
    """當用戶角色為viewer時隱藏新增訂單按鈕"""
    if user_role == "viewer":
        return {"display": "none"}
    else:
        return {"fontWeight": "500", "fontSize": "16px", "marginRight": "15px"}

# 根據用戶角色重新渲染訂單列表
@app.callback(
    Output("orders-container", "children", allow_duplicate=True),
    Input("user-role-store", "data"),
    [State("filter-all", "outline"),
     State("filter-unconfirmed", "outline"),
     State("filter-confirmed", "outline"),
     State("filter-deleted", "outline"),
     State("customer-search-input", "value")],
    prevent_initial_call=True
)
def update_orders_with_role(user_role, all_outline, unconfirmed_outline, confirmed_outline, deleted_outline, search_value):
    """根據用戶角色重新渲染訂單列表，控制按鈕顯示"""
    orders = get_orders()

    # 根據當前篩選狀態過濾訂單
    if not all_outline:  # 全部按鈕被選中
        filtered_orders = orders
    elif not unconfirmed_outline:  # 未確認按鈕被選中
        filtered_orders = [order for order in orders if order.get("status") == "0"]
    elif not confirmed_outline:  # 已確認按鈕被選中
        filtered_orders = [order for order in orders if order.get("status") == "1"]
    elif not deleted_outline:  # 已刪除按鈕被選中
        filtered_orders = [order for order in orders if order.get("status") == "2"]
    else:
        filtered_orders = orders

    # 如果有搜尋詞，進一步過濾
    if search_value:
        search_value_lower = search_value.lower()
        search_result_orders = []
        for order in filtered_orders:
            customer_name = order.get("customer_name", "")
            if customer_name and search_value_lower in customer_name.lower():
                search_result_orders.append(order)
        filtered_orders = search_result_orders

    return create_grouped_orders_layout(filtered_orders, user_role)
