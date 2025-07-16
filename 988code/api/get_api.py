from fastapi import APIRouter, HTTPException
import psycopg2
import pandas as pd

router = APIRouter()

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

# 得到所有新進訂單
@router.get("/get_new_orders")
def get_new_orders():
    print("[API] get_new_orders 被呼叫")
    try:
        df = get_data_from_db('SELECT * FROM temp_customer_records')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_new_orders: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到新品購買訂單
@router.get("/get_new_item_orders")
def get_new_orders():
    print("[API] get_new_orders 被呼叫")
    try:
        df = get_data_from_db('SELECT customer_id, customer_name, purchase_record, created_at FROM temp_customer_records WHERE is_new_product = true')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_new_orders: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 客戶資料管理列表資料
@router.get("/get_customer_data")
def get_customer_data():
    print("[API] get_customer_data 被呼叫")
    try:
        query = """
        SELECT c.customer_id, c.customer_name, c.phone_number, c.address, c.delivery_schedule,
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
@router.get("/get_restock_data")
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

# 得到商品類別列表
@router.get("/get_category")
def get_categories():
    print("[API] get_categories 被呼叫")
    try:
        query = """
        SELECT DISTINCT category 
        FROM product_master 
        WHERE category IS NOT NULL 
        AND category IN (
            SELECT DISTINCT category 
            FROM product_master 
            WHERE is_active = 'active'
        ) 
        ORDER BY category
        """
        df = get_data_from_db(query)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_categories: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到商品子類別列表
@router.get("/get_subcategory")
def get_subcategories():
    print("[API] get_subcategories 被呼叫")
    try:
        query = """
        SELECT DISTINCT subcategory 
        FROM product_master 
        WHERE subcategory IS NOT NULL 
        AND subcategory IN (
            SELECT DISTINCT subcategory 
            FROM product_master 
            WHERE is_active = 'active'
        ) 
        ORDER BY subcategory
        """
        df = get_data_from_db(query)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_subcategories: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到商品品項列表
@router.get("/get_name_zh")
def get_product_names():
    print("[API] get_product_names 被呼叫")
    try:
        df = get_data_from_db('SELECT DISTINCT name_zh FROM product_master WHERE name_zh IS NOT NULL AND status = \'active\' ORDER BY name_zh')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_product_names: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 得到新產品資料
@router.get("/get_buy_new_items")
def get_new_products():
    print("[API] get_new_products 被呼叫")
    try:
        df = get_data_from_db('SELECT * FROM temp_customer_records WHERE is_new_product = true')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_new_products: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 得到商品庫存類別
# TODO 缺總庫存量
@router.get("/get_inventory_data")
def get_inventory_data():                                                                       
    print("[API] get_inventory_data 被呼叫")
    try:
        query = """
        SELECT pm.category,
            pm.subcategory,
            COALESCE(SUM(inv.stock_quantity), 0) as total_stock_quantity,
            pm.updated_at
        FROM product_master pm
        LEFT JOIN inventory inv ON pm.product_id = inv.product_id 
                            AND pm.warehouse_id = inv.warehouse_id
        WHERE pm.is_active = 'active'
        GROUP BY pm.category, pm.subcategory, pm.updated_at
        ORDER BY pm.category, pm.subcategory;
        """
        print("[DEBUG] SQL 查詢開始")
        df = get_data_from_db(query)
        print("[DEBUG] SQL 查詢成功，資料筆數:", len(df))
        return df.to_dict(orient="records")
    except Exception as e:
        import traceback
        print(f"[API ERROR] get_inventory_data: {e}")
        traceback.print_exc()  # 印出完整 traceback
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到客戶ID列表
@router.get("/get_customer_ids")
def get_customer_ids():
    print("[API] get_customer_ids 被呼叫")
    try:
        df = get_data_from_db('SELECT customer_id FROM customer ORDER BY customer_id')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_customer_ids: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到客戶名稱列表
@router.get("/get_customer_names")
def get_customer_names():
    print("[API] get_customer_names 被呼叫")
    try:
        df = get_data_from_db('SELECT customer_name FROM customer ORDER BY customer_name')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_customer_names: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
@router.get("/get_repurchase_data")
def get_repurchase_data():
    print("[API] get_repurchase_reminders 被呼叫")
    try:
        df = get_data_from_db('SELECT id, reminder_sent, customer_id, customer_name, product_name, last_purchase_date, days_since_purchase, repurchase_note FROM repurchase_reminders')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_repurchase_reminders: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到不活躍客戶資料
@router.get("/get_inactive_customers")
def get_inactive_customers():
    print("[API] get_inactive_customers 被呼叫")
    try:
        query = """
        SELECT customer_name, inactive_days, last_order_date, last_product, 
               processed, processed_at, processed_by
        FROM inactive_customers
        ORDER BY inactive_days DESC
        """
        df = get_data_from_db(query)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_inactive_customers: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")