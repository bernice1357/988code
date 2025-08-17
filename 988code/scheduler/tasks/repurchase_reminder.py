from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import sys
import os

# Add predict_product_main to path for database modules
predict_main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'predict_product_main'))
if predict_main_path not in sys.path:
    sys.path.insert(0, predict_main_path)

from repurchase_reminder_db import RepurchaseReminderDB

class RepurchaseReminder:
    """
    回購提醒處理類別
    
    repurchase_reminders 表欄位說明：
    - id: SERIAL PRIMARY KEY - 自動遞增的主鍵
    - customer_id: VARCHAR(100) - 客戶ID
    - customer_name: VARCHAR(100) - 客戶名稱
    - line_id: VARCHAR(100) - LINE用戶ID
    - product_name: VARCHAR(255) - 產品名稱
    - last_purchase_date: TIMESTAMP - 最後購買日期（來自temp_customer_records的created_at）
    - days_since_purchase: INTEGER - 距離購買已經過的天數（每日更新）
    - reminder_sent: BOOLEAN DEFAULT FALSE - 是否已發送提醒
    - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - 提醒記錄建立時間
    - updated_at: TIMESTAMP - 最後更新時間
    
    功能：
    1. 購買新品1天後建立提醒記錄
    2. 每天更新所有未發送提醒的 days_since_purchase
    3. 自動標記已重新購買的客戶
    """
 
    def __init__(self, db_config, create_reminder_after_days=1):
        self.db_config = db_config
        self.create_reminder_after_days = create_reminder_after_days
        self.tz_utc8 = timezone(timedelta(hours=8))
        self.logger = logging.getLogger(__name__)
        self.db = RepurchaseReminderDB(db_config)
        
    def get_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def get_current_time_utc8(self):
        return datetime.now(self.tz_utc8)
    
    def daily_repurchase_reminder_maintenance(self):
        """每日回購提醒維護（建立新記錄 + 更新現有記錄）"""
        current_time = self.get_current_time_utc8()
        print(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}] 開始回購提醒維護...")
        
        # 步驟1: 建立新的提醒記錄
        new_count = self.create_repurchase_reminder_records()
        
        # 步驟2: 更新現有提醒記錄的天數
        updated_count = self.update_existing_reminders()
        
        # 步驟3: 處理已重新購買的客戶
        completed_count = self.mark_completed_reminders()
        
        print(f"維護完成: 新增 {new_count} 筆, 更新 {updated_count} 筆, 完成 {completed_count} 筆")
        
        # 顯示統計
        self.show_statistics()
    
    def create_repurchase_reminder_records(self):
        """建立新的回購提醒記錄（購買新品1天後）"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                current_time = self.get_current_time_utc8()
                cutoff_date = current_time - timedelta(days=self.create_reminder_after_days)
                
                cursor.execute("""
                    SELECT DISTINCT ON (customer_id, purchase_record) 
                        id, line_id, customer_id, customer_name, 
                        purchase_record, created_at
                    FROM temp_customer_records
                    WHERE is_new_product = true
                        AND created_at <= %s
                        AND (customer_id, purchase_record) NOT IN (
                            SELECT customer_id, product_name 
                            FROM repurchase_reminders 
                            WHERE customer_id IS NOT NULL 
                            AND product_name IS NOT NULL
                        )
                    ORDER BY customer_id, purchase_record, created_at DESC
                """, (cutoff_date,))
                
                new_reminders = cursor.fetchall()
                
                created_count = 0
                for reminder in new_reminders:
                    try:
                        days_since = (current_time - reminder['created_at'].replace(tzinfo=self.tz_utc8)).days
                        
                        cursor.execute("""
                            INSERT INTO repurchase_reminders 
                            (customer_id, customer_name, line_id, product_name,
                             last_purchase_date, days_since_purchase, reminder_sent, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            reminder['customer_id'],
                            reminder['customer_name'],
                            reminder['line_id'],
                            reminder['purchase_record'],
                            reminder['created_at'],
                            days_since,
                            False,
                            current_time,
                            current_time
                        ))
                        created_count += 1
                        
                    except psycopg2.IntegrityError:
                        conn.rollback()
                        continue
                
                conn.commit()
                return created_count
                
        except Exception as e:
            conn.rollback()
            print(f"建立新記錄錯誤: {e}")
            return 0
        finally:
            conn.close()
    
    def update_existing_reminders(self):
        """更新現有提醒記錄的天數"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                current_time = self.get_current_time_utc8()
                
                # 更新所有未發送且未完成的提醒記錄
                cursor.execute("""
                    UPDATE repurchase_reminders 
                    SET days_since_purchase = EXTRACT(EPOCH FROM (%s - last_purchase_date)) / 86400,
                        updated_at = %s
                    WHERE reminder_sent = FALSE 
                    AND last_purchase_date IS NOT NULL
                    RETURNING id, customer_id, product_name, days_since_purchase
                """, (current_time, current_time))
                
                updated_records = cursor.fetchall()
                updated_count = len(updated_records)
                
                conn.commit()
                return updated_count
                
        except Exception as e:
            conn.rollback()
            print(f"更新天數錯誤: {e}")
            return 0
        finally:
            conn.close()
    
    def mark_completed_reminders(self):
        """標記已重新購買的客戶（提醒完成）"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                current_time = self.get_current_time_utc8()
                
                # 找出已重新購買相同產品的客戶
                cursor.execute("""
                    UPDATE repurchase_reminders rr
                    SET reminder_sent = TRUE,
                        updated_at = %s
                    FROM (
                        SELECT DISTINCT
                            rr.id,
                            rr.customer_id,
                            rr.product_name
                        FROM repurchase_reminders rr
                        INNER JOIN temp_customer_records tcr 
                            ON rr.customer_id = tcr.customer_id
                            AND rr.product_name = tcr.purchase_record
                            AND tcr.created_at > rr.last_purchase_date
                            AND tcr.is_new_product = true
                        WHERE rr.reminder_sent = FALSE
                    ) AS repurchased
                    WHERE rr.id = repurchased.id
                    RETURNING rr.customer_id, rr.product_name
                """, (current_time,))
                
                completed_records = cursor.fetchall()
                completed_count = len(completed_records)
                
                conn.commit()
                return completed_count
                
        except Exception as e:
            conn.rollback()
            print(f"標記完成錯誤: {e}")
            return 0
        finally:
            conn.close()
    
    def show_statistics(self):
        """顯示回購提醒統計"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 總提醒記錄數
                cursor.execute("SELECT COUNT(*) as total FROM repurchase_reminders WHERE reminder_sent = FALSE")
                total_result = cursor.fetchone()
                total_reminders = total_result['total'] if total_result else 0
                
                # 按天數分組統計
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN days_since_purchase BETWEEN 1 AND 7 THEN '1-7天'
                            WHEN days_since_purchase BETWEEN 8 AND 15 THEN '8-15天'
                            WHEN days_since_purchase BETWEEN 16 AND 30 THEN '16-30天'
                            WHEN days_since_purchase > 30 THEN '30天以上'
                        END as day_range,
                        COUNT(*) as count
                    FROM repurchase_reminders 
                    WHERE reminder_sent = FALSE
                    AND days_since_purchase > 0
                    GROUP BY 
                        CASE 
                            WHEN days_since_purchase BETWEEN 1 AND 7 THEN '1-7天'
                            WHEN days_since_purchase BETWEEN 8 AND 15 THEN '8-15天'
                            WHEN days_since_purchase BETWEEN 16 AND 30 THEN '16-30天'
                            WHEN days_since_purchase > 30 THEN '30天以上'
                        END
                    ORDER BY MIN(days_since_purchase)
                """)
                day_stats = cursor.fetchall()
                
                # 今日新增記錄
                today = self.get_current_time_utc8().date()
                cursor.execute("""
                    SELECT COUNT(*) as today_created FROM repurchase_reminders 
                    WHERE DATE(created_at AT TIME ZONE 'UTC' AT TIME ZONE '+08:00') = %s
                """, (today,))
                today_result = cursor.fetchone()
                today_created = today_result['today_created'] if today_result else 0
                
                print(f"\n=== 回購提醒統計 ===")
                print(f"待處理提醒總數: {total_reminders}")
                print(f"今日新增記錄: {today_created}")
                print(f"\n按天數分布（供前端篩選參考）:")
                for stat in day_stats:
                    print(f"  {stat['day_range']}: {stat['count']} 筆")
                print(f"\n前端可根據業務需求篩選：")
                print(f"  - 7天提醒: >= 7天的記錄")
                print(f"  - 15天提醒: >= 15天的記錄")
                print(f"  - 30天最後提醒: >= 30天的記錄")
                print("=" * 25)
                
        except Exception as e:
            print(f"統計錯誤: {e}")
        finally:
            conn.close()
    
    def get_reminders_by_days(self, min_days=7, max_days=None):
        """根據天數獲取提醒記錄（供前端使用）"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM repurchase_reminders
                    WHERE reminder_sent = FALSE
                    AND days_since_purchase >= %s
                """
                params = [min_days]
                
                if max_days:
                    query += " AND days_since_purchase <= %s"
                    params.append(max_days)
                
                query += " ORDER BY days_since_purchase DESC, created_at ASC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Exception as e:
            print(f"查詢錯誤: {e}")
            return []
        finally:
            conn.close()

def main():
    """測試用主函數"""
    db_config = {
        'host': '26.210.160.206',
        'port': 5433,
        'database': '988',
        'user': 'n8n',
        'password': '1234'
    }
    
    reminder = RepurchaseReminder(db_config, create_reminder_after_days=1)
    
    # 執行一次維護
    reminder.daily_repurchase_reminder_maintenance()
    
    print("\n回購提醒維護測試完成")

if __name__ == "__main__":
    main()