from dash import dash_table
from dash import html, dcc, dash_table, Input, Output, State, ctx, callback_context, exceptions
    
def button_table(df, button_text="查看", button_class="btn btn-warning btn-sm", button_id_type='view-button', address_columns=None):
    header = html.Tr([html.Th(col) for col in df.columns] + [html.Th("操作")])
    rows = []

    for i, row in df.iterrows():
        row_cells = []
        for col in df.columns:
            if address_columns and col in address_columns:
                cell_style = {
                    'maxWidth': '200px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'whiteSpace': 'nowrap'
                }
                row_cells.append(html.Td(row[col], style=cell_style, title=str(row[col])))
            else:
                row_cells.append(html.Td(row[col]))
        
        button_props = {
            'id': {'type': button_id_type, 'index': i}, 
            'n_clicks': 0, 
            'className': button_class,
            'style': {'fontSize': '16px'}
        }
        
        row_cells.append(
            html.Td(
                html.Button(button_text, **button_props)
            )
        )
        rows.append(html.Tr(row_cells))

    table = html.Table([
        html.Thead([
            html.Tr([
                html.Th(col, style={"position": "sticky", "top": "0px", "zIndex": 1})
                for col in df.columns
            ] + [html.Th("操作", style={"position": "sticky", "top": "0px", "zIndex": 1})])
        ]),
        html.Tbody(rows)
    ], style={
        "width": "100%",
        "borderCollapse": "collapse",
    })

    return html.Div(table, style={
        'overflowY': 'auto',
        'maxHeight': '75vh',
        'minHeight': '75vh',
        'display': 'block',
    })
    
def normal_table(df):
    header = html.Tr([html.Th(col) for col in df.columns])
    rows = []

    for i, row in df.iterrows():
        row_cells = [html.Td(row[col]) for col in df.columns]
        rows.append(html.Tr(row_cells))

    table = html.Table([
        html.Thead([
            html.Tr([
                html.Th(col, style={"position": "sticky", "top": "0px", "zIndex": 1})
                for col in df.columns
            ])
        ]),
        html.Tbody(rows)
    ], style={
        "width": "100%",
        "borderCollapse": "collapse",
    })

    return html.Div(table, style={
        'overflowY': 'auto',
        'maxHeight': '75vh',
        'minHeight': '75vh',
        'display': 'block',
    })

def status_table(df):
    header = html.Tr([html.Th(col) for col in df.columns])
    rows = []

    for i, row in df.iterrows():
        row_cells = [html.Td(row[col]) for col in df.columns]
        rows.append(html.Tr(row_cells))

    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        row_selectable="multi",  # 可以多選
        selected_rows=[],        # 預設沒選任何列
        style_table={
            'overflowX': 'auto',
            'border': '1px solid #ccc'
        },
        style_cell={
            'padding': '8px 12px',
            'textAlign': 'center',
            'border': '1px solid #ccc'
        },
        style_header={
            'backgroundColor': '#fbe8a6',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f9f9f9',
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': '#e6f7ff',
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': '#d2f8d2',  # 勾選後的顏色
                'border': '1px solid #00aa00',
            },
        ]
    )

    return html.Div(table, style={
        'overflowY': 'auto',
        'maxHeight': '60vh',
        'minHeight': '60vh',
        'display': 'block',
    })
    
def customer_table(df):
    header = html.Tr([html.Th(col) for col in df.columns])
    rows = []

    for i, row in df.iterrows():
        row_cells = [html.Td(row[col]) for col in df.columns]
        rows.append(html.Tr(row_cells))

    table = html.Table([
        html.Thead([
            html.Tr([
                html.Th(col, style={"position": "sticky", "top": "0px", "zIndex": 1})
                for col in df.columns
            ])
        ]),
        html.Tbody(rows)
    ], style={
        "width": "100%",
        "borderCollapse": "collapse",
    })

    return html.Div(table, style={
        'overflowY': 'auto',
        'maxHeight': '70vh',
        'minHeight': '70vh',
        'display': 'block',
    })