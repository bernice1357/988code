from dash import dash_table
from dash import html, dcc, dash_table, Input, Output, State, ctx, callback_context, exceptions

# TODO 要把欄位標題做懸空的
def custom_table(df, show_checkbox=False, show_button=False, button_text="操作", button_class="btn btn-warning btn-sm", button_id_type='status-button'):
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
                    'border': '1px solid #ccc',
                    'fontSize': '16px',
                    'height': '50px',
                    'width': '50px'
                }
            )
            row_cells.append(checkbox)
        
        row_cells.extend([html.Td(row[col], style={
            'padding': '8px 12px',
            'textAlign': 'center',
            'border': '1px solid #ccc',
            'fontSize': '16px',
            'height': '50px'
        }) for col in df.columns])
        
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
                        'height': '50px'
                    }
                )
            )
        
        rows.append(html.Tr(row_cells, style={
            'backgroundColor': '#f9f9f9' if i % 2 == 1 else 'white'
        }))

    table = html.Table([
        html.Thead([
            html.Tr(
                ([html.Th('', style={
                    "position": "sticky", 
                    "top": "0px", 
                    "zIndex": 1,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc',
                    'width': '50px'
                })] if show_checkbox else []) +
                [html.Th(col, style={
                    "position": "sticky", 
                    "top": "0px", 
                    "zIndex": 1,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc'
                }) for col in df.columns] +
                ([html.Th('操作', style={
                    "position": "sticky", 
                    "top": "0px", 
                    "zIndex": 1,
                    'backgroundColor': '#bcd1df',
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'padding': '8px 12px',
                    'textAlign': 'center',
                    'border': '1px solid #ccc'
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