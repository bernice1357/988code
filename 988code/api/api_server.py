# uvicorn api_server:app --reload

from fastapi import FastAPI, HTTPException
import psycopg2
import pandas as pd
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI()

# get
def get_data_from_db(sql_prompt: str) -> pd.DataFrame:
    try:
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_prompt)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(f"[DB ERROR] {e}")
        raise

# put
def update_data_to_db(sql_prompt: str, params: tuple = ()):
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
                conn.commit()
    except Exception as e:
        print(f"[DB ERROR] {e}")
        raise

# 得到首頁新進訂單
@app.get("/get_new_orders")
def get_new_orders():
    print("[API] get_new_orders 被呼叫")
    try:
        df = get_data_from_db('SELECT * FROM temp_customer_records')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_new_orders: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 客戶資料管理列表資料
@app.get("/get_customer_data")
def get_customer_data():
    print("[API] get_customer_data 被呼叫")
    try:
        query = """
        SELECT c.customer_id, c.customer_name, c.address, c.delivery_schedule,
                ot.transaction_date, c.notes
        FROM customer c
        LEFT JOIN (
            SELECT customer_id, transaction_date,
                    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY transaction_date DESC) as rn
            FROM order_transactions
        ) ot ON c.customer_id = ot.customer_id AND ot.rn = 1
        """
        df = get_data_from_db(query)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_customer_data: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到客戶最新補貨紀錄
# TODO 還沒放預計補貨日期欄位
@app.get("/get_restock_transactions")
def get_customer_latest_transactions():
    print("[API] get_customer_latest_transactions 被呼叫")
    try:
        query = """
        SELECT ot.customer_id, c.customer_name, ot.product_name, ot.transaction_date
        FROM (
            SELECT customer_id, product_name, transaction_date,
                   ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY transaction_date DESC) as rn
            FROM order_transactions
        ) ot
        LEFT JOIN customer c ON ot.customer_id = c.customer_id
        WHERE ot.rn = 1
        """
        df = get_data_from_db(query)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_customer_latest_transactions: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

class RecordUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    purchase_record: Optional[str] = None
    updated_at: Optional[datetime] = None
    status: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None

# 更新暫存訂單
@app.put("/temp/{id}")
def update_temp(id: int, update_data: RecordUpdate):
    update_fields = update_data.dict(exclude_none=True)

    if not update_fields:
        raise HTTPException(status_code=400, detail="沒有提供要更新的欄位")

    set_clause = ", ".join([f"{key} = %s" for key in update_fields])
    sql = f"UPDATE temp_customer_records SET {set_clause} WHERE id = %s"
    params = tuple(update_fields.values()) + (id,)

    try:
        update_data_to_db(sql, params)
        return {
            "message": "更新成功",
            "id": id,
            "updated_fields": update_fields
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫更新失敗")

# 更新客戶資料
class CustomerUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

@app.put("/customer/{customer_id}")
def update_customer(customer_id: str, update_data: CustomerUpdate):
    update_fields = update_data.dict(exclude_none=True)

    if not update_fields:
        raise HTTPException(status_code=400, detail="沒有提供要更新的欄位")

    set_clause = ", ".join([f"{key} = %s" for key in update_fields])
    sql = f"UPDATE customer SET {set_clause} WHERE customer_id = %s"
    params = tuple(update_fields.values()) + (customer_id,)

    try:
        update_data_to_db(sql, params)
        return {
            "message": "更新成功",
            "customer_id": customer_id,
            "updated_fields": update_fields
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫更新失敗")

# 得到類別列表
@app.get("/get_category")
def get_categories():
    print("[API] get_categories 被呼叫")
    try:
        df = get_data_from_db('SELECT DISTINCT category FROM product_master WHERE category IS NOT NULL ORDER BY category')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_categories: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到子類別列表
@app.get("/get_subcategory")
def get_subcategories():
    print("[API] get_subcategories 被呼叫")
    try:
        df = get_data_from_db('SELECT DISTINCT subcategory FROM product_master WHERE subcategory IS NOT NULL ORDER BY subcategory')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_subcategories: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到品項列表
@app.get("/get_name_zh")
def get_product_names():
    print("[API] get_product_names 被呼叫")
    try:
        df = get_data_from_db('SELECT DISTINCT name_zh FROM product_master WHERE name_zh IS NOT NULL ORDER BY name_zh')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_product_names: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")