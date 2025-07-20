from .common import *
from components.offcanvas import create_search_offcanvas, register_offcanvas_callback
import dash_bootstrap_components as dbc

tab_content = html.Div([
    # 產品ID下拉選單
    html.Div([
        html.Label('產品 ID', style={'margin-right': '10px', 'font-weight': 'bold', 'align-self': 'center'}),
        dcc.Dropdown(
            id='product-id-dropdown',
            options=[],
            placeholder='選擇產品ID',
            style={'width': '200px'}
        )
    ], style={'margin': '30px 10px 10px 10px', 'display': 'flex', 'align-items': 'center'}),
    
    # 大框
    html.Div([
        html.Div([
            html.Div([
                # 推薦客戶區塊
                html.Div([
                    html.H4(id='recommended-customers-title', children='推薦客戶', style={'margin-bottom': '30px', 'height': '32px', 'line-height': '64px', 'display': 'flex', 'align-items': 'center'}),
                    html.Div(
                        id='recommended-customers-table', 
                        children=[],
                        style={
                            'height': '56vh',
                            'overflow': 'hidden',
                            'border': '1px solid #ccc',
                            'background-color': '#fafafa'
                        }
                    )
                ])
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
    Output('product-id-dropdown', 'options'),
    Input('product-id-dropdown', 'id')
)
def update_product_options(dropdown_id):
    response = requests.get("http://127.0.0.1:8000/get_recommended_product_ids")
    product_ids = response.json()
    options = [{'label': item['product_id'], 'value': item['product_id']} for item in product_ids]
    return options

@app.callback(
    [Output('recommended-customers-table', 'children'),
     Output('recommended-customers-title', 'children')],
    Input('product-id-dropdown', 'value')
)
def update_recommended_customers(selected_product_id):
    if not selected_product_id:
        return [], '推薦客戶'
    
    try:
        # 調用 API 獲取推薦客戶
        response = requests.get(f"http://127.0.0.1:8000/get_product_recommendations/{selected_product_id}")
        
        product_name = '推薦客戶'
        
        # 先獲取產品名稱
        product_info_response = requests.get("http://127.0.0.1:8000/get_recommended_product_ids")
        if product_info_response.status_code == 200:
            product_data = product_info_response.json()
            product_item = next((item for item in product_data if item['product_id'] == selected_product_id), None)
            if product_item and 'name_zh' in product_item:
                product_name = [
                    html.Span(product_item["name_zh"], style={'color': '#30648c'}),
                    html.Span(' 推薦客戶')
                ]
        
        if response.status_code == 200:
            recommendation_data = response.json()
            
            # 建立推薦客戶表格
            accordions = []
            
            if recommendation_data:
                item = recommendation_data[0]
                
                # 處理3個推薦客戶
                for rank in range(1, 4):
                    customer_id = item.get(f'recommended_customer_id_rank{rank}', '')
                    customer_name = item.get(f'recommended_customer_name_rank{rank}', '')
                    
                    if customer_id and customer_name:
                        # 建立 Accordion，預設顯示提示文字
                        accordion = dbc.AccordionItem([
                            html.Div('點擊展開查看購買記錄', 
                                   style={
                                       'padding': '20px', 
                                       'text-align': 'center', 
                                       'color': '#666',
                                       'background-color': 'white'
                                   })
                        ], title=f'{customer_id} - {customer_name}', item_id=f'accordion-{customer_id}')
                        
                        accordions.append(accordion)
            
            return [
                dbc.Accordion(accordions, id='customer-accordion', start_collapsed=True),
                dcc.Store(id='accordion-trigger')
            ], product_name
            
        else:
            return [
                html.Div('無法獲取推薦客戶', style={'padding': '10px', 'color': 'red'})
            ], product_name
            
    except Exception as e:
        return [
            html.Div(f'載入推薦資料時發生錯誤：{str(e)}', style={'padding': '10px', 'color': 'red'})
        ], '推薦客戶'

# 使用 clientside callback 處理 accordion 展開事件
app.clientside_callback(
    """
    function(active_item, product_id) {
        if (!active_item || !product_id) {
            return window.dash_clientside.no_update;
        }
        
        // 只有當 active_item 改變時才觸發
        return active_item;
    }
    """,
    Output('accordion-trigger', 'data'),
    [Input('customer-accordion', 'active_item')],
    [State('product-id-dropdown', 'value')],
    prevent_initial_call=True
)

@app.callback(
    Output('customer-accordion', 'children'),
    [Input('accordion-trigger', 'data')],
    [State('product-id-dropdown', 'value'),
     State('customer-accordion', 'active_item'),
     State('customer-accordion', 'children')]
)
def load_customer_history_on_expand(trigger, selected_product_id, active_item, current_children):
    if not trigger or not selected_product_id or not active_item or not current_children:
        return dash.no_update
    
    try:
        # 獲取推薦客戶資料
        response = requests.get(f"http://127.0.0.1:8000/get_product_recommendations/{selected_product_id}")
        if response.status_code != 200:
            return dash.no_update
        
        recommendation_data = response.json()
        if not recommendation_data:
            return dash.no_update
        
        item = recommendation_data[0]
        accordions = []
        
        # 重建 accordion 項目
        for rank in range(1, 4):
            customer_id = item.get(f'recommended_customer_id_rank{rank}', '')
            customer_name = item.get(f'recommended_customer_name_rank{rank}', '')
            
            if customer_id and customer_name:
                accordion_content = []
                
                # 如果是當前展開的項目，載入詳細資料
                if active_item == f'accordion-{customer_id}':
                    history_response = requests.get(f"http://127.0.0.1:8000/get_recommended_customer_history/{customer_id}")
                    
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        
                        if history_data:
                            # 建立固定標題和可滾動內容的結構
                            table_header = html.Div([
                                html.Div('購買品項ID', style={'font-weight': 'bold', 'flex': '1'}),
                                html.Div('購買品項名稱', style={'font-weight': 'bold', 'flex': '2'}),
                                html.Div('購買次數', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1'}),
                                html.Div('首次購買日期', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1'}),
                                html.Div('最後購買日期', style={'font-weight': 'bold', 'text-align': 'center', 'flex': '1'})
                            ], style={'display': 'flex', 'padding': '10px', 'background-color': '#f8f9fa', 'border-bottom': '1px solid #ddd'})
                            
                            # 可滾動的資料內容
                            table_rows = []
                            for record in history_data:
                                product_id = record.get('product_id', '')
                                product_name = record.get('product_name', '')
                                purchase_count = record.get('purchase_count', '')
                                earliest_date = record.get('earliest_purchase_date', '')
                                latest_date = record.get('latest_purchase_date', '')
                                
                                if product_id and product_name and earliest_date and latest_date:
                                    table_rows.append(
                                        html.Div([
                                            html.Div(product_id, style={'flex': '1'}),
                                            html.Div(product_name, style={'flex': '2'}),
                                            html.Div(str(purchase_count), style={'text-align': 'center', 'flex': '1'}),
                                            html.Div(earliest_date, style={'text-align': 'center', 'flex': '1'}),
                                            html.Div(latest_date, style={'text-align': 'center', 'flex': '1'})
                                        ], style={
                                            'display': 'flex', 
                                            'padding': '8px 10px', 
                                            'border-bottom': '1px solid #eee',
                                            'align-items': 'center'
                                        })
                                    )
                            
                            scrollable_content = html.Div(table_rows, style={
                                'max-height': '33vh', 
                                'overflow-y': 'auto',
                                'background-color': 'white'
                            })
                            
                            accordion_content = [table_header, scrollable_content]
                        else:
                            accordion_content.append(html.Div('無購買記錄', style={'padding': '10px', 'color': '#666'}))
                    else:
                        accordion_content.append(html.Div('無法載入購買記錄', style={'padding': '10px', 'color': 'red'}))
                else:
                    accordion_content.append(html.Div('點擊展開查看購買記錄', style={'padding': '20px', 'text-align': 'center', 'color': '#666'}))
                
                accordion = dbc.AccordionItem([
                    html.Div(accordion_content, 
                            style={
                                'max-height': '800px', 
                                'background-color': 'white'
                            })
                ], title=f'{customer_id} - {customer_name}', item_id=f'accordion-{customer_id}')
                
                accordions.append(accordion)
        
        return accordions
        
    except Exception as e:
        return dash.no_update