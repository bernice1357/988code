"""
任務執行器模組
連接 API 任務 ID 與實際執行函數
"""

import logging
from datetime import datetime
import sys
import os

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(__file__))

# 導入統一配置
from config import DatabaseConfig, LoggingConfig, get_db_config

# 任務模組將在執行時動態導入以避免循環導入問題

# 設置日誌（使用統一配置）
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LOG_LEVEL),
    format=LoggingConfig.LOG_FORMAT
)

class TaskExecutor:
    """任務執行器類"""
    
    def __init__(self):
        self.task_map = {
            # 補貨排程 (restock)
            "prophet_training": self.execute_prophet_training,
            "daily_prediction": self.execute_daily_prediction,
            "trigger_health_check": self.execute_trigger_health_check,
            
            # 銷售排程 (sales)
            "sales_change_check": self.execute_sales_change_check,
            "monthly_prediction": self.execute_monthly_prediction,
            "monthly_sales_reset": self.execute_monthly_sales_reset,
            
            # 推薦排程 (recommendation)
            "weekly_recommendation": self.execute_weekly_recommendation,
            
            # 客戶管理排程 (customer_management)
            "inactive_customer_check": self.execute_inactive_customer_check,
            "repurchase_reminder": self.execute_repurchase_reminder,
        }
    
    def execute_task(self, task_id: str) -> dict:
        """執行指定的任務"""
        if task_id not in self.task_map:
            return {
                "success": False,
                "message": f"Unknown task ID: {task_id}",
                "duration": 0
            }
        
        start_time = datetime.now()
        logging.info(f"Starting task: {task_id}")
        
        try:
            # 執行任務
            result = self.task_map[task_id]()
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            logging.info(f"Task {task_id} completed in {duration} seconds")
            
            return {
                "success": True,
                "message": f"Task {task_id} completed successfully",
                "duration": duration,
                "result": result
            }
            
        except Exception as e:
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            error_msg = f"Task {task_id} failed: {str(e)}"
            
            logging.error(error_msg)
            
            return {
                "success": False,
                "message": error_msg,
                "duration": duration,
                "error": str(e)
            }
    
    # 補貨排程任務
    def execute_prophet_training(self):
        """執行 Prophet 模型訓練"""
        try:
            from tasks.prophet_system import ProphetPredictionSystem
            # ProphetPredictionSystem doesn't accept db_config parameter
            system = ProphetPredictionSystem()
            return system.saturday_model_training()
        except Exception as e:
            logging.error(f"Prophet training error: {e}")
            return {"error": str(e)}
    
    def execute_daily_prediction(self):
        """執行每日預測生成"""
        try:
            from tasks.prophet_system import ProphetPredictionSystem
            
            # ProphetPredictionSystem doesn't accept db_config parameter
            system = ProphetPredictionSystem()
            
            # Load trained models first
            if not system.load_latest_models():
                return {"status": "failed", "message": "Failed to load Prophet models"}
            
            # Generate predictions
            result = system.generate_daily_predictions(prediction_days=7)
            
            if result is None:
                return {"status": "failed", "message": "Daily prediction generation failed"}
            
            return {"status": "completed", "message": "Daily prediction completed successfully"}
        except Exception as e:
            logging.error(f"Daily prediction error: {e}")
            return {"error": str(e)}
    
    def execute_trigger_health_check(self):
        """執行觸發器健康檢查"""
        try:
            from tasks.trigger_health import TriggerHealthMonitor
            
            # 使用統一配置
            db_config = get_db_config()
            
            monitor = TriggerHealthMonitor(db_config)
            result = monitor.run_complete_health_check()
            return {"status": "completed", "message": "Trigger health check completed", "result": result}
        except Exception as e:
            logging.error(f"Trigger health check error: {e}")
            return {"error": str(e)}
    
    # 銷售排程任務
    def execute_sales_change_check(self):
        """執行銷量變化檢查"""
        try:
            from tasks.sales_change import SalesChangeManager
            
            # Use unified config
            db_config = get_db_config()
            
            manager = SalesChangeManager(db_config)
            manager.daily_consistency_check()
            return {"status": "completed", "message": "Sales change check completed"}
        except Exception as e:
            logging.error(f"Sales change check error: {e}")
            return {"error": str(e)}
    
    def execute_monthly_prediction(self):
        """執行月銷售預測"""
        try:
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            from tasks.monthly_prediction import MonthlyPredictionDB
            
            # Add predict_product_main to path
            import sys
            import os
            predict_main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'predict_product_main'))
            if predict_main_path not in sys.path:
                sys.path.insert(0, predict_main_path)
            
            from hybrid_cv_optimized_system import HybridCVOptimizedSystem
            
            # Use unified config
            db_config = get_db_config()
            
            current_time = datetime.now()
            next_month = current_time + relativedelta(months=1)
            
            # Create prediction system
            monthly_system = HybridCVOptimizedSystem(db_config, prediction_month=next_month)
            monthly_db = MonthlyPredictionDB(db_config)
            
            # Execute prediction
            logging.info(f"Executing monthly prediction for {next_month.strftime('%Y-%m')}")
            subcategory_df, sku_df = monthly_system.run_prediction()
            
            if subcategory_df is None:
                return {"status": "failed", "message": "Monthly prediction execution failed"}
            
            # Upload to database
            batch_id = f"monthly_{next_month.strftime('%Y%m%d')}_{current_time.strftime('%H%M%S')}"
            upload_success = monthly_db.save_predictions(subcategory_df, sku_df, batch_id)
            
            result_msg = f"Prediction completed: {len(subcategory_df)} subcategories, {len(sku_df)} SKUs"
            if upload_success:
                result_msg += f", batch_id: {batch_id}"
            else:
                result_msg += " (database upload failed)"
                
            return {"status": "completed", "message": result_msg}
        except Exception as e:
            logging.error(f"Monthly prediction error: {e}")
            return {"error": str(e)}
    
    def execute_monthly_sales_reset(self):
        """執行銷量重置"""
        try:
            from tasks.sales_change import SalesChangeManager
            
            # Use unified config
            db_config = get_db_config()
            
            manager = SalesChangeManager(db_config)
            manager.monthly_reset()
            return {"status": "completed", "message": "Monthly sales reset completed"}
        except Exception as e:
            logging.error(f"Monthly sales reset error: {e}")
            return {"error": str(e)}
    
    # 推薦排程任務
    def execute_weekly_recommendation(self):
        """執行推薦系統更新"""
        try:
            from tasks.recommendation import generate_recommendations
            
            # Use unified config
            db_config = get_db_config()
            
            # Execute recommendation generation
            logging.info("Executing recommendation system update")
            customer_recs, product_recs = generate_recommendations(db_config)
            
            if customer_recs is None or product_recs is None:
                return {"status": "failed", "message": "Recommendation generation failed"}
            
            result_msg = f"Recommendation update completed: {len(customer_recs)} customer recs, {len(product_recs)} product recs"
            return {"status": "completed", "message": result_msg}
        except Exception as e:
            logging.error(f"Weekly recommendation error: {e}")
            return {"error": str(e)}
    
    # 客戶管理排程任務
    def execute_inactive_customer_check(self):
        """執行不活躍客戶檢查"""
        try:
            from tasks.inactive_customer import InactiveCustomerManager
            
            # Use unified config
            db_config = get_db_config()
            
            manager = InactiveCustomerManager(db_config)
            
            # Initialize system
            if not manager.initialize_system():
                return {"status": "failed", "message": "System initialization failed"}
            
            # Execute daily check
            success = manager.daily_check_inactive_customers()
            
            if success:
                stats = manager.get_statistics()
                result_msg = f"Inactive customer check completed: {stats.get('total_inactive', 0)} total"
                return {"status": "completed", "message": result_msg}
            else:
                return {"status": "failed", "message": "Inactive customer check failed"}
        except Exception as e:
            logging.error(f"Inactive customer check error: {e}")
            return {"error": str(e)}
    
    def execute_repurchase_reminder(self):
        """執行回購提醒維護"""
        try:
            from tasks.repurchase_reminder import RepurchaseReminder
            
            # Use unified config
            db_config = get_db_config()
            
            reminder = RepurchaseReminder(db_config)
            reminder.daily_repurchase_reminder_maintenance()
            
            return {"status": "completed", "message": "Repurchase reminder maintenance completed"}
        except Exception as e:
            logging.error(f"Repurchase reminder error: {e}")
            return {"error": str(e)}

# 創建全域執行器實例
task_executor = TaskExecutor()

def execute_task(task_id: str) -> dict:
    """全域任務執行函數"""
    return task_executor.execute_task(task_id)