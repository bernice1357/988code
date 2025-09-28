from fastapi import APIRouter, HTTPException
import sys
import os
# 新增資料庫連線管理
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection, execute_query, execute_transaction
from env_loader import load_env_file

# 載入環境變數
load_env_file()
from pydantic import BaseModel
from typing import List
import psycopg2
import pandas as pd
from datetime import datetime

router = APIRouter()

# 數據模型
class SalesDataRequest(BaseModel):
    filter_level: str  # 'category', 'subcategory', 'name_zh', 'city', 'district'
    filter_values: List[str]
    start_date: str  # 'YYYY-MM-DD'
    end_date: str    # 'YYYY-MM-DD'

def get_data_from_db(sql_prompt: str) -> pd.DataFrame:
    """執行SQL查詢並返回DataFrame"""
    try:
        # 使用統一的資料庫連線系統
        rows = execute_query(sql_prompt, (), fetch='all')

        # 如果沒有結果，返回空 DataFrame
        if not rows:
            return pd.DataFrame()

        # 需要獲取列名，使用新的連線方式
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_prompt)
                columns = [desc[0] for desc in cursor.description]

        df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(f"[DB ERROR] {e}")
        raise

@router.post("/get_sales_data")
def get_sales_data(request: SalesDataRequest):
    """
    根據產品階層或地理位置和日期範圍查詢銷售資料
    
    Parameters:
    - filter_level: 篩選層級 'category', 'subcategory', 'name_zh', 'city', 或 'district'
    - filter_values: 篩選值清單
    - start_date: 開始日期 'YYYY-MM-DD'
    - end_date: 結束日期 'YYYY-MM-DD'
    
    Returns:
    - 包含銷售資料的 JSON
    """
    try:
        # 將篩選值轉換為SQL IN子句格式
        filter_values_str = "'" + "','".join(request.filter_values) + "'"
        
        # 根據篩選層級建立不同的SQL查詢
        if request.filter_level == 'category':
            sql = f"""
            SELECT 
                DATE_TRUNC('month', ot.transaction_date) as sales_month,
                pm.category as filter_value,
                SUM(ot.amount) as total_amount
            FROM order_transactions ot
            JOIN product_master pm ON ot.product_id = pm.product_id
            WHERE ot.document_type = '銷貨'
                AND ot.transaction_date >= '{request.start_date}'
                AND ot.transaction_date <= '{request.end_date}'
                AND ot.is_active = 'active'
                AND pm.category IN ({filter_values_str})
            GROUP BY DATE_TRUNC('month', ot.transaction_date), pm.category
            ORDER BY sales_month, pm.category
            """
        elif request.filter_level == 'subcategory':
            sql = f"""
            SELECT 
                DATE_TRUNC('month', ot.transaction_date) as sales_month,
                pm.subcategory as filter_value,
                SUM(ot.amount) as total_amount
            FROM order_transactions ot
            JOIN product_master pm ON ot.product_id = pm.product_id
            WHERE ot.document_type = '銷貨'
                AND ot.transaction_date >= '{request.start_date}'
                AND ot.transaction_date <= '{request.end_date}'
                AND ot.is_active = 'active'
                AND pm.subcategory IN ({filter_values_str})
            GROUP BY DATE_TRUNC('month', ot.transaction_date), pm.subcategory
            ORDER BY sales_month, pm.subcategory
            """
        elif request.filter_level == 'name_zh':
            sql = f"""
            SELECT 
                DATE_TRUNC('month', ot.transaction_date) as sales_month,
                pm.name_zh as filter_value,
                SUM(ot.amount) as total_amount
            FROM order_transactions ot
            JOIN product_master pm ON ot.product_id = pm.product_id
            WHERE ot.document_type = '銷貨'
                AND ot.transaction_date >= '{request.start_date}'
                AND ot.transaction_date <= '{request.end_date}'
                AND ot.is_active = 'active'
                AND pm.name_zh IN ({filter_values_str})
            GROUP BY DATE_TRUNC('month', ot.transaction_date), pm.name_zh
            ORDER BY sales_month, pm.name_zh
            """
        elif request.filter_level == 'city':
            sql = f"""
            SELECT 
                DATE_TRUNC('month', ot.transaction_date) as sales_month,
                c.city as filter_value,
                SUM(ot.amount) as total_amount
            FROM order_transactions ot
            JOIN customer c ON ot.customer_id = c.customer_id
            WHERE ot.document_type = '銷貨'
                AND ot.transaction_date >= '{request.start_date}'
                AND ot.transaction_date <= '{request.end_date}'
                AND ot.is_active = 'active'
                AND c.city IN ({filter_values_str})
            GROUP BY DATE_TRUNC('month', ot.transaction_date), c.city
            ORDER BY sales_month, c.city
            """
        elif request.filter_level == 'district':
            sql = f"""
            SELECT 
                DATE_TRUNC('month', ot.transaction_date) as sales_month,
                c.district as filter_value,
                SUM(ot.amount) as total_amount
            FROM order_transactions ot
            JOIN customer c ON ot.customer_id = c.customer_id
            WHERE ot.document_type = '銷貨'
                AND ot.transaction_date >= '{request.start_date}'
                AND ot.transaction_date <= '{request.end_date}'
                AND ot.is_active = 'active'
                AND c.district IN ({filter_values_str})
            GROUP BY DATE_TRUNC('month', ot.transaction_date), c.district
            ORDER BY sales_month, c.district
            """
        else:
            raise HTTPException(status_code=400, detail="filter_level 必須是 'category', 'subcategory', 'name_zh', 'city', 或 'district'")
            
        # 執行查詢
        df = get_data_from_db(sql)
        
        if df.empty:
            return {"data": [], "message": "沒有找到符合條件的資料"}
        
        # 將結果轉換為 JSON 格式，處理日期序列化
        result = []
        for _, row in df.iterrows():
            result.append({
                "sales_month": row['sales_month'].strftime('%Y-%m-%d') if pd.notnull(row['sales_month']) else None,
                "filter_value": row['filter_value'],
                "total_amount": float(row['total_amount']) if pd.notnull(row['total_amount']) else 0
            })
        
        return {"data": result, "message": "查詢成功"}
        
    except Exception as e:
        print(f"[API ERROR] get_sales_data: {e}")
        raise HTTPException(status_code=500, detail=f"資料庫查詢失敗: {str(e)}")

@router.get("/get_product_hierarchy")
def get_product_hierarchy():
    """
    取得產品階層資料
    
    Returns:
    - 包含各層級資料的字典
    """
    try:
        sql = """
        SELECT DISTINCT category, subcategory, name_zh 
        FROM product_master 
        WHERE is_active = 'active'
        ORDER BY category, subcategory, name_zh
        """
        
        df = get_data_from_db(sql)
        
        if df.empty:
            return {"categories": [], "subcategories": {}, "products": {}}
        
        # 整理成階層結構
        hierarchy = {
            'categories': df['category'].unique().tolist(),
            'subcategories': df.groupby('category')['subcategory'].apply(list).to_dict(),
            'products': df.groupby(['category', 'subcategory'])['name_zh'].apply(list).to_dict()
        }
        
        return hierarchy
        
    except Exception as e:
        print(f"[API ERROR] get_product_hierarchy: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")