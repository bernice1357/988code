from fastapi import APIRouter, HTTPException
import psycopg2
import pandas as pd

router = APIRouter()

# 需要新增一個支援參數的資料庫查詢函數
def get_data_from_db_with_params(sql_prompt: str, params: tuple = ()) -> pd.DataFrame:
    try:
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_prompt, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(f"[DB ERROR] {e}")
        raise

# 得到特定客戶的所有交易日期
@router.get("/get_restock_history/{customer_id}")
def get_customer_transactions(customer_id: str):
    try:
        query = """
        SELECT transaction_date 
        FROM order_transactions 
        WHERE customer_id = %s 
        ORDER BY transaction_date ASC
        """
        # 使用參數化查詢避免 SQL 注入
        df = get_data_from_db_with_params(query, (customer_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 透過
@router.get("/get_recommendation_purchase_history/{customer_id}")
def get_customer_transactions(customer_id: str):
    try:
        query = """
        SELECT product_name, quantity, transaction_date
        FROM order_transactions 
        WHERE customer_id = %s 
        ORDER BY transaction_date DESC
        """
        # 使用參數化查詢避免 SQL 注入
        df = get_data_from_db_with_params(query, (customer_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 商品庫存 - 取得商品群組 modal 的資料
@router.get("/get_subcategory_items/{subcategory}")
def get_subcategory_items(subcategory: str):
    try:
        query = """
        SELECT pm.product_id, 
                pm.name_zh, 
                COALESCE(inv.stock_quantity, 0) as stock_quantity,
                pm.warehouse_id,
                pm.updated_at
        FROM product_master pm
        LEFT JOIN inventory inv ON pm.product_id = inv.product_id 
                            AND pm.warehouse_id = inv.warehouse_id
        WHERE pm.subcategory = %s 
        AND pm.is_active = 'active'
        ORDER BY pm.product_id, pm.warehouse_id
        """
        df = get_data_from_db_with_params(query, (subcategory,))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 商品庫存 - 取得類別的所有商品群組
@router.get("/get_subcategories_of_category/{category}")
def get_subcategories(category: str):
    try:
        query = "SELECT DISTINCT subcategory FROM product_master WHERE category = %s"
        df = get_data_from_db_with_params(query, (category,))
        subcategories = df['subcategory'].tolist()
        return {"subcategories": subcategories}
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 取得客戶的備註
@router.get("/get_customer_notes/{customer_id}")
def get_customer_notes(customer_id: str):
    try:
        query = "SELECT notes FROM customer WHERE customer_id = %s"
        df = get_data_from_db_with_params(query, (customer_id,))
        if df.empty:
            return {"notes": None}
        return {"notes": df.iloc[0]['notes']}
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
