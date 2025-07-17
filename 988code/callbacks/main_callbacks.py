from .common import *
from pages import *

@app.callback(
    Output('main-content', 'children'),
    Input('url', 'pathname')
)
def display_main_content(pathname):
    if pathname == '/':
        return homepage.layout
    
    elif pathname == '/new_orders':
        return new_orders.layout
    
    elif pathname == '/customer_data':
        return customer_data.layout
    
    elif pathname == '/product_recommendation':
        return product_recommendation.layout
    
    elif pathname == '/history_orders':
        return customer_data.layout
    
    elif pathname == '/inactive_customers':
        return inactive_customers.layout
    
    elif pathname == '/potential_customers':
        return potential_customers.layout
    
    elif pathname == '/buy_new_item':
        return buy_new_item.layout

    elif pathname == '/inventory_forecasting':
        return inventory_forecasting.layout

    elif pathname == '/product_inventory':
        return product_inventory.layout
    
    elif pathname == '/rag':
        return rag.layout
    
    elif pathname == '/repurchase_reminder':
        return repurchase_reminder.layout
    
    elif pathname == '/restock_reminder':
        return restock_reminder.layout
    
    elif pathname == '/sales_analysis':
        return sales_analysis.layout
    
    elif pathname == '/login':
        return login.layout

    else:
        return html.Div([html.H1('404 找不到頁面')])
