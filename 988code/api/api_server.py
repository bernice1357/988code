import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 引入各個路由模組
from get_api import router as get_data_router
from get_params_api import router as get_data_with_params_router
from put_api import router as update_data_router
from role_api import router as role_router
from import_data_api import router as import_data_router
from sales_predict_api import router as sales_predict_router
from schedule_api import router as schedule_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8050", "http://localhost:8050"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
