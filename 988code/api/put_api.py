from fastapi import APIRouter, HTTPException
import psycopg2
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

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

class RecordUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    purchase_record: Optional[str] = None
    updated_at: Optional[datetime] = None
    status: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None

# 更新暫存訂單
@router.put("/temp/{id}")
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

# 客戶資料管理 - 更新資料
class CustomerUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    delivery_schedule: Optional[str] = None  # 新增此欄位

@router.put("/customer/{customer_id}")
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

# 批量更新subcategory
class ItemSubcategoryUpdate(BaseModel):
    item_id: str
    new_subcategory: str

@router.put("/product_master/update_subcategory")
def update_item_subcategory(update_data: ItemSubcategoryUpdate):
    sql = "UPDATE product_master SET subcategory = %s WHERE product_id = %s"
    params = (update_data.new_subcategory, update_data.item_id)

    try:
        update_data_to_db(sql, params)
        return {
            "message": "品項商品群組更新成功",
            "item_id": update_data.item_id,
            "new_subcategory": update_data.new_subcategory
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫更新失敗")
    

# 不活躍客戶處理狀態更新
class InactiveCustomerUpdate(BaseModel):
    processed: Optional[bool] = None
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None

@router.put("/inactive_customer/{customer_name}")
def update_inactive_customer(customer_name: str, update_data: InactiveCustomerUpdate):
    update_fields = update_data.dict(exclude_none=True)
    
    # 如果沒有提供處理時間，自動設定為當前時間
    if update_fields.get('processed') is True and 'processed_at' not in update_fields:
        update_fields['processed_at'] = datetime.now()
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="沒有提供要更新的欄位")

    set_clause = ", ".join([f"{key} = %s" for key in update_fields])
    sql = f"UPDATE inactive_customers SET {set_clause} WHERE customer_name = %s"
    params = tuple(update_fields.values()) + (customer_name,)

    try:
        update_data_to_db(sql, params)
        return {
            "message": "不活躍客戶狀態更新成功",
            "customer_name": customer_name,
            "updated_fields": update_fields
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫更新失敗")

# 批量更新不活躍客戶處理狀態
class BatchInactiveCustomerUpdate(BaseModel):
    customer_names: list[str]
    processed: bool = True
    processed_by: Optional[str] = None

@router.put("/inactive_customers/batch_update")
def batch_update_inactive_customers(update_data: BatchInactiveCustomerUpdate):
    if not update_data.customer_names:
        raise HTTPException(status_code=400, detail="沒有提供客戶名稱列表")
    
    try:
        success_count = 0
        failed_customers = []
        
        for customer_name in update_data.customer_names:
            try:
                # 準備更新資料
                processed_at = datetime.now() if update_data.processed else None
                
                sql = """
                UPDATE inactive_customers 
                SET processed = %s, processed_by = %s, processed_at = %s 
                WHERE customer_name = %s
                """
                params = (update_data.processed, update_data.processed_by, processed_at, customer_name)
                
                update_data_to_db(sql, params)
                success_count += 1
                
            except Exception as e:
                print(f"[ERROR] 更新客戶 {customer_name} 失敗: {e}")
                failed_customers.append(customer_name)
        
        return {
            "message": f"批量更新完成",
            "success_count": success_count,
            "total_count": len(update_data.customer_names),
            "failed_customers": failed_customers,
            "updated_fields": {
                "processed": update_data.processed,
                "processed_by": update_data.processed_by,
                "processed_at": datetime.now() if update_data.processed else None
            }
        }
        
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="批量更新失敗")