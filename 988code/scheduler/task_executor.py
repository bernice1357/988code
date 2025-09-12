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
            "daily_prediction": self.execute_daily_prediction,
            "weekly_model_training": self.execute_weekly_model_training,
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
    
    
    def execute_daily_prediction(self):
        """執行每日預測（使用優化後的模型配置）"""
        try:
            import os
            import subprocess
            
            # 直接在 ml_system 目錄中執行預測腳本
            current_dir = os.path.dirname(__file__)
            ml_system_dir = os.path.join(current_dir, 'ml_system')
            
            logging.info("=== 執行每日預測 (優化配置) ===")
            
            # 創建臨時腳本來執行預測
            script_content = '''
from model_service import CatBoostPredictor
from config import MLConfig

predictor = CatBoostPredictor()
result = predictor.daily_prediction_process()

if result:
    print("PREDICTION_SUCCESS")
    print(f"THRESHOLD:{MLConfig.PREDICTION_THRESHOLD}")
    print(f"WEIGHTS:{MLConfig.CATBOOST_PARAMS['class_weights']}")
else:
    print("PREDICTION_FAILED")
'''
            
            script_path = os.path.join(ml_system_dir, 'temp_daily_prediction.py')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            try:
                # 在 ml_system 目錄中執行預測
                result = subprocess.run([
                    'python', 'temp_daily_prediction.py'
                ], cwd=ml_system_dir, capture_output=True, text=True, timeout=300)
                
                # 清理臨時文件
                if os.path.exists(script_path):
                    os.remove(script_path)
                
                if result.returncode == 0:
                    output_lines = result.stdout.strip().split('\n')
                    if 'PREDICTION_SUCCESS' in output_lines:
                        threshold_line = [line for line in output_lines if line.startswith('THRESHOLD:')]
                        weights_line = [line for line in output_lines if line.startswith('WEIGHTS:')]
                        
                        config_info = {}
                        if threshold_line:
                            config_info['threshold'] = threshold_line[0].split(':', 1)[1]
                        if weights_line:
                            config_info['weights'] = weights_line[0].split(':', 1)[1]
                        
                        logging.info("每日預測執行成功")
                        return {
                            "status": "completed", 
                            "message": "CatBoost每日預測完成", 
                            "config": config_info
                        }
                    else:
                        logging.error("預測執行失敗")
                        return {"status": "failed", "message": "CatBoost每日預測失敗"}
                else:
                    logging.error(f"預測執行出錯: {result.stderr}")
                    return {"status": "failed", "message": f"預測執行錯誤: {result.stderr[:100]}"}
                    
            except subprocess.TimeoutExpired:
                logging.error("預測執行超時")
                return {"status": "failed", "message": "預測執行超時"}
            except Exception as e:
                logging.error(f"執行預測時發生錯誤: {e}")
                return {"error": str(e)}
                    
        except Exception as e:
            logging.error(f"CatBoost每日預測錯誤: {e}")
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
        """執行月銷售預測（僅在每月1號執行）"""
        try:
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            from tasks.monthly_prediction import MonthlyPredictionDB
            
            # 檢查是否為每月1號
            current_date = datetime.now().date()
            if current_date.day != 1:
                logging.info(f"今天是 {current_date}，不是月初，跳過月銷售預測")
                return {"status": "skipped", "message": f"非月初日期({current_date})，月銷售預測已跳過"}
            
            logging.info(f"月初執行月銷售預測: {current_date}")
            
            # 導入本地的混合CV優化預測系統
            from tasks.hybrid_cv_system import HybridCVOptimizedSystem
            
            # Use unified config
            db_config = get_db_config()
            
            current_time = datetime.now()
            current_month = current_time  # 預測當月而不是下月
            
            # Create prediction system
            monthly_system = HybridCVOptimizedSystem(db_config, prediction_month=current_month)
            monthly_db = MonthlyPredictionDB(db_config)
            
            # Execute prediction
            logging.info(f"Executing monthly prediction for {current_month.strftime('%Y-%m')} (當月預測)")
            subcategory_df, sku_df = monthly_system.run_prediction()
            
            if subcategory_df is None:
                return {"status": "failed", "message": "Monthly prediction execution failed"}
            
            # Upload to database
            batch_id = f"monthly_{current_month.strftime('%Y%m%d')}_{current_time.strftime('%H%M%S')}"
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
        """執行銷量重置（僅在每月1號執行）"""
        try:
            from datetime import datetime
            from tasks.sales_change import SalesChangeManager
            
            # 檢查是否為每月1號
            current_date = datetime.now().date()
            if current_date.day != 1:
                logging.info(f"今天是 {current_date}，不是月初，跳過銷量重置")
                return {"status": "skipped", "message": f"非月初日期({current_date})，銷量重置已跳過"}
            
            logging.info(f"月初執行銷量重置: {current_date}")
            
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
    
    def execute_weekly_model_training(self):
        """執行週度模型訓練 - 使用優化的TwoStageCatBoostTrainer"""
        try:
            import sys
            import os
            
            # 確保能找到 ml_system 模組
            current_dir = os.path.dirname(__file__)
            ml_system_dir = os.path.join(current_dir, 'ml_system')
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            if ml_system_dir not in sys.path:
                sys.path.insert(0, ml_system_dir)
            
            # 添加 ml_system 到 sys.path 並直接導入
            sys.path.insert(0, ml_system_dir)
            
            from two_stage_trainer import TwoStageCatBoostTrainer
            from model_manager import ModelManager
            
            # 導入 MLConfig - 使用完整模組路徑
            import importlib.util
            config_path = os.path.join(ml_system_dir, 'config.py')
            spec = importlib.util.spec_from_file_location("ml_config", config_path)
            ml_config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ml_config_module)
            MLConfig = ml_config_module.MLConfig
            
            # 使用統一配置
            db_config = get_db_config()
            
            # 記錄優化配置
            logging.info("=== 週度模型訓練 (優化配置) ===")
            logging.info(f"預測閾值: {MLConfig.PREDICTION_THRESHOLD}")
            logging.info(f"類別權重: {MLConfig.CATBOOST_PARAMS['class_weights']}")
            logging.info("使用TwoStageCatBoostTrainer進行真實前瞻性預測訓練")
            
            trainer = TwoStageCatBoostTrainer()
            
            # 使用優化的兩段式訓練
            logging.info("開始優化的兩段式模型訓練")
            training_success = trainer.train_with_real_prediction()
            
            if training_success and hasattr(trainer, 'prediction_metrics'):
                # 獲取優化後的性能指標
                metrics = trainer.prediction_metrics
                f1_score = metrics.get('f1_score', 0)
                precision = metrics.get('precision', 0)
                recall = metrics.get('recall', 0)
                tp = metrics.get('true_positives', 0)
                fp = metrics.get('false_positives', 0)
                fn = metrics.get('false_negatives', 0)
                
                result_message = f"優化模型訓練完成: F1={f1_score:.3f}, P={precision:.3f}, R={recall:.3f}, TP={tp}, FP={fp}, FN={fn}"
                
                # 模型管理與清理
                try:
                    manager = ModelManager()
                    manager.cleanup_old_models(keep_count=3)
                except Exception as e:
                    logging.warning(f"Model cleanup failed: {e}")
                
                return {
                    "status": "completed", 
                    "message": result_message,
                    "metrics": metrics,
                    "config": {
                        "threshold": MLConfig.PREDICTION_THRESHOLD,
                        "weights": MLConfig.CATBOOST_PARAMS['class_weights']
                    },
                    "validation_method": "real_forward_prediction",
                    "no_data_leakage": True,
                    "optimized": True
                }
            else:
                return {"status": "failed", "message": "優化模型訓練失敗"}
                
        except Exception as e:
            logging.error(f"週度優化模型訓練錯誤: {e}")
            return {"error": str(e)}
        finally:
            # 清理 sys.path
            if ml_system_dir in sys.path:
                sys.path.remove(ml_system_dir)

# 創建全域執行器實例
task_executor = TaskExecutor()

def execute_task(task_id: str) -> dict:
    """全域任務執行函數"""
    return task_executor.execute_task(task_id)