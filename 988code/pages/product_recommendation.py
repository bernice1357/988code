from .common import *
from . import find_customers_for_item, find_items_for_customer
from components.tabs import create_tabs

tab_configs = [
    {"content": find_items_for_customer.tab_content, "label": "為客戶推薦產品"},
    {"content": find_customers_for_item.tab_content, "label": "為產品尋找客戶"},
]

layout = dbc.Container([
    create_tabs(tab_configs)
], fluid=True)