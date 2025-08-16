#!/usr/bin/env python3
"""
Prophet客戶補貨預測系統 - 主程式
整合Prophet模型訓練、預測生成、數據庫存儲的完整解決方案
"""

import os
import logging
import psycopg2
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score, accuracy_score
import warnings
warnings.filterwarnings('ignore')

try:
    from prophet import Prophet
    prophet_available = True
except ImportError:
    print("ERROR: Prophet未安裝，請執行: pip install prophet")
    prophet_available = False

class ProphetPredictionSystem:
    """Prophet預測系統主類別"""
    
    def __init__(self):
        self.prophet_models = {}
        self.customer_segments = {}
        self.customer_performance = {}
        
        # 設定日誌
        self.setup_logging()
        
        # 數據庫連接配置
        self.db_config = {
            'host': "26.210.160.206",
            'database': "988",
            'user': "n8n", 
            'password': "1234",
            'port': "5433"
        }
        
        print("=== Prophet客戶補貨預測系統 ===")
    
    def setup_logging(self):
        """設定日誌系統"""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/prophet_system_{datetime.now().strftime("%Y%m")}.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_db_connection(self):
        """獲取數據庫連接"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            self.logger.error(f"數據庫連接失敗: {e}")
            return None
    
    def load_customer_data(self, start_date, end_date):
        """載入客戶交易數據"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            query = """
                SELECT 
                    customer_id,
                    product_id,
                    transaction_date,
                    quantity,
                    amount
                FROM order_transactions 
                WHERE transaction_date BETWEEN %s AND %s
                    AND customer_id IS NOT NULL
                    AND product_id IS NOT NULL
                ORDER BY customer_id, transaction_date
            """
            
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            self.logger.info(f"載入數據: {len(df)} 筆交易記錄")
            return df
            
        except Exception as e:
            self.logger.error(f"載入數據失敗: {e}")
            return None
        finally:
            conn.close()
    
    def analyze_customer_segments(self, df):
        """分析客戶分群"""
        customer_stats = df.groupby('customer_id').agg({
            'transaction_date': ['count', 'nunique'],
            'amount': ['sum', 'mean'],
            'quantity': 'sum'
        }).round(2)
        
        customer_stats.columns = ['total_orders', 'unique_days', 'total_amount', 'avg_amount', 'total_quantity']
        
        # 計算購買頻率
        for customer_id in customer_stats.index:
            customer_data = df[df['customer_id'] == customer_id]
            date_range = (pd.to_datetime(customer_data['transaction_date']).max() - 
                         pd.to_datetime(customer_data['transaction_date']).min()).days
            
            if date_range > 0:
                frequency = customer_stats.loc[customer_id, 'unique_days'] / (date_range / 7)  # 每週頻率
            else:
                frequency = 0
            
            # 分群邏輯
            if customer_stats.loc[customer_id, 'total_amount'] >= 5000 and frequency >= 1.5:
                segment = "核心VIP客戶"
            elif customer_stats.loc[customer_id, 'total_amount'] >= 2000 and frequency >= 0.8:
                segment = "重要客戶"
            elif frequency >= 0.5:
                segment = "活躍客戶"
            elif customer_stats.loc[customer_id, 'total_orders'] >= 3:
                segment = "計劃型客戶"
            else:
                segment = "新客戶"
            
            self.customer_segments[customer_id] = segment
        
        self.logger.info(f"完成客戶分群: {len(self.customer_segments)} 位客戶")
        
        # 分群統計
        segment_counts = pd.Series(list(self.customer_segments.values())).value_counts()
        for segment, count in segment_counts.items():
            self.logger.info(f"  {segment}: {count} 位客戶")
    
    def identify_suitable_customers(self, df):
        """識別適合Prophet建模的客戶"""
        suitable_customers = []
        
        for customer_id, segment in self.customer_segments.items():
            customer_data = df[df['customer_id'] == customer_id]
            
            if len(customer_data) >= 5:  # 至少5筆訂單
                unique_days = customer_data['transaction_date'].nunique()
                date_range = (pd.to_datetime(customer_data['transaction_date']).max() - 
                            pd.to_datetime(customer_data['transaction_date']).min()).days
                
                # Prophet適用性評分
                prophet_score = 0
                if unique_days >= 3:
                    prophet_score += 2
                if date_range >= 14:
                    prophet_score += 2
                if len(customer_data) >= 8:
                    prophet_score += 1
                
                if prophet_score >= 2:
                    suitable_customers.append({
                        'customer_id': customer_id,
                        'segment': segment,
                        'total_orders': len(customer_data),
                        'unique_days': unique_days,
                        'date_range': date_range,
                        'prophet_score': prophet_score
                    })
        
        self.logger.info(f"識別出 {len(suitable_customers)} 位適合建模的客戶")
        return suitable_customers
    
    def prepare_customer_timeseries(self, df, customer_id):
        """為單個客戶準備時間序列數據"""
        customer_data = df[df['customer_id'] == customer_id].copy()
        customer_data['transaction_date'] = pd.to_datetime(customer_data['transaction_date'])
        customer_data = customer_data.sort_values('transaction_date')
        
        if len(customer_data) < 3:
            return None
        
        # 按日期聚合訂單
        daily_orders = customer_data.groupby('transaction_date').agg({
            'amount': 'sum',
            'quantity': 'sum', 
            'product_id': 'count'
        }).rename(columns={'product_id': 'order_count'}).reset_index()
        
        # 創建完整的日期範圍
        date_range = pd.date_range(
            start=daily_orders['transaction_date'].min(),
            end=daily_orders['transaction_date'].max(),
            freq='D'
        )
        
        # 創建完整時間序列
        full_ts = pd.DataFrame({'ds': date_range})
        full_ts = full_ts.merge(
            daily_orders.rename(columns={'transaction_date': 'ds'}),
            on='ds', how='left'
        ).fillna(0)
        
        return full_ts
    
    def train_prophet_model(self, customer_id, timeseries_data, segment):
        """訓練單個客戶的Prophet模型"""
        if not prophet_available:
            return None
        
        try:
            # 準備Prophet數據格式
            prophet_data = timeseries_data[['ds', 'order_count']].rename(columns={'order_count': 'y'})
            
            # 根據分群調整Prophet參數
            if "VIP" in segment or "重要客戶" in segment:
                model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.08,
                    seasonality_prior_scale=12.0,
                    interval_width=0.8
                )
            elif "新客戶" in segment:
                model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True, 
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.03,
                    seasonality_prior_scale=8.0,
                    interval_width=0.85
                )
            else:
                model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.05,
                    seasonality_prior_scale=10.0,
                    interval_width=0.8
                )
            
            # 訓練模型
            model.fit(prophet_data)
            
            return {
                'model': model,
                'segment': segment,
                'training_data_points': len(prophet_data),
                'avg_orders_per_day': prophet_data['y'].mean()
            }
            
        except Exception as e:
            self.logger.warning(f"客戶 {customer_id} 訓練失敗: {str(e)[:50]}")
            return None
    
    def saturday_model_training(self):
        """週六模型訓練主流程"""
        if not prophet_available:
            self.logger.error("Prophet未安裝，無法執行模型訓練")
            return False
        
        self.logger.info("開始週六Prophet模型訓練流程")
        
        try:
            # 計算訓練數據範圍 - 6個月訓練數據
            today = datetime.now()
            training_start = today - timedelta(days=180)  # 6個月前
            training_end = today - timedelta(days=1)      # 昨天
            
            # 載入訓練數據
            training_df = self.load_customer_data(
                training_start.strftime('%Y-%m-%d'), 
                training_end.strftime('%Y-%m-%d')
            )
            
            if training_df is None or len(training_df) == 0:
                self.logger.error("無法載入訓練數據")
                return False
            
            # 分析客戶分群
            self.analyze_customer_segments(training_df)
            
            # 識別適合的客戶
            suitable_customers = self.identify_suitable_customers(training_df)
            
            if len(suitable_customers) == 0:
                self.logger.error("沒有適合建模的客戶")
                return False
            
            # 訓練Prophet模型
            successful_models = 0
            
            for i, customer_info in enumerate(suitable_customers):
                customer_id = customer_info['customer_id']
                segment = customer_info['segment']
                
                self.logger.info(f"[{i+1}/{len(suitable_customers)}] 訓練客戶 {customer_id} ({segment})")
                
                # 準備時間序列數據
                ts_data = self.prepare_customer_timeseries(training_df, customer_id)
                
                if ts_data is not None and len(ts_data) >= 7:
                    # 訓練Prophet模型
                    model_info = self.train_prophet_model(customer_id, ts_data, segment)
                    
                    if model_info:
                        self.prophet_models[customer_id] = model_info
                        successful_models += 1
                        self.logger.info(f"  ✓ 訓練成功")
                    else:
                        self.logger.info(f"  ✗ 訓練失敗")
                else:
                    self.logger.info(f"  ✗ 數據不足")
            
            self.logger.info(f"成功訓練 {successful_models} 個模型")
            
            if successful_models > 0:
                # 保存模型備份
                self.save_model_backup()
                self.logger.info("週六模型訓練完成")
                return True
            else:
                self.logger.error("沒有成功訓練的模型")
                return False
                
        except Exception as e:
            self.logger.error(f"週六訓練過程發生異常: {e}")
            return False
    
    def generate_daily_predictions(self, prediction_days=7):
        """生成每日預測"""
        if not prophet_available:
            self.logger.error("Prophet未安裝，無法生成預測")
            return None
        
        self.logger.info(f"開始生成未來{prediction_days}天預測")
        
        if len(self.prophet_models) == 0:
            self.logger.error("沒有可用的Prophet模型")
            return None
        
        try:
            # 載入歷史數據分析產品模式
            historical_start = datetime.now() - timedelta(days=180)
            historical_end = datetime.now() - timedelta(days=1)
            
            historical_df = self.load_customer_data(
                historical_start.strftime('%Y-%m-%d'),
                historical_end.strftime('%Y-%m-%d')
            )
            
            if historical_df is None:
                self.logger.error("無法載入歷史數據")
                return None
            
            # 生成預測
            all_predictions = []
            tomorrow = datetime.now() + timedelta(days=1)
            test_dates = [(tomorrow + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(prediction_days)]
            
            for customer_id, model_info in self.prophet_models.items():
                model = model_info['model']
                segment = model_info['segment']
                
                # 預測未來
                future = model.make_future_dataframe(periods=prediction_days + 5)
                forecast = model.predict(future)
                
                # 設定閾值
                if "VIP" in segment or "重要客戶" in segment:
                    threshold = 0.15
                elif "新客戶" in segment:
                    threshold = 0.4
                else:
                    threshold = 0.25
                
                # 分析客戶的產品模式
                customer_products = self.get_customer_top_products(historical_df, customer_id)
                
                # 為每個測試日期生成預測
                for test_date in test_dates:
                    # 找到對應日期的預測
                    matching_pred = forecast[forecast['ds'].dt.strftime('%Y-%m-%d') == test_date]
                    
                    if len(matching_pred) > 0:
                        predicted_orders = max(0, matching_pred.iloc[0]['yhat'])
                        will_purchase = predicted_orders >= threshold
                        
                        if will_purchase and len(customer_products) > 0:
                            # 為每個主要產品都生成預測記錄
                            for product_info in customer_products:
                                all_predictions.append({
                                    'customer_id': customer_id,
                                    'product_id': product_info['product_id'],
                                    'prediction_date': test_date,
                                    'will_purchase_anything': True,
                                    'purchase_probability': min(1.0, predicted_orders / threshold) if threshold > 0 else 0,
                                    'estimated_quantity': max(1, int(predicted_orders)),
                                    'confidence_level': 'high' if predicted_orders > threshold * 1.5 else 'medium',
                                    'original_segment': segment
                                })
                        else:
                            # 預測不會購買
                            all_predictions.append({
                                'customer_id': customer_id,
                                'product_id': '',
                                'prediction_date': test_date,
                                'will_purchase_anything': False,
                                'purchase_probability': 0.0,
                                'estimated_quantity': 0,
                                'confidence_level': 'low',
                                'original_segment': segment
                            })
            
            self.logger.info(f"生成預測完成，總記錄數: {len(all_predictions)}")
            return all_predictions
            
        except Exception as e:
            self.logger.error(f"生成預測失敗: {e}")
            return None
    
    def get_customer_top_products(self, df, customer_id):
        """獲取客戶最常購買的產品"""
        customer_data = df[df['customer_id'] == customer_id]
        
        if len(customer_data) == 0:
            return []
        
        product_freq = customer_data['product_id'].value_counts()
        top_products = []
        
        for product_id, freq in product_freq.head(3).items():
            top_products.append({
                'product_id': product_id,
                'frequency': freq
            })
        
        return top_products
    
    def save_model_backup(self):
        """保存模型備份"""
        try:
            backup_dir = 'model_backups'
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f'{backup_dir}/prophet_models_{timestamp}.pkl'
            
            backup_data = {
                'prophet_models': self.prophet_models,
                'customer_segments': self.customer_segments,
                'customer_performance': self.customer_performance,
                'backup_timestamp': datetime.now(),
                'model_count': len(self.prophet_models),
                'system_version': 'v1.0'
            }
            
            with open(backup_file, 'wb') as f:
                pickle.dump(backup_data, f)
            
            # 同時保存為最新版本
            latest_file = f'{backup_dir}/prophet_models_latest.pkl'
            with open(latest_file, 'wb') as f:
                pickle.dump(backup_data, f)
            
            self.logger.info(f"模型備份完成: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"模型備份失敗: {e}")
    
    def load_latest_models(self):
        """載入最新的Prophet模型"""
        try:
            model_file = 'model_backups/prophet_models_latest.pkl'
            
            if not os.path.exists(model_file):
                self.logger.error("找不到最新的模型文件")
                return False
            
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            self.prophet_models = model_data['prophet_models']
            self.customer_segments = model_data['customer_segments'] 
            self.customer_performance = model_data.get('customer_performance', {})
            
            self.logger.info(f"成功載入模型，包含 {len(self.prophet_models)} 個客戶模型")
            return True
            
        except Exception as e:
            self.logger.error(f"載入模型失敗: {e}")
            return False
    
    def save_predictions_to_csv(self, predictions, filename_prefix='daily_predictions'):
        """保存預測結果到CSV"""
        if not predictions:
            self.logger.error("沒有預測數據可保存")
            return None
        
        try:
            csv_dir = 'csv_outputs'
            os.makedirs(csv_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f'{csv_dir}/{filename_prefix}_{timestamp}.csv'
            
            # 轉換為DataFrame
            df = pd.DataFrame(predictions)
            
            # 添加額外信息
            df['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df['system_version'] = 'v1.0'
            
            # 保存CSV
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            
            # 統計信息
            total_records = len(df)
            purchase_records = len(df[df['will_purchase_anything'] == True])
            unique_customers = df['customer_id'].nunique()
            
            self.logger.info(f"預測結果已保存:")
            self.logger.info(f"  文件: {csv_filename}")
            self.logger.info(f"  總記錄數: {total_records}")
            self.logger.info(f"  購買預測: {purchase_records}")
            self.logger.info(f"  涉及客戶: {unique_customers}")
            
            return csv_filename
            
        except Exception as e:
            self.logger.error(f"保存CSV失敗: {e}")
            return None

def main():
    """主函數 - 完整系統測試"""
    print("=== Prophet客戶補貨預測系統 ===")
    print("開始系統測試...")
    
    # 初始化系統
    system = ProphetPredictionSystem()
    
    print("\n=== 第一階段：模型訓練 ===")
    training_success = system.saturday_model_training()
    
    if training_success:
        print("✓ 模型訓練成功完成")
        
        print("\n=== 第二階段：預測生成 ===")
        predictions = system.generate_daily_predictions(prediction_days=7)
        
        if predictions and len(predictions) > 0:
            print("✓ 預測生成成功完成")
            
            print("\n=== 第三階段：保存結果 ===")
            csv_file = system.save_predictions_to_csv(predictions, 'daily_predictions')
            
            if csv_file:
                print(f"✓ 預測結果已保存到: {csv_file}")
                print("\n=== 系統測試成功完成 ===")
                print(f"成功生成 {len(predictions)} 筆預測記錄")
                
                # 顯示預測統計
                df = pd.DataFrame(predictions)
                purchase_count = len(df[df['will_purchase_anything'] == True])
                print(f"購買預測: {purchase_count} 筆")
                print(f"涉及客戶: {df['customer_id'].nunique()} 位")
                
                return True
            else:
                print("✗ 保存預測結果失敗")
                return False
        else:
            print("✗ 預測生成失敗")
            return False
    else:
        print("✗ 模型訓練失敗")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Prophet客戶補貨預測系統測試通過！")
    else:
        print("\n❌ Prophet客戶補貨預測系統測試失敗！")