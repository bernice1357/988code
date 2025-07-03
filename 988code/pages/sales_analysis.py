from .common import *
from . import area_sales_analysis, category_sales_analysis
from components.tabs import create_tabs
import requests

tab_configs = [
    {"content": area_sales_analysis.tab_content, "label": "根據地區分析"},
    {"content": category_sales_analysis.tab_content, "label": "根據產品分析"}
]

layout = dbc.Container([
    create_tabs(tab_configs)
], fluid=True)
