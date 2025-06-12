#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastMCPサーバーモジュール（司書LLMエージェント対応版）

FastMCPを使用してModel Context Protocol (MCP)に準拠したサーバーを提供します。
司書LLMエージェントを使用して、ユーザーの質問に対する回答を生成します。
"""

import os
import sys
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
# 現在のファイルのパスからルートディレクトリを取得
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, root_dir)

# FastMCPのインポート
from fastmcp import FastMCP

# 自作モジュールのインポート
from src.utils.resource_manager import get_resource_manager
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

# 環境変数の読み込み
load_dotenv()

# FastMCPサーバーのインスタンスを作成
mcp = FastMCP(
    name="Librarian RAG Server",
    description="司書LLMエージェントを使用したRAG検索サーバー",
    version="0.1.0",
    port=int(os.getenv('MCP_PORT', '8765')),
    host=os.getenv('MCP_HOST', '0.0.0.0')
)

def get_librarian():
    """
    司書LLMエージェントのインスタンスを取得します。
    共有リソースマネージャーからインスタンスを取得します。
    
    Returns:
        LibrarianAgent: 司書LLMエージェントのインスタンス
    """
    # 共有リソースマネージャーから司書エージェントを取得
    resource_manager = get_resource_manager()
    return resource_manager.get_librarian()

@mcp.tool()
def ask_librarian(query: str) -> str:
    """
    司書LLMエージェントに質問します。
    
    Args:
        query: ユーザーからの質問
        
    Returns:
        司書LLMエージェントからの回答
    """
    logger.info(f"司書LLMエージェントに質問します: {query}")
    
    try:
        # 司書LLMエージェントの取得
        agent = get_librarian()
        
        # クエリの処理
        response = agent.process_query(query)
        
        return response
    except Exception as e:
        logger.error(f"質問処理中にエラーが発生しました: {e}", exc_info=True)
        return f"# エラー\n\n質問の処理中にエラーが発生しました: {str(e)}"

@mcp.tool()
def get_system_info() -> str:
    """
    システム情報を取得します。
    
    Returns:
        システム情報（Markdown形式）
    """
    import platform
    import json
    
    logger.info("システム情報を取得します")
    
    try:
        # システム情報の収集
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "cpu_count": os.cpu_count(),
            "platform": platform.platform(),
        }
        
        # 環境変数から設定情報を取得
        config_info = {
            "llm_model": os.getenv('OLLAMA_MODEL', 'gemma3:12b'),
            "embedding_model": os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large'),
            "temperature": os.getenv('LLM_TEMPERATURE', '0.1'),
        }
        
        # 結果のフォーマット
        info_text = "# システム情報\n\n"
        info_text += "## 基本情報\n\n"
        info_text += "```json\n"
        info_text += json.dumps(system_info, indent=2, ensure_ascii=False)
        info_text += "\n```\n\n"
        
        info_text += "## 設定情報\n\n"
        info_text += "```json\n"
        info_text += json.dumps(config_info, indent=2, ensure_ascii=False)
        info_text += "\n```\n"
        
        return info_text
    except Exception as e:
        logger.error(f"システム情報取得中にエラーが発生しました: {e}", exc_info=True)
        return f"# エラー\n\nシステム情報取得中にエラーが発生しました: {str(e)}"

@mcp.prompt()
def handle_prompt(prompt: str) -> str:
    """
    MCPのプロンプトを処理します。
    
    Args:
        prompt: ユーザーからのプロンプト
        
    Returns:
        司書LLMエージェントからの回答
    """
    logger.info(f"MCPプロンプトを受信しました: {prompt[:50]}...")
    
    try:
        # 司書LLMエージェントの取得
        agent = get_librarian()
        
        # プロンプトの処理
        response = agent.process_query(prompt)
        
        return response
    except Exception as e:
        logger.error(f"プロンプト処理中にエラーが発生しました: {e}", exc_info=True)
        return f"# エラー\n\nプロンプトの処理中にエラーが発生しました: {str(e)}"

def run_server():
    """
    FastMCPサーバーを起動します。
    """
    logger.info("司書LLMエージェントを使用したFastMCPサーバーを起動します")
    
    # 司書LLMエージェントの初期化（事前に初期化しておく）
    get_librarian()
    
    # サーバーの起動
    mcp.run()

def signal_handler(sig, frame):
    """
    シグナルハンドラー
    """
    logger.info(f"シグナル {sig} を受信しました。サーバーをシャットダウンします。")
    # リソースのクリーンアップはアプリケーション終了時に行う
    # 共有リソースマネージャーはアプリケーション全体で管理されるため、
    # 個々のサーバーがクリーンアップを行う必要はない
    sys.exit(0)

if __name__ == "__main__":
    import signal
    import sys
    
    # シグナルハンドラーの登録
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("FastMCPサーバーを起動します...")
        run_server()
    except Exception as e:
        logger.error(f"FastMCPサーバーの起動中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # リソースのクリーンアップはアプリケーション終了時に行う
        # 共有リソースマネージャーはアプリケーション全体で管理されるため、
        # 個々のサーバーがクリーンアップを行う必要はない
        pass