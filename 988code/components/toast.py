import dash_bootstrap_components as dbc

def create_success_toast(message="操作成功", header="✅ 系統通知", duration=5000):
    """創建成功提示 Toast"""
    return dbc.Toast(
        message,
        header=header,
        is_open=True,
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

def create_error_toast(message="操作失敗", header="❌ 系統通知", duration=5000):# TODOid, 
    """創建錯誤提示 Toast"""
    return dbc.Toast(
        message,
        # id=id,
        header=header,
        is_open=True,
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

def create_warning_toast(message="請注意", header="⚠️ 系統通知", duration=5000):
    """創建警告提示 Toast"""
    return dbc.Toast(
        message,
        header=header,
        is_open=True,
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

def create_info_toast(message="提示訊息", header="ℹ️ 系統通知", duration=5000):
    """創建資訊提示 Toast"""
    return dbc.Toast(
        message,
        header=header,
        is_open=True,
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