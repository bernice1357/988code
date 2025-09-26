#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產品潛在客戶搜尋系統 - 資料庫管理模組
"""

import psycopg2
import logging
from typing import List, Dict, Optional, Tuple
from potential_customer_finder.config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    """資料庫管理類別，處理與PostgreSQL的所有互動"""
    
    def __init__(self):
        """初始化資料庫連線"""
        self.connection = None
        self._connect()
    
    def _connect(self):
        """建立資料庫連線"""
        try:
            self.connection = psycopg2.connect(**DATABASE_CONFIG)
            logger.info("資料庫連線成功")
        except psycopg2.Error as e:
            logger.error(f"資料庫連線失敗: {e}")
            raise
    
    def _ensure_connection(self):
        """確保資料庫連線有效"""
        if self.connection is None or self.connection.closed:
            logger.info("重新建立資料庫連線")
            self._connect()
    
    def execute_query(self, query: str, params: Optional[tuple] = None, fetch_all: bool = True):
        """執行SQL查詢"""
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.fetchone()
                    
        except psycopg2.Error as e:
            logger.error(f"查詢執行失敗: {e}")
            self.connection.rollback()
            raise
    
    def get_customers_who_purchased_by_subcategory(self, product_name: str, customer_ids: List[str]) -> List[str]:
        """批量檢查哪些客戶購買過同一子類別的產品"""
        if not customer_ids:
            return []
        
        try:
            # 第1步：獲取產品的 product_id
            product_id = self.get_product_id_by_name_zh(product_name)
            
            if not product_id:
                logger.warning(f"未找到產品 '{product_name}' 的 product_id")
                return []
            
            # 第2步：通過 product_id 獲取 subcategory
            subcategory_query = """
            SELECT subcategory
            FROM product_master
            WHERE product_id = %s
            """
            
            subcategory_result = self.execute_query(subcategory_query, (product_id,), fetch_all=False)
            if not subcategory_result:
                logger.warning(f"未找到 product_id '{product_id}' 的子類別")
                return []
            
            subcategory = subcategory_result[0]
            logger.info(f"產品 '{product_name}' 屬於子類別: '{subcategory}'")
            
            # 第3步：找到同一子類別下的所有 product_id
            same_subcategory_query = """
            SELECT DISTINCT product_id
            FROM product_master
            WHERE subcategory = %s
            """
            
            same_subcategory_results = self.execute_query(same_subcategory_query, (subcategory,))
            subcategory_product_ids = [result[0] for result in same_subcategory_results]
            
            if not subcategory_product_ids:
                logger.warning(f"子類別 '{subcategory}' 下沒有找到任何產品")
                return []
                
            # 第4步：檢查這些客戶是否購買過同子類別的任何產品
            customer_placeholders = ', '.join(['%s'] * len(customer_ids))
            product_placeholders = ', '.join(['%s'] * len(subcategory_product_ids))
            
            purchase_query = f"""
            SELECT DISTINCT customer_id
            FROM order_transactions
            WHERE customer_id IN ({customer_placeholders})
            AND product_id IN ({product_placeholders})
            """
            
            params = customer_ids + subcategory_product_ids
            results = self.execute_query(purchase_query, tuple(params))
            purchased_customers = [result[0] for result in results]
            
            logger.info(f"找到 {len(purchased_customers)} 個客戶購買過子類別 '{subcategory}' 的產品")
            return purchased_customers
            
        except Exception as e:
            logger.error(f"批量檢查客戶子類別購買記錄失敗: {e}")
            return []
    
    def get_product_id_by_name_zh(self, product_name: str) -> Optional[str]:
        """從 product_master 表透過 name_zh 獲取 product_id"""
        query = """
        SELECT product_id
        FROM product_master
        WHERE name_zh = %s
        """
        
        try:
            result = self.execute_query(query, (product_name,), fetch_all=False)
            if result:
                logger.info(f"找到產品 '{product_name}' 的 product_id: {result[0]}")
                return result[0]
            else:
                logger.warning(f"未找到產品 '{product_name}' 在 product_master 中")
                return None
        except Exception as e:
            logger.error(f"查詢 product_id 失敗: {e}")
            return None
    
    def get_recommended_customers_by_product_id(self, product_id: str) -> List[Dict]:
        """
        從 product_customer_recommendations 獲取推薦客戶 (rank1-7)
        
        Args:
            product_id: 產品ID
            
        Returns:
            List[Dict]: 推薦客戶列表
        """
        query = """
        SELECT 
            pcr.product_id,
            pcr.recommended_customer_id_rank1,
            pcr.recommended_customer_id_rank2,
            pcr.recommended_customer_id_rank3,
            pcr.recommended_customer_id_rank4,
            pcr.recommended_customer_id_rank5,
            pcr.recommended_customer_id_rank6,
            pcr.recommended_customer_id_rank7
        FROM product_customer_recommendations pcr
        WHERE pcr.product_id = %s
        """
        
        try:
            result = self.execute_query(query, (product_id,), fetch_all=False)
            
            if not result:
                logger.warning(f"未找到產品ID '{product_id}' 的推薦客戶")
                return []
            
            # 提取推薦客戶ID (rank1-7)
            recommended_customer_ids = []
            for i in range(1, 8):  # rank1 到 rank7
                customer_id = result[i]  # result[1] 到 result[7]
                if customer_id:  # 排除空值
                    recommended_customer_ids.append(customer_id)
            
            if not recommended_customer_ids:
                logger.info(f"產品ID '{product_id}' 沒有有效的推薦客戶")
                return []
            
            # 批量查詢客戶名稱
            placeholders = ', '.join(['%s'] * len(recommended_customer_ids))
            customer_query = f"""
            SELECT customer_id, customer_name
            FROM customer
            WHERE customer_id IN ({placeholders})
            """
            
            customer_results = self.execute_query(customer_query, tuple(recommended_customer_ids))
            
            # 建立客戶資料字典
            customers = []
            customer_name_map = {r[0]: r[1] for r in customer_results}
            
            for i, customer_id in enumerate(recommended_customer_ids, 1):
                customers.append({
                    'customer_id': customer_id,
                    'customer_name': customer_name_map.get(customer_id, 'Unknown'),
                    'recommendation_rank': i
                })
            
            logger.info(f"找到 {len(customers)} 個產品ID '{product_id}' 的推薦客戶")
            return customers
            
        except Exception as e:
            logger.error(f"獲取推薦客戶失敗: {e}")
            return []

    def close(self):
        """關閉資料庫連線"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("資料庫連線已關閉")

# 單例模式的資料庫管理器
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """獲取資料庫管理器實例 (單例模式)"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager