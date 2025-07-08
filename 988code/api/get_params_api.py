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

# 商品庫存 - 取得商品群組底下的資料
# TODO現在還少備註、庫存量
@router.get("/get_subcategory_items/{subcategory}")
def get_subcategory_items(subcategory: str):
    try:
        query = """
        SELECT product_id, name_zh, specification, warehouse_id, updated_at
        FROM product_master 
        WHERE subcategory = %s
        """
        df = get_data_from_db_with_params(query, (subcategory,))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

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