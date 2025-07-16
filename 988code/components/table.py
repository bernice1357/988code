from dash import dash_table
from dash import html, dcc, dash_table, Input, Output, State, ctx, callback_context, exceptions

# TODO 要把欄位標題做懸空的
def custom_table(df, show_checkbox=False, show_button=False, button_text="操作", button_class="btn btn-warning btn-sm", button_id_type='status-button', sticky_columns=None):
    if sticky_columns is None:
        sticky_columns = []
    
    # 計算每個浮空欄位的最適寬度
    def calculate_column_width(col):
        # 計算標題寬度 (padding: 8px 12px = 24px)
        header_width = len(str(col)) * 12 + 24
        
        # 計算內容最大寬度
        max_content_width = 0
        for value in df[col]:
            content_width = len(str(value)) * 10 + 24  # padding: 8px 12px = 24px
            max_content_width = max(max_content_width, content_width)
        
        # 取標題和內容的最大值，再加上額外的空間避免超出，最小100px，最大300px
        calculated_width = max(header_width, max_content_width) + 20  # 額外20px緩衝
        return max(100, min(300, calculated_width))
    
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
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'fontSize': '16px',
                    'height': '50px',
                    'minWidth': '50px',
                    'maxWidth': '50px',
                    'position': 'sticky',
                    'left': '0px',
                    'zIndex': 2,
                    'backgroundColor': '#edf7ff',
                    'border': '1px solid #ccc',
                    'boxShadow': '2px 0 5px rgba(0,0,0,0.1)' if len(sticky_columns) == 0 else 'none'
                }
            )
            row_cells.append(checkbox)
        
        sticky_col_data = []
        normal_col_data = []
        
        for col in                 ([col for col in df.columns if col in sticky_columns] + 
                 [col for col in df.columns if col not in sticky_columns]) if sticky_columns else df.columns:
            cell_style = {
                'padding': '8px 12px',
                'textAlign': 'center',
                'border': '1px solid #ccc',
                'fontSize': '16px',
                'height': '50px',
                'whiteSpace': 'nowrap',
                'backgroundColor': 'white'
            }
            
            if col in sticky_columns:
                sticky_index = sticky_columns.index(col)
                # 計算前面所有欄位的寬度總和
                left_offset = 0
                if show_checkbox:
                    left_offset += 50
                for j in range(sticky_index):
                    left_offset += sticky_widths[sticky_columns[j]]
                
                cell_style.update({
                    'position': 'sticky',
                    'left': f'{left_offset}px',
                    'zIndex': 2,
                    'backgroundColor': "#edf7ff",
                    'width': f'{sticky_widths[col]}px',
                    'minWidth': f'{sticky_widths[col]}px',
                    'maxWidth': f'{sticky_widths[col]}px'
                })
                sticky_col_data.append(html.Td(row[col], style=cell_style))
            else:
                normal_col_data.append(html.Td(row[col], style=cell_style))
        
        row_cells.extend(sticky_col_data + normal_col_data)
        
        if show_button:
            button_props = {
                'id': {'type': button_id_type, 'index': i}, 
                'n_clicks': 0, 
                'className': button_class,
                'style': {'fontSize': '16px'}
            }
            
            row_cells.append(
                html.Td(
                    html.Button(button_text, **button_props),
                    style={
                        'padding': '8px 12px',
                        'textAlign': 'center',
                        'border': '1px solid #ccc',
                        'fontSize': '16px',
                        'height': '50px',
                        'whiteSpace': 'nowrap',
                        'position': 'sticky',
                        'right': '0px',
                        'zIndex': 2,
                        'backgroundColor': 'white',
                        'boxShadow': '-2px 0 5px rgba(0,0,0,0.1)'
                    }
                )
            )
        
        rows.append(html.Tr(row_cells, style={
            'backgroundColor': 'white'
        }))

    table = html.Table([
        html.Thead([
            html.Tr(
                ([html.Th('', style={
                    "position": "sticky",
                    "top": "0px",
                    "left": "0px",
                    "zIndex": 4,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc',
                    'width': '50px',
                    'boxShadow': '2px 0 5px rgba(0,0,0,0.1)' if len(sticky_columns) == 0 else 'none'
                })] if show_checkbox else []) +
                [html.Th(col, style={
                    "position": "sticky",
                    "top": "0px" if col not in sticky_columns else "0px",
                    "left": f'{(50 if show_checkbox else 0) + sum(sticky_widths[sticky_columns[j]] for j in range(sticky_columns.index(col)))}px' if col in sticky_columns else 'auto',
                    "zIndex": 3 if col in sticky_columns else 1,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc',
                    'whiteSpace': 'nowrap',
                    'width': f'{sticky_widths[col]}px' if col in sticky_columns else 'auto',
                    'minWidth': f'{sticky_widths[col]}px' if col in sticky_columns else 'auto',
                    'maxWidth': f'{sticky_widths[col]}px' if col in sticky_columns else 'auto',
                    'boxShadow': 'none'
                }) for col in df.columns] +
                ([html.Th('操作', style={
                    "position": "sticky",
                    "top": "0px",
                    "right": "0px",
                    "zIndex": 4,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc',
                    'whiteSpace': 'nowrap',
                    'boxShadow': '-2px 0 5px rgba(0,0,0,0.1)'
                })] if show_button else [])
            )
        ]),
        html.Tbody(rows)
    ], style={
        "width": "100%",
        "borderCollapse": "collapse",
        'border': '1px solid #ccc'
    })

    return html.Div(table, style={
        'overflowY': 'auto',
        'overflowX': 'auto',
        'maxHeight': '77vh',
        'minHeight': '77vh',
        'display': 'block',
        'position': 'relative',
    })