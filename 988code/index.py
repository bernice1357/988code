from dash import dcc, html
import dash_bootstrap_components as dbc
from app import app
from callbacks import main_callbacks, sidebar_callbacks, breadcrumb_callbacks

sidebar = html.Div(
    [
        html.Div(
            html.A(
                html.Img(src="/assets/images/logo.png", style={"width": "100%", "height": "auto", "margin-bottom": "20px"}),
                href="/",
                style={"text-decoration": "none"}
            )
        ),
        html.Hr(),
        dbc.Nav( # TODO 這邊把下拉選單做成可以看到J
            [
                dbc.NavLink("新進訂單", href="/new_orders", active="exact"),
                dbc.NavLink("客戶資料管理", href="/customer_data", active="exact"),
                dbc.NavLink("銷售分析", href="/sales_analysis", active="exact"),
                dbc.NavLink("產品推薦與分析", href="/product_recommendation", active="exact"),
                dbc.DropdownMenu(
                    label="提醒管理",
                    nav=True,
                    in_navbar=True,
                    children=[
                        dbc.DropdownMenuItem("補貨提醒", href="/restock_reminder"),
                        dbc.DropdownMenuItem("新品購買", href="/buy_new_item"),
                        dbc.DropdownMenuItem("新品回購提醒", href="/repurchase_reminder"),
                        dbc.DropdownMenuItem("商品潛在客戶列表", href="/potential_customers"),
                    ],
                    style={"margin-top": "1rem", "width": "224px"},  # 設定寬度
                ),
                dbc.DropdownMenu(
                    label="商品管理",
                    nav=True,
                    in_navbar=True,
                    children=[
                        dbc.DropdownMenuItem("商品庫存管理", href="/product_inventory"),
                        dbc.DropdownMenuItem("滯銷品與未活躍客戶", href="/inactive_customers"),
                        dbc.DropdownMenuItem("庫存預測", href="/inventory_forecasting"),
                    ],
                    style={"margin-top": "1rem"},  # 設定寬度
                ),
                dbc.NavLink("RAG數據管理", href="/rag", active="exact"),
            ],
            vertical=True,
            pills=True,
            style={"margin-top": "2rem", "fontWeight": "bold", "color": "#2c3e50"}
        ),
        html.Button(
            html.I(className="fas fa-caret-left"),
            id="toggle-button",
            style={
                "position": "absolute", "bottom": "20px", "right": "20px", "zIndex": "1001",
                "backgroundColor": "transparent", "color": "#000000",
                "border": "none", "borderRadius": "50%", "width": "48px", "height": "48px",
                "fontSize": "20px", "cursor": "pointer", "display": "flex",
                "justifyContent": "center", "alignItems": "center",
                "boxShadow": "0 0 8px rgba(0, 0, 0, 0.3)"
            }
        )
    ],
    id="sidebar",
    style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "16rem",
        "transition": "all 0.3s", "overflow": "hidden", "padding": "2rem 1rem",
        "backgroundColor": "#f0f4f8", "boxShadow": "2px 0px 8px rgba(0, 0, 0, 0.1)"
    }
)

toggle_button_float = html.Button(
    html.I(className="fas fa-caret-right"),
    id="toggle-button-float",
    style={
        "position": "fixed", "bottom": "20px", "left": "10px",
        "zIndex": "1001", "backgroundColor": "#ffffff", "color": "#000000",
        "border": "1px solid #e0e0e0", "borderRadius": "50%", "width": "48px", "height": "48px",
        "fontSize": "20px", "cursor": "pointer", "display": "none",
        "justifyContent": "center", "alignItems": "center",
        "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.1)"
    }
)

app.layout = html.Div([
    dcc.Store(id="sidebar-toggle", data=True),
    sidebar,
    toggle_button_float,
    dcc.Location(id='url', refresh=False),
    html.Div([
    html.Div([
        dbc.Breadcrumb(
            id='breadcrumb',
            items=[{"label": "首頁", "href": "/", "active": True}],
        ),
        dbc.NavLink(
            "登入",
            href="/login",
            id="login-nav-link"
        )
    ], style={"position": "relative"}),
    html.Div(
        id="main-content",
        style={"margin-left": "16rem", "margin-top": "64px", "padding": "2rem", "backgroundColor": "#FFFFFF", "color": "#000000"}
        )
    ])
])

if __name__ == '__main__':
    app.run(debug=True)