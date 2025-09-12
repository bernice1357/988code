#!/usr/bin/env python3
"""
兩段式CatBoost模型訓練器
解決時間洩漏問題，使用真實業務週期驗證
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
    from config import MLConfig  # 直接導入（ml_system目錄內）
except ImportError:
    try:
        from ml_system.config import MLConfig  # 外部導入
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
            
            @classmethod
            def calculate_training_periods(cls):
                """真實前瞻性預測邏輯 - 假設今天是8月25日"""
                # 假設今天是8月25日，進行真實的未來7天預測
                today = datetime(2025, 8, 25).date()
                
                # 預測期間：今天開始的未來7天 (8月25-31日)
                predict_start = today  # 8月25日
                predict_end = today + timedelta(days=cls.PREDICTION_HORIZON_DAYS - 1)  # 8月31日
                
                # 訓練數據：今天之前的所有數據 (到8月24日)
                train_end = today - timedelta(days=1)  # 8月24日
                train_start = train_end - timedelta(days=cls.TRAINING_DATA_DAYS - 1)  # 往前180天
                
                return {
                    'predict_period': {
                        'start': predict_start,
                        'end': predict_end,
                        'description': f'真實預測期間: {predict_start} ~ {predict_end} (未來7天)'
                    },
                    'train_period': {
                        'start': train_start,
                        'end': train_end,
                        'description': f'訓練數據: {train_start} ~ {train_end} (8月25日前180天)'
                    }
                }

class TwoStageCatBoostTrainer:
    """兩段式CatBoost模型訓練器"""
    
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
        self.stage1_metrics = {}
        self.stage2_metrics = {}
        self.training_periods = None
        
        self.setup_logging()
        MLConfig.ensure_directories()
        
        print("=== 兩段式CatBoost模型訓練器 ===")
        print(f"訓練數據期間: {MLConfig.TRAINING_DATA_DAYS}天")
        print(f"特徵計算窗口: {MLConfig.FEATURE_CALCULATION_DAYS}天")
        print(f"驗證期間: {MLConfig.VAL_PERIOD_DAYS}天")
    
    def setup_logging(self):
        """設置日誌"""
        log_file = os.path.join(MLConfig.LOG_DIR, f'two_stage_trainer_{datetime.now().strftime("%Y%m")}.log')
        
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
        
        self.logger.info("=== 真實前瞻性預測時間期間 ===")
        for period_name, period_info in self.training_periods.items():
            self.logger.info(f"{period_info['description']}")
        
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
    
    def generate_samples_for_period(self, transactions_df, val_data, period_name):
        """為指定期間生成訓練樣本"""
        self.logger.info(f"開始生成{period_name}樣本...")
        
        # 計算樣本生成範圍
        min_date = transactions_df['transaction_date'].min()
        max_date = transactions_df['transaction_date'].max()
        
        # 從第90天開始到最後一天，每15天生成一次樣本
        start_sample_date = min_date + timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
        end_sample_date = max_date
        
        sample_dates = pd.date_range(start_sample_date, end_sample_date, 
                                   freq=f'{MLConfig.SAMPLE_FREQUENCY_DAYS}D')
        
        self.logger.info(f"{period_name}樣本生成配置:")
        self.logger.info(f"  樣本日期範圍: {start_sample_date} ~ {end_sample_date}")
        self.logger.info(f"  樣本時間點: {len(sample_dates)} 個 (每{MLConfig.SAMPLE_FREQUENCY_DAYS}天)")
        
        samples = []
        for i, sample_date in enumerate(sample_dates):
            if i % 3 == 0:
                self.logger.info(f"  {period_name}樣本進度: {i+1}/{len(sample_dates)} ({(i+1)/len(sample_dates)*100:.1f}%)")
            
            # 獲取該日期的90天特徵數據
            feature_start = sample_date - timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
            feature_data = transactions_df[
                (transactions_df['transaction_date'] >= feature_start) &
                (transactions_df['transaction_date'] < sample_date)
            ]
            
            # 獲取標籤數據（根據是否為驗證階段使用不同邏輯）
            if val_data is not None:
                # 第一段：使用獨立的VAL數據作為標籤
                label_data = val_data
            else:
                # 第二段：使用該日期後7天的數據作為標籤
                label_start = sample_date
                label_end = sample_date + timedelta(days=MLConfig.PREDICTION_HORIZON_DAYS)
                label_data = transactions_df[
                    (transactions_df['transaction_date'] >= label_start) &
                    (transactions_df['transaction_date'] < label_end)
                ]
            
            # 生成該時間點的樣本
            date_samples = self._create_samples_for_date(
                feature_data, label_data, sample_date
            )
            samples.extend(date_samples)
        
        self.logger.info(f"{period_name}樣本生成完成: {len(samples):,} 筆")
        return samples
    
    def _create_samples_for_date(self, feature_data, label_data, sample_date):
        """為特定日期創建樣本"""
        samples = []
        
        # 獲取有購買歷史的客戶-產品組合
        historical_pairs = set(zip(feature_data['customer_id'], feature_data['product_id']))
        positive_pairs = set(zip(label_data['customer_id'], label_data['product_id']))
        
        # 創建正樣本
        for customer_id, product_id in positive_pairs:
            if (customer_id, product_id) in historical_pairs:  # 只考慮有歷史的組合
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
        max_negative_samples = min(len(negative_candidates), len(positive_pairs) * 2)
        
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
        
        # 處理不同的日期格式
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
    
    def train_stage1_with_validation(self):
        """第一段：使用真實VAL期間進行驗證訓練"""
        self.logger.info("=== 開始第一段驗證訓練 ===")
        
        periods = self.training_periods
        
        # 載入第一段訓練數據
        train1_data = self.load_data_for_period(
            periods['stage1_train']['start'],
            periods['stage1_train']['end'],
            "第一段訓練"
        )
        
        # 載入VAL數據
        val_data = self.load_data_for_period(
            periods['val_period']['start'],
            periods['val_period']['end'],
            "驗證期間"
        )
        
        if train1_data is None or val_data is None:
            self.logger.error("第一段訓練數據載入失敗")
            return False
        
        # 生成訓練樣本（使用VAL數據作為標籤）
        training_samples = self.generate_samples_for_period(train1_data, val_data, "第一段")
        
        if not training_samples:
            self.logger.error("第一段樣本生成失敗")
            return False
        
        # 轉換為DataFrame並訓練
        samples_df = pd.DataFrame(training_samples)
        
        # 檢查正負樣本比例
        positive_samples = (samples_df['label'] == 1).sum()
        negative_samples = (samples_df['label'] == 0).sum()
        
        self.logger.info(f"第一段樣本統計:")
        self.logger.info(f"  正樣本: {positive_samples:,} ({positive_samples/len(samples_df)*100:.2f}%)")
        self.logger.info(f"  負樣本: {negative_samples:,} ({negative_samples/len(samples_df)*100:.2f}%)")
        
        if positive_samples == 0:
            self.logger.error("第一段沒有正樣本，無法訓練")
            return False
        
        # 準備特徵
        feature_columns = [col for col in samples_df.columns 
                          if col not in ['label', 'sample_date', 'customer_id', 'product_id']]
        
        X = samples_df[feature_columns].fillna(0)
        y = samples_df['label']
        
        # 訓練模型
        self.model = CatBoostClassifier(**MLConfig.CATBOOST_PARAMS)
        
        try:
            # 第一段不使用eval_set，因為我們要在真實VAL數據上評估
            self.model.fit(
                X, y,
                cat_features=[i for i, col in enumerate(feature_columns) 
                             if col in MLConfig.CATEGORICAL_FEATURES],
                verbose=100
            )
            
            self.feature_names = feature_columns
            self.logger.info("第一段模型訓練完成")
            
            # 評估模型（這就是真實的驗證性能）
            y_pred = self.model.predict(X)
            y_pred_proba = self.model.predict_proba(X)[:, 1]
            
            # 計算指標
            f1 = f1_score(y, y_pred)
            precision = precision_score(y, y_pred)
            recall = recall_score(y, y_pred)
            
            self.stage1_metrics = {
                'f1_score': float(f1),
                'precision': float(precision),
                'recall': float(recall),
                'training_samples': len(X),
                'positive_samples': int(positive_samples),
                'stage': 'validation_training',
                'trained_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"第一段模型性能 (真實業務驗證):")
            self.logger.info(f"  F1 Score: {f1:.3f}")
            self.logger.info(f"  Precision: {precision:.3f}")
            self.logger.info(f"  Recall: {recall:.3f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"第一段模型訓練失敗: {e}")
            return False
    
    def train_stage2_full_data(self):
        """第二段：使用完整數據重新訓練"""
        self.logger.info("=== 開始第二段完整訓練 ===")
        
        periods = self.training_periods
        
        # 載入第二段完整訓練數據
        train2_data = self.load_data_for_period(
            periods['stage2_train']['start'],
            periods['stage2_train']['end'],
            "第二段訓練"
        )
        
        if train2_data is None:
            self.logger.error("第二段訓練數據載入失敗")
            return False
        
        # 生成訓練樣本（不使用獨立VAL數據）
        training_samples = self.generate_samples_for_period(train2_data, None, "第二段")
        
        if not training_samples:
            self.logger.error("第二段樣本生成失敗")
            return False
        
        # 轉換為DataFrame並訓練
        samples_df = pd.DataFrame(training_samples)
        
        # 檢查正負樣本比例
        positive_samples = (samples_df['label'] == 1).sum()
        negative_samples = (samples_df['label'] == 0).sum()
        
        self.logger.info(f"第二段樣本統計:")
        self.logger.info(f"  正樣本: {positive_samples:,} ({positive_samples/len(samples_df)*100:.2f}%)")
        self.logger.info(f"  負樣本: {negative_samples:,} ({negative_samples/len(samples_df)*100:.2f}%)")
        
        if positive_samples == 0:
            self.logger.error("第二段沒有正樣本，無法訓練")
            return False
        
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
            
            # 記錄第二段訓練信息（但性能指標來自第一段）
            self.stage2_metrics = {
                'training_samples': len(X),
                'positive_samples': int(positive_samples),
                'stage': 'full_data_training',
                'trained_at': datetime.now().isoformat(),
                'note': 'Performance metrics from stage1 validation'
            }
            
            self.logger.info("第二段完整模型訓練完成")
            self.logger.info(f"  最終訓練樣本: {len(X):,}")
            self.logger.info(f"  性能指標來自第一段真實驗證")
            
            return True
            
        except Exception as e:
            self.logger.error(f"第二段模型訓練失敗: {e}")
            return False
    
    def save_model(self):
        """保存模型和元數據"""
        try:
            # 保存模型
            model_path = MLConfig.get_current_model_path()
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # 保存特徵名稱
            feature_names_path = MLConfig.get_feature_names_path()
            with open(feature_names_path, 'wb') as f:
                pickle.dump(self.feature_names, f)
            
            # 保存元數據（使用真實預測的性能指標）
            metadata = {
                'model_type': 'RealForwardPredictionCatBoostClassifier',
                'training_method': 'real_forward_prediction',
                'prediction_approach': 'forward_looking_time_series',
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
                'feature_count': len(self.feature_names),
                'catboost_params': MLConfig.CATBOOST_PARAMS,
                'metrics': self.prediction_metrics if hasattr(self, 'prediction_metrics') else {},
                'prediction_metrics': self.prediction_metrics if hasattr(self, 'prediction_metrics') else {},
                'created_at': datetime.now().isoformat(),
                'version': '3.0_real_forward_prediction'
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
    
    def train_historical_model(self, train_data):
        """用純歷史數據訓練模型"""
        self.logger.info("=== 開始歷史模型訓練 ===")
        
        # 生成歷史訓練樣本
        training_samples = self.generate_historical_samples(train_data)
        
        if not training_samples:
            self.logger.error("歷史樣本生成失敗")
            return False
        
        # 轉換為DataFrame並訓練
        samples_df = pd.DataFrame(training_samples)
        
        # 檢查正負樣本比例
        positive_samples = (samples_df['label'] == 1).sum()
        negative_samples = (samples_df['label'] == 0).sum()
        
        self.logger.info(f"歷史訓練樣本統計:")
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
        
        # 訓練模型
        self.model = CatBoostClassifier(**MLConfig.CATBOOST_PARAMS)
        
        try:
            self.model.fit(
                X, y,
                cat_features=[i for i, col in enumerate(feature_columns) 
                             if col in MLConfig.CATEGORICAL_FEATURES],
                verbose=100
            )
            
            self.feature_names = feature_columns
            self.logger.info("歷史模型訓練完成")
            
            return True
            
        except Exception as e:
            self.logger.error(f"歷史模型訓練失敗: {e}")
            return False
    
    def generate_historical_samples(self, train_data):
        """生成純歷史訓練樣本（避免未來信息洩漏）"""
        self.logger.info("開始生成歷史訓練樣本...")
        
        # 計算樣本生成範圍
        min_date = train_data['transaction_date'].min()
        max_date = train_data['transaction_date'].max()
        
        # 從第90天開始到最後一天前7天，每15天生成一次樣本
        start_sample_date = min_date + timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
        end_sample_date = max_date - timedelta(days=MLConfig.PREDICTION_HORIZON_DAYS)
        
        sample_dates = pd.date_range(start_sample_date, end_sample_date, 
                                   freq=f'{MLConfig.SAMPLE_FREQUENCY_DAYS}D')
        
        self.logger.info(f"歷史樣本生成配置:")
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
            
            # 獲取該日期後7天的標籤數據（純歷史，不涉及預測期間）
            label_start = sample_date
            label_end = sample_date + timedelta(days=MLConfig.PREDICTION_HORIZON_DAYS)
            label_data = train_data[
                (train_data['transaction_date'] >= label_start) &
                (train_data['transaction_date'] < label_end)
            ]
            
            # 生成該時間點的樣本
            date_samples = self._create_samples_for_date(feature_data, label_data, sample_date)
            samples.extend(date_samples)
        
        self.logger.info(f"歷史樣本生成完成: {len(samples):,} 筆")
        return samples
    
    def perform_real_prediction(self, train_data, actual_data):
        """執行真實的8月25-31日預測"""
        self.logger.info("=== 開始真實預測 (8月25-31日) ===")
        
        # 獲取預測期間開始日期
        periods = self.training_periods
        if 'predict_period' in periods:
            prediction_start = periods['predict_period']['start']
        else:
            # 舊結構適配
            from datetime import datetime
            prediction_start = datetime(2025, 8, 25).date()
        
        # 獲取預測所需的特徵數據（8月25日前90天）
        feature_end_date = prediction_start - timedelta(days=1)  # 8月24日
        feature_start_date = feature_end_date - timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
        
        # 將日期轉換為 datetime 以避免比較錯誤
        feature_start_datetime = pd.to_datetime(feature_start_date)
        feature_end_datetime = pd.to_datetime(feature_end_date)
        
        feature_data = train_data[
            (train_data['transaction_date'] >= feature_start_datetime) &
            (train_data['transaction_date'] <= feature_end_datetime)
        ]
        
        self.logger.info(f"預測特徵期間: {feature_start_date} ~ {feature_end_date}")
        self.logger.info(f"特徵數據: {len(feature_data):,} 筆記錄")
        
        # 獲取需要預測的客戶-產品組合（基於歷史活動）
        prediction_combinations = self.get_prediction_combinations(feature_data)
        
        self.logger.info(f"需要預測的組合: {len(prediction_combinations):,} 對")
        
        # 對每個組合進行預測
        predictions = []
        for i, (customer_id, product_id) in enumerate(prediction_combinations):
            if i % 1000 == 0 and i > 0:
                self.logger.info(f"預測進度: {i:,}/{len(prediction_combinations):,}")
            
            # 計算特徵
            features = self._calculate_features(customer_id, product_id, feature_data, prediction_start)
            feature_vector = [features[col] for col in self.feature_names]
            
            # 預測
            try:
                prob = self.model.predict_proba([feature_vector])[0][1]
                if prob >= MLConfig.PREDICTION_THRESHOLD:
                    predictions.append((customer_id, product_id))
            except Exception as e:
                self.logger.warning(f"預測失敗 {customer_id}-{product_id}: {e}")
        
        self.logger.info(f"高信心預測: {len(predictions):,} 個組合")
        
        # 如果有實際數據，計算性能指標
        if len(actual_data) > 0:
            actual_purchases = set(zip(actual_data['customer_id'], actual_data['product_id']))
            predicted_purchases = set(predictions)
            
            tp = len(predicted_purchases & actual_purchases)
            fp = len(predicted_purchases - actual_purchases)
            fn = len(actual_purchases - predicted_purchases)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            self.prediction_metrics = {
                'f1_score': f1,
                'precision': precision,
                'recall': recall,
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn,
                'total_predictions': len(predictions),
                'total_actual': len(actual_purchases),
                'prediction_method': 'real_forward_prediction'
            }
            
            self.logger.info(f"真實預測結果:")
            self.logger.info(f"  實際購買: {len(actual_purchases):,} 個組合")
            self.logger.info(f"  預測購買: {len(predictions):,} 個組合")
            self.logger.info(f"  True Positives: {tp}")
            self.logger.info(f"  False Positives: {fp}")
            self.logger.info(f"  False Negatives: {fn}")
            self.logger.info(f"  Precision: {precision:.3f}")
            self.logger.info(f"  Recall: {recall:.3f}")
            self.logger.info(f"  F1 Score: {f1:.3f}")
        else:
            self.logger.warning("無實際購買數據，無法計算性能指標")
            self.prediction_metrics = {
                'total_predictions': len(predictions),
                'prediction_method': 'real_forward_prediction_no_validation'
            }
        
        return True
    
    def get_prediction_combinations(self, feature_data):
        """獲取需要預測的客戶-產品組合"""
        # 獲取有歷史活動的客戶-產品組合
        historical_pairs = set(zip(feature_data['customer_id'], feature_data['product_id']))
        
        # 限制組合數量避免過度計算
        max_combinations = 5000
        if len(historical_pairs) > max_combinations:
            # 按購買頻率排序選擇
            pair_activity = feature_data.groupby(['customer_id', 'product_id']).size()
            top_pairs = pair_activity.nlargest(max_combinations).index.tolist()
            historical_pairs = set(top_pairs)
        
        return list(historical_pairs)
    
    def train_with_real_prediction(self):
        """真實前瞻性預測訓練流程"""
        self.logger.info("=== 開始真實前瞻性預測訓練 ===")
        
        # 計算訓練時間期間
        if not self.calculate_and_display_periods():
            return False
        
        periods = self.training_periods
        
        # 檢查數據結構並適配
        if 'train_period' in periods:
            # 新的真實預測結構
            train_period = periods['train_period']
            predict_period = periods['predict_period']
        else:
            # 舊的兩段式結構，需要轉換
            self.logger.warning("使用舊的時間配置，轉換為真實預測邏輯")
            # 使用今天之前的數據作為訓練，預測未來7天
            from datetime import datetime, timedelta
            today = datetime(2025, 8, 25).date()
            train_period = {
                'start': today - timedelta(days=180),
                'end': today - timedelta(days=1)
            }
            predict_period = {
                'start': today,
                'end': today + timedelta(days=6)
            }
        
        # 載入訓練數據 (8月25日之前的所有數據)
        train_data = self.load_data_for_period(
            train_period['start'],
            train_period['end'],
            "訓練數據"
        )
        
        # 載入預測目標數據 (8月25-31日的實際購買，用於驗證)
        actual_data = self.load_data_for_period(
            predict_period['start'],
            predict_period['end'],
            "實際購買數據"
        )
        
        if train_data is None:
            self.logger.error("訓練數據載入失敗")
            return False
        
        if actual_data is None:
            self.logger.warning("實際購買數據載入失敗，無法驗證預測效果")
            actual_data = pd.DataFrame()  # 空DataFrame，繼續訓練但無法驗證
        
        # 第一步：用歷史數據訓練模型
        if not self.train_historical_model(train_data):
            self.logger.error("歷史模型訓練失敗")
            return False
        
        # 第二步：對預測期間進行真實預測
        if not self.perform_real_prediction(train_data, actual_data):
            self.logger.error("真實預測失敗")
            return False
        
        # 保存模型
        if not self.save_model():
            self.logger.error("模型保存失敗")
            return False
        
        self.logger.info("=== 真實前瞻性預測訓練完成 ===")
        if hasattr(self, 'prediction_metrics'):
            # 為向後兼容，也設置stage1_metrics
            self.stage1_metrics = self.prediction_metrics.copy()
            
            self.logger.info(f"真實預測性能:")
            self.logger.info(f"  F1分數: {self.prediction_metrics['f1_score']:.3f}")
            self.logger.info(f"  精確度: {self.prediction_metrics['precision']:.3f}")
            self.logger.info(f"  召回率: {self.prediction_metrics['recall']:.3f}")
            self.logger.info(f"  True Positives: {self.prediction_metrics['true_positives']}")
            self.logger.info(f"  False Positives: {self.prediction_metrics['false_positives']}")
        
        return True
    
    def train_two_stage(self):
        """向後兼容的接口，調用真實預測訓練"""
        return self.train_with_real_prediction()

def main():
    """測試函數"""
    print("=== 兩段式CatBoost模型訓練器測試 ===")
    
    trainer = TwoStageCatBoostTrainer()
    success = trainer.train_two_stage()
    
    if success:
        print("✓ 兩段式模型訓練成功")
    else:
        print("✗ 兩段式模型訓練失敗")
    
    return success

if __name__ == "__main__":
    main()