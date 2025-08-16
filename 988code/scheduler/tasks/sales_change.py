import psycopg2
from psycopg2 import Error
import logging
from datetime import datetime, timedelta
from sales_change_db import SalesChangeDB

class SalesChangeManager:
    def __init__(self, db_config):
        """
        銷量變化管理系統
        
        Args:
            db_config: 資料庫設定字典
        """
        self.db_config = db_config
        self.connection = None
        self.db = SalesChangeDB(db_config)
        self.logger = logging.getLogger(__name__)

    def get_connection(self):
        """獲取資料庫連接"""
        try:
            if self.connection is None or self.connection.closed != 0:
                self.connection = psycopg2.connect(**self.db_config)
                self.connection.autocommit = False
            return self.connection
        except Error as e:
            self.logger.error(f"資料庫連接失敗: {e}")
            return None

    def execute_query(self, query, params=None, fetch=False):
        """執行SQL查詢"""
        connection = self.get_connection()
        if not connection:
            return None
            
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            
            if fetch:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows] if rows else []
            else:
                connection.commit()
                result = cursor.rowcount
                
            cursor.close()
            return result
        except Error as e:
            self.logger.error(f"執行查詢失敗: {e}")
            connection.rollback()
            return None

    def call_function(self, function_name, params=None):
        """呼叫PostgreSQL函數"""
        connection = self.get_connection()
        if not connection:
            return False
            
        try:
            cursor = connection.cursor()
            if params:
                cursor.execute(f"SELECT {function_name}(%s)", params)
            else:
                cursor.execute(f"SELECT {function_name}()")
            connection.commit()
            cursor.close()
            self.logger.info(f"函數 {function_name} 執行成功")
            return True
        except Error as e:
            self.logger.error(f"呼叫函數 {function_name} 失敗: {e}")
            connection.rollback()
            return False

    def daily_consistency_check(self):
        """每日資料一致性檢查"""
        self.logger.info("開始執行每日資料一致性檢查...")
        
        try:
            # 呼叫一致性檢查函數
            if self.call_function('check_data_consistency'):
                self.logger.info("每日資料一致性檢查完成")
                
                # 檢查異常資料
                self.check_anomalies()
            else:
                self.logger.error("每日資料一致性檢查失敗")
        except Exception as e:
            self.logger.error(f"每日檢查過程中發生錯誤: {e}")

    def check_anomalies(self):
        """檢查異常資料"""
        # 檢查銷量異常大的變化
        anomaly_query = """
        SELECT product_id, change_percentage, current_month_sales, last_month_sales
        FROM sales_change_table
        WHERE ABS(change_percentage) > 500
           OR (current_month_sales > 1000 AND last_month_sales = 0)
        ORDER BY ABS(change_percentage) DESC
        LIMIT 10
        """
        
        anomalies = self.execute_query(anomaly_query, fetch=True)
        if anomalies:
            self.logger.warning(f"發現 {len(anomalies)} 筆異常銷量變化:")
            for anomaly in anomalies:
                self.logger.warning(
                    f"產品ID: {anomaly['product_id']}, "
                    f"變化率: {anomaly['change_percentage']}%, "
                    f"當月: {anomaly['current_month_sales']}, "
                    f"上月: {anomaly['last_month_sales']}"
                )

    def monthly_reset(self):
        """月初重置銷量資料"""
        self.logger.info("開始執行月初銷量重置...")
        
        try:
            # 執行月度重置
            if self.call_function('reset_monthly_sales'):
                self.logger.info("月初銷量重置完成")
                
                # 重新初始化所有產品記錄
                self.initialize_new_month_data()
            else:
                self.logger.error("月初銷量重置失敗")
        except Exception as e:
            self.logger.error(f"月初重置過程中發生錯誤: {e}")

    def initialize_new_month_data(self):
        """初始化新月份的產品資料"""
        # 確保所有啟用產品都有記錄
        init_query = """
        INSERT INTO sales_change_table (
            product_id, last_month_sales, current_month_sales,
            change_amount, change_percentage, stock_quantity,
            recommendeed_customer_id_rank1, recommendeed_customer_id_rank2,
            recommendeed_customer_id_rank3
        )
        SELECT 
            pm.product_id,
            COALESCE(psc.last_month_sales, 0),
            0,
            0,
            0.00,
            COALESCE(inv.stock_quantity, 0),
            pcr.rank1,
            pcr.rank2,
            pcr.rank3
        FROM product_master pm
        LEFT JOIN product_sales_cache psc ON pm.product_id = psc.product_id
        LEFT JOIN inventory inv ON pm.product_id = inv.product_id
        LEFT JOIN (
            SELECT 
                product_id,
                MAX(CASE WHEN rank = 1 THEN recommendeed_customer_id END) as rank1,
                MAX(CASE WHEN rank = 2 THEN recommendeed_customer_id END) as rank2,
                MAX(CASE WHEN rank = 3 THEN recommendeed_customer_id END) as rank3
            FROM product_customer_recommendations
            WHERE rank IN (1, 2, 3)
            GROUP BY product_id
        ) pcr ON pm.product_id = pcr.product_id
        WHERE pm.is_active = 1
        ON CONFLICT (product_id) DO NOTHING
        """
        
        try:
            rows_initialized = self.execute_query(init_query)
            self.logger.info(f"新月份初始化 {rows_initialized} 筆產品記錄")
        except Exception as e:
            self.logger.error(f"新月份資料初始化失敗: {e}")

    def manual_update_product_sales(self, product_id):
        """手動更新特定產品的銷量資料"""
        self.logger.info(f"手動更新產品 {product_id} 的銷量資料...")
        
        # 重新計算該產品的銷量
        update_query = """
        UPDATE sales_change_table 
        SET current_month_sales = calc.current_sales,
            change_amount = calc.current_sales - sales_change_table.last_month_sales,
            change_percentage = CASE 
                WHEN sales_change_table.last_month_sales > 0 THEN 
                    ((calc.current_sales - sales_change_table.last_month_sales)::DECIMAL / sales_change_table.last_month_sales) * 100
                ELSE 0.00 
            END,
            stock_quantity = COALESCE(inv.stock_quantity, 0),
            recommendeed_customer_id_rank1 = pcr.rank1,
            recommendeed_customer_id_rank2 = pcr.rank2,
            recommendeed_customer_id_rank3 = pcr.rank3,
            updated_at = CURRENT_TIMESTAMP
        FROM (
            SELECT 
                product_id,
                SUM(quantity) as current_sales
            FROM order_transactions
            WHERE product_id = %s
              AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
              AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
            GROUP BY product_id
        ) calc,
        inventory inv,
        (
            SELECT 
                product_id,
                MAX(CASE WHEN rank = 1 THEN recommendeed_customer_id END) as rank1,
                MAX(CASE WHEN rank = 2 THEN recommendeed_customer_id END) as rank2,
                MAX(CASE WHEN rank = 3 THEN recommendeed_customer_id END) as rank3
            FROM product_customer_recommendations
            WHERE rank IN (1, 2, 3) AND product_id = %s
            GROUP BY product_id
        ) pcr
        WHERE sales_change_table.product_id = calc.product_id
          AND sales_change_table.product_id = inv.product_id
          AND sales_change_table.product_id = pcr.product_id
          AND sales_change_table.product_id = %s
        """
        
        try:
            rows_updated = self.execute_query(update_query, (product_id, product_id, product_id))
            if rows_updated and rows_updated > 0:
                self.logger.info(f"產品 {product_id} 銷量資料更新成功")
            else:
                self.logger.warning(f"產品 {product_id} 沒有找到或無需更新")
            return rows_updated and rows_updated > 0
        except Exception as e:
            self.logger.error(f"手動更新產品 {product_id} 失敗: {e}")
            return False

    def initialize_system(self):
        """初始化銷量變化監控系統"""
        return self.db.create_indexes()
    
    def get_sales_statistics(self):
        """獲取銷量變化統計"""
        return self.db.get_sales_statistics()