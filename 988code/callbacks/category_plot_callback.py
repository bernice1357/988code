from .common import *
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import json
from collections import defaultdict

# API 服務器配置
API_BASE_URL = "http://127.0.0.1:8000"

def extract_products_from_badges(badges):
    """
    從 badges 提取產品名稱和類型配對
    
    Parameters:
    - badges: badge HTML 結構列表
    
    Returns:
    - 列表格式: [(product_name, product_type), ...]
    """
    products = []
    
    print(f"[DEBUG] extract_products_from_badges - 輸入 badges 數量: {len(badges) if badges else 0}")
    
    if not badges:
        return products
        
    for i, badge in enumerate(badges):
        if badge and 'props' in badge:
            # 提取產品名稱
            product_name = None
            if 'children' in badge['props']:
                children = badge['props']['children']
                if isinstance(children, list) and len(children) > 0:
                    span_content = children[0]
                    if 'props' in span_content and 'children' in span_content['props']:
                        product_name = span_content['props']['children']
            
            # 提取產品類型
            product_type = badge['props'].get('data-product-type')
            
            if product_name and product_type:
                products.append((product_name, product_type))
                print(f"[DEBUG] extract_products_from_badges - 第 {i+1} 個產品: {product_name} ({product_type})")
            else:
                print(f"[DEBUG] extract_products_from_badges - 第 {i+1} 個 badge 解析失敗: name={product_name}, type={product_type}")
    
    print(f"[DEBUG] extract_products_from_badges - 最終提取到的產品: {products}")
    return products

def convert_date_to_api_format(date_value, is_end_date=False):
    """
    將月份格式轉換為 API 需要的日期格式
    
    Parameters:
    - date_value: YYYY-MM 格式的日期字符串
    - is_end_date: 是否為結束日期，True 時轉換為該月最後一天
    
    Returns:
    - YYYY-MM-DD 格式的日期字符串
    """
    if not date_value:
        return None
    
    try:
        # 如果已經是 YYYY-MM-DD 格式，直接返回
        if len(date_value.split('-')) == 3:
            return date_value
        
        # 如果是 YYYY-MM 格式
        if is_end_date:
            # 結束日期：轉換為該月最後一天
            from datetime import datetime
            import calendar
            
            year, month = map(int, date_value.split('-'))
            last_day = calendar.monthrange(year, month)[1]
            return f"{year}-{month:02d}-{last_day:02d}"
        else:
            # 開始日期：轉換為該月第一天
            return f"{date_value}-01"
    except:
        return None

def fetch_sales_data_by_groups(product_pairs, start_date, end_date):
    """
    按產品類型分組查詢銷售數據
    
    Parameters:
    - product_pairs: [(product_name, product_type), ...] 格式的產品列表
    - start_date: 開始日期
    - end_date: 結束日期
    
    Returns:
    - tuple: (合併後的銷售數據列表, 有資料的產品列表, 沒有資料的產品列表, 產品類型映射)
    """
    # 按產品類型分組
    groups = defaultdict(list)
    product_type_mapping = {}  # 產品名稱 -> 產品類型的映射
    
    for product_name, product_type in product_pairs:
        groups[product_type].append(product_name)
        product_type_mapping[product_name] = product_type
    
    # 映射前端產品類型到 API filter_level
    filter_level_mapping = {
        'category': 'category',
        'subcategory': 'subcategory', 
        'item': 'name_zh'
    }
    
    all_data = []
    products_with_data = set()
    products_without_data = []
    
    # 建立所有選中產品的集合
    all_selected_products = {name for name, _ in product_pairs}
    
    # 為每個產品類型分組分別查詢
    for product_type, product_names in groups.items():
        api_filter_level = filter_level_mapping.get(product_type)
        if not api_filter_level:
            # 如果產品類型無效，這些產品都算沒有資料
            products_without_data.extend(product_names)
            continue
            
        try:
            # 準備 API 請求數據
            request_data = {
                "filter_level": api_filter_level,
                "filter_values": product_names,
                "start_date": start_date,
                "end_date": end_date
            }
            
            # 調用 API
            response = requests.post(
                f"{API_BASE_URL}/get_sales_data",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                api_result = response.json()
                group_data = api_result.get('data', [])
                
                if group_data:
                    # 為每個數據項添加產品類型資訊
                    for item in group_data:
                        item['product_type'] = product_type
                    all_data.extend(group_data)
                    
                    # 記錄有資料的產品
                    for item in group_data:
                        products_with_data.add(item['filter_value'])
                
                # 找出這個組中沒有資料的產品
                products_in_response = {item['filter_value'] for item in group_data}
                no_data_in_group = set(product_names) - products_in_response
                products_without_data.extend(list(no_data_in_group))
                
            else:
                print(f"API 請求失敗，產品類型: {product_type}, 狀態碼: {response.status_code}")
                # API 失敗，這組的所有產品都算沒有資料
                products_without_data.extend(product_names)
                
        except requests.exceptions.RequestException as e:
            print(f"API 請求異常，產品類型: {product_type}, 錯誤: {str(e)}")
            # API 異常，這組的所有產品都算沒有資料
            products_without_data.extend(product_names)
        except Exception as e:
            print(f"處理產品類型 {product_type} 時發生錯誤: {str(e)}")
            # 處理異常，這組的所有產品都算沒有資料
            products_without_data.extend(product_names)
    
    return all_data, list(products_with_data), products_without_data, product_type_mapping


def create_plotly_chart(data, start_date, end_date, all_selected_products=None, product_type_mapping=None):
    """
    創建 Plotly 圖表
    
    Parameters:
    - data: 銷售數據列表
    - start_date: 開始日期
    - end_date: 結束日期
    - all_selected_products: 所有選中的產品列表
    - product_type_mapping: 產品類型映射
    
    Returns:
    - Plotly 圖表組件
    """
    # 即使沒有原始數據，如果有選中的產品也要生成圖表
    if not data and not all_selected_products:
        return html.Div([
            html.H5("沒有找到符合條件的資料", style={"textAlign": "center", "color": "#666", "marginTop": "50px"})
        ])
    
    # 轉換數據為 DataFrame
    df = pd.DataFrame(data) if data else pd.DataFrame()
    if not df.empty:
        df['sales_month'] = pd.to_datetime(df['sales_month'])
    
    # 如果有選中的產品，檢查並填補缺失的數據點
    if all_selected_products:
        # 生成日期範圍
        from datetime import datetime
        import calendar
        
        # 解析開始和結束日期
        start_dt = datetime.strptime(start_date, '%Y-%m')
        end_dt = datetime.strptime(end_date, '%Y-%m')
        
        # 生成月份列表
        months = []
        current = start_dt
        while current <= end_dt:
            months.append(current.replace(day=1))
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        # 為缺失的產品-月份組合添加0值記錄
        zero_records = []
        
        # 獲取現有的產品-月份組合
        if not df.empty:
            existing_combinations = set((row['filter_value'], row['sales_month'].replace(day=1)) 
                                      for _, row in df.iterrows())
        else:
            existing_combinations = set()
        
        # 為所有選中的產品檢查每個月份
        for product_name in all_selected_products:
            for month in months:
                combination = (product_name, month)
                if combination not in existing_combinations:
                    zero_records.append({
                        'sales_month': month,
                        'filter_value': product_name,
                        'total_amount': 0,
                        'product_type': product_type_mapping.get(product_name, 'item') if product_type_mapping else 'item'
                    })
        
        # 將0值記錄添加到DataFrame
        if zero_records:
            print(f"[DEBUG] 添加 {len(zero_records)} 個0值數據點")
            zero_df = pd.DataFrame(zero_records)
            if df.empty:
                df = zero_df
            else:
                df = pd.concat([df, zero_df], ignore_index=True)
            df['sales_month'] = pd.to_datetime(df['sales_month'])
        else:
            print(f"[DEBUG] 沒有需要添加的0值數據點")
    
    # 分析產品名稱和數量（使用更新後的數據）
    unique_products = df['filter_value'].unique() if not df.empty else []
    product_count = len(unique_products)
    
    # 如果仍然沒有數據，返回空圖表提示
    if df.empty:
        return html.Div([
            html.H5("沒有找到符合條件的資料", style={"textAlign": "center", "color": "#666", "marginTop": "50px"})
        ])
    
    # 檢查每個產品的資料點數量和數值範圍
    for product in unique_products:
        product_data = df[df['filter_value'] == product]
    
    # 為每個產品添加類型前綴
    name_mapping = {}  # 帶前綴名稱 -> 原始名稱
    display_names = {}  # 原始名稱 -> 帶前綴名稱
    
    type_labels = {
        'category': '類別',
        'subcategory': '子類別',
        'item': '品項'
    }
    
    for product in unique_products:
        # 獲取該產品的類型
        product_type = df[df['filter_value'] == product]['product_type'].iloc[0]
        type_label = type_labels.get(product_type, '未知')
        
        # 創建帶前綴的顯示名稱（用方括號包起來）
        display_name = f"[{type_label}] {product}"
        name_mapping[display_name] = product
        display_names[product] = display_name
    
    # 創建新的 DataFrame 使用帶前綴的顯示名稱
    df_display = df.copy()
    df_display['display_name'] = df_display['filter_value'].map(display_names)
    
    # 統一使用垂直圖例，根據產品數量調整高度
    chart_height = max(500, 400 + product_count * 20)  # 每個產品約20px高度
    chart_width = "100%"
    
    # 垂直圖例配置：字體較小但顯示完整名稱
    legend_config = dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left", 
        x=1.02,
        font=dict(
            size=10  # 較小的字體確保完整顯示
        )
    )
    
    # 增加右邊距給圖例預留足夠空間
    margin_config = dict(l=0, r=200, t=40, b=0)
    
    # 自動生成標題，包含分析期間
    chart_title = f"銷售分析圖表 ({start_date} 至 {end_date})"
    
    # 建立折線圖（使用帶前綴的顯示名稱）
    # 為了確保支持更多顏色，使用完整的顏色序列
    colors = px.colors.qualitative.Plotly + px.colors.qualitative.Set1 + px.colors.qualitative.Set2
    
    fig = px.line(
        df_display, 
        x='sales_month', 
        y='total_amount', 
        color='display_name',
        title=chart_title,
        color_discrete_sequence=colors,  # 明確指定顏色序列
        labels={
            'sales_month': '銷售月份',
            'total_amount': '銷售金額 (元)',
            'display_name': '產品'
        }
    )
    
    # 添加調試信息（開發時使用）
    print(f"[DEBUG] 圖表生成 - 產品數量: {product_count}")
    print(f"[DEBUG] 圖表生成 - 產品列表: {list(unique_products)}")
    print(f"[DEBUG] 圖表生成 - 圖表線條數量: {len(fig.data)}")
    
    # 美化圖表，恢復原生圖例
    fig.update_layout(
        xaxis_title="銷售月份",
        yaxis_title="銷售金額 (元)",
        hovermode='x unified',
        legend=legend_config,
        height=chart_height,
        margin=margin_config
    )
    
    # 根據產品類型設定線條樣式
    type_line_styles = {
        'category': 'solid',     # 類別：實線
        'subcategory': 'dash',   # 子類別：虛線
        'item': 'dot'           # 品項：點線
    }
    
    for trace in fig.data:
        display_name = trace.name
        # 獲取原始產品名稱用於 hover
        original_name = name_mapping.get(display_name, display_name)
        
        # 找到該產品的類型
        product_type = df[df['filter_value'] == original_name]['product_type'].iloc[0]
        line_style = type_line_styles.get(product_type, 'solid')
        
        trace.update(
            mode='lines+markers',
            line=dict(dash=line_style),
            hovertemplate=f'<b>{original_name}</b><br>' +
                         '月份: %{x|%Y-%m}<br>' +
                         '銷售金額: NT$ %{y:,.0f}<extra></extra>'
        )
    
    # 生成下載檔名
    start_formatted = start_date.replace('-', '/')
    end_formatted = end_date.replace('-', '/')
    download_filename = f"{start_formatted}~{end_formatted}銷售分析"
    
    return dcc.Graph(
        figure=fig, 
        style={"height": f"{chart_height}px", "width": chart_width},
        config={
            'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d'],
            'displaylogo': False,
            'displayModeBar': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': download_filename,
                'height': chart_height,
                'width': 1200,
                'scale': 1
            }
        }
    )

@app.callback(
    Output('item-selected-items-container', 'children'),
    Input('item-generate-chart-button', 'n_clicks'),
    [State('item-badges-container', 'children'),
     State('item-start-date', 'value'),
     State('item-end-date', 'value'),
     State('item-radio-options', 'value')],
    prevent_initial_call=True
)
def generate_chart(n_clicks, badges, start_date, end_date, radio_value):
    """
    生成圖表的主要 callback 函數
    """
    if not n_clicks:
        return []
    
    # 檢查是否有選中的產品
    product_pairs = extract_products_from_badges(badges)
    
    # 添加調試信息
    print(f"[DEBUG] 生成圖表 - 選中的產品對: {product_pairs}")
    print(f"[DEBUG] 生成圖表 - 產品數量: {len(product_pairs)}")
    
    if not product_pairs:
        return [
            html.Div([
                html.H5("請先選擇要分析的產品", 
                       style={"textAlign": "center", "color": "#ff6b6b", "marginTop": "50px"}),
                html.P("請在左側選擇產品類別、子類別或品項後點擊「新增」",
                      style={"textAlign": "center", "color": "#666"})
            ])
        ]
    
    # 檢查日期格式
    api_start_date = convert_date_to_api_format(start_date, is_end_date=False)
    api_end_date = convert_date_to_api_format(end_date, is_end_date=True)
    
    if not api_start_date or not api_end_date:
        return [
            html.Div([
                html.H5("日期格式錯誤", 
                       style={"textAlign": "center", "color": "#ff6b6b", "marginTop": "50px"}),
                html.P("請檢查開始日期和結束日期",
                      style={"textAlign": "center", "color": "#666"})
            ])
        ]
    
    try:
        # 使用新的分組查詢邏輯
        chart_data, products_with_data, products_without_data, product_type_mapping = fetch_sales_data_by_groups(product_pairs, api_start_date, api_end_date)
        
        # 添加調試信息
        print(f"[DEBUG] 數據獲取 - 總數據筆數: {len(chart_data)}")
        print(f"[DEBUG] 數據獲取 - 有數據的產品: {products_with_data}")
        print(f"[DEBUG] 數據獲取 - 無數據的產品: {products_without_data}")
        
        # 即使沒有數據，也要生成圖表顯示0值線條
        # if not chart_data:
        #     return [
        #         html.Div([
        #             html.H5("沒有找到符合條件的銷售資料", 
        #                    style={"textAlign": "center", "color": "#ffa500", "marginTop": "50px"}),
        #             html.P(f"時間範圍: {start_date} 至 {end_date}",
        #                   style={"textAlign": "center", "color": "#666"}),
        #             html.P(f"選中產品: {', '.join([name for name, _ in product_pairs])}",
        #                   style={"textAlign": "center", "color": "#666"})
        #         ])
        #     ]
        
        # 生成圖表
        all_selected_product_names = [name for name, _ in product_pairs]
        chart = create_plotly_chart(chart_data, start_date, end_date, all_selected_product_names, product_type_mapping)
        
        # 創建數據摘要
        df = pd.DataFrame(chart_data)
        total_sales = df['total_amount'].sum()
        date_range = f"{start_date} 至 {end_date}"
        
        # 統計各產品類型數量
        type_counts = defaultdict(int)
        for _, product_type in product_pairs:
            type_names = {
                'category': '類別',
                'subcategory': '子類別', 
                'item': '品項'
            }
            type_counts[type_names.get(product_type, product_type)] += 1
        
        type_summary = ", ".join([f"{type_name}: {count}" for type_name, count in type_counts.items()])
        
        # 準備 Popover 內容（資料摘要）
        popover_content = [
            html.P(f"產品統計: {type_summary}", style={"margin": "5px 0"}),
        ]
        
        # 如果有產品有資料，顯示銷售額
        if products_with_data:
            popover_content.append(
                html.P(f"總銷售額: NT$ {total_sales:,.0f}", style={"margin": "5px 0", "fontWeight": "bold"})
            )
        
        # 如果有產品沒有資料，顯示提醒
        if products_without_data:
            popover_content.extend([
                html.Hr(style={"margin": "8px 0"}),
                html.P("⚠️ 以下產品沒有銷售資料:", 
                      style={"margin": "5px 0", "color": "#856404", "fontWeight": "bold", "fontSize": "12px"}),
                html.P(f"{', '.join(products_without_data)}", 
                      style={"margin": "2px 0", "color": "#856404", "fontStyle": "italic", "fontSize": "11px"})
            ])
        
        # 創建標題列（標題 + 資料摘要按鈕）
        title_row = html.Div([
            html.H4("銷售分析圖表", style={"margin": "0 10px 0 0", "color": "#333"}),
            dbc.Button(
                html.I(className="fas fa-chart-bar"),
                id="data-summary-popover-button",
                color="dark",
                size="sm",
                outline=True,
                style={"fontSize": "14px", "padding": "4px 8px"}
            )
        ], style={
            "display": "flex", 
            "justifyContent": "center", 
            "alignItems": "center",
            "marginBottom": "15px",
            "padding": "0"
        })
        
        # 創建 Popover
        popover = dbc.Popover(
            popover_content,
            target="data-summary-popover-button",
            trigger="legacy",
            placement="left",
            style={"maxWidth": "350px"},
            hide_arrow=False
        )
        
        return [title_row, chart, popover]
        
    except Exception as e:
        return [
            html.Div([
                html.H5("處理數據時發生錯誤", 
                       style={"textAlign": "center", "color": "#ff6b6b", "marginTop": "50px"}),
                html.P(f"錯誤詳情: {str(e)}",
                      style={"textAlign": "center", "color": "#666"})
            ])
        ]