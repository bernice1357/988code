import dash
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import datetime
import plotly.express as px
import requests
from dash import ctx
import urllib.parse

from components.toast import create_success_toast, create_error_toast, create_warning_toast, create_info_toast
from components.table import button_table, normal_table, status_table, customer_table
from app import app