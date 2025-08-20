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

def extract_areas_from_badges(badges):
    """
    從 badges 提取地區名稱和類型配對
    
    Parameters:
    - badges: badge HTML 結構列表
    
    Returns:
    - 列表格式: [(area_name, area_type), ...]
    """
    areas = []
    
    if not badges:
        return areas
        
    for badge in badges:
        if badge and 'props' in badge:
            # 提取地區名稱（現在直接從 span 內容取得，不需要解析前綴）
            area_name = None
            if 'children' in badge['props']:
                children = badge['props']['children']
                if isinstance(children, list) and len(children) > 0:
                    span_content = children[0]
                    if 'props' in span_content and 'children' in span_content['props']:
                        area_name = span_content['props']['children']
            
            # 提取地區類型
            area_type = badge['props'].get('data-area-type')
            
            if area_name and area_type:
                areas.append((area_name, area_type))
    
    return areas

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

def fetch_area_sales_data_by_groups(area_pairs, start_date, end_date):
    """
    按地區類型分組查詢銷售數據
    
    Parameters:
    - area_pairs: [(area_name, area_type), ...] 格式的地區列表
    - start_date: 開始日期
    - end_date: 結束日期
    
    Returns:
    - tuple: (合併後的銷售數據列表, 有資料的地區列表, 沒有資料的地區列表, 地區類型映射)
    """
    # 按地區類型分組
    groups = defaultdict(list)
    area_type_mapping = {}  # 地區名稱 -> 地區類型的映射
    
    for area_name, area_type in area_pairs:
        groups[area_type].append(area_name)
        area_type_mapping[area_name] = area_type
    
    # 映射前端地區類型到 API filter_level
    filter_level_mapping = {
        'county': 'city',      # 縣市 -> city
        'district': 'district'  # 地區 -> district
    }
    
    all_data = []
    areas_with_data = set()
    areas_without_data = []
    
    # 建立所有選中地區的集合
    all_selected_areas = {name for name, _ in area_pairs}
    
    # 為每個地區類型分組分別查詢
    for area_type, area_names in groups.items():
        api_filter_level = filter_level_mapping.get(area_type)
        if not api_filter_level:
            # 如果地區類型無效，這些地區都算沒有資料
            areas_without_data.extend(area_names)
            continue
            
        try:
            # 準備 API 請求數據
            request_data = {
                "filter_level": api_filter_level,
                "filter_values": area_names,
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
                    # 為每個數據項添加地區類型資訊
                    for item in group_data:
                        item['area_type'] = area_type
                    all_data.extend(group_data)
                    
                    # 記錄有資料的地區
                    for item in group_data:
                        areas_with_data.add(item['filter_value'])
                
                # 找出這個組中沒有資料的地區
                areas_in_response = {item['filter_value'] for item in group_data}
                no_data_in_group = set(area_names) - areas_in_response
                areas_without_data.extend(list(no_data_in_group))
                
            else:
                print(f"API 請求失敗，地區類型: {area_type}, 狀態碼: {response.status_code}")
                # API 失敗，這組的所有地區都算沒有資料
                areas_without_data.extend(area_names)
                
        except requests.exceptions.RequestException as e:
            print(f"API 請求異常，地區類型: {area_type}, 錯誤: {str(e)}")
            # API 異常，這組的所有地區都算沒有資料
            areas_without_data.extend(area_names)
        except Exception as e:
            print(f"處理地區類型 {area_type} 時發生錯誤: {str(e)}")
            # 處理異常，這組的所有地區都算沒有資料
            areas_without_data.extend(area_names)
    
    return all_data, list(areas_with_data), areas_without_data, area_type_mapping

def create_area_plotly_chart(data, start_date, end_date, all_selected_areas=None, area_type_mapping=None):
    """
    創建地區 Plotly 圖表
    
    Parameters:
    - data: 銷售數據列表
    - start_date: 開始日期
    - end_date: 結束日期
    - all_selected_areas: 所有選中的地區列表
    - area_type_mapping: 地區類型映射
    
    Returns:
    - Plotly 圖表組件
    """
    # 即使沒有原始數據，如果有選中的地區也要生成圖表
    if not data and not all_selected_areas:
        return html.Div([
            html.H5("沒有找到符合條件的資料", style={"textAlign": "center", "color": "#666", "marginTop": "50px"})
        ])
    
    # 轉換數據為 DataFrame
    df = pd.DataFrame(data) if data else pd.DataFrame()
    if not df.empty:
        df['sales_month'] = pd.to_datetime(df['sales_month'])
    
    # 如果有選中的地區，檢查並填補缺失的數據點
    if all_selected_areas:
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
        
        # 為缺失的地區-月份組合添加0值記錄
        zero_records = []
        
        # 獲取現有的地區-月份組合
        if not df.empty:
            existing_combinations = set((row['filter_value'], row['sales_month'].replace(day=1)) 
                                      for _, row in df.iterrows())
        else:
            existing_combinations = set()
        
        # 為所有選中的地區檢查每個月份
        for area_name in all_selected_areas:
            for month in months:
                combination = (area_name, month)
                if combination not in existing_combinations:
                    zero_records.append({
                        'sales_month': month,
                        'filter_value': area_name,
                        'total_amount': 0,
                        'area_type': area_type_mapping.get(area_name, 'district') if area_type_mapping else 'district'
                    })
        
        # 將0值記錄添加到DataFrame
        if zero_records:
            print(f"[DEBUG] 地區分析 - 添加 {len(zero_records)} 個0值數據點")
            zero_df = pd.DataFrame(zero_records)
            if df.empty:
                df = zero_df
            else:
                df = pd.concat([df, zero_df], ignore_index=True)
            df['sales_month'] = pd.to_datetime(df['sales_month'])
            
            # 排序數據以確保時間序列的連續性
            df = df.sort_values(['filter_value', 'sales_month']).reset_index(drop=True)
            print(f"[DEBUG] 地區數據已按地區名稱和時間排序")
        else:
            print(f"[DEBUG] 地區分析 - 沒有需要添加的0值數據點")
    
    # 分析地區名稱和數量（使用更新後的數據）
    unique_areas = df['filter_value'].unique() if not df.empty else []
    area_count = len(unique_areas)
    
    # 如果仍然沒有數據，返回空圖表提示
    if df.empty:
        return html.Div([
            html.H5("沒有找到符合條件的資料", style={"textAlign": "center", "color": "#666", "marginTop": "50px"})
        ])
    
    # 為每個地區添加類型前綴
    name_mapping = {}  # 帶前綴名稱 -> 原始名稱
    display_names = {}  # 原始名稱 -> 帶前綴名稱
    
    type_labels = {
        'county': '縣市',
        'district': '地區'
    }
    
    for area in unique_areas:
        # 獲取該地區的類型
        area_type = df[df['filter_value'] == area]['area_type'].iloc[0]
        type_label = type_labels.get(area_type, '未知')
        
        # 創建帶前綴的顯示名稱（用方括號包起來）
        full_name = f"[{type_label}] {area}"
        
        # 智慧換行：如果名稱過長，按字符數量切割
        if len(full_name) > 30:  # 超過30個字符就考慮換行
            lines = []
            current_line = ""
            
            # 逐字符處理
            for char in full_name:
                # 如果加上這個字符後會超過15個字符，就換行
                if len(current_line + char) > 15 and current_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    current_line += char
            
            # 加入最後一行
            if current_line:
                lines.append(current_line)
            
            # 用 <br> 連接多行
            display_name = '<br>'.join(lines) if len(lines) > 1 else full_name
        else:
            display_name = full_name
        
        name_mapping[display_name] = area
        display_names[area] = display_name
    
    # 創建新的 DataFrame 使用帶前綴的顯示名稱
    df_display = df.copy()
    df_display['display_name'] = df_display['filter_value'].map(display_names)
    
    # 圖表高度設定
    chart_height_plotly = 500  # plotly 內部使用的固定高度
    chart_height_css = "100%"  # CSS 樣式使用的響應式高度
    chart_width = "100%"  # 圖表寬度與容器一致
    
    # 垂直圖例配置：調整圖表與圖例的寬度比例
    legend_config = dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left", 
        x=1.02,  # 圖例放在圖表右側外面
        font=dict(
            size=10  # 較小的字體確保完整顯示
        ),
        itemwidth=30,  # 限制每個圖例項目的寬度
        tracegroupgap=5  # 圖例項目間距
    )
    
    # 調整邊距：為圖例預留足夠的右邊距空間
    margin_config = dict(l=40, r=200, t=40, b=40)
    
    # 自動生成標題，包含分析期間
    chart_title = f"地區銷售趨勢分析 ({start_date} 至 {end_date})"
    
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
            'display_name': '地區'
        }
    )
    
    # 添加調試信息（開發時使用）
    print(f"[DEBUG] 地區圖表生成 - 地區數量: {area_count}")
    print(f"[DEBUG] 地區圖表生成 - 地區列表: {list(unique_areas)}")
    print(f"[DEBUG] 地區圖表生成 - 圖表線條數量: {len(fig.data)}")
    
    # 美化圖表，恢復原生圖例
    fig.update_layout(
        xaxis_title="銷售月份",
        yaxis_title="銷售金額 (元)",
        hovermode='x unified',
        legend=legend_config,
        height=chart_height_plotly,
        margin=margin_config,
        xaxis=dict(
            tickformat='%Y年%m月'  # 橫軸顯示中文格式：2025年01月
        )
    )
    
    # 根據地區類型設定線條樣式
    type_line_styles = {
        'county': 'solid',    # 縣市：實線
        'district': 'dash'    # 地區：虛線
    }
    
    for trace in fig.data:
        display_name = trace.name
        # 獲取原始地區名稱用於 hover
        original_name = name_mapping.get(display_name, display_name)
        
        # 找到該地區的類型
        area_type = df[df['filter_value'] == original_name]['area_type'].iloc[0]
        line_style = type_line_styles.get(area_type, 'solid')
        
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
    download_filename = f"{start_formatted}~{end_formatted}地區銷售分析"
    
    return dcc.Graph(
        figure=fig, 
        style={"height": chart_height_css, "width": chart_width},
        config={
            'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d'],
            'displaylogo': False,
            'displayModeBar': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': download_filename,
                'height': chart_height_plotly,
                'width': 1200,
                'scale': 1
            }
        }
    )

@app.callback(
    Output('area-selected-items-container', 'children'),
    Input('area-generate-chart-button', 'n_clicks'),
    [State('area-badges-container', 'children'),
     State('area-start-date', 'value'),
     State('area-end-date', 'value')],
    prevent_initial_call=True
)
def generate_area_chart(n_clicks, badges, start_date, end_date):
    """
    生成地區圖表的主要 callback 函數
    """
    if not n_clicks:
        return []
    
    # 檢查是否有選中的地區
    area_pairs = extract_areas_from_badges(badges)
    
    if not area_pairs:
        return [
            html.Div([
                html.H5("請先選擇要分析的地區", 
                       style={"textAlign": "center", "color": "#ff6b6b", "marginTop": "50px"}),
                html.P("請在左側選擇縣市或地區後點擊對應的「新增」按鈕",
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
        chart_data, areas_with_data, areas_without_data, area_type_mapping = fetch_area_sales_data_by_groups(area_pairs, api_start_date, api_end_date)
        
        # 即使沒有數據，也要生成圖表顯示0值線條
        # if not chart_data:
        #     return [
        #         html.Div([
        #             html.H5("沒有找到符合條件的銷售資料", 
        #                    style={"textAlign": "center", "color": "#ffa500", "marginTop": "50px"}),
        #             html.P(f"時間範圍: {start_date} 至 {end_date}",
        #                   style={"textAlign": "center", "color": "#666"}),
        #             html.P(f"選中地區: {', '.join([name for name, _ in area_pairs])}",
        #                   style={"textAlign": "center", "color": "#666"})
        #         ])
        #     ]
        
        # 生成圖表
        all_selected_area_names = [name for name, _ in area_pairs]
        chart = create_area_plotly_chart(chart_data, start_date, end_date, all_selected_area_names, area_type_mapping)
        
        # 創建數據摘要
        df = pd.DataFrame(chart_data)
        total_sales = df['total_amount'].sum() if not df.empty and 'total_amount' in df.columns else 0
        date_range = f"{start_date} 至 {end_date}"
        
        # 統計各地區類型數量
        type_counts = defaultdict(int)
        for _, area_type in area_pairs:
            type_names = {
                'county': '縣市',
                'district': '地區'
            }
            type_counts[type_names.get(area_type, area_type)] += 1
        
        type_summary = ", ".join([f"{type_name}: {count}" for type_name, count in type_counts.items()])
        
        # 創建標題和警告信息
        title_components = []
        
        # 如果有地區沒有資料，顯示警告信息
        if areas_without_data:
            warning_text = f"⚠️ 以下地區沒有銷售資料：{', '.join(areas_without_data)}"
            title_components.append(
                html.P(warning_text, style={
                    "textAlign": "center", 
                    "color": "#856404", 
                    "fontWeight": "bold", 
                    "fontSize": "14px",
                    "marginBottom": "15px",
                    "backgroundColor": "#fff3cd",
                    "padding": "8px 12px",
                    "borderRadius": "4px",
                    "border": "1px solid #ffeaa7"
                })
            )
        
        title_section = html.Div(title_components, style={"marginBottom": "15px"})
        
        return [title_section, chart]
        
    except Exception as e:
        return [
            html.Div([
                html.H5("處理數據時發生錯誤", 
                       style={"textAlign": "center", "color": "#ff6b6b", "marginTop": "50px"}),
                html.P(f"錯誤詳情: {str(e)}",
                      style={"textAlign": "center", "color": "#666"})
            ])
        ]