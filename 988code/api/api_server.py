from fastapi import FastAPI

# 引入各個路由模組
from get_api import router as get_data_router
from get_params_api import router as get_data_with_params_router
from put_api import router as update_data_router

app = FastAPI()

# 註冊路由
app.include_router(get_data_router)
app.include_router(get_data_with_params_router)
app.include_router(update_data_router)