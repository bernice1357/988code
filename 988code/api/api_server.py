# uvicorn api_server:app --reload

from fastapi import FastAPI, HTTPException
import psycopg2
import pandas as pd

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
