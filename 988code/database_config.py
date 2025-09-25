"""
統一資料庫連線管理器
支援多環境配置和連線池管理
"""
import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional, Dict, Any
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """資料庫配置管理類別"""

    def __init__(self):
        self._connection_pools: Dict[str, psycopg2.pool.ThreadedConnectionPool] = {}
        self._load_config()

    def _load_config(self):
        """載入資料庫配置"""
        # 從環境變數載入配置，如果沒有則使用預設值
        self.configs = {
            'local': {
                'host': os.getenv('LOCAL_DB_HOST', 'localhost'),
                'port': os.getenv('LOCAL_DB_PORT', '5432'),
                'database': os.getenv('LOCAL_DB_NAME', '988'),
                'user': os.getenv('LOCAL_DB_USER', 'postgres'),
                'password': os.getenv('LOCAL_DB_PASSWORD', '988988'),
            },
            'remote': {
                'host': os.getenv('REMOTE_DB_HOST', ''),
                'port': os.getenv('REMOTE_DB_PORT', '5432'),
                'database': os.getenv('REMOTE_DB_NAME', '988'),
                'user': os.getenv('REMOTE_DB_USER', ''),
                'password': os.getenv('REMOTE_DB_PASSWORD', ''),
            }
        }

        # 決定預設環境
        self.default_env = os.getenv('DB_ENVIRONMENT', 'local')
        logger.info(f"資料庫環境設定為: {self.default_env}")

    def get_connection_pool(self, env: str = None) -> psycopg2.pool.ThreadedConnectionPool:
        """取得連線池"""
        env = env or self.default_env

        if env not in self._connection_pools:
            config = self.configs.get(env)
            if not config:
                raise ValueError(f"無效的環境名稱: {env}")

            try:
                self._connection_pools[env] = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=config['host'],
                    port=config['port'],
                    database=config['database'],
                    user=config['user'],
                    password=config['password'],
                    connect_timeout=10,
                    application_name='988_web_app'
                )
                logger.info(f"成功建立{env}環境連線池")
            except Exception as e:
                logger.error(f"建立{env}環境連線池失敗: {e}")
                raise

        return self._connection_pools[env]

    @contextmanager
    def get_connection(self, env: str = None):
        """取得資料庫連線的上下文管理器"""
        env = env or self.default_env
        pool = self.get_connection_pool(env)
        conn = None

        try:
            conn = pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"資料庫操作錯誤: {e}")
            raise
        finally:
            if conn:
                pool.putconn(conn)

    def execute_query(self, query: str, params: tuple = (), env: str = None, fetch: str = 'all'):
        """執行查詢"""
        with self.get_connection(env) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)

                if fetch == 'all':
                    return cursor.fetchall()
                elif fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'none':
                    conn.commit()
                    return cursor.rowcount
                else:
                    raise ValueError("fetch 參數必須是 'all', 'one', 或 'none'")

    def execute_transaction(self, queries_params: list, env: str = None):
        """執行事務（多個查詢）"""
        with self.get_connection(env) as conn:
            try:
                with conn.cursor() as cursor:
                    for query, params in queries_params:
                        cursor.execute(query, params)
                conn.commit()
                logger.info(f"事務執行成功，共執行{len(queries_params)}個查詢")
            except Exception as e:
                conn.rollback()
                logger.error(f"事務執行失敗: {e}")
                raise

    def test_connection(self, env: str = None) -> Dict[str, Any]:
        """測試資料庫連線"""
        env = env or self.default_env
        result = {'env': env, 'success': False, 'message': '', 'version': None}

        try:
            with self.get_connection(env) as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT version();')
                    result['version'] = cursor.fetchone()[0]
                    result['success'] = True
                    result['message'] = '連線成功'
                    logger.info(f"{env}環境連線測試成功")
        except Exception as e:
            result['message'] = str(e)
            logger.error(f"{env}環境連線測試失敗: {e}")

        return result

    def close_all_pools(self):
        """關閉所有連線池"""
        for env, pool in self._connection_pools.items():
            try:
                pool.closeall()
                logger.info(f"已關閉{env}環境連線池")
            except Exception as e:
                logger.error(f"關閉{env}環境連線池失敗: {e}")
        self._connection_pools.clear()

# 全域資料庫配置實例
db_config = DatabaseConfig()

# 便利函數
def get_db_connection(env: str = None):
    """取得資料庫連線（便利函數）"""
    return db_config.get_connection(env)

def execute_query(query: str, params: tuple = (), env: str = None, fetch: str = 'all'):
    """執行查詢（便利函數）"""
    return db_config.execute_query(query, params, env, fetch)

def execute_transaction(queries_params: list, env: str = None):
    """執行事務（便利函數）"""
    return db_config.execute_transaction(queries_params, env)

def test_db_connection(env: str = None):
    """測試資料庫連線（便利函數）"""
    return db_config.test_connection(env)