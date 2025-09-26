#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產品潛在客戶搜尋系統 - 統一日誌配置模組
設定檔案和控制台日誌輸出
"""

import logging
import logging.handlers
from pathlib import Path
from potential_customer_finder.config import LOGGING_CONFIG

class ImmediateFileHandler(logging.handlers.RotatingFileHandler):
    """立即刷新的檔案處理器，確保日誌即時寫入檔案"""
    
    def emit(self, record):
        """發出日誌記錄並立即刷新到檔案"""
        super().emit(record)
        self.flush()  # 強制立即刷新到檔案

def setup_logging(module_name: str = None) -> logging.Logger:
    """
    設定統一的日誌配置
    
    Args:
        module_name: 模組名稱，如果為None則使用根記錄器
        
    Returns:
        logging.Logger: 配置好的記錄器
    """
    
    # 避免重複配置
    if logging.getLogger().handlers:
        return logging.getLogger(module_name)
    
    # 基本配置
    log_config = LOGGING_CONFIG
    log_level = getattr(logging, log_config['level'].upper())
    log_format = log_config['format']
    
    # 設定根記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除現有的處理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 1. 控制台處理器
    if log_config['console_logging']['enabled']:
        console_handler = logging.StreamHandler()
        console_level = getattr(logging, log_config['console_logging']['level'].upper())
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # 2. 檔案處理器配置
    if log_config['file_logging']['enabled']:
        log_dir = log_config['file_logging']['log_dir']
        max_bytes = log_config['file_logging']['max_file_size_mb'] * 1024 * 1024
        backup_count = log_config['file_logging']['backup_count']
        encoding = log_config['file_logging']['encoding']
        
        # 確保日誌目錄存在
        log_dir.mkdir(exist_ok=True)
        
        # 一般系統日誌（即時記錄）
        general_log_file = log_dir / log_config['file_logging']['general_log_file']
        general_handler = ImmediateFileHandler(
            general_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding
        )
        general_handler.setLevel(log_level)
        general_formatter = logging.Formatter(log_format)
        general_handler.setFormatter(general_formatter)
        root_logger.addHandler(general_handler)
        
        # API 調用專用日誌（即時記錄）
        if log_config['api_logging']['enabled']:
            api_log_file = log_dir / log_config['file_logging']['api_log_file']
            api_handler = ImmediateFileHandler(
                api_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=encoding
            )
            api_handler.setLevel(log_level)
            api_formatter = logging.Formatter(f"[API] {log_format}")
            api_handler.setFormatter(api_formatter)
            
            # 建立 API 專用記錄器
            api_logger = logging.getLogger('api_calls')
            api_logger.addHandler(api_handler)
            api_logger.setLevel(log_level)
            api_logger.propagate = False  # 避免重複輸出到根記錄器
        
        # 錯誤專用日誌（即時記錄）
        if log_config['error_logging']['enabled']:
            error_log_file = log_dir / log_config['file_logging']['error_log_file']
            error_handler = ImmediateFileHandler(
                error_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=encoding
            )
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(f"[ERROR] {log_format}")
            error_handler.setFormatter(error_formatter)
            root_logger.addHandler(error_handler)
    
    # 返回指定模組的記錄器
    if module_name:
        return logging.getLogger(module_name)
    else:
        return root_logger

def get_api_logger() -> logging.Logger:
    """獲取 API 專用記錄器"""
    return logging.getLogger('api_calls')

def log_api_call(model: str, operation: str, input_tokens: int, output_tokens: int, 
                cost_usd: float, response_time: float = None):
    """
    記錄 API 調用詳情到專用日誌檔案
    
    Args:
        model: 模型名稱
        operation: 操作類型
        input_tokens: 輸入 token 數量
        output_tokens: 輸出 token 數量  
        cost_usd: 成本 (USD)
        response_time: 回應時間 (秒)
    """
    api_logger = get_api_logger()
    
    # 匯率轉換
    USD_TO_TWD_RATE = 31.5
    cost_twd = cost_usd * USD_TO_TWD_RATE
    
    log_parts = [
        f"模型={model}",
        f"操作={operation}",
        f"輸入={input_tokens}tokens",
        f"輸出={output_tokens}tokens",
        f"成本=NT${cost_twd:.2f}"
    ]
    
    if response_time is not None:
        log_parts.append(f"耗時={response_time:.2f}s")
    
    api_logger.info(" | ".join(log_parts))

def log_error_with_context(logger: logging.Logger, error: Exception, context: str = None):
    """
    記錄錯誤並包含上下文資訊
    
    Args:
        logger: 記錄器
        error: 錯誤物件
        context: 上下文描述
    """
    error_config = LOGGING_CONFIG['error_logging']
    
    error_msg = f"錯誤: {type(error).__name__}: {str(error)}"
    
    if context and error_config['include_context']:
        max_length = error_config['max_context_length']
        if len(context) > max_length:
            context = context[:max_length] + "..."
        error_msg += f" | 上下文: {context}"
    
    logger.error(error_msg)
    
    if error_config['include_stack_trace']:
        logger.exception("詳細錯誤堆疊:")

# 測試函數
def test_logging_setup():
    """測試日誌配置"""
    print("測試日誌配置...")
    
    # 設定日誌
    logger = setup_logging('test_module')
    api_logger = get_api_logger()
    
    # 測試各種日誌級別
    logger.debug("這是除錯訊息")
    logger.info("這是資訊訊息")
    logger.warning("這是警告訊息")
    logger.error("這是錯誤訊息")
    
    # 測試 API 日誌
    log_api_call('gpt-5-mini', 'test_operation', 100, 50, 0.001, 1.5)
    
    # 測試錯誤日誌
    try:
        raise ValueError("測試錯誤")
    except Exception as e:
        log_error_with_context(logger, e, "測試錯誤上下文資訊")
    
    print("日誌配置測試完成")
    print(f"日誌檔案位置: {LOGGING_CONFIG['file_logging']['log_dir']}")
    
    return True

if __name__ == "__main__":
    test_logging_setup()