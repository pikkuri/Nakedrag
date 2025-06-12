#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPIクライアントモジュール

司書LLMエージェントAPIサーバーにクエリを送信するためのクライアントプログラム。
コマンドラインから質問を入力し、サーバーに送信して回答を表示します。
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
# 現在のファイルのパスからルートディレクトリを取得
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, root_dir)

# 自作モジュールのインポート
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

# 環境変数の読み込み
load_dotenv()

class LibrarianClient:
    """
    司書LLMエージェントAPIクライアントクラス
    """
    
    def __init__(self, host: str = None, port: int = None):
        """
        初期化
        
        Args:
            host: APIサーバーのホスト
            port: APIサーバーのポート
        """
        self.host = host or os.getenv('API_HOST', 'localhost')
        self.port = port or int(os.getenv('API_PORT', '8000'))
        self.base_url = f"http://{self.host}:{self.port}"
        logger.info(f"司書LLMエージェントAPIクライアントを初期化しました: {self.base_url}")
    
    def send_query(self, query: str) -> str:
        """
        クエリを送信して回答を取得
        
        Args:
            query: 質問内容
            
        Returns:
            サーバーからの回答
        """
        endpoint = f"{self.base_url}/query"
        payload = {"query": query}
        
        try:
            logger.info(f"クエリを送信します: {query[:50]}...")
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()  # エラーレスポンスの場合は例外を発生
            
            result = response.json()
            return result["response"]
        except requests.exceptions.RequestException as e:
            logger.error(f"APIリクエスト中にエラーが発生しました: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                    return f"エラー: {error_detail}"
                except:
                    return f"エラー: {str(e)}"
            return f"エラー: {str(e)}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        システム情報を取得
        
        Returns:
            システム情報の辞書
        """
        endpoint = f"{self.base_url}/system-info"
        
        try:
            logger.info("システム情報を取得します")
            response = requests.get(endpoint)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"システム情報取得中にエラーが発生しました: {e}")
            return {"error": str(e)}

def print_markdown(text: str):
    """
    マークダウンテキストを整形して表示
    
    Args:
        text: マークダウンテキスト
    """
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80 + "\n")

def interactive_mode(client: LibrarianClient):
    """
    対話モード
    
    Args:
        client: 司書LLMエージェントAPIクライアント
    """
    print("\n司書LLMエージェント対話モード")
    print("質問を入力してください。終了するには 'exit' または 'quit' と入力してください。\n")
    
    while True:
        try:
            query = input("\n質問> ")
            if query.lower() in ["exit", "quit", "終了"]:
                print("対話モードを終了します。")
                break
                
            if not query.strip():
                continue
                
            print("回答を取得中...")
            response = client.send_query(query)
            print_markdown(response)
            
        except KeyboardInterrupt:
            print("\n対話モードを終了します。")
            break
        except Exception as e:
            logger.error(f"対話中にエラーが発生しました: {e}", exc_info=True)
            print(f"エラーが発生しました: {e}")

def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description="司書LLMエージェントAPIクライアント")
    parser.add_argument("--host", help="APIサーバーのホスト", default=None)
    parser.add_argument("--port", type=int, help="APIサーバーのポート", default=None)
    parser.add_argument("--query", "-q", help="送信するクエリ（指定しない場合は対話モード）", default=None)
    parser.add_argument("--system-info", "-s", action="store_true", help="システム情報を取得")
    
    args = parser.parse_args()
    
    # クライアントの初期化
    client = LibrarianClient(host=args.host, port=args.port)
    
    if args.system_info:
        # システム情報の取得
        info = client.get_system_info()
        print_markdown(json.dumps(info, indent=2, ensure_ascii=False))
    elif args.query:
        # 単一クエリの送信
        response = client.send_query(args.query)
        print_markdown(response)
    else:
        # 対話モード
        interactive_mode(client)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nプログラムを終了します。")
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
        print(f"エラー: {e}")
        sys.exit(1)
