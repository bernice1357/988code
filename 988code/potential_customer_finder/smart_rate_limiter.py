#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產品潛在客戶搜尋系統 - 智能速率限制器
動態調整API調用延遲，提升批量處理效率
"""

import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from config import API_RATE_LIMITING

# 設定統一日誌配置
from logging_setup import setup_logging
logger = setup_logging(__name__)

class SmartRateLimiter:
    """智能速率限制器，根據API表現動態調整延遲"""
    
    def __init__(self, limiter_type: str = 'validation'):
        """
        初始化智能速率限制器
        
        Args:
            limiter_type: 限制器類型 ('validation' 或 'keyword')
        """
        self.limiter_type = limiter_type
        
        # 根據類型設定基礎延遲
        if limiter_type == 'validation':
            self.base_delay = API_RATE_LIMITING['validation_base_delay']
        elif limiter_type == 'keyword':
            self.base_delay = API_RATE_LIMITING['keyword_base_delay']
        else:
            raise ValueError(f"不支持的限制器類型: {limiter_type}")
        
        # 延遲參數
        self.current_delay = self.base_delay
        self.max_delay = API_RATE_LIMITING['max_delay']
        self.adaptation_factor = API_RATE_LIMITING['adaptation_factor']
        self.success_reduction_factor = API_RATE_LIMITING['success_reduction_factor']
        self.success_threshold = API_RATE_LIMITING['success_threshold']
        self.batch_size = API_RATE_LIMITING['batch_size']
        self.enable_adaptive = API_RATE_LIMITING['enable_adaptive_delay']
        
        # 狀態追蹤
        self.consecutive_successes = 0
        self.consecutive_errors = 0
        self.total_calls = 0
        self.total_errors = 0
        self.last_error_time: Optional[datetime] = None
        self.last_call_time: Optional[datetime] = None
        
        # 性能監控
        self.response_times = []
        self.max_response_history = 20  # 保留最近20次響應時間
        
        logger.info(f"智能速率限制器已初始化: {limiter_type}, 基礎延遲: {self.base_delay}s")
    
    def wait_if_needed(self, batch_index: Optional[int] = None) -> float:
        """
        根據當前狀態決定是否需要等待
        
        Args:
            batch_index: 批量處理中的索引 (用於決定是否需要延遲)
            
        Returns:
            float: 實際等待時間
        """
        if not self.enable_adaptive:
            # 如果禁用自適應，使用固定延遲
            if batch_index is not None and (batch_index + 1) % self.batch_size == 0:
                time.sleep(self.base_delay)
                return self.base_delay
            return 0.0
        
        # 計算需要等待的時間
        wait_time = self._calculate_delay(batch_index)
        
        if wait_time > 0:
            logger.debug(f"等待 {wait_time:.2f}s (當前延遲: {self.current_delay:.2f}s)")
            time.sleep(wait_time)
        
        self.last_call_time = datetime.now()
        return wait_time
    
    def _calculate_delay(self, batch_index: Optional[int] = None) -> float:
        """
        計算延遲時間
        
        Args:
            batch_index: 批量處理中的索引
            
        Returns:
            float: 需要延遲的時間
        """
        # 如果是批量處理，只在批量邊界延遲
        if batch_index is not None and (batch_index + 1) % self.batch_size != 0:
            return 0.0
        
        # 如果最近有錯誤，使用當前延遲
        if self.last_error_time and datetime.now() - self.last_error_time < timedelta(minutes=1):
            return self.current_delay
        
        # 如果響應時間較慢，略微增加延遲
        if len(self.response_times) >= 3:
            avg_response_time = sum(self.response_times[-3:]) / 3
            if avg_response_time > 2.0:  # 如果平均響應時間超過2秒
                return min(self.current_delay * 1.2, self.max_delay)
        
        return self.current_delay
    
    def record_success(self, response_time: float):
        """
        記錄成功的API調用
        
        Args:
            response_time: API響應時間 (秒)
        """
        self.total_calls += 1
        self.consecutive_successes += 1
        self.consecutive_errors = 0
        
        # 記錄響應時間
        self.response_times.append(response_time)
        if len(self.response_times) > self.max_response_history:
            self.response_times.pop(0)
        
        # 如果連續成功次數達到閾值，減少延遲
        if self.consecutive_successes >= self.success_threshold:
            old_delay = self.current_delay
            self.current_delay = max(
                self.base_delay, 
                self.current_delay * self.success_reduction_factor
            )
            
            if old_delay != self.current_delay:
                logger.info(f"延遲優化: {old_delay:.2f}s → {self.current_delay:.2f}s "
                           f"(連續成功: {self.consecutive_successes})")
                
            self.consecutive_successes = 0  # 重置計數器
        
        logger.debug(f"記錄成功調用: 響應時間 {response_time:.2f}s, 連續成功 {self.consecutive_successes}")
    
    def record_error(self, error_type: str = 'unknown'):
        """
        記錄失敗的API調用
        
        Args:
            error_type: 錯誤類型
        """
        self.total_calls += 1
        self.total_errors += 1
        self.consecutive_errors += 1
        self.consecutive_successes = 0
        self.last_error_time = datetime.now()
        
        # 根據錯誤類型調整延遲
        old_delay = self.current_delay
        
        if '429' in error_type or 'rate' in error_type.lower():
            # 速率限制錯誤，大幅增加延遲
            self.current_delay = min(self.max_delay, self.current_delay * self.adaptation_factor * 1.5)
        else:
            # 其他錯誤，適度增加延遲
            self.current_delay = min(self.max_delay, self.current_delay * self.adaptation_factor)
        
        logger.warning(f"記錄API錯誤: {error_type}, 延遲調整: {old_delay:.2f}s → {self.current_delay:.2f}s "
                      f"(連續錯誤: {self.consecutive_errors})")
    
    def get_stats(self) -> Dict:
        """
        獲取統計信息
        
        Returns:
            Dict: 統計信息
        """
        success_rate = ((self.total_calls - self.total_errors) / self.total_calls * 100) if self.total_calls > 0 else 0
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            'limiter_type': self.limiter_type,
            'current_delay': self.current_delay,
            'base_delay': self.base_delay,
            'total_calls': self.total_calls,
            'total_errors': self.total_errors,
            'success_rate': round(success_rate, 1),
            'consecutive_successes': self.consecutive_successes,
            'consecutive_errors': self.consecutive_errors,
            'avg_response_time': round(avg_response_time, 2),
            'adaptive_enabled': self.enable_adaptive
        }
    
    def reset(self):
        """重置所有統計和狀態"""
        self.current_delay = self.base_delay
        self.consecutive_successes = 0
        self.consecutive_errors = 0
        self.total_calls = 0
        self.total_errors = 0
        self.last_error_time = None
        self.last_call_time = None
        self.response_times = []
        
        logger.info(f"速率限制器已重置: {self.limiter_type}")

# 單例模式的速率限制器管理器
_rate_limiters = {}

def get_rate_limiter(limiter_type: str = 'validation') -> SmartRateLimiter:
    """
    獲取速率限制器實例 (單例模式)
    
    Args:
        limiter_type: 限制器類型
        
    Returns:
        SmartRateLimiter: 速率限制器實例
    """
    if limiter_type not in _rate_limiters:
        _rate_limiters[limiter_type] = SmartRateLimiter(limiter_type)
    return _rate_limiters[limiter_type]

# 測試函數
def test_rate_limiter():
    """測試速率限制器功能"""
    try:
        print("測試智能速率限制器...")
        
        # 測試驗證器類型
        validator_limiter = get_rate_limiter('validation')
        print(f"驗證器基礎延遲: {validator_limiter.base_delay}s")
        
        # 測試關鍵詞生成器類型
        keyword_limiter = get_rate_limiter('keyword')
        print(f"關鍵詞生成器基礎延遲: {keyword_limiter.base_delay}s")
        
        # 模擬一些成功調用
        start_time = time.time()
        for i in range(3):
            validator_limiter.wait_if_needed(i)
            validator_limiter.record_success(0.5)  # 模擬0.5秒響應時間
        
        elapsed = time.time() - start_time
        print(f"模擬3次調用耗時: {elapsed:.2f}s")
        
        # 顯示統計信息
        stats = validator_limiter.get_stats()
        print("驗證器統計:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"速率限制器測試失敗: {e}")
        return False

if __name__ == "__main__":
    # 執行測試
    print("開始速率限制器測試...")
    success = test_rate_limiter()
    print(f"測試結果: {'成功' if success else '失敗'}")