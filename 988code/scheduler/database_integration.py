#!/usr/bin/env python3
"""
數據庫整合模組
處理預測結果的數據庫存儲、觸發器管理、審計日誌
"""

import os
import logging
import psycopg2
import pandas as pd
from datetime import datetime, timedelta

class DatabaseIntegration:
    """數據庫整合類別"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or {
            'host': "26.210.160.206",
            'database': "988",
            'user': "n8n",
            'password': "1234",
            'port': "5433"
        }
        
        self.setup_logging()
    
    def setup_logging(self):
        """設定日誌系統"""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/database_integration_{datetime.now().strftime("%Y%m")}.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self):
        """獲取數據庫連接"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            self.logger.error(f"數據庫連接失敗: {e}")
            return None
    
    def create_database_schema(self):
        """創建數據庫函數 - 表格已存在，僅創建需要的函數"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                # 跳過表格創建 - 使用現有的表格
                # prophet_predictions, prophet_prediction_logs, prophet_prediction_backup 已存在
                self.logger.info("使用現有數據庫表格...")
                
                # 清理可能衝突的舊函數
                cur.execute("DROP FUNCTION IF EXISTS cleanup_expired_predictions(integer);")
                cur.execute("DROP FUNCTION IF EXISTS get_prediction_stats();")
                self.logger.info("清理舊函數完成...")
                
                # 創建統計函數
                create_stats_function = """
                CREATE OR REPLACE FUNCTION get_prediction_stats()
                RETURNS TABLE(
                    prediction_status TEXT,
                    count BIGINT,
                    percentage NUMERIC
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        pp.prediction_status,
                        COUNT(*) as count,
                        ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM prophet_predictions)), 2) as percentage
                    FROM prophet_predictions pp
                    GROUP BY pp.prediction_status
                    ORDER BY count DESC;
                END;
                $$ LANGUAGE plpgsql;
                """
                
                cur.execute(create_stats_function)
                
                # 創建清理函數
                create_cleanup_function = """
                CREATE OR REPLACE FUNCTION cleanup_expired_predictions(days_to_keep INTEGER DEFAULT 30)
                RETURNS INTEGER AS $$
                DECLARE
                    expired_count INTEGER;
                BEGIN
                    -- 只處理完全無反應的預測：30天後仍為active狀態
                    -- cancelled 狀態由前端手動標記，不自動處理
                    -- fulfilled 狀態由觸發器自動標記，不清理
                    UPDATE prophet_predictions 
                    SET prediction_status = 'expired',
                        updated_at = NOW()
                    WHERE prediction_date < CURRENT_DATE - INTERVAL '1 day' * days_to_keep
                      AND prediction_status = 'active';
                    
                    GET DIAGNOSTICS expired_count = ROW_COUNT;
                    RETURN expired_count;
                END;
                $$ LANGUAGE plpgsql;
                """
                
                cur.execute(create_cleanup_function)
                
                conn.commit()
                self.logger.info("數據庫函數創建成功")
                return True
                
        except Exception as e:
            self.logger.error(f"創建數據庫函數失敗: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def create_purchase_detection_trigger(self):
        """創建補貨提醒取消觸發器 - 監控temp_customer_records表的訂單確認"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                # 創建觸發器函數
                trigger_function = """
                CREATE OR REPLACE FUNCTION handle_restock_reminder_cancellation()
                RETURNS TRIGGER AS $$
                DECLARE
                    affected_rows INTEGER;
                    log_batch_id TEXT;
                    confirmed_date DATE;
                BEGIN
                    -- 只處理訂單確認的情況 (status 0 → 1)
                    IF OLD.status = '0' AND NEW.status = '1' THEN
                        
                        log_batch_id := 'restock_cancel_' || to_char(NOW(), 'YYYYMMDD_HH24MISS') || '_' || NEW.line_id;
                        
                        -- 處理confirmed_at字段，可能是字串或時間戳
                        BEGIN
                            confirmed_date := DATE(CAST(NEW.confirmed_at AS TIMESTAMP));
                        EXCEPTION
                            WHEN OTHERS THEN
                                confirmed_date := CURRENT_DATE;  -- 如果轉換失敗，使用當前日期
                        END;
                        
                        -- 更新對應的補貨提醒記錄為 fulfilled
                        -- 使用子類別匹配邏輯
                        UPDATE prophet_predictions 
                        SET 
                            prediction_status = 'fulfilled',
                            updated_at = NOW(),
                            fulfilled_at = NOW(),
                            actual_transaction_id = NEW.line_id
                        WHERE 
                            customer_id = NEW.customer_id 
                            AND product_id IN (
                                -- 子類別匹配：找出所有與訂單產品同子類別的產品
                                SELECT DISTINCT p2.product_id 
                                FROM product_master p1, product_master p2
                                WHERE p1.product_id = NEW.product_id 
                                  AND p2.subcategory = p1.subcategory
                                  AND p1.subcategory IS NOT NULL
                                  AND p1.subcategory != ''
                            )
                            AND prediction_date <= confirmed_date  -- 只取消預測日期在確認日期之前或當天的提醒
                            AND prediction_status = 'active';
                        
                        GET DIAGNOSTICS affected_rows = ROW_COUNT;
                        
                        -- 記錄到審計日誌
                        IF affected_rows > 0 THEN
                            INSERT INTO prophet_prediction_logs (
                                customer_id, product_id, prediction_date, action_type,
                                old_status, new_status, change_reason,
                                related_transaction_id, related_transaction_date,
                                batch_id, created_by
                            ) VALUES (
                                NEW.customer_id, NEW.product_id, confirmed_date,
                                'fulfilled', 'active', 'fulfilled', 'Order confirmed - restock reminder auto-cancelled',
                                NEW.line_id, confirmed_date,
                                log_batch_id, 'restock_reminder_trigger'
                            );
                        END IF;
                    END IF;
                    
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
                
                cur.execute(trigger_function)
                
                # 刪除舊觸發器
                cur.execute("DROP TRIGGER IF EXISTS prophet_purchase_detection_trigger ON order_transactions;")
                cur.execute("DROP TRIGGER IF EXISTS restock_reminder_cancellation_trigger ON temp_customer_records;")
                
                # 創建新觸發器 - 監控temp_customer_records表
                cur.execute("""
                    CREATE TRIGGER restock_reminder_cancellation_trigger
                        AFTER UPDATE ON temp_customer_records
                        FOR EACH ROW
                        WHEN (OLD.status = '0' AND NEW.status = '1' AND NEW.customer_id IS NOT NULL AND NEW.product_id IS NOT NULL)
                        EXECUTE FUNCTION handle_restock_reminder_cancellation();
                """)
                
                conn.commit()
                self.logger.info("補貨提醒取消觸發器創建成功 - 監控temp_customer_records表")
                return True
                
        except Exception as e:
            self.logger.error(f"創建觸發器失敗: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def import_predictions_to_database(self, predictions, batch_id):
        """導入預測到數據庫"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                imported_count = 0
                error_count = 0
                
                for prediction in predictions:
                    try:
                        # 只處理會購買的預測記錄 - 只上傳will_purchase_anything=True的記錄
                        if prediction.get('will_purchase_anything', False):
                            # 處理空值
                            product_id = prediction.get('product_id', '') or ''
                            
                            cur.execute("""
                                INSERT INTO prophet_predictions (
                                    customer_id, product_id, prediction_date, will_purchase_anything,
                                    purchase_probability, estimated_quantity, confidence_level,
                                    original_segment, prediction_batch_id, created_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
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
                                product_id,
                                prediction['prediction_date'],
                                prediction['will_purchase_anything'],
                                prediction.get('purchase_probability', 0),
                                prediction.get('estimated_quantity', 0),
                                prediction.get('confidence_level', 'unknown'),
                                prediction.get('original_segment', ''),
                                batch_id
                            ))
                            
                            imported_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        self.logger.warning(f"預測導入失敗: {str(e)[:100]}")
                
                conn.commit()
                
                self.logger.info(f"導入完成: 成功 {imported_count}, 失敗 {error_count}")
                return error_count == 0
                
        except Exception as e:
            self.logger.error(f"數據庫導入異常: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def cleanup_expired_predictions(self, days_to_keep=14):
        """清理過期預測"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT cleanup_expired_predictions(%s);", (days_to_keep,))
                expired_count = cur.fetchone()[0]
                conn.commit()
                
                if expired_count > 0:
                    self.logger.info(f"清理完成: 共處理 {expired_count} 個預測 (包含過期和取消狀態)")
                
                return expired_count
                    
        except Exception as e:
            self.logger.error(f"清理過期預測失敗: {e}")
            return 0
        finally:
            conn.close()
    
    def get_prediction_statistics(self):
        """獲取預測統計"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_prediction_stats();")
                stats = cur.fetchall()
                
                print("=== 預測統計 ===")
                for status, count, percentage in stats:
                    print(f"{status}: {count} ({percentage}%)")
                
                return stats
                
        except Exception as e:
            self.logger.error(f"獲取統計失敗: {e}")
            return None
        finally:
            conn.close()
    
    def check_yesterday_accuracy(self):
        """檢查昨日預測準確率"""
        try:
            conn = self.get_connection()
            if not conn:
                return 0.0
            
            with conn.cursor() as cur:
                yesterday = datetime.now().date() - timedelta(days=1)
                
                # 獲取昨日預測統計
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_predictions,
                        COUNT(CASE WHEN prediction_status = 'fulfilled' THEN 1 END) as fulfilled_predictions
                    FROM prophet_predictions 
                    WHERE prediction_date = %s AND will_purchase_anything = true;
                """, (yesterday,))
                
                result = cur.fetchone()
                if result and result[0] > 0:
                    accuracy = result[1] / result[0]
                    return accuracy
                else:
                    return 0.0
                    
        except Exception as e:
            self.logger.error(f"檢查昨日準確率失敗: {e}")
            return 0.0
        finally:
            if conn:
                conn.close()
    
    def get_system_status(self):
        """獲取系統狀態"""
        print("=" * 60)
        print("數據庫整合系統狀態")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            if not conn:
                print("[ERROR] 數據庫連接失敗")
                return False
            
            with conn.cursor() as cur:
                # 檢查預測統計
                print("\n[1] 預測統計:")
                cur.execute("SELECT * FROM get_prediction_stats();")
                stats = cur.fetchall()
                
                for status, count, percentage in stats:
                    print(f"  {status}: {count} ({percentage}%)")
                
                # 檢查最近預測
                print("\n[2] 近期預測:")
                cur.execute("""
                    SELECT prediction_date, COUNT(*) as total,
                           SUM(CASE WHEN will_purchase_anything THEN 1 ELSE 0 END) as purchase_pred
                    FROM prophet_predictions 
                    WHERE prediction_date >= CURRENT_DATE
                    GROUP BY prediction_date
                    ORDER BY prediction_date
                    LIMIT 7;
                """)
                
                recent = cur.fetchall()
                for date, total, purchases in recent:
                    print(f"  {date}: {purchases}/{total} 購買預測")
                
                # 檢查觸發器狀態
                print("\n[3] 數據庫觸發器:")
                cur.execute("""
                    SELECT trigger_name, event_manipulation, action_timing
                    FROM information_schema.triggers
                    WHERE trigger_name LIKE 'prophet_%';
                """)
                
                triggers = cur.fetchall()
                for name, event, timing in triggers:
                    print(f"  {name}: {timing} {event}")
                
                print("\n" + "=" * 60)
                print("系統狀態: 正常運行")
                print("=" * 60)
                
                return True
                
        except Exception as e:
            print(f"[ERROR] 狀態檢查失敗: {e}")
            return False
        finally:
            if conn:
                conn.close()

def main():
    """測試數據庫整合功能"""
    print("=== 數據庫整合模組測試 ===")
    
    # 初始化數據庫整合
    db_integration = DatabaseIntegration()
    
    print("\n[1] 創建數據庫架構...")
    if db_integration.create_database_schema():
        print("✓ 數據庫架構創建成功")
    else:
        print("✗ 數據庫架構創建失敗")
        return False
    
    print("\n[2] 創建購買偵測觸發器...")
    if db_integration.create_purchase_detection_trigger():
        print("✓ 觸發器創建成功")
    else:
        print("✗ 觸發器創建失敗")
        return False
    
    print("\n[3] 測試數據導入...")
    test_predictions = [
        {
            'customer_id': 'TEST_001',
            'product_id': 'PROD_A',
            'prediction_date': '2025-08-08',
            'will_purchase_anything': True,
            'purchase_probability': 0.85,
            'estimated_quantity': 2,
            'confidence_level': 'high',
            'original_segment': 'VIP客戶'
        }
    ]
    
    batch_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if db_integration.import_predictions_to_database(test_predictions, batch_id):
        print("✓ 數據導入測試成功")
    else:
        print("✗ 數據導入測試失敗")
        return False
    
    print("\n[4] 系統狀態檢查...")
    db_integration.get_system_status()
    
    print("\n=== 數據庫整合模組測試完成 ===")
    return True

if __name__ == "__main__":
    main()