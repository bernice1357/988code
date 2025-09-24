#!/usr/bin/env python3
"""
整合排程系統
結合 Web API 控制與自動定時排程功能
"""

import os
import time
import logging
import schedule
import threading
import pytz
from datetime import datetime, timedelta
from task_executor import execute_task
# from database_integration import DatabaseIntegration  # 暫時註解掉
import psycopg2

class IntegratedScheduler:
    """整合排程管理系統"""
    
    def __init__(self):
        # self.db_integration = DatabaseIntegration()  # 暫時註解掉
        self.setup_logging()
        self.schedule_enabled = {}
        self.running = False
        self.scheduler_thread = None
        
        # 資料庫配置
        self.db_config = {
            'host': 'localhost',
            'port': '5432',
            'database': '988',
            'user': 'postgres',
            'password': '1234'
        }
        
        # 載入排程狀態
        self.load_schedule_states()
        
    def setup_logging(self):
        """設置日誌"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'integrated_scheduler_{datetime.now().strftime("%Y%m")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('IntegratedScheduler')
        
    def load_schedule_states(self):
        """從資料庫載入排程開關狀態"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT category, enabled FROM schedule_settings")
                    for category, enabled in cursor.fetchall():
                        self.schedule_enabled[category] = enabled
            
            self.logger.info(f"Loaded schedule states: {self.schedule_enabled}")
        except Exception as e:
            self.logger.error(f"Failed to load schedule states: {e}")
            # 預設全部啟用
            self.schedule_enabled = {
                'restock': True,
                'sales': True,
                'recommendation': True,
                'customer_management': True
            }
    
    def is_category_enabled(self, category):
        """檢查排程分類是否啟用"""
        return self.schedule_enabled.get(category, True)
    
    def execute_task_with_logging(self, task_id, category):
        """執行任務並記錄結果"""
        if not self.is_category_enabled(category):
            self.logger.info(f"Skipping {task_id} - category {category} is disabled")
            return
        
        self.logger.info(f"Starting scheduled task: {task_id}")
        start_time = datetime.now()
        
        try:
            # 記錄任務開始
            self.record_task_execution(task_id, category, "running", "Scheduled execution started")
            
            # 執行任務
            result = execute_task(task_id)
            
            # 記錄結果
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            success = result.get('success', False)
            message = result.get('message', f"Task {task_id} completed")
            
            status = "success" if success else "failed"
            self.record_task_execution(task_id, category, status, message, duration)
            
            self.logger.info(f"Task {task_id} completed: {status} in {duration}s")
            
        except Exception as e:
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            error_msg = f"Task {task_id} failed: {str(e)}"
            
            self.record_task_execution(task_id, category, "failed", error_msg, duration)
            self.logger.error(error_msg)
    
    def record_task_execution(self, task_id, category, status, message, duration=None):
        """記錄任務執行到資料庫"""
        try:
            # 獲取任務名稱
            task_names = {
                "daily_prediction": "每日預測生成",
                "weekly_model_training": "週度模型訓練", 
                "trigger_health_check": "觸發器健康檢查",
                "sales_change_check": "銷量變化檢查",
                "monthly_prediction": "月銷售預測",
                "monthly_sales_reset": "銷量重置",
                "weekly_recommendation": "推薦系統更新",
                "inactive_customer_check": "不活躍客戶檢查",
                "repurchase_reminder": "回購提醒維護"
            }
            
            task_name = task_names.get(task_id, task_id)
            
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO schedule_history (task_id, task_name, category, status, message, duration_seconds)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (task_id, task_name, category, status, message, duration))
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to record task execution: {e}")
    
    def setup_schedules(self):
        """設定排程任務 (時間與 schedule_api.py 同步)"""
        # 清除所有現有排程
        schedule.clear()
        
        # 補貨排程 (restock)
        schedule.every().saturday.at("08:00").do(
            self.execute_task_with_logging, "weekly_model_training", "restock"
        )
        schedule.every().day.at("22:00").do(
            self.execute_task_with_logging, "daily_prediction", "restock"
        )
        schedule.every().day.at("02:00").do(
            self.execute_task_with_logging, "trigger_health_check", "restock"
        )
        
        # 銷售排程 (sales)
        schedule.every().day.at("00:30").do(
            self.execute_task_with_logging, "monthly_sales_reset", "sales"
        )
        schedule.every().day.at("01:00").do(
            self.execute_task_with_logging, "monthly_prediction", "sales"
        )
        schedule.every().day.at("06:00").do(
            self.execute_task_with_logging, "sales_change_check", "sales"
        )
        
        # 推薦排程 (recommendation)
        schedule.every().sunday.at("08:00").do(
            self.execute_task_with_logging, "weekly_recommendation", "recommendation"
        )
        
        # 客戶管理排程 (customer_management)
        schedule.every().day.at("02:30").do(
            self.execute_task_with_logging, "inactive_customer_check", "customer_management"
        )
        schedule.every().day.at("04:00").do(
            self.execute_task_with_logging, "repurchase_reminder", "customer_management"
        )
        
        self.logger.info("Schedule setup completed with updated times:")
        self.logger.info("- Monthly 1st 00:30: Sales reset")
        self.logger.info("- Monthly 1st 01:00: Monthly prediction")
        self.logger.info("- Saturday 08:00: Weekly model training (UTC+8)")
        self.logger.info("- Daily 02:00: Trigger health check")
        self.logger.info("- Daily 02:30: Inactive customer check")
        self.logger.info("- Daily 04:00: Repurchase reminder")
        self.logger.info("- Daily 06:00: Sales change check")
        self.logger.info("- Daily 22:00: CatBoost daily prediction (use trained model)")
        self.logger.info("- Sunday 08:00: Weekly recommendation")
    
    def refresh_schedule_states(self):
        """刷新排程狀態"""
        self.load_schedule_states()
        self.logger.info("Schedule states refreshed")
    
    def start_scheduler(self):
        """啟動排程器"""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.setup_schedules()
        
        def run_scheduler():
            self.logger.info("Integrated scheduler started")
            while self.running:
                try:
                    # 每分鐘刷新一次排程狀態
                    if datetime.now().second == 0:
                        self.refresh_schedule_states()
                    
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Scheduler error: {e}")
                    time.sleep(5)
            
            self.logger.info("Integrated scheduler stopped")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
    def stop_scheduler(self):
        """停止排程器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        self.logger.info("Scheduler stopped")
    
    def get_next_jobs(self):
        """獲取下次執行的任務"""
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                'job': str(job.job_func),
                'next_run': job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else None
            })
        return jobs

# 全域排程器實例
integrated_scheduler = IntegratedScheduler()

def start_integrated_scheduler():
    """啟動整合排程器"""
    integrated_scheduler.start_scheduler()

def stop_integrated_scheduler():
    """停止整合排程器"""
    integrated_scheduler.stop_scheduler()

if __name__ == "__main__":
    try:
        start_integrated_scheduler()
        print("Integrated scheduler is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping integrated scheduler...")
        stop_integrated_scheduler()
        print("Scheduler stopped.")