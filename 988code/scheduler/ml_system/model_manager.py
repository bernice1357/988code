#!/usr/bin/env python3
"""
模型管理器
負責模型版本管理、部署和回滾
"""

import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path

try:
    from config import MLConfig  # 直接導入（ml_system目錄內）
except ImportError:
    from ml_system.config import MLConfig  # 外部導入

class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self.setup_logging()
        MLConfig.ensure_directories()
        
        print("=== CatBoost模型管理器 ===")
        print(f"模型目錄: {MLConfig.MODEL_DIR}")
        print(f"當前模型目錄: {MLConfig.CURRENT_MODEL_DIR}")
        print(f"歸檔目錄: {MLConfig.ARCHIVE_MODEL_DIR}")
    
    def setup_logging(self):
        """設置日誌"""
        log_file = os.path.join(MLConfig.LOG_DIR, f'model_manager_{datetime.now().strftime("%Y%m")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def deploy_new_model(self, trained_model_dir):
        """部署新訓練的模型"""
        self.logger.info(f"開始部署新模型: {trained_model_dir}")
        
        try:
            # 1. 驗證新模型
            if not self._validate_model_files(trained_model_dir):
                self.logger.error("新模型文件驗證失敗")
                return False
            
            # 2. 備份當前模型
            if not self._backup_current_model():
                self.logger.error("備份當前模型失敗")
                return False
            
            # 3. 部署新模型
            if not self._deploy_model_files(trained_model_dir):
                self.logger.error("部署模型文件失敗")
                return False
            
            self.logger.info("新模型部署成功")
            return True
            
        except Exception as e:
            self.logger.error(f"部署新模型異常: {e}")
            return False
    
    def _validate_model_files(self, model_dir):
        """驗證模型文件完整性"""
        required_files = [
            MLConfig.MODEL_FILE,
            MLConfig.FEATURE_NAMES_FILE,
            MLConfig.METADATA_FILE
        ]
        
        for file_name in required_files:
            file_path = os.path.join(model_dir, file_name)
            if not os.path.exists(file_path):
                self.logger.error(f"缺少必要文件: {file_path}")
                return False
        
        # 驗證元數據文件
        try:
            metadata_path = os.path.join(model_dir, MLConfig.METADATA_FILE)
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 檢查必要字段
            required_fields = ['model_type', 'created_at', 'feature_count']
            for field in required_fields:
                if field not in metadata:
                    self.logger.error(f"元數據缺少字段: {field}")
                    return False
            
            self.logger.info(f"模型驗證通過: {metadata.get('model_type')}, 特徵數: {metadata.get('feature_count')}")
            return True
            
        except Exception as e:
            self.logger.error(f"元數據驗證失敗: {e}")
            return False
    
    def _backup_current_model(self):
        """備份當前模型到歸檔目錄"""
        try:
            # 檢查是否有當前模型需要備份
            if not os.path.exists(MLConfig.get_current_model_path()):
                self.logger.info("沒有當前模型需要備份")
                return True
            
            # 讀取當前模型的元數據
            try:
                with open(MLConfig.get_metadata_path(), 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                created_at = metadata.get('created_at', datetime.now().isoformat())
            except:
                created_at = datetime.now().isoformat()
            
            # 生成備份目錄名
            timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%Y%m%d_%H%M%S')
            backup_dir_name = f"catboost_model_{timestamp}"
            backup_path = os.path.join(MLConfig.ARCHIVE_MODEL_DIR, backup_dir_name)
            
            # 創建備份目錄
            os.makedirs(backup_path, exist_ok=True)
            
            # 複製模型文件
            files_to_backup = [
                MLConfig.MODEL_FILE,
                MLConfig.FEATURE_NAMES_FILE,
                MLConfig.METADATA_FILE
            ]
            
            for file_name in files_to_backup:
                src_path = os.path.join(MLConfig.CURRENT_MODEL_DIR, file_name)
                dst_path = os.path.join(backup_path, file_name)
                
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)
            
            self.logger.info(f"當前模型已備份到: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"備份當前模型失敗: {e}")
            return False
    
    def _deploy_model_files(self, source_dir):
        """將模型文件部署到當前目錄"""
        try:
            files_to_deploy = [
                MLConfig.MODEL_FILE,
                MLConfig.FEATURE_NAMES_FILE,
                MLConfig.METADATA_FILE
            ]
            
            for file_name in files_to_deploy:
                src_path = os.path.join(source_dir, file_name)
                dst_path = os.path.join(MLConfig.CURRENT_MODEL_DIR, file_name)
                
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)
                    self.logger.info(f"部署文件: {file_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"部署模型文件失敗: {e}")
            return False
    
    def list_available_models(self):
        """列出所有可用的模型版本"""
        try:
            models = []
            
            # 當前模型
            if os.path.exists(MLConfig.get_current_model_path()):
                try:
                    with open(MLConfig.get_metadata_path(), 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    models.append({
                        'version': 'current',
                        'path': MLConfig.CURRENT_MODEL_DIR,
                        'created_at': metadata.get('created_at'),
                        'model_type': metadata.get('model_type'),
                        'feature_count': metadata.get('feature_count'),
                        'f1_score': metadata.get('metrics', {}).get('f1_score'),
                        'is_current': True
                    })
                except Exception as e:
                    self.logger.warning(f"讀取當前模型元數據失敗: {e}")
            
            # 歸檔模型
            if os.path.exists(MLConfig.ARCHIVE_MODEL_DIR):
                for item in os.listdir(MLConfig.ARCHIVE_MODEL_DIR):
                    item_path = os.path.join(MLConfig.ARCHIVE_MODEL_DIR, item)
                    if os.path.isdir(item_path):
                        metadata_path = os.path.join(item_path, MLConfig.METADATA_FILE)
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                
                                models.append({
                                    'version': item,
                                    'path': item_path,
                                    'created_at': metadata.get('created_at'),
                                    'model_type': metadata.get('model_type'),
                                    'feature_count': metadata.get('feature_count'),
                                    'f1_score': metadata.get('metrics', {}).get('f1_score'),
                                    'is_current': False
                                })
                            except Exception as e:
                                self.logger.warning(f"讀取歷史模型 {item} 元數據失敗: {e}")
            
            # 按時間排序
            models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return models
            
        except Exception as e:
            self.logger.error(f"列出可用模型失敗: {e}")
            return []
    
    def rollback_to_previous_model(self):
        """回滾到上一個版本的模型"""
        self.logger.info("開始回滾到上一個模型版本...")
        
        try:
            # 獲取可用模型列表
            models = self.list_available_models()
            archived_models = [m for m in models if not m['is_current']]
            
            if not archived_models:
                self.logger.error("沒有可回滾的歷史模型")
                return False
            
            # 選擇最新的歷史模型
            previous_model = archived_models[0]
            self.logger.info(f"回滾到模型: {previous_model['version']}")
            
            # 備份當前模型
            if not self._backup_current_model():
                self.logger.error("備份當前模型失敗")
                return False
            
            # 部署歷史模型
            if not self._deploy_model_files(previous_model['path']):
                self.logger.error("部署歷史模型失敗")
                return False
            
            self.logger.info(f"成功回滾到模型版本: {previous_model['version']}")
            return True
            
        except Exception as e:
            self.logger.error(f"模型回滾異常: {e}")
            return False
    
    def cleanup_old_models(self, keep_count=5):
        """清理舊的模型版本，保留最新的幾個"""
        self.logger.info(f"開始清理舊模型，保留最新 {keep_count} 個版本...")
        
        try:
            models = self.list_available_models()
            archived_models = [m for m in models if not m['is_current']]
            
            if len(archived_models) <= keep_count:
                self.logger.info(f"當前歷史模型數量: {len(archived_models)}，無需清理")
                return True
            
            # 按時間排序，刪除舊的模型
            models_to_delete = archived_models[keep_count:]
            deleted_count = 0
            
            for model in models_to_delete:
                try:
                    if os.path.exists(model['path']):
                        shutil.rmtree(model['path'])
                        deleted_count += 1
                        self.logger.info(f"刪除舊模型: {model['version']}")
                except Exception as e:
                    self.logger.warning(f"刪除模型 {model['version']} 失敗: {e}")
            
            self.logger.info(f"清理完成，刪除了 {deleted_count} 個舊模型版本")
            return True
            
        except Exception as e:
            self.logger.error(f"清理舊模型異常: {e}")
            return False
    
    def get_current_model_info(self):
        """獲取當前模型信息"""
        try:
            if not os.path.exists(MLConfig.get_current_model_path()):
                return {'status': 'no_model', 'message': '沒有當前模型'}
            
            with open(MLConfig.get_metadata_path(), 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return {
                'status': 'active',
                'model_type': metadata.get('model_type'),
                'created_at': metadata.get('created_at'),
                'feature_count': metadata.get('feature_count'),
                'training_data_months': metadata.get('training_data_months'),
                'f1_score': metadata.get('metrics', {}).get('f1_score'),
                'precision': metadata.get('metrics', {}).get('precision'),
                'recall': metadata.get('metrics', {}).get('recall')
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

def main():
    """測試函數"""
    print("=== 模型管理器測試 ===")
    
    manager = ModelManager()
    
    # 列出可用模型
    models = manager.list_available_models()
    print(f"可用模型數量: {len(models)}")
    
    for model in models:
        status = "【當前】" if model['is_current'] else "【歷史】"
        print(f"{status} {model['version']}: {model.get('created_at', 'Unknown')} (F1: {model.get('f1_score', 'N/A')})")
    
    # 獲取當前模型信息
    current_info = manager.get_current_model_info()
    print(f"當前模型狀態: {current_info}")
    
    # 清理舊模型
    manager.cleanup_old_models(keep_count=3)
    
    return len(models) > 0

if __name__ == "__main__":
    main()