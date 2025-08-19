#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進度追蹤系統 - 用於顯示潛在客戶分析進度
"""

import json
import time
from pathlib import Path
from datetime import datetime
from threading import Lock

class DateTimeEncoder(json.JSONEncoder):
    """自定義JSON編碼器，處理datetime對象"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
    
    def encode(self, obj):
        """重寫encode方法以處理嵌套的datetime對象"""
        def convert_datetime(item):
            if isinstance(item, datetime):
                return item.isoformat()
            elif isinstance(item, dict):
                return {key: convert_datetime(value) for key, value in item.items()}
            elif isinstance(item, list):
                return [convert_datetime(element) for element in item]
            else:
                return item
        
        converted_obj = convert_datetime(obj)
        return super().encode(converted_obj)

class ProgressTracker:
    def __init__(self):
        self.progress_file = Path(__file__).parent / "progress.json"
        self.lock = Lock()
        self.current_task_id = None
        
    def start_task(self, task_id: str, product_name: str):
        """開始新任務"""
        with self.lock:
            self.current_task_id = task_id
            progress_data = {
                "task_id": task_id,
                "product_name": product_name,
                "start_time": datetime.now().isoformat(),
                "status": "running",
                "current_step": "初始化中...",
                "total_steps": 7,
                "current_step_number": 0,
                "messages": [],
                "percentage": 0
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
    
    def update_step(self, step_number: int, step_name: str, message: str = ""):
        """更新當前步驟"""
        if not self.current_task_id:
            return
            
        with self.lock:
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                progress_data["current_step_number"] = step_number
                progress_data["current_step"] = step_name
                progress_data["percentage"] = int((step_number / progress_data["total_steps"]) * 100)
                
                if message:
                    progress_data["messages"].append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "message": message
                    })
                
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
                    
            except Exception as e:
                print(f"進度更新錯誤: {e}")
    
    def add_message(self, message: str):
        """添加進度消息"""
        if not self.current_task_id:
            return
            
        with self.lock:
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                progress_data["messages"].append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "message": message
                })
                
                # 只保留最近20條消息
                if len(progress_data["messages"]) > 20:
                    progress_data["messages"] = progress_data["messages"][-20:]
                
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
                    
            except Exception as e:
                print(f"消息添加錯誤: {e}")
    
    def complete_task(self, results_count: int = 0, analysis_result: dict = None):
        """完成任務"""
        if not self.current_task_id:
            return
            
        with self.lock:
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                progress_data["status"] = "completed"
                progress_data["current_step"] = "分析完成"
                progress_data["current_step_number"] = progress_data["total_steps"]
                progress_data["percentage"] = 100
                progress_data["end_time"] = datetime.now().isoformat()
                progress_data["results_count"] = results_count
                
                # 儲存完整的分析結果
                if analysis_result:
                    progress_data["analysis_result"] = analysis_result
                
                progress_data["messages"].append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "message": f"分析完成！找到 {results_count} 個結果"
                })
                
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
                    
            except Exception as e:
                print(f"任務完成錯誤: {e}")
    
    def error_task(self, error_message: str):
        """任務出錯"""
        if not self.current_task_id:
            return
            
        with self.lock:
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                progress_data["status"] = "error"
                progress_data["current_step"] = "發生錯誤"
                progress_data["end_time"] = datetime.now().isoformat()
                progress_data["error"] = error_message
                
                progress_data["messages"].append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "message": f"錯誤: {error_message}"
                })
                
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
                    
            except Exception as e:
                print(f"錯誤處理錯誤: {e}")
    
    def get_progress(self, task_id: str = None):
        """獲取進度信息"""
        try:
            if not self.progress_file.exists():
                return None
                
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                
            if task_id and progress_data.get("task_id") != task_id:
                return None
                
            return progress_data
            
        except Exception as e:
            print(f"獲取進度錯誤: {e}")
            return None

# 全域進度追蹤器實例
progress_tracker = ProgressTracker()