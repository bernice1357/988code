#!/usr/bin/env python3
"""
排程控制服務
提供API接口與實際排程系統之間的橋樑
"""

import os
import sys
import time
import threading
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# 導入排程系統
from scheduler import PredictionScheduler
# 導入統一配置
from config import DatabaseConfig, LoggingConfig, get_db_config

class ScheduleController:
    """排程控制器"""
    
    def __init__(self):
        self.scheduler = PredictionScheduler()
        self.running = False
        self.thread = None
        
        # 資料庫配置（使用統一配置）
        self.db_config = get_db_config()
        
        # 任務映射
        self.task_map = {
            "prophet_training": self.scheduler.saturday_training_job,
            "daily_prediction": self.scheduler.daily_prediction_job,
            "trigger_health_check": self.scheduler.daily_trigger_health_check_job,
            "sales_change_check": self.scheduler.daily_sales_change_job,
            "monthly_prediction": self.scheduler.monthly_sales_prediction_job,
            "monthly_sales_reset": self.scheduler.monthly_sales_change_reset_job,
            "weekly_recommendation": self.scheduler.weekly_recommendation_job,
            "inactive_customer_check": self.scheduler.daily_inactive_customer_job,
            "repurchase_reminder": self.scheduler.daily_repurchase_reminder_job
        }
        
        self.setup_logging()
        
    def setup_logging(self):
        """設定日誌（使用統一配置）"""
        os.makedirs(LoggingConfig.LOG_DIR, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, LoggingConfig.LOG_LEVEL),
            format=LoggingConfig.LOG_FORMAT,
            handlers=[
                logging.FileHandler(LoggingConfig.get_log_file_path('schedule_controller'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            self.logger.error(f"資料庫連接失敗: {e}")
            return None
    
    def is_schedule_enabled(self, category: str) -> bool:
        """檢查排程是否啟用"""
        conn = self.get_db_connection()
        if not conn:
            return True  # 預設啟用
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT enabled FROM schedule_settings WHERE category = %s", (category,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result[0] if result else True
        except Exception as e:
            self.logger.error(f"檢查排程狀態失敗: {e}")
            return True
    
    def log_task_execution(self, task_id: str, task_name: str, category: str, 
                          status: str, message: str = None, duration: int = None):
        """記錄任務執行"""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schedule_history (task_id, task_name, category, status, message, duration_seconds)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (task_id, task_name, category, status, message, duration))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.logger.error(f"記錄任務執行失敗: {e}")
    
    def execute_task_with_logging(self, task_id: str, task_name: str, category: str, task_func):
        """執行任務並記錄結果"""
        start_time = datetime.now()
        self.logger.info(f"開始執行任務: {task_name} ({task_id})")
        
        # 記錄開始執行
        self.log_task_execution(task_id, task_name, category, "running", "任務開始執行")
        
        try:
            # 執行任務
            success = task_func()
            
            # 計算執行時間
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            # 記錄結果
            status = "success" if success else "failed"
            message = f"任務執行{'成功' if success else '失敗'}"
            
            self.log_task_execution(task_id, task_name, category, status, message, duration)
            self.logger.info(f"任務 {task_name} 執行完成，狀態: {status}，耗時: {duration}秒")
            
            return success
            
        except Exception as e:
            # 執行失敗
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            error_message = f"任務執行異常: {str(e)}"
            self.log_task_execution(task_id, task_name, category, "error", error_message, duration)
            self.logger.error(f"任務 {task_name} 執行異常: {e}")
            
            return False
    
    def execute_manual_task(self, task_id: str) -> Dict[str, Any]:
        """手動執行任務"""
        if task_id not in self.task_map:
            return {"success": False, "message": f"未知的任務ID: {task_id}"}
        
        # 任務配置映射
        task_configs = {
            "prophet_training": {"name": "Prophet模型訓練", "category": "restock"},
            "daily_prediction": {"name": "每日預測生成", "category": "restock"},
            "trigger_health_check": {"name": "觸發器健康檢查", "category": "restock"},
            "sales_change_check": {"name": "銷量變化檢查", "category": "sales"},
            "monthly_prediction": {"name": "月銷售預測", "category": "sales"},
            "monthly_sales_reset": {"name": "銷量重置", "category": "sales"},
            "weekly_recommendation": {"name": "推薦系統更新", "category": "recommendation"},
            "inactive_customer_check": {"name": "不活躍客戶檢查", "category": "customer_management"},
            "repurchase_reminder": {"name": "回購提醒維護", "category": "customer_management"}
        }
        
        config = task_configs.get(task_id)
        if not config:
            return {"success": False, "message": f"任務配置不存在: {task_id}"}
        
        # 檢查排程是否啟用
        if not self.is_schedule_enabled(config["category"]):
            return {"success": False, "message": f"排程 {config['category']} 已停用"}
        
        # 執行任務
        start_time = datetime.now()
        success = self.execute_task_with_logging(
            task_id, 
            config["name"], 
            config["category"], 
            self.task_map[task_id]
        )
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        
        return {
            "success": success,
            "message": f"任務 {config['name']} {'執行成功' if success else '執行失敗'}",
            "duration_seconds": duration
        }
    
    def start_monitoring(self):
        """啟動監控服務"""
        if self.running:
            return {"success": False, "message": "服務已在運行中"}
        
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("排程監控服務已啟動")
        return {"success": True, "message": "排程監控服務已啟動"}
    
    def stop_monitoring(self):
        """停止監控服務"""
        if not self.running:
            return {"success": False, "message": "服務未在運行"}
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        self.logger.info("排程監控服務已停止")
        return {"success": True, "message": "排程監控服務已停止"}
    
    def _monitoring_loop(self):
        """監控循環"""
        self.logger.info("開始排程監控循環")
        
        while self.running:
            try:
                # 這裡可以添加定期檢查邏輯
                # 例如檢查排程狀態、清理過期記錄等
                time.sleep(60)  # 每分鐘檢查一次
                
            except Exception as e:
                self.logger.error(f"監控循環異常: {e}")
                time.sleep(10)  # 出錯時短暫休息
    
    def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "running": self.running,
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "start_time": getattr(self, 'start_time', None)
        }

def main():
    """主函數"""
    print("=== 排程控制服務 ===")
    print("1. 啟動監控服務")
    print("2. 手動執行任務")
    print("3. 查看服務狀態")
    print("4. 停止服務")
    print("0. 退出")
    
    controller = ScheduleController()
    
    while True:
        try:
            choice = input("\n請選擇操作: ").strip()
            
            if choice == "0":
                if controller.running:
                    controller.stop_monitoring()
                print("再見！")
                break
                
            elif choice == "1":
                result = controller.start_monitoring()
                print(result["message"])
                
            elif choice == "2":
                print("\n可執行的任務:")
                for i, task_id in enumerate(controller.task_map.keys(), 1):
                    print(f"{i}. {task_id}")
                
                try:
                    task_index = int(input("選擇任務編號: ")) - 1
                    task_ids = list(controller.task_map.keys())
                    
                    if 0 <= task_index < len(task_ids):
                        task_id = task_ids[task_index]
                        print(f"執行任務: {task_id}")
                        result = controller.execute_manual_task(task_id)
                        print(f"結果: {result['message']}")
                        if 'duration_seconds' in result:
                            print(f"耗時: {result['duration_seconds']}秒")
                    else:
                        print("無效的任務編號")
                        
                except ValueError:
                    print("請輸入有效的數字")
                    
            elif choice == "3":
                status = controller.get_service_status()
                print(f"服務狀態: {'運行中' if status['running'] else '已停止'}")
                print(f"監控線程: {'活躍' if status['thread_alive'] else '非活躍'}")
                
            elif choice == "4":
                result = controller.stop_monitoring()
                print(result["message"])
                
            else:
                print("無效選項")
                
        except KeyboardInterrupt:
            if controller.running:
                controller.stop_monitoring()
            print("\n\n程式已停止")
            break
        except Exception as e:
            print(f"操作異常: {e}")

if __name__ == "__main__":
    main()