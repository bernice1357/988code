# TODO 要改回ORDER_TRANSACTIONS

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import datetime
import tempfile
import os
import pandas as pd
import random
import string
import openpyxl
from openpyxl import load_workbook
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Dict, Optional, Tuple

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def check_editor_permission(user_role: str):
    """檢查是否有編輯權限"""
    if user_role != 'editor':
        raise HTTPException(status_code=403, detail="權限不足：僅限編輯者使用此功能")

# 備用配置
DEFAULT_CONFIG = {
    'batch_size': 100,
    'timeout': 30
}

class SalesDataUploader:
    def __init__(self):
        """初始化數據上傳器"""
        self.connection = None
        
        # 這個模組專用的表配置
        self.table_config = {
            'order_transactions': 'order_transactions',
            'product_master': 'product_master',
            'customer': 'customer'  # 新增客戶表配置
        }
        
    def connect_database(self):
        """連接數據庫"""
        try:
            # 使用專案的實際資料庫連接參數
            self.connection = psycopg2.connect(
                dbname='988',
                user='n8n',  
                password='1234',
                host='26.210.160.206',
                port='5433',
                connect_timeout=DEFAULT_CONFIG['timeout']
            )
            logger.info("數據庫連接成功")
            return True
        except Exception as e:
            logger.error(f"數據庫連接失敗: {str(e)}")
            return False
    
    def close_connection(self):
        """關閉數據庫連接"""
        if self.connection:
            self.connection.close()
            logger.info("數據庫連接已關閉")
    
    def delete_records_by_months(self, months: set) -> int:
        """
        刪除多個年月的記錄
        
        Args:
            months (set): 包含 (年份, 月份) 元組的集合
            
        Returns:
            int: 刪除的記錄總數
        """
        if not months:
            return 0
            
        total_deleted = 0
        
        try:
            for year, month in months:
                with self.connection.cursor() as cursor:
                    query = f"""
                    DELETE FROM {self.table_config['order_transactions']}
                    WHERE EXTRACT(YEAR FROM transaction_date) = %s 
                      AND EXTRACT(MONTH FROM transaction_date) = %s
                    """
                    cursor.execute(query, (year, month))
                    deleted_count = cursor.rowcount
                    total_deleted += deleted_count
                    
                    logger.info(f"刪除了 {deleted_count} 筆 {year}年{month}月 的記錄")
            
            self.connection.commit()
            logger.info(f"總共刪除了 {total_deleted} 筆記錄")
            return total_deleted
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"刪除月份記錄失敗: {str(e)}")
            raise
    
    def extract_months_from_data(self, data: List[Dict]) -> set:
        """
        從數據中提取所有涉及的年月
        
        Args:
            data (list): 交易記錄列表
            
        Returns:
            set: 包含 (年份, 月份) 元組的集合
        """
        months = set()
        
        for record in data:
            transaction_date = record['transaction_date']
            if transaction_date:
                # 處理不同的日期格式
                if isinstance(transaction_date, str):
                    # 如果是字符串，嘗試解析
                    try:
                        date_obj = datetime.datetime.strptime(transaction_date, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            date_obj = datetime.datetime.strptime(transaction_date, '%Y/%m/%d').date()
                        except ValueError:
                            logger.warning(f"無法解析日期格式: {transaction_date}")
                            continue
                elif hasattr(transaction_date, 'year') and hasattr(transaction_date, 'month'):
                    # 如果已經是日期對象
                    date_obj = transaction_date
                else:
                    logger.warning(f"未知日期格式: {transaction_date}")
                    continue
                
                months.add((date_obj.year, date_obj.month))
        
        return months
    
    def generate_unique_transaction_id(self) -> str:
        """
        生成唯一的 8 位數字+小寫英文 transaction_id
        格式: 8位隨機字符 (數字+小寫字母) 例如: a1b2c3d4
        
        Returns:
            str: 唯一的 transaction_id
        """
        max_attempts = 10
        for attempt in range(max_attempts):
            # 使用更精確的時間戳 + 隨機字符確保唯一性
            timestamp = str(int(datetime.datetime.now().timestamp() * 1000000))[-6:]  # 取微秒時間戳後6位
            random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=2))
            transaction_id = timestamp + random_chars
            
            # 檢查是否已存在（僅在有資料庫連接時）
            if self.connection and not self.transaction_id_exists(transaction_id):
                return transaction_id
            elif not self.connection:
                # 如果沒有資料庫連接，直接返回（在解析階段）
                return transaction_id
            
            # 如果重複，加入更多隨機性
            import time
            time.sleep(0.001)  # 等待1毫秒確保時間戳不同
        
        # 如果10次嘗試都失敗，使用完全隨機的ID
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    def transaction_id_exists(self, transaction_id: str) -> bool:
        """
        檢查 transaction_id 是否已存在
        
        Args:
            transaction_id (str): 要檢查的 transaction_id
            
        Returns:
            bool: 如果已存在返回 True，否則返回 False
        """
        try:
            with self.connection.cursor() as cursor:
                query = f"""
                SELECT EXISTS(
                    SELECT 1 FROM {self.table_config['order_transactions']}
                    WHERE transaction_id = %s
                )
                """
                cursor.execute(query, (transaction_id,))
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"檢查 transaction_id 存在性失敗: {str(e)}")
            # 回滾當前事務以清除錯誤狀態
            try:
                self.connection.rollback()
            except:
                pass
            return True  # 出錯時保守處理，假設已存在

    def check_customer_exists(self, customer_id: str) -> bool:
        """
        檢查客戶是否已存在
        
        Args:
            customer_id (str): 客戶ID
            
        Returns:
            bool: 如果已存在返回 True，否則返回 False
        """
        try:
            with self.connection.cursor() as cursor:
                query = f"""
                SELECT EXISTS(
                    SELECT 1 FROM {self.table_config['customer']}
                    WHERE customer_id = %s
                )
                """
                cursor.execute(query, (customer_id,))
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"檢查客戶存在性失敗: {str(e)}")
            # 回滾當前事務以清除錯誤狀態
            try:
                self.connection.rollback()
            except:
                pass
            return False  # 出錯時假設不存在
    
    def get_missing_customers(self, data: List[Dict]) -> List[str]:
        """
        檢查數據中哪些客戶不存在於資料庫中
        
        Args:
            data (list): 交易記錄列表
            
        Returns:
            list: 不存在的客戶ID列表
        """
        if not self.connection:
            raise Exception("數據庫未連接")
        
        # 提取所有唯一的客戶ID
        unique_customer_ids = set()
        for record in data:
            customer_id = record.get('customer_id')
            if customer_id and customer_id.strip():
                unique_customer_ids.add(customer_id.strip())
        
        missing_customers = []
        
        for customer_id in unique_customer_ids:
            if not self.check_customer_exists(customer_id):
                missing_customers.append(customer_id)
                logger.info(f"發現新客戶ID: {customer_id}")
        
        return missing_customers
    
    def parse_sales_data(self, file_path: str) -> List[Dict]:
        """
        解析 Excel 文件，提取交易數據
        
        Args:
            file_path (str): Excel 文件路徑
        
        Returns:
            list: 包含所有交易記錄的列表
        """
        logger.info(f"開始解析文件: {file_path}")
        
        # 使用 openpyxl 讀取 Excel 文件
        workbook = load_workbook(file_path, data_only=True)
        worksheet = workbook.active
        
        logger.info(f"工作表名稱: {worksheet.title}")
        logger.info(f"數據範圍: {worksheet.calculate_dimension()}")
        
        # 獲取最大行數和列數
        max_row = worksheet.max_row
        max_col = worksheet.max_column
        
        logger.info(f"總行數: {max_row}, 總列數: {max_col}")
        
        # 數據從第8行開始
        data = []
        
        # 用於向前填充的變量
        current_customer_id = ''
        current_product_id = ''
        current_product_name = ''
        current_currency = ''
        
        # 遍歷從第8行開始的所有行
        for row in range(8, max_row + 1):
            # 獲取各列的值
            customer_id_cell = worksheet.cell(row=row, column=1).value    # A列
            product_id_cell = worksheet.cell(row=row, column=6).value     # F列
            product_name_cell = worksheet.cell(row=row, column=11).value  # K列
            transaction_date = worksheet.cell(row=row, column=14).value   # N列
            document_type = worksheet.cell(row=row, column=17).value or '' # Q列
            quantity = worksheet.cell(row=row, column=19).value           # S列
            unit_price = worksheet.cell(row=row, column=22).value or 0    # V列
            currency_cell = worksheet.cell(row=row, column=25).value      # Y列
            amount = worksheet.cell(row=row, column=26).value or 0        # Z列
            
            # 向前填充邏輯
            if customer_id_cell and str(customer_id_cell).strip():
                current_customer_id = str(customer_id_cell).strip()
                
            if product_id_cell and str(product_id_cell).strip():
                current_product_id = str(product_id_cell).strip()
                
            if product_name_cell and str(product_name_cell).strip():
                current_product_name = str(product_name_cell).strip()
                
            if currency_cell and str(currency_cell).strip():
                current_currency = str(currency_cell).strip()
            
            # 檢查是否有關鍵數據
            if transaction_date and quantity is not None and quantity != '':
                # 生成唯一的 transaction_id
                unique_transaction_id = self.generate_unique_transaction_id()
                
                record = {
                    'transaction_id': unique_transaction_id,
                    'customer_id': current_customer_id,
                    'product_id': current_product_id, 
                    'product_name': current_product_name,
                    'transaction_date': transaction_date,
                    'document_type': str(document_type),
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'currency': current_currency,
                    'amount': amount
                }
                
                data.append(record)
        
        logger.info(f"解析完成，共 {len(data)} 筆交易記錄")
        return data
    
    def get_product_is_active(self, product_id: str) -> Optional[bool]:
        """
        從 product_master 表中獲取產品的 is_active 狀態
        
        Args:
            product_id (str): 產品編號
            
        Returns:
            bool: is_active 狀態，如果找不到則返回 None
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = f"""
                SELECT is_active 
                FROM {self.table_config['product_master']} 
                WHERE product_id = %s
                """
                cursor.execute(query, (product_id,))
                result = cursor.fetchone()
                
                if result:
                    return result['is_active']
                else:
                    logger.warning(f"產品 {product_id} 在 product_master 中未找到")
                    return None
                    
        except Exception as e:
            logger.error(f"查詢產品 {product_id} 的 is_active 狀態失敗: {str(e)}")
            # 回滾當前事務以清除錯誤狀態
            try:
                self.connection.rollback()
            except:
                pass
            return None
    
    def insert_record(self, record: Dict, is_active: Optional[bool]):
        """
        插入新記錄
        
        Args:
            record (dict): 交易記錄
            is_active (bool): 產品是否活躍
        """
        try:
            with self.connection.cursor() as cursor:
                query = f"""
                INSERT INTO {self.table_config['order_transactions']}
                (transaction_id, customer_id, product_id, product_name, 
                 transaction_date, document_type, quantity, unit_price, 
                 currency, amount, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    record['transaction_id'],
                    record['customer_id'],
                    record['product_id'],
                    record['product_name'],
                    record['transaction_date'],
                    record['document_type'],
                    record['quantity'],
                    record['unit_price'],
                    record['currency'],
                    record['amount'],
                    is_active,
                    datetime.datetime.now()
                ))
                logger.debug(f"插入新記錄 transaction_id: {record['transaction_id']}")
                
        except Exception as e:
            logger.error(f"插入記錄失敗: {str(e)}")
            raise
    
    def insert_all_records(self, data: List[Dict]) -> int:
        """
        直接插入所有記錄（不檢查重複）
        
        Args:
            data (list): 交易記錄列表
            
        Returns:
            int: 插入記錄數
        """
        if not self.connection:
            raise Exception("數據庫未連接")
        
        inserted_count = 0
        
        try:
            logger.info(f"開始插入 {len(data)} 筆記錄")
            
            for i, record in enumerate(data):
                # 獲取產品的 is_active 狀態
                is_active = self.get_product_is_active(record['product_id'])
                
                # 直接插入新記錄
                self.insert_record(record, is_active)
                inserted_count += 1
                
                # 每處理一定數量記錄就提交一次
                if (i + 1) % DEFAULT_CONFIG['batch_size'] == 0:
                    self.connection.commit()
                    logger.info(f"已處理 {i + 1} 筆記錄")
            
            # 最終提交
            self.connection.commit()
            logger.info(f"數據插入完成 - 插入: {inserted_count} 筆")
            
            return inserted_count
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"數據插入失敗: {str(e)}")
            raise
    
    def process_file_with_customer_check(self, file_path: str, delete_month_records: bool = True) -> Tuple[int, int, List[str]]:
        """
        處理整個流程：解析文件 -> 檢查客戶 -> 返回缺失客戶列表
        
        Args:
            file_path (str): Excel 文件路徑
            delete_month_records (bool): 是否刪除涉及月份記錄，默認為 True
            
        Returns:
            tuple: (刪除記錄數, 插入記錄數, 缺失客戶列表)
        """
        deleted_count = 0
        
        try:
            # 連接數據庫
            if not self.connect_database():
                raise Exception("無法連接數據庫")
            
            # 1. 先解析 Excel 文件
            logger.info("解析 Excel 文件以提取月份信息...")
            data = self.parse_sales_data(file_path)
            
            # 2. 檢查缺失的客戶
            missing_customers = self.get_missing_customers(data)
            
            if missing_customers:
                logger.info(f"發現 {len(missing_customers)} 個新客戶需要創建: {missing_customers}")
                # 返回缺失客戶列表，暫不進行數據插入
                return 0, 0, missing_customers
            
            # 3. 如果沒有缺失客戶，繼續原有流程
            # 從數據中提取所有涉及的年月
            months_to_delete = self.extract_months_from_data(data)
            logger.info(f"Excel 中包含的月份: {sorted(list(months_to_delete))}")
            
            # 4. 刪除這些月份的所有記錄（如果需要）
            if delete_month_records and months_to_delete:
                logger.info(f"開始刪除 {len(months_to_delete)} 個月份的記錄...")
                deleted_count = self.delete_records_by_months(months_to_delete)
            
            # 5. 直接插入新記錄
            inserted_count = self.insert_all_records(data)
            
            return deleted_count, inserted_count, []
            
        finally:
            # 關閉數據庫連接
            self.close_connection()

    def process_file(self, file_path: str, delete_month_records: bool = True) -> Tuple[int, int]:
        """
        處理整個流程：解析文件 -> 刪除涉及月份記錄 -> 上傳數據庫
        
        Args:
            file_path (str): Excel 文件路徑
            delete_month_records (bool): 是否刪除涉及月份記錄，默認為 True
            
        Returns:
            tuple: (刪除記錄數, 插入記錄數)
        """
        deleted_count = 0
        
        try:
            # 連接數據庫
            if not self.connect_database():
                raise Exception("無法連接數據庫")
            
            # 1. 先解析 Excel 文件
            logger.info("解析 Excel 文件以提取月份信息...")
            data = self.parse_sales_data(file_path)
            
            # 2. 從數據中提取所有涉及的年月
            months_to_delete = self.extract_months_from_data(data)
            logger.info(f"Excel 中包含的月份: {sorted(list(months_to_delete))}")
            
            # 3. 刪除這些月份的所有記錄（如果需要）
            if delete_month_records and months_to_delete:
                logger.info(f"開始刪除 {len(months_to_delete)} 個月份的記錄...")
                deleted_count = self.delete_records_by_months(months_to_delete)
            
            # 4. 直接插入新記錄
            inserted_count = self.insert_all_records(data)
            
            return deleted_count, inserted_count
            
        finally:
            # 關閉數據庫連接
            self.close_connection()

# API 端點
@router.post("/import/sales/check-customers")
async def check_sales_customers(file: UploadFile = File(...), user_role: str = Form(...)):
    """
    檢查銷貨資料中的客戶是否存在，返回缺失的客戶列表
    """
    try:
        # 檢查權限
        check_editor_permission(user_role)
        
        # 檢查檔案類型
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支援 Excel 檔案格式")
        
        # 創建臨時檔案
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 使用 SalesDataUploader 處理檔案
            sales_uploader = SalesDataUploader()
            deleted_count, inserted_count, missing_customers = sales_uploader.process_file_with_customer_check(temp_file_path)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "missing_customers": missing_customers,
                    "message": f"檢查完成，發現 {len(missing_customers)} 個新客戶需要創建" if missing_customers else "所有客戶都已存在，可以直接匯入",
                    "filename": file.filename
                }
            )
            
        finally:
            # 清理臨時檔案
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"檢查客戶失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"檢查失敗: {str(e)}")

@router.post("/import/sales")
async def import_sales_data(file: UploadFile = File(...), user_role: str = Form(...)):
    """
    匯入銷貨資料 API
    """
    try:
        # 檢查權限
        check_editor_permission(user_role)
        
        # 檢查檔案類型
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支援 Excel 檔案格式")
        
        # 創建臨時檔案
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 使用 SalesDataUploader 處理檔案
            sales_uploader = SalesDataUploader()
            deleted_count, inserted_count = sales_uploader.process_file(temp_file_path)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"匯入成功！刪除 {deleted_count} 筆舊記錄，新增 {inserted_count} 筆交易記錄",
                    "deleted_count": deleted_count,
                    "inserted_count": inserted_count,
                    "filename": file.filename
                }
            )
            
        finally:
            # 清理臨時檔案
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"匯入銷貨資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"匯入失敗: {str(e)}")

@router.post("/customer/create")
async def create_customer(customer_data: dict):
    """
    創建新客戶API
    """
    try:
        uploader = SalesDataUploader()
        if not uploader.connect_database():
            raise Exception("無法連接數據庫")
        
        try:
            with uploader.connection.cursor() as cursor:
                # 修正：移除 created_at 欄位
                query = f"""
                INSERT INTO {uploader.table_config['customer']}
                (customer_id, customer_name, phone_number, address, delivery_schedule, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    customer_data['customer_id'],
                    customer_data['customer_name'],
                    customer_data.get('phone_number', ''),
                    customer_data.get('address', ''),
                    customer_data.get('delivery_schedule', ''),
                    customer_data.get('notes', '')
                ))
                uploader.connection.commit()
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": f"客戶 {customer_data['customer_id']} 創建成功",
                        "customer_id": customer_data['customer_id']
                    }
                )
                
        finally:
            uploader.close_connection()
            
    except Exception as e:
        logger.error(f"創建客戶失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"創建客戶失敗: {str(e)}")

@router.get("/import/test-connection")
async def test_database_connection():
    """
    測試資料庫連接
    """
    try:
        uploader = SalesDataUploader()
        if uploader.connect_database():
            uploader.close_connection()
            return JSONResponse(
                status_code=200,
                content={"success": True, "message": "資料庫連接成功"}
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "資料庫連接失敗"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"連接測試失敗: {str(e)}"}
        )