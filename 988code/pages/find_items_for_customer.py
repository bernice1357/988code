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
                        html.Div([
                            html.H4('歷史購買記錄', style={'margin-bottom': '15px', 'flex': '1', 'height': '32px', 'line-height': '32px'}),
                            dcc.Dropdown(
                                id='month-filter-dropdown',
                                options=[],
                                placeholder='選擇年月',
                                value='all',
                                style={'width': '150px'}
                            )
                        ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between', 'margin-bottom': '15px'}),
                        
                        html.Div([
                            # 表格標題（固定不滾動）
                            html.Div([
                                html.Div('商品名稱', style={'font-weight': 'bold', 'flex': '2'}),
                                html.Div('數量', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1'}),
                                html.Div('購買時間', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1'})
                            ], style={'display': 'flex', 'padding': '10px', 'background-color': '#f0f0f0', 'border-bottom': '2px solid #ddd'}),
                            
                            # 可滾動的表格內容區域
                            dcc.Loading(
                                id="loading-purchase-history-table",
                                type="dot",
                                children=html.Div(
                                    id='purchase-history-table', 
                                    children=[],
                                    style={
                                        'height': '45vh',       # 調整為45vh
                                        'overflow-y': 'auto',   # 垂直滾動
                                        'overflow-x': 'hidden', # 隱藏水平滾動
                                        'border': 'none',
                                        'background-color': '#fafafa'  # 淺色背景，讓空白區域更明顯
                                    }
                                ),
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "position": "fixed", 
                                    "top": "50%",          
                                }
                            )
                        ], style={'border': '1px solid #ccc', 'margin-bottom': '15px'}),
                        html.Div([
                            html.Div(id='current-month-spending', children='當月消費總金額 $ 0', 
                                    style={'text-align': 'left', 'font-size': '16px', 'flex': '1'}),
                            html.Div(id='monthly-average', children='所有月份平均消費 $ 0', 
                                    style={'text-align': 'right', 'font-size': '16px', 'flex': '1', 'font-weight': 'bold'})
                        ], style={'display': 'flex'})
                    ])
                ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),
                
                # 右側區塊
                html.Div([
                    # 推薦產品區塊
                    html.Div([
                        html.H4('推薦產品', style={'margin-bottom': '30px', 'height': '32px', 'line-height': '64px', 'display': 'flex', 'align-items': 'center'}),
                        html.Div([
                            html.Div([
                                html.Div('商品ID', style={'font-weight': 'bold', 'flex': '1'}),
                                html.Div('商品名稱', style={'font-weight': 'bold', 'text-align': 'right'})
                            ], style={'display': 'flex', 'padding': '10px', 'background-color': '#f0f0f0', 'border-bottom': '2px solid #ddd'}),
                            
                            # 可滾動的推薦產品內容區域
                            dcc.Loading(
                                id="loading-recommended-products-table",
                                type="dot",
                                children=html.Div(
                                    id='recommended-products-table', 
                                    children=[],
                                    style={
                                        'height': '45vh',      # 調整為45vh，與歷史紀錄一致
                                        'overflow-y': 'auto',   # 垂直滾動
                                        'overflow-x': 'hidden', # 隱藏水平滾動
                                        'border': 'none',
                                        'background-color': '#fafafa'  # 淺色背景，讓空白區域更明顯
                                    }
                                ),
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "position": "fixed", 
                                    "top": "50%",          
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
    [Output('month-filter-dropdown', 'options'),
     Output('month-filter-dropdown', 'value')],
    Input('customer-id-dropdown', 'value')
)
def update_month_options(selected_customer_id):
    if not selected_customer_id:
        return [{'label': '所有月份', 'value': 'all'}], 'all'
    
    try:
        response = requests.get(f"http://127.0.0.1:8000/get_customer_monthly_spending/{selected_customer_id}")
        
        if response.status_code == 200:
            monthly_data = response.json()
            options = [{'label': '所有月份', 'value': 'all'}]
            
            for item in monthly_data:
                month = item['month']
                options.append({'label': month, 'value': month})
            
            return options, 'all'
        else:
            return [{'label': '所有月份', 'value': 'all'}], 'all'
            
    except Exception as e:
        return [{'label': '所有月份', 'value': 'all'}], 'all'

@app.callback(
    [Output('purchase-history-table', 'children'),
     Output('current-month-spending', 'children'),
     Output('monthly-average', 'children')],
    [Input('customer-id-dropdown', 'value'),
     Input('month-filter-dropdown', 'value')]
)
def update_customer_info_and_history(selected_customer_id, selected_month):
    if not selected_customer_id:
        return [], '當月消費總金額 $ 0', '所有月份平均消費 $ 0'
    
    try:
        # 調用 API 獲取歷史購買記錄
        purchase_response = requests.get(f"http://127.0.0.1:8000/get_recommendation_purchase_history/{selected_customer_id}")
        
        # 調用 API 獲取月消費金額
        monthly_response = requests.get(f"http://127.0.0.1:8000/get_customer_monthly_spending/{selected_customer_id}")
        
        table_rows = []
        current_month_text = '當月消費總金額 $ 0'
        monthly_average_text = '所有月份平均消費 $ 0'
        
        # 處理歷史購買記錄
        if purchase_response.status_code == 200:
            purchase_data = purchase_response.json()
            
            # 如果選擇了特定月份，篩選資料
            if selected_month and selected_month != 'all':
                purchase_data = [item for item in purchase_data 
                               if item.get('transaction_date', '').startswith(selected_month)]
            
            for item in purchase_data:
                product_name = item.get('product_name', item.get('品項', ''))
                quantity = item.get('quantity', item.get('數量', ''))
                transaction_date = item.get('transaction_date', item.get('購買時間', ''))
                
                row = html.Div([
                    html.Div(product_name, style={'flex': '2'}),
                    html.Div(str(quantity), style={'text-align': 'center', 'flex': '1'}),
                    html.Div(transaction_date, style={'text-align': 'center', 'flex': '1'})
                ], style={
                    'display': 'flex', 
                    'padding': '10px', 
                    'border-bottom': '1px solid #ddd',
                    'min-height': '40px',
                    'align-items': 'center'
                })
                
                table_rows.append(row)
        else:
            table_rows = [html.Div('無法獲取歷史購買記錄', style={'padding': '10px', 'color': 'red'})]
        
        # 處理月平均消費和當月消費
        if monthly_response.status_code == 200:
            monthly_data = monthly_response.json()
            
            if monthly_data:
                total_amount = sum(item['total_amount'] for item in monthly_data)
                month_count = len(monthly_data)
                monthly_average = total_amount / month_count if month_count > 0 else 0
                monthly_average_text = f'所有月份平均消費 $ {monthly_average:,.0f}'
                
                # 計算當月消費（選擇的月份或最新月份）
                if selected_month and selected_month != 'all':
                    # 如果選擇了特定月份，顯示該月的消費
                    current_month_data = next((item for item in monthly_data if item['month'] == selected_month), None)
                    if current_month_data:
                        current_month_text = f'當月消費總金額 $ {current_month_data["total_amount"]:,.0f}'
                else:
                    # 如果選擇全部，顯示最新月份的消費
                    latest_month_data = max(monthly_data, key=lambda x: x['month'])
                    current_month_text = f'當月消費總金額 $ {latest_month_data["total_amount"]:,.0f}'
        
        return table_rows, current_month_text, monthly_average_text
            
    except Exception as e:
        return [
            html.Div(f'載入資料時發生錯誤：{str(e)}', style={'padding': '10px', 'color': 'red'})
        ], '當月消費總金額 $ 0', '所有月份平均消費 $ 0'
    
@app.callback(
    Output('recommended-products-table', 'children'),
    Input('customer-id-dropdown', 'value')
)
def update_recommended_products(selected_customer_id):
    if not selected_customer_id:
        return []
    
    try:
        # 調用 API 獲取推薦產品
        response = requests.get(f"http://127.0.0.1:8000/get_customer_recommendations/{selected_customer_id}")
        
        if response.status_code == 200:
            recommendation_data = response.json()
            
            # 建立推薦產品表格
            table_rows = []
            
            if recommendation_data:  # 確保有資料
                item = recommendation_data[0]  # 只取第一筆記錄
                
                # 處理3個推薦商品
                for rank in range(1, 4):
                    product_id = item.get(f'recommended_product_id_rank{rank}', '')
                    product_name = item.get(f'recommended_product_name_rank{rank}', '')
                    
                    if product_id and product_name:  # 確保ID和名稱都有值
                        row = html.Div([
                            html.Div(product_id, style={'flex': '1'}),
                            html.Div(product_name, style={'text-align': 'right'})
                        ], style={
                            'display': 'flex', 
                            'padding': '10px', 
                            'border-bottom': '1px solid #ddd',
                            'min-height': '40px',
                            'align-items': 'center'
                        })
                        
                        table_rows.append(row)
            
            return table_rows
            
        else:
            return [
                html.Div('無法獲取推薦產品', style={'padding': '10px', 'color': 'red'})
            ]
            
    except Exception as e:
        return [
            html.Div(f'載入推薦資料時發生錯誤：{str(e)}', style={'padding': '10px', 'color': 'red'})
        ]