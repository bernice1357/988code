#!/usr/bin/env python3
"""
簡化版排程系統 - 用於測試和隔離問題
"""

import logging
import schedule
import threading
import time
from datetime import datetime
from task_executor import execute_task
import psycopg2
# 導入統一配置
from config import DatabaseConfig, LoggingConfig, get_db_config

class SimpleScheduler:
    """簡化排程管理系統"""
    
    def __init__(self):
        self.setup_logging()
        self.schedule_enabled = {
            'restock': True,
            'sales': True,
            'recommendation': True,
            'customer_management': True
        }
        self.running = False
        self.scheduler_thread = None
        
        # 資料庫配置（使用統一配置）
        self.db_config = get_db_config()
        
    def setup_logging(self):
        """設置日誌（使用統一配置）"""
        logging.basicConfig(
            level=getattr(logging, LoggingConfig.LOG_LEVEL),
            format=LoggingConfig.LOG_FORMAT
        )
        self.logger = logging.getLogger('SimpleScheduler')
        
    def is_category_enabled(self, category):
        """檢查排程分類是否啟用"""
        return self.schedule_enabled.get(category, True)
    
    def execute_task_with_logging(self, task_id, category):
        """執行任務並記錄結果"""
        if not self.is_category_enabled(category):
            self.logger.info(f"Skipping {task_id} - category {category} is disabled")
            return
        
        self.logger.info(f"Starting scheduled task: {task_id}")
        
        try:
            result = execute_task(task_id)
            success = result.get('success', False)
            message = result.get('message', f"Task {task_id} completed")
            self.logger.info(f"Task {task_id} completed: {'success' if success else 'failed'}")
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {str(e)}")
    
    def setup_schedules(self):
        """設定排程任務"""
        schedule.clear()
        
        # 補貨排程 (restock)
        schedule.every().saturday.at("08:00").do(
            self.execute_task_with_logging, "prophet_training", "restock"
        )
        schedule.every().day.at("22:00").do(
            self.execute_task_with_logging, "daily_prediction", "restock"
        )
        
        # 簡化版只設定幾個主要任務
        self.logger.info("Simple schedule setup completed")
    
    def start_scheduler(self):
        """啟動排程器"""
        if self.running:
            return
        
        self.running = True
        self.setup_schedules()
        
        def run_scheduler():
            self.logger.info("Simple scheduler started")
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Scheduler error: {e}")
                    time.sleep(5)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
    def stop_scheduler(self):
        """停止排程器"""
        self.running = False
        schedule.clear()
    
    def refresh_schedule_states(self):
        """刷新排程狀態"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT category, enabled FROM schedule_settings")
                    for category, enabled in cursor.fetchall():
                        self.schedule_enabled[category] = enabled
            self.logger.info("Schedule states refreshed")
        except Exception as e:
            self.logger.error(f"Failed to refresh schedule states: {e}")
    
    def get_next_jobs(self):
        """獲取下次執行的任務"""
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                'job': str(job.job_func),
                'next_run': job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else None
            })
        return jobs

# 全域簡化排程器實例
simple_scheduler = SimpleScheduler()

if __name__ == "__main__":
    print("Testing simple scheduler...")
    simple_scheduler.start_scheduler()
    time.sleep(5)
    simple_scheduler.stop_scheduler()
    print("Simple scheduler test completed")