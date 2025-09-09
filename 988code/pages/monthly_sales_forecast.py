from .common import *
from components.table import custom_table
import requests
from dash import ALL
from datetime import datetime

current_month = datetime.now().strftime("%Y-%m")
# 初始空的 DataFrame，將由 callback 動態載入
monthly_forecast_df = pd.DataFrame()

tab_content = html.Div([
    # 隱藏的存儲組件來儲存資料
    dcc.Store(id="monthly-forecast-data", data=[]),
    dcc.Store(id="category-count-store", data=0),  # 新增：存儲分類數量
    
    # 控制面板
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.Label("預測期間：", style={"marginRight": "10px", "fontWeight": "normal"}),
                    dbc.Input(
                        type="month",
                        value=current_month,
                        id="monthly-forecast-period",
                        style={"width": "120px", "display": "inline-block", "marginRight": "20px"}
                    )
                ], style={"display": "inline-block", "marginRight": "30px"}),
                
                html.Div([
                    html.Label("商品類別：", style={"marginRight": "10px", "fontWeight": "normal"}),
                    dbc.Select(
                        options=[{"label": "全部類別", "value": "全部類別"}],
                        value="全部類別",
                        id="monthly-category-select",
                        style={"width": "auto", "display": "inline-block", "marginRight": "20px"}
                    )
                ], style={"display": "inline-block", "marginRight": "30px"}),
                
                dbc.Button(
                    "更新預測",
                    color="success",
                    id="update-monthly-forecast-btn",
                    style={"backgroundColor": "#28a745", "borderColor": "#28a745"}
                )
            ], style={
                "backgroundColor": "#e8e8e8",
                "padding": "15px",
                "marginBottom": "20px",
                "display": "flex",
                "alignItems": "center",
                "flexWrap": "wrap"
            })
        ])
    ]),
    
    # 預測數據詳情區域
    html.Div([
        html.H5("預測數據詳情", style={
            "backgroundColor": "#f8f9fa",
            "padding": "10px 15px",
            "margin": "0",
            "borderBottom": "1px solid #dee2e6",
            "fontWeight": "bold",
            "fontSize": "16px"
        }),
        
        # 動態生成的階層式表格
        html.Div(id="monthly-forecast-table-container", children=[], style={
            "overflow-y": "auto",
            "max-height": "calc(65vh - 60px)",  # 減去標題高度
            "padding": "10px"
        })
    ], style={
        "backgroundColor": "white",
        "border": "1px solid #dee2e6",
        "borderRadius": "4px",
        "overflow": "hidden",
        "height": "65vh"
    })
], style={
    "padding": "20px",
    "minHeight": "500px"
})

# 載入資料的 callback
@app.callback(
    [Output('monthly-forecast-data', 'data'),
     Output('monthly-category-select', 'options')],
    [Input('update-monthly-forecast-btn', 'n_clicks'),
    Input('monthly-forecast-period', 'value')],
    prevent_initial_call=False
)
def load_monthly_forecast_data(n_clicks, selected_period):
    try:
        # 呼叫 API 獲取每月銷量預測資料
        response = requests.get(f'http://127.0.0.1:8000/get_monthly_sales_predictions?period={selected_period}')
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                # 獲取所有子類別選項，處理可能的空值
                subcategories = list(set([
                    item.get('subcategory', '') 
                    for item in data 
                    if item.get('subcategory') and str(item.get('subcategory')).strip()
                ]))
                subcategories.sort()
                
                # 建立選項列表
                category_options = [{"label": "全部類別", "value": "全部類別"}]
                for subcategory in subcategories:
                    category_options.append({"label": subcategory, "value": subcategory})
                
                return data, category_options
            else:
                return [], [{"label": "全部類別", "value": "全部類別"}]
        else:
            return [], [{"label": "全部類別", "value": "全部類別"}]
            
    except Exception as e:
        print(f"[前端] 載入預測資料失敗: {e}")
        import traceback
        traceback.print_exc()
        return [], [{"label": "全部類別", "value": "全部類別"}]

# 生成階層式表格的 callback
@app.callback(
    [Output('monthly-forecast-table-container', 'children'),
     Output('category-count-store', 'data')],
    [Input('monthly-forecast-data', 'data'),
     Input('monthly-category-select', 'value')],
    prevent_initial_call=False
)
def generate_hierarchical_table(data, selected_category):
    if not data:
        return html.Div("暫無資料", style={"padding": "20px", "textAlign": "center"}), 0
    
    # 篩選資料
    if selected_category and selected_category != "全部類別":
        filtered_data = [item for item in data if item.get('subcategory') == selected_category]
    else:
        filtered_data = data
    
    # 按子類別分組
    subcategory_groups = {}
    for item in filtered_data:
        subcategory = item.get('subcategory', '未知分類')
        if subcategory not in subcategory_groups:
            subcategory_groups[subcategory] = {
                'subcategory': subcategory,
                'volatility_group': '',  # 先初始化為空
                'total_month_minus_1': 0,
                'total_prediction_value': 0,
                'products': [],
                'sku_products': [],  # 只存儲 sku 級別的產品
                'has_subcategory_level': False,  # 追蹤是否有 subcategory 級別的預測
                'sku_total_month_minus_1': 0,  # sku 級別的總計
                'sku_total_prediction_value': 0  # sku 級別的總計
            }
        
        # 確保數值類型正確
        month_minus_1 = item.get('month_minus_1', 0)
        prediction_value = item.get('prediction_value', 0)
        
        # 轉換為整數，處理可能的字串或None值
        try:
            month_minus_1 = int(month_minus_1) if month_minus_1 is not None else 0
        except (ValueError, TypeError):
            month_minus_1 = 0
            
        try:
            prediction_value = int(prediction_value) if prediction_value is not None else 0
        except (ValueError, TypeError):
            prediction_value = 0
        
        # 獲取波動量 - 優先使用非空值
        item_volatility = item.get('volatility_group', '')
        if item_volatility and str(item_volatility).strip():
            subcategory_groups[subcategory]['volatility_group'] = str(item_volatility).strip()
        
        subcategory_groups[subcategory]['products'].append(item)
        
        # 分別處理 subcategory 和 sku 級別
        if item.get('prediction_level') == 'subcategory':
            subcategory_groups[subcategory]['has_subcategory_level'] = True
            subcategory_groups[subcategory]['total_month_minus_1'] = month_minus_1
            subcategory_groups[subcategory]['total_prediction_value'] = prediction_value
        elif item.get('prediction_level') == 'sku':
            subcategory_groups[subcategory]['sku_products'].append(item)
            subcategory_groups[subcategory]['sku_total_month_minus_1'] += month_minus_1
            subcategory_groups[subcategory]['sku_total_prediction_value'] += prediction_value
    
    # 決定最終顯示的總計：優先使用 SKU 總計以保持一致性
    for subcategory, group_data in subcategory_groups.items():
        if len(group_data['sku_products']) > 0:
            # 如果有 SKU 級別的產品，使用 SKU 總計以保持與詳細資料的一致性
            group_data['total_month_minus_1'] = group_data['sku_total_month_minus_1']
            group_data['total_prediction_value'] = group_data['sku_total_prediction_value']
        elif group_data['has_subcategory_level']:
            # 如果只有 subcategory 級別沒有 SKU，使用 subcategory 的值
            pass  # 已經在前面設定了
    
    # 建立表格內容
    table_content = []
    
    # 標題行
    header_row = html.Div([
        html.Div("子類別", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f8f9fa", "fontWeight": "bold", "textAlign": "center"}),
        html.Div("波動量", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f8f9fa", "fontWeight": "bold", "textAlign": "center"}),
        html.Div("上月銷量", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f8f9fa", "fontWeight": "bold", "textAlign": "center"}),
        html.Div("預測銷量", style={"flex": "1", "padding": "10px", "backgroundColor": "#f8f9fa", "fontWeight": "bold", "textAlign": "center"})
    ], style={"display": "flex", "border": "1px solid #ddd"})
    
    table_content.append(header_row)
    
    # 為每個子類別生成內容
    for i, (subcategory, group_data) in enumerate(subcategory_groups.items()):
        # 根據是否有多個 sku 級別的產品決定是否顯示箭頭和是否可點擊
        has_details = len(group_data['sku_products']) > 0
        
        if has_details:
            # 有子項目 - 可點擊的按鈕
            category_row = html.Button([
                html.Div([
                    html.Span(group_data['subcategory'], style={"marginRight": "8px"}),
                    html.Span("▼", 
                             id={'type': 'arrow', 'index': i},
                             style={"fontSize": "14px", "color": "#666", "transition": "all 0.3s ease"})
                ], style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "display": "flex", "alignItems": "center"}),
                html.Div(group_data['volatility_group'], style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd"}),
                html.Div(str(group_data['total_month_minus_1']), style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center"}),
                html.Div(str(group_data['total_prediction_value']), style={"flex": "1", "padding": "10px", "textAlign": "center"})
            ], style={
                "display": "flex", 
                "border": "1px solid #ddd", 
                "borderTop": "none", 
                "width": "100%", 
                "backgroundColor": "#ffffff", 
                "cursor": "pointer",
                "padding": "0"
            }, 
            id={'type': 'category-button', 'index': i})
        else:
            # 沒有子項目 - 普通的 div（不可點擊）
            category_row = html.Div([
                html.Div([
                    html.Span(group_data['subcategory'], style={"marginRight": "8px"}),
                    # 不顯示箭頭
                ], style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "display": "flex", "alignItems": "center"}),
                html.Div(group_data['volatility_group'], style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd"}),
                html.Div(str(group_data['total_month_minus_1']), style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center"}),
                html.Div(str(group_data['total_prediction_value']), style={"flex": "1", "padding": "10px", "textAlign": "center"})
            ], style={
                "display": "flex", 
                "border": "1px solid #ddd", 
                "borderTop": "none", 
                "width": "100%", 
                "backgroundColor": "#f9f9f9",  # 略微不同的背景色表示不可點擊
                "padding": "0"
            })
        
        table_content.append(category_row)
        
        # 只有當有 sku 級別的產品時才生成子項目
        if has_details:
            # 子項目 - 默認隱藏
            details_content = []
            
            # 子項目標題行
            sub_header = html.Div([
                html.Div("子類別", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                html.Div("產品id", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                html.Div("產品名稱", style={"flex": "2", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                html.Div("上月預測銷量", style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"}),
                html.Div("預測銷量", style={"flex": "1", "padding": "10px", "backgroundColor": "#f0f0f0", "fontWeight": "bold", "fontSize": "14px", "textAlign": "center"})
            ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none"})
            
            details_content.append(sub_header)
            
            # 只顯示 sku 級別的產品
            for product in group_data['sku_products']:
                # 確保產品資料的數值類型正確
                product_month_minus_1 = product.get('month_minus_1', 0)
                product_prediction_value = product.get('prediction_value', 0)
                
                try:
                    product_month_minus_1 = int(product_month_minus_1) if product_month_minus_1 is not None else 0
                except (ValueError, TypeError):
                    product_month_minus_1 = 0
                    
                try:
                    product_prediction_value = int(product_prediction_value) if product_prediction_value is not None else 0
                except (ValueError, TypeError):
                    product_prediction_value = 0
                
                product_row = html.Div([
                    html.Div(product.get('subcategory', ''), style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff", "textAlign": "center"}),
                    html.Div(product.get('product_id', ''), style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                    html.Div(product.get('product_name', ''), style={"flex": "2", "padding": "10px", "borderRight": "1px solid #ddd", "backgroundColor": "#ffffff"}),
                    html.Div(str(product_month_minus_1), style={"flex": "1", "padding": "10px", "borderRight": "1px solid #ddd", "textAlign": "center", "backgroundColor": "#ffffff"}),
                    html.Div(str(product_prediction_value), style={"flex": "1", "padding": "10px", "textAlign": "center", "backgroundColor": "#ffffff"})
                ], style={"display": "flex", "border": "1px solid #ddd", "borderTop": "none"})
                
                details_content.append(product_row)
            
            # 包裝子項目
            details_div = html.Div(details_content, id={'type': 'details', 'index': i}, style={"display": "none"})
            table_content.append(details_div)
    
    return html.Div(table_content, style={"marginBottom": "10px"}), len(subcategory_groups)

# 處理點擊事件以顯示/隱藏詳細資料和箭頭變化 - 使用動態 callback
@app.callback(
    [Output({'type': 'details', 'index': ALL}, 'style'),
     Output({'type': 'arrow', 'index': ALL}, 'children')],
    [Input({'type': 'category-button', 'index': ALL}, 'n_clicks')],
    [State({'type': 'details', 'index': ALL}, 'style'),
     State({'type': 'arrow', 'index': ALL}, 'children')],
    prevent_initial_call=True
)
def toggle_category_details(button_clicks, current_styles, current_arrows):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update] * len(current_styles), [dash.no_update] * len(current_arrows)
    
    # 找出被點擊的按鈕
    button_id = ctx.triggered[0]['prop_id']
    
    # 解析按鈕 ID 獲取索引
    import json
    try:
        button_data = json.loads(button_id.split('.')[0])
        clicked_index = button_data['index']
    except:
        return [dash.no_update] * len(current_styles), [dash.no_update] * len(current_arrows)
    
    # 準備返回值
    new_styles = []
    new_arrows = []
    
    for i in range(len(current_styles)):
        if i == clicked_index:
            # 切換被點擊的項目
            current_style = current_styles[i] if current_styles[i] else {"display": "none"}
            current_arrow = current_arrows[i] if current_arrows[i] else "▼"
            
            if current_style.get("display") == "none":
                new_styles.append({"display": "block"})
                new_arrows.append("▲")
            else:
                new_styles.append({"display": "none"})
                new_arrows.append("▼")
        else:
            # 保持其他項目不變
            new_styles.append(dash.no_update)
            new_arrows.append(dash.no_update)
    
    return new_styles, new_arrows