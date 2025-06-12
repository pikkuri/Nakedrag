#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LINE Bot用のAPIサーバープログラム
司書LLMエージェントを使用して、LINEからの質問に対する回答を生成します。
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
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# LINE Bot SDKのインポート
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom
)

# 自作モジュールのインポート
from src.utils.resource_manager import get_resource_manager
from src.utils.logger_util import setup_logger
from src.agents.librarian_agent import LibrarianAgent

# ロガーの設定
logger = setup_logger(__name__)

# 環境変数の読み込み
load_dotenv()

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="司書LLMエージェント LINE Bot API",
    description="LINE Botを通じて司書LLMエージェントに質問できるAPIサーバー",
    version="1.0.0"
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE Bot APIの設定
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
WEBHOOK_BASE_URL = os.environ.get('LINE_WEBHOOK_BASE_URL', 'https://example.com')
WEBHOOK_URL = os.environ.get('LINE_WEBHOOK_URL', f"{WEBHOOK_BASE_URL}/callback")

# LINE Bot APIとWebhookHandlerのインスタンスを作成
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 司書LLMエージェントのインスタンス（シングルトン）
librarian = None

def get_librarian() -> LibrarianAgent:
    """
    司書LLMエージェントのインスタンスを取得します。
    共有リソースマネージャーからインスタンスを取得します。
    
    Returns:
        LibrarianAgent: 司書LLMエージェントのインスタンス
    """
    # 共有リソースマネージャーから司書エージェントを取得
    resource_manager = get_resource_manager()
    return resource_manager.get_librarian()

class SystemInfo(BaseModel):
    """システム情報のモデル"""
    version: str
    llm_model: str
    temperature: float
    web_server_url: str

@app.get("/")
async def root():
    """
    ルートエンドポイント
    
    Returns:
        JSONResponse: サーバーの状態情報
    """
    return {"status": "running", "message": "司書LLMエージェント LINE Bot APIサーバー"}

@app.get("/system_info")
async def system_info():
    """
    システム情報を返すエンドポイント
    
    Returns:
        SystemInfo: システム情報
    """
    try:
        agent = get_librarian()
        return SystemInfo(
            version="1.0.0",
            llm_model=os.getenv('OLLAMA_MODEL', 'gemma3:12b'),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.1')),
            web_server_url=os.getenv('WEB_SERVER_URL', 'http://localhost:8000')
        )
    except Exception as e:
        logger.error(f"システム情報の取得中にエラーが発生しました: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"システム情報の取得中にエラーが発生しました: {str(e)}")

@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None), background_tasks: BackgroundTasks = None):
    """
    LINE Webhookコールバックエンドポイント
    
    Args:
        request: HTTPリクエスト
        x_line_signature: LINEからのリクエストの署名
        background_tasks: バックグラウンドタスク
        
    Returns:
        PlainTextResponse: 処理結果
    """
    logger.info("LINE Webhookコールバックエンドポイントが呼び出されました")
    
    # リクエストヘッダーのログ出力
    headers = dict(request.headers)
    logger.info(f"Webhookリクエストヘッダー: {headers}")
    logger.info(f"X-Line-Signature: {x_line_signature}")
    
    # リクエストボディを取得
    body = await request.body()
    body_str = body.decode('utf-8')
    logger.info(f"Webhookリクエストボディ: {body_str[:200]}..." if len(body_str) > 200 else f"Webhookリクエストボディ: {body_str}")
    
    # 署名を検証
    try:
        logger.info("署名の検証を行います")
        handler.handle(body_str, x_line_signature)
        logger.info("署名の検証に成功しました")
    except InvalidSignatureError:
        logger.error("署名の検証に失敗しました")
        raise HTTPException(status_code=400, detail="署名の検証に失敗しました")
    except Exception as e:
        logger.error(f"Webhook処理中にエラーが発生しました: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Webhook処理中にエラーが発生しました: {str(e)}")
    
    logger.info("Webhook処理が正常に完了しました")
    return PlainTextResponse("OK")

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """
    テキストメッセージを処理します
    
    Args:
        event: LINEのメッセージイベント
    """
    logger.info(f"handle_text_messageが呼び出されました - イベントタイプ: {type(event)}")
    logger.info(f"イベント詳細: {event}")
    
    # ユーザーからのメッセージを取得
    user_message = event.message.text
    logger.info(f"受信メッセージ: '{user_message}'")
    
    try:
        # 終了コマンドの場合は無視
        if user_message.lower() in ["exit", "quit"]:
            logger.info("終了コマンドを受信しましたが無視します")
            return
        
        logger.info(f"LINEからのメッセージを処理します: '{user_message}'")
        
        # 司書LLMエージェントを使用して回答を生成
        logger.info("司書LLMエージェントを取得します")
        agent = get_librarian()
        logger.info("クエリを処理します")
        response = agent.process_query(user_message)
        logger.info(f"生成された回答: '{response[:100]}...'" if len(response) > 100 else f"生成された回答: '{response}'")
        
        # 回答をLINEに送信
        logger.info(f"LINEに回答を送信します - reply_token: {event.reply_token}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
        
        logger.info("回答の送信が完了しました")
        
    except LineBotApiError as e:
        logger.error(f"LINE Bot APIエラー: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"メッセージ処理中にエラーが発生しました: {e}", exc_info=True)
        # エラーメッセージを送信
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"エラーが発生しました: {str(e)}")
            )
        except Exception:
            pass

@app.on_event("startup")
async def startup_event():
    """
    アプリケーション起動時のイベントハンドラ
    """
    logger.info("司書LLMエージェント LINE Bot APIサーバーを起動します")
    
    # LINE Bot APIの設定を確認
    if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
        logger.warning("LINE_CHANNEL_ACCESS_TOKEN または LINE_CHANNEL_SECRET が設定されていません")
        logger.warning(f"CHANNEL_ACCESS_TOKEN: {'設定あり' if CHANNEL_ACCESS_TOKEN else '未設定'}")
        logger.warning(f"CHANNEL_SECRET: {'設定あり' if CHANNEL_SECRET else '未設定'}")
    else:
        logger.info("LINE Bot API設定が正しく読み込まれました")
        logger.info(f"CHANNEL_ACCESS_TOKEN: {'設定あり' if CHANNEL_ACCESS_TOKEN else '未設定'}")
        logger.info(f"CHANNEL_SECRET: {'設定あり' if CHANNEL_SECRET else '未設定'}")
    
    # Webhook URLの表示
    webhook_base_url = os.environ.get('LINE_WEBHOOK_BASE_URL', 'https://example.com')
    webhook_url = os.environ.get('LINE_WEBHOOK_URL', f"{webhook_base_url}/callback")
    logger.info(f"LINE Webhook Base URL: {webhook_base_url}")
    logger.info(f"LINE Webhook URL: {webhook_url}")
    logger.info(f"LINE Webhookを設定する際は、LINE Developersコンソールで上記URLを設定してください")
    
    # サーバーの設定を表示
    host = os.getenv("LINE_BOT_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("LINE_BOT_SERVER_PORT", "8001"))
    logger.info(f"サーバーは {host}:{port} でリッスンしています")
    
    # 司書LLMエージェントの初期化（事前に初期化しておく）
    get_librarian()

@app.on_event("shutdown")
async def shutdown_event():
    """
    アプリケーション終了時のイベントハンドラ
    """
    logger.info("司書LLMエージェント LINE Bot APIサーバーをシャットダウンします")
    
    # リソースのクリーンアップはアプリケーション終了時に行う
    # 共有リソースマネージャーはアプリケーション全体で管理されるため、
    # 個々のサーバーがクリーンアップを行う必要はない

def run_server():
    """
    FastAPIサーバーを起動します。
    """
    # サーバー設定
    host = os.getenv("LINE_BOT_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("LINE_BOT_SERVER_PORT", "8001"))
    
    # サーバー起動
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
