#!/usr/bin/env python3
"""
Scheduler專用API服務器
運行在9000端口，專門處理scheduler相關的API請求
"""

import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 設定環境變數 - 必須在導入schedule_api之前設定
os.environ["SCHEDULER_AUTOSTART"] = "1"

# 添加必要目錄到路徑
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
api_dir = os.path.join(parent_dir, 'api')
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, api_dir)

# 導入schedule API路由
from schedule_api import router as schedule_router

# 創建FastAPI應用
app = FastAPI(
    title="988 Scheduler API",
    description="Scheduler任務管理和控制API",
    version="1.0.0"
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8050", 
        "http://localhost:8050",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "https://988kitchen.com/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊scheduler API路由
app.include_router(schedule_router)

@app.get("/")
def root():
    """根路徑 - 服務狀態檢查"""
    return {
        "service": "988 Scheduler API",
        "status": "running",
        "port": 9000,
        "endpoints": [
            "/schedule/tasks",
            "/schedule/execute", 
            "/schedule/toggle",
            "/schedule/status",
            "/schedule/history/{task_id}",
            "/schedule/start_scheduler",
            "/schedule/stop_scheduler",
            "/schedule/scheduler_status"
        ]
    }

@app.get("/health")
def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "scheduler_api"}

def main():
    """主函數 - 啟動scheduler API服務器"""
    
    print("=" * 50)
    print("988 SCHEDULER API SERVER")
    print("=" * 50)
    print("Port: 9000")
    print("Environment: SCHEDULER_AUTOSTART=1")
    print("Endpoints:")
    print("  GET  /              - 服務狀態")
    print("  GET  /health        - 健康檢查")
    print("  GET  /schedule/tasks - 獲取所有任務")
    print("  POST /schedule/execute - 手動執行任務")
    print("  POST /schedule/toggle - 切換排程開關")
    print("  GET  /schedule/status - 排程系統狀態")
    print("  POST /schedule/start_scheduler - 啟動排程器")
    print("  POST /schedule/stop_scheduler - 停止排程器")
    print("=" * 50)
    
    # 啟動服務器
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()