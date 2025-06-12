#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGツールモジュール

MCPサーバーに登録するRAG関連のツールを提供します。
"""

import os
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

# 自作モジュールのインポート
from src.rag.rag_searcher import RAGSearcher, search
from src.rag.rag_class import RAGSystem
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)


def register_rag_tools(server):
    """
    RAG関連ツールをMCPサーバーに登録します。

    Args:
        server: MCPサーバーのインスタンス
    """
    # RAG検索ツールの登録
    server.register_tool(
        name="rag_search",
        description="RAGシステムを使用して検索を実行します",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "検索クエリ",
                },
                "top_k": {
                    "type": "integer",
                    "description": "検索結果の上位件数（デフォルト: 20）",
                },
                "similarity_threshold": {
                    "type": "number",
                    "description": "検索の類似度閾値（デフォルト: 0.7）",
                },
            },
            "required": ["query"],
        },
        handler=rag_search_handler,
    )

    # ドキュメント数取得ツールの登録
    server.register_tool(
        name="get_document_count",
        description="RAGデータベース内のドキュメント数を取得します",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=get_document_count_handler,
    )

    # ソース一覧取得ツールの登録
    server.register_tool(
        name="get_unique_sources",
        description="RAGデータベース内のユニークなソースを取得します",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=get_unique_sources_handler,
    )

    logger.info("RAG関連ツールを登録しました")


def rag_search_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAG検索を実行するハンドラ関数

    Args:
        params: パラメータ
            - query: 検索クエリ
            - top_k: 検索結果の上位件数（オプション）
            - similarity_threshold: 検索の類似度閾値（オプション）

    Returns:
        検索結果
    """
    try:
        # パラメータの取得
        query = params.get("query")
        if not query:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "エラー: 検索クエリが指定されていません",
                    }
                ],
                "isError": True,
            }

        top_k = params.get("top_k", 20)
        similarity_threshold = params.get("similarity_threshold", 0.7)

        # 検索の実行
        result = search(query, top_k, similarity_threshold)

        return {
            "content": [
                {
                    "type": "text",
                    "text": result,
                }
            ]
        }
    except Exception as e:
        logger.error(f"RAG検索中にエラーが発生しました: {e}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"エラー: RAG検索中にエラーが発生しました: {str(e)}",
                }
            ],
            "isError": True,
        }


def get_document_count_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAGデータベース内のドキュメント数を取得するハンドラ関数

    Args:
        params: パラメータ（未使用）

    Returns:
        ドキュメント数
    """
    try:
        # RAGシステムの初期化
        rag_system = RAGSystem()

        # ドキュメント数の取得
        count = rag_system.get_document_count()

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"RAGデータベース内のドキュメント数: {count}",
                }
            ]
        }
    except Exception as e:
        logger.error(f"ドキュメント数取得中にエラーが発生しました: {e}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"エラー: ドキュメント数取得中にエラーが発生しました: {str(e)}",
                }
            ],
            "isError": True,
        }
    finally:
        if 'rag_system' in locals():
            rag_system.cleanup()


def get_unique_sources_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAGデータベース内のユニークなソースを取得するハンドラ関数

    Args:
        params: パラメータ（未使用）

    Returns:
        ユニークなソースのリスト
    """
    try:
        # RAGシステムの初期化
        rag_system = RAGSystem()

        # ユニークなソースの取得
        sources = rag_system.get_unique_sources()

        # 結果のフォーマット
        sources_text = "# RAGデータベース内のソース一覧\n\n"
        for i, (filename, filepath) in enumerate(sources, 1):
            sources_text += f"{i}. **{filename}** - `{filepath}`\n"

        return {
            "content": [
                {
                    "type": "text",
                    "text": sources_text,
                }
            ]
        }
    except Exception as e:
        logger.error(f"ソース一覧取得中にエラーが発生しました: {e}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"エラー: ソース一覧取得中にエラーが発生しました: {str(e)}",
                }
            ],
            "isError": True,
        }
    finally:
        if 'rag_system' in locals():
            rag_system.cleanup()


if __name__ == "__main__":
    print("このモジュールは直接実行せず、MCPサーバーからインポートして使用してください。")
