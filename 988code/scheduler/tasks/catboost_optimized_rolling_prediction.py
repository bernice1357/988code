#!/usr/bin/env python3
"""
優化滾動預測版本 CatBoost 客戶補貨預測模型 (Scheduler Integration Version)
結合改進版的優點：
1. 增強時間特徵 (從改進版移植)
2. 只預測最有把握的那一天 (提高閾值)
3. 保持滾動預測的動態更新能力
4. 待處理預測列表機制
5. 新增數量欄位 (直接取最近3次最低數量)
"""

import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime, timedelta
from catboost import CatBoostClassifier
import warnings
warnings.filterwarnings('ignore')

class OptimizedRollingPredictionModel:
    """
    優化版滾動預測客戶補貨模型 (Scheduler Version)
    """
    
    def __init__(self, db_config=None, rolling_window_days=90, prediction_horizon=7):
        self.model = None
        self.feature_names = None
        self.cat_features = ['customer_id', 'product_id', 'day_of_week', 'weekday_name', 'preferred_weekday']
        self.is_trained = False
        
        # 滾動預測參數
        self.rolling_window_days = rolling_window_days
        self.prediction_horizon = prediction_horizon
        
        # 客戶過濾條件
        self.min_purchases_90d = 3
        self.max_days_inactive = 30
        self.min_cp_history = 2
        
        # 優化的預測閾值 (提高品質)
        self.prediction_threshold = 0.7  # 從 0.3 提高到 0.7
        
        # 待處理預測列表
        self.pending_predictions = {}
        
        self.db_config = db_config or {
            'host': '26.210.160.206',
            'database': '988',
            'user': 'n8n',
            'password': '1234',
            'port': 5433
        }
        
        print("=== 優化滾動預測 CatBoost 客戶補貨模型 (Scheduler) ===")
        print(f"滾動窗口: {rolling_window_days} 天")
        print(f"預測範圍: 未來 {prediction_horizon} 天")
        print(f"預測閾值: {self.prediction_threshold} (高品質策略)")
        print("特徵包含: 增強時間特徵、數量預測")
        print("=" * 60)
    
    def connect_database(self):
        """建立資料庫連接"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"資料庫連接失敗: {e}")
            return None
    
    def get_latest_transaction_date(self, conn):
        """獲取資料庫中最新的交易日期"""
        query = """
        SELECT MAX(transaction_date) as latest_date
        FROM order_transactions 
        WHERE document_type = '銷貨'
        AND is_active = 'active'
        """
        
        result = pd.read_sql(query, conn)
        return pd.to_datetime(result.iloc[0]['latest_date'])
    
    def load_rolling_training_data(self, conn, end_date):
        """載入滾動窗口的訓練數據"""
        end_date = pd.to_datetime(end_date)
        start_date = end_date - timedelta(days=self.rolling_window_days)
        
        print(f"\n=== 載入滾動訓練數據 ===")
        print(f"訓練期間: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        query = """
        SELECT 
            ot.customer_id,
            ot.product_id,
            ot.transaction_date,
            SUM(ot.quantity) as quantity
        FROM order_transactions ot
        JOIN product_master pm ON ot.product_id = pm.product_id
        WHERE ot.transaction_date BETWEEN %s::date AND %s::date
            AND ot.document_type = '銷貨'
            AND pm.is_active = 'active'
            AND ot.quantity > 0
        GROUP BY ot.customer_id, ot.product_id, ot.transaction_date
        ORDER BY ot.customer_id, ot.product_id, ot.transaction_date
        """
        
        try:
            df = pd.read_sql(query, conn, params=[start_date.date(), end_date.date()])
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            
            print(f"載入完成: {len(df):,} 筆交易")
            print(f"  - 客戶數: {df['customer_id'].nunique():,}")
            print(f"  - 產品數: {df['product_id'].nunique():,}")
            print(f"  - 客戶-產品對: {df.groupby(['customer_id', 'product_id']).ngroups:,}")
            
            return df
            
        except Exception as e:
            print(f"數據載入失敗: {e}")
            return None
    
    def filter_qualified_customers(self, transactions_df, reference_date):
        """過濾符合條件的客戶"""
        print(f"\n=== 客戶過濾 (基準日期: {reference_date.strftime('%Y-%m-%d')}) ===")
        reference_date = pd.to_datetime(reference_date)
        
        customer_stats = transactions_df.groupby('customer_id').agg({
            'transaction_date': ['count', 'min', 'max'],
            'quantity': 'sum'
        }).round(2)
        
        customer_stats.columns = ['total_purchases', 'first_purchase', 'last_purchase', 'total_quantity']
        customer_stats = customer_stats.reset_index()
        customer_stats['days_since_last'] = (reference_date - customer_stats['last_purchase']).dt.days
        
        print(f"總客戶數: {len(customer_stats):,}")
        
        condition1 = customer_stats['total_purchases'] >= self.min_purchases_90d
        qualified_customers_1 = customer_stats[condition1]
        print(f"條件1 (>={self.min_purchases_90d}次購買): {len(qualified_customers_1):,} 位")
        
        condition2 = qualified_customers_1['days_since_last'] <= self.max_days_inactive
        qualified_customers_2 = qualified_customers_1[condition2]
        print(f"條件2 (<={self.max_days_inactive}天未活動): {len(qualified_customers_2):,} 位")
        
        qualified_customer_ids = set(qualified_customers_2['customer_id'])
        
        cp_stats = transactions_df[
            transactions_df['customer_id'].isin(qualified_customer_ids)
        ].groupby(['customer_id', 'product_id']).size().reset_index(name='cp_purchases')
        
        condition3 = cp_stats['cp_purchases'] >= self.min_cp_history
        qualified_cp_pairs = cp_stats[condition3]
        print(f"條件3 (客戶-產品對>={self.min_cp_history}次): {len(qualified_cp_pairs):,} 對")
        
        qualified_transactions = transactions_df[
            transactions_df.set_index(['customer_id', 'product_id']).index.isin(
                qualified_cp_pairs.set_index(['customer_id', 'product_id']).index
            )
        ]
        
        print(f"過濾後交易數據: {len(qualified_transactions):,} 筆")
        print(f"最終客戶-產品對: {qualified_transactions.groupby(['customer_id', 'product_id']).ngroups:,}")
        
        return qualified_transactions
    
    def get_min_recent_quantity(self, transactions_df, customer_id, product_id):
        """取得最近3次交易的最低數量"""
        cp_history = transactions_df[
            (transactions_df['customer_id'] == customer_id) &
            (transactions_df['product_id'] == product_id)
        ].sort_values('transaction_date')
        
        if len(cp_history) == 0:
            return 1
        
        return max(1, int(cp_history['quantity'].tail(3).min()))
    
    def extract_optimized_time_features(self, transactions_df, customer_id, product_id, target_date):
        """
        提取優化的增強時間特徵 (從改進版移植並優化)
        """
        target_date = pd.to_datetime(target_date)
        
        features = {
            'customer_id': customer_id,
            'product_id': product_id,
            'day_of_week': target_date.weekday(),
            'weekday_name': target_date.strftime('%A'),
            'day_of_month': target_date.day,
            'is_weekend': 1 if target_date.weekday() >= 5 else 0,
        }
        
        cp_history = transactions_df[
            (transactions_df['customer_id'] == customer_id) &
            (transactions_df['product_id'] == product_id) &
            (transactions_df['transaction_date'] < target_date)
        ].copy().sort_values('transaction_date')
        
        if len(cp_history) == 0:
            features.update(self._get_default_features(target_date))
            return features
        
        # === 增強時間特徵 1: 客戶偏好分析 ===
        purchase_weekdays = cp_history['transaction_date'].dt.weekday
        if len(purchase_weekdays) > 0:
            preferred_weekday = purchase_weekdays.mode().iloc[0] if len(purchase_weekdays.mode()) > 0 else target_date.weekday()
            features['preferred_weekday'] = preferred_weekday
            features['is_preferred_weekday'] = 1 if target_date.weekday() == preferred_weekday else 0
            
            # 星期偏好強度
            weekday_counts = purchase_weekdays.value_counts()
            features['preferred_weekday_strength'] = weekday_counts.max() / len(purchase_weekdays)
            
            # 星期購買多樣性 (熵)
            if len(weekday_counts) > 1:
                weekday_probs = weekday_counts / len(purchase_weekdays)
                entropy = -np.sum(weekday_probs * np.log2(weekday_probs))
                features['weekday_entropy'] = entropy / np.log2(7)
            else:
                features['weekday_entropy'] = 0
        else:
            features['preferred_weekday'] = target_date.weekday()
            features['is_preferred_weekday'] = 0
            features['preferred_weekday_strength'] = 0
            features['weekday_entropy'] = 0
        
        # === 增強時間特徵 2: 精確時間計算 ===
        last_purchase = cp_history['transaction_date'].max()
        days_since_last = (target_date - last_purchase).days
        features['days_since_last'] = days_since_last
        
        # 時間衰減因子 (多層次)
        features['time_decay_factor'] = np.exp(-days_since_last / 30)
        features['time_decay_squared'] = np.exp(-days_since_last**2 / 900)
        features['time_decay_log'] = np.exp(-np.log1p(days_since_last) / 3)
        
        # === 增強時間特徵 3: 購買週期深度分析 ===
        purchase_dates = cp_history['transaction_date'].sort_values()
        if len(purchase_dates) >= 2:
            intervals = purchase_dates.diff().dt.days.dropna()
            features['avg_interval'] = intervals.mean()
            features['interval_std'] = intervals.std() if len(intervals) > 1 else 0
            features['interval_cv'] = features['interval_std'] / features['avg_interval'] if features['avg_interval'] > 0 else 0
            features['regularity_score'] = 1 / (1 + features['interval_cv']) if features['interval_cv'] > 0 else 1
            
            # 預期購買日期偏差
            expected_next_date = last_purchase + timedelta(days=features['avg_interval'])
            features['expected_purchase_deviation'] = abs((target_date - expected_next_date).days)
            features['is_expected_date'] = 1 if features['expected_purchase_deviation'] <= 1 else 0
            
            # 購買頻率變化趨勢
            if len(intervals) >= 3:
                recent_intervals = intervals.tail(3).mean()
                early_intervals = intervals.head(max(1, len(intervals)-3)).mean()
                features['purchase_acceleration'] = (early_intervals - recent_intervals) / early_intervals if early_intervals > 0 else 0
            else:
                features['purchase_acceleration'] = 0
            
            # 間隔穩定性評分
            features['interval_stability'] = 1 / (1 + features['interval_std']) if features['interval_std'] > 0 else 1
            
        else:
            features.update({
                'avg_interval': 0, 'interval_std': 0, 'interval_cv': 0,
                'regularity_score': 0, 'expected_purchase_deviation': 999,
                'is_expected_date': 0, 'purchase_acceleration': 0, 'interval_stability': 0
            })
        
        # === 增強時間特徵 4: 最近購買趨勢 ===
        if len(purchase_dates) >= 3:
            recent_3_dates = purchase_dates.tail(3)
            recent_intervals = recent_3_dates.diff().dt.days.dropna()
            
            if len(recent_intervals) >= 2:
                features['recent_interval_trend'] = recent_intervals.iloc[-1] - recent_intervals.iloc[0]
                features['recent_avg_interval'] = recent_intervals.mean()
                features['recent_interval_stability'] = 1 / (1 + recent_intervals.std()) if recent_intervals.std() > 0 else 1
                
                # 最近 vs 整體間隔比較
                overall_avg = features['avg_interval']
                features['recent_vs_overall_ratio'] = features['recent_avg_interval'] / overall_avg if overall_avg > 0 else 1
            else:
                features.update({
                    'recent_interval_trend': 0, 'recent_avg_interval': 0,
                    'recent_interval_stability': 0, 'recent_vs_overall_ratio': 1
                })
        else:
            features.update({
                'recent_interval_trend': 0, 'recent_avg_interval': 0,
                'recent_interval_stability': 0, 'recent_vs_overall_ratio': 1
            })
        
        # === 增強時間特徵 5: 購買統計強化 ===
        features['cp_total_purchases'] = len(cp_history)
        features['cp_total_quantity'] = cp_history['quantity'].sum()
        features['cp_avg_quantity'] = cp_history['quantity'].mean()
        features['cp_quantity_trend'] = cp_history['quantity'].diff().mean() if len(cp_history) > 1 else 0
        
        # 不同時間窗口的購買頻率
        features['cp_recent_7d'] = len(cp_history[cp_history['transaction_date'] >= target_date - timedelta(days=7)])
        features['cp_recent_14d'] = len(cp_history[cp_history['transaction_date'] >= target_date - timedelta(days=14)])
        features['cp_recent_30d'] = len(cp_history[cp_history['transaction_date'] >= target_date - timedelta(days=30)])
        
        # 購買密度
        if len(cp_history) > 1:
            date_span = (cp_history['transaction_date'].max() - cp_history['transaction_date'].min()).days
            features['purchase_density'] = len(cp_history) / max(date_span, 1)
        else:
            features['purchase_density'] = 0
        
        return features
    
    def _get_default_features(self, target_date):
        """獲取默認特徵值"""
        return {
            'preferred_weekday': target_date.weekday(),
            'is_preferred_weekday': 0,
            'preferred_weekday_strength': 0,
            'weekday_entropy': 0,
            'days_since_last': 999,
            'time_decay_factor': 0,
            'time_decay_squared': 0,
            'time_decay_log': 0,
            'avg_interval': 0,
            'interval_std': 0,
            'interval_cv': 0,
            'regularity_score': 0,
            'expected_purchase_deviation': 999,
            'is_expected_date': 0,
            'purchase_acceleration': 0,
            'interval_stability': 0,
            'recent_interval_trend': 0,
            'recent_avg_interval': 0,
            'recent_interval_stability': 0,
            'recent_vs_overall_ratio': 1,
            'cp_total_purchases': 0,
            'cp_total_quantity': 0,
            'cp_avg_quantity': 0,
            'cp_quantity_trend': 0,
            'cp_recent_7d': 0,
            'cp_recent_14d': 0,
            'cp_recent_30d': 0,
            'purchase_density': 0
        }
    
    def train_rolling_model(self, qualified_transactions, training_end_date):
        """訓練滾動模型"""
        print(f"\n=== 訓練優化滾動預測模型 ===")
        
        training_end_date = pd.to_datetime(training_end_date)
        
        # 生成訓練樣本
        val_start = training_end_date - timedelta(days=6)
        val_end = training_end_date
        
        date_range = pd.date_range(val_start, val_end, freq='D')
        business_dates = [d for d in date_range if d.weekday() != 6]
        
        print(f"標籤期間: {val_start.strftime('%Y-%m-%d')} ~ {val_end.strftime('%Y-%m-%d')}")
        print(f"工作日數: {len(business_dates)} 天")
        
        # 創建實際購買集合
        actual_purchases = set()
        for _, row in qualified_transactions.iterrows():
            if row['transaction_date'] >= val_start and row['transaction_date'] <= val_end:
                actual_purchases.add((row['customer_id'], row['product_id'], row['transaction_date'].date()))
        
        print(f"標籤期間實際購買: {len(actual_purchases)} 筆")
        
        # 獲取所有客戶-產品對
        cp_pairs = qualified_transactions.groupby(['customer_id', 'product_id']).size().reset_index()
        cp_pairs = cp_pairs[['customer_id', 'product_id']]
        
        print(f"總客戶-產品對: {len(cp_pairs)}")
        
        # 生成訓練樣本 (使用優化特徵)
        samples = []
        positive_samples = 0
        negative_samples = 0
        
        for idx, (_, cp_row) in enumerate(cp_pairs.iterrows()):
            if idx % 100 == 0:
                print(f"生成樣本進度: {idx}/{len(cp_pairs)} ({idx/len(cp_pairs)*100:.1f}%)")
            
            customer_id = cp_row['customer_id']
            product_id = cp_row['product_id']
            
            for target_date in business_dates:
                features = self.extract_optimized_time_features(
                    qualified_transactions, customer_id, product_id, target_date
                )
                
                actual_purchase = (customer_id, product_id, target_date.date()) in actual_purchases
                features['label'] = 1 if actual_purchase else 0
                features['target_date'] = target_date
                
                samples.append(features)
                
                if actual_purchase:
                    positive_samples += 1
                else:
                    negative_samples += 1
        
        samples_df = pd.DataFrame(samples)
        
        print(f"\n訓練樣本生成完成:")
        print(f"總樣本數: {len(samples_df):,}")
        print(f"正樣本: {positive_samples:,} ({positive_samples/len(samples_df)*100:.2f}%)")
        print(f"負樣本: {negative_samples:,} ({negative_samples/len(samples_df)*100:.2f}%)")
        
        if positive_samples == 0:
            print("警告: 沒有正樣本，無法訓練模型")
            return False
        
        # 訓練模型
        feature_columns = [col for col in samples_df.columns if col not in ['label', 'target_date']]
        
        X = samples_df[feature_columns]
        y = samples_df['label']
        
        print(f"\n開始訓練模型...")
        print(f"特徵數: {len(feature_columns)}")
        
        self.model = CatBoostClassifier(
            iterations=300,  # 增加迭代次數
            learning_rate=0.1,
            depth=6,
            cat_features=self.cat_features,
            random_seed=42,
            verbose=False,
            class_weights=[1, 10]
        )
        
        self.model.fit(X, y)
        self.feature_names = feature_columns
        self.is_trained = True
        
        print("優化滾動模型訓練完成")
        return True
    
    def update_pending_predictions(self, actual_purchases_df):
        """更新待處理預測列表"""
        print(f"\n=== 更新待處理預測列表 ===")
        print(f"更新前待處理預測: {len(self.pending_predictions)} 項")
        
        if len(actual_purchases_df) > 0:
            actual_cp_set = set(zip(actual_purchases_df['customer_id'], 
                                  actual_purchases_df['product_id']))
            print(f"實際購買的客戶-產品對: {len(actual_cp_set)} 項")
            
            removed_count = 0
            for cp_pair in list(self.pending_predictions.keys()):
                if cp_pair in actual_cp_set:
                    del self.pending_predictions[cp_pair]
                    removed_count += 1
            
            print(f"移除已購買預測: {removed_count} 項")
        
        print(f"更新後待處理預測: {len(self.pending_predictions)} 項")
    
    def predict_optimized_rolling_horizon(self, qualified_transactions, prediction_start_date, actual_purchases_df=None):
        """
        優化版滾動預測 - 只預測最有把握的日期，包含預測數量
        """
        print(f"\n=== 優化滾動預測未來 {self.prediction_horizon} 天 ===")
        print(f"預測閾值: {self.prediction_threshold} (高品質策略)")
        
        if not self.is_trained:
            print("模型尚未訓練")
            return None
        
        # 更新待處理預測列表
        if actual_purchases_df is not None:
            self.update_pending_predictions(actual_purchases_df)
        
        prediction_start_date = pd.to_datetime(prediction_start_date)
        prediction_end_date = prediction_start_date + timedelta(days=self.prediction_horizon - 1)
        
        # 生成預測日期列表
        date_range = pd.date_range(prediction_start_date, prediction_end_date, freq='D')
        business_dates = [d for d in date_range if d.weekday() != 6]
        
        print(f"預測期間: {prediction_start_date.strftime('%Y-%m-%d')} ~ {prediction_end_date.strftime('%Y-%m-%d')}")
        print(f"預測工作日數: {len(business_dates)} 天")
        
        # 獲取客戶-產品對
        cp_pairs = qualified_transactions.groupby(['customer_id', 'product_id']).size().reset_index()
        cp_pairs = cp_pairs[['customer_id', 'product_id']]
        
        print(f"總客戶-產品對: {len(cp_pairs)}")
        
        # 過濾掉已經在待處理列表中的客戶-產品對
        filtered_cp_pairs = []
        for _, cp_row in cp_pairs.iterrows():
            cp_key = (cp_row['customer_id'], cp_row['product_id'])
            if cp_key not in self.pending_predictions:
                filtered_cp_pairs.append(cp_row)
        
        print(f"需要新預測的客戶-產品對: {len(filtered_cp_pairs)} (排除 {len(cp_pairs) - len(filtered_cp_pairs)} 個已預測)")
        
        all_predictions = []
        new_pending_count = 0
        high_quality_predictions = 0
        
        for idx, cp_row in enumerate(filtered_cp_pairs):
            if idx % 100 == 0:
                print(f"預測進度: {idx}/{len(filtered_cp_pairs)} ({idx/len(filtered_cp_pairs)*100:.1f}%)")
            
            customer_id = cp_row['customer_id']
            product_id = cp_row['product_id']
            
            # 取得預測數量
            predicted_quantity = self.get_min_recent_quantity(qualified_transactions, customer_id, product_id)
            
            # 找出最佳預測日期
            best_pred = None
            best_prob = 0
            
            for target_date in business_dates:
                features = self.extract_optimized_time_features(
                    qualified_transactions, customer_id, product_id, target_date
                )
                
                feature_values = [features[col] for col in self.feature_names]
                X_pred = pd.DataFrame([feature_values], columns=self.feature_names)
                
                prob = self.model.predict_proba(X_pred)[0, 1]
                
                if prob > best_prob:
                    best_prob = prob
                    best_pred = {
                        'customer_id': customer_id,
                        'product_id': product_id,
                        'prediction_date': target_date.strftime('%Y-%m-%d'),
                        'prediction_weekday': target_date.strftime('%A'),
                        'quantity': predicted_quantity,
                        'purchase_probability': prob,
                        'days_since_last': features['days_since_last'],
                        'regularity_score': features['regularity_score'],
                        'is_preferred_weekday': features['is_preferred_weekday'],
                        'is_expected_date': features['is_expected_date'],
                        'time_decay_factor': features['time_decay_factor'],
                        'expected_deviation': features['expected_purchase_deviation']
                    }
            
            # 只保留高品質預測 (提高閾值)
            if best_pred and best_prob >= self.prediction_threshold:
                all_predictions.append(best_pred)
                high_quality_predictions += 1
                
                # 添加到待處理預測列表
                cp_key = (customer_id, product_id)
                self.pending_predictions[cp_key] = best_pred['prediction_date']
                new_pending_count += 1
        
        predictions_df = pd.DataFrame(all_predictions)
        
        print(f"\n優化滾動預測結果:")
        print(f"高品質預測數: {len(predictions_df):,} 筆 (閾值 >= {self.prediction_threshold})")
        print(f"品質提升率: {high_quality_predictions}/{len(filtered_cp_pairs)} = {high_quality_predictions/len(filtered_cp_pairs)*100:.1f}%")
        print(f"新增待處理預測: {new_pending_count} 項")
        print(f"總待處理預測: {len(self.pending_predictions)} 項")
        
        if len(predictions_df) > 0:
            print(f"\n預測品質統計:")
            print(f"平均購買機率: {predictions_df['purchase_probability'].mean():.3f}")
            print(f"機率範圍: {predictions_df['purchase_probability'].min():.3f} ~ {predictions_df['purchase_probability'].max():.3f}")
            print(f"偏好日預測: {predictions_df['is_preferred_weekday'].sum()} 筆 ({predictions_df['is_preferred_weekday'].mean()*100:.1f}%)")
            print(f"預期日期預測: {predictions_df['is_expected_date'].sum()} 筆 ({predictions_df['is_expected_date'].mean()*100:.1f}%)")
            print(f"平均預測數量: {predictions_df['quantity'].mean():.1f}")
            print(f"數量範圍: {predictions_df['quantity'].min()} ~ {predictions_df['quantity'].max()}")
            
            # 按日期統計
            print(f"\n各日期預測分佈:")
            date_dist = predictions_df['prediction_date'].value_counts().sort_index()
            for date, count in date_dist.items():
                weekday = pd.to_datetime(date).strftime('%A')
                avg_prob = predictions_df[predictions_df['prediction_date'] == date]['purchase_probability'].mean()
                avg_qty = predictions_df[predictions_df['prediction_date'] == date]['quantity'].mean()
                print(f"  {date} ({weekday}): {count:,} 筆, 平均機率: {avg_prob:.3f}, 平均數量: {avg_qty:.1f}")
        
        return predictions_df
    
    def run_optimized_rolling_prediction(self, base_date=None):
        """執行優化版滾動預測流程 (Scheduler 版本)"""
        print("=" * 80)
        print("開始優化滾動預測流程 (Scheduler Integration)")
        print("=" * 80)
        
        conn = self.connect_database()
        if not conn:
            return None
        
        try:
            # 確定基準日期
            if base_date is None:
                base_date = self.get_latest_transaction_date(conn)
            else:
                base_date = pd.to_datetime(base_date)
            
            print(f"基準日期: {base_date.strftime('%Y-%m-%d')}")
            
            # 1. 載入滾動訓練數據
            transactions_df = self.load_rolling_training_data(conn, base_date)
            
            if transactions_df is None or len(transactions_df) == 0:
                print("無法載入交易數據")
                return None
            
            # 2. 過濾符合條件的客戶
            qualified_transactions = self.filter_qualified_customers(transactions_df, base_date)
            
            # 3. 訓練優化滾動模型
            success = self.train_rolling_model(qualified_transactions, base_date)
            
            if not success:
                print("模型訓練失敗")
                return None
            
            # 4. 執行優化預測
            prediction_start = base_date + timedelta(days=1)
            predictions_df = self.predict_optimized_rolling_horizon(qualified_transactions, prediction_start, actual_purchases_df=None)
            
            # 5. 返回結果（不保存 CSV，由上層處理）
            if predictions_df is not None and len(predictions_df) > 0:
                print(f"\n優化滾動預測執行成功")
                print(f"基準日期: {base_date.strftime('%Y-%m-%d')}")
                print(f"預測記錄數: {len(predictions_df):,} 筆")
                print(f"涉及客戶: {predictions_df['customer_id'].nunique():,} 位")
                print(f"涉及產品: {predictions_df['product_id'].nunique():,} 個")
                print(f"平均購買機率: {predictions_df['purchase_probability'].mean():.3f}")
                print(f"總數量: {predictions_df['quantity'].sum():,} 件")
                
                return {
                    'predictions': predictions_df,
                    'model': self,
                    'base_date': base_date,
                    'threshold': self.prediction_threshold
                }
            else:
                print("沒有生成預測結果")
                return None
                
        finally:
            conn.close()

# 當直接執行此文件時的測試函數
if __name__ == "__main__":
    print("=== CatBoost 優化滾動預測模型測試 ===")
    
    predictor = OptimizedRollingPredictionModel(
        rolling_window_days=90,
        prediction_horizon=7
    )
    
    # 測試預測
    base_date = datetime.now() - timedelta(days=1)
    results = predictor.run_optimized_rolling_prediction(base_date=base_date)
    
    if results:
        print("✓ CatBoost 預測測試成功")
    else:
        print("✗ CatBoost 預測測試失敗")