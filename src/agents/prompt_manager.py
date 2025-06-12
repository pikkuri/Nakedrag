#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
プロンプトマネージャーモジュール

AIエージェントのプロンプト、ロール、システムメッセージを管理するためのモジュールです。
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class PromptManager:
    """
    AIエージェントのプロンプト、ロール、システムメッセージを管理するクラス
    
    このクラスは以下の機能を提供します：
    1. 各種AIエージェントのロールとシステムメッセージの管理
    2. プロンプトテンプレートの管理
    3. 動的なプロンプト生成
    """
    
    def __init__(self, agent_name: str = "librarian"):
        """プロンプトマネージャーの初期化

        Args:
            agent_name: エージェントの名前（デフォルトは"librarian"）
        """
        from config.config_manager import ConfigManager
        self.config = ConfigManager()
        self.agent_name = agent_name
        self.agent_config = self.config.get_agent_config(agent_name)
        
        if not self.agent_config:
            raise ValueError(f"Agent '{agent_name}' not found in configuration")
        
        # システムメッセージの準備
        system_message = self.agent_config.get("system_message", {})
        self.system_message = "\n".join(system_message.get("content", []))
        
        # RAGデータベース説明の準備
        rag_intro = self.agent_config.get("rag_database_introduction", {})
        self.rag_database_introduction = "\n".join(rag_intro.get("content", []))
        
        # テンプレートの準備
        self.templates = self.agent_config.get("templates", {})
    
    def _load_prompts(self) -> Dict[str, Any]:
        """
        プロンプトファイルからプロンプト定義を読み込みます
        
        Returns:
            プロンプト定義の辞書
        """
        prompts = {}
        prompt_dir_path = Path(self.prompt_dir)
        
        if not prompt_dir_path.exists():
            return self._default_prompts
        
        for file_path in prompt_dir_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                    agent_name = file_path.stem
                    prompts[agent_name] = prompt_data
            except Exception as e:
                print(f"プロンプトファイル {file_path} の読み込みに失敗しました: {e}")
        
        # デフォルトのプロンプトで不足しているものを補完
        for agent_name, prompt_data in self._default_prompts.items():
            if agent_name not in prompts:
                prompts[agent_name] = prompt_data
        
        return prompts
    
    def save_prompts(self) -> None:
        """
        現在のプロンプト定義をファイルに保存します
        """
        if not self.prompt_dir:
            return
        
        prompt_dir_path = Path(self.prompt_dir)
        prompt_dir_path.mkdir(parents=True, exist_ok=True)
        
        for agent_name, prompt_data in self.prompts.items():
            file_path = prompt_dir_path / f"{agent_name}.json"
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"プロンプトファイル {file_path} の保存に失敗しました: {e}")
    
    def get_role(self, agent_type: str) -> str:
        """
        エージェントのロールを取得します
        
        Args:
            agent_type: エージェントの種類（"librarian", "researcher"など）
            
        Returns:
            エージェントのロール
        """
        if agent_type not in self.prompts:
            raise ValueError(f"未知のエージェントタイプです: {agent_type}")
        
        return self.prompts[agent_type]["role"]
    
    def get_system_message(self, agent_type: str) -> str:
        """
        エージェントのシステムメッセージを取得します
        
        Args:
            agent_type: エージェントの種類（"librarian", "researcher"など）
            
        Returns:
            エージェントのシステムメッセージ
        """
        if agent_type not in self.prompts:
            raise ValueError(f"未知のエージェントタイプです: {agent_type}")
        
        return self.prompts[agent_type]["system_message"]
    
    def get_template(self, agent_type: str, template_name: str) -> str:
        """
        エージェントのテンプレートを取得します
        
        Args:
            agent_type: エージェントの種類（"librarian", "researcher"など）
            template_name: テンプレート名（"search_query", "answer_format"など）
            
        Returns:
            テンプレート文字列
        """
        if agent_type not in self.prompts:
            raise ValueError(f"未知のエージェントタイプです: {agent_type}")
        
        templates = self.prompts[agent_type].get("templates", {})
        if template_name not in templates:
            raise ValueError(f"未知のテンプレート名です: {template_name}")
        
        return templates[template_name]
    
    def format_template(self, agent_type: str, template_name: str, **kwargs) -> str:
        """
        テンプレートを指定された引数でフォーマットします
        
        Args:
            agent_type: エージェントの種類（"librarian", "researcher"など）
            template_name: テンプレート名（"search_query", "answer_format"など）
            **kwargs: テンプレートに埋め込む変数
            
        Returns:
            フォーマットされたテンプレート文字列
        """
        template = self.get_template(agent_type, template_name)
        return template.format(**kwargs)
    
    def add_agent_type(self, agent_type: str, role: str, system_message: str, templates: Dict[str, str]) -> None:
        """
        新しいエージェントタイプを追加します
        
        Args:
            agent_type: エージェントの種類
            role: エージェントのロール
            system_message: エージェントのシステムメッセージ
            templates: エージェントのテンプレート辞書
        """
        self.prompts[agent_type] = {
            "role": role,
            "system_message": system_message,
            "templates": templates
        }
        
        # プロンプトファイルに保存
        self.save_prompts()
    
    def update_agent_type(self, agent_type: str, role: Optional[str] = None, 
                          system_message: Optional[str] = None, 
                          templates: Optional[Dict[str, str]] = None) -> None:
        """
        既存のエージェントタイプを更新します
        
        Args:
            agent_type: エージェントの種類
            role: エージェントのロール（Noneの場合は更新しない）
            system_message: エージェントのシステムメッセージ（Noneの場合は更新しない）
            templates: エージェントのテンプレート辞書（Noneの場合は更新しない）
        """
        if agent_type not in self.prompts:
            raise ValueError(f"未知のエージェントタイプです: {agent_type}")
        
        if role is not None:
            self.prompts[agent_type]["role"] = role
        
        if system_message is not None:
            self.prompts[agent_type]["system_message"] = system_message
        
        if templates is not None:
            self.prompts[agent_type]["templates"] = templates
        
        # プロンプトファイルに保存
        self.save_prompts()
    
    def get_available_agent_types(self) -> List[str]:
        """
        利用可能なエージェントタイプの一覧を取得します
        
        Returns:
            エージェントタイプのリスト
        """
        return list(self.prompts.keys())


# シングルトンインスタンス
_prompt_manager = None

def get_prompt_manager(prompt_dir: Optional[str] = None) -> PromptManager:
    """
    プロンプトマネージャーのシングルトンインスタンスを取得します
    
    Args:
        prompt_dir: プロンプトファイルを格納するディレクトリ
                    （初回呼び出し時のみ有効）
    
    Returns:
        プロンプトマネージャーのインスタンス
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager(prompt_dir)
    return _prompt_manager


if __name__ == "__main__":
    # 使用例
    prompt_manager = get_prompt_manager("./prompts")
    
    # 利用可能なエージェントタイプの表示
    print("利用可能なエージェントタイプ:", prompt_manager.get_available_agent_types())
    
    # 司書AIのシステムメッセージを表示
    print("\n司書AIのシステムメッセージ:")
    print(prompt_manager.get_system_message("librarian"))
    
    # テンプレートの使用例
    user_query = "人工知能の歴史について教えてください"
    search_query = prompt_manager.format_template("librarian", "search_query", user_query=user_query)
    print("\n検索クエリテンプレート:")
    print(search_query)
