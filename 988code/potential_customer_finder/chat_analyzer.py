#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天記錄分析模組 - 簡化版本
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict
import os

logger = logging.getLogger(__name__)

class ChatAnalyzer:
    """聊天記錄分析器 - 簡化版本"""

    def __init__(self):
        # 動態獲取最新的聊天記錄目錄
        self.chat_dir = self._get_latest_chat_history_dir()

        if not self.chat_dir.exists():
            logger.warning(f"聊天記錄目錄不存在: {self.chat_dir}")
        else:
            logger.info(f"使用聊天記錄目錄: {self.chat_dir}")

    def _get_latest_chat_history_dir(self) -> Path:
        """自動獲取最新的聊天記錄資料夾"""
        base_dir = Path("/home/chou_fish_988/Documents/988/Line_bot/chat_history_original")

        if not base_dir.exists():
            # 回退到舊的相對路徑
            return Path(__file__).parent / "line_oa_chat_csv"

        # 找出所有符合格式的資料夾（以 line_oa_chat_csv 開頭的目錄）
        chat_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("line_oa_chat_csv")]

        if not chat_dirs:
            # 回退到舊的相對路徑
            return Path(__file__).parent / "line_oa_chat_csv"

        # 按照修改時間排序，取最新的
        latest_dir = max(chat_dirs, key=lambda d: d.stat().st_mtime)
        return latest_dir
    
    def _read_chat_file(self, csv_file: Path) -> List[Dict]:
        """讀取單個聊天記錄檔案"""
        records = []
        
        try:
            # 從檔案名提取客戶資訊
            filename = csv_file.stem  # 去掉.csv後綴
            customer_info = self._extract_customer_info_from_filename(filename)
            
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                # 讀取CSV檔案
                reader = csv.reader(f)
                headers = next(reader, None)  # 讀取標題行
                
                for row_idx, row in enumerate(reader):
                    try:
                        if len(row) >= 5:  # 確保有足夠的欄位（需要5個欄位）
                            # 正確的CSV格式：傳送者類型, 傳送者名稱, 傳送日期, 傳送時間, 內容
                            sender_type = row[0].strip() if row[0] else ''     # User/Account
                            sender_name = row[1].strip() if row[1] else ''     # 客戶名稱或工作人員名稱
                            date_str = row[2].strip() if row[2] else ''        # 日期
                            time_str = row[3].strip() if row[3] else ''        # 時間
                            content = row[4].strip() if row[4] else ''         # 內容
                            
                            # 只處理客戶發送的文字訊息 (sender_type == 'User')
                            if sender_type.lower() == 'user' and self._is_text_message('text', content):
                                record = {
                                    'customer_name': customer_info['customer_name'],
                                    'customer_id': customer_info.get('customer_id'),
                                    'content': content,
                                    'date': f"{date_str} {time_str}",
                                    'date_str': date_str,
                                    'sender_name': sender_name,
                                    'file_source': csv_file.name,
                                    'row_number': row_idx + 2  # +2 因為標題行和從1開始計數
                                }
                                records.append(record)
                    
                    except Exception as e:
                        # 跳過有問題的行
                        continue
            
            if records:
                logger.info(f"從 {csv_file.name} 讀取到 {len(records)} 條客戶訊息")
        
        except Exception as e:
            logger.error(f"讀取檔案 {csv_file} 失敗: {e}")
        
        return records
    
    def _extract_customer_info_from_filename(self, filename: str) -> Dict:
        """從檔案名提取客戶資訊"""
        # 檔案名格式通常類似：1000_Unknown.csv 或 100_20240101_20250709_長治_尹賀日本料理(UCB1XX000).csv
        
        parts = filename.split('_')
        customer_info = {
            'customer_name': 'Unknown',
            'customer_id': None
        }
        
        if len(parts) >= 2:
            # 如果有足夠的部分，嘗試提取客戶名稱
            if len(parts) >= 4:
                # 格式：序號_日期_日期_地區_店名
                if len(parts) >= 5:
                    customer_name = '_'.join(parts[4:])  # 店名部分
                    # 移除括號內的客戶ID
                    if '(' in customer_name and ')' in customer_name:
                        customer_id_part = customer_name[customer_name.find('(')+1:customer_name.find(')')]
                        customer_name = customer_name[:customer_name.find('(')].strip()
                        if customer_id_part and customer_id_part != 'Unknown':
                            customer_info['customer_id'] = customer_id_part
                    
                    customer_info['customer_name'] = customer_name if customer_name else 'Unknown'
                else:
                    customer_info['customer_name'] = parts[-1] if parts[-1] != 'Unknown' else 'Unknown'
            else:
                # 簡單格式：序號_客戶名
                customer_info['customer_name'] = parts[1] if parts[1] != 'Unknown' else 'Unknown'
        
        return customer_info
    
    def _is_customer_message(self, sender: str) -> bool:
        """判斷是否為客戶發送的訊息"""
        # 常見的客戶發送者標識
        customer_indicators = ['客戶', '使用者', 'user', 'customer', '顧客']
        sender_lower = sender.lower()
        
        # 如果發送者包含客戶相關關鍵詞，或者不是系統/商家發送
        system_indicators = ['系統', 'system', '商家', '客服', '店家', 'bot']
        
        for indicator in system_indicators:
            if indicator in sender_lower:
                return False
        
        # 預設認為是客戶訊息（除非明確是系統訊息）
        return True
    
    def _is_text_message(self, msg_type: str, content: str) -> bool:
        """判斷是否為有效的文字訊息"""
        if not content or len(content) < 2:
            return False
        
        # 排除的訊息類型
        excluded_types = ['貼圖', 'sticker', '圖片', 'image', '檔案', 'file']
        msg_type_lower = msg_type.lower()
        
        for excluded in excluded_types:
            if excluded in msg_type_lower:
                return False
        
        return True
    
    def _search_keywords_in_message(self, keywords: List[str], message: str) -> List[Dict]:
        """在訊息中搜尋關鍵詞"""
        matches = []
        message_lower = message.lower()
        
        for keyword in keywords:
            if keyword.lower() in message_lower:
                matches.append({
                    'keyword': keyword,
                    'match_type': 'exact',
                    'confidence': 1.0,
                    'position': message_lower.find(keyword.lower())
                })
        
        return matches

def get_chat_analyzer() -> ChatAnalyzer:
    """獲取聊天分析器實例"""
    return ChatAnalyzer()