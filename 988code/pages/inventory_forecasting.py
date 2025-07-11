from .common import *
from . import daily_delivery_forecast, monthly_sales_forecast
from components.tabs import create_tabs
import requests

tab_configs = [
    {"content": daily_delivery_forecast.tab_content, "label": "每日銷量預測"},
    {"content": monthly_sales_forecast.tab_content, "label": "每月配送預測"}
]

layout = dbc.Container([
    create_tabs(tab_configs)
], fluid=True)