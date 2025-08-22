# 全域變數儲存
# 用於存儲所有使用者共享的設定值

# 滯銷品變化比例閾值（預設50%）
sales_threshold = 50

# 不活躍客戶天數閾值（預設30天）
inactive_days = 30

# 回購提醒天數閾值（預設7天）
repurchase_days = 7

def get_sales_threshold():
    """取得滯銷品變化比例閾值"""
    return sales_threshold

def set_sales_threshold(value):
    """設定滯銷品變化比例閾值"""
    global sales_threshold
    if value and value > 0:
        sales_threshold = value
        return True
    return False

def get_inactive_days():
    """取得不活躍客戶天數閾值"""
    return inactive_days

def set_inactive_days(value):
    """設定不活躍客戶天數閾值"""
    global inactive_days
    if value and value > 0:
        inactive_days = value
        return True
    return False

def get_repurchase_days():
    """取得回購提醒天數閾值"""
    return repurchase_days

def set_repurchase_days(value):
    """設定回購提醒天數閾值"""
    global repurchase_days
    if value and value > 0:
        repurchase_days = value
        return True
    return False