from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional
import logging
import sys
import os

# Add predict_product_main to path for database modules
predict_main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'predict_product_main'))
if predict_main_path not in sys.path:
    sys.path.insert(0, predict_main_path)

from inactive_customer_db import InactiveCustomerDB

class InactiveCustomerManager:
    """
    不活躍客戶管理類別 - 後端數據層
    - 後端（此系統）：1天後建立不活躍記錄到DB，持續維護數據狀態
    
    inactive_customers 表欄位說明：
    - id: SERIAL PRIMARY KEY - 自動遞增的主鍵
    - customer_id: VARCHAR(100) NOT NULL - 客戶編號
    - customer_name: VARCHAR(100) - 客戶名稱
    - first_inactive_date: DATE NOT NULL - 首次標記為不活躍的日期
    - last_check_date: DATE NOT NULL - 最後檢查/更新的日期
    - inactive_days: INTEGER NOT NULL DEFAULT 0 - 累計不活躍天數
    - last_order_date: TIMESTAMP - 客戶最後一次購買時間
    - last_product: VARCHAR(255) - 最後購買的商品名稱
    - processed: BOOLEAN DEFAULT FALSE - 是否已由客服處理（前端更新）
    - processed_at: TIMESTAMP - 客服處理時間
    - processed_by: VARCHAR(100) - 處理人員名稱或ID
    - process_note: TEXT - 處理備註
    - reactivated_date: DATE - 客戶重新購買的日期（NULL表示仍不活躍）
    - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - 記錄建立時間
    - updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - 最後更新時間
    """
    
    def __init__(self, db_config: Dict[str, str], inactive_days: int = 1):
        """
        初始化
        
        Args:
            db_config: 資料庫設定
            inactive_days: 後端建立記錄的天數（建議1天，供前端靈活使用）
        """
        self.db_config = db_config
        self.inactive_days = inactive_days  # 後端建立記錄的門檻（1天）
        self.tz_utc8 = timezone(timedelta(hours=8))
        self.db = InactiveCustomerDB(db_config)
        self.logger = logging.getLogger(__name__)
        
    def get_current_date_utc8(self) -> date:
        """取得 UTC+8 的當前日期"""
        return datetime.now(self.tz_utc8).date()
    
    def initialize_system(self):
        """初始化系統（建立表和觸發器）"""
        self.logger.info("初始化不活躍客戶管理系統...")
        
        # 建立表
        if not self.db.create_inactive_customers_table():
            self.logger.error("建立不活躍客戶表失敗")
            return False
        
        # 建立觸發器
        if not self.db.create_reactivation_trigger():
            self.logger.error("建立重新活躍觸發器失敗")
            return False
        
        self.logger.info("不活躍客戶管理系統初始化完成")
        return True
    
    def daily_check_inactive_customers(self):
        """
        每日執行的主要邏輯（後端數據維護）
        1. 找出所有超過1天未購買的客戶，建立不活躍記錄
        2. 更新現有記錄的不活躍天數
        
        注意：重新活躍狀態由觸發器自動處理
        """
        current_date = self.get_current_date_utc8()
        self.logger.info(f"開始檢查不活躍客戶 - {current_date}")
        
        try:
            # 獲取需要處理的不活躍客戶
            inactive_customers = self.db.get_inactive_customers_to_process(self.inactive_days)
            self.logger.info(f"找到 {len(inactive_customers)} 個符合條件的客戶")
            
            new_records = 0
            updated_records = 0
            
            # 處理每個不活躍客戶
            for customer in inactive_customers:
                result = self.db.upsert_inactive_customer(customer)
                
                if result == "inserted":
                    new_records += 1
                elif result == "updated":
                    updated_records += 1
            
            # 獲取今日重新活躍的客戶（由觸發器自動更新）
            reactivated_customers = self.db.get_reactivated_customers_today()
            
            # 顯示執行結果
            self.logger.info(f"執行結果: 新增 {new_records} 筆, 更新 {updated_records} 筆")
            self.logger.info(f"今日重新活躍客戶: {len(reactivated_customers)} 個")
            
            if reactivated_customers:
                for customer in reactivated_customers:
                    self.logger.info(f"重新活躍: {customer['customer_id']} {customer['customer_name']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"每日檢查不活躍客戶失敗: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """取得完整統計資訊"""
        return self.db.get_inactive_customer_stats()
    
    def mark_as_processed(self, customer_id: str, processed_by: str, note: str = ''):
        """標記客戶為已處理"""
        return self.db.mark_customer_processed(customer_id, processed_by, note)
    
    def get_inactive_customers(self, min_days: int = 1) -> List[Dict]:
        """取得不活躍客戶列表"""
        conn = self.db.get_database_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM inactive_customers
                WHERE reactivated_date IS NULL
                    AND inactive_days >= %s
                ORDER BY inactive_days DESC, first_inactive_date ASC
            """, (min_days,))
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            self.logger.error(f"查詢不活躍客戶失敗: {e}")
            if conn:
                conn.close()
            return []
    
    def cleanup_old_records(self, days_to_keep=90):
        """清理過期記錄"""
        return self.db.cleanup_old_records(days_to_keep)

def generate_inactive_customer_report(db_config=None):
    """生成不活躍客戶檢查，返回統計資料"""
    if db_config is None:
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': '988',
            'user': 'postgres',
            'password': '1234'
        }
    
    manager = InactiveCustomerManager(db_config, inactive_days=1)
    
    try:
        # 執行每日檢查
        success = manager.daily_check_inactive_customers()
        
        if not success:
            return None
        
        # 獲取統計資料
        stats = manager.get_statistics()
        
        return stats
        
    except Exception as e:
        logging.error(f"生成不活躍客戶報告失敗: {e}")
        return None

def main():
    """測試用主函數"""
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': '988',
        'user': 'postgres',
        'password': '1234'
    }
    
    manager = InactiveCustomerManager(db_config, inactive_days=1)
    
    # 初始化系統
    if manager.initialize_system():
        print("系統初始化成功")
        
        # 執行一次檢查
        if manager.daily_check_inactive_customers():
            print("不活躍客戶檢查完成")
            
            # 顯示統計
            stats = manager.get_statistics()
            if stats:
                print(f"\n統計結果:")
                print(f"總不活躍客戶: {stats.get('total_inactive', 0)}")
                print(f"今日新增: {stats.get('today_created', 0)}")
                print(f"本月重新活躍: {stats.get('reactivated_this_month', 0)}")
        else:
            print("不活躍客戶檢查失敗")
    else:
        print("系統初始化失敗")

if __name__ == "__main__":
    main()
