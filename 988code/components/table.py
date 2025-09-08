from dash import dash_table
from dash import html, dcc, dash_table, Input, Output, State, ctx, callback_context, exceptions

# 解決方案：重新設計表格結構，將 sticky header 提取到 overflow 容器之外

def custom_table(df, show_checkbox=False, show_button=False, button_text="操作", button_class="btn btn-warning btn-sm", button_id_type='status-button', sticky_columns=None, table_height='78vh', sortable_columns=None, sort_state=None):
    if sticky_columns is None:
        sticky_columns = []
    if sortable_columns is None:
        sortable_columns = []
    
    # ... (保持原有的計算函數不變)
    def calculate_column_width(col):
        col_str = str(col)
        char_width = sum(14 if ord(c) > 127 else 8 for c in col_str)
        header_width = char_width + 16
        
        max_content_width = 0
        for value in df[col]:
            value_str = str(value)
            value_char_width = sum(14 if ord(c) > 127 else 8 for c in value_str)
            content_width = value_char_width + 16
            max_content_width = max(max_content_width, content_width)
        
        calculated_width = max(header_width, max_content_width) + 22
        return calculated_width
    
    sticky_widths = {}
    for col in sticky_columns:
        sticky_widths[col] = calculate_column_width(col)
    
    button_width = 100
    
    # 建立 header 行（固定在外部）
    header_cells = []
    
    if show_checkbox:
        header_cells.append(html.Th('', style={
            'backgroundColor': '#bcd1df',
            'fontWeight': 'bold',
            'fontSize': '16px',
            'padding': '4px 8px',
            'textAlign': 'center',
            'border': '1px solid #ccc',
            'width': '50px',
            'minWidth': '50px'
        }))
    
    for col in df.columns:
        header_cells.append(html.Th(
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
                'backgroundColor': '#bcd1df',
                'fontWeight': 'bold',
                'fontSize': '16px',
                'padding': '8px 12px' if col not in sortable_columns else '4px 8px',
                'textAlign': 'center',
                'border': '1px solid #ccc',
                'whiteSpace': 'nowrap',
                'width': f'{sticky_widths[col]}px' if col in sticky_columns else 'max-content',
                'minWidth': f'{sticky_widths[col]}px' if col in sticky_columns else '80px',
            }
        ))
    
    if show_button:
        header_cells.append(html.Th('操作', style={
            'backgroundColor': '#bcd1df',
            'fontWeight': 'bold',
            'fontSize': '16px',
            'padding': '4px 8px',
            'textAlign': 'center',
            'border': '1px solid #ccc',
            'whiteSpace': 'nowrap',
            'width': f'{button_width}px',
            'minWidth': f'{button_width}px'
        }))

    # 建立固定的 header 表格
    header_table = html.Table([
        html.Thead([
            html.Tr(header_cells, style={
                'position': 'sticky',
                'top': '0px',
                'zIndex': 1000,
                'backgroundColor': '#bcd1df'
            })
        ])
    ], style={
        "width": "100%",
        "borderCollapse": "collapse",
        'border': '1px solid #ccc',
        'borderBottom': 'none',
        'position': 'sticky',
        'top': '0px',
        'zIndex': 1000,
        'backgroundColor': '#bcd1df'
    })

    # 建立 body 行（原有的 rows 邏輯）
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
                    'overflow': 'hidden'
                }
            )
            row_cells.append(checkbox)
        
        # 處理其他欄位（保持原有邏輯但移除 header 相關的 sticky）
        for col in ([col for col in df.columns if col in sticky_columns] + 
                   [col for col in df.columns if col not in sticky_columns]) if sticky_columns else df.columns:
            
            cell_style = {
                'padding': '4px 8px',
                'textAlign': 'center',
                'border': '1px solid #ccc',
                'fontSize': '16px',
                'height': '50px',
                'whiteSpace': 'nowrap',
                'backgroundColor': 'white',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            }
            
            if col in sticky_columns:
                sticky_index = sticky_columns.index(col)
                left_offset = 0
                if show_checkbox:
                    left_offset += 50
                for j in range(sticky_index):
                    left_offset += sticky_widths[sticky_columns[j]]
                
                cell_style.update({
                    'position': 'sticky',
                    'left': f'{left_offset}px',
                    'zIndex': 5 + sticky_index,
                    'backgroundColor': "#edf7ff",
                    'width': f'{sticky_widths[col]}px',
                    'minWidth': f'{sticky_widths[col]}px',
                    'maxWidth': f'{sticky_widths[col]}px',
                })
            
            row_cells.append(html.Td(row[col], style=cell_style))
        
        if show_button:
            row_cells.append(
                html.Td(
                    html.Button(button_text, 
                               id={'type': button_id_type, 'index': i}, 
                               n_clicks=0, 
                               className=button_class,
                               style={'fontSize': '16px'}),
                    style={
                        'padding': '4px 8px',
                        'textAlign': 'center',
                        'border': '1px solid #ccc',
                        'fontSize': '16px',
                        'height': '50px',
                        'whiteSpace': 'nowrap',
                        'position': 'sticky',
                        'right': '0px',
                        'zIndex': 2,
                        'backgroundColor': 'white',
                        'boxShadow': '-2px 0 5px rgba(0,0,0,0.1)',
                        'width': f'{button_width}px',
                        'minWidth': f'{button_width}px',
                        'maxWidth': f'{button_width}px',
                    }
                )
            )
        
        rows.append(html.Tr(row_cells, style={'backgroundColor': 'white'}))

    # 建立 body 表格（可捲動）
    body_table = html.Table([
        html.Tbody(rows)
    ], style={
        "width": "100%",
        "borderCollapse": "collapse",
        'border': '1px solid #ccc',
        'borderTop': 'none'
    })

    # 組合最終結構
    table_div = html.Div([
        # 固定的 header
        header_table,
        # 可捲動的 body
        html.Div([
            body_table
        ], style={
            'overflowY': 'auto',
            'overflowX': 'auto',
            'maxHeight': f'calc({table_height} - 51px)',  # 減去 header 高度
            'border': '1px solid #ccc',
            'borderTop': 'none'
        })
    ], style={
        'position': 'relative',
        'border': '1px solid #ccc',
        'borderRadius': '4px'
    })
    
    return table_div