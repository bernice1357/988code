"""
ML系統配置文件
"""

import os

class MLConfig:
    """ML系統配置類"""
    
    # 數據時間窗口配置
    TRAINING_DATA_DAYS = 180        # 訓練使用180天歷史數據
    FEATURE_CALCULATION_DAYS = 90   # 特徵計算使用90天數據  
    PREDICTION_HORIZON_DAYS = 7     # 預測未來7天
    
    # 兩段式訓練配置
    VAL_PERIOD_DAYS = 7            # 驗證期間：上週7天
    SAMPLE_FREQUENCY_DAYS = 15     # 樣本生成頻率：每15天
    
    # 模型配置
    MODEL_RETRAIN_FREQUENCY = 'weekly'  # 每週重新訓練
    PREDICTION_THRESHOLD = 0.7          # 最佳閾值 (F1=0.613)
    BATCH_SIZE = 1000                   # 預測批次大小
    
    # 客戶過濾條件
    MIN_CUSTOMER_PURCHASES_90D = 1      # 客戶90天內最少購買次數
    MAX_DAYS_INACTIVE = 90              # 最大不活躍天數
    MIN_CP_HISTORY = 2                  # 最少客戶-產品歷史記錄
    
    # 文件路徑配置
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # scheduler目錄
    MODEL_DIR = os.path.join(BASE_DIR, 'models')
    CURRENT_MODEL_DIR = os.path.join(MODEL_DIR, 'current')
    ARCHIVE_MODEL_DIR = os.path.join(MODEL_DIR, 'archive')  
    LOG_DIR = os.path.join(BASE_DIR, 'ml_logs')
    
    # 模型文件名
    MODEL_FILE = 'catboost_model.pkl'
    FEATURE_NAMES_FILE = 'feature_names.pkl'
    METADATA_FILE = 'metadata.json'
    
    # CatBoost參數
    CATBOOST_PARAMS = {
        'iterations': 500,
        'learning_rate': 0.1,
        'depth': 8,
        'random_seed': 42,
        'verbose': False,
        'class_weights': [1, 8]  # 最佳權重配置 (F1=0.619, 召回率=62.2%)
    }
    
    # 特徵配置
    CATEGORICAL_FEATURES = [
        'customer_id', 'product_id', 'prediction_day_of_week', 
        'prediction_month', 'customer_segment', 'product_category'
    ]
    
    @classmethod
    def get_current_model_path(cls):
        """獲取當前模型路徑"""
        return os.path.join(cls.CURRENT_MODEL_DIR, cls.MODEL_FILE)
    
    @classmethod
    def get_feature_names_path(cls):
        """獲取特徵名稱文件路徑"""
        return os.path.join(cls.CURRENT_MODEL_DIR, cls.FEATURE_NAMES_FILE)
    
    @classmethod
    def get_metadata_path(cls):
        """獲取元數據文件路徑"""
        return os.path.join(cls.CURRENT_MODEL_DIR, cls.METADATA_FILE)
    
    @classmethod
    def ensure_directories(cls):
        """確保所有目錄存在"""
        for directory in [cls.MODEL_DIR, cls.CURRENT_MODEL_DIR, 
                         cls.ARCHIVE_MODEL_DIR, cls.LOG_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def calculate_training_periods(cls):
        """計算兩段式訓練的時間期間 - 動態選擇有數據的VAL期間"""
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        
        # 動態尋找有數據的VAL期間（從近期往前找）
        val_start, val_end = cls._find_valid_val_period(today)
        
        # 第一段訓練期間 (VAL前180天，完全不包含VAL，增加7天緩衝)
        train1_end = val_start - timedelta(days=7)  # VAL開始前7天，增加緩衝
        train1_start = train1_end - timedelta(days=cls.TRAINING_DATA_DAYS - 1)  # 確保正好180天
        
        # 第二段訓練期間 (包含所有數據到昨天，但保持與第一段的緩衝一致)
        train2_start = train1_start
        # 如果VAL期間是歷史數據，第二段可以包含VAL；如果VAL是近期，則不包含
        if val_end < today - timedelta(days=1):
            # VAL是歷史期間，可以包含
            train2_end = today - timedelta(days=1)
        else:
            # VAL是近期，保持相同的緩衝區
            train2_end = val_start - timedelta(days=7)
        
        return {
            'val_period': {
                'start': val_start,
                'end': val_end,
                'description': f'驗證期間 (有數據週期): {val_start} ~ {val_end}'
            },
            'stage1_train': {
                'start': train1_start,
                'end': train1_end,
                'description': f'第一段訓練: {train1_start} ~ {train1_end} ({cls.TRAINING_DATA_DAYS}天，不含VAL)'
            },
            'stage2_train': {
                'start': train2_start,
                'end': train2_end,
                'description': f'第二段訓練: {train2_start} ~ {train2_end} (完整數據+VAL)'
            }
        }
    
    @classmethod
    def _find_valid_val_period(cls, today):
        """尋找有數據的VAL期間"""
        import psycopg2
        from datetime import timedelta
        
        # 資料庫配置
        db_config = {
            'host': '26.210.160.206',
            'database': '988',
            'user': 'n8n',
            'password': '1234',
            'port': 5433
        }
        
        try:
            conn = psycopg2.connect(**db_config)
            
            # 從較早期間開始尋找，避免與訓練數據重疊
            for weeks_back in range(3, 8):  # 從3週前到7週前尋找
                # 計算該週的週一到週日
                days_since_monday = today.weekday()
                target_monday = today - timedelta(days=days_since_monday + 7 * weeks_back)
                target_sunday = target_monday + timedelta(days=6)
                
                # 檢查該週期是否有交易數據
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*)
                        FROM order_transactions ot
                        JOIN product_master pm ON ot.product_id = pm.product_id
                        WHERE ot.transaction_date BETWEEN %s::date AND %s::date
                            AND ot.document_type = '銷貨'
                            AND pm.is_active = 'active'
                            AND ot.quantity > 0
                    """, (target_monday, target_sunday))
                    
                    count = cur.fetchone()[0]
                    
                    if count >= 50:  # 至少要有50筆交易記錄
                        conn.close()
                        return target_monday, target_sunday
            
            conn.close()
            
            # 如果找不到合適的週期，使用固定的fallback
            fallback_end = today - timedelta(days=14)  # 兩週前
            fallback_start = fallback_end - timedelta(days=6)  # 7天期間
            
            return fallback_start, fallback_end
            
        except Exception as e:
            # 如果資料庫連接失敗，使用默認邏輯
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 14)  # 兩週前
            last_sunday = last_monday + timedelta(days=6)
            
            return last_monday, last_sunday