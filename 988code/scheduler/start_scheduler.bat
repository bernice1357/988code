@echo off
echo === 啟動排程器系統 ===
echo.
echo 排程器將在背景持續運行，監控並執行以下任務：
echo.
echo [每日任務]
echo   02:00 - 觸發器健康檢查
echo   02:30 - 不活躍客戶檢查
echo   04:00 - 回購提醒維護
echo   06:00 - 銷量變化檢查
echo   22:00 - 每日預測生成
echo.
echo [每週任務]
echo   週六 08:00 - Prophet模型訓練
echo   週日 02:00 - 推薦系統更新
echo.
echo [每月任務]
echo   每月1號 00:30 - 銷量重置
echo   每月1號 01:00 - 月銷售預測
echo.
echo 按任意鍵開始...
pause

cd /d "C:\Users\user\Desktop\988\988code\988code\scheduler"
"C:\Users\user\anaconda3\envs\fabric\python.exe" -c "from scheduler import PredictionScheduler; scheduler = PredictionScheduler(); scheduler.run_scheduler()"