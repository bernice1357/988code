from .common import *
from . import inactive_customers_1, inactive_customers_2
from components.tabs import create_tabs

tab_configs = [
    {"content": inactive_customers_1.tab_content, "label": "不活躍客戶"},
    {"content": inactive_customers_2.tab_content, "label": "商品銷量異動"}
]

layout = dbc.Container([
    create_tabs(tab_configs)
], fluid=True)