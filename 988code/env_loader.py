"""
環境變數載入器
在應用程式啟動時載入 .env 檔案
"""
import os
from pathlib import Path

def load_env_file(env_file_path: str = None):
    """載入 .env 檔案中的環境變數"""

    if env_file_path is None:
        # 尋找 .env 檔案
        current_dir = Path(__file__).parent
        env_file_path = current_dir / '.env'

    if not os.path.exists(env_file_path):
        print(f"警告: .env 檔案不存在: {env_file_path}")
        return False

    try:
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # 忽略空行和註解
                if not line or line.startswith('#'):
                    continue

                # 分析 KEY=VALUE 格式
                if '=' not in line:
                    print(f"警告: .env 檔案第{line_num}行格式錯誤: {line}")
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # 移除值兩邊的引號（如果有）
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                # 設定環境變數（不覆蓋已存在的）
                if key not in os.environ:
                    os.environ[key] = value

        print(f"成功載入環境變數: {env_file_path}")
        return True

    except Exception as e:
        print(f"載入 .env 檔案失敗: {e}")
        return False

def get_env(key: str, default: str = None):
    """取得環境變數值"""
    return os.getenv(key, default)

def get_env_bool(key: str, default: bool = False):
    """取得布林型環境變數"""
    value = os.getenv(key, '').lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int = 0):
    """取得整數型環境變數"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

# 自動載入 .env 檔案（當模組被匯入時）
if __name__ != "__main__":
    load_env_file()