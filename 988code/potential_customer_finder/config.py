#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產品潛在客戶搜尋系統 - 配置檔案
"""

import os
import sys
from pathlib import Path

print("使用環境變數配置")

# 直接從環境變數讀取配置
DATABASE_CONFIG = {
    'host': '127.0.0.1',
    'database': '988',
    'user': 'n8n',
    'password': '1234',
    'port': 5433
}

LLM_CONFIG = {
    'api_key': '',
    'model_name': 'gpt-5-mini',
    # 雙模型配置
    'keyword_model': 'gpt-5-mini',
    'validation_model': 'gpt-5-nano'
}

# --- 專案特定設定 ---
# 聊天記錄資料夾路徑 - 使用相對路徑
CHAT_HISTORY_DIR = Path(__file__).parent / "line_oa_chat_csv"

# 產品關鍵詞快取資料夾
KEYWORDS_CACHE_DIR = Path(__file__).parent / "cache"

# --- 搜尋設定 ---
# 模糊匹配相似度閾值 (0.0-1.0)
FUZZY_THRESHOLD = 0.6

# 最大搜尋結果數量 (設為 None 表示無限制)
MAX_SEARCH_RESULTS = None  # 無限制，處理所有結果

# --- LLM 關鍵詞生成設定 ---
KEYWORD_GENERATION_CONFIG = {
    'max_completion_tokens': 8000,   # 增加輸出 token 限制
    'model': os.getenv('KEYWORD_MODEL_NAME', 'gpt-5-mini')  # 使用專用關鍵詞生成模型
}

# --- LLM 結果驗證設定 ---
RESULT_VALIDATION_CONFIG = {
    'max_completion_tokens': 8000,   # 推理模型需要更多 tokens 進行推理過程
    'model': os.getenv('VALIDATION_MODEL_NAME', 'gpt-5-nano')  # 使用專用驗證模型
}

# --- OpenAI API 成本配置 (2025年8月價格) ---
OPENAI_PRICING = {
    'gpt-5': {
        'input': 1.25,   # USD per million tokens
        'output': 10.0   # USD per million tokens
    },
    'gpt-5-mini': {
        'input': 0.25,   # USD per million tokens
        'output': 2.0    # USD per million tokens
    },
    'gpt-5-nano': {
        'input': 0.05,   # USD per million tokens
        'output': 0.40   # USD per million tokens
    }
}

# --- 快取設定 ---
# 關鍵詞快取有效期 (天)
CACHE_EXPIRY_DAYS = 30

# --- 匹配權重設定 ---
MATCH_WEIGHTS = {
    'exact': 1.0,        # 完全匹配
    'high_similarity': 0.85,   # 高相似度匹配
    'medium_similarity': 0.7,  # 中相似度匹配
    'low_similarity': 0.5,     # 低相似度匹配  
    'context': 0.6             # 上下文匹配
}

# --- 聊天記錄分析設定 ---
CHAT_ANALYSIS_CONFIG = {
    # 只分析客人發送的訊息
    'customer_sender_types': ['使用者', '客戶', 'user', 'customer'],
    # 排除的訊息類型 (如系統訊息、貼圖等)
    'exclude_message_types': ['貼圖', 'sticker', '圖片', 'image'],
    # 最小訊息長度 (字元數)
    'min_message_length': 2
}

# --- 結果顯示設定 ---
DISPLAY_CONFIG = {
    # 每頁顯示結果數
    'results_per_page': 20,
    # 訊息內容最大顯示長度
    'max_message_display_length': 100,
    # 日期格式
    'date_format': '%Y-%m-%d %H:%M'
}

# --- 匯出設定 ---
EXPORT_CONFIG = {
    # 預設匯出格式
    'default_format': 'csv',
    # CSV 編碼
    'csv_encoding': 'utf-8-sig',  # 支援中文Excel開啟
    # 匯出檔案名稱格式
    'filename_format': 'potential_customers_{product}_{timestamp}.csv'
}

# --- API 速率限制設定 ---
API_RATE_LIMITING = {
    # 結果驗證基礎延遲 (秒)
    'validation_base_delay': 0.2,
    # 關鍵詞生成基礎延遲 (秒) 
    'keyword_base_delay': 0.5,
    # 最大延遲時間 (秒)
    'max_delay': 5.0,
    # 錯誤時的延遲增加係數
    'adaptation_factor': 1.5,
    # 連續成功時的延遲減少係數
    'success_reduction_factor': 0.8,
    # 連續成功次數閾值 (達到後開始減少延遲)
    'success_threshold': 5,
    # 批量處理大小 (每批後檢查延遲調整)
    'batch_size': 10,
    # 啟用動態延遲調整
    'enable_adaptive_delay': True
}

# --- 日誌配置設定 ---
LOGGING_CONFIG = {
    # 日誌級別
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    # 日誌格式
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    # 日誌文件設定
    'file_logging': {
        'enabled': True,
        'log_dir': Path(__file__).parent / 'logs',
        'api_log_file': 'api_calls.log',
        'error_log_file': 'errors.log',
        'general_log_file': 'system.log',
        'max_file_size_mb': 50,
        'backup_count': 5,
        'encoding': 'utf-8'
    },
    # 控制台日誌設定
    'console_logging': {
        'enabled': True,
        'level': 'INFO'  # 可以和文件日誌設定不同級別
    },
    # API 調用專用日誌設定
    'api_logging': {
        'enabled': True,
        'log_requests': True,
        'log_responses': True,
        'log_token_usage': True,
        'log_timing': True,
        'truncate_long_content': True,
        'max_content_length': 1000,  # 超過此長度的內容會被截斷
        'sensitive_fields': ['api_key', 'password']  # 敏感欄位不會被記錄
    },
    # 錯誤日誌專用設定
    'error_logging': {
        'enabled': True,
        'include_stack_trace': True,
        'include_context': True,
        'max_context_length': 500
    }
}

# --- 除錯設定 ---
DEBUG_CONFIG = {
    # 是否顯示詳細日誌
    'verbose': True,
    # 是否顯示匹配過程
    'show_matching_process': True,
    # 是否儲存搜尋歷史
    'save_search_history': True
}

# 確保必要的資料夾存在
KEYWORDS_CACHE_DIR.mkdir(exist_ok=True)
LOGGING_CONFIG['file_logging']['log_dir'].mkdir(exist_ok=True)

# 驗證必要的配置
def validate_config(skip_llm_check=False):
    """驗證配置是否完整"""
    errors = []
    
    if not skip_llm_check and not LLM_CONFIG.get('api_key'):
        errors.append("缺少 OpenAI API Key")
    
    if not CHAT_HISTORY_DIR.exists():
        errors.append(f"聊天記錄資料夾不存在: {CHAT_HISTORY_DIR}")
    
    if not DATABASE_CONFIG.get('host'):
        errors.append("缺少資料庫主機設定")
    
    return errors

if __name__ == "__main__":
    # 配置驗證
    errors = validate_config()
    if errors:
        print("配置錯誤:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("配置驗證通過")
        print(f"聊天記錄資料夾: {CHAT_HISTORY_DIR}")
        print(f"關鍵詞快取資料夾: {KEYWORDS_CACHE_DIR}")
        print(f"使用 LLM 模型: {LLM_CONFIG.get('model_name')}")