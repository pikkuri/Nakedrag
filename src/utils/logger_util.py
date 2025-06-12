#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ロギングユーティリティモジュール

このモジュールは、NakedRAGシステム全体で使用される共通のロギング機能を提供します。
.envファイルの設定に基づいてロガーを設定し、デバッグモードの切り替えを可能にします。
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# .envファイルの読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenvがインストールされていません。環境変数は直接OSから読み込まれます。")


def setup_logger(module_name: str) -> logging.Logger:
    """
    モジュール用のロガーを設定します。
    
    Args:
        module_name (str): ロガーを設定するモジュール名
        
    Returns:
        logging.Logger: 設定されたロガーオブジェクト
    """
    # 環境変数からログ設定を読み込み
    debug_enabled = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    log_level_str = os.getenv('LOG_LEVEL', 'INFO')
    debug_modules = os.getenv('DEBUG_MODULES', '').split(',')
    log_file = os.getenv('LOG_FILE', './logs/nakedrag.log')
    
    # モジュール名を短縮形に変換（パスを除去）
    short_module_name = module_name.split('.')[-1]
    
    # ロガーの取得
    logger = logging.getLogger(module_name)
    
    # すでに設定済みの場合は、そのまま返す
    if logger.handlers:
        return logger
    
    # ログレベルの設定
    if debug_enabled or short_module_name in debug_modules:
        logger_level = logging.DEBUG
    else:
        # 環境変数のLOG_LEVELを使用
        try:
            logger_level = getattr(logging, log_level_str.upper())
        except AttributeError:
            logger_level = logging.INFO
            print(f"警告: 無効なログレベル '{log_level_str}'。INFOを使用します。")
    
    logger.setLevel(logger_level)
    
    # フォーマッターの作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # コンソールハンドラーの追加
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラーの追加（ログディレクトリがない場合は作成）
    if log_file:
        log_path = Path(log_file)
        log_dir = log_path.parent
        
        try:
            # ログディレクトリが存在しない場合は作成
            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)
                
            # ファイルハンドラーの追加
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"警告: ログファイル '{log_file}' を設定できませんでした: {e}")
    
    return logger
