from fastapi import APIRouter, HTTPException, Form, Query
import psycopg2
import pandas as pd
from datetime import datetime

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
    try:
        df = get_data_from_db('SELECT * FROM temp_customer_records')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_new_orders: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到新品購買訂單
@router.get("/get_new_item_orders")
def get_new_item_orders():
    try:
        df = get_data_from_db('SELECT customer_id, customer_name, purchase_record, created_at FROM temp_customer_records WHERE is_new_product = true')
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_new_orders: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
@router.get("/get_new_item_customers")
def get_new_item_customers():
    try:
        df = get_data_from_db('SELECT customer_id FROM temp_customer_records WHERE is_new_product = true')
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
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 補貨提醒 - 取得所有客戶ID
@router.get("/get_restock_customer_ids")
def get_all_customer_ids():
    try:
        query = "SELECT DISTINCT customer_id FROM prophet_predictions"
        df = get_data_from_db(query)
        customer_ids = df['customer_id'].tolist()
        return {"customer_ids": customer_ids}
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到客戶最新補貨紀錄
# TODO 還沒放預計補貨日期欄位
@router.get("/get_restock_data")
def get_customer_latest_transactions():
    print("[API] get_customer_latest_transactions 被呼叫")
    try:
        query = """
        SELECT pp.customer_id, c.customer_name, c.phone_number, pp.product_id, pp.product_name, 
               pp.prediction_date, pp.estimated_quantity, pp.confidence_level
        FROM prophet_predictions pp
        LEFT JOIN customer c ON pp.customer_id = c.customer_id
        ORDER BY pp.customer_id, pp.prediction_date
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
        df = get_data_from_db('SELECT DISTINCT name_zh FROM product_master WHERE name_zh IS NOT NULL AND is_active = \'active\' ORDER BY name_zh')
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
        df = get_data_from_db(query)
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

# 獲取RAG知識庫條目列表
@router.get("/get_rag_titles")
def get_rag_titles():
    try:
        query = "SELECT title FROM rag"
        df = get_data_from_db(query)
        result = df.to_dict(orient="records")
        return result
    except Exception as e:
        print(f"[API ERROR] get_rag_titles: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 獲取指定RAG條目的內容
@router.get("/get_rag_content/{title}")
def get_rag_content(title: str):
    try:
        query = "SELECT title, text_content, file_content, file_name FROM rag WHERE title = %s"
        
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (title,))
                result = cursor.fetchone()
                if result:
                    
                    file_names_list = []
                    if result[3] and len(result[3]) > 0:
                        file_names_list = result[3]
                    
                    return {
                        "title": result[0],
                        "text_content": result[1][0] if result[1] and len(result[1]) > 0 else "",
                        "has_file": result[2] is not None and len(result[2]) > 0,
                        "file_names": file_names_list
                    }
                else:
                    return {
                        "title": title,
                        "text_content": "",
                        "has_file": False,
                        "file_names": []
                    }
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 得到每月銷量預測資料
@router.get("/get_monthly_sales_predictions")
def get_monthly_sales_predictions():
    print("[API] get_monthly_sales_predictions 被呼叫")
    try:
        query = """
        SELECT 
            product_id,
            product_name,
            subcategory,
            prediction_level,
            prediction_value,
            volatility_group,
            month_minus_3,
            month_minus_2,
            month_minus_1,
            cv_value,
            allocation_ratio,
            prediction_method,
            batch_id,
            created_at,
            updated_at
        FROM monthly_sales_predictions
        ORDER BY subcategory, product_id
        """
        df = get_data_from_db(query)
        result = df.to_dict(orient="records")
        print(f"[API] 返回 {len(result)} 筆資料")
        if result:
            print(f"[API] 第一筆資料: {result[0]}")
        return result
    except Exception as e:
        print(f"[API ERROR] get_monthly_sales_predictions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 獲取每日配送預測資料 - 適配現有表結構
@router.get("/get_delivery_schedule")
def get_delivery_schedule():
    print("[API] get_delivery_schedule 被呼叫")
    try:
        query = """
        SELECT ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
               ds.created_at, ds.updated_at, ds.scheduled_at,
               COALESCE(ot.customer_id, 'N/A') as customer_id,
               COALESCE(ot.customer_name, '未知客戶') as customer_name,
               COALESCE(ot.product_name, '未知產品') as product_name
        FROM delivery_schedule ds
        LEFT JOIN order_transactions ot ON ds.source_order_id::text = ot.id::text
        ORDER BY ds.delivery_date DESC, ds.id
        """
        df = get_data_from_db(query)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_delivery_schedule: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據日期篩選配送預測 - 適配現有表結構
@router.get("/get_delivery_schedule_by_date/{delivery_date}")
def get_delivery_schedule_by_date(delivery_date: str):
    print(f"[API] get_delivery_schedule_by_date 被呼叫，日期：{delivery_date}")
    try:
        query = """
        SELECT ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
               ds.created_at, ds.updated_at, ds.scheduled_at,
               COALESCE(ot.customer_id, 'N/A') as customer_id,
               COALESCE(ot.customer_name, '未知客戶') as customer_name,
               COALESCE(ot.product_name, '未知產品') as product_name
        FROM delivery_schedule ds
        LEFT JOIN order_transactions ot ON ds.source_order_id::text = ot.id::text
        WHERE DATE(ds.delivery_date) = %s
        ORDER BY ds.id
        """
        # 使用參數化查詢
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (delivery_date,))
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)
        
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_delivery_schedule_by_date: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據類別篩選配送預測 - 適配現有表結構
@router.get("/get_delivery_schedule_by_category/{category}")
def get_delivery_schedule_by_category(category: str):
    print(f"[API] get_delivery_schedule_by_category 被呼叫，類別：{category}")
    try:
        if category == "全部類別":
            query = """
            SELECT ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
                   ds.created_at, ds.updated_at, ds.scheduled_at,
                   COALESCE(ot.customer_id, 'N/A') as customer_id,
                   COALESCE(ot.customer_name, '未知客戶') as customer_name,
                   COALESCE(ot.product_name, '未知產品') as product_name,
                   COALESCE(pm.category, '未知類別') as category
            FROM delivery_schedule ds
            LEFT JOIN order_transactions ot ON ds.source_order_id::text = ot.id::text
            LEFT JOIN product_master pm ON ot.product_name = pm.name_zh
            ORDER BY ds.delivery_date DESC, ds.id
            """
            df = get_data_from_db(query)
        else:
            query = """
            SELECT ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
                   ds.created_at, ds.updated_at, ds.scheduled_at,
                   COALESCE(ot.customer_id, 'N/A') as customer_id,
                   COALESCE(ot.customer_name, '未知客戶') as customer_name,
                   COALESCE(ot.product_name, '未知產品') as product_name,
                   pm.category
            FROM delivery_schedule ds
            LEFT JOIN order_transactions ot ON ds.source_order_id::text = ot.id::text
            LEFT JOIN product_master pm ON ot.product_name = pm.name_zh
            WHERE pm.category = %s
            ORDER BY ds.delivery_date DESC, ds.id
            """
            with psycopg2.connect(
                dbname='988',
                user='n8n',
                password='1234',
                host='26.210.160.206',
                port='5433'
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (category,))
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    df = pd.DataFrame(rows, columns=columns)
        
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_delivery_schedule_by_category: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據日期和類別同時篩選 - 適配現有表結構
@router.get("/get_delivery_schedule_filtered")
def get_delivery_schedule_filtered(delivery_date: str = None, category: str = None):
    print(f"[API] get_delivery_schedule_filtered 被呼叫，日期：{delivery_date}，類別：{category}")
    try:
        # 修復後的查詢，簡化 JOIN 邏輯
        base_query = """
        SELECT ds.id, ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
               ds.created_at, ds.updated_at, ds.scheduled_at,
               ds.customer_id,
               ds.customer_name,
               ds.product_name
        FROM delivery_schedule ds
        WHERE 1=1
        """
        
        params = []
        
        if delivery_date:
            base_query += " AND DATE(ds.delivery_date) = %s"
            params.append(delivery_date)
        
        # 如果需要根據類別篩選，需要 JOIN product_master 表
        if category and category != "全部類別":
            base_query = """
            SELECT ds.id, ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
                   ds.created_at, ds.updated_at, ds.scheduled_at,
                   ds.customer_id,
                   ds.customer_name,
                   ds.product_name,
                   pm.category
            FROM delivery_schedule ds
            LEFT JOIN product_master pm ON ds.product_name = pm.name_zh
            WHERE 1=1
            """
            
            if delivery_date:
                base_query += " AND DATE(ds.delivery_date) = %s"
            
            base_query += " AND pm.category = %s"
            params.append(category)
        
        base_query += " ORDER BY ds.delivery_date DESC, ds.id"
        
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(base_query, tuple(params))
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)
        
        print(f"[API] 查詢成功，返回 {len(df)} 筆資料")
        return df.to_dict(orient="records")
        
    except Exception as e:
        print(f"[API ERROR] get_delivery_schedule_filtered: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"資料庫查詢失敗: {str(e)}")


# 同時修復其他相關的 delivery_schedule API 函數

# 獲取每日配送預測資料 - 適配現有表結構
@router.get("/get_delivery_schedule")
def get_delivery_schedule():
    print("[API] get_delivery_schedule 被呼叫")
    try:
        query = """
        SELECT ds.id, ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
               ds.created_at, ds.updated_at, ds.scheduled_at,
               ds.customer_id,
               ds.customer_name,
               ds.product_name
        FROM delivery_schedule ds
        ORDER BY ds.delivery_date DESC, ds.id
        """
        df = get_data_from_db(query)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_delivery_schedule: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據日期篩選配送預測 - 適配現有表結構
@router.get("/get_delivery_schedule_by_date/{delivery_date}")
def get_delivery_schedule_by_date(delivery_date: str):
    print(f"[API] get_delivery_schedule_by_date 被呼叫，日期：{delivery_date}")
    try:
        query = """
        SELECT ds.id, ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
               ds.created_at, ds.updated_at, ds.scheduled_at,
               ds.customer_id,
               ds.customer_name,
               ds.product_name
        FROM delivery_schedule ds
        WHERE DATE(ds.delivery_date) = %s
        ORDER BY ds.id
        """
        # 使用參數化查詢
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (delivery_date,))
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)
        
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_delivery_schedule_by_date: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據類別篩選配送預測 - 適配現有表結構
@router.get("/get_delivery_schedule_by_category/{category}")
def get_delivery_schedule_by_category(category: str):
    print(f"[API] get_delivery_schedule_by_category 被呼叫，類別：{category}")
    try:
        if category == "全部類別":
            query = """
            SELECT ds.id, ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
                   ds.created_at, ds.updated_at, ds.scheduled_at,
                   ds.customer_id,
                   ds.customer_name,
                   ds.product_name,
                   COALESCE(pm.category, '未知類別') as category
            FROM delivery_schedule ds
            LEFT JOIN product_master pm ON ds.product_name = pm.name_zh
            ORDER BY ds.delivery_date DESC, ds.id
            """
            df = get_data_from_db(query)
        else:
            query = """
            SELECT ds.id, ds.delivery_date, ds.amount, ds.status, ds.quantity, ds.source_order_id,
                   ds.created_at, ds.updated_at, ds.scheduled_at,
                   ds.customer_id,
                   ds.customer_name,
                   ds.product_name,
                   pm.category
            FROM delivery_schedule ds
            LEFT JOIN product_master pm ON ds.product_name = pm.name_zh
            WHERE pm.category = %s
            ORDER BY ds.delivery_date DESC, ds.id
            """
            with psycopg2.connect(
                dbname='988',
                user='n8n',
                password='1234',
                host='26.210.160.206',
                port='5433'
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (category,))
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    df = pd.DataFrame(rows, columns=columns)
        
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[API ERROR] get_delivery_schedule_by_category: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到縣市列表
@router.get("/get_county")
def get_counties():
    print("[API] get_counties 被呼叫")
    try:
        query = "SELECT DISTINCT city FROM customer WHERE city IS NOT NULL ORDER BY city"
        df = get_data_from_db(query)
        # 將欄位名稱從 city 改為 county 以符合前端期望
        result = [{"county": row["city"]} for _, row in df.iterrows()]
        return result
    except Exception as e:
        print(f"[API ERROR] get_counties: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 得到地區列表（根據縣市篩選）
@router.get("/get_region")
def get_regions(county: str = Query(..., description="縣市名稱")):
    print(f"[API] get_regions 被呼叫，縣市: {county}")
    try:
        # 使用參數化查詢避免 SQL 注入
        with psycopg2.connect(
            dbname='988',
            user='n8n',
            password='1234',
            host='26.210.160.206',
            port='5433'
        ) as conn:
            with conn.cursor() as cursor:
                query = "SELECT DISTINCT district FROM customer WHERE city = %s AND district IS NOT NULL ORDER BY district"
                cursor.execute(query, (county,))
                rows = cursor.fetchall()
                # 將結果轉換為所需格式
                result = [{"region": row[0]} for row in rows]
                return result
    except Exception as e:
        print(f"[API ERROR] get_regions: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 新增：潛在客戶分析 API 端點
@router.get("/get_potential_customers_analysis/{product_name:path}")
def get_potential_customers_analysis(product_name: str):
    import urllib.parse
    # URL解碼產品名稱以處理特殊字符
    decoded_product_name = urllib.parse.unquote(product_name)
    print(f"[API] get_potential_customers_analysis 被呼叫，產品: {decoded_product_name}")
    try:
        # 導入 potential_customer_finder 模組
        import sys
        import os
        # 當前檔案在 988code/api/get_api.py
        # potential_customer_finder 在 988code/potential_customer_finder/
        api_dir = os.path.dirname(__file__)  # 988code/api
        code_dir = os.path.dirname(api_dir)  # 988code
        potential_finder_path = os.path.join(code_dir, 'potential_customer_finder')
        
        # 添加到路徑開頭，確保優先載入
        if potential_finder_path not in sys.path:
            sys.path.insert(0, potential_finder_path)
        
        print(f"[DEBUG] 添加路徑: {potential_finder_path}")
        print(f"[DEBUG] 路徑存在: {os.path.exists(potential_finder_path)}")
        
        from organized_search_system import organized_complete_search
        
        # 執行完整的潛在客戶搜尋
        result = organized_complete_search(decoded_product_name)
        
        print(f"[API] 潛在客戶分析完成，找到 {result['results_count']} 個結果")
        return result
        
    except Exception as e:
        print(f"[API ERROR] get_potential_customers_analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"潛在客戶分析失敗: {str(e)}")

# 新增：獲取分析進度 API 端點
@router.get("/get_analysis_progress/{task_id}")
def get_analysis_progress(task_id: str = None):
    print(f"[API] get_analysis_progress 被呼叫，任務ID: {task_id}")
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from potential_customer_finder.progress_tracker import progress_tracker
        
        progress_data = progress_tracker.get_progress(task_id)
        
        if progress_data is None:
            return {"status": "not_found", "message": "找不到指定的任務"}
        
        return progress_data
        
    except Exception as e:
        print(f"[API ERROR] get_analysis_progress: {e}")
        raise HTTPException(status_code=500, detail=f"獲取進度失敗: {str(e)}")

# 新增：獲取當前分析進度 API 端點（不需要任務ID）
@router.get("/get_current_analysis_progress")
def get_current_analysis_progress():
    print("[API] get_current_analysis_progress 被呼叫")
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from potential_customer_finder.progress_tracker import progress_tracker
        
        progress_data = progress_tracker.get_progress()
        
        if progress_data is None:
            return {"status": "no_task", "message": "目前沒有正在執行的任務"}
        
        return progress_data
        
    except Exception as e:
        print(f"[API ERROR] get_current_analysis_progress: {e}")
        raise HTTPException(status_code=500, detail=f"獲取進度失敗: {str(e)}")

# 新增：獲取潛在客戶分析詳細結果 API 端點
@router.get("/get_potential_customers_details")
def get_potential_customers_details(product_name: str = Query(..., description="產品名稱")):
    import json
    import os
    from pathlib import Path
    
    # 查詢參數會自動解碼，無需手動處理
    print(f"[API] get_potential_customers_details 被呼叫，產品: {product_name}")
    
    try:
        # 搜尋最新的整合客戶檔案
        results_dir = Path("C:/Users/user/Desktop/988/988code/988code/customer_search_results")
        
        # 尋找所有相關的整合客戶檔案
        integrated_files = []
        for search_dir in results_dir.glob("by_date/search_*"):
            for json_file in search_dir.glob("*integrated_customers.json"):
                # 處理產品名稱中的特殊字符，與文件名格式匹配（與 organized_search_system.py 保持一致）
                processed_name = (product_name
                                 .replace('/', '_')
                                 .replace('\\', '_') 
                                 .replace('*', '_')
                                 .replace('?', '_')
                                 .replace('"', '_')
                                 .replace('<', '_')
                                 .replace('>', '_')
                                 .replace('|', '_')
                                 .replace(':', '_')
                                 .replace('(', '_')
                                 .replace(')', '_')
                                 .replace('[', '_')
                                 .replace(']', '_')
                                 .replace('±', '_')
                                 .replace('%', '_')
                                 .replace(' ', '_'))
                if processed_name in json_file.name:
                    integrated_files.append(json_file)
        
        if not integrated_files:
            # 如果沒有找到整合客戶檔案，可能是結果為 0，返回空結果
            print(f"[API] 未找到整合客戶檔案，可能是搜尋結果為 0")
            return {
                "product_name": product_name,
                "classification_stats": {
                    "total_results": 0,
                    "can_process_count": 0,
                    "purchased_count": 0,
                    "potential_count": 0,
                    "cannot_process_count": 0
                },
                "can_process_customers": [],
                "purchased_customers": [],
                "potential_customers": [],
                "cannot_process_customers": [],
                "results_count": 0,
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        # 選擇最新的檔案
        latest_file = max(integrated_files, key=lambda x: x.stat().st_mtime)
        print(f"[API] 使用整合客戶檔案: {latest_file}")
        
        # 讀取整合客戶結果
        with open(latest_file, 'r', encoding='utf-8') as f:
            integrated_data = json.load(f)
        
        # 整理回傳的資料，使用整合客戶格式
        customers_list = integrated_data.get("customers", [])
        
        # 根據客戶類型分類 (integrated_customers.json 格式)
        can_process_customers = [c for c in customers_list if c.get("customer_type") == "曾詢問客戶"]
        purchased_customers = [c for c in customers_list if c.get("customer_type") == "已購買客戶"]
        potential_customers = [c for c in customers_list if c.get("customer_type") == "潛在需求客戶"]
        # integrated_customers.json 中所有客戶都有customer_id，沒有"無法處理"的分類
        cannot_process_customers = []
        
        result = {
            "product_name": product_name,
            "classification_stats": {
                "total_results": len(customers_list),
                "can_process_count": len(can_process_customers),
                "purchased_count": len(purchased_customers),
                "potential_count": len(potential_customers),
                "cannot_process_count": len(cannot_process_customers)
            },
            "can_process_customers": can_process_customers,
            "purchased_customers": purchased_customers,
            "potential_customers": potential_customers,
            "cannot_process_customers": cannot_process_customers,
            "results_count": len(customers_list),
            "analysis_timestamp": integrated_data.get("analysis_timestamp", "")
        }
        
        print(f"[API] 返回詳細結果，可處理客戶: {len(result['can_process_customers'])} 個")
        return result
        
    except Exception as e:
        print(f"[API ERROR] get_potential_customers_details: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"獲取詳細結果失敗: {str(e)}")