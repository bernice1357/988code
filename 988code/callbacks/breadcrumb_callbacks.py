from .common import *

@app.callback(
    Output('breadcrumb', 'items'),
    Input('url', 'pathname')
)

def update_breadcrumb(pathname):
    if pathname == "/":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
        ]
    elif pathname == "/new_orders":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "新進訂單", "href": "/new_orders", "active": True}
        ]
    elif pathname == "/customer_data":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "客戶資料管理", "href": "/customer_data", "active": True}
        ]
    elif pathname == "/rag":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "RAG數據管理", "href": "/rag", "active": True}
        ]
    elif pathname == "/sales_analysis":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "銷售分析", "href": "/sales_analysis", "active": True}
        ]
    elif pathname == "/product_recommendation":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "產品推薦與分析", "href": "/product_recommendation", "active": True}
        ]
    elif pathname == "/restock_reminder":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "補貨提醒", "href": "/restock_reminder", "active": True}
        ]
    elif pathname == "/buy_new_item":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "新品購買", "href": "/buy_new_item", "active": True}
        ]
    elif pathname == "/repurchase_reminder":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "新品回購提醒", "href": "/repurchase_reminder", "active": True}
        ]
    elif pathname == "/potential_customers":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "商品潛在客戶列表", "href": "/potential_customers", "active": True}
        ]
    elif pathname == "/product_inventory":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "商品庫存管理", "href": "/product_inventory", "active": True}
        ]
    elif pathname == "/inactive_customers":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "滯銷品與未活躍客戶", "href": "/inactive_customers", "active": True}
        ]
    elif pathname == "/inventory_forecasting":
        return [
            {"label": "首頁", "href": "/", "active": False}, 
            {"label": "庫存預測", "href": "/inventory_forecasting", "active": True}
        ]
    else:
        return [
            {"label": "404 - 找不到頁面", "href": "#", "active": True}
        ]
