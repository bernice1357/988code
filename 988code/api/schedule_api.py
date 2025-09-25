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
from typing import Dict, List, Optional
import psycopg2
import json
from datetime import datetime, timezone, timedelta
import requests
import logging
import sys
import os

# 添加 scheduler 模組到路徑
scheduler_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scheduler')
scheduler_path = os.path.abspath(scheduler_path)
sys.path.insert(0, scheduler_path)

# 使用子進程執行以避免segfault
import subprocess

def run_task(task_id: str) -> dict:
    """在子進程中執行任務，避免記憶體衝突"""
    try:
        # 構建Python命令 - 使用動態路徑而非硬編碼
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        scheduler_path = os.path.join(os.path.dirname(current_file_dir), 'scheduler')
        scheduler_path = scheduler_path.replace('\\', '\\\\')  # Windows路徑轉義
        
        python_code = f"""
import sys
import json
import os

# 動態添加scheduler路徑
scheduler_path = r'{scheduler_path}'
sys.path.insert(0, scheduler_path)

try:
    from task_executor import execute_task
    result = execute_task('{task_id}')
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{'success': False, 'error': str(e)}}))
"""
        
        # 執行子進程
        result = subprocess.run(
            ["python", "-c", python_code],
            capture_output=True,
            text=True,
            timeout=300  # 5分鐘超時
        )
        
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            return {"success": False, "error": error_msg}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Task execution timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 導入並實例化integrated_scheduler
try:
    scheduler_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scheduler')
    scheduler_path = os.path.abspath(scheduler_path)
    sys.path.insert(0, scheduler_path)
    
    from integrated_scheduler import integrated_scheduler
    logging.info("Integrated scheduler imported successfully")
except Exception as e:
    logging.error(f"Failed to import integrated_scheduler: {e}")
    integrated_scheduler = None

router = APIRouter()


# 排程任務配置
SCHEDULE_TASKS = {
    "restock": {
        "name": "補貨排程",
        "tasks": [
            {"id": "weekly_model_training", "name": "週度模型訓練", "schedule": "週六 08:00", "description": "使用CatBoost進行週度模型訓練"},
            {"id": "daily_prediction", "name": "每日預測生成", "schedule": "每天 22:00", "description": "使用CatBoost生成明天的購買預測"},
            {"id": "trigger_health_check", "name": "觸發器健康檢查", "schedule": "每天 02:00", "description": "檢查資料庫觸發器狀態"}
        ]
    },
    "sales": {
        "name": "銷售排程",
        "tasks": [
            {"id": "sales_change_check", "name": "銷量變化檢查", "schedule": "每天 06:00", "description": "監控產品銷量變化"},
            {"id": "monthly_prediction", "name": "月銷售預測", "schedule": "每月1號 01:00", "description": "使用混合CV系統預測下個月銷量"},
            {"id": "monthly_sales_reset", "name": "銷量重置", "schedule": "每月1號 00:30", "description": "重置月度銷量統計"}
        ]
    },
    "recommendation": {
        "name": "推薦排程",
        "tasks": [
            {"id": "weekly_recommendation", "name": "推薦系統更新", "schedule": "週日 02:00", "description": "更新產品推薦列表"}
        ]
    },
    "customer_management": {
        "name": "客戶管理排程",
        "tasks": [
            {"id": "inactive_customer_check", "name": "不活躍客戶檢查", "schedule": "每天 02:30", "description": "識別並追蹤不活躍客戶"},
            {"id": "repurchase_reminder", "name": "回購提醒維護", "schedule": "每天 04:00", "description": "管理客戶回購提醒"}
        ]
    }
}

class ScheduleToggleRequest(BaseModel):
    category: str
    enabled: bool

class TaskExecuteRequest(BaseModel):
    task_id: str

def get_data_from_db(sql_prompt: str, params=None):
    """從資料庫獲取數據"""
    try:
        # 注意: 此處仍使用舊的資料庫連線方式，需要根據具體邏輯手動替換
        with psycopg2.connect(
            dbname='988',
            user='postgres',
            password='988988',
            host='localhost',
            port='5432'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_prompt, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return rows, columns
    except Exception as e:
        logging.error(f"[DB ERROR] {e}")
        raise

def update_data_to_db(sql_prompt: str, params=None):
    """更新資料庫數據"""
    try:
        # 注意: 此處仍使用舊的資料庫連線方式，需要根據具體邏輯手動替換
        with psycopg2.connect(
            dbname='988',
            user='postgres',
            password='988988',
            host='localhost',
            port='5432'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_prompt, params)
                conn.commit()
    except Exception as e:
        logging.error(f"[DB ERROR] {e}")
        raise

# 台北時區
TAIPEI_TZ = timezone(timedelta(hours=8))

def get_taipei_time():
    """獲取台北時間"""
    return datetime.now(TAIPEI_TZ)

def init_schedule_tables():
    """初始化排程相關資料表"""
    try:
        # 使用新的資料庫連線系統
        # 建立排程設定表
        execute_query("""
            CREATE TABLE IF NOT EXISTS schedule_settings (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) NOT NULL UNIQUE,
                category_name VARCHAR(100) NOT NULL,
                enabled BOOLEAN DEFAULT true,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Taipei')
            )
        """, fetch='none')

        # 建立任務執行歷史表
        execute_query("""
            CREATE TABLE IF NOT EXISTS schedule_history (
                id SERIAL PRIMARY KEY,
                task_id VARCHAR(50) NOT NULL,
                task_name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                execution_time TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Taipei'),
                status VARCHAR(20) NOT NULL,
                message TEXT,
                duration_seconds INTEGER
            )
        """, fetch='none')

        # 插入預設排程設定
        for category, config in SCHEDULE_TASKS.items():
            execute_query("""
                INSERT INTO schedule_settings (category, category_name, enabled)
                VALUES (%s, %s, %s)
                ON CONFLICT (category) DO NOTHING
            """, (category, config["name"], True), fetch='none')

        return True

    except Exception as e:
        logging.error(f"初始化排程表失敗: {e}")
        return False

@router.get("/schedule/tasks")
def get_schedule_tasks():
    """獲取所有排程任務配置"""
    try:
        # 注意: 此處仍使用舊的資料庫連線方式，需要根據具體邏輯手動替換
        with psycopg2.connect(
            dbname='988',
            user='postgres',
            password='988988',
            host='localhost',
            port='5432'
        ) as conn:
            with conn.cursor() as cursor:
                # 獲取排程設定
                cursor.execute("SELECT category, enabled FROM schedule_settings")
                settings = dict(cursor.fetchall())
                
                # 獲取最後執行時間
                cursor.execute("""
                    SELECT DISTINCT ON (task_id) task_id, execution_time, status
                    FROM schedule_history 
                    ORDER BY task_id, execution_time DESC
                """)
                last_executions = {row[0]: {"time": row[1], "status": row[2]} for row in cursor.fetchall()}
        
        # 組合結果
        result = {}
        for category, config in SCHEDULE_TASKS.items():
            result[category] = {
                "name": config["name"],
                "enabled": settings.get(category, True),
                "tasks": []
            }
            
            for task in config["tasks"]:
                task_info = task.copy()
                if task["id"] in last_executions:
                    # 確保時間轉換為台北時區
                    exec_time = last_executions[task["id"]]["time"]
                    if exec_time.tzinfo is None:
                        # 如果沒有時區信息，假設是 UTC 並轉換為台北時間
                        exec_time = exec_time.replace(tzinfo=timezone.utc).astimezone(TAIPEI_TZ)
                    else:
                        # 轉換為台北時間
                        exec_time = exec_time.astimezone(TAIPEI_TZ)
                    
                    task_info["last_execution"] = exec_time.isoformat()
                    task_info["last_status"] = last_executions[task["id"]]["status"]
                else:
                    task_info["last_execution"] = None
                    task_info["last_status"] = "never"
                result[category]["tasks"].append(task_info)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        logging.error(f"獲取排程任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取排程任務失敗: {str(e)}")

@router.post("/schedule/toggle")
def toggle_schedule(request: ScheduleToggleRequest):
    """切換排程開關"""
    try:
        if request.category not in SCHEDULE_TASKS:
            raise HTTPException(status_code=400, detail="無效的排程分類")
        
        # 注意: 此處仍使用舊的資料庫連線方式，需要根據具體邏輯手動替換
        with psycopg2.connect(
            dbname='988',
            user='postgres',
            password='988988',
            host='localhost',
            port='5432'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE schedule_settings 
                    SET enabled = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE category = %s
                """, (request.enabled, request.category))
                conn.commit()
        
        # 刷新整合排程器的狀態
        if integrated_scheduler:
            integrated_scheduler.refresh_schedule_states()
        
        return {
            "success": True, 
            "message": f"排程 {SCHEDULE_TASKS[request.category]['name']} 已{'啟用' if request.enabled else '停用'}"
        }
        
    except Exception as e:
        logging.error(f"切換排程失敗: {e}")
        raise HTTPException(status_code=500, detail=f"切換排程失敗: {str(e)}")

@router.post("/schedule/execute")
def execute_task(request: TaskExecuteRequest):
    """手動執行任務"""
    try:
        # 找到任務配置
        task_config = None
        category = None
        
        for cat, config in SCHEDULE_TASKS.items():
            for task in config["tasks"]:
                if task["id"] == request.task_id:
                    task_config = task
                    category = cat
                    break
            if task_config:
                break
        
        if not task_config:
            raise HTTPException(status_code=400, detail="無效的任務ID")
        
        # 記錄執行開始（台北時間）
        start_time = get_taipei_time()
        
        # 注意: 此處仍使用舊的資料庫連線方式，需要根據具體邏輯手動替換
        with psycopg2.connect(
            dbname='988',
            user='postgres',
            password='988988',
            host='localhost',
            port='5432'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO schedule_history (task_id, task_name, category, status, message)
                    VALUES (%s, %s, %s, %s, %s)
                """, (request.task_id, task_config["name"], category, "running", "手動執行開始"))
                conn.commit()
        
        # 使用子進程執行任務
        try:
            execution_result = run_task(request.task_id)
            success = execution_result.get('success', False)
            message = execution_result.get('message', f"任務 {task_config['name']} 執行完成")
            # 如果任務執行器提供了持續時間，使用它
            if 'duration' in execution_result:
                duration = execution_result['duration']
                end_time = start_time + timedelta(seconds=duration)
        except Exception as e:
            success = False
            message = f"任務 {task_config['name']} 執行失敗: {str(e)}"
            logging.error(f"Task execution error: {e}")
        
        # 記錄執行結果（台北時間）
        if 'end_time' not in locals():
            end_time = get_taipei_time()
        if 'duration' not in locals():
            duration = int((end_time - start_time).total_seconds())
        
        # 注意: 此處仍使用舊的資料庫連線方式，需要根據具體邏輯手動替換
        with psycopg2.connect(
            dbname='988',
            user='postgres',
            password='988988',
            host='localhost',
            port='5432'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO schedule_history (task_id, task_name, category, status, message, duration_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (request.task_id, task_config["name"], category, 
                      "success" if success else "failed", message, duration))
                conn.commit()
        
        return {
            "success": success,
            "message": message,
            "duration_seconds": duration
        }
        
    except Exception as e:
        logging.error(f"執行任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"執行任務失敗: {str(e)}")

@router.get("/schedule/history/{task_id}")
def get_task_history(task_id: str, limit: int = 10):
    """獲取任務執行歷史"""
    try:
        # 注意: 此處仍使用舊的資料庫連線方式，需要根據具體邏輯手動替換
        with psycopg2.connect(
            dbname='988',
            user='postgres',
            password='988988',
            host='localhost',
            port='5432'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT execution_time AT TIME ZONE 'Asia/Taipei' as execution_time, 
                           status, message, duration_seconds
                    FROM schedule_history 
                    WHERE task_id = %s
                    ORDER BY execution_time DESC
                    LIMIT %s
                """, (task_id, limit))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        "execution_time": row[0].isoformat(),
                        "status": row[1],
                        "message": row[2],
                        "duration_seconds": row[3]
                    })
        
        return {"success": True, "data": history}
        
    except Exception as e:
        logging.error(f"獲取任務歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取任務歷史失敗: {str(e)}")

@router.get("/schedule/status")
def get_schedule_status():
    """獲取排程系統狀態"""
    try:
        # 注意: 此處仍使用舊的資料庫連線方式，需要根據具體邏輯手動替換
        with psycopg2.connect(
            dbname='988',
            user='postgres',
            password='988988',
            host='localhost',
            port='5432'
        ) as conn:
            with conn.cursor() as cursor:
                # 獲取今日執行統計
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM schedule_history 
                    WHERE DATE(execution_time) = CURRENT_DATE
                    GROUP BY status
                """)
                today_stats = dict(cursor.fetchall())
                
                # 獲取啟用的排程數量
                cursor.execute("SELECT COUNT(*) FROM schedule_settings WHERE enabled = true")
                enabled_schedules = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM schedule_settings")
                total_schedules = cursor.fetchone()[0]
        
        return {
            "success": True,
            "data": {
                "enabled_schedules": enabled_schedules,
                "total_schedules": total_schedules,
                "today_executions": today_stats,
                "system_status": "running" if enabled_schedules > 0 else "stopped"
            }
        }
        
    except Exception as e:
        logging.error(f"獲取排程狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取排程狀態失敗: {str(e)}")

@router.post("/schedule/start_scheduler")
def start_scheduler():
    """啟動整合排程器"""
    try:
        if integrated_scheduler:
            integrated_scheduler.start_scheduler()
            return {"success": True, "message": "Integrated scheduler started"}
        else:
            return {"success": False, "message": "Integrated scheduler not available"}
    except Exception as e:
        logging.error(f"Failed to start scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/schedule/stop_scheduler")
def stop_scheduler():
    """停止整合排程器"""
    try:
        if integrated_scheduler:
            integrated_scheduler.stop_scheduler()
            return {"success": True, "message": "Integrated scheduler stopped"}
        else:
            return {"success": False, "message": "Integrated scheduler not available"}
    except Exception as e:
        logging.error(f"Failed to stop scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.get("/schedule/scheduler_status")
def get_scheduler_status():
    """獲取排程器狀態"""
    try:
        logging.info(f"integrated_scheduler type: {type(integrated_scheduler)}")
        logging.info(f"integrated_scheduler value: {integrated_scheduler}")
        
        if integrated_scheduler is not None:
            return {
                "success": True,
                "data": {
                    "running": integrated_scheduler.running,
                    "schedule_states": integrated_scheduler.schedule_enabled,
                    "next_jobs": integrated_scheduler.get_next_jobs()
                }
            }
        else:
            logging.warning("integrated_scheduler is None")
            return {"success": False, "message": "Integrated scheduler not available"}
    except Exception as e:
        logging.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

# 初始化資料表
init_schedule_tables()

# 環境變數控制自動啟動整合排程器
# 設定 SCHEDULER_AUTOSTART=1 時才自動啟動，避免在8000和9000端口重複啟動
if integrated_scheduler and os.getenv("SCHEDULER_AUTOSTART") == "1":
    try:
        integrated_scheduler.start_scheduler()
        logging.info("Integrated scheduler auto-started with API (SCHEDULER_AUTOSTART=1)")
    except Exception as e:
        logging.error(f"Failed to auto-start scheduler: {e}")
else:
    if integrated_scheduler:
        logging.info("Scheduler available but not auto-started (set SCHEDULER_AUTOSTART=1 to enable)")
    else:
        logging.warning("Integrated scheduler not available")