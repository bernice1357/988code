import dash_bootstrap_components as dbc

def success_toast(page_id, message="操作成功", header="✅ 系統通知", duration=5000):
    """創建成功提示 Toast"""
    return dbc.Toast(
        message,
        id=f"{page_id}-success-toast",
        header=header,
        is_open=False,
        dismissable=True,
        duration=duration,
        style={
            "position": "fixed", 
            "top": 20, 
            "right": 20, 
            "width": 350, 
            "zIndex": 9999,
            "backgroundColor": "#d4edda",
            "borderColor": "#c3e6cb",
            "color": "#155724"
        }
    )

def error_toast(page_id, message="操作失敗", header="❌ 系統通知", duration=5000):
    """創建錯誤提示 Toast"""
    return dbc.Toast(
        message,
        id=f"{page_id}-error-toast",
        header=header,
        is_open=False,
        dismissable=True,
        duration=duration,
        style={
            "position": "fixed", 
            "top": 20, 
            "right": 20, 
            "width": 350, 
            "zIndex": 9999,
            "backgroundColor": "#f8d7da",
            "borderColor": "#f5c6cb",
            "color": "#721c24"
        }
    )

def warning_toast(page_id, message="請注意", header="⚠️ 系統通知", duration=5000):
    """創建警告提示 Toast"""
    return dbc.Toast(
        message,
        id=f"{page_id}-warning-toast",
        header=header,
        is_open=False,
        dismissable=True,
        duration=duration,
        style={
            "position": "fixed", 
            "top": 20, 
            "right": 20, 
            "width": 350, 
            "zIndex": 9999,
            "backgroundColor": "#fff3cd",
            "borderColor": "#ffeaa7",
            "color": "#856404"
        }
    )

def info_toast(page_id, message="提示訊息", header="ℹ️ 系統通知", duration=5000):
    """創建資訊提示 Toast"""
    return dbc.Toast(
        message,
        id=f"{page_id}-info-toast",
        header=header,
        is_open=False,
        dismissable=True,
        duration=duration,
        style={
            "position": "fixed", 
            "top": 20, 
            "right": 20, 
            "width": 350, 
            "zIndex": 9999,
            "backgroundColor": "#d1ecf1",
            "borderColor": "#bee5eb",
            "color": "#0c5460"
        }
    )