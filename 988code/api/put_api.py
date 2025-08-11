from fastapi import APIRouter, HTTPException, UploadFile, File
import psycopg2
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import base64
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image

router = APIRouter(prefix="/put")

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

def query_data_from_db(sql_prompt: str, params: tuple = ()):
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
                return cursor.fetchall()
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
    
@router.put("/update_repurchase_reminder/{id}")
def update_reminder_sent(id: int):
    sql = "UPDATE repurchase_reminders SET reminder_sent = %s WHERE id = %s"
    params = (True, id)

    try:
        update_data_to_db(sql, params)
        return {
            "message": "提醒狀態更新成功",
            "id": id,
            "reminder_sent": True
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫更新失敗")
    
# 更新repurchase_note
class RepurchaseNoteUpdate(BaseModel):
    repurchase_note: str

@router.put("/update_repurchase_note/{id}")
def update_repurchase_note(id: int, update_data: RepurchaseNoteUpdate):
    sql = "UPDATE repurchase_reminders SET repurchase_note = %s WHERE id = %s"
    params = (update_data.repurchase_note, id)

    try:
        update_data_to_db(sql, params)
        return {
            "message": "回購備註更新成功",
            "id": id,
            "repurchase_note": update_data.repurchase_note
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="資料庫更新失敗")

# RAG 知識庫處理
def convert_file_to_pdf(file_content: bytes, filename: str) -> bytes:
    """將不同格式的檔案轉換為A4直向的PDF"""
    try:
        file_extension = filename.lower().split('.')[-1]
        
        # 如果已經是PDF，檢查並調整格式
        if file_extension == 'pdf':
            # 使用PyMuPDF處理PDF
            doc = fitz.open(stream=file_content, filetype="pdf")
            output_doc = fitz.open()
            
            for page in doc:
                # 創建A4大小的新頁面 (595, 842)
                new_page = output_doc.new_page(width=595, height=842)
                
                # 獲取原頁面內容
                page_rect = page.rect
                target_rect = fitz.Rect(0, 0, 595, 842)
                
                # 計算縮放比例，保持長寬比
                scale_x = target_rect.width / page_rect.width
                scale_y = target_rect.height / page_rect.height
                scale = min(scale_x, scale_y)
                
                # 計算居中位置
                scaled_width = page_rect.width * scale
                scaled_height = page_rect.height * scale
                x_offset = (target_rect.width - scaled_width) / 2
                y_offset = (target_rect.height - scaled_height) / 2
                
                # 設置變換矩陣
                mat = fitz.Matrix(scale, scale).pretranslate(x_offset, y_offset)
                new_page.show_pdf_page(target_rect, doc, page.number, mat)
            
            doc.close()
            return output_doc.tobytes()
        
        # 處理Excel檔案
        elif file_extension in ['xls', 'xlsx']:
            # 讀取Excel檔案
            df = pd.read_excel(io.BytesIO(file_content))
            
            # 創建PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # 添加標題
            title = Paragraph(f"<b>{filename}</b>", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # 轉換DataFrame為文字內容
            content_text = df.to_string(index=False)
            # 分行處理，避免單行過長
            lines = content_text.split('\n')
            for line in lines[:50]:  # 限制行數避免檔案過大
                if line.strip():
                    para = Paragraph(line, styles['Normal'])
                    story.append(para)
            
            doc.build(story)
            return buffer.getvalue()
        
        # 處理Word檔案 (簡化處理)
        elif file_extension in ['doc', 'docx']:
            # 創建簡單的PDF，顯示檔案名稱
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            title = Paragraph(f"<b>{filename}</b>", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.5*inch))
            
            content = Paragraph("Word檔案內容已上傳，請使用專門的文件檢視器開啟。", styles['Normal'])
            story.append(content)
            
            doc.build(story)
            return buffer.getvalue()
        
        else:
            raise HTTPException(status_code=400, detail=f"不支援的檔案格式: {file_extension}")
            
    except Exception as e:
        print(f"[ERROR] 檔案轉換失敗: {e}")
        raise HTTPException(status_code=500, detail="檔案轉換失敗")

class RAGKnowledgeBase(BaseModel):
    title: str
    text_content: Optional[str] = None
    files: Optional[List[dict]] = None  # 包含檔名和base64內容
    delete_file_index: Optional[int] = None  # 要刪除的檔案索引

@router.put("/rag/save_knowledge")
def save_rag_knowledge(knowledge_data: RAGKnowledgeBase):
    """儲存RAG知識庫內容，包含文字和檔案"""
    try:
        # 準備PDF檔案數據
        pdf_files = []
        
        if knowledge_data.files:
            for file_info in knowledge_data.files:
                filename = file_info.get('filename')
                file_content = base64.b64decode(file_info.get('content', ''))
                
                # 轉換為A4 PDF
                pdf_content = convert_file_to_pdf(file_content, filename)
                pdf_files.append({
                    'filename': filename,
                    'pdf_content': pdf_content
                })
        
        # 檢查是否已存在該標題的記錄
        check_sql = "SELECT COUNT(*) FROM rag WHERE title = %s"
        result = query_data_from_db(check_sql, (knowledge_data.title,))
        exists = result[0][0] > 0
        
        if exists:
            # 更新現有記錄
            if knowledge_data.delete_file_index is not None:
                # 刪除指定索引的檔案
                get_existing_sql = "SELECT file_content, file_name FROM rag WHERE title = %s"
                existing_data = query_data_from_db(get_existing_sql, (knowledge_data.title,))
                
                if existing_data and existing_data[0]:
                    existing_file_content = list(existing_data[0][0]) if existing_data[0][0] else []
                    existing_file_names = list(existing_data[0][1]) if existing_data[0][1] else []
                    
                    # 刪除指定索引的檔案
                    if 0 <= knowledge_data.delete_file_index < len(existing_file_names):
                        del existing_file_content[knowledge_data.delete_file_index]
                        del existing_file_names[knowledge_data.delete_file_index]
                        
                        sql = """
                        UPDATE rag 
                        SET text_content = %s, file_content = %s, file_name = %s
                        WHERE title = %s
                        """
                        params = (
                            [knowledge_data.text_content] if knowledge_data.text_content else [],
                            existing_file_content,
                            existing_file_names,
                            knowledge_data.title
                        )
                        update_data_to_db(sql, params)
            elif pdf_files:
                # 先獲取現有的檔案內容
                get_existing_sql = "SELECT file_content, file_name FROM rag WHERE title = %s"
                existing_data = query_data_from_db(get_existing_sql, (knowledge_data.title,))
                
                existing_file_content = existing_data[0][0] if existing_data and existing_data[0][0] else []
                existing_file_names = existing_data[0][1] if existing_data and existing_data[0][1] else []
                
                # 累積新檔案到現有檔案中
                new_file_content = list(existing_file_content) if existing_file_content else []
                new_file_names = list(existing_file_names) if existing_file_names else []
                
                for file_info in pdf_files:
                    # 檢查是否已經存在相同檔名，如果存在就跳過
                    if file_info['filename'] not in new_file_names:
                        new_file_content.append(file_info['pdf_content'].hex())
                        new_file_names.append(file_info['filename'])
                
                sql = """
                UPDATE rag 
                SET text_content = %s, file_content = %s, file_name = %s
                WHERE title = %s
                """
                params = (
                    [knowledge_data.text_content] if knowledge_data.text_content else [],
                    new_file_content,
                    new_file_names,
                    knowledge_data.title
                )
                update_data_to_db(sql, params)
            elif knowledge_data.files is None:
                # 如果files明確為None，清除檔案內容
                sql = """
                UPDATE rag 
                SET text_content = %s, file_content = NULL, file_name = NULL
                WHERE title = %s
                """
                params = ([knowledge_data.text_content] if knowledge_data.text_content else [], knowledge_data.title)
                update_data_to_db(sql, params)
            else:
                # 只更新文字內容，不動檔案
                sql = """
                UPDATE rag 
                SET text_content = %s
                WHERE title = %s
                """
                params = ([knowledge_data.text_content] if knowledge_data.text_content else [], knowledge_data.title)
                update_data_to_db(sql, params)
        else:
            # 新增記錄
            if pdf_files:
                # 儲存所有檔案到陣列中
                file_contents = []
                file_names = []
                
                for file_info in pdf_files:
                    file_contents.append(file_info['pdf_content'].hex())
                    file_names.append(file_info['filename'])
                
                sql = """
                INSERT INTO rag (title, text_content, file_content, file_name)
                VALUES (%s, %s, %s, %s)
                """
                params = (
                    knowledge_data.title,
                    [knowledge_data.text_content] if knowledge_data.text_content else [],
                    file_contents,
                    file_names
                )
                update_data_to_db(sql, params)
            else:
                # 只有文字內容的記錄
                sql = """
                INSERT INTO rag (title, text_content)
                VALUES (%s, %s)
                """
                params = (
                    knowledge_data.title,
                    [knowledge_data.text_content] if knowledge_data.text_content else []
                )
                update_data_to_db(sql, params)
        
        return {
            "message": "知識庫儲存成功",
            "title": knowledge_data.title,
            "files_processed": len(pdf_files) if pdf_files else 0
        }
        
    except Exception as e:
        print(f"[ERROR] RAG儲存失敗: {e}")
        raise HTTPException(status_code=500, detail=f"知識庫儲存失敗: {str(e)}")

@router.put("/rag/delete_knowledge/{title}")
def delete_rag_knowledge(title: str):
    """刪除RAG知識庫條目"""
    try:
        sql = "DELETE FROM rag WHERE title = %s"
        params = (title,)
        
        update_data_to_db(sql, params)
        
        return {
            "message": "知識庫條目刪除成功",
            "title": title
        }
        
    except Exception as e:
        print(f"[ERROR] RAG刪除失敗: {e}")
        raise HTTPException(status_code=500, detail="知識庫條目刪除失敗")

class RAGTitleUpdate(BaseModel):
    old_title: str
    new_title: str

@router.put("/rag/update_title")
def update_rag_title(update_data: RAGTitleUpdate):
    """更新RAG知識庫條目標題"""
    try:
        # 檢查新標題是否已存在
        check_sql = "SELECT COUNT(*) FROM rag WHERE title = %s AND title != %s"
        result = query_data_from_db(check_sql, (update_data.new_title, update_data.old_title))
        
        if result[0][0] > 0:
            raise HTTPException(status_code=400, detail="新標題已存在，請使用其他標題")
        
        # 更新標題
        sql = "UPDATE rag SET title = %s WHERE title = %s"
        params = (update_data.new_title, update_data.old_title)
        
        update_data_to_db(sql, params)
        
        return {
            "message": "標題更新成功",
            "old_title": update_data.old_title,
            "new_title": update_data.new_title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] RAG標題更新失敗: {e}")
        raise HTTPException(status_code=500, detail="標題更新失敗")