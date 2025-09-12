# 排程器健康監控系統

本系統提供完整的排程器健康狀態監控功能，可以檢查資料庫中各個排程器在其對應表格中的更新時間，識別問題並發送警報。

## 系統概述

### 監控的排程器 (9個)

#### 補貨排程 (restock) - 3個
- **daily_prediction**: 每日預測生成 - `prophet_predictions` 表 (每日 22:00)
- **weekly_model_training**: 週度模型訓練 - `schedule_history` 表 (每週六 08:00)
- **trigger_health_check**: 觸發器健康檢查 - `trigger_health_log` 表 (每日 02:00)

#### 銷售排程 (sales) - 3個
- **sales_change_check**: 銷量變化檢查 - `sales_change_table` 表 (每日 06:00)
- **monthly_prediction**: 月銷售預測 - `monthly_sales_predictions` 表 (每月1號 01:00)
- **monthly_sales_reset**: 銷量重置 - `sales_change_table` 表 (每月1號 00:30)

#### 推薦排程 (recommendation) - 1個
- **weekly_recommendation**: 推薦系統更新 - `schedule_history` 表 (每週日 08:00)

#### 客戶管理排程 (customer_management) - 2個
- **inactive_customer_check**: 不活躍客戶檢查 - `inactive_customers` 表 (每日 02:30)
- **repurchase_reminder**: 回購提醒維護 - `repurchase_reminders` 表 (每日 04:00)

## 核心組件

### 1. scheduler_health_monitor.py
核心健康檢查模組，提供：
- 檢查各排程器的最新更新時間
- 分析健康狀態 (healthy/warning/critical/error)
- 生成詳細的健康狀態報告
- 支援單次檢查

### 2. continuous_monitor.py
持續監控模組，提供：
- 定期自動執行健康檢查
- 智慧警報系統 (避免重複警報)
- 警報歷史記錄管理
- 可配置的檢查間隔和警報設定

### 3. web_dashboard.py
Web 監控儀表板，提供：
- 即時查看排程器狀態
- 圖形化介面顯示健康狀態
- 自動刷新功能
- RESTful API 介面

### 4. test_monitoring.py
系統測試模組，提供：
- 完整的監控系統測試
- 資料庫連接測試
- 功能驗證測試

### 5. start_monitoring.py
啟動腳本，提供：
- 統一的啟動介面
- 互動式選單
- 命令行參數支援

## 快速開始

### 方法1: 使用啟動腳本 (推薦)
```bash
# 互動式選單
python start_monitoring.py

# 單次健康檢查
python start_monitoring.py --check

# 持續監控 (30分鐘間隔)
python start_monitoring.py --monitor

# 持續監控 (自定義間隔)
python start_monitoring.py --monitor --interval 15

# 啟動Web儀表板
python start_monitoring.py --web

# 自定義端口的Web儀表板
python start_monitoring.py --web --port 8080

# 執行系統測試
python start_monitoring.py --test
```

### 方法2: 直接使用個別模組
```bash
# 單次健康檢查
python scheduler_health_monitor.py

# 持續監控
python continuous_monitor.py --interval 30

# 單次檢查不進入持續模式
python continuous_monitor.py --once

# Web儀表板
python web_dashboard.py --port 5000

# 系統測試
python test_monitoring.py
```

## 健康狀態說明

### 狀態等級
- **healthy**: 排程器運行正常
- **warning**: 有輕微問題但不影響基本功能
- **critical**: 有嚴重問題需要立即處理
- **error**: 系統錯誤，無法判斷狀態

### 判斷標準
- **每日任務**: 檢查是否在預期時間的容忍範圍內執行
- **每週任務**: 檢查本週是否執行
- **每月任務**: 檢查本月是否執行
- **記錄數量**: 檢查最近24小時是否有新記錄

## 警報系統

### 警報觸發條件
- **嚴重問題**: 立即發送警報
- **警告問題**: 持續2小時後發送警報

### 警報限制
- 每個排程器最多發送5次警報
- 警報冷卻時間4小時
- 自動清理7天前的警報記錄

### 警報方式
- 控制台輸出
- 日誌記錄
- 可擴展到郵件、Slack等

## 報告系統

### 健康狀態報告
- 自動生成詳細的健康狀態報告
- 包含統計資訊、詳細狀態、修復建議
- 保存到 `reports/` 目錄
- 支援文本格式，易於閱讀和分享

### 報告內容
1. 總體統計資訊
2. 按分類分組的詳細狀態
3. 問題診斷和修復建議
4. 時間戳和版本資訊

## Web 儀表板

### 功能特色
- 即時顯示所有排程器狀態
- 彩色狀態指示器
- 自動30秒刷新
- 響應式設計，支援手機瀏覽
- RESTful API 支援

### 訪問方式
- 預設地址: http://localhost:5000
- API端點: http://localhost:5000/api/status
- 健康檢查: http://localhost:5000/api/health

## 設定檔

### 資料庫配置
系統使用 `config.py` 中的統一資料庫配置：
```python
{
    'host': '26.210.160.206',
    'port': '5433',
    'database': '988',
    'user': 'n8n',
    'password': '1234'
}
```

### 排程器配置
在 `scheduler_health_monitor.py` 中的 `scheduler_configs` 字典中配置：
- 排程器名稱和描述
- 對應的資料庫表格
- 時間欄位
- 執行頻率和預期時間
- 容忍範圍

## 日誌系統

### 日誌位置
- 健康監控: `logs/scheduler_health_YYYYMM.log`
- 持續監控: `logs/continuous_monitor_YYYYMM.log`

### 日誌等級
- INFO: 一般資訊
- WARNING: 警報資訊
- ERROR: 錯誤資訊

## 疑難排解

### 常見問題

1. **Unicode編碼錯誤**
   - 確保終端支援UTF-8編碼
   - 在Windows上可能需要設定環境變數 `PYTHONIOENCODING=utf-8`

2. **資料庫連接失敗**
   - 檢查網路連接
   - 確認資料庫配置正確
   - 檢查防火牆設定

3. **表格不存在錯誤**
   - 確認資料庫中存在對應的表格
   - 檢查表格名稱是否正確

4. **權限錯誤**
   - 確認資料庫用戶有讀取權限
   - 檢查檔案系統寫入權限

### 除錯方式

1. **執行系統測試**
   ```bash
   python test_monitoring.py
   ```

2. **檢查日誌檔案**
   ```bash
   # 查看最新的日誌
   tail -f logs/scheduler_health_*.log
   ```

3. **單獨測試資料庫連接**
   ```bash
   python -c "
   from scheduler_health_monitor import SchedulerHealthMonitor
   monitor = SchedulerHealthMonitor()
   conn = monitor.get_connection()
   print('連接成功' if conn else '連接失敗')
   "
   ```

## 擴展功能

### 添加新的排程器
1. 在 `scheduler_configs` 中添加配置
2. 確保對應的資料庫表格存在
3. 測試新配置

### 自定義警報方式
1. 繼承 `ContinuousMonitor` 類
2. 覆寫 `send_alert` 方法
3. 實作新的警報邏輯

### 自定義報告格式
1. 繼承 `SchedulerHealthMonitor` 類
2. 覆寫 `generate_health_report` 方法
3. 實作新的報告格式

## 維護建議

### 定期檢查
- 每日檢查健康狀態報告
- 每週檢查警報歷史
- 每月清理舊日誌檔案

### 監控指標
- 健康排程器數量/總數比例
- 平均延遲時間
- 警報頻率

### 性能優化
- 定期清理舊報告檔案
- 調整檢查間隔時間
- 優化資料庫查詢

## 技術支援

如有問題或建議，請檢查：
1. 日誌檔案中的錯誤資訊
2. 系統測試結果
3. 資料庫連接狀態

## 更新歷史

- v1.0.0: 初始版本，支援基本健康檢查和警報功能
- 包含完整的Web介面和持續監控功能
- 支援多種啟動方式和配置選項