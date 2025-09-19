from dash import dash_table
from dash import html, dcc, dash_table, Input, Output, State, ctx, callback_context, exceptions

def get_row_background_color(row_data):
    """根據狀態決定行的背景顏色"""
    if '狀態' in row_data:
        if row_data['狀態'] == '已處理':
            return '#d4edda'  # 淺綠色
        elif row_data['狀態'] == '未處理':
            return '#f8d7da'  # 淺紅色
    return 'white'  # 默認白色

def custom_table(df, show_checkbox=False, show_button=False, button_text="操作", button_class="btn btn-warning btn-sm", button_id_type='status-button', sticky_columns=None, table_height='78vh', sortable_columns=None, sort_state=None):
    if sticky_columns is None:
        sticky_columns = []
    if sortable_columns is None:
        sortable_columns = []
    
    # 計算每個浮空欄位的最適寬度
    def calculate_column_width(col):
        # 計算標題寬度 (padding: 4px 8px = 16px)
        # 考慮中文字符較寬的問題
        col_str = str(col)
        char_width = sum(14 if ord(c) > 127 else 8 for c in col_str)  # 中文14px, 英文8px
        header_width = char_width + 16
        
        # 計算內容最大寬度
        max_content_width = 0
        for value in df[col]:
            value_str = str(value)
            value_char_width = sum(14 if ord(c) > 127 else 8 for c in value_str)  # 中文14px, 英文8px
            content_width = value_char_width + 16  # padding: 4px 8px = 16px
            max_content_width = max(max_content_width, content_width)
        
        # 取標題和內容的最大值，左右各加5px（總共15px），再加5px buffer，加2px邊框
        calculated_width = max(header_width, max_content_width) + 22
        return calculated_width
    
    # 計算所有浮空欄位的寬度
    sticky_widths = {}
    for col in sticky_columns:
        sticky_widths[col] = calculate_column_width(col)
    
    # 計算按鈕欄位寬度
    button_width = 100  # 固定按鈕欄位寬度
    
    rows = []

    for i, row in df.iterrows():
        row_cells = []
        
        if show_checkbox:
            checkbox = html.Td(
                dcc.Checklist(
                    id={'type': 'status-checkbox', 'index': i},
                    options=[{'label': '', 'value': i}],
                    value=[],
                    style={'margin': '0px'}
                ),
                style={
                    'padding': '4px 8px',
                    'textAlign': 'center',
                    'fontSize': '16px',
                    'height': '50px',
                    'minWidth': '50px',
                    'maxWidth': '50px',
                    'position': 'sticky',
                    'left': '0px',
                    'zIndex': 10,
                    'backgroundColor': '#edf7ff',
                    'border': '1px solid #ccc',
                    'boxShadow': '2px 0 5px rgba(0,0,0,0.1)' if len(sticky_columns) == 0 else 'none',
                    'overflow': 'hidden'
                }
            )
            row_cells.append(checkbox)
        
        sticky_col_data = []
        normal_col_data = []
        
        for col in                 ([col for col in df.columns if col in sticky_columns] + 
                 [col for col in df.columns if col not in sticky_columns]) if sticky_columns else df.columns:
            # 計算cell內容的寬度 - 取標題或內容的最大值，左右各加5px（總共15px），再加5px buffer，加2px邊框
            col_str = str(col)
            header_char_width = sum(14 if ord(c) > 127 else 8 for c in col_str)  # 中文14px, 英文8px
            header_width = header_char_width + 16
            
            row_value_str = str(row[col])
            content_char_width = sum(14 if ord(c) > 127 else 8 for c in row_value_str)  # 中文14px, 英文8px
            content_width = content_char_width + 16
            
            cell_width = max(header_width, content_width) + 22
            
            cell_style = {
                'padding': '4px 8px',
                'textAlign': 'center',
                'border': '1px solid #ccc',
                'fontSize': '16px',
                'height': '50px',
                'whiteSpace': 'nowrap',
                'backgroundColor': get_row_background_color(row) if col == '狀態' else 'white',
                'width': f'{cell_width}px',
                'minWidth': f'{cell_width}px',
                'maxWidth': f'{cell_width}px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            }
            
            if col in sticky_columns:
                sticky_index = sticky_columns.index(col)
                # 計算前面所有欄位的寬度總和（使用統一的寬度計算）
                left_offset = 0
                if show_checkbox:
                    left_offset += 50
                for j in range(sticky_index):
                    left_offset += sticky_widths[sticky_columns[j]]
                
                # 設定 sticky column 的背景顏色
                if col == '狀態':
                    sticky_bg_color = get_row_background_color(row)  # 狀態欄位使用顏色
                elif col == '提醒狀態':
                    if row[col] == '未提醒':
                        sticky_bg_color = '#ffebee'  # 淺紅色背景
                    elif row[col] == '已提醒':
                        sticky_bg_color = '#e8f5e8'  # 淺綠色背景
                else:
                    sticky_bg_color = "#edf7ff"  # 其他sticky欄位預設背景色

                # 右邊的 sticky column 應該有更高的 z-index
                sticky_z_index = 5 + sticky_index  # 第0個是5，第1個是6，以此類推
                
                cell_style.update({
                    'position': 'sticky',
                    'left': f'{left_offset}px',
                    'zIndex': sticky_z_index,
                    'backgroundColor': sticky_bg_color,
                    'width': f'{sticky_widths[col]}px',
                    'minWidth': f'{sticky_widths[col]}px',
                    'maxWidth': f'{sticky_widths[col]}px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis'
                })
                


                # 確保使用統一的寬度計算
                cell_width = sticky_widths[col]
                
                cell_content = row[col]
                    
                sticky_col_data.append(html.Td(cell_content, style=cell_style))
            else:
                cell_content = row[col]
                    
                normal_col_data.append(html.Td(cell_content, style=cell_style))
        
        row_cells.extend(sticky_col_data + normal_col_data)
        
        if show_button:
            button_props = {
                'id': {'type': button_id_type, 'index': i}, 
                'n_clicks': 0, 
                'className': button_class,
                'style': {'fontSize': '16px'}
            }
            
            button_right_position = '0px'
            
            row_cells.append(
                html.Td(
                    html.Button(button_text, **button_props),
                    style={
                        'padding': '4px 8px',
                        'textAlign': 'center',
                        'border': '1px solid #ccc',
                        'fontSize': '16px',
                        'height': '50px',
                        'whiteSpace': 'nowrap',
                        'position': 'sticky',
                        'right': button_right_position,
                        'zIndex': 0,
                        'backgroundColor': 'white',
                        'boxShadow': '-2px 0 5px rgba(0,0,0,0.1)',
                        'width': f'{button_width}px',
                        'minWidth': f'{button_width}px',
                        'maxWidth': f'{button_width}px',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis'
                    }
                )
            )
        
        # 添加主要行
        rows.append(html.Tr(row_cells, style={
            'backgroundColor': 'white'
        }))

    table = html.Table([
        html.Thead([
            html.Tr(
                ([html.Th('', style={
                    "position": "sticky",
                    "top": "0",
                    "left": "0px",
                    "zIndex": 10,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '4px 8px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc',
                    'borderTop': '0',
                    'width': '50px',
                    'boxShadow': '2px 0 5px rgba(0,0,0,0.1)' if len(sticky_columns) == 0 else 'none'
                })] if show_checkbox else []) +
                [html.Th(
                    html.Button(
                        html.Div([
                            html.Span(col, style={"marginRight": "8px"}),
                            html.Div([
                                html.Div("▲", style={
                                    "margin": "0",
                                    "lineHeight": "0.8",
                                    "fontSize": "12px",
                                    "color": "#cc5500" if sort_state and sort_state.get("column") == col and sort_state.get("ascending", True) else "#666"
                                }),
                                html.Div("▼", style={
                                    "margin": "0",
                                    "lineHeight": "0.8",
                                    "fontSize": "12px",
                                    "color": "#cc5500" if sort_state and sort_state.get("column") == col and not sort_state.get("ascending", True) else "#666"
                                })
                            ], style={
                                "display": "flex",
                                "flexDirection": "column",
                                "alignItems": "center"
                            })
                        ], style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "width": "100%"
                        }),
                        id={"type": "sort-button", "column": col},
                        style={
                            "background": "transparent",
                            "border": "none",
                            "color": "inherit",
                            "fontWeight": "bold",
                            "fontSize": "16px",
                            "cursor": "pointer",
                            "width": "100%",
                            "textAlign": "center"
                        }
                    ) if col in sortable_columns else col,
                    style={
                        "position": "sticky",
                        "top": "0",
                        "left": f'{(50 if show_checkbox else 0) + sum(sticky_widths[sticky_columns[j]] for j in range(sticky_columns.index(col)))}px' if col in sticky_columns else 'auto',
                        "zIndex": (10 + sticky_columns.index(col)) if col in sticky_columns else 1,
                        'backgroundColor': '#bcd1df',
                        'fontWeight': 'bold',
                        'fontSize': '16px',
                        'padding': '8px 12px' if col not in sortable_columns else '4px 8px',
                        'textAlign': 'center',
                        'border': '1px solid #ccc',
                        'borderTop': '0',
                        'whiteSpace': 'nowrap',
                        'width': f'{sticky_widths[col]}px' if col in sticky_columns else 'max-content',
                        'minWidth': f'{sticky_widths[col]}px' if col in sticky_columns else '80px',
                        'boxShadow': '2px 0 5px rgba(0,0,0,0.1)' if col in sticky_columns else 'none'
                    }
                ) for col in df.columns] +
                ([html.Th('操作', style={
                    "position": "sticky",
                    "top": "0",
                    "right": "0px",
                    "zIndex": 2,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '4px 8px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc',
                    'borderTop': '0',
                    'whiteSpace': 'nowrap',
                    'boxShadow': '-2px 0 5px rgba(0,0,0,0.1)',
                    'width': f'{button_width}px',
                    'minWidth': f'{button_width}px'
                })] if show_button else [])
            )
        ],style={
            # 新增：確保表格頭部緊貼容器頂部
            'margin': '0',
            'padding': '0',
            'position': 'sticky',
            'top': '0',
            'zIndex': 10
        }),
        html.Tbody(rows, style={
            # 新增：確保表格內容無間隙
            'margin': '0',
            'padding': '0'
        })
    ], style={
        "width": "max-content",  # 讓表格根據內容自動調整寬度
        "minWidth": "100%",      # 最小寬度為容器寬度
        "borderCollapse": "collapse",
        'border': '1px solid #ccc',
        'borderTop': '0',
        'margin': '0',       
        'padding': '0',
        "borderSpacing": "0px",
        'display': 'table',
        'tableLayout': 'auto'
    })

    table_div = html.Div([
        table
    ], style={
        'overflowY': 'auto',
        'overflowX': 'auto',
        'maxHeight': table_height,
        'minHeight': table_height,
        'display': 'block',
        'position': 'relative',
        'width': '100%',  # 確保容器寬度
        'maxWidth': '100%',  # 防止容器超出父容器
        'border': '2px solid #dee2e6',        # 新增：外框
        'borderRadius': '8px',                 # 裁掉溢出內容以保留圓角
        'padding': '0',                      # 新增：移除內邊距
        'margin': '0',
        'lineHeight': '1',
        'fontSize': '0',
        "borderSpacing": "0px",
        'boxSizing': 'border-box',            
        'background': 'white'
        
    })
    
    return table_div
