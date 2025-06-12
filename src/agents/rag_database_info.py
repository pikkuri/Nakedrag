#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGデータベース情報モジュール

RAGデータベースの概要情報や自己紹介テンプレートを管理します。
このモジュールは、司書AIが使用する知識ベースの概要を提供します。
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from src.rag.rag_class import RAGSystem
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)


class RAGDatabaseInfo:
    """
    RAGデータベース情報クラス
    
    RAGデータベースの概要情報や自己紹介テンプレートを管理するクラスです。
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        RAGデータベース情報の初期化
        
        Args:
            config_file: 設定ファイルのパス（オプション）
        """
        self.config_file = config_file
        self.config = self._load_config()
        
        # RAGシステムのインスタンス
        self.rag_system = None
    
    def _load_config(self) -> Dict[str, Any]:
        """
        設定ファイルから設定を読み込みます
        
        Returns:
            設定情報の辞書
        """
        default_config = {
            "database_name": "NakedRAG知識ベース",
            "description": "このRAGシステムには、特定のプロジェクトやドメインに関する文書が格納されています。",
            "scope_description": "プロジェクトのドキュメント、コードの説明、技術仕様、その他関連資料",
            "introduction_template": """このRAGシステムには、特定のプロジェクトやドメインに関する文書が格納されています。

現在の知識ベースには、以下のような情報が含まれています：
- プロジェクトのドキュメント
- コードの説明
- 技術仕様
- その他関連資料

この自己紹介テキストは、RAGシステムを構築した人によって更新されるべきものです。"""
        }
        
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return {**default_config, **config}
            except Exception as e:
                logger.error(f"設定ファイルの読み込みに失敗しました: {e}", exc_info=True)
        
        return default_config
    
    def save_config(self, config_file: Optional[str] = None) -> bool:
        """
        設定を保存します
        
        Args:
            config_file: 保存先の設定ファイルパス（指定しない場合は初期化時のパスを使用）
            
        Returns:
            保存成功ならTrue、失敗ならFalse
        """
        save_path = config_file or self.config_file
        if not save_path:
            logger.error("設定ファイルのパスが指定されていません")
            return False
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"設定ファイルの保存に失敗しました: {e}", exc_info=True)
            return False
    
    def get_database_introduction(self) -> str:
        """
        RAGデータベースの自己紹介テンプレートを取得します
        
        Returns:
            自己紹介テンプレート
        """
        # RAGシステムから情報を取得して動的に生成
        try:
            if self.rag_system is None:
                self.rag_system = RAGSystem()
            
            # ドキュメント数の取得
            doc_count = self.rag_system.get_document_count()
            
            # ユニークなソースの取得
            sources = self.rag_system.get_unique_sources()
            source_count = len(sources)
            
            # 代表的なソースファイル名（最大5つ）
            sample_sources = [filename for filename, _ in sources[:5]]
            
            # 自己紹介テンプレートの生成
            introduction = f"""# {self.config['database_name']}

{self.config['description']}

## 知識ベースの概要
- 総ドキュメント数: {doc_count}
- ソースファイル数: {source_count}

## 含まれる情報の種類
{self.config['scope_description']}

## 代表的なソースファイル
{', '.join(sample_sources) if sample_sources else '（情報がありません）'}

この知識ベースに関する質問にお答えします。"""
            
            return introduction
            
        except Exception as e:
            logger.error(f"データベース情報の取得に失敗しました: {e}", exc_info=True)
            return self.config["introduction_template"]
        finally:
            # リソースのクリーンアップ
            if self.rag_system is not None:
                self.rag_system.cleanup()
                self.rag_system = None
    
    def update_database_info(self, name: Optional[str] = None, 
                            description: Optional[str] = None,
                            scope_description: Optional[str] = None) -> None:
        """
        データベース情報を更新します
        
        Args:
            name: データベース名（Noneの場合は更新しない）
            description: 説明（Noneの場合は更新しない）
            scope_description: 範囲の説明（Noneの場合は更新しない）
        """
        if name is not None:
            self.config["database_name"] = name
        
        if description is not None:
            self.config["description"] = description
        
        if scope_description is not None:
            self.config["scope_description"] = scope_description


# シングルトンインスタンス
_database_info = None

def get_database_info(config_file: Optional[str] = None) -> RAGDatabaseInfo:
    """
    RAGデータベース情報のシングルトンインスタンスを取得します
    
    Args:
        config_file: 設定ファイルのパス（初回呼び出し時のみ有効）
    
    Returns:
        RAGデータベース情報のインスタンス
    """
    global _database_info
    if _database_info is None:
        _database_info = RAGDatabaseInfo(config_file)
    return _database_info


if __name__ == "__main__":
    # 使用例
    database_info = get_database_info()
    
    # データベースの自己紹介を取得
    introduction = database_info.get_database_introduction()
    print(introduction)
