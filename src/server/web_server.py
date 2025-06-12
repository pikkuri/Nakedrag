#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGシステムの検索結果を表示するためのWebサーバーモジュール

このモジュールは、NakedRAGプロジェクトの検索結果と参照ソースを
Webインターフェースを通じて表示するためのサーバーを提供します。
MCPサーバーと連携して、検索結果を外部から参照可能にします。
"""

import os
import sys
import json
import uuid
import argparse
import threading
import time
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# dotenvをインポート
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# ファイアウォール管理は独立したモジュールとして実行するため、ここでは不要

# Flaskをインポート
from flask import Flask, render_template_string, request, jsonify, send_from_directory, abort
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class RAGWebServer:
    """
    RAGシステムの検索結果を表示するためのWebサーバークラス
    
    このクラスは以下の機能を提供します：
    1. 検索結果と参照ソースの保存
    2. Webインターフェースを通じた検索結果の表示
    3. 参照ソースの表示
    4. 古いデータの自動クリーンアップ
    """
    
    def __init__(self, 
                 data_dir: str = "./web_data",
                 host: str = "0.0.0.0",
                 port: int = 5000,
                 cleanup_days: int = 7):
        """
        RAGWebServerの初期化
        
        Args:
            data_dir (str): データを保存するディレクトリ
            host (str): サーバーのホスト
            port (int): サーバーのポート番号
            cleanup_days (int): 古いデータを削除する日数
        """
        self.data_dir = Path(data_dir)
        self.host = host
        self.port = port
        self.cleanup_days = cleanup_days
        
        # データディレクトリの作成
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Flaskアプリケーションの作成
        self.app = Flask(__name__)
        
        # ルートの設定
        self.setup_routes()
        
        logger.info(f"RAGWebServerを初期化しました。データディレクトリ: {self.data_dir}, ポート: {self.port}")
    
    def setup_routes(self):
        """
        Flaskアプリケーションのルートを設定
        """
        # メインページ
        @self.app.route('/')
        def index():
            return self.render_index()
        
        # 検索結果ページ
        @self.app.route('/result/<result_id>')
        def result(result_id):
            return self.render_result(result_id)
        
        # ソースファイルの取得
        @self.app.route('/source/<result_id>/<source_id>')
        def source(result_id, source_id):
            return self.get_source(result_id, source_id)
        
        # 最新の検索結果一覧
        @self.app.route('/recent')
        def recent():
            return self.render_recent()
            
        # 元ソースファイルの取得（司書エージェント用）
        @self.app.route('/sources/<path:file_path>')
        def original_source(file_path):
            return self.get_original_source(file_path)
    
    def render_index(self):
        """
        インデックスページを表示
        """
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>NakedRAG 検索システム</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                a.button {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 20px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                a.button:hover {
                    background-color: #2980b9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>NakedRAG 検索システム</h1>
                <p>NakedRAGシステムの検索結果を表示するためのWebサーバーです。</p>
                <p>検索結果を表示するには、検索結果IDを含むURLにアクセスしてください。</p>
                <a href="/recent" class="button">最近の検索結果を表示</a>
            </div>
        </body>
        </html>
        '''
        return render_template_string(html)
    
    def render_result(self, result_id: str):
        """
        検索結果ページを表示
        
        Args:
            result_id (str): 検索結果ID
        """
        # 検索結果データの読み込み
        data_file = self.data_dir / f"{result_id}.json"
        if not data_file.exists():
            return abort(404, description="検索結果が見つかりません")
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            query = data.get('query', '不明なクエリ')
            answer = data.get('answer', '回答がありません')
            sources = data.get('sources', [])
            timestamp = data.get('timestamp', '不明な時間')
            
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>NakedRAG 検索結果</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .container {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 20px;
                    }
                    .main-content {
                        flex: 2;
                        min-width: 500px;
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .sidebar {
                        flex: 1;
                        min-width: 300px;
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    h1 {
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                    }
                    h2 {
                        color: #2c3e50;
                        margin-top: 20px;
                    }
                    .source-item {
                        margin-bottom: 10px;
                        padding: 10px;
                        background-color: #f9f9f9;
                        border-left: 4px solid #3498db;
                        cursor: pointer;
                        transition: background-color 0.2s;
                    }
                    .source-item:hover {
                        background-color: #e9e9e9;
                    }
                    pre {
                        background-color: #f8f8f8;
                        padding: 15px;
                        border-radius: 5px;
                        overflow-x: auto;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                    .query {
                        font-style: italic;
                        color: #7f8c8d;
                        margin-bottom: 20px;
                    }
                    .timestamp {
                        font-size: 0.8em;
                        color: #7f8c8d;
                        margin-top: 20px;
                    }
                    .highlight {
                        background-color: #ffffcc;
                        padding: 2px;
                    }
                    .back-button {
                        margin-top: 20px;
                        padding: 8px 15px;
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        text-decoration: none;
                        display: inline-block;
                    }
                    .back-button:hover {
                        background-color: #2980b9;
                    }
                    #source-content {
                        display: none;
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        margin-top: 20px;
                    }
                </style>
            </head>
            <body>
                <h1>NakedRAG 検索結果</h1>
                <div class="query">検索クエリ: {{ query }}</div>
                
                <div class="container">
                    <div class="main-content">
                        <h2>回答</h2>
                        <div id="answer">{{ answer }}</div>
                        <div class="timestamp">検索時間: {{ timestamp }}</div>
                    </div>
                    
                    <div class="sidebar">
                        <h2>参照ソース</h2>
                        <div id="sources">
                            {% for i, (filename, filepath) in enumerate(sources) %}
                            <div class="source-item" onclick="viewSource('{{ result_id }}', '{{ i }}')">
                                {{ filename }}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                
                <div id="source-content">
                    <h2 id="source-title"></h2>
                    <pre id="source-text"></pre>
                    <button class="back-button" onclick="hideSource()">戻る</button>
                </div>
                
                <a href="/" class="back-button" style="margin-top: 20px;">トップページに戻る</a>
                
                <script>
                    function viewSource(resultId, sourceId) {
                        fetch(`/source/${resultId}/${sourceId}`)
                            .then(response => response.json())
                            .then(data => {
                                document.querySelector('.container').style.display = 'none';
                                document.getElementById('source-content').style.display = 'block';
                                document.getElementById('source-title').textContent = data.filename;
                                document.getElementById('source-text').textContent = data.content;
                            });
                    }
                    
                    function hideSource() {
                        document.querySelector('.container').style.display = 'flex';
                        document.getElementById('source-content').style.display = 'none';
                    }
                </script>
            </body>
            </html>
            '''
            return render_template_string(html, query=query, answer=answer, sources=enumerate(sources), result_id=result_id, timestamp=timestamp)
        
        except Exception as e:
            logger.error(f"検索結果の表示中にエラーが発生しました: {e}")
            return abort(500, description=f"エラーが発生しました: {str(e)}")
    
    def get_source(self, result_id: str, source_id: str):
        """
        ソースファイルの内容を取得
        
        Args:
            result_id (str): 検索結果ID
            source_id (str): ソースID
        """
        # 検索結果データの読み込み
        data_file = self.data_dir / f"{result_id}.json"
        if not data_file.exists():
            return jsonify({'error': '検索結果が見つかりません'})
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            sources = data.get('sources', [])
            source_id = int(source_id)
            
            if source_id < 0 or source_id >= len(sources):
                return jsonify({'error': 'ソースが見つかりません'})
            
            filename, filepath = sources[source_id]
            
            # ソースファイルの内容を読み込み
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify({'filename': filename, 'content': content})
            except Exception as e:
                logger.error(f"ソースファイルの読み込み中にエラーが発生しました: {e}")
                return jsonify({'error': f'ソースファイルの読み込みに失敗しました: {str(e)}'})
        
        except Exception as e:
            logger.error(f"ソースの取得中にエラーが発生しました: {e}")
            return jsonify({'error': f'エラーが発生しました: {str(e)}'})
    
    def render_recent(self):
        """
        最近の検索結果一覧を表示
        """
        # 検索結果ファイルの一覧を取得
        result_files = list(self.data_dir.glob("*.json"))
        result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        recent_results = []
        for file in result_files[:20]:  # 最新20件を表示
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                result_id = file.stem
                query = data.get('query', '不明なクエリ')
                timestamp = data.get('timestamp', '不明な時間')
                
                recent_results.append({
                    'id': result_id,
                    'query': query,
                    'timestamp': timestamp
                })
            except Exception as e:
                logger.error(f"検索結果ファイルの読み込み中にエラーが発生しました: {e}")
        
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>NakedRAG 最近の検索結果</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                .result-item {
                    margin-bottom: 10px;
                    padding: 10px;
                    background-color: #f9f9f9;
                    border-left: 4px solid #3498db;
                    transition: background-color 0.2s;
                }
                .result-item:hover {
                    background-color: #e9e9e9;
                }
                .result-link {
                    text-decoration: none;
                    color: #333;
                    display: block;
                }
                .timestamp {
                    font-size: 0.8em;
                    color: #7f8c8d;
                }
                .back-button {
                    margin-top: 20px;
                    padding: 8px 15px;
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                }
                .back-button:hover {
                    background-color: #2980b9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>最近の検索結果</h1>
                
                {% if recent_results %}
                    {% for result in recent_results %}
                    <a href="/result/{{ result.id }}" class="result-link">
                        <div class="result-item">
                            <div>{{ result.query }}</div>
                            <div class="timestamp">{{ result.timestamp }}</div>
                        </div>
                    </a>
                    {% endfor %}
                {% else %}
                    <p>最近の検索結果はありません。</p>
                {% endif %}
                
                <a href="/" class="back-button">トップページに戻る</a>
            </div>
        </body>
        </html>
        '''
        return render_template_string(html, recent_results=recent_results)
    
    def save_search_result(self, query: str, answer: str, sources: List[Tuple[str, str]]) -> str:
        """
        検索結果を保存し、結果IDを返す
        
        Args:
            query (str): 検索クエリ
            answer (str): 検索結果の回答
            sources (List[Tuple[str, str]]): 参照ソースのリスト (ファイル名, ファイルパス)
        
        Returns:
            str: 結果ID
        """
        # 一意のIDを生成
        result_id = str(uuid.uuid4())
        
        # タイムスタンプを生成
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # データを作成
        data = {
            'query': query,
            'answer': answer,
            'sources': sources,
            'timestamp': timestamp
        }
        
        # データを保存
        data_file = self.data_dir / f"{result_id}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"検索結果を保存しました。ID: {result_id}, クエリ: {query}")
        
        # 古いデータのクリーンアップ
        self.cleanup_old_data()
        
        return result_id
    
    def get_original_source(self, file_path: str):
        """
        元のソースファイルを提供する
        
        Args:
            file_path (str): ファイルパス
            
        Returns:
            ファイルの内容またはエラーレスポンス
        """
        try:
            # ソースファイルのルートディレクトリ
            source_root = Path(os.getenv('SOURCE_ROOT', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sources')))
            
            # パスの正規化と検証
            safe_path = os.path.normpath(file_path)
            
            # パストラバーサル攻撃対策
            if safe_path.startswith('..') or safe_path.startswith('/'):
                logger.warning(f"不正なファイルパスへのアクセス試行: {file_path}")
                return abort(403)  # Forbidden
            
            # ファイルの完全パスを構築
            full_path = os.path.join(source_root, safe_path)
            
            # ファイルの存在確認
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                logger.warning(f"存在しないファイルへのアクセス: {full_path}")
                return abort(404)  # Not Found
            
            # ファイルを送信
            logger.info(f"元ソースファイルを提供: {full_path}")
            return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))
            
        except Exception as e:
            logger.error(f"元ソースファイル提供中にエラーが発生: {str(e)}")
            return abort(500)  # Internal Server Error
    
    def cleanup_old_data(self):
        """
        古いデータを削除
        """
        # クリーンアップする日付を計算
        cleanup_date = datetime.now() - timedelta(days=self.cleanup_days)
        
        # 古いファイルを削除
        for file in self.data_dir.glob("*.json"):
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            if file_time < cleanup_date:
                try:
                    file.unlink()
                    logger.info(f"古いデータを削除しました: {file}")
                except Exception as e:
                    logger.error(f"古いデータの削除中にエラーが発生しました: {e}")
    
    def start(self, debug: bool = False):
        """
        Webサーバーを起動
        
        Args:
            debug (bool): デバッグモードで起動するかどうか
        """
        logger.info(f"Webサーバーを起動します。ホスト: {self.host}, ポート: {self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)
    
    def start_background(self):
        """
        バックグラウンドでWebサーバーを起動
        """
        thread = threading.Thread(target=self.start)
        thread.daemon = True
        thread.start()
        logger.info("バックグラウンドでWebサーバーを起動しました")
        return thread

def main():
    """
    メイン関数
    """
    # .envファイルからデフォルト値を読み込む
    default_web_data_dir = os.getenv('WEB_DATA_DIR', './web_data')
    default_web_server_host = os.getenv('WEB_SERVER_HOST', '127.0.0.1')
    default_web_server_port = int(os.getenv('WEB_SERVER_PORT', '5000'))
    default_mcp_server_port = int(os.getenv('MCP_SERVER_PORT', '8080'))
    default_cleanup_days = int(os.getenv('WEB_CLEANUP_DAYS', '7'))
    
    parser = argparse.ArgumentParser(description='RAG検索結果表示Webサーバー')
    parser.add_argument('--data-dir', type=str, default=default_web_data_dir,
                        help=f'データを保存するディレクトリ (デフォルト: {default_web_data_dir})')
    parser.add_argument('--host', type=str, default=default_web_server_host,
                        help=f'サーバーのホスト (デフォルト: {default_web_server_host})')
    parser.add_argument('--port', type=int, default=default_web_server_port,
                        help=f'サーバーのポート番号 (デフォルト: {default_web_server_port})')
    parser.add_argument('--cleanup-days', type=int, default=default_cleanup_days,
                        help=f'古いデータを削除する日数 (デフォルト: {default_cleanup_days})')
    parser.add_argument('--debug', action='store_true',
                        help='デバッグモードで起動する')
    
    args = parser.parse_args()
    
    # Webサーバーの作成と起動
    server = RAGWebServer(
        data_dir=args.data_dir,
        host=args.host,
        port=args.port,
        cleanup_days=args.cleanup_days
    )
    
    try:
        server.start(debug=args.debug)
    except KeyboardInterrupt:
        logger.info("Webサーバーを停止します")
        sys.exit(0)

if __name__ == "__main__":
    main()
