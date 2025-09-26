#!/usr/bin/env python3
"""
CatBoost模型訓練器
使用12個月歷史數據進行訓練，生成可持久化的模型
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
from sklearn.model_selection import train_test_split
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
        TRAINING_DATA_MONTHS = 12
        FEATURE_CALCULATION_DAYS = 90
        PREDICTION_HORIZON_DAYS = 7
        PREDICTION_THRESHOLD = 0.7
        
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

class CatBoostTrainer:
    """CatBoost模型訓練器"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or {
            'host': 'localhost',
            'database': '988',
            'user': 'postgres',
            'password': '1234',
            'port': 5432
        }
        
        self.model = None
        self.feature_names = None
        self.training_metrics = {}
        
        self.setup_logging()
        MLConfig.ensure_directories()
        
        print("=== CatBoost模型訓練器 ===")
        print(f"訓練數據範圍: {MLConfig.TRAINING_DATA_MONTHS}個月")
        print(f"特徵計算窗口: {MLConfig.FEATURE_CALCULATION_DAYS}天")
        print(f"預測目標: 未來{MLConfig.PREDICTION_HORIZON_DAYS}天")
    
    def setup_logging(self):
        """設置日誌"""
        log_file = os.path.join(MLConfig.LOG_DIR, f'model_trainer_{datetime.now().strftime("%Y%m")}.log')
        
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
    
    def load_training_data(self):
        """載入12個月訓練數據"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            # 計算數據範圍
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=MLConfig.TRAINING_DATA_MONTHS * 30)
            
            self.logger.info(f"載入訓練數據: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
            
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
            
            self.logger.info(f"載入交易記錄: {len(df):,} 筆")
            self.logger.info(f"涉及客戶: {df['customer_id'].nunique():,} 位")
            self.logger.info(f"涉及產品: {df['product_id'].nunique():,} 個")
            
            return df
            
        except Exception as e:
            self.logger.error(f"載入訓練數據失敗: {e}")
            return None
        finally:
            conn.close()
    
    def generate_training_samples(self, transactions_df):
        """生成訓練樣本 - 每個樣本用90天特徵 + 7天標籤"""
        self.logger.info("開始生成訓練樣本...")
        
        # 計算有效日期範圍
        min_date = transactions_df['transaction_date'].min()
        max_date = transactions_df['transaction_date'].max()
        
        # 從第90天開始到倒數第7天，每10天生成一次樣本（減少計算量）
        start_sample_date = min_date + timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
        end_sample_date = max_date - timedelta(days=MLConfig.PREDICTION_HORIZON_DAYS)
        
        samples = []
        sample_dates = pd.date_range(start_sample_date, end_sample_date, freq='15D')  # 每15天一個樣本點，保持更多近期數據
        
        self.logger.info(f"樣本生成日期範圍: {start_sample_date} ~ {end_sample_date}")
        self.logger.info(f"預計生成 {len(sample_dates)} 個時間點的樣本")
        
        for i, sample_date in enumerate(sample_dates):
            if i % 5 == 0:
                self.logger.info(f"處理進度: {i+1}/{len(sample_dates)} ({(i+1)/len(sample_dates)*100:.1f}%)")
            
            # 獲取該日期的90天特徵數據
            feature_start = sample_date - timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
            feature_data = transactions_df[
                (transactions_df['transaction_date'] >= feature_start) &
                (transactions_df['transaction_date'] < sample_date)
            ]
            
            # 獲取該日期後7天的標籤數據
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
        
        self.logger.info(f"生成訓練樣本完成: {len(samples):,} 筆")
        return samples
    
    def _create_samples_for_date(self, feature_data, label_data, sample_date):
        """為特定日期創建樣本 - 智能採樣策略"""
        samples = []
        
        # 1. 獲取有購買歷史的客戶-產品組合（智能採樣）
        historical_pairs = set(zip(feature_data['customer_id'], feature_data['product_id']))
        positive_pairs = set(zip(label_data['customer_id'], label_data['product_id']))
        
        self.logger.info(f"歷史組合數: {len(historical_pairs)}, 正樣本數: {len(positive_pairs)}")
        
        # 2. 創建正樣本（所有有購買的組合）
        for customer_id, product_id in positive_pairs:
            features = self._calculate_features(
                customer_id, product_id, feature_data, sample_date
            )
            
            sample = {
                **features,
                'label': 1,
                'sample_date': sample_date,
                'customer_id': customer_id,
                'product_id': product_id
            }
            samples.append(sample)
        
        # 3. 創建負樣本 - 智能選擇
        # 從有歷史但這次沒購買的組合中採樣
        negative_candidates = historical_pairs - positive_pairs
        
        # 限制負樣本數量為正樣本的3-5倍（平衡樣本）
        max_negative_samples = min(len(negative_candidates), len(positive_pairs) * 4)
        
        if max_negative_samples > 0:
            # 隨機選擇負樣本 - 修復numpy選擇錯誤
            negative_candidates_list = list(negative_candidates)
            selected_indices = np.random.choice(
                len(negative_candidates_list), 
                size=max_negative_samples, 
                replace=False
            )
            negative_pairs = [negative_candidates_list[i] for i in selected_indices]
            
            for customer_id, product_id in negative_pairs:
                features = self._calculate_features(
                    customer_id, product_id, feature_data, sample_date
                )
                
                sample = {
                    **features,
                    'label': 0,
                    'sample_date': sample_date,
                    'customer_id': customer_id,
                    'product_id': product_id
                }
                samples.append(sample)
        
        self.logger.info(f"該時間點樣本數: {len(samples)} (正:{len(positive_pairs)}, 負:{len(samples)-len(positive_pairs)})")
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
            return 999  # 大數值表示從未購買
        
        last_purchase = data['transaction_date'].max()
        days_diff = (reference_date - last_purchase).days
        return min(days_diff, 999)  # 限制最大值
    
    def train_model(self):
        """訓練CatBoost模型"""
        self.logger.info("開始模型訓練流程...")
        
        # 1. 載入數據
        transactions_df = self.load_training_data()
        if transactions_df is None:
            self.logger.error("載入訓練數據失敗")
            return False
        
        # 2. 生成樣本
        training_samples = self.generate_training_samples(transactions_df)
        if not training_samples:
            self.logger.error("生成訓練樣本失敗")
            return False
        
        # 3. 轉換為DataFrame
        samples_df = pd.DataFrame(training_samples)
        
        # 檢查正負樣本比例
        positive_samples = (samples_df['label'] == 1).sum()
        negative_samples = (samples_df['label'] == 0).sum()
        
        self.logger.info(f"樣本統計:")
        self.logger.info(f"  正樣本: {positive_samples:,} ({positive_samples/len(samples_df)*100:.2f}%)")
        self.logger.info(f"  負樣本: {negative_samples:,} ({negative_samples/len(samples_df)*100:.2f}%)")
        
        if positive_samples == 0:
            self.logger.error("沒有正樣本，無法訓練模型")
            return False
        
        # 4. 準備特徵
        feature_columns = [col for col in samples_df.columns 
                          if col not in ['label', 'sample_date', 'customer_id', 'product_id']]
        
        X = samples_df[feature_columns].fillna(0)
        y = samples_df['label']
        
        # 5. 分割訓練測試集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        self.logger.info(f"特徵數量: {len(feature_columns)}")
        self.logger.info(f"訓練集大小: {len(X_train):,}")
        self.logger.info(f"測試集大小: {len(X_test):,}")
        
        # 6. 訓練模型
        self.model = CatBoostClassifier(**MLConfig.CATBOOST_PARAMS)
        
        try:
            self.model.fit(
                X_train, y_train,
                cat_features=[i for i, col in enumerate(feature_columns) 
                             if col in MLConfig.CATEGORICAL_FEATURES],
                eval_set=(X_test, y_test),
                verbose=100
            )
            
            self.feature_names = feature_columns
            
        except Exception as e:
            self.logger.error(f"模型訓練失敗: {e}")
            return False
        
        # 7. 評估模型
        self._evaluate_model(X_test, y_test)
        
        self.logger.info("模型訓練完成")
        return True
    
    def _evaluate_model(self, X_test, y_test):
        """評估模型性能"""
        try:
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            # 計算指標
            f1 = f1_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            
            self.training_metrics = {
                'f1_score': float(f1),
                'precision': float(precision),
                'recall': float(recall),
                'test_samples': len(X_test),
                'positive_samples': int((y_test == 1).sum()),
                'trained_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"模型評估結果:")
            self.logger.info(f"  F1 Score: {f1:.3f}")
            self.logger.info(f"  Precision: {precision:.3f}")
            self.logger.info(f"  Recall: {recall:.3f}")
            
        except Exception as e:
            self.logger.error(f"模型評估失敗: {e}")
            self.training_metrics = {'error': str(e)}
    
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
            
            # 保存元數據
            metadata = {
                'model_type': 'CatBoostClassifier',
                'training_data_months': MLConfig.TRAINING_DATA_MONTHS,
                'feature_calculation_days': MLConfig.FEATURE_CALCULATION_DAYS,
                'prediction_horizon_days': MLConfig.PREDICTION_HORIZON_DAYS,
                'feature_count': len(self.feature_names),
                'catboost_params': MLConfig.CATBOOST_PARAMS,
                'metrics': self.training_metrics,
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            metadata_path = MLConfig.get_metadata_path()
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"模型已保存到: {model_path}")
            self.logger.info(f"特徵已保存到: {feature_names_path}")
            self.logger.info(f"元數據已保存到: {metadata_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存模型失敗: {e}")
            return False
    
    def train_and_save(self):
        """完整的訓練和保存流程"""
        self.logger.info("開始完整訓練流程...")
        
        # 訓練模型
        if not self.train_model():
            return False
        
        # 保存模型
        if not self.save_model():
            return False
        
        self.logger.info("訓練和保存流程完成")
        return True

def main():
    """測試函數"""
    print("=== CatBoost模型訓練器測試 ===")
    
    trainer = CatBoostTrainer()
    success = trainer.train_and_save()
    
    if success:
        print("✓ 模型訓練和保存成功")
    else:
        print("✗ 模型訓練失敗")
    
    return success

if __name__ == "__main__":
    main()