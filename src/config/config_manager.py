"""設定ファイルを管理するモジュール"""
import json
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigManager:
    def __init__(self, config_path: str = "agent_settings.json"):
        """
        設定マネージャーの初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """設定ファイルを読み込む"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            self._config = {}
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """エージェントの設定を取得"""
        return self._config.get("agents", {}).get(agent_name, {})
    
    def get_rag_config(self) -> Dict[str, Any]:
        """RAGデータベースの設定を取得"""
        return self._config.get("rag_database", {})
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """埋め込みモデルの設定を取得"""
        return self._config.get("embedding", {})
    
    def save_config(self) -> None:
        """設定をファイルに保存"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
