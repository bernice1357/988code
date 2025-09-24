from fastapi import APIRouter, HTTPException
import psycopg2
import pandas as pd
from typing import Optional

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

# 得到特定客戶的所有交易日期 (畫補貨時間軸用的)
@router.get("/get_restock_history/{customer_id}")
def get_customer_transactions(customer_id: str, product_id: Optional[str] = None):
    try:
        filters = ["customer_id = %s"]
        params = [customer_id]
        if product_id:
            filters.append("LOWER(COALESCE(product_id::text, '')) = LOWER(%s)")
            params.append(product_id.strip())
        query = (
            "SELECT transaction_date, product_id, product_name, quantity\n"
            "FROM order_transactions \n"
            f"WHERE {' AND '.join(filters)}\n"
            "ORDER BY transaction_date ASC"
        )
        df = get_data_from_db_with_params(query, tuple(params))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 透過
@router.get("/get_recommendation_purchase_history/{customer_id}")
def get_customer_transactions(customer_id: str):
    try:
        query = """
        WITH net_transactions AS (
            SELECT 
                product_name,
                transaction_date,
                SUM(quantity) as net_quantity,
                -- 保留原始交易類型信息
                STRING_AGG(DISTINCT document_type, ',') as doc_types
            FROM order_transactions 
            WHERE customer_id = %s
            GROUP BY product_name, transaction_date
        )
        SELECT 
            product_name,
            net_quantity as quantity,
            transaction_date,
            CASE 
                WHEN net_quantity > 0 THEN '銷貨'
                WHEN net_quantity < 0 THEN '銷退'
                ELSE '抵銷'
            END as document_type
        FROM net_transactions
        WHERE net_quantity != 0  -- 只顯示非零的淨交易
        ORDER BY transaction_date DESC
        """
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
        query = "SELECT DISTINCT subcategory FROM product_master WHERE category = %s AND is_active = 'active'"
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
    
# 取得超過指定天數的補貨提醒
@router.get("/get_repurchase_reminders/{days}")
def get_repurchase_reminders(days: int):
    try:
        query = "SELECT id, reminder_sent, customer_id, customer_name, product_name, last_purchase_date, days_since_purchase, repurchase_note FROM repurchase_reminders WHERE days_since_purchase >= %s"
        df = get_data_from_db_with_params(query, (days,))
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 取得客戶商品推薦
@router.get("/get_customer_recommendations/{customer_id}")
def get_customer_recommendations(customer_id: str):
    try:
        query = """
        SELECT 
            cpr.recommended_product_id_rank1,
            cpr.recommended_product_id_rank2,
            cpr.recommended_product_id_rank3,
            pm1.name_zh as recommended_product_name_rank1,
            pm2.name_zh as recommended_product_name_rank2,
            pm3.name_zh as recommended_product_name_rank3
        FROM customer_product_recommendations cpr
        LEFT JOIN product_master pm1 ON cpr.recommended_product_id_rank1 = pm1.product_id
        LEFT JOIN product_master pm2 ON cpr.recommended_product_id_rank2 = pm2.product_id
        LEFT JOIN product_master pm3 ON cpr.recommended_product_id_rank3 = pm3.product_id
        WHERE cpr.customer_id = %s
        """
        df = get_data_from_db_with_params(query, (customer_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 取得客戶每月消費金額統計
@router.get("/get_customer_monthly_spending/{customer_id}")
def get_customer_monthly_spending(customer_id: str):
    try:
        query = """
        SELECT 
            TO_CHAR(DATE_TRUNC('month', transaction_date), 'YYYY-MM') as month,
            SUM(amount) as total_amount
        FROM order_transactions 
        WHERE customer_id = %s 
        GROUP BY DATE_TRUNC('month', transaction_date)
        ORDER BY DATE_TRUNC('month', transaction_date) ASC
        """
        df = get_data_from_db_with_params(query, (customer_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據 product_id 取得推薦的客戶
@router.get("/get_product_recommendations/{product_id}")
def get_product_recommendations(product_id: str):
    try:
        query = """
        SELECT 
            pcr.recommended_customer_id_rank1,
            pcr.recommended_customer_id_rank2,
            pcr.recommended_customer_id_rank3,
            c1.customer_name as recommended_customer_name_rank1,
            c2.customer_name as recommended_customer_name_rank2,
            c3.customer_name as recommended_customer_name_rank3
        FROM product_customer_recommendations pcr
        LEFT JOIN customer c1 ON pcr.recommended_customer_id_rank1 = c1.customer_id
        LEFT JOIN customer c2 ON pcr.recommended_customer_id_rank2 = c2.customer_id
        LEFT JOIN customer c3 ON pcr.recommended_customer_id_rank3 = c3.customer_id
        WHERE pcr.product_id = %s
        """
        df = get_data_from_db_with_params(query, (product_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 根據 customer_id 取得客戶購買過的產品（不重複）
@router.get("/get_recommended_customer_history/{customer_id}")
def get_recommended_customer_history(customer_id: str):
    try:
        query = """
        SELECT 
            product_id,
            product_name,
            MIN(transaction_date) as earliest_purchase_date,
            MAX(transaction_date) as latest_purchase_date,
            COUNT(*) as purchase_count
        FROM order_transactions 
        WHERE customer_id = %s
        GROUP BY product_id, product_name
        ORDER BY product_id
        """
        df = get_data_from_db_with_params(query, (customer_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據下降比例篩選滯銷品資料
@router.get("/get_sales_change_data_by_threshold/{threshold}")
def get_sales_change_data_by_threshold(threshold: float):
    print(f"[API] get_sales_change_data_by_threshold 被呼叫，閾值：{threshold}")
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
        WHERE ABS(sct.change_percentage) >= %s
        ORDER BY sct.change_percentage ASC
        """
        df = get_data_from_db_with_params(query, (threshold,))
        
        # 在後端也處理一下 NULL 值
        result = df.to_dict(orient="records")
        print(f"[API] 返回 {len(result)} 筆資料")
        if result:
            print(f"[API] 第一筆資料: {result[0]}")
        
        return result
        
    except Exception as e:
        print(f"[API ERROR] get_sales_change_data_by_threshold: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 根據客戶ID獲取配送計劃
@router.get("/get_delivery_schedule_by_customer/{customer_id}")
def get_delivery_schedule_by_customer(customer_id: str):
    try:
        query = """
        SELECT customer_id, customer_name, product_name, status, quantity, 
               delivery_date, created_at, updated_at
        FROM delivery_schedule
        WHERE customer_id = %s
        ORDER BY delivery_date DESC
        """
        df = get_data_from_db_with_params(query, (customer_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據產品名稱獲取配送計劃
@router.get("/get_delivery_schedule_by_product/{product_name}")
def get_delivery_schedule_by_product(product_name: str):
    try:
        query = """
        SELECT customer_id, customer_name, product_name, status, quantity, 
               delivery_date, created_at, updated_at
        FROM delivery_schedule
        WHERE product_name = %s
        ORDER BY delivery_date DESC, customer_id
        """
        df = get_data_from_db_with_params(query, (product_name,))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據狀態獲取配送計劃
@router.get("/get_delivery_schedule_by_status/{status}")
def get_delivery_schedule_by_status(status: str):
    try:
        query = """
        SELECT customer_id, customer_name, product_name, status, quantity, 
               delivery_date, created_at, updated_at
        FROM delivery_schedule
        WHERE status = %s
        ORDER BY delivery_date DESC, customer_id
        """
        df = get_data_from_db_with_params(query, (status,))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 獲取指定日期範圍的配送計劃
@router.get("/get_delivery_schedule_by_date_range/{start_date}/{end_date}")
def get_delivery_schedule_by_date_range(start_date: str, end_date: str):
    try:
        query = """
        SELECT customer_id, customer_name, product_name, status, quantity, 
               delivery_date, created_at, updated_at
        FROM delivery_schedule
        WHERE DATE(delivery_date) BETWEEN %s AND %s
        ORDER BY delivery_date ASC, customer_id
        """
        df = get_data_from_db_with_params(query, (start_date, end_date))
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 檢查客戶是否存在
@router.get("/check_customer_exists/{customer_id}")
def check_customer_exists(customer_id: str):
    print(f"[API] check_customer_exists 被呼叫，客戶ID: {customer_id}")
    try:
        query = "SELECT COUNT(*) as count FROM customer WHERE customer_id = %s"
        df = get_data_from_db_with_params(query, (customer_id,))
        exists = df.iloc[0]['count'] > 0 if not df.empty else False
        return {"exists": exists}
    except Exception as e:
        print(f"[API ERROR] check_customer_exists: {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")
    
# 根據 customer_id 獲取對應的 line_id
@router.get("/get_line_id_by_customer/{customer_id}")
def get_line_id_by_customer(customer_id: str):
    try:
        query = "SELECT line_id, created_date, notes FROM customer_line_mapping WHERE customer_id = %s"
        df = get_data_from_db_with_params(query, (customer_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

# 根據 line_id 獲取對應的 customer_id
@router.get("/get_customer_id_by_line/{line_id}")
def get_customer_id_by_line(line_id: str):
    try:
        query = "SELECT customer_id, created_date, notes FROM customer_line_mapping WHERE line_id = %s"
        df = get_data_from_db_with_params(query, (line_id,))
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫查詢失敗")

