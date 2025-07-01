# uvicorn api_server:app --reload

from fastapi import FastAPI, HTTPException
import psycopg2
import pandas as pd
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI()

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

@app.get("/get_new_orders")
def get_new_orders():
    print("[API] get_new_orders 被呼叫")
    try:
        df = get_data_from_db('SELECT * FROM temp_customer_records')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_new_orders: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

@app.get("/get_customer_data")
def get_customer_data():
    print("[API] get_customer_data 被呼叫")
    try:
        df = get_data_from_db('SELECT customer_id, customer_name, address, updated_date, notes FROM customer')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_customer_data: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

class RecordUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    purchase_record: Optional[str] = None
    updated_at: Optional[datetime] = None
    status: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None

@app.put("/customer/{id}")
def update_customer(id: int, update_data: RecordUpdate):
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