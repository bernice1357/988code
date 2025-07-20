from fastapi import APIRouter, HTTPException, Form
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

# 得到滯銷品分析資料
@router.get("/get_sales_change_data")
def get_sales_change_data():
    print("[API] get_sales_change_data 被呼叫")
    try:
        query = """
        SELECT 
            sct.product_id,
            COALESCE(pm.name_zh, '未知商品') as product_name,
            COALESCE(sct.last_month_sales, 0) as last_month_sales,
            COALESCE(sct.current_month_sales, 0) as current_month_sales,
            COALESCE(sct.change_percentage, 0) as change_percentage,
            COALESCE(sct.stock_quantity, 0) as stock_quantity,
            COALESCE(c1.customer_name, NULL) as recommended_customer_1,
            COALESCE(c1.phone_number, NULL) as recommended_customer_1_phone,
            COALESCE(c2.customer_name, NULL) as recommended_customer_2,
            COALESCE(c2.phone_number, NULL) as recommended_customer_2_phone,
            COALESCE(c3.customer_name, NULL) as recommended_customer_3,
            COALESCE(c3.phone_number, NULL) as recommended_customer_3_phone,
            COALESCE(sct.status, false) as status
        FROM sales_change_table sct
        LEFT JOIN product_master pm ON sct.product_id = pm.product_id
        LEFT JOIN customer c1 ON sct.recommended_customer_id_rank1 = c1.customer_id
        LEFT JOIN customer c2 ON sct.recommended_customer_id_rank2 = c2.customer_id
        LEFT JOIN customer c3 ON sct.recommended_customer_id_rank3 = c3.customer_id
        ORDER BY sct.change_percentage ASC
        """
        df = get_data_from_db(query)
        
        # 在後端也處理一下 NULL 值
        result = df.to_dict(orient="records")
        print(f"[API] 返回 {len(result)} 筆資料")
        if result:
            print(f"[API] 第一筆資料: {result[0]}")
        
        return result
        
    except Exception as e:
        print(f"[API ERROR] get_sales_change_data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 登入驗證
@router.post("/login")
def login(username: str, password: str):
    print(f"[API] login 被呼叫，使用者: {username}")
    try:
        query = """
        SELECT username, email, password_hash, full_name, role, is_active
        FROM users 
        WHERE username = %s AND is_active = true
        """
        
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username,))
                user_data = cursor.fetchone()
                
                if user_data:
                    columns = [desc[0] for desc in cursor.description]
                    user_dict = dict(zip(columns, user_data))
                    
                    # 這裡應該要驗證密碼hash，暫時簡化處理
                    # 實際應用中需要使用 bcrypt 或其他加密方式驗證
                    if password == "password":  # 簡化的密碼驗證
                        return {
                            "success": True,
                            "user": {
                                "username": user_dict["username"],
                                "email": user_dict["email"],
                                "full_name": user_dict["full_name"],
                                "role": user_dict["role"]
                            }
                        }
                    else:
                        return {"success": False, "message": "密碼錯誤"}
                else:
                    return {"success": False, "message": "使用者不存在"}
                    
    except Exception as e:
        print(f"[API ERROR] login: {e}")
        raise HTTPException(status_code=500, detail="登入驗證失敗")

# 獲取使用者資料
@router.get("/get_user/{username}")
def get_user(username: str):
    print(f"[API] get_user 被呼叫，使用者: {username}")
    try:
        query = """
        SELECT username, email, full_name, role, is_active
        FROM users 
        WHERE username = %s
        """
        df = get_data_from_db(query % f"'{username}'")
        if not df.empty:
            return df.iloc[0].to_dict()
        else:
            raise HTTPException(status_code=404, detail="使用者不存在")
    except Exception as e:
        print(f"[API ERROR] get_user: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 註冊新使用者
@router.post("/register")
def register(request: dict):
    print(f"[API] register 被呼叫，使用者: {request.get('username')}")
    try:
        username = request.get('username')
        email = request.get('email')
        full_name = request.get('full_name')
        password = request.get('password')
        role = request.get('role', 'user')
        
        # 檢查使用者是否已存在
        check_query = """
        SELECT username, email FROM users 
        WHERE username = %s OR email = %s
        """
        
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(check_query, (username, email))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    return {"success": False, "message": "使用者名稱或電子郵件已存在"}
                
                # 插入新使用者（這裡簡化密碼處理，實際應用中需要加密）
                insert_query = """
                INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                # 實際應用中應該使用 bcrypt 加密密碼
                password_hash = password  # 簡化處理
                
                cursor.execute(insert_query, (username, email, password_hash, full_name, role, True))
                conn.commit()
                
                return {"success": True, "message": "註冊成功"}
                
    except Exception as e:
        print(f"[API ERROR] register: {e}")
        raise HTTPException(status_code=500, detail="註冊失敗")
    
# 得到商品推薦列表
@router.get("/get_recommended_product_ids")
def get_product_recommendations():
    print("[API] get_product_recommendations 被呼叫")
    try:
        query = """
        SELECT pcr.product_id, pm.name_zh
        FROM product_customer_recommendations pcr
        LEFT JOIN product_master pm ON pcr.product_id = pm.product_id
        """
        df = get_data_from_db(query)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_product_recommendations: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")