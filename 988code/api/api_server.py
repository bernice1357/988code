import os
from fastapi import FastAPI, HTTPException, status
import sys
import os

# 首先載入環境變數
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env_loader import load_env_file, get_env_int
load_env_file()

# 然後載入資料庫連線管理
from database_config import get_db_connection, execute_query, execute_transaction
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# 引入各個路由模組
from get_api import router as get_data_router
from get_params_api import router as get_data_with_params_router
from put_api import router as update_data_router
from role_api import router as role_router
from import_data_api import router as import_data_router
from sales_predict_api import router as sales_predict_router
from schedule_api import router as schedule_router

MAX_UPLOAD_SIZE_MB = get_env_int('MAX_UPLOAD_SIZE_MB', 50)
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    """限制請求內容長度，避免過大的檔案造成 413 或佔用過多資源"""

    def __init__(self, app, max_upload_size: int):
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit():
            if int(content_length) > self.max_upload_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"上傳內容超過 {MAX_UPLOAD_SIZE_MB}MB 限制"
                )
        return await call_next(request)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8050", "http://localhost:8050","https://988kitchen.com/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LimitUploadSizeMiddleware, max_upload_size=MAX_UPLOAD_SIZE_BYTES)

# 註冊路由
app.include_router(get_data_router)
app.include_router(get_data_with_params_router)
app.include_router(update_data_router)
app.include_router(role_router)
app.include_router(import_data_router)
app.include_router(sales_predict_router)

# 環境變數控制是否在8000端口暴露scheduler API
# 設為 "1" 時才會在8000端口註冊scheduler路由，預設隔離到9000端口
if os.getenv("EXPOSE_SCHEDULER_ON_8000") == "1":
    app.include_router(schedule_router)
    print("INFO: Scheduler API exposed on port 8000")
else:
    print("INFO: Scheduler API isolated to port 9000 (recommended)")

# 基本路由檢查
@app.get("/")
def read_root():
    return {"message": "988 API Server is running", "version": "1.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API server is operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
