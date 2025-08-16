from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 引入各個路由模組
from get_api import router as get_data_router
from get_params_api import router as get_data_with_params_router
from put_api import router as update_data_router
from role_api import router as role_router
from import_data_api import router as import_data_router
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
app.include_router(schedule_router)

@app.get("/")
async def root():
    return {"message": "988 API Server is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": "2025-08-16"}