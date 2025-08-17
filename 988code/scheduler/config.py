#!/usr/bin/env python3
"""
排程系統統一配置文件
集中管理所有數據庫連接、系統設定和常數
"""

import os

class DatabaseConfig:
    """數據庫配置類"""
    
    # 主數據庫配置
    HOST = '26.210.160.206'
    PORT = 5433
    DATABASE = '988'
    USER = 'n8n'
    PASSWORD = '1234'
    
    @classmethod
    def get_config(cls) -> dict:
        """獲取數據庫配置字典"""
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'database': cls.DATABASE,
            'user': cls.USER,
            'password': cls.PASSWORD
        }
    
    @classmethod
    def get_connection_string(cls) -> str:
        """獲取數據庫連接字符串"""
        return f"postgresql://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.DATABASE}"

class SchedulerConfig:
    """排程器配置類"""
    
    # 時區設定
    TIMEZONE = 'Asia/Taipei'
    
    # 排程時間設定
    SCHEDULES = {
        # 每日任務
        'trigger_health_check': '02:00',      # 觸發器健康檢查
        'inactive_customer_check': '02:30',   # 不活躍客戶檢查
        'repurchase_reminder': '04:00',       # 回購提醒維護
        'sales_change_check': '06:00',        # 銷量變化檢查
        'daily_prediction': '22:00',          # 每日預測生成
        
        # 每週任務
        'prophet_training': 'saturday.08:00',     # Prophet模型訓練
        'weekly_recommendation': 'sunday.02:00', # 推薦系統更新
        
        # 每月任務
        'monthly_sales_reset': 'monthly.00:30',    # 銷量重置（每月1號）
        'monthly_prediction': 'monthly.01:00',     # 月銷售預測（每月1號）
    }
    
    # 排程類別
    SCHEDULE_CATEGORIES = {
        'restock': {
            'enabled': True,
            'tasks': ['prophet_training', 'daily_prediction', 'trigger_health_check']
        },
        'sales': {
            'enabled': True,
            'tasks': ['sales_change_check', 'monthly_prediction', 'monthly_sales_reset']
        },
        'recommendation': {
            'enabled': True,
            'tasks': ['weekly_recommendation']
        },
        'customer_management': {
            'enabled': True,
            'tasks': ['inactive_customer_check', 'repurchase_reminder']
        }
    }

class LoggingConfig:
    """日誌配置類"""
    
    # 日誌目錄
    LOG_DIR = 'logs'
    
    # 日誌文件名格式
    LOG_FILE_FORMAT = '{component}_{date}.log'
    
    # 日誌級別
    LOG_LEVEL = 'INFO'
    
    # 日誌格式
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 日誌文件大小限制（MB）
    MAX_LOG_SIZE = 50
    
    # 保留日誌文件數量
    BACKUP_COUNT = 10
    
    @classmethod
    def get_log_file_path(cls, component: str) -> str:
        """獲取指定組件的日誌文件路徑"""
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m')
        filename = cls.LOG_FILE_FORMAT.format(component=component, date=date_str)
        return os.path.join(cls.LOG_DIR, filename)

class SystemConfig:
    """系統配置類"""
    
    # 系統組件
    COMPONENTS = {
        'scheduler': 'PredictionScheduler',
        'controller': 'ScheduleController', 
        'executor': 'TaskExecutor',
        'monitor': 'SchedulerMonitor'
    }
    
    # 重試設定
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 5  # 秒
    
    # 監控間隔
    MONITOR_INTERVAL = 60  # 秒
    
    # 報告目錄
    REPORT_DIR = 'reports'
    OUTPUT_DIR = 'outputs'
    
    # 清理設定
    CLEANUP_DAYS = {
        'logs': 90,          # 日誌文件保留90天
        'reports': 30,       # 報告文件保留30天
        'predictions': 7,    # 預測結果保留7天
    }

class TaskConfig:
    """任務配置類"""
    
    # Prophet系統配置
    PROPHET_CONFIG = {
        'prediction_days': 7,
        'model_save_path': 'models',
        'backup_enabled': True,
        'csv_output_enabled': True
    }
    
    # 推薦系統配置
    RECOMMENDATION_CONFIG = {
        'top_n': 7,
        'customer_similarity_threshold': 0.5,
        'product_similarity_threshold': 0.3
    }
    
    # 客戶管理配置
    CUSTOMER_CONFIG = {
        'inactive_days_threshold': 30,   # 30天未購買視為不活躍
        'repurchase_reminder_days': 14,  # 14天提醒回購
        'cleanup_days': 90               # 清理90天前的記錄
    }
    
    # 銷量監控配置
    SALES_CONFIG = {
        'anomaly_threshold': 0.5,        # 50%變化視為異常
        'low_stock_threshold': 10,       # 低庫存閾值
        'zero_stock_alert': True         # 缺貨警報
    }

# 環境變量覆蓋配置
def load_from_env():
    """從環境變量載入配置覆蓋"""
    # 數據庫配置
    if os.getenv('DB_HOST'):
        DatabaseConfig.HOST = os.getenv('DB_HOST')
    if os.getenv('DB_PORT'):
        DatabaseConfig.PORT = int(os.getenv('DB_PORT'))
    if os.getenv('DB_NAME'):
        DatabaseConfig.DATABASE = os.getenv('DB_NAME')
    if os.getenv('DB_USER'):
        DatabaseConfig.USER = os.getenv('DB_USER')
    if os.getenv('DB_PASSWORD'):
        DatabaseConfig.PASSWORD = os.getenv('DB_PASSWORD')
    
    # 日誌級別
    if os.getenv('LOG_LEVEL'):
        LoggingConfig.LOG_LEVEL = os.getenv('LOG_LEVEL')
    
    # 時區設定
    if os.getenv('TIMEZONE'):
        SchedulerConfig.TIMEZONE = os.getenv('TIMEZONE')

# 配置驗證
def validate_config():
    """驗證配置的有效性"""
    errors = []
    
    # 檢查數據庫配置
    required_db_fields = ['HOST', 'PORT', 'DATABASE', 'USER', 'PASSWORD']
    for field in required_db_fields:
        if not hasattr(DatabaseConfig, field) or not getattr(DatabaseConfig, field):
            errors.append(f"Database config missing: {field}")
    
    # 檢查必要目錄
    for dir_name in [LoggingConfig.LOG_DIR, SystemConfig.REPORT_DIR, SystemConfig.OUTPUT_DIR]:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_name}: {e}")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

# 快捷訊問函數
def get_db_config() -> dict:
    """獲取數據庫配置字典"""
    return DatabaseConfig.get_config()

def get_schedule_time(task_name: str) -> str:
    """獲取任務排程時間"""
    return SchedulerConfig.SCHEDULES.get(task_name, '00:00')

def is_category_enabled(category: str) -> bool:
    """檢查排程類別是否啟用"""
    return SchedulerConfig.SCHEDULE_CATEGORIES.get(category, {}).get('enabled', False)

# 初始化配置
def init_config():
    """初始化配置系統"""
    load_from_env()
    validate_config()
    print(f"Configuration initialized successfully")
    print(f"Database: {DatabaseConfig.HOST}:{DatabaseConfig.PORT}/{DatabaseConfig.DATABASE}")
    print(f"Timezone: {SchedulerConfig.TIMEZONE}")
    print(f"Log Level: {LoggingConfig.LOG_LEVEL}")

if __name__ == "__main__":
    # 測試配置
    init_config()
    print("\nDatabase Config:", get_db_config())
    print("Prophet Training Time:", get_schedule_time('prophet_training'))
    print("Restock Category Enabled:", is_category_enabled('restock'))