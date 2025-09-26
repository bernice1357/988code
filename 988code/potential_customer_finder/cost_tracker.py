#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產品潛在客戶搜尋系統 - API 成本追踪器
追踪 OpenAI API 使用量和成本統計
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from potential_customer_finder.config import OPENAI_PRICING

# 美元轉台幣匯率 (可以根據實際匯率調整)
USD_TO_TWD_RATE = 31.5

# 設定統一日誌配置
from potential_customer_finder.logging_setup import setup_logging
logger = setup_logging(__name__)

class CostTracker:
    """API 成本追踪器"""
    
    def __init__(self):
        """初始化成本追踪器"""
        self.session_costs = []  # 當前 session 的成本記錄
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0
        self.total_cost_twd = 0.0
        
        # 分模型統計
        self.model_stats = {}
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        計算單次 API 調用成本
        
        Args:
            model: 模型名稱
            input_tokens: 輸入 token 數量
            output_tokens: 輸出 token 數量
            
        Returns:
            float: 成本 (USD)
        """
        if model not in OPENAI_PRICING:
            logger.warning(f"未知模型 {model}，無法計算成本")
            return 0.0
        
        pricing = OPENAI_PRICING[model]
        
        # 計算成本 (價格是每百萬 tokens)
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        total_cost = input_cost + output_cost
        
        logger.debug(f"成本計算 - 模型: {model}, 輸入: {input_tokens}, 輸出: {output_tokens}, 成本: ${total_cost:.6f}")
        
        return total_cost
    
    def track_api_call(self, model: str, input_tokens: int, output_tokens: int, 
                      operation_type: str = "unknown") -> Dict:
        """
        追踪單次 API 調用
        
        Args:
            model: 模型名稱
            input_tokens: 輸入 token 數量
            output_tokens: 輸出 token 數量
            operation_type: 操作類型 (keyword_generation, validation, etc.)
            
        Returns:
            Dict: 成本資訊
        """
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        # 記錄到 session
        call_record = {
            'timestamp': datetime.now(),
            'model': model,
            'operation_type': operation_type,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost_usd': cost,
            'cost_twd': cost * USD_TO_TWD_RATE
        }
        self.session_costs.append(call_record)
        
        # 更新總計
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost
        self.total_cost_twd += cost * USD_TO_TWD_RATE
        
        # 更新分模型統計
        if model not in self.model_stats:
            self.model_stats[model] = {
                'calls': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'cost_usd': 0.0,
                'cost_twd': 0.0
            }
        
        stats = self.model_stats[model]
        stats['calls'] += 1
        stats['input_tokens'] += input_tokens
        stats['output_tokens'] += output_tokens
        stats['cost_usd'] += cost
        stats['cost_twd'] += cost * USD_TO_TWD_RATE
        
        cost_twd = cost * USD_TO_TWD_RATE
        logger.info(f"API 調用追踪 - {operation_type}({model}): {input_tokens}輸入+{output_tokens}輸出 = NT${cost_twd:.2f}")
        
        return call_record
    
    def get_session_summary(self) -> Dict:
        """
        獲取當前 session 的成本摘要
        
        Returns:
            Dict: 成本摘要資訊
        """
        total_tokens = self.total_input_tokens + self.total_output_tokens
        
        # 按操作類型分組統計
        operation_stats = {}
        for call in self.session_costs:
            op_type = call['operation_type']
            if op_type not in operation_stats:
                operation_stats[op_type] = {
                    'calls': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'cost_usd': 0.0,
                    'cost_twd': 0.0
                }
            
            stats = operation_stats[op_type]
            stats['calls'] += 1
            stats['input_tokens'] += call['input_tokens']
            stats['output_tokens'] += call['output_tokens']
            stats['cost_usd'] += call['cost_usd']
            stats['cost_twd'] += call['cost_twd']
        
        return {
            'total_calls': len(self.session_costs),
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': total_tokens,
            'total_cost_usd': self.total_cost_usd,
            'total_cost_twd': self.total_cost_twd,
            'model_breakdown': self.model_stats.copy(),
            'operation_breakdown': operation_stats,
            'session_start': self.session_costs[0]['timestamp'] if self.session_costs else None,
            'session_end': self.session_costs[-1]['timestamp'] if self.session_costs else None
        }
    
    def format_cost_summary(self) -> str:
        """
        格式化成本摘要為可讀文字
        
        Returns:
            str: 格式化的成本摘要
        """
        if not self.session_costs:
            return "本次搜尋未使用 API"
        
        summary = self.get_session_summary()
        
        lines = []
        lines.append("API 使用成本統計")
        lines.append("=" * 50)
        
        # 總體統計
        lines.append(f"總計:")
        lines.append(f"  API 調用次數: {summary['total_calls']}")
        lines.append(f"  Token 使用: {summary['total_input_tokens']:,} 輸入 + {summary['total_output_tokens']:,} 輸出 = {summary['total_tokens']:,}")
        lines.append(f"  總成本: NT${summary['total_cost_twd']:.2f}")
        lines.append(f"  (約 ${summary['total_cost_usd']:.6f} USD)")
        
        # 分模型統計
        if summary['model_breakdown']:
            lines.append(f"\n分模型統計:")
            for model, stats in summary['model_breakdown'].items():
                lines.append(f"  {model}:")
                lines.append(f"    調用: {stats['calls']} 次")
                lines.append(f"    Token: {stats['input_tokens']:,} + {stats['output_tokens']:,} = {stats['input_tokens'] + stats['output_tokens']:,}")
                lines.append(f"    成本: NT${stats['cost_twd']:.2f}")
        
        # 分操作統計
        if summary['operation_breakdown']:
            lines.append(f"\n分操作統計:")
            for op_type, stats in summary['operation_breakdown'].items():
                op_name_map = {
                    'keyword_generation': '關鍵詞生成',
                    'validation': '結果驗證',
                    'unknown': '其他操作'
                }
                op_display = op_name_map.get(op_type, op_type)
                
                lines.append(f"  {op_display}:")
                lines.append(f"    調用: {stats['calls']} 次")
                lines.append(f"    成本: NT${stats['cost_twd']:.2f}")
        
        return "\n".join(lines)
    
    def reset_session(self):
        """重置 session 統計"""
        self.session_costs.clear()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0
        self.total_cost_twd = 0.0
        self.model_stats.clear()
        logger.info("成本追踪器已重置")

# 全域單例
_cost_tracker = None

def get_cost_tracker() -> CostTracker:
    """獲取成本追踪器實例 (單例模式)"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker

def track_openai_usage(model: str, usage_data: Dict, operation_type: str = "unknown") -> Dict:
    """
    便利函數：追踪 OpenAI API 使用量
    
    Args:
        model: 模型名稱
        usage_data: OpenAI API 回應中的 usage 物件
        operation_type: 操作類型
        
    Returns:
        Dict: 成本記錄
    """
    tracker = get_cost_tracker()
    
    input_tokens = getattr(usage_data, 'prompt_tokens', 0)
    output_tokens = getattr(usage_data, 'completion_tokens', 0)
    
    return tracker.track_api_call(model, input_tokens, output_tokens, operation_type)

# 測試函數
def test_cost_tracker():
    """測試成本追踪功能"""
    print("測試成本追踪器...")
    
    tracker = CostTracker()
    
    # 模擬一些 API 調用
    tracker.track_api_call('gpt-5-mini', 100, 50, 'keyword_generation')
    tracker.track_api_call('gpt-5-nano', 200, 30, 'validation')
    tracker.track_api_call('gpt-5-nano', 150, 25, 'validation')
    
    # 顯示摘要
    print(tracker.format_cost_summary())
    
    return True

if __name__ == "__main__":
    test_cost_tracker()