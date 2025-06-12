#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPIサーバーモジュール（司書LLMエージェント対応版）

FastAPIを使用してRESTful APIサーバーを提供します。
司書LLMエージェントを使用して、ユーザーの質問に対する回答を生成します。
"""

import os
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
# 現在のファイルのパスからルートディレクトリを取得
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, root_dir)

# FastAPIのインポート
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os.path
import tempfile
import shutil
from pathlib import Path

# 自作モジュールのインポート
from src.utils.resource_manager import get_resource_manager
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

# 環境変数の読み込み
load_dotenv()

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="Librarian RAG API",
    description="司書LLMエージェントを使用したRAG検索API",
    version="0.1.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンのみを許可するべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 司書LLMエージェントのインスタンス（遅延初期化用）
librarian = None

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

# リクエストモデルの定義
class QueryRequest(BaseModel):
    query: str
    
class SystemInfoResponse(BaseModel):
    os: str
    os_version: str
    python_version: str
    hostname: str
    cpu_count: int
    platform: str
    llm_model: str
    embedding_model: str
    temperature: str

@app.get("/")
async def root():
    """
    ルートエンドポイント
    """
    return {
        "message": "司書LLMエージェントAPI",
        "version": "0.1.0",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "このヘルプメッセージ"},
            {"path": "/query", "method": "POST", "description": "司書LLMエージェントに質問する"},
            {"path": "/system-info", "method": "GET", "description": "システム情報を取得する"},
            {"path": "/api/source", "method": "GET", "description": "ソースファイル（主にマークダウン）を取得する"},
        ]
    }

@app.post("/query")
async def query(request: QueryRequest):
    """
    司書LLMエージェントに質問するエンドポイント
    """
    logger.info(f"司書LLMエージェントに質問します: {request.query[:50]}...")
    
    try:
        # 司書LLMエージェントの取得
        agent = get_librarian()
        
        # クエリの処理
        response = agent.process_query(request.query)
        
        return {"response": response}
    except Exception as e:
        logger.error(f"質問処理中にエラーが発生しました: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"質問の処理中にエラーが発生しました: {str(e)}")

@app.get("/system-info")
async def system_info():
    """
    システム情報を取得するエンドポイント
    """
    import platform
    
    logger.info("システム情報を取得します")
    
    try:
        # システム情報の収集
        system_info = SystemInfoResponse(
            os=platform.system(),
            os_version=platform.version(),
            python_version=platform.python_version(),
            hostname=platform.node(),
            cpu_count=os.cpu_count() or 0,
            platform=platform.platform(),
            llm_model=os.getenv('OLLAMA_MODEL', 'gemma3:12b'),
            embedding_model=os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large'),
            temperature=os.getenv('LLM_TEMPERATURE', '0.1')
        )
        
        return system_info
    except Exception as e:
        logger.error(f"システム情報取得中にエラーが発生しました: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"システム情報取得中にエラーが発生しました: {str(e)}")

@app.get("/api/source")
async def get_source_file(path: str = Query(..., description="ソースファイルのパス")):
    """
    指定されたパスのソースファイル（主にマークダウン）を返すエンドポイント
    
    Args:
        path: ファイルパス（例: data/markdowns/rag_database.md）
    
    Returns:
        ファイルの内容
    """
    logger.info(f"ソースファイルへのアクセス要求: {path}")
    
    # RAGシステムからファイル情報を取得する関数
    def find_original_file(requested_path):
        # パスの正規化
        normalized_requested_path = os.path.normpath(requested_path)
        filename = os.path.basename(normalized_requested_path)
        
        try:
            # 司書エージェントからRAGシステムを取得
            agent = get_librarian()
            rag_system = agent.rag_system
            
            # ファイル名で検索する簡易クエリ
            search_results = rag_system.search(
                query=filename,
                limit=10,
                similarity_threshold=0.5  # 広めに検索
            )
            
            # 結果からファイル名が一致するものを探す
            for result in search_results:
                result_filename = result.get('filename', '')
                result_filepath = result.get('filepath', '')
                original_filepath = result.get('original_filepath', '')
                
                # ファイル名が一致する場合
                if result_filename == filename or result_filename in normalized_requested_path:
                    # original_filepathがあればそれを優先
                    if original_filepath:
                        # data/sourceディレクトリからの相対パスを取得
                        source_dir = os.path.join(root_dir, "data", "source")
                        
                        # original_filepathが絶対パスの場合は相対パスに変換
                        if os.path.isabs(original_filepath):
                            try:
                                # 絶対パスから相対パスへの変換を試みる
                                rel_path = os.path.relpath(original_filepath, source_dir)
                                # 相対パスがソースディレクトリ外を指していないか確認
                                if not rel_path.startswith('..'):
                                    # ソースディレクトリ内のファイルパス
                                    source_file_path = os.path.join(source_dir, rel_path)
                                    if os.path.exists(source_file_path):
                                        logger.info(f"元ファイルが見つかりました: {source_file_path}")
                                        return source_file_path
                            except ValueError:
                                # 相対パスへの変換に失敗した場合
                                pass
                        
                        # 直接パスを試す
                        direct_path = os.path.join(source_dir, original_filepath)
                        if os.path.exists(direct_path):
                            logger.info(f"元ファイルが直接パスで見つかりました: {direct_path}")
                            return direct_path
                        
                        # ファイル名のみで検索
                        filename_only = os.path.basename(original_filepath)
                        for root, _, files in os.walk(source_dir):
                            for file in files:
                                if file == filename_only:
                                    found_path = os.path.join(root, file)
                                    logger.info(f"元ファイルがファイル名で見つかりました: {found_path}")
                                    return found_path
                    
                    # filepathがあればそれを使用
                    if result_filepath and os.path.exists(result_filepath):
                        logger.info(f"filepathが見つかりました: {result_filepath}")
                        return result_filepath
            
            # 見つからなかった場合はリクエストされたパスをそのまま返す
            return None
        except Exception as e:
            logger.warning(f"RAGシステムからのファイル情報取得中にエラー: {e}")
            return None
    
    try:
        # パスの正規化と安全性チェック
        normalized_path = os.path.normpath(os.path.join(root_dir, path))
        if not normalized_path.startswith(root_dir):
            logger.warning(f"不正なパスへのアクセス試行: {path}")
            raise HTTPException(status_code=403, detail="不正なパスへのアクセスは許可されていません")
        
        # RAGシステムから元のファイル情報を取得
        original_file_path = find_original_file(path)
        
        # ファイルパスの決定
        file_path_to_use = original_file_path if original_file_path else normalized_path
        
        # ファイルの存在確認
        if not os.path.exists(file_path_to_use) or not os.path.isfile(file_path_to_use):
            logger.warning(f"ファイルが見つかりません: {file_path_to_use}")
            raise HTTPException(status_code=404, detail=f"ファイルが見つかりません: {path}")
        
        # ファイル拡張子の確認
        _, ext = os.path.splitext(file_path_to_use)
        
        # プロジェクトのtempディレクトリを使用
        temp_dir = os.path.join(root_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = os.path.basename(file_path_to_use)
        temp_file_path = os.path.join(temp_dir, filename)
        
        # ファイルをコピー
        shutil.copy2(file_path_to_use, temp_file_path)
        logger.info(f"ファイルを一時ディレクトリにコピーしました: {file_path_to_use} -> {temp_file_path}")
        
        # 一時ファイルの削除を保証するための関数
        @app.on_event("shutdown")
        async def cleanup_temp_files():
            try:
                # tempディレクトリ内のすべてのファイルを削除
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            logger.info(f"一時ファイルを削除しました: {file_path}")
            except Exception as e:
                logger.error(f"一時ファイルの削除中にエラーが発生しました: {e}")
        
        # マークダウンファイルの場合はテキストとして返す
        if ext.lower() in [".md", ".markdown"]:
            logger.info(f"マークダウンファイルを返します: {filename}")
            with open(temp_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return PlainTextResponse(content, media_type="text/markdown")
        
        # その他のファイルタイプはFileResponseで返す
        logger.info(f"ファイルを返します: {filename}")
        return FileResponse(temp_file_path)
    
    except HTTPException:
        # 既に適切なHTTPExceptionが発生している場合はそのまま再送
        raise
    except Exception as e:
        logger.error(f"ソースファイル取得中にエラーが発生しました: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ソースファイル取得中にエラーが発生しました: {str(e)}")

@app.post("/prompt")
async def handle_prompt(request: QueryRequest):
    """
    プロンプトを処理するエンドポイント（/queryのエイリアス）
    """
    logger.info(f"プロンプトを受信しました: {request.query[:50]}...")
    
    try:
        # 司書LLMエージェントの取得
        agent = get_librarian()
        
        # プロンプトの処理
        response = agent.process_query(request.query)
        
        return {"response": response}
    except Exception as e:
        logger.error(f"プロンプト処理中にエラーが発生しました: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"プロンプトの処理中にエラーが発生しました: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """
    アプリケーション起動時のイベントハンドラ
    """
    logger.info("司書LLMエージェントAPIサーバーを起動します")
    
    # 司書LLMエージェントの初期化（事前に初期化しておく）
    get_librarian()

@app.on_event("shutdown")
async def shutdown_event():
    """
    アプリケーション終了時のイベントハンドラ
    """
    logger.info("司書LLMエージェントAPIサーバーをシャットダウンします")
    
    # リソースのクリーンアップはアプリケーション終了時に行う
    # 共有リソースマネージャーはアプリケーション全体で管理されるため、
    # 個々のサーバーがクリーンアップを行う必要はない

def run_server():
    """
    FastAPIサーバーを起動します。
    """
    port = int(os.getenv('API_PORT', '8000'))
    host = os.getenv('API_HOST', '0.0.0.0')
    
    logger.info(f"司書LLMエージェントを使用したFastAPIサーバーを起動します - {host}:{port}")
    
    # UvicornでFastAPIアプリケーションを起動
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("キーボード割り込みを受信しました。サーバーをシャットダウンします。")
    except Exception as e:
        logger.error(f"FastAPIサーバーの起動中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # リソースのクリーンアップ
        if librarian is not None:
            logger.info("司書LLMエージェントのリソースをクリーンアップします")
            librarian.cleanup()
