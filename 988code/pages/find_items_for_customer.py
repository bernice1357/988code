from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback

tab_content = html.Div([
    # 客戶ID下拉選單
    html.Div([
        html.Label('客戶 ID', style={'margin-right': '10px', 'font-weight': 'bold', 'align-self': 'center'}),
        dcc.Dropdown(
            id='customer-id-dropdown',
            options=[],
            placeholder='選擇客戶ID',
            style={'width': '200px'}
        )
    ], style={'margin': '30px 10px 10px 10px', 'display': 'flex', 'align-items': 'center'}),
    
    # 大框
    html.Div([
        html.Div([
            html.Div([
                # 左側區塊
                html.Div([
                    # 歷史購買記錄區塊
                    html.Div([
                        html.H4('歷史購買記錄', style={'margin-bottom': '15px'}),
                        html.Div([
                            # 表格標題（固定不滾動）
                            html.Div([
                                html.Div('商品名稱', style={'font-weight': 'bold', 'flex': '2'}),
                                html.Div('數量', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1'}),
                                html.Div('購買時間', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1'})
                            ], style={'display': 'flex', 'padding': '10px', 'background-color': '#f0f0f0', 'border-bottom': '2px solid #ddd'}),
                            
                            # 可滾動的表格內容區域
                            html.Div(
                                id='purchase-history-table', 
                                children=[],
                                style={
                                    'height': '50vh',       # 改為40vh（視窗高度的40%）
                                    'overflow-y': 'auto',   # 垂直滾動
                                    'overflow-x': 'hidden', # 隱藏水平滾動
                                    'border': 'none',
                                    'background-color': '#fafafa'  # 淺色背景，讓空白區域更明顯
                                }
                            )
                        ], style={'border': '1px solid #ccc', 'margin-bottom': '15px'}),
                        html.Div(id='monthly-average', children='月平均消費　　　　　　　　$ 0', 
                                style={'text-align': 'right', 'font-size': '16px'})
                    ])
                ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),
                
                # 右側區塊
                html.Div([
                    # 推薦產品區塊
                    html.Div([
                        html.H4('推薦產品', style={'margin-bottom': '15px'}),
                        html.Div([
                            # 表格標題（固定不滾動）
                            html.Div([
                                html.Div('商品名稱', style={'font-weight': 'bold', 'flex': '1'}),
                                html.Div('類別', style={'font-weight': 'bold', 'text-align': 'right'})
                            ], style={'display': 'flex', 'padding': '10px', 'background-color': '#f0f0f0', 'border-bottom': '2px solid #ddd'}),
                            
                            # 可滾動的推薦產品內容區域
                            html.Div(
                                id='recommended-products-table', 
                                children=[],
                                style={
                                    'height': '50vh',      # 固定高度
                                    'overflow-y': 'auto',   # 垂直滾動
                                    'overflow-x': 'hidden', # 隱藏水平滾動
                                    'border': 'none',
                                    'background-color': '#fafafa'  # 淺色背景，讓空白區域更明顯
                                }
                            )
                        ], style={'border': '1px solid #ccc'})
                    ])
                ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '4%'})
            ], style={
                'box-shadow': '0 4px 8px rgba(0,0,0,0.15)',
                'padding': '20px',
                'margin': '20px 0',
                'background-color': '#ffffff'
            })
        ])
    ], style={'margin': '10px'})
])

@app.callback(
    Output('customer-id-dropdown', 'options'),
    Input('customer-id-dropdown', 'id')
)
def update_customer_options(dropdown_id):
    response = requests.get("http://127.0.0.1:8000/get_customer_ids")
    customer_ids = response.json()
    options = [{'label': item['customer_id'], 'value': item['customer_id']} for item in customer_ids]
    return options

@app.callback(
    [Output('purchase-history-table', 'children'),
     Output('monthly-average', 'children')],
    Input('customer-id-dropdown', 'value')
)
def update_customer_info_and_history(selected_customer_id):
    if not selected_customer_id:
        return [], '月平均消費　　　　　　　　$ 0'
    
    try:
        # 調用 API 獲取歷史購買記錄
        response = requests.get(f"http://127.0.0.1:8000/get_recommendation_purchase_history/{selected_customer_id}")
        
        if response.status_code == 200:
            purchase_data = response.json()
            
            # 建立歷史購買記錄表格
            table_rows = []
            total_amount = 0
            
            for item in purchase_data:
                # 從 API 回傳的資料中提取品項、數量、購買時間
                product_name = item.get('product_name', item.get('品項', ''))
                quantity = item.get('quantity', item.get('數量', ''))
                transaction_date = item.get('transaction_date', item.get('購買時間', ''))
                
                # 如果有價格資訊，計算總金額
                if 'amount' in item:
                    total_amount += item['amount']
                
                row = html.Div([
                    html.Div(product_name, style={'flex': '2'}),
                    html.Div(str(quantity), style={'text-align': 'center', 'flex': '1'}),
                    html.Div(transaction_date, style={'text-align': 'center', 'flex': '1'})
                ], style={
                    'display': 'flex', 
                    'padding': '10px', 
                    'border-bottom': '1px solid #ddd',
                    'min-height': '40px',  # 確保每行有最小高度
                    'align-items': 'center'  # 垂直居中對齊
                })
                
                table_rows.append(row)
            
            # 計算月平均消費（假設根據總金額計算）
            monthly_average = f'月平均消費　　　　　　　　$ {total_amount:,.0f}' if total_amount > 0 else '月平均消費　　　　　　　　$ 0'
            
            return table_rows, monthly_average
            
        else:
            # API 調用失敗時的處理
            return [
                html.Div('無法獲取歷史購買記錄', style={'padding': '10px', 'color': 'red'})
            ], '月平均消費　　　　　　　　$ 0'
            
    except Exception as e:
        # 例外處理
        return [
            html.Div(f'載入資料時發生錯誤：{str(e)}', style={'padding': '10px', 'color': 'red'})
        ], '月平均消費　　　　　　　　$ 0'