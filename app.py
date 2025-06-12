#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NakedRAGアプリケーションメインモジュール

環境変数に基づいて必要なサーバーを起動します。
初期化処理のオプションも提供します。
"""

import os
import sys
import argparse
import threading
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root_dir)

# 自作モジュールのインポート
from src.utils.logger_util import setup_logger
from src.utils.resource_manager import get_resource_manager

# ロガーの設定
logger = setup_logger(__name__)

def parse_arguments():
    """
    コマンドライン引数をパースします
    """
    parser = argparse.ArgumentParser(description='NakedRAGアプリケーションを起動します')
    parser.add_argument('--init', action='store_true', help='起動前にRAGシステムを初期化します')
    parser.add_argument('--mcp', action='store_true', help='MCPサーバーを有効にします（環境変数の設定より優先）')
    parser.add_argument('--api', action='store_true', help='APIサーバーを有効にします（環境変数の設定より優先）')
    parser.add_argument('--line', action='store_true', help='LINE Botサーバーを有効にします（環境変数の設定より優先）')
    parser.add_argument('--web', action='store_true', help='Webサーバーを有効にします（環境変数の設定より優先）')
    parser.add_argument('--all', action='store_true', help='全てのサーバーを有効にします（環境変数の設定より優先）')
    
    return parser.parse_args()

def initialize_rag_system():
    """
    RAGシステムを初期化します
    """
    logger.info("RAGシステムの初期化を開始します...")
    
    try:
        # RAG初期化モジュールをインポート
        from src.rag.rag_initializer import initialize_rag_system as rag_init
        
        # 初期化処理を実行
        rag_init()
        
        logger.info("RAGシステムの初期化が完了しました")
    except Exception as e:
        logger.error(f"RAGシステムの初期化中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

def start_mcp_server():
    """
    MCPサーバーを起動します
    """
    try:
        from src.server.fastmcp_server import run_server as run_mcp_server
        logger.info("MCPサーバーを起動します...")
        run_mcp_server()
    except Exception as e:
        logger.error(f"MCPサーバーの起動中にエラーが発生しました: {e}", exc_info=True)

def start_api_server():
    """
    APIサーバーを起動します
    """
    try:
        from src.server.fastapi_server import run_server as run_api_server
        logger.info("APIサーバーを起動します...")
        run_api_server()
    except Exception as e:
        logger.error(f"APIサーバーの起動中にエラーが発生しました: {e}", exc_info=True)

def start_line_bot_server():
    """
    LINE Botサーバーを起動します
    """
    try:
        from src.server.line_bot_server import run_server as run_line_bot_server
        logger.info("LINE Botサーバーを起動します...")
        run_line_bot_server()
    except Exception as e:
        logger.error(f"LINE Botサーバーの起動中にエラーが発生しました: {e}", exc_info=True)

def start_web_server():
    """
    Webサーバーを起動します
    """
    try:
        # Webサーバーモジュールが実装されたら、ここでインポートして起動
        logger.info("Webサーバーを起動します...")
        # from src.server.web_server import run_server as run_web_server
        # run_web_server()
        logger.warning("Webサーバーモジュールが実装されていないため、起動をスキップします")
    except Exception as e:
        logger.error(f"Webサーバーの起動中にエラーが発生しました: {e}", exc_info=True)

def main():
    """
    メイン関数
    """
    # .envファイルを読み込む
    load_dotenv(override=True)
    
    # コマンドライン引数をパース
    args = parse_arguments()
    
    # 初期化オプションが指定されている場合は初期化を実行
    if args.init:
        initialize_rag_system()
    
    # 起動するサーバーを決定
    # コマンドライン引数が優先、なければ環境変数を使用
    run_mcp = args.mcp or args.all or os.getenv('MCP_SERVER_ENABLED', 'false').lower() == 'true'
    run_api = args.api or args.all or os.getenv('API_SERVER_ENABLED', 'false').lower() == 'true'
    run_line = args.line or args.all or os.getenv('LINE_BOT_ENABLED', 'false').lower() == 'true'
    run_web = args.web or args.all or os.getenv('WEB_SERVER_ENABLED', 'false').lower() == 'true'
    
    # 各サーバーを別スレッドで起動
    threads = []
    
    if run_mcp:
        mcp_thread = threading.Thread(target=start_mcp_server, name="MCPServerThread")
        threads.append(mcp_thread)
    
    if run_api:
        api_thread = threading.Thread(target=start_api_server, name="APIServerThread")
        threads.append(api_thread)
    
    if run_line:
        line_thread = threading.Thread(target=start_line_bot_server, name="LineBotServerThread")
        threads.append(line_thread)
    
    if run_web:
        web_thread = threading.Thread(target=start_web_server, name="WebServerThread")
        threads.append(web_thread)
    
    # スレッドを開始
    for thread in threads:
        thread.daemon = True  # メインスレッドが終了したら一緒に終了するように設定
        thread.start()
        logger.info(f"{thread.name}を開始しました")
    
    # 起動するサーバーがない場合
    if not threads:
        logger.warning("起動するサーバーが指定されていません。--help オプションでヘルプを表示します。")
        return
    
    # メインスレッドが終了しないようにする
    try:
        while True:
            time.sleep(1)  # CPUの使用率を下げるために少し待機
    except KeyboardInterrupt:
        logger.info("キーボード割り込みを受信しました。アプリケーションを終了します。")
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
    finally:
        logger.info("アプリケーションを終了します...")
        
        # 共有リソースのクリーンアップ
        try:
            resource_manager = get_resource_manager()
            resource_manager.cleanup()
            logger.info("共有リソースのクリーンアップが完了しました")
        except Exception as e:
            logger.error(f"共有リソースのクリーンアップ中にエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    main()
