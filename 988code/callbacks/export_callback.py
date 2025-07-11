import pandas as pd
from dash import dcc
from dash.dependencies import Output, Input, State
from datetime import datetime

def create_export_callback(app, page_name, data_store_id, filename_prefix="export_data"):
    """
    建立共用的匯出 callback
    
    Args:
        app: Dash app instance
        page_name: 頁面名稱，用於建立唯一的 callback ID
        data_store_id: 資料 store 的 ID
        filename_prefix: 匯出檔案名稱前綴
    """
    @app.callback(
        Output(f"{page_name}-download", "data"),
        Input(f"{page_name}-export-button", "n_clicks"),
        State(data_store_id, "data"),
        prevent_initial_call=True
    )
    def export_data(n_clicks, data):
        if n_clicks and data:
            # 轉換為 DataFrame
            df = pd.DataFrame(data)
            
            # 生成帶時間戳的檔案名稱
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.xlsx"
            
            # 匯出為 Excel
            return dcc.send_data_frame(df.to_excel, filename, index=False)
        return None

def add_download_component(page_name):
    """
    加入下載元件
    
    Args:
        page_name: 頁面名稱
    
    Returns:
        dcc.Download 元件
    """
    return dcc.Download(id=f"{page_name}-download")