#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月銷售預測資料庫操作類別
處理月銷售預測結果的資料庫存取
"""

import pandas as pd
import psycopg2
from datetime import datetime
import logging

class MonthlyPredictionDB:
    """月銷售預測資料庫操作類別"""
    
    def __init__(self, db_config):
        """初始化"""
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
        
    def get_database_connection(self):
        """建立數據庫連接"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            self.logger.error(f"數據庫連接失敗: {str(e)}")
            return None
    
    def save_predictions(self, subcategory_df, sku_df, batch_id):
        """儲存預測結果到資料庫"""
        conn = self.get_database_connection()
        if conn is None:
            return False
        
        try:
            cursor = conn.cursor()
            
            # 準備插入SQL
            insert_sql = """
            INSERT INTO monthly_sales_predictions (
                prediction_level, prediction_month, prediction_value, 
                subcategory, cv_value, volatility_group, prediction_method,
                product_id, product_name, allocation_ratio,
                month_minus_3, month_minus_2, month_minus_1,
                batch_id, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            records_inserted = 0
            
            # 插入子類別預測
            if subcategory_df is not None and len(subcategory_df) > 0:
                for _, row in subcategory_df.iterrows():
                    # 確定預測方法
                    prediction_method = self._determine_prediction_method(row.get('volatility_group', 'unknown'))
                    
                    # 取得預測月份
                    prediction_month = self._get_prediction_month_from_batch(batch_id)
                    
                    values = (
                        'subcategory',  # prediction_level
                        prediction_month,  # prediction_month
                        int(round(row.get('prediction', 0))),  # prediction_value (整數)
                        str(row.get('subcategory', '')),  # subcategory
                        float(row.get('cv', 0)) if row.get('cv') is not None else None,  # cv_value
                        str(row.get('volatility_group', '')),  # volatility_group
                        prediction_method,  # prediction_method
                        None,  # product_id
                        None,  # product_name
                        None,  # allocation_ratio
                        int(round(row.get('month_minus_3', 0))),  # month_minus_3 (整數)
                        int(round(row.get('month_minus_2', 0))),  # month_minus_2 (整數)
                        int(round(row.get('month_minus_1', 0))),  # month_minus_1 (整數)
                        batch_id,  # batch_id
                        datetime.now()  # created_at
                    )
                    
                    cursor.execute(insert_sql, values)
                    records_inserted += 1
            
            # 插入SKU預測
            if sku_df is not None and len(sku_df) > 0:
                for _, row in sku_df.iterrows():
                    prediction_month = self._get_prediction_month_from_batch(batch_id)
                    
                    values = (
                        'sku',  # prediction_level
                        prediction_month,  # prediction_month
                        int(round(row.get('prediction', 0))),  # prediction_value (整數)
                        str(row.get('subcategory', '')),  # subcategory
                        None,  # cv_value
                        None,  # volatility_group
                        None,  # prediction_method
                        str(row.get('product_id', '')),  # product_id
                        str(row.get('product_name', '')),  # product_name
                        float(row.get('allocation_ratio', 0)) if row.get('allocation_ratio') is not None else None,  # allocation_ratio
                        int(round(row.get('month_minus_3', 0))),  # month_minus_3 (整數)
                        int(round(row.get('month_minus_2', 0))),  # month_minus_2 (整數)
                        int(round(row.get('month_minus_1', 0))),  # month_minus_1 (整數)
                        batch_id,  # batch_id
                        datetime.now()  # created_at
                    )
                    
                    cursor.execute(insert_sql, values)
                    records_inserted += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"成功儲存 {records_inserted} 條預測記錄到資料庫")
            return True
            
        except Exception as e:
            self.logger.error(f"儲存預測結果失敗: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def _determine_prediction_method(self, volatility_group):
        """根據波動性分組確定預測方法"""
        method_map = {
            '低波動': 'prophet',
            '中波動': 'ewma',
            '高波動': 'median'
        }
        return method_map.get(volatility_group, 'unknown')
    
    def _get_prediction_month_from_batch(self, batch_id):
        """從batch_id中提取預測月份"""
        try:
            # batch_id 格式通常是 monthly_20250701_123456
            if 'monthly_' in batch_id:
                date_part = batch_id.split('_')[1]  # 20250701
                year = int(date_part[:4])
                month = int(date_part[4:6])
                return f"{year}-{month:02d}-01"
            else:
                # 如果無法解析，返回當前月份的下個月
                from dateutil.relativedelta import relativedelta
                next_month = datetime.now() + relativedelta(months=1)
                return next_month.strftime('%Y-%m-01')
        except:
            # 預設返回下個月
            from dateutil.relativedelta import relativedelta
            next_month = datetime.now() + relativedelta(months=1)
            return next_month.strftime('%Y-%m-01')
    
    def get_predictions(self, prediction_month, prediction_level=None):
        """查詢預測結果"""
        conn = self.get_database_connection()
        if conn is None:
            return None
        
        try:
            where_clause = "WHERE prediction_month = %s"
            params = [prediction_month]
            
            if prediction_level:
                where_clause += " AND prediction_level = %s"
                params.append(prediction_level)
            
            query = f"""
            SELECT * FROM monthly_sales_predictions 
            {where_clause}
            ORDER BY prediction_level, subcategory, product_id
            """
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"查詢預測結果失敗: {e}")
            if conn:
                conn.close()
            return None
    
    def get_prediction_summary(self, prediction_month):
        """取得預測摘要統計"""
        conn = self.get_database_connection()
        if conn is None:
            return None
        
        try:
            query = """
            SELECT 
                prediction_level,
                COUNT(*) as total_predictions,
                SUM(prediction_value) as total_predicted_value,
                AVG(prediction_value) as avg_predicted_value,
                MIN(prediction_value) as min_predicted_value,
                MAX(prediction_value) as max_predicted_value
            FROM monthly_sales_predictions 
            WHERE prediction_month = %s
            GROUP BY prediction_level
            ORDER BY prediction_level
            """
            
            df = pd.read_sql(query, conn, params=[prediction_month])
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"取得預測摘要失敗: {e}")
            if conn:
                conn.close()
            return None
    
    def get_batch_info(self, batch_id):
        """取得批次資訊"""
        conn = self.get_database_connection()
        if conn is None:
            return None
        
        try:
            query = """
            SELECT 
                batch_id,
                prediction_month,
                COUNT(*) as total_records,
                COUNT(CASE WHEN prediction_level = 'subcategory' THEN 1 END) as subcategory_count,
                COUNT(CASE WHEN prediction_level = 'sku' THEN 1 END) as sku_count,
                SUM(prediction_value) as total_predicted_value,
                MIN(created_at) as batch_start_time,
                MAX(created_at) as batch_end_time
            FROM monthly_sales_predictions 
            WHERE batch_id = %s
            GROUP BY batch_id, prediction_month
            """
            
            df = pd.read_sql(query, conn, params=[batch_id])
            conn.close()
            
            return df.iloc[0] if len(df) > 0 else None
            
        except Exception as e:
            self.logger.error(f"取得批次資訊失敗: {e}")
            if conn:
                conn.close()
            return None