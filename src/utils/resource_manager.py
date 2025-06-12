#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
共有リソースマネージャー

複数のサーバー間で共有されるリソース（司書エージェントなど）を一元管理します。
シングルトンパターンを使用して、リソースの重複生成を防ぎます。
"""

import os
import threading
from typing import Optional, Dict, Any

# 自作モジュールのインポート
from src.agents.librarian_agent import LibrarianAgent
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class ResourceManager:
    """
    共有リソースマネージャークラス
    シングルトンパターンを使用して、リソースの重複生成を防ぎます。
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ResourceManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # リソースの初期化
        self._librarian: Optional[LibrarianAgent] = None
        self._librarian_lock = threading.Lock()
        
        self._initialized = True
        logger.info("共有リソースマネージャーを初期化しました")
    
    def get_librarian(self) -> LibrarianAgent:
        """
        司書エージェントのインスタンスを取得します。
        インスタンスが存在しない場合は新しく作成します。
        
        Returns:
            LibrarianAgent: 司書エージェントのインスタンス
        """
        with self._librarian_lock:
            if self._librarian is None:
                logger.info("司書LLMエージェントを初期化しています...")
                try:
                    self._librarian = LibrarianAgent()
                    logger.info("司書LLMエージェントの初期化が完了しました")
                except Exception as e:
                    logger.error(f"司書LLMエージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
                    raise
            
            return self._librarian
    
    def cleanup(self):
        """
        すべてのリソースをクリーンアップします。
        アプリケーション終了時に呼び出されます。
        """
        logger.info("共有リソースのクリーンアップを開始します...")
        
        with self._librarian_lock:
            if self._librarian is not None:
                logger.info("司書LLMエージェントのリソースをクリーンアップします")
                try:
                    self._librarian.cleanup()
                except Exception as e:
                    logger.error(f"司書LLMエージェントのクリーンアップ中にエラーが発生しました: {e}", exc_info=True)
                finally:
                    self._librarian = None
        
        logger.info("共有リソースのクリーンアップが完了しました")

# グローバルなリソースマネージャーのインスタンス
_resource_manager = None
_resource_manager_lock = threading.Lock()

def get_resource_manager() -> ResourceManager:
    """
    共有リソースマネージャーのインスタンスを取得します。
    
    Returns:
        ResourceManager: 共有リソースマネージャーのインスタンス
    """
    global _resource_manager
    
    with _resource_manager_lock:
        if _resource_manager is None:
            _resource_manager = ResourceManager()
        
        return _resource_manager
