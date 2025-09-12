#!/usr/bin/env python3
"""
CatBoost 客戶補貨預測系統 - 替代 Prophet
採用每日訓練+預測模式，提供高精度的客戶補貨預測
整合原有 scheduler 系統，相容 prophet_predictions 資料表
"""

import os
import logging
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 從本地 scheduler 目錄導入 CatBoost 模型
try:
    import sys
    import os
    scheduler_path = os.path.dirname(os.path.dirname(__file__))  # 上一層目錄 (scheduler)
    if scheduler_path not in sys.path:
        sys.path.insert(0, scheduler_path)
    from production_catboost_model import OptimizedRollingPredictionModel
    print(f"成功從本地導入 CatBoost 模型: {scheduler_path}")
except ImportError as e:
    print(f"無法從本地導入 CatBoost 模型: {e}")
    OptimizedRollingPredictionModel = None

class CatBoostPredictionSystem:
    """CatBoost 預測系統主類別 - 相容 Prophet 介面"""
    
    def __init__(self):
        # 設定日誌
        self.setup_logging()
        
        # 資料庫連接配置
        self.db_config = {
            'host': "26.210.160.206",
            'database': "988", 
            'user': "n8n",
            'password': "1234",
            'port': 5433
        }
        
        print("=== CatBoost 客戶補貨預測系統 ===")
        print("每日訓練+預測模式")
        print("CatBoost機器學習預測系統")
        
    def setup_logging(self):
        """設定日誌系統"""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/catboost_system_{datetime.now().strftime("%Y%m")}.log', encoding='utf-8'),
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
    
    def daily_train_and_predict(self, prediction_days=7):
        """每日訓練+預測主流程"""
        self.logger.info("開始 CatBoost 每日訓練+預測流程")
        
        try:
            # 1. 創建 CatBoost 預測器
            predictor = OptimizedRollingPredictionModel(
                db_config=self.db_config,
                rolling_window_days=90,
                prediction_horizon=prediction_days
            )
            
            # 2. 設定基準日期 (昨天)
            base_date = datetime.now() - timedelta(days=1)
            self.logger.info(f"基準日期: {base_date.strftime('%Y-%m-%d')}")
            
            # 3. 執行訓練和預測
            results = predictor.run_optimized_rolling_prediction(base_date=base_date)
            
            if not results or not results.get('predictions') or len(results['predictions']) == 0:
                self.logger.error("CatBoost 預測生成失敗")
                return False
            
            predictions_df = results['predictions']
            self.logger.info(f"CatBoost 生成預測: {len(predictions_df)} 筆")
            
            # 4. 轉換為 Prophet 相容格式
            prophet_format_predictions = self.convert_catboost_to_prophet_format(predictions_df)
            
            if len(prophet_format_predictions) == 0:
                self.logger.warning("沒有符合條件的預測記錄")
                return False
            
            # 5. 保存 CSV 備份
            self.save_predictions_to_csv(predictions_df, 'catboost_daily_predictions')
            
            # 6. 寫入資料庫
            batch_id = f"catboost_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success = self.import_predictions_to_database(prophet_format_predictions, batch_id)
            
            if success:
                self.logger.info(f"CatBoost 每日預測完成: {len(prophet_format_predictions)} 筆寫入資料庫")
                return True
            else:
                self.logger.error("資料庫寫入失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"CatBoost 每日預測流程異常: {e}")
            return False
    
    def convert_catboost_to_prophet_format(self, catboost_predictions):
        """將 CatBoost 預測轉換為 prophet_predictions 表格格式"""
        self.logger.info(f"轉換 CatBoost 格式: {len(catboost_predictions)} 筆")
        
        prophet_format = []
        
        for _, pred in catboost_predictions.iterrows():
            # 獲取預測機率
            prob = pred['purchase_probability']
            
            # 只處理高品質預測 (probability >= 0.7)
            if prob >= 0.7:
                # 判斷信心等級
                if prob >= 0.9:
                    confidence = 'high'
                elif prob >= 0.8:
                    confidence = 'medium'
                else:
                    confidence = 'low'
                
                # 客戶分群 (基於規律性分數)
                regularity = pred.get('regularity_score', 0)
                if regularity >= 0.8:
                    segment = "高規律客戶"
                elif regularity >= 0.6:
                    segment = "中規律客戶"
                elif regularity >= 0.3:
                    segment = "低規律客戶"
                else:
                    segment = "新客戶"
                
                prophet_record = {
                    'customer_id': pred['customer_id'],
                    'product_id': pred['product_id'],
                    'prediction_date': pred['prediction_date'],
                    'will_purchase_anything': True,  # 只有 prob >= 0.7 的才會進入
                    'purchase_probability': round(prob, 4),
                    'estimated_quantity': int(pred['quantity']),
                    'confidence_level': confidence,
                    'original_segment': segment
                }
                
                prophet_format.append(prophet_record)
        
        self.logger.info(f"轉換完成: {len(prophet_format)} 筆高品質預測")
        return prophet_format
    
    def import_predictions_to_database(self, predictions, batch_id):
        """將預測結果寫入 prophet_predictions 表"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                # 預先載入每個 (customer_id, product_id) 的最後一次預測與購買時間
                last_pred_map = {}
                last_buy_map = {}

                try:
                    # 取最後一次預測時間（以 updated_at 優先，若無則使用 created_at）
                    cur.execute(
                        """
                        SELECT customer_id, product_id, MAX(COALESCE(updated_at, created_at)) AS last_pred_at
                        FROM prophet_predictions
                        WHERE prediction_status = 'active'
                        GROUP BY customer_id, product_id
                        """
                    )
                    for row in cur.fetchall():
                        last_pred_map[(row[0], row[1])] = row[2]
                except Exception as e:
                    self.logger.warning(f"讀取最後預測時間失敗，將不套用購買後刷新規則: {str(e)}")

                try:
                    # 取最後一次實際購買時間
                    cur.execute(
                        """
                        SELECT customer_id, product_id, MAX(transaction_date) AS last_buy_at
                        FROM order_transactions
                        WHERE document_type = %s AND is_active = 'active'
                        GROUP BY customer_id, product_id
                        """,
                        ('補貨',)
                    )
                    for row in cur.fetchall():
                        last_buy_map[(row[0], row[1])] = row[2]
                except Exception as e:
                    self.logger.warning(f"讀取最後購買時間失敗，將不套用購買後刷新規則: {str(e)}")

                imported_count = 0
                error_count = 0
                skipped_count = 0
                
                for prediction in predictions:
                    try:
                        # 僅當「從未預測過」或「自上次預測後有新購買」才寫入
                        key = (prediction['customer_id'], prediction['product_id'])
                        last_pred_at = last_pred_map.get(key)
                        last_buy_at = last_buy_map.get(key)

                        should_write = False
                        if last_pred_at is None:
                            should_write = True
                        else:
                            if last_buy_at is not None and last_buy_at > last_pred_at:
                                should_write = True

                        if not should_write:
                            skipped_count += 1
                            continue
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
                            WHERE prophet_predictions.prediction_status = 'active';
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
                # 額外記錄被跳過的筆數
                try:
                    self.logger.info(f"略過(自上次預測後無新購買) {skipped_count} 筆")
                except Exception:
                    pass
                
                self.logger.info(f"資料庫導入完成: 成功 {imported_count}, 失敗 {error_count}")
                return error_count == 0
                
        except Exception as e:
            self.logger.error(f"資料庫導入異常: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def save_predictions_to_csv(self, predictions, filename_prefix='catboost_predictions'):
        """保存預測結果到 CSV"""
        try:
            csv_dir = 'csv_outputs'
            os.makedirs(csv_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f'{csv_dir}/{filename_prefix}_{timestamp}.csv'
            
            # 添加額外資訊
            predictions_with_info = predictions.copy()
            predictions_with_info['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            predictions_with_info['system_version'] = 'catboost_v1.0'
            
            # 保存 CSV
            predictions_with_info.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            
            # 統計資訊
            total_records = len(predictions_with_info)
            unique_customers = predictions_with_info['customer_id'].nunique()
            unique_products = predictions_with_info['product_id'].nunique()
            avg_probability = predictions_with_info['purchase_probability'].mean()
            total_quantity = predictions_with_info['quantity'].sum()
            
            self.logger.info(f"CSV 已保存: {csv_filename}")
            self.logger.info(f"  總記錄數: {total_records}")
            self.logger.info(f"  涉及客戶: {unique_customers}")
            self.logger.info(f"  涉及產品: {unique_products}")
            self.logger.info(f"  平均機率: {avg_probability:.3f}")
            self.logger.info(f"  總數量: {total_quantity}")
            
            return csv_filename
            
        except Exception as e:
            self.logger.error(f"CSV 保存失敗: {e}")
            return None
    
    # === 相容 Prophet 介面的方法 ===
    
    def saturday_model_training(self):
        """相容 Prophet 介面 - 但實際上每天都會重新訓練"""
        self.logger.info("CatBoost 不需要週六訓練 - 每天都會重新訓練")
        return True
    
    def generate_daily_predictions(self, prediction_days=7):
        """相容 Prophet 介面 - 實際執行每日訓練+預測"""
        return self.daily_train_and_predict(prediction_days)
    
    def load_latest_models(self):
        """相容 Prophet 介面 - CatBoost 不需要載入模型"""
        self.logger.info("CatBoost 每天重新訓練，不需要載入模型")
        return True

def main():
    """測試主函數"""
    print("=== CatBoost 預測系統測試 ===")
    
    # 初始化系統
    system = CatBoostPredictionSystem()
    
    print("\n=== 執行每日訓練+預測 ===")
    success = system.daily_train_and_predict(prediction_days=7)
    
    if success:
        print("✓ CatBoost 每日預測成功完成")
        print("\n=== 系統測試通過 ===")
        return True
    else:
        print("✗ CatBoost 每日預測失敗")
        print("\n=== 系統測試失敗 ===")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 CatBoost 客戶補貨預測系統測試通過！")
    else:
        print("\n❌ CatBoost 客戶補貨預測系統測試失敗！")
