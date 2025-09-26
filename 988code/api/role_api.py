from fastapi import APIRouter, HTTPException
import sys
import os
# 新增資料庫連線管理
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection, execute_query, execute_transaction
from env_loader import load_env_file

# 載入環境變數
load_env_file()
from pydantic import BaseModel
import pandas as pd
import psycopg2
import bcrypt
from datetime import datetime, timedelta

router = APIRouter()

def role_data_from_db(sql_prompt: str, params=None) -> pd.DataFrame:
    try:
        # 使用新的資料庫連線管理系統
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_prompt, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(f"[DB ERROR] {e}")
        raise

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(login_data: LoginRequest):
    sql = """
        SELECT password_hash, full_name, role
        FROM users 
        WHERE (username = %s OR email = %s) AND is_active = TRUE
    """
    params = (login_data.username, login_data.username)

    try:
        df = role_data_from_db(sql, params)
        
        if df.empty:
            raise HTTPException(status_code=401, detail="帳號不存在或已停用")
        
        user_data = df.iloc[0]
        
        # 驗證密碼
        if bcrypt.checkpw(login_data.password.encode(), user_data['password_hash'].encode()):
            return {
                "success": True,
                "user": {
                    "full_name": user_data['full_name'],
                    "role": user_data['role']
                }
            }
        else:
            raise HTTPException(status_code=401, detail="密碼錯誤")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail="登入失敗")