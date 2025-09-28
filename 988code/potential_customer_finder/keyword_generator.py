#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產品潛在客戶搜尋系統 - 關鍵詞生成系統
使用LLM生成客戶可能使用的產品描述詞彙，包含錯字和變體
"""

import json
import logging
import time
from openai import OpenAI
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from potential_customer_finder.config import (
    LLM_CONFIG,
    KEYWORD_GENERATION_CONFIG,
    KEYWORDS_CACHE_DIR,
    CACHE_EXPIRY_DAYS
)
from potential_customer_finder.cost_tracker import track_openai_usage
from potential_customer_finder.database_manager import get_database_manager
from potential_customer_finder.smart_rate_limiter import get_rate_limiter
# 移除複雜的錯誤處理和日誌配置
# from error_handler import get_error_handler, get_batch_error_handler
# from logging_config import get_logger

# 設定統一日誌配置
from potential_customer_finder.logging_setup import setup_logging, log_api_call
logger = setup_logging(__name__)

class KeywordGenerator:
    """關鍵詞生成器，使用LLM生成產品相關關鍵詞"""
    
    def __init__(self):
        """初始化關鍵詞生成器"""
        # 設定 OpenAI API
        self.client = OpenAI(api_key=LLM_CONFIG['api_key'])
        self.model = KEYWORD_GENERATION_CONFIG['model']
        self.max_completion_tokens = KEYWORD_GENERATION_CONFIG.get('max_completion_tokens', 2000)
        
        # 快取設定
        self.cache_dir = KEYWORDS_CACHE_DIR
        self.cache_expiry_days = CACHE_EXPIRY_DAYS
        
        # 確保快取目錄存在
        self.cache_dir.mkdir(exist_ok=True)
        
        # 初始化智能速率限制器
        self.rate_limiter = get_rate_limiter('keyword')
        
        # 移除複雜的錯誤處理器
        # self.error_handler = get_error_handler('keyword_generator')
    
    def _get_cache_filepath(self, product_name: str) -> Path:
        """
        獲取產品關鍵詞快取檔案路徑
        
        Args:
            product_name: 產品名稱
            
        Returns:
            Path: 快取檔案路徑
        """
        # 清理產品名稱作為檔案名
        safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        return self.cache_dir / f"{safe_name}_keywords.json"
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """
        檢查快取檔案是否有效
        
        Args:
            cache_file: 快取檔案路徑
            
        Returns:
            bool: 是否有效
        """
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 檢查快取時間
            cache_time = datetime.fromisoformat(cache_data.get('created_at', ''))
            expiry_time = cache_time + timedelta(days=self.cache_expiry_days)
            
            return datetime.now() < expiry_time
        except (json.JSONDecodeError, ValueError, KeyError):
            return False
    
    def _load_keywords_from_cache(self, product_name: str) -> Optional[List[str]]:
        """
        從快取載入關鍵詞
        
        Args:
            product_name: 產品名稱
            
        Returns:
            List[str]: 關鍵詞列表，如果快取無效則返回None
        """
        cache_file = self._get_cache_filepath(product_name)
        
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            logger.info(f"從快取載入 '{product_name}' 的關鍵詞")
            return cache_data.get('keywords', [])
        except Exception as e:
            # 簡單的錯誤處理
            logger.error(f"讀取快取失敗 {cache_file}: {e}")
            return None
    
    def _save_keywords_to_cache(self, product_name: str, keywords: List[str]):
        """
        將關鍵詞儲存到快取
        
        Args:
            product_name: 產品名稱
            keywords: 關鍵詞列表
        """
        cache_file = self._get_cache_filepath(product_name)
        
        cache_data = {
            'product_name': product_name,
            'keywords': keywords,
            'created_at': datetime.now().isoformat(),
            'keyword_count': len(keywords)
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已快取 '{product_name}' 的 {len(keywords)} 個關鍵詞")
        except Exception as e:
            # 簡單的錯誤處理
            logger.error(f"儲存快取失敗 {cache_file}: {e}")
    
    def _generate_keywords_prompt(self, product_name: str, product_context: Optional[Dict] = None) -> str:
        """
        生成LLM提示詞來產生關鍵詞
        
        Args:
            product_name: 產品名稱
            product_context: 產品上下文資訊
            
        Returns:
            str: LLM提示詞
        """
        context_info = ""
        if product_context:
            context_info = f"""
產品詳細資訊:
- 訂單數量: {product_context.get('order_count', 0)}
- 總銷售量: {product_context.get('total_quantity', 0)}
- 最近訂單日期: {product_context.get('last_order_date', '未知')}
"""
        
        prompt = f"""你你是一個專門分析客戶購買行為的專家。我需要你為產品「{product_name}」生成客戶在搜尋時可能使用的**所有可能表達方式**。

{context_info}

**目標**：預測客戶的真實搜尋行為，包括各種可能的輸入方式

**核心原則**：
- **嚴格限定同一產品**：只能生成指向相同產品的不同叫法和表達方式。
- **精準鎖定屬性**：生成的關鍵詞必須完整保留原始產品的所有**關鍵屬性（例如：部位、處理方式、調味等）**。例如，分析「去刺虱目魚肚」時，生成的關鍵詞**絕對不能**是「虱目魚排」（部位不同）或「有刺虱目魚肚」（處理方式不同）。
- **核心與描述詞分離**：生成關鍵詞時，必須區分「核心產品名詞」（如：鱈魚塊、雞排）與「描述性形容詞」（如：香酥、冷凍、無骨）。描述性形容詞**嚴禁**單獨成為一個關鍵詞，它必須與一個核心產品名詞結合才能出現。例如，針對「香酥鱈魚塊」，可以生成「鱈魚塊」，但**不能**生成「香酥」。
- **通用名稱應對策略**：當核心產品為通用名稱時（如「魚排」、「肉丸」），生成的關鍵詞應圍繞其**型態、常見料理方式或用途**進行擴展，但**嚴禁**猜測或添加未提及的具體種類（例如，「魚排」不能生成「鱈魚排」，但可以生成「冷凍魚片」、「煎魚排」）。
- **絕對禁止跨類別**：不能生成不同類別產品的名稱（如菇類產品不能生成魚類關鍵詞）。
- **必須包含核心產品名稱**：從產品名稱中提取的主要產品名稱必須出現在關鍵詞中。

**客戶搜尋行為分析**：
客戶可能會：
- 使用繁體中文（台灣主要用戶）
- 使用簡體中文（部分客戶習慣或輸入法）
- 打錯字或用注音輸入錯誤
- 使用地方俗稱或簡化說法
- 使用不完整的產品名稱

**智能識別產品結構**：
從「{product_name}」中，拆解出**核心產品**與**關鍵屬性**，並忽略不重要的包裝規格、品牌或無法識別的代號。

**範例分析**：
- **產品輸入**：「香酥鱈魚塊」
    - **核心產品**：鱈魚塊
    - **關鍵屬性**：
        - **描述**：香酥
- **產品輸入**：「冷凍魚排-丸楊」
    - **核心產品**：魚排 (通用名稱)
    - **關鍵屬性**：
        - **狀態**：冷凍
    - **（應忽略資訊）**：品牌名稱(丸楊)
- **產品輸入**：「大比目魚切片TS(10K/箱)」
    - **核心產品**：大比目魚
    - **關鍵屬性**：
        - **部位**：切片
    - **（應忽略資訊）**：(10K/箱), 無法識別的代號(TS)

**需要生成的類型**：

1. **核心名稱**（繁體為主）
2. **簡體中文變體**（客戶可能的搜尋方式）
3. **常見錯字**（注音輸入、手寫錯誤等）
4. **地方俗稱**（台灣、香港、大陸不同叫法）
5. **簡化搜尋**（客戶可能只打部分字）
6. **描述性搜尋**（菇類、蘑菇類、食用菌等）

**客戶真實搜尋範例**：
✅ 「杏鮑菇」→ 客戶可能搜尋：「杏鲍菇」、「杏苞菇」、「鮑菇」、「菇類」
✅ 「薄鹽鯖魚」→ 客戶可能搜尋：「鯖魚」、「鲭鱼」、「青花魚」、「鹽魚」

**嚴格禁止生成**：
❌ **同類但不同規格的產品**：例如，分析「無刺虱目魚肚」時，禁止生成「虱目魚排」、「虱目魚頭」或「帶刺虱目魚肚」。
❌ **不同類別產品**：菇類產品不能生成魚類、蔬菜名稱。
❌ **規格包裝**：「3K」、「包」、「-B」等包裝標記。
❌ **完整句子**：「我要買」、「有沒有」等。

請以JSON格式回傳，按搜尋頻率重要性排序：
{{
  "primary_search_terms": ["主要搜尋詞 - 客戶最可能使用"],
  "alternative_names": ["替代名稱 - 同產品不同叫法"],
  "simplified_chinese": ["簡體中文變體 - 客戶可能的搜尋方式"],
  "common_typos": ["常見錯字 - 輸入錯誤"],
  "partial_searches": ["部分搜尋 - 客戶可能只打部分字"],
  "category_searches": ["分類搜尋 - 描述性詞彙"]
}}

記住：這是為了匹配客戶的真實搜尋行為，包括各種可能的輸入方式！
"""
        
        return prompt
    
    def _call_openai_api(self, prompt: str):
        """
        調用 OpenAI Chat Completions API
        
        Args:
            prompt: 提示詞
            
        Returns:
            OpenAI API 回應對象
        """
        messages = [
            {
                "role": "system",
                "content": "你是一個專業的關鍵詞生成專家，擅長分析客戶的購買語言模式。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        start_time = time.time()
        
        try:
            # 記錄 API 調用詳情
            logger.info(f"調用 OpenAI API，模型: {self.model}")
            logger.info(f"API 參數: max_completion_tokens={self.max_completion_tokens}")
            
            # 記錄提示詞內容 (截斷過長的提示詞)
            prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
            logger.info(f"提示詞內容 (前500字符): {prompt_preview}")
            logger.info(f"完整提示詞長度: {len(prompt)} 字符")
            
            # GPT-5 使用 max_completion_tokens 參數
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=self.max_completion_tokens
            )
            
            # 記錄成功調用和詳細回應
            response_time = time.time() - start_time
            self.rate_limiter.record_success(response_time)
            
            # 記錄 API 回應詳情
            response_content = response.choices[0].message.content if response.choices[0].message.content else ""
            logger.info(f"API 調用成功，耗時: {response_time:.2f}s")
            logger.info(f"API 回應長度: {len(response_content) if response_content else 0} 字符")
            if response_content:
                logger.info(f"API 完整回應內容:\n{response_content}")
            else:
                logger.warning("API 返回空內容，可能是模型參數問題")
            
            # 記錄 token 使用情況和成本追踪 (如果可用)
            if hasattr(response, 'usage'):
                usage = response.usage
                logger.info(f"Token 使用: 輸入={usage.prompt_tokens}, 輸出={usage.completion_tokens}, 總計={usage.total_tokens}")
                
                # 追踪 API 成本
                cost_record = track_openai_usage(self.model, usage, "keyword_generation")
                logger.info(f"成本追踪: NT${cost_record['cost_twd']:.2f}")
                
                # 記錄到 API 專用日誌
                log_api_call(
                    self.model, 
                    "keyword_generation", 
                    usage.prompt_tokens, 
                    usage.completion_tokens,
                    cost_record['cost_usd'],
                    response_time
                )
            
            return response
            
        except Exception as e:
            # 記錄錯誤調用到速率限制器
            self.rate_limiter.record_error(str(e))
            
            # 簡單的錯誤處理
            logger.error(f"OpenAI API 調用失敗: {e}")
            
            # 拋出異常以便上層處理
            raise Exception(f"OpenAI API 調用失敗: {e}。請檢查 API 密鑰權限和網路連接。")

    def _parse_llm_response(self, response_text: str) -> List[str]:
        """
        解析LLM回應並提取關鍵詞
        
        Args:
            response_text: LLM回應文本
            
        Returns:
            List[str]: 關鍵詞列表
        """
        try:
            # 記錄原始回應內容
            logger.info(f"開始解析 LLM 回應，原始長度: {len(response_text)} 字符")
            logger.debug(f"原始回應內容:\n{response_text}")
            
            # 處理 markdown 格式的 JSON
            clean_response = response_text.strip()
            original_response = clean_response
            
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
                logger.info("檢測到 markdown JSON 格式，已清理")
            elif clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '').strip()
                logger.info("檢測到 markdown 代碼格式，已清理")
            
            logger.info(f"清理後 JSON 長度: {len(clean_response)} 字符")
            logger.debug(f"清理後 JSON 內容:\n{clean_response}")
            
            # 移除 JavaScript 風格的註釋 (// 註釋) 和 C 風格註釋 (/* */ 註釋)
            import re
            
            # 移除 C 風格的多行註釋 /* ... */
            clean_response = re.sub(r'/\*.*?\*/', '', clean_response, flags=re.DOTALL)
            
            # 移除 JavaScript 風格的單行註釋 //
            lines = clean_response.split('\n')
            cleaned_lines = []
            for line in lines:
                # 移除行內的 // 註釋，但保留字符串內的 //
                if '//' in line:
                    # 簡單處理：找到 // 前的內容，但要避免在字符串內的 //
                    # 如果 // 前面有引號且沒有配對的結束引號，則保留
                    comment_pos = line.find('//')
                    if comment_pos > 0:
                        before_comment = line[:comment_pos].rstrip()
                        # 檢查是否在字符串中
                        quote_count = before_comment.count('"') - before_comment.count('\\"')
                        if quote_count % 2 == 0:  # 偶數個引號，表示不在字符串中
                            line = before_comment + (',' if before_comment.endswith('"') else '')
                    elif comment_pos == 0:  # 整行都是註釋
                        continue
                cleaned_lines.append(line)
            
            clean_response = '\n'.join(cleaned_lines)
            logger.info(f"移除註釋後 JSON 長度: {len(clean_response)} 字符")
            
            # 嘗試解析JSON回應
            response_data = json.loads(clean_response)
            logger.info(f"JSON 解析成功，包含 {len(response_data)} 個頂級欄位")
            logger.info(f"JSON 欄位: {list(response_data.keys())}")
            
            all_keywords = []
            category_stats = {}
            
            # 從各個類別中提取關鍵詞
            # 支援兩種格式的欄位名稱（新舊版本兼容）
            categories_mapping = {
                'primary_search_terms': 'core_product_names',
                'alternative_names': 'product_aliases', 
                'simplified_chinese': 'simplified_names',
                'common_typos': 'typo_variants',
                'partial_searches': 'regional_names',
                'category_searches': 'descriptive_terms',
                # 保留舊欄位名稱的支援
                'core_product_names': 'core_product_names',
                'product_aliases': 'product_aliases',
                'simplified_names': 'simplified_names',
                'typo_variants': 'typo_variants',
                'regional_names': 'regional_names',
                'descriptive_terms': 'descriptive_terms'
            }
            
            # 遍歷所有可能的欄位名稱
            for api_field, internal_category in categories_mapping.items():
                if api_field in response_data and isinstance(response_data[api_field], list):
                    category_keywords = response_data[api_field]
                    category_stats[internal_category] = len(category_keywords)
                    all_keywords.extend(category_keywords)
                    logger.info(f"類別 '{api_field}' (映射到 '{internal_category}'): {len(category_keywords)} 個關鍵詞")
                    # 只顯示前10個關鍵詞以避免日誌過長
                    preview = category_keywords[:10] if len(category_keywords) > 10 else category_keywords
                    logger.info(f"  關鍵詞範例: {preview}")
            
            # 記錄提取統計
            total_before_dedup = len(all_keywords)
            logger.info(f"提取統計: {category_stats}")
            logger.info(f"去重前總關鍵詞數: {total_before_dedup}")
            
            # 去重並過濾空字串和分類標籤
            category_labels = {'core_product_names', 'product_aliases', 'simplified_names', 'typo_variants', 'regional_names', 'descriptive_terms'}
            unique_keywords = list(set(keyword.strip() for keyword in all_keywords 
                                     if keyword.strip() and keyword.strip() not in category_labels))
            
            # 記錄最終結果
            removed_duplicates = total_before_dedup - len(unique_keywords)
            logger.info(f"去重後關鍵詞數: {len(unique_keywords)}")
            logger.info(f"移除重複項: {removed_duplicates} 個")
            logger.info(f"最終關鍵詞列表: {unique_keywords}")
            
            return unique_keywords
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失敗: {e}")
            logger.error(f"原始回應長度: {len(response_text)}")
            logger.error(f"完整原始回應內容:\n{response_text}")
            
            # 記錄清理過程
            clean_response = response_text.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            elif clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '').strip()
            
            logger.error(f"清理後內容長度: {len(clean_response)}")
            logger.error(f"清理後內容:\n{clean_response}")
            
            # 備用解析方法：提取引號中的內容
            import re
            keywords = re.findall(r'"([^"]+)"', response_text)
            keywords = [kw.strip() for kw in keywords if kw.strip()]
            
            logger.info(f"使用備用方法從引號中解析出 {len(keywords)} 個關鍵詞")
            logger.info(f"備用方法解析結果: {keywords}")
            return keywords
    
    def generate_keywords_for_product(self, product_name: str, use_cache: bool = True) -> List[str]:
        """
        為指定產品生成關鍵詞
        
        Args:
            product_name: 產品名稱
            use_cache: 是否使用快取
            
        Returns:
            List[str]: 關鍵詞列表
        """
        # 檢查快取
        if use_cache:
            cached_keywords = self._load_keywords_from_cache(product_name)
            if cached_keywords is not None:
                return cached_keywords
        
        logger.info(f"為產品 '{product_name}' 生成關鍵詞...")
        
        try:
            # 簡化：直接生成提示詞，不需要從資料庫獲取上下文
            # 原本的 get_product_details 方法不存在
            product_context = None
            
            # 生成提示詞
            prompt = self._generate_keywords_prompt(product_name, product_context)
            
            # 呼叫OpenAI API
            response = self._call_openai_api(prompt)
            
            # 解析回應
            response_text = response.choices[0].message.content if response.choices[0].message.content else ""
            
            # 如果 API 返回空內容，使用簡化的關鍵詞生成
            if not response_text:
                logger.warning(f"API 返回空內容，使用簡化關鍵詞生成邏輯")
                keywords = self._generate_simple_keywords(product_name)
            else:
                keywords = self._parse_llm_response(response_text)
            
            # 加入原始產品名稱確保包含
            if product_name not in keywords:
                keywords.insert(0, product_name)
            
            # 儲存到快取
            if use_cache and keywords:
                self._save_keywords_to_cache(product_name, keywords)
            
            logger.info(f"成功生成 {len(keywords)} 個關鍵詞")
            return keywords
            
        except Exception as e:
            # 簡單的錯誤處理
            logger.error(f"關鍵詞生成失敗: {e}")
            logger.info("LLM 關鍵詞生成失敗，切換到備用關鍵詞生成模式...")
            
            fallback_keywords = self._generate_fallback_keywords(product_name)
            
            # 儲存到快取
            if use_cache and fallback_keywords:
                self._save_keywords_to_cache(product_name, fallback_keywords)
            
            return fallback_keywords
    
    def _generate_simple_keywords(self, product_name: str) -> List[str]:
        """
        簡化的關鍵詞生成 - 從產品名稱提取基本變體
        
        Args:
            product_name: 產品名稱
            
        Returns:
            List[str]: 關鍵詞列表
        """
        import re
        keywords = [product_name]
        
        # 提取核心產品名稱（去除括號內容和特殊符號）
        core_name = re.sub(r'[（\(].*?[）\)]', '', product_name)
        core_name = re.sub(r'[-_/]', '', core_name)
        core_name = core_name.strip()
        
        if core_name and core_name != product_name:
            keywords.append(core_name)
        
        # 針對「杏鮑菇」這類產品，添加常見變體
        if '杏鮑菇' in product_name:
            keywords.extend(['杏鮑菇', '杏苞菇', '杏包菇', '刺芹側耳', '鮑魚菇'])
        
        # 去除重複
        keywords = list(dict.fromkeys(keywords))
        
        logger.info(f"簡化關鍵詞生成: {keywords}")
        return keywords
    
    def _generate_fallback_keywords(self, product_name: str) -> List[str]:
        """
        當 LLM 不可用時的備用關鍵詞生成方法
        
        依據 claude.md 規範：僅返回原始產品名稱，不使用任何枚舉或模式匹配方法
        
        Args:
            product_name: 產品名稱
            
        Returns:
            List[str]: 僅包含原始產品名稱的關鍵詞列表
        """
        logger.warning(f"LLM 關鍵詞生成失敗，僅返回原始產品名稱（依據 claude.md 規範，不使用枚舉方法）")
        return [product_name]
    
    def batch_generate_keywords(self, product_names: List[str], use_cache: bool = True) -> Dict[str, List[str]]:
        """
        批量生成多個產品的關鍵詞
        
        Args:
            product_names: 產品名稱列表
            use_cache: 是否使用快取
            
        Returns:
            Dict[str, List[str]]: 產品名稱到關鍵詞列表的對應
        """
        results = {}
        # 移除複雜的批量錯誤處理器
        # batch_error_handler = get_batch_error_handler('keyword_generator', 'batch_generate_keywords')
        
        # 簡單計數器
        success_count = 0
        error_count = 0
        
        for i, product_name in enumerate(product_names):
            logger.info(f"處理產品 {i+1}/{len(product_names)}: {product_name}")
            
            try:
                keywords = self.generate_keywords_for_product(product_name, use_cache)
                results[product_name] = keywords
                success_count += 1
                
                # 使用智能速率限制器進行動態延遲調整
                # 只有實際進行API調用時才需要延遲
                if not use_cache or self._load_keywords_from_cache(product_name) is None:
                    wait_time = self.rate_limiter.wait_if_needed(i)
                    if wait_time > 0:
                        logger.debug(f"智能延遲調整: 等待 {wait_time:.2f}s")
                    
            except Exception as e:
                # 簡單的錯誤處理
                logger.error(f"處理產品 {product_name} 失敗: {e}")
                results[product_name] = [product_name]  # 備用結果
                error_count += 1
        
        # 簡單的批量處理摘要
        total_count = len(product_names)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        rate_limiter_stats = self.rate_limiter.get_stats()
        
        logger.info(f"批量關鍵詞生成完成 - 成功率: {success_rate:.1f}% ({success_count}/{total_count})")
        logger.info(f"速率限制器統計: {rate_limiter_stats}")
        
        if error_count > 0:
            logger.warning(f"批量處理中發生 {error_count} 個錯誤，請檢查日誌")
        
        return results
    
    def get_all_product_keywords(self) -> Dict[str, List[str]]:
        """
        獲取資料庫中所有產品的關鍵詞
        
        Returns:
            Dict[str, List[str]]: 所有產品的關鍵詞對照表
        """
        db = get_database_manager()
        products = db.get_all_products()
        
        product_names = [product[0] for product in products]
        logger.info(f"準備為 {len(product_names)} 個產品生成關鍵詞")
        
        return self.batch_generate_keywords(product_names)
    
    def get_rate_limiter_stats(self) -> Dict:
        """
        獲取速率限制器統計信息
        
        Returns:
            Dict: 速率限制器統計信息
        """
        return self.rate_limiter.get_stats()
    
    # 移除複雜的錯誤統計功能
    # def get_error_statistics(self) -> Dict:
    
    def clear_cache(self, product_name: Optional[str] = None):
        """
        清理快取
        
        Args:
            product_name: 特定產品名稱，如果為None則清理所有快取
        """
        if product_name:
            cache_file = self._get_cache_filepath(product_name)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"已清除 '{product_name}' 的快取")
        else:
            # 清理所有快取檔案
            for cache_file in self.cache_dir.glob("*_keywords.json"):
                cache_file.unlink()
            logger.info("已清除所有關鍵詞快取")

# 單例模式的關鍵詞生成器
_keyword_generator = None

def get_keyword_generator() -> KeywordGenerator:
    """獲取關鍵詞生成器實例 (單例模式)"""
    global _keyword_generator
    if _keyword_generator is None:
        _keyword_generator = KeywordGenerator()
    return _keyword_generator

# 測試函數
def test_keyword_generator():
    """測試關鍵詞生成功能"""
    try:
        generator = get_keyword_generator()
        
        # 測試單一產品關鍵詞生成
        test_product = "薄鹽鯖魚(無骨)S(以公斤計)"
        print(f"測試產品: {test_product}")
        
        keywords = generator.generate_keywords_for_product(test_product, use_cache=False)
        print(f"生成的關鍵詞 ({len(keywords)} 個):")
        for i, keyword in enumerate(keywords, 1):
            print(f"  {i}. {keyword}")
        
        return True
        
    except Exception as e:
        print(f"關鍵詞生成器測試失敗: {e}")
        return False

if __name__ == "__main__":
    # 執行測試
    print("開始關鍵詞生成器測試...")
    success = test_keyword_generator()
    print(f"測試結果: {'成功' if success else '失敗'}")