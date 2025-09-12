#!/usr/bin/env python3
"""
CatBoost預測服務
載入已訓練模型，使用90天數據進行預測
"""

import os
import json
import pickle
import logging
import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime, timedelta

from config import MLConfig

class CatBoostPredictor:
    """CatBoost預測服務"""
    
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
        self.metadata = None
        self.last_loaded = None
        
        self.setup_logging()
        
        print("=== CatBoost預測服務 ===")
        print(f"特徵計算窗口: {MLConfig.FEATURE_CALCULATION_DAYS}天")
        print(f"預測閾值: {MLConfig.PREDICTION_THRESHOLD}")
    
    def setup_logging(self):
        """設置日誌"""
        log_file = os.path.join(MLConfig.LOG_DIR, f'model_service_{datetime.now().strftime("%Y%m")}.log')
        
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
    
    def ensure_model_loaded(self):
        """確保模型已載入，支持熱更新"""
        model_path = MLConfig.get_current_model_path()
        
        # 檢查是否需要重新載入
        if self._should_reload_model(model_path):
            return self._load_model()
        
        return self.model is not None
    
    def _should_reload_model(self, model_path):
        """檢查是否需要重新載入模型"""
        if not os.path.exists(model_path):
            return False
        
        if self.model is None:
            return True
        
        # 檢查文件修改時間
        current_mtime = os.path.getmtime(model_path)
        if self.last_loaded is None or current_mtime > self.last_loaded:
            return True
        
        return False
    
    def _load_model(self):
        """載入模型和相關文件"""
        try:
            model_path = MLConfig.get_current_model_path()
            feature_names_path = MLConfig.get_feature_names_path()
            metadata_path = MLConfig.get_metadata_path()
            
            # 檢查文件存在
            if not all(os.path.exists(p) for p in [model_path, feature_names_path, metadata_path]):
                self.logger.error("模型文件不完整，請先訓練模型")
                return False
            
            # 載入模型
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # 載入特徵名稱
            with open(feature_names_path, 'rb') as f:
                self.feature_names = pickle.load(f)
            
            # 載入元數據
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            
            self.last_loaded = datetime.now().timestamp()
            
            self.logger.info(f"模型載入成功:")
            self.logger.info(f"  模型類型: {self.metadata.get('model_type', 'Unknown')}")
            self.logger.info(f"  特徵數量: {len(self.feature_names)}")
            self.logger.info(f"  訓練時間: {self.metadata.get('created_at', 'Unknown')}")
            self.logger.info(f"  F1分數: {self.metadata.get('metrics', {}).get('f1_score', 'Unknown')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"載入模型失敗: {e}")
            self.model = None
            self.feature_names = None
            self.metadata = None
            return False
    
    def load_feature_data(self, start_date, end_date):
        """載入特徵計算需要的數據"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
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
            
            self.logger.info(f"載入特徵數據: {len(df):,} 筆交易記錄")
            return df
            
        except Exception as e:
            self.logger.error(f"載入特徵數據失敗: {e}")
            return None
        finally:
            conn.close()
    
    def get_recent_purchases(self, days=7):
        """獲取最近N天的實際購買記錄"""
        conn = self.get_db_connection()
        if not conn:
            return set()
        
        try:
            from datetime import timedelta
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT ot.customer_id, ot.product_id, ot.transaction_date
                FROM order_transactions ot
                JOIN product_master pm ON ot.product_id = pm.product_id
                WHERE ot.transaction_date BETWEEN %s::date AND %s::date
                    AND ot.document_type = '銷貨'
                    AND pm.is_active = 'active'
                    AND ot.quantity > 0
                ORDER BY ot.transaction_date DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            
            if len(df) > 0:
                # 轉換為 (customer_id, product_id, date) 的集合
                purchases = set()
                for _, row in df.iterrows():
                    purchases.add((row['customer_id'], row['product_id'], row['transaction_date'].date()))
                
                self.logger.info(f"獲取最近{days}天購買記錄: {len(purchases):,}筆")
                return purchases
            else:
                self.logger.info(f"最近{days}天無購買記錄")
                return set()
                
        except Exception as e:
            self.logger.error(f"獲取購買記錄失敗: {e}")
            return set()
        finally:
            conn.close()
    
    def get_current_active_predictions(self):
        """獲取當前所有活躍預測"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        try:
            query = """
                SELECT customer_id, product_id, prediction_date, 
                       purchase_probability, created_at
                FROM prophet_predictions 
                WHERE prediction_status = 'active'
                    AND prediction_date >= CURRENT_DATE
                ORDER BY customer_id, product_id, prediction_date
            """
            
            df = pd.read_sql_query(query, conn)
            
            active_predictions = {}
            for _, row in df.iterrows():
                combo = (row['customer_id'], row['product_id'])
                if combo not in active_predictions:
                    active_predictions[combo] = []
                
                active_predictions[combo].append({
                    'prediction_date': row['prediction_date'] if isinstance(row['prediction_date'], pd.Timestamp) else row['prediction_date'],
                    'probability': row['purchase_probability'],
                    'created_at': row['created_at'] if isinstance(row['created_at'], pd.Timestamp) else row['created_at']
                })
            
            self.logger.info(f"當前活躍預測組合數: {len(active_predictions):,}")
            return active_predictions
            
        except Exception as e:
            self.logger.error(f"獲取活躍預測失敗: {e}")
            return {}
        finally:
            conn.close()
    
    def has_prediction_been_fulfilled(self, combo, predictions, recent_purchases):
        """檢查預測是否已被實際購買驗證"""
        customer_id, product_id = combo
        
        # 檢查是否有匹配的購買記錄
        for purchase_customer, purchase_product, purchase_date in recent_purchases:
            if purchase_customer == customer_id and purchase_product == product_id:
                # 檢查購買日期是否在預測日期範圍內（前後2天容錯）
                for pred in predictions:
                    pred_date = pred['prediction_date']
                    date_diff = abs((purchase_date - pred_date).days)
                    if date_diff <= 2:  # 2天容錯
                        return True, purchase_date, pred_date
        
        return False, None, None
    
    def is_prediction_expired(self, predictions, expire_days=7):
        """檢查預測是否過期"""
        today = datetime.now().date()
        
        for pred in predictions:
            # 如果有任何預測日期是未來7天內，則未過期
            days_until_prediction = (pred['prediction_date'] - today).days
            if 0 <= days_until_prediction <= expire_days:
                return False
        
        return True  # 所有預測都過期了
    
    def get_active_combinations(self, feature_data):
        """獲取需要預測的客戶-產品組合 - 基於實際購買的智能觸發"""
        # 獲取90天內實際存在的客戶-產品購買組合
        historical_pairs = set(zip(feature_data['customer_id'], feature_data['product_id']))
        
        self.logger.info(f"90天內實際購買組合數: {len(historical_pairs):,}")
        
        # 獲取當前活躍預測和最近購買記錄
        self.logger.info("開始智能預測觸發分析...")
        active_predictions = self.get_current_active_predictions()
        recent_purchases = self.get_recent_purchases(days=7)
        
        # 智能篩選符合預測條件的組合
        eligible_combinations = []
        new_combinations = 0
        fulfilled_combinations = 0
        expired_combinations = 0
        skipped_combinations = 0
        
        for combo in historical_pairs:
            customer_id, product_id = combo
            
            # 檢查是否有活躍預測
            if combo in active_predictions:
                predictions = active_predictions[combo]
                
                # 檢查預測是否已被購買驗證
                fulfilled, purchase_date, pred_date = self.has_prediction_been_fulfilled(
                    combo, predictions, recent_purchases
                )
                
                if fulfilled:
                    # 預測成功，可以生成下一次預測
                    eligible_combinations.append(combo)
                    fulfilled_combinations += 1
                    self.logger.debug(f"預測成功: {customer_id}-{product_id} (購買:{purchase_date}, 預測:{pred_date})")
                
                elif self.is_prediction_expired(predictions):
                    # 預測過期，可以重新預測
                    eligible_combinations.append(combo)
                    expired_combinations += 1
                    self.logger.debug(f"預測過期: {customer_id}-{product_id}")
                
                else:
                    # 有活躍預測但未購買，暫不預測
                    skipped_combinations += 1
                    self.logger.debug(f"暫停預測: {customer_id}-{product_id} (等待購買驗證)")
            
            else:
                # 新組合，沒有歷史預測
                eligible_combinations.append(combo)
                new_combinations += 1
        
        # 按購買頻率排序符合條件的組合
        pair_activity = feature_data.groupby(['customer_id', 'product_id']).size().sort_values(ascending=False)
        
        # 限制預測組合數量
        max_combinations = 10000  # 最多預測1萬個有意義的組合
        
        if len(eligible_combinations) > max_combinations:
            # 根據購買頻率選擇最高優先級的組合
            eligible_pairs_df = pair_activity[pair_activity.index.isin(eligible_combinations)]
            top_pairs = eligible_pairs_df.head(max_combinations).index.tolist()
            combinations = [(customer_id, product_id) for customer_id, product_id in top_pairs]
            self.logger.info(f"限制到高優先級組合: {len(combinations):,}")
        else:
            combinations = eligible_combinations
        
        # 記錄智能觸發統計
        self.logger.info(f"=== 智能預測觸發統計 ===")
        self.logger.info(f"  新組合 (無歷史預測): {new_combinations:,}")
        self.logger.info(f"  成功組合 (已購買驗證): {fulfilled_combinations:,}")
        self.logger.info(f"  過期組合 (重新啟動): {expired_combinations:,}")
        self.logger.info(f"  暫停組合 (等待驗證): {skipped_combinations:,}")
        self.logger.info(f"  符合條件總數: {len(eligible_combinations):,}")
        self.logger.info(f"  最終預測組合: {len(combinations):,}")
        
        # 統計信息
        customer_count = len(set(combo[0] for combo in combinations))
        product_count = len(set(combo[1] for combo in combinations))
        
        self.logger.info(f"預測組合統計:")
        self.logger.info(f"  總組合數: {len(combinations):,}")
        self.logger.info(f"  涉及客戶: {customer_count:,}")
        self.logger.info(f"  涉及產品: {product_count:,}")
        self.logger.info(f"  平均每客戶: {len(combinations)/customer_count:.1f} 產品")
        
        return combinations
    
    def calculate_90day_features(self, customer_id, product_id, feature_data, target_date):
        """計算單個客戶-產品-目標日期的90天特徵"""
        # 獲取相關數據
        customer_data = feature_data[feature_data['customer_id'] == customer_id]
        product_data = feature_data[feature_data['product_id'] == product_id]
        cp_data = feature_data[
            (feature_data['customer_id'] == customer_id) & 
            (feature_data['product_id'] == product_id)
        ]
        
        features = {
            # 目標日期特徵（保持與現有模型兼容的名稱）
            'prediction_day_of_week': target_date.weekday(),
            'prediction_day_of_month': target_date.day,
            'prediction_month': target_date.month,
            'prediction_quarter': (target_date.month - 1) // 3 + 1,
            
            # 客戶90天特徵
            'customer_purchase_days_90d': customer_data['transaction_date'].nunique(),
            'customer_total_amount_90d': customer_data['amount'].sum(),
            'customer_avg_amount_90d': customer_data['amount'].mean() if len(customer_data) > 0 else 0,
            'customer_total_quantity_90d': customer_data['quantity'].sum(),
            'customer_unique_products_90d': customer_data['product_id'].nunique(),
            'days_since_customer_last_purchase': self._days_since_last_purchase(customer_data, target_date),
            
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
            'days_since_cp_last_purchase': self._days_since_last_purchase(cp_data, target_date),
        }
        
        return features
    
    def _days_since_last_purchase(self, data, reference_date):
        """計算距離最後一次購買的天數"""
        if len(data) == 0:
            return 999  # 大數值表示從未購買
        
        last_purchase = data['transaction_date'].max()
        if pd.isna(last_purchase):
            return 999
        
        days_diff = (reference_date - last_purchase.date()).days
        return min(days_diff, 999)  # 限制最大值
    
    def _get_weekday_purchase_count(self, data, target_weekday):
        """計算該客戶-產品在特定星期幾的歷史購買次數"""
        if len(data) == 0:
            return 0
        
        # 計算歷史數據中該星期幾的購買次數
        weekday_purchases = data[data['transaction_date'].dt.weekday == target_weekday]
        return len(weekday_purchases)
    
    def predict_combinations(self, combinations, feature_data, prediction_date):
        """批量預測客戶-產品組合 - 為每天獨立預測並選擇最佳日期"""
        self.logger.info(f"開始7天窗口預測 {len(combinations):,} 個組合...")
        
        # 為每個組合預測未來7天，然後選擇最佳日期
        best_predictions = []
        
        for i, (customer_id, product_id) in enumerate(combinations):
            if i % 1000 == 0 and i > 0:
                self.logger.info(f"組合預測進度: {i:,}/{len(combinations):,}")
            
            try:
                # 為該組合預測未來7天
                daily_predictions = []
                
                for day_offset in range(1, MLConfig.PREDICTION_HORIZON_DAYS + 1):
                    target_date = prediction_date + timedelta(days=day_offset)
                    
                    # 計算該特定日期的特徵
                    features = self.calculate_90day_features(
                        customer_id, product_id, feature_data, target_date
                    )
                    
                    # 轉換為DataFrame並確保特徵順序
                    features_df = pd.DataFrame([features])
                    features_df = features_df.reindex(columns=self.feature_names, fill_value=0)
                    
                    # 預測該日期的購買概率
                    try:
                        prob = self.model.predict_proba(features_df)[0, 1]
                        daily_predictions.append({
                            'date': target_date,
                            'probability': float(prob),
                            'day_offset': day_offset
                        })
                    except Exception as e:
                        self.logger.warning(f"客戶{customer_id}-產品{product_id}日期{target_date}預測失敗: {e}")
                        continue
                
                # 選擇概率最高的日期
                if daily_predictions:
                    best_day = max(daily_predictions, key=lambda x: x['probability'])
                    
                    # 只有概率超過閾值才保留
                    if best_day['probability'] >= MLConfig.PREDICTION_THRESHOLD:
                        # 估算購買數量（基於歷史平均）
                        cp_data = feature_data[
                            (feature_data['customer_id'] == customer_id) & 
                            (feature_data['product_id'] == product_id)
                        ]
                        
                        if len(cp_data) > 0:
                            avg_quantity = cp_data['quantity'].mean()
                            estimated_quantity = max(1, int(avg_quantity))
                        else:
                            estimated_quantity = 1
                        
                        best_predictions.append({
                            'customer_id': customer_id,
                            'product_id': product_id,
                            'prediction_date': best_day['date'],
                            'purchase_probability': best_day['probability'],
                            'estimated_quantity': estimated_quantity,
                            'confidence_level': 'high' if best_day['probability'] >= 0.8 else 'medium',
                            'will_purchase_anything': True,
                            'original_segment': 'ML預測客戶',
                            'best_day_offset': best_day['day_offset'],
                            'all_day_probabilities': [p['probability'] for p in daily_predictions]
                        })
                        
            except Exception as e:
                self.logger.warning(f"客戶{customer_id}-產品{product_id}組合預測失敗: {e}")
        
        self.logger.info(f"最佳日期預測完成: {len(best_predictions):,} 個高品質預測")
        self.logger.info(f"平均最佳概率: {np.mean([p['purchase_probability'] for p in best_predictions]):.3f}")
        
        return best_predictions
    
    def save_predictions_to_database(self, predictions, batch_id):
        """保存預測結果到資料庫"""
        if not predictions:
            self.logger.warning("沒有預測結果需要保存")
            return True
        
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                imported_count = 0
                error_count = 0
                
                for prediction in predictions:
                    try:
                        # 為新預測結構添加額外信息到notes
                        notes = f"最佳日期偏移: +{prediction.get('best_day_offset', 'N/A')}天"
                        if 'all_day_probabilities' in prediction:
                            notes += f", 7天概率: {prediction['all_day_probabilities']}"
                        
                        cur.execute("""
                            INSERT INTO prophet_predictions (
                                customer_id, product_id, prediction_date, will_purchase_anything,
                                purchase_probability, estimated_quantity, confidence_level,
                                original_segment, prediction_batch_id, created_at, prediction_status
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'active')
                            ON CONFLICT (customer_id, product_id, prediction_date)
                            DO UPDATE SET
                                will_purchase_anything = EXCLUDED.will_purchase_anything,
                                purchase_probability = EXCLUDED.purchase_probability,
                                estimated_quantity = EXCLUDED.estimated_quantity,
                                confidence_level = EXCLUDED.confidence_level,
                                prediction_batch_id = EXCLUDED.prediction_batch_id,
                                updated_at = NOW()
                            WHERE prophet_predictions.prediction_status = 'active'
                        """, (
                            prediction['customer_id'],
                            prediction['product_id'],
                            prediction['prediction_date'],
                            prediction['will_purchase_anything'],
                            prediction['purchase_probability'],
                            prediction['estimated_quantity'],
                            prediction['confidence_level'],
                            prediction['original_segment'],
                            batch_id
                        ))
                        
                        imported_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        self.logger.warning(f"預測導入失敗: {str(e)[:100]}")
                
                conn.commit()
                
                self.logger.info(f"資料庫導入完成: 成功 {imported_count}, 失敗 {error_count}")
                return error_count == 0
                
        except Exception as e:
            self.logger.error(f"資料庫導入異常: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def daily_prediction_process(self):
        """每日預測主流程"""
        self.logger.info("開始每日預測流程...")
        
        # 1. 確保模型載入
        if not self.ensure_model_loaded():
            self.logger.error("無法載入模型")
            return False
        
        try:
            # 2. 計算數據範圍（90天特徵數據）
            prediction_date = datetime.now().date()
            feature_end_date = prediction_date - timedelta(days=1)  # 昨天
            feature_start_date = feature_end_date - timedelta(days=MLConfig.FEATURE_CALCULATION_DAYS)
            
            self.logger.info(f"預測日期: {prediction_date}")
            self.logger.info(f"特徵數據範圍: {feature_start_date} ~ {feature_end_date}")
            
            # 3. 載入特徵數據
            feature_data = self.load_feature_data(feature_start_date, feature_end_date)
            if feature_data is None or len(feature_data) == 0:
                self.logger.error("無法載入特徵數據")
                return False
            
            # 4. 獲取預測組合
            combinations = self.get_active_combinations(feature_data)
            if not combinations:
                self.logger.error("沒有可預測的組合")
                return False
            
            # 5. 執行預測
            predictions = self.predict_combinations(combinations, feature_data, prediction_date)
            if not predictions:
                self.logger.warning("沒有生成高品質預測")
                return True  # 不算失敗，只是沒有符合閾值的預測
            
            # 6. 保存結果
            batch_id = f"catboost_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success = self.save_predictions_to_database(predictions, batch_id)
            
            if success:
                self.logger.info(f"每日預測完成: {len(predictions):,} 筆高品質預測")
                return True
            else:
                self.logger.error("預測結果保存失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"每日預測流程異常: {e}")
            return False
    
    def health_check(self):
        """健康檢查"""
        try:
            # 檢查模型狀態
            if not self.ensure_model_loaded():
                return {'status': 'error', 'message': '模型載入失敗'}
            
            # 檢查資料庫連接
            conn = self.get_db_connection()
            if not conn:
                return {'status': 'error', 'message': '資料庫連接失敗'}
            conn.close()
            
            # 檢查模型信息
            info = {
                'status': 'healthy',
                'model_loaded': True,
                'model_type': self.metadata.get('model_type', 'Unknown'),
                'feature_count': len(self.feature_names) if self.feature_names else 0,
                'last_trained': self.metadata.get('created_at', 'Unknown'),
                'f1_score': self.metadata.get('metrics', {}).get('f1_score', 'Unknown')
            }
            
            return info
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

def main():
    """測試函數"""
    print("=== CatBoost預測服務測試 ===")
    
    predictor = CatBoostPredictor()
    
    # 健康檢查
    health = predictor.health_check()
    print(f"健康檢查: {health}")
    
    if health['status'] == 'healthy':
        # 執行預測
        success = predictor.daily_prediction_process()
        if success:
            print("✓ 每日預測成功")
        else:
            print("✗ 每日預測失敗")
    
    return health['status'] == 'healthy'

if __name__ == "__main__":
    main()