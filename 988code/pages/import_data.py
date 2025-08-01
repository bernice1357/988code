import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import base64
import io
from .common import *

layout = html.Div([
    # 三個區塊水平排列
    html.Div([
        # 客戶資料區塊
        html.Div([
            html.H3("客戶資料", style={'color': '#2E86AB'}),
            dcc.Upload(
                id='upload-customer',
                children=html.Div([
                    '拖拽或點擊上傳客戶資料檔案'
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px 0'
                },
                multiple=False
            ),
            html.Div(id='customer-output')
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'margin': '10px', 'borderRadius': '10px', 'width': '31%', 'height': '400px', 'display': 'inline-block', 'verticalAlign': 'top', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'}),
        
        # 銷貨資料區塊
        html.Div([
            html.H3("銷貨資料", style={'color': '#A23B72'}),
            dcc.Upload(
                id='upload-sales',
                children=html.Div([
                    '拖拽或點擊上傳銷貨資料檔案'
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px 0'
                },
                multiple=False
            ),
            html.Div(id='sales-output')
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'margin': '10px', 'borderRadius': '10px', 'width': '31%', 'height': '400px', 'display': 'inline-block', 'verticalAlign': 'top', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'}),
        
        # 庫存資料區塊
        html.Div([
            html.H3("庫存資料", style={'color': '#F18F01'}),
            dcc.Upload(
                id='upload-inventory',
                children=html.Div([
                    '拖拽或點擊上傳庫存資料檔案'
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px 0'
                },
                multiple=False
            ),
            html.Div(id='inventory-output')
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'margin': '10px', 'borderRadius': '10px', 'width': '31%', 'height': '400px', 'display': 'inline-block', 'verticalAlign': 'top', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'})
    ])
], style={'maxWidth': '1200px', 'margin': '0 auto'})

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div(['不支援的檔案格式'])
        
        return html.Div([
            html.H5(f'檔案: {filename}'),
            html.P(f'資料筆數: {len(df)}'),
            dash_table.DataTable(
                data=df.head(10).to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
            )
        ])
    except Exception as e:
        return html.Div([f'處理檔案時發生錯誤: {str(e)}'])

@app.callback(Output('customer-output', 'children'),
              Input('upload-customer', 'contents'),
              State('upload-customer', 'filename'))
def update_customer_output(contents, filename):
    if contents is not None:
        return parse_contents(contents, filename)

@app.callback(Output('sales-output', 'children'),
              Input('upload-sales', 'contents'),
              State('upload-sales', 'filename'))
def update_sales_output(contents, filename):
    if contents is not None:
        return parse_contents(contents, filename)

@app.callback(Output('inventory-output', 'children'),
              Input('upload-inventory', 'contents'),
              State('upload-inventory', 'filename'))
def update_inventory_output(contents, filename):
    if contents is not None:
        return parse_contents(contents, filename)