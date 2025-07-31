import psycopg2
from psycopg2 import Error
import bcrypt
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets
import DATABASE_CONFIG, APP_CONFIG  # 導入配置


class LoginSystem:
    def __init__(self):
        """初始化登入系統"""
        self.db_config = DATABASE_CONFIG
        self.connection = None
        
        # 這個模組專用的表配置
        self.table_config = {
            'users': 'users'
        }
        
        # 會話存儲 (實際應用中建議使用 Redis 或數據庫)
        self.sessions = {}
        
        # 設定日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def connect_database(self):
        """連接到資料庫"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.username,
                password=self.db_config.password,
                connect_timeout=APP_CONFIG.get('timeout', 30)  # 默認30秒超時
            )
            self.connection.autocommit = False
            self.logger.info("數據庫連接成功")
            return True
        except Error as e:
            self.logger.error(f"數據庫連接失敗: {e}")
            return False

    def close_connection(self):
        """關閉數據庫連接"""
        if self.connection:
            self.connection.close()
            self.logger.info("數據庫連接已關閉")

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        驗證用戶登入
        
        Args:
            username: 用戶名或郵箱
            password: 密碼
            
        Returns:
            用戶資訊字典或 None
        """
        try:
            cursor = self.connection.cursor()
            
            # 使用表配置
            users_table = self.table_config['users']
            
            # 查詢用戶（支援用戶名或郵箱登入）
            query = f"""
                SELECT id, username, email, password_hash, full_name, role, is_active
                FROM {users_table} 
                WHERE (username = %s OR email = %s) AND is_active = TRUE
            """
            cursor.execute(query, (username, username))
            user_data = cursor.fetchone()
            
            if not user_data:
                self.logger.warning(f"用戶不存在或已停用: {username}")
                cursor.close()
                return None
            
            # 解包用戶資料
            user_id, user_username, email, password_hash, full_name, role, is_active = user_data
            
            # 驗證密碼
            if bcrypt.checkpw(password.encode(), password_hash.encode()):
                cursor.close()
                return {
                    'id': user_id,
                    'username': user_username,
                    'email': email,
                    'full_name': full_name,
                    'role': role,
                    'is_active': is_active
                }
            else:
                self.logger.warning(f"用戶 {username} 密碼錯誤")
                cursor.close()
                return None
                
        except Error as e:
            self.logger.error(f"認證過程中發生錯誤: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def login(self, username: str, password: str) -> Optional[str]:
        """
        用戶登入
        
        Args:
            username: 用戶名或郵箱
            password: 密碼
            
        Returns:
            會話令牌或 None
        """
        user = self.authenticate_user(username, password)
        if user:
            # 生成會話令牌
            session_token = self._generate_session_token()
            
            # 存儲會話資訊
            self.sessions[session_token] = {
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role'],
                'login_time': datetime.now(),
                'expires_at': datetime.now() + timedelta(hours=24)  # 24小時過期
            }
            
            self.logger.info(f"用戶 {username} 登入成功")
            return session_token
        return None

    def logout(self, session_token: str) -> bool:
        """
        用戶登出
        
        Args:
            session_token: 會話令牌
            
        Returns:
            是否成功登出
        """
        if session_token in self.sessions:
            username = self.sessions[session_token]['username']
            del self.sessions[session_token]
            self.logger.info(f"用戶 {username} 登出成功")
            return True
        return False

    def get_current_user(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        獲取當前登入用戶資訊
        
        Args:
            session_token: 會話令牌
            
        Returns:
            用戶資訊或 None
        """
        if session_token not in self.sessions:
            return None
            
        session = self.sessions[session_token]
        
        # 檢查會話是否過期
        if datetime.now() > session['expires_at']:
            del self.sessions[session_token]
            self.logger.info(f"會話已過期: {session['username']}")
            return None
            
        return session

    def is_logged_in(self, session_token: str) -> bool:
        """
        檢查用戶是否已登入
        
        Args:
            session_token: 會話令牌
            
        Returns:
            是否已登入
        """
        return self.get_current_user(session_token) is not None

    def change_password(self, session_token: str, old_password: str, new_password: str) -> bool:
        """
        更改密碼
        
        Args:
            session_token: 會話令牌
            old_password: 舊密碼
            new_password: 新密碼
            
        Returns:
            是否成功更改
        """
        user = self.get_current_user(session_token)
        if not user:
            return False
            
        # 驗證舊密碼
        if not self.authenticate_user(user['username'], old_password):
            self.logger.warning(f"用戶 {user['username']} 舊密碼驗證失敗")
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # 使用表配置
            users_table = self.table_config['users']
            
            # 加密新密碼
            new_password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            
            # 更新密碼
            update_query = f"""
                UPDATE {users_table} 
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """
            cursor.execute(update_query, (new_password_hash, user['user_id']))
            self.connection.commit()
            cursor.close()
            
            self.logger.info(f"用戶 {user['username']} 密碼更改成功")
            return True
            
        except Error as e:
            self.logger.error(f"更改密碼失敗: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def get_user_role(self, session_token: str) -> Optional[str]:
        """
        獲取用戶角色
        
        Args:
            session_token: 會話令牌
            
        Returns:
            用戶角色或 None
        """
        user = self.get_current_user(session_token)
        return user['role'] if user else None

    def check_permission(self, session_token: str, required_role: str) -> bool:
        """
        檢查用戶權限
        
        Args:
            session_token: 會話令牌
            required_role: 需要的角色
            
        Returns:
            是否有權限
        """
        user_role = self.get_user_role(session_token)
        if not user_role:
            return False
            
        # 簡單的角色階層 admin > moderator > user
        role_hierarchy = {'admin': 3, 'moderator': 2, 'user': 1}
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level

    def _generate_session_token(self) -> str:
        """生成會話令牌"""
        return secrets.token_urlsafe(32)

    def cleanup_expired_sessions(self):
        """清理過期會話"""
        current_time = datetime.now()
        expired_tokens = [
            token for token, session in self.sessions.items()
            if current_time > session['expires_at']
        ]
        
        for token in expired_tokens:
            username = self.sessions[token]['username']
            del self.sessions[token]
            self.logger.info(f"清理過期會話: {username}")

    def get_active_sessions_count(self) -> int:
        """獲取活躍會話數量"""
        self.cleanup_expired_sessions()
        return len(self.sessions)

    # 向下兼容的方法 (可選)
    def connect(self):
        """向下兼容的連接方法"""
        return self.connect_database()
    
    def close(self):
        """向下兼容的關閉方法"""
        self.close_connection()