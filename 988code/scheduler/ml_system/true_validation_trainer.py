#!/usr/bin/env python3
"""
真實驗證兩段式訓練器
徹底解決數據洩漏問題，實現真正的時序驗證
"""

import os
import json
import pickle
import logging
import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime, timedelta
from catboost import CatBoostClassifier
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score

import sys
import os

# 添加當前目錄到路徑
current_dir = os.path.dirname(__file__)
scheduler_dir = os.path.dirname(current_dir)
if scheduler_dir not in sys.path:
    sys.path.insert(0, scheduler_dir)

try:
    from ml_system.config import MLConfig
except ImportError:
    # 如果作為獨立腳本運行，創建簡化配置
    class MLConfig:
        TRAINING_DATA_DAYS = 180
        FEATURE_CALCULATION_DAYS = 90
        PREDICTION_HORIZON_DAYS = 7
        VAL_PERIOD_DAYS = 7
        SAMPLE_FREQUENCY_DAYS = 15
        PREDICTION_THRESHOLD = 0.8
        
        BASE_DIR = scheduler_dir
        MODEL_DIR = os.path.join(BASE_DIR, 'models')
        CURRENT_MODEL_DIR = os.path.join(MODEL_DIR, 'current')
        ARCHIVE_MODEL_DIR = os.path.join(MODEL_DIR, 'archive')
        LOG_DIR = os.path.join(BASE_DIR, 'ml_logs')
        
        MODEL_FILE = 'catboost_model.pkl'
        FEATURE_NAMES_FILE = 'feature_names.pkl'
        METADATA_FILE = 'metadata.json'
        
        CATBOOST_PARAMS = {
            'iterations': 500,
            'learning_rate': 0.1,
            'depth': 8,
            'random_seed': 42,
            'verbose': False,
            'class_weights': [1, 5]
        }
        
        CATEGORICAL_FEATURES = [
            'customer_id', 'product_id', 'prediction_day_of_week', 
            'prediction_month', 'customer_segment', 'product_category'
        ]
        
        @classmethod
        def get_current_model_path(cls):
            return os.path.join(cls.CURRENT_MODEL_DIR, cls.MODEL_FILE)
        
        @classmethod
        def get_feature_names_path(cls):
            return os.path.join(cls.CURRENT_MODEL_DIR, cls.FEATURE_NAMES_FILE)
        
        @classmethod
        def get_metadata_path(cls):
            return os.path.join(cls.CURRENT_MODEL_DIR, cls.METADATA_FILE)
        
        @classmethod
        def ensure_directories(cls):
            for directory in [cls.MODEL_DIR, cls.CURRENT_MODEL_DIR, 
                             cls.ARCHIVE_MODEL_DIR, cls.LOG_DIR]:
                os.makedirs(directory, exist_ok=True)

class TrueValidationTrainer:
    """真實驗證兩段式訓練器 - 無數據洩漏版本"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or {
            'host': '26.210.160.206',
            'database': '988',
            'user': 'n8n',
            'password': '1234',
            'port': 5433
        }
        
        self.model = None
        self.feature_names = None
        self.real_validation_metrics = {}
        self.final_model_info = {}
        self.training_periods = None
        
        self.setup_logging()
        MLConfig.ensure_directories()
        
        print("=== 真實驗證兩段式訓練器 ===")
        print(f"特色: 無數據洩漏的真實時序驗證")
        print(f"訓練數據期間: {MLConfig.TRAINING_DATA_DAYS}天")
        print(f"時間緩衝區: 7天")
    
    def setup_logging(self):
        """設置日誌"""
        log_file = os.path.join(MLConfig.LOG_DIR, f'true_validation_{datetime.now().strftime("%Y%m")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            self.logger.error(f"資料庫連接失敗: {e}")
            return None
    
    def calculate_and_display_periods(self):
        """計算並顯示訓練時間期間"""
        self.training_periods = MLConfig.calculate_training_periods()
        
        self.logger.info("=== 真實驗證時間期間 ===")
        for period_name, period_info in self.training_periods.items():
            self.logger.info(f"{period_info['description']}")
        
        # 驗證時間緩衝
        val_period = self.training_periods['val_period']
        stage1_train = self.training_periods['stage1_train']
        
        buffer_days = (val_period['start'] - stage1_train['end']).days - 1
        self.logger.info(f"時間緩衝區: {buffer_days} 天 (避免信息洩漏)")
        
        return self.training_periods
    
    def load_data_for_period(self, start_date, end_date, period_name):
        """載入指定期間的數據"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            self.logger.info(f"載入{period_name}數據: {start_date} ~ {end_date}")
            
            query = """
                SELECT 
                    ot.customer_id,
                    ot.product_id,
                    ot.transaction_date,
                    SUM(ot.quantity) as quantity,
                    SUM(ot.amount) as amount
                FROM order_transactions ot
                JOIN product_master pm ON ot.product_id = pm.product_id
                WHERE ot.transaction_date BETWEEN %s::date AND %s::date
                    AND ot.document_type = '銷貨'
                    AND pm.is_active = 'active'
                    AND ot.quantity > 0
                GROUP BY ot.customer_id, ot.product_id, ot.transaction_date
                ORDER BY ot.transaction_date
            """
            
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            
            self.logger.info(f"{period_name}數據載入完成:")
            self.logger.info(f"  交易記錄: {len(df):,} 筆")
            self.logger.info(f"  涉及客戶: {df['customer_id'].nunique():,} 位")
            self.logger.info(f"  涉及產品: {df['product_id'].nunique():,} 個")
            
            return df
            
        except Exception as e:
            self.logger.error(f"載入{period_name}數據失敗: {e}")
            return None
        finally:
            conn.close()
    
    def generate_historical_training_samples(self, train_data):
        """生成純歷史訓練樣本 - 不涉及VAL數據"""
        self.logger.info("開始生成純歷史訓練樣本...")
        
        # 計算樣本生成範圍
        min_date = train_data['transaction_date'].min()
        max_date = train_data['transaction_date'].max()
        
        # 從第90天開始到結束，每15天生成一次樣本
        start_sample_date = min_date + timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
        end_sample_date = max_date - timedelta(days=MLConfig.PREDICTION_HORIZON_DAYS)
        
        sample_dates = pd.date_range(start_sample_date, end_sample_date, 
                                   freq=f'{MLConfig.SAMPLE_FREQUENCY_DAYS}D')
        
        self.logger.info(f"純歷史樣本生成配置:")
        self.logger.info(f"  樣本日期範圍: {start_sample_date} ~ {end_sample_date}")
        self.logger.info(f"  樣本時間點: {len(sample_dates)} 個")
        
        samples = []
        for i, sample_date in enumerate(sample_dates):
            if i % 3 == 0:
                self.logger.info(f"  歷史樣本進度: {i+1}/{len(sample_dates)} ({(i+1)/len(sample_dates)*100:.1f}%)")
            
            # 獲取該日期的90天特徵數據
            feature_start = sample_date - timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
            feature_data = train_data[
                (train_data['transaction_date'] >= feature_start) &
                (train_data['transaction_date'] < sample_date)
            ]
            
            # 獲取該日期後7天的標籤數據（純歷史）
            label_start = sample_date
            label_end = sample_date + timedelta(days=MLConfig.PREDICTION_HORIZON_DAYS)
            label_data = train_data[
                (train_data['transaction_date'] >= label_start) &
                (train_data['transaction_date'] < label_end)
            ]
            
            # 生成該時間點的樣本
            date_samples = self._create_samples_for_date(feature_data, label_data, sample_date)
            samples.extend(date_samples)
        
        self.logger.info(f"純歷史樣本生成完成: {len(samples):,} 筆")
        return samples
    
    def _create_samples_for_date(self, feature_data, label_data, sample_date):
        """為特定日期創建樣本"""
        samples = []
        
        # 獲取有購買歷史的客戶-產品組合
        historical_pairs = set(zip(feature_data['customer_id'], feature_data['product_id']))
        positive_pairs = set(zip(label_data['customer_id'], label_data['product_id']))
        
        # 創建正樣本
        for customer_id, product_id in positive_pairs:
            if (customer_id, product_id) in historical_pairs:
                features = self._calculate_features(customer_id, product_id, feature_data, sample_date)
                sample = {
                    **features,
                    'label': 1,
                    'sample_date': sample_date,
                    'customer_id': customer_id,
                    'product_id': product_id
                }
                samples.append(sample)
        
        # 創建負樣本
        negative_candidates = historical_pairs - positive_pairs
        max_negative_samples = min(len(negative_candidates), len(positive_pairs) * 4)
        
        if max_negative_samples > 0:
            negative_candidates_list = list(negative_candidates)
            selected_indices = np.random.choice(
                len(negative_candidates_list), 
                size=max_negative_samples, 
                replace=False
            )
            negative_pairs = [negative_candidates_list[i] for i in selected_indices]
            
            for customer_id, product_id in negative_pairs:
                features = self._calculate_features(customer_id, product_id, feature_data, sample_date)
                sample = {
                    **features,
                    'label': 0,
                    'sample_date': sample_date,
                    'customer_id': customer_id,
                    'product_id': product_id
                }
                samples.append(sample)
        
        return samples
    
    def _calculate_features(self, customer_id, product_id, feature_data, sample_date):
        """計算90天特徵"""
        # 獲取相關數據
        customer_data = feature_data[feature_data['customer_id'] == customer_id]
        product_data = feature_data[feature_data['product_id'] == product_id]
        cp_data = feature_data[
            (feature_data['customer_id'] == customer_id) & 
            (feature_data['product_id'] == product_id)
        ]
        
        features = {
            # 時間特徵
            'prediction_day_of_week': sample_date.weekday(),
            'prediction_day_of_month': sample_date.day,
            'prediction_month': sample_date.month,
            'prediction_quarter': (sample_date.month - 1) // 3 + 1,
            
            # 客戶90天特徵
            'customer_purchase_days_90d': customer_data['transaction_date'].nunique(),
            'customer_total_amount_90d': customer_data['amount'].sum(),
            'customer_avg_amount_90d': customer_data['amount'].mean() if len(customer_data) > 0 else 0,
            'customer_total_quantity_90d': customer_data['quantity'].sum(),
            'customer_unique_products_90d': customer_data['product_id'].nunique(),
            'days_since_customer_last_purchase': self._days_since_last_purchase(customer_data, sample_date),
            
            # 產品90天特徵  
            'product_sale_days_90d': product_data['transaction_date'].nunique(),
            'product_total_quantity_90d': product_data['quantity'].sum(),
            'product_unique_customers_90d': product_data['customer_id'].nunique(),
            'product_avg_quantity_per_sale_90d': product_data['quantity'].mean() if len(product_data) > 0 else 0,
            
            # 客戶-產品90天特徵
            'cp_purchase_count_90d': len(cp_data),
            'cp_total_quantity_90d': cp_data['quantity'].sum(),
            'cp_avg_quantity_90d': cp_data['quantity'].mean() if len(cp_data) > 0 else 0,
            'cp_total_amount_90d': cp_data['amount'].sum(),
            'days_since_cp_last_purchase': self._days_since_last_purchase(cp_data, sample_date),
        }
        
        return features
    
    def _days_since_last_purchase(self, data, reference_date):
        """計算距離最後一次購買的天數"""
        if len(data) == 0:
            return 999
        
        last_purchase = data['transaction_date'].max()
        
        # Convert to datetime objects for comparison
        if hasattr(reference_date, 'date'):
            ref_date = reference_date.date()
        else:
            ref_date = reference_date
            
        if hasattr(last_purchase, 'date'):
            last_date = last_purchase.date()
        else:
            last_date = pd.to_datetime(last_purchase).date()
        
        days_diff = (ref_date - last_date).days
        return min(days_diff, 999)
    
    def train_on_historical_data(self, train_data):
        """第一階段：基於純歷史數據訓練模型"""
        self.logger.info("=== 第一階段：純歷史數據訓練 ===")
        
        # 生成純歷史訓練樣本
        training_samples = self.generate_historical_training_samples(train_data)
        
        if not training_samples:
            self.logger.error("純歷史樣本生成失敗")
            return False
        
        # 轉換為DataFrame並訓練
        samples_df = pd.DataFrame(training_samples)
        
        # 檢查正負樣本比例
        positive_samples = (samples_df['label'] == 1).sum()
        negative_samples = (samples_df['label'] == 0).sum()
        
        self.logger.info(f"純歷史樣本統計:")
        self.logger.info(f"  正樣本: {positive_samples:,} ({positive_samples/len(samples_df)*100:.2f}%)")
        self.logger.info(f"  負樣本: {negative_samples:,} ({negative_samples/len(samples_df)*100:.2f}%)")
        
        if positive_samples == 0:
            self.logger.error("沒有正樣本，無法訓練")
            return False
        
        # 準備特徵
        feature_columns = [col for col in samples_df.columns 
                          if col not in ['label', 'sample_date', 'customer_id', 'product_id']]
        
        X = samples_df[feature_columns].fillna(0)
        y = samples_df['label']
        
        # 訓練模型（不需要eval_set，因為我們要做真實驗證）
        self.model = CatBoostClassifier(**MLConfig.CATBOOST_PARAMS)
        
        try:
            self.model.fit(
                X, y,
                cat_features=[i for i, col in enumerate(feature_columns) 
                             if col in MLConfig.CATEGORICAL_FEATURES],
                verbose=100
            )
            
            self.feature_names = feature_columns
            self.logger.info("純歷史模型訓練完成")
            
            return True
            
        except Exception as e:
            self.logger.error(f"模型訓練失敗: {e}")
            return False
    
    def perform_real_validation(self, train_data, val_data):
        """執行真實驗證：用訓練好的模型預測VAL期間"""
        self.logger.info("=== 執行真實VAL預測驗證 ===")
        
        val_period = self.training_periods['val_period']
        prediction_date = val_period['start']
        
        # 1. 獲取VAL預測所需的特徵數據（來自TRAIN數據）
        feature_end_date = prediction_date - timedelta(days=1)  # 預測前一天
        feature_start_date = feature_end_date - timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
        
        # Convert dates to datetime for comparison
        feature_start_datetime = pd.to_datetime(feature_start_date)
        feature_end_datetime = pd.to_datetime(feature_end_date)
        
        feature_data = train_data[
            (train_data['transaction_date'] >= feature_start_datetime) &
            (train_data['transaction_date'] <= feature_end_datetime)
        ]
        
        self.logger.info(f"VAL預測特徵期間: {feature_start_date} ~ {feature_end_date}")
        self.logger.info(f"特徵數據: {len(feature_data):,} 筆記錄")
        
        # 2. 獲取需要預測的客戶-產品組合（基於歷史活動）
        val_combinations = self.get_validation_combinations(feature_data)
        
        self.logger.info(f"需要預測的組合: {len(val_combinations):,} 對")
        
        # 3. 為每個組合進行預測
        predictions = []
        for i, (customer_id, product_id) in enumerate(val_combinations):
            if i % 1000 == 0 and i > 0:
                self.logger.info(f"VAL預測進度: {i:,}/{len(val_combinations):,}")
            
            # 計算特徵
            features = self._calculate_features(customer_id, product_id, feature_data, prediction_date)
            feature_vector = [features[col] for col in self.feature_names]
            
            # 預測
            try:
                prob = self.model.predict_proba([feature_vector])[0][1]
                if prob >= MLConfig.PREDICTION_THRESHOLD:
                    predictions.append((customer_id, product_id))
            except Exception as e:
                self.logger.warning(f"預測失敗 {customer_id}-{product_id}: {e}")
        
        self.logger.info(f"高信心預測: {len(predictions):,} 個組合")
        
        # 4. 獲取VAL期間實際購買記錄
        actual_purchases = set(zip(val_data['customer_id'], val_data['product_id']))
        predicted_purchases = set(predictions)
        
        self.logger.info(f"實際購買: {len(actual_purchases):,} 個組合")
        
        # 5. 計算真實性能指標
        tp = len(predicted_purchases & actual_purchases)
        fp = len(predicted_purchases - actual_purchases)
        fn = len(actual_purchases - predicted_purchases)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        self.real_validation_metrics = {
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'total_predictions': len(predictions),
            'total_actual': len(actual_purchases),
            'validation_method': 'real_time_series_validation',
            'validated_at': datetime.now().isoformat()
        }
        
        self.logger.info(f"真實驗證結果:")
        self.logger.info(f"  True Positives: {tp}")
        self.logger.info(f"  False Positives: {fp}")
        self.logger.info(f"  False Negatives: {fn}")
        self.logger.info(f"  Precision: {precision:.3f}")
        self.logger.info(f"  Recall: {recall:.3f}")
        self.logger.info(f"  F1 Score: {f1:.3f}")
        
        return True
    
    def get_validation_combinations(self, feature_data):
        """獲取需要驗證預測的客戶-產品組合"""
        # 獲取有歷史活動的客戶和產品
        active_customers = feature_data['customer_id'].unique()
        active_products = feature_data['product_id'].unique()
        
        # 只預測有歷史購買關係的組合
        historical_pairs = set(zip(feature_data['customer_id'], feature_data['product_id']))
        
        # 限制組合數量避免過度計算
        max_combinations = 5000
        if len(historical_pairs) > max_combinations:
            # 按購買頻率排序選擇
            pair_activity = feature_data.groupby(['customer_id', 'product_id']).size()
            top_pairs = pair_activity.nlargest(max_combinations).index.tolist()
            historical_pairs = set(top_pairs)
        
        return list(historical_pairs)
    
    def train_final_model(self, full_data):
        """第二階段：使用完整數據訓練最終模型"""
        self.logger.info("=== 第二階段：完整數據訓練 ===")
        
        # 使用完整數據生成訓練樣本
        full_samples = self.generate_historical_training_samples(full_data)
        
        if not full_samples:
            self.logger.error("完整樣本生成失敗")
            return False
        
        # 轉換為DataFrame並訓練
        samples_df = pd.DataFrame(full_samples)
        
        positive_samples = (samples_df['label'] == 1).sum()
        negative_samples = (samples_df['label'] == 0).sum()
        
        self.logger.info(f"完整數據樣本統計:")
        self.logger.info(f"  正樣本: {positive_samples:,} ({positive_samples/len(samples_df)*100:.2f}%)")
        self.logger.info(f"  負樣本: {negative_samples:,} ({negative_samples/len(samples_df)*100:.2f}%)")
        
        # 準備特徵
        feature_columns = [col for col in samples_df.columns 
                          if col not in ['label', 'sample_date', 'customer_id', 'product_id']]
        
        X = samples_df[feature_columns].fillna(0)
        y = samples_df['label']
        
        # 訓練最終模型
        self.model = CatBoostClassifier(**MLConfig.CATBOOST_PARAMS)
        
        try:
            self.model.fit(
                X, y,
                cat_features=[i for i, col in enumerate(feature_columns) 
                             if col in MLConfig.CATEGORICAL_FEATURES],
                verbose=100
            )
            
            self.feature_names = feature_columns
            
            self.final_model_info = {
                'training_samples': len(X),
                'positive_samples': int(positive_samples),
                'feature_count': len(feature_columns),
                'stage': 'final_full_data_training',
                'trained_at': datetime.now().isoformat()
            }
            
            self.logger.info("最終模型訓練完成")
            return True
            
        except Exception as e:
            self.logger.error(f"最終模型訓練失敗: {e}")
            return False
    
    def save_model(self):
        """保存模型和真實驗證元數據"""
        try:
            # 保存模型
            model_path = MLConfig.get_current_model_path()
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # 保存特徵名稱
            feature_names_path = MLConfig.get_feature_names_path()
            with open(feature_names_path, 'wb') as f:
                pickle.dump(self.feature_names, f)
            
            # 保存元數據（使用真實驗證的性能指標）
            metadata = {
                'model_type': 'TrueValidationCatBoostClassifier',
                'training_method': 'true_validation_two_stage',
                'validation_approach': 'real_time_series_validation',
                'no_data_leakage': True,
                'training_periods': {
                    k: {
                        'start': v['start'].isoformat(),
                        'end': v['end'].isoformat(),
                        'description': v['description']
                    }
                    for k, v in self.training_periods.items()
                },
                'training_data_days': MLConfig.TRAINING_DATA_DAYS,
                'feature_calculation_days': MLConfig.FEATURE_CALCULATION_DAYS,
                'time_buffer_days': 7,
                'feature_count': len(self.feature_names),
                'catboost_params': MLConfig.CATBOOST_PARAMS,
                'metrics': self.real_validation_metrics,  # 使用真實驗證的性能
                'real_validation_metrics': self.real_validation_metrics,
                'final_model_info': self.final_model_info,
                'created_at': datetime.now().isoformat(),
                'version': '3.0_no_leakage'
            }
            
            metadata_path = MLConfig.get_metadata_path()
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"模型已保存:")
            self.logger.info(f"  模型文件: {model_path}")
            self.logger.info(f"  特徵文件: {feature_names_path}")
            self.logger.info(f"  元數據文件: {metadata_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存模型失敗: {e}")
            return False
    
    def train_with_true_validation(self):
        """完整的真實驗證兩段式訓練流程"""
        self.logger.info("=== 開始真實驗證兩段式訓練 ===")
        
        # 計算訓練時間期間
        periods = self.calculate_and_display_periods()
        if not periods:
            return False
        
        # 載入第一段訓練數據
        stage1_train = periods['stage1_train']
        train_data = self.load_data_for_period(
            stage1_train['start'],
            stage1_train['end'],
            "第一段訓練"
        )
        
        # 載入VAL數據
        val_period = periods['val_period']
        val_data = self.load_data_for_period(
            val_period['start'],
            val_period['end'],
            "真實驗證期間"
        )
        
        if train_data is None or val_data is None:
            self.logger.error("數據載入失敗")
            return False
        
        # 第一階段：基於純歷史數據訓練
        if not self.train_on_historical_data(train_data):
            self.logger.error("第一階段訓練失敗")
            return False
        
        # 執行真實驗證
        if not self.perform_real_validation(train_data, val_data):
            self.logger.error("真實驗證失敗")
            return False
        
        # 第二階段：載入完整數據並訓練最終模型
        stage2_train = periods['stage2_train']
        full_data = self.load_data_for_period(
            stage2_train['start'],
            stage2_train['end'],
            "第二段完整數據"
        )
        
        if full_data is None:
            self.logger.error("完整數據載入失敗")
            return False
        
        if not self.train_final_model(full_data):
            self.logger.error("最終模型訓練失敗")
            return False
        
        # 保存模型
        if not self.save_model():
            self.logger.error("模型保存失敗")
            return False
        
        self.logger.info("=== 真實驗證兩段式訓練完成 ===")
        self.logger.info(f"真實驗證性能:")
        self.logger.info(f"  F1分數: {self.real_validation_metrics['f1_score']:.3f}")
        self.logger.info(f"  精確度: {self.real_validation_metrics['precision']:.3f}")
        self.logger.info(f"  召回率: {self.real_validation_metrics['recall']:.3f}")
        self.logger.info(f"  True Positives: {self.real_validation_metrics['true_positives']}")
        self.logger.info(f"  False Positives: {self.real_validation_metrics['false_positives']}")
        
        return True

def main():
    """測試函數"""
    print("=== 真實驗證兩段式訓練器測試 ===")
    
    trainer = TrueValidationTrainer()
    success = trainer.train_with_true_validation()
    
    if success:
        print("✓ 真實驗證兩段式訓練成功")
        metrics = trainer.real_validation_metrics
        print(f"真實性能: F1={metrics['f1_score']:.3f}, P={metrics['precision']:.3f}, R={metrics['recall']:.3f}")
    else:
        print("✗ 真實驗證兩段式訓練失敗")
    
    return success

if __name__ == "__main__":
    main()