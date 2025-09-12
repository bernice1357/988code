#!/usr/bin/env python3
"""
持續監控腳本
定期檢查排程器健康狀態並在發現問題時發送警報
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
import schedule
import threading
from typing import Dict, List, Optional

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(__file__))

from scheduler_health_monitor import SchedulerHealthMonitor

class ContinuousMonitor:
    """持續監控器"""
    
    def __init__(self, check_interval_minutes: int = 30):
        self.check_interval = check_interval_minutes
        self.monitor = SchedulerHealthMonitor()
        self.setup_logging()
        self.running = False
        self.monitor_thread = None
        
        # 警報設定
        self.alert_config = {
            "critical_immediate": True,  # 嚴重問題立即警報
            "warning_threshold_hours": 2,  # 警告狀態持續2小時後警報
            "max_alerts_per_scheduler": 5,  # 每個排程器最多發送5次警報
            "alert_cooldown_hours": 4  # 警報冷卻時間4小時
        }
        
        # 警報歷史記錄
        self.alert_history = {}
        self.load_alert_history()
        
    def setup_logging(self):
        """設置日誌"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'continuous_monitor_{datetime.now().strftime("%Y%m")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('ContinuousMonitor')
        
    def load_alert_history(self):
        """載入警報歷史記錄"""
        history_file = os.path.join(os.path.dirname(__file__), 'alert_history.json')
        
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.alert_history = json.load(f)
                    
                # 清理過期的警報記錄 (超過7天)
                cutoff_time = datetime.now().timestamp() - (7 * 24 * 3600)
                for scheduler_id in list(self.alert_history.keys()):
                    alerts = self.alert_history[scheduler_id]
                    alerts = [alert for alert in alerts if alert['timestamp'] > cutoff_time]
                    
                    if alerts:
                        self.alert_history[scheduler_id] = alerts
                    else:
                        del self.alert_history[scheduler_id]
                        
                self.save_alert_history()
                
        except Exception as e:
            self.logger.error(f"載入警報歷史記錄失敗: {e}")
            self.alert_history = {}
    
    def save_alert_history(self):
        """保存警報歷史記錄"""
        history_file = os.path.join(os.path.dirname(__file__), 'alert_history.json')
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存警報歷史記錄失敗: {e}")
    
    def should_send_alert(self, scheduler_id: str, status: str, issues: List[str]) -> bool:
        """判斷是否應該發送警報"""
        now = datetime.now().timestamp()
        
        # 檢查該排程器的警報歷史
        if scheduler_id not in self.alert_history:
            self.alert_history[scheduler_id] = []
        
        scheduler_alerts = self.alert_history[scheduler_id]
        
        # 檢查警報數量限制
        if len(scheduler_alerts) >= self.alert_config["max_alerts_per_scheduler"]:
            self.logger.info(f"排程器 {scheduler_id} 已達到最大警報數量限制")
            return False
        
        # 檢查冷卻時間
        cooldown_seconds = self.alert_config["alert_cooldown_hours"] * 3600
        recent_alerts = [alert for alert in scheduler_alerts 
                        if now - alert['timestamp'] < cooldown_seconds]
        
        if recent_alerts:
            self.logger.info(f"排程器 {scheduler_id} 仍在冷卻期內")
            return False
        
        # 嚴重問題立即警報
        if status == "critical" and self.alert_config["critical_immediate"]:
            return True
        
        # 警告狀態需要持續一定時間
        if status == "warning":
            warning_threshold_seconds = self.alert_config["warning_threshold_hours"] * 3600
            
            # 檢查是否有舊的警告記錄
            old_warnings = [alert for alert in scheduler_alerts 
                           if alert['status'] == 'warning' and 
                              now - alert['timestamp'] > warning_threshold_seconds]
            
            if old_warnings:
                return True
        
        return False
    
    def send_alert(self, scheduler_result: Dict):
        """發送警報"""
        scheduler_id = scheduler_result["scheduler_id"]
        status = scheduler_result["status"]
        issues = scheduler_result["issues"]
        
        try:
            # 記錄警報
            alert_record = {
                "timestamp": datetime.now().timestamp(),
                "status": status,
                "issues": issues,
                "scheduler_name": scheduler_result["name"],
                "last_update": scheduler_result["last_update"]
            }
            
            if scheduler_id not in self.alert_history:
                self.alert_history[scheduler_id] = []
            
            self.alert_history[scheduler_id].append(alert_record)
            self.save_alert_history()
            
            # 生成警報消息
            alert_msg = self.generate_alert_message(scheduler_result)
            
            # 發送警報 (這裡可以集成郵件、Slack、Teams等)
            self.logger.warning(f"警報發送: {alert_msg}")
            
            # 可以在這裡添加其他警報方式
            # self.send_email_alert(alert_msg)
            # self.send_slack_alert(alert_msg)
            
            print(f"[ALERT] {alert_msg}")
            
        except Exception as e:
            self.logger.error(f"發送警報失敗: {e}")
    
    def generate_alert_message(self, scheduler_result: Dict) -> str:
        """生成警報消息"""
        status_emoji = {
            "critical": "[CRITICAL]",
            "warning": "[WARNING]",
            "error": "[ERROR]"
        }
        
        emoji = status_emoji.get(scheduler_result["status"], "[ALERT]")
        
        msg = f"{emoji} 排程器警報\n"
        msg += f"排程器: {scheduler_result['name']} ({scheduler_result['scheduler_id']})\n"
        msg += f"狀態: {scheduler_result['status'].upper()}\n"
        msg += f"表格: {scheduler_result['table']}\n"
        msg += f"最後更新: {scheduler_result['last_update'] or '無記錄'}\n"
        msg += f"問題: {', '.join(scheduler_result['issues'])}\n"
        msg += f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return msg
    
    def check_and_alert(self):
        """執行檢查並發送必要的警報"""
        try:
            self.logger.info("開始執行排程器健康檢查")
            
            # 執行健康檢查
            results = self.monitor.check_all_schedulers()
            
            # 分析結果並發送警報
            alerts_sent = 0
            
            for result in results:
                status = result["status"]
                scheduler_id = result["scheduler_id"]
                
                # 只對有問題的排程器發送警報
                if status in ["critical", "warning", "error"]:
                    if self.should_send_alert(scheduler_id, status, result["issues"]):
                        self.send_alert(result)
                        alerts_sent += 1
            
            # 記錄檢查結果
            summary = {
                "total": len(results),
                "healthy": len([r for r in results if r["status"] == "healthy"]),
                "warning": len([r for r in results if r["status"] == "warning"]),
                "critical": len([r for r in results if r["status"] == "critical"]),
                "error": len([r for r in results if r["status"] == "error"]),
                "alerts_sent": alerts_sent
            }
            
            self.logger.info(f"健康檢查完成: {summary}")
            
            # 如果有嚴重問題，生成詳細報告
            if summary["critical"] > 0 or summary["error"] > 0:
                report = self.monitor.generate_health_report(results)
                report_file = self.monitor.save_report_to_file(report)
                self.logger.warning(f"發現嚴重問題，詳細報告: {report_file}")
                
        except Exception as e:
            self.logger.error(f"執行健康檢查時發生錯誤: {e}")
    
    def start_monitoring(self):
        """開始持續監控"""
        if self.running:
            self.logger.warning("監控已在運行中")
            return
        
        self.running = True
        
        def monitor_loop():
            self.logger.info(f"開始持續監控，檢查間隔: {self.check_interval} 分鐘")
            
            # 立即執行一次檢查
            self.check_and_alert()
            
            # 設定定期檢查
            schedule.every(self.check_interval).minutes.do(self.check_and_alert)
            
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # 每分鐘檢查一次是否有待執行的任務
                except Exception as e:
                    self.logger.error(f"監控循環錯誤: {e}")
                    time.sleep(60)
            
            self.logger.info("監控已停止")
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止持續監控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        schedule.clear()
        self.logger.info("監控已停止")
    
    def get_monitoring_status(self) -> Dict:
        """獲取監控狀態"""
        return {
            "running": self.running,
            "check_interval_minutes": self.check_interval,
            "alert_config": self.alert_config,
            "total_alerts_in_history": sum(len(alerts) for alerts in self.alert_history.values()),
            "next_check": schedule.next_run().strftime('%Y-%m-%d %H:%M:%S') if schedule.jobs else None
        }

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='排程器持續監控系統')
    parser.add_argument('--interval', type=int, default=30, 
                       help='檢查間隔時間(分鐘)，預設30分鐘')
    parser.add_argument('--once', action='store_true', 
                       help='只執行一次檢查，不進入持續監控模式')
    
    args = parser.parse_args()
    
    monitor = ContinuousMonitor(check_interval_minutes=args.interval)
    
    if args.once:
        # 單次檢查模式
        print("執行單次排程器健康檢查...")
        monitor.check_and_alert()
        print("檢查完成。")
    else:
        # 持續監控模式
        try:
            monitor.start_monitoring()
            print(f"持續監控已啟動，檢查間隔: {args.interval} 分鐘")
            print("按 Ctrl+C 停止監控")
            
            while monitor.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n收到停止信號，正在停止監控...")
            monitor.stop_monitoring()
            print("監控已停止。")

if __name__ == "__main__":
    main()