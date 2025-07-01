from .common import *
from . import inactive_customers_1, inactive_customers_2

tabs = dbc.Tabs(
    [
        dbc.Tab(inactive_customers_1.tab_content, label="不活躍客戶"),
        dbc.Tab(inactive_customers_2.tab_content, label="滯銷品分析")
    ],
    className="my-tabs",
)

layout = dbc.Container([
    tabs
], fluid=True)