#!/usr/bin/env python3
"""
排程器健康狀態監控系統
檢查資料庫中各個排程器在其對應表格中的更新時間
"""

import os
import sys
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import pytz
import logging
from typing import Dict, List, Optional, Any
import json

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(__file__))
from config import get_db_config

class SchedulerHealthMonitor:
    """排程器健康狀態監控器"""
    
    def __init__(self):
        self.db_config = get_db_config()
        self.setup_logging()
        
        # 台北時區
        self.tz_utc8 = pytz.timezone('Asia/Taipei')
        
        # 排程器配置
        self.scheduler_configs = {
            # 補貨排程 (restock)
            "daily_prediction": {
                "name": "每日預測生成",
                "category": "restock",
                "table": "prophet_predictions",
                "time_column": "created_at",
                "frequency": "daily",
                "expected_time": "22:00",
                "tolerance_hours": 2
            },
            "weekly_model_training": {
                "name": "週度模型訓練",
                "category": "restock", 
                "table": "schedule_history",
                "time_column": "execution_time",
                "frequency": "weekly",
                "expected_day": "Saturday",
                "expected_time": "08:00",
                "tolerance_hours": 4,
                "filter_condition": "task_id = 'weekly_model_training'"
            },
            "trigger_health_check": {
                "name": "觸發器健康檢查",
                "category": "restock",
                "table": "trigger_health_log", 
                "time_column": "check_timestamp",
                "frequency": "daily",
                "expected_time": "02:00",
                "tolerance_hours": 2
            },
            
            # 銷售排程 (sales)
            "sales_change_check": {
                "name": "銷量變化檢查",
                "category": "sales",
                "table": "sales_change_table",
                "time_column": "updated_at", 
                "frequency": "daily",
                "expected_time": "06:00",
                "tolerance_hours": 2
            },
            "monthly_prediction": {
                "name": "月銷售預測",
                "category": "sales",
                "table": "monthly_sales_predictions",
                "time_column": "created_at",
                "frequency": "monthly",
                "expected_day": 1,
                "expected_time": "01:00",
                "tolerance_hours": 6
            },
            "monthly_sales_reset": {
                "name": "銷量重置",
                "category": "sales", 
                "table": "sales_change_table",
                "time_column": "updated_at",
                "frequency": "monthly",
                "expected_day": 1,
                "expected_time": "00:30",
                "tolerance_hours": 2,
                "special_check": "reset_operation"
            },
            
            # 推薦排程 (recommendation)
            "weekly_recommendation": {
                "name": "推薦系統更新",
                "category": "recommendation",
                "table": "schedule_history",
                "time_column": "execution_time", 
                "frequency": "weekly",
                "expected_day": "Sunday",
                "expected_time": "08:00",
                "tolerance_hours": 4,
                "filter_condition": "task_id = 'weekly_recommendation'"
            },
            
            # 客戶管理排程 (customer_management)
            "inactive_customer_check": {
                "name": "不活躍客戶檢查",
                "category": "customer_management",
                "table": "inactive_customers",
                "time_column": "updated_at",
                "frequency": "daily",
                "expected_time": "02:30",
                "tolerance_hours": 2
            },
            "repurchase_reminder": {
                "name": "回購提醒維護",
                "category": "customer_management",
                "table": "repurchase_reminders",
                "time_column": "updated_at",
                "frequency": "daily", 
                "expected_time": "04:00",
                "tolerance_hours": 2
            }
        }
        
    def setup_logging(self):
        """設置日誌"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'scheduler_health_{datetime.now().strftime("%Y%m")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('SchedulerHealthMonitor')
        
    def get_connection(self):
        """獲取資料庫連接"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            self.logger.error(f"資料庫連接失敗: {e}")
            return None
    
    def check_table_exists(self, table_name: str) -> bool:
        """檢查表格是否存在"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, (table_name,))
                    return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"檢查表格 {table_name} 是否存在時出錯: {e}")
            return False
    
    def get_latest_update_time(self, scheduler_id: str, config: Dict) -> Optional[datetime]:
        """獲取指定排程器的最新更新時間"""
        try:
            table = config["table"]
            time_column = config["time_column"]
            
            # 檢查表格是否存在
            if not self.check_table_exists(table):
                self.logger.warning(f"表格 {table} 不存在")
                return None
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 建構查詢語句
                    query = f"SELECT MAX({time_column}) FROM {table}"
                    
                    # 添加篩選條件
                    if "filter_condition" in config:
                        query += f" WHERE {config['filter_condition']}"
                    
                    cursor.execute(query)
                    result = cursor.fetchone()[0]
                    
                    if result:
                        # 轉換為台北時區
                        if result.tzinfo is None:
                            result = pytz.utc.localize(result)
                        return result.astimezone(self.tz_utc8)
                    
                    return None
                    
        except Exception as e:
            self.logger.error(f"獲取 {scheduler_id} 最新更新時間時出錯: {e}")
            return None
    
    def get_record_count_in_timeframe(self, scheduler_id: str, config: Dict, hours: int = 24) -> int:
        """獲取指定時間範圍內的記錄數量"""
        try:
            table = config["table"]
            time_column = config["time_column"]
            
            if not self.check_table_exists(table):
                return 0
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 建構查詢語句
                    query = f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE {time_column} >= NOW() - INTERVAL '{hours} hours'
                    """
                    
                    # 添加篩選條件
                    if "filter_condition" in config:
                        query += f" AND {config['filter_condition']}"
                    
                    cursor.execute(query)
                    return cursor.fetchone()[0]
                    
        except Exception as e:
            self.logger.error(f"獲取 {scheduler_id} 記錄數量時出錯: {e}")
            return 0
    
    def calculate_next_expected_time(self, config: Dict) -> datetime:
        """計算下次預期執行時間"""
        now = datetime.now(self.tz_utc8)
        frequency = config["frequency"]
        expected_time_str = config["expected_time"]
        
        # 解析時間
        expected_hour, expected_minute = map(int, expected_time_str.split(":"))
        
        if frequency == "daily":
            # 每日任務
            next_run = now.replace(hour=expected_hour, minute=expected_minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
                
        elif frequency == "weekly":
            # 每週任務
            expected_day = config["expected_day"]
            weekdays = {
                "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                "Friday": 4, "Saturday": 5, "Sunday": 6
            }
            
            target_weekday = weekdays[expected_day]
            days_ahead = target_weekday - now.weekday()
            
            if days_ahead <= 0:  # 如果已經過了這週的目標日
                days_ahead += 7
                
            next_run = now.replace(hour=expected_hour, minute=expected_minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
            
        elif frequency == "monthly":
            # 每月任務
            expected_day = config["expected_day"]
            
            # 計算下個月的第一天或指定日期
            if now.day > expected_day or (now.day == expected_day and now.hour >= expected_hour):
                # 下個月
                if now.month == 12:
                    next_month = now.replace(year=now.year + 1, month=1, day=expected_day)
                else:
                    next_month = now.replace(month=now.month + 1, day=expected_day)
                next_run = next_month.replace(hour=expected_hour, minute=expected_minute, second=0, microsecond=0)
            else:
                # 這個月
                next_run = now.replace(day=expected_day, hour=expected_hour, minute=expected_minute, second=0, microsecond=0)
        
        return next_run
    
    def analyze_scheduler_health(self, scheduler_id: str, config: Dict) -> Dict:
        """分析排程器健康狀態"""
        result = {
            "scheduler_id": scheduler_id,
            "name": config["name"],
            "category": config["category"],
            "table": config["table"],
            "frequency": config["frequency"],
            "status": "unknown",
            "last_update": None,
            "next_expected": None,
            "delay_hours": 0,
            "recent_records": 0,
            "issues": []
        }
        
        try:
            # 獲取最新更新時間
            last_update = self.get_latest_update_time(scheduler_id, config)
            result["last_update"] = last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else None
            
            # 計算下次預期執行時間
            next_expected = self.calculate_next_expected_time(config)
            result["next_expected"] = next_expected.strftime('%Y-%m-%d %H:%M:%S')
            
            # 獲取最近24小時的記錄數量
            recent_records = self.get_record_count_in_timeframe(scheduler_id, config, 24)
            result["recent_records"] = recent_records
            
            # 分析健康狀態
            now = datetime.now(self.tz_utc8)
            tolerance_hours = config.get("tolerance_hours", 2)
            
            if last_update is None:
                result["status"] = "critical"
                result["issues"].append("無法找到任何執行記錄")
            else:
                # 計算延遲時間
                if config["frequency"] == "daily":
                    # 每日任務：檢查是否在容忍範圍內
                    expected_today = now.replace(
                        hour=int(config["expected_time"].split(":")[0]),
                        minute=int(config["expected_time"].split(":")[1]),
                        second=0, microsecond=0
                    )
                    
                    if now >= expected_today:
                        # 已經過了今天的預期時間
                        if last_update.date() < now.date():
                            # 最後更新不是今天
                            delay_hours = (now - expected_today).total_seconds() / 3600
                            result["delay_hours"] = round(delay_hours, 2)
                            
                            if delay_hours > tolerance_hours:
                                result["status"] = "critical"
                                result["issues"].append(f"延遲 {delay_hours:.1f} 小時")
                            else:
                                result["status"] = "warning"
                                result["issues"].append(f"輕微延遲 {delay_hours:.1f} 小時")
                        else:
                            result["status"] = "healthy"
                    else:
                        # 還沒到今天的預期時間
                        if last_update.date() == (now - timedelta(days=1)).date():
                            result["status"] = "healthy"
                        else:
                            result["status"] = "warning"
                            result["issues"].append("昨日未執行")
                
                elif config["frequency"] == "weekly":
                    # 每週任務：檢查本週是否執行
                    week_start = now - timedelta(days=now.weekday())
                    if last_update < week_start:
                        result["status"] = "warning"
                        result["issues"].append("本週尚未執行")
                    else:
                        result["status"] = "healthy"
                
                elif config["frequency"] == "monthly":
                    # 每月任務：檢查本月是否執行
                    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    if last_update < month_start:
                        if now.day > config["expected_day"]:
                            result["status"] = "critical"
                            result["issues"].append("本月尚未執行")
                        else:
                            result["status"] = "healthy"
                    else:
                        result["status"] = "healthy"
            
            # 檢查記錄數量
            if config["frequency"] == "daily" and recent_records == 0:
                result["issues"].append("24小時內無新記錄")
                if result["status"] == "healthy":
                    result["status"] = "warning"
                    
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"分析時發生錯誤: {str(e)}")
            self.logger.error(f"分析 {scheduler_id} 健康狀態時出錯: {e}")
        
        return result
    
    def check_all_schedulers(self) -> List[Dict]:
        """檢查所有排程器的健康狀態"""
        results = []
        
        self.logger.info("開始檢查所有排程器健康狀態")
        
        for scheduler_id, config in self.scheduler_configs.items():
            self.logger.info(f"檢查排程器: {scheduler_id}")
            result = self.analyze_scheduler_health(scheduler_id, config)
            results.append(result)
        
        return results
    
    def generate_health_report(self, results: List[Dict]) -> str:
        """生成健康狀態報告"""
        report = []
        report.append("=" * 80)
        report.append("排程器健康狀態報告")
        report.append(f"生成時間: {datetime.now(self.tz_utc8).strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)")
        report.append("=" * 80)
        
        # 統計
        total = len(results)
        healthy = len([r for r in results if r["status"] == "healthy"])
        warning = len([r for r in results if r["status"] == "warning"])
        critical = len([r for r in results if r["status"] == "critical"])
        error = len([r for r in results if r["status"] == "error"])
        
        report.append(f"\n總體狀態統計:")
        report.append(f"  總排程器數量: {total}")
        report.append(f"  健康: {healthy}")
        report.append(f"  警告: {warning}")
        report.append(f"  嚴重: {critical}")
        report.append(f"  錯誤: {error}")
        
        # 按分類分組
        categories = {}
        for result in results:
            category = result["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # 詳細報告
        for category, schedulers in categories.items():
            report.append(f"\n{'-' * 40}")
            report.append(f"分類: {category.upper()}")
            report.append(f"{'-' * 40}")
            
            for scheduler in schedulers:
                status_symbol = {
                    "healthy": "[OK]",
                    "warning": "[WARN]", 
                    "critical": "[CRIT]",
                    "error": "[ERR]",
                    "unknown": "[UNK]"
                }.get(scheduler["status"], "[UNK]")
                
                report.append(f"\n{status_symbol} {scheduler['name']} ({scheduler['scheduler_id']})")
                report.append(f"   表格: {scheduler['table']}")
                report.append(f"   頻率: {scheduler['frequency']}")
                report.append(f"   最後更新: {scheduler['last_update'] or '無記錄'}")
                report.append(f"   下次預期: {scheduler['next_expected']}")
                report.append(f"   最近記錄數: {scheduler['recent_records']}")
                
                if scheduler["delay_hours"] > 0:
                    report.append(f"   延遲時間: {scheduler['delay_hours']} 小時")
                
                if scheduler["issues"]:
                    report.append(f"   問題: {', '.join(scheduler['issues'])}")
        
        # 建議
        report.append(f"\n{'-' * 40}")
        report.append("建議修復動作:")
        report.append(f"{'-' * 40}")
        
        critical_schedulers = [r for r in results if r["status"] == "critical"]
        warning_schedulers = [r for r in results if r["status"] == "warning"]
        
        if critical_schedulers:
            report.append("\n[!] 立即處理 (Critical):")
            for scheduler in critical_schedulers:
                report.append(f"   - {scheduler['name']}: {', '.join(scheduler['issues'])}")
        
        if warning_schedulers:
            report.append("\n[!] 需要關注 (Warning):")
            for scheduler in warning_schedulers:
                report.append(f"   - {scheduler['name']}: {', '.join(scheduler['issues'])}")
        
        if healthy == total:
            report.append("\n[OK] 所有排程器運作正常！")
        
        return "\n".join(report)
    
    def save_report_to_file(self, report: str) -> str:
        """保存報告到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"scheduler_health_report_{timestamp}.txt"
        filepath = os.path.join(os.path.dirname(__file__), 'reports', filename)
        
        # 確保reports目錄存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filepath
    
    def run_health_check(self) -> Dict:
        """運行完整的健康檢查"""
        self.logger.info("開始運行排程器健康檢查")
        
        # 檢查所有排程器
        results = self.check_all_schedulers()
        
        # 生成報告
        report = self.generate_health_report(results)
        
        # 保存報告
        report_file = self.save_report_to_file(report)
        
        # 輸出到控制台
        print(report)
        
        self.logger.info(f"健康檢查完成，報告已保存到: {report_file}")
        
        return {
            "results": results,
            "report": report,
            "report_file": report_file,
            "summary": {
                "total": len(results),
                "healthy": len([r for r in results if r["status"] == "healthy"]),
                "warning": len([r for r in results if r["status"] == "warning"]),
                "critical": len([r for r in results if r["status"] == "critical"]),
                "error": len([r for r in results if r["status"] == "error"])
            }
        }

def main():
    """主函數"""
    monitor = SchedulerHealthMonitor()
    monitor.run_health_check()

if __name__ == "__main__":
    main()