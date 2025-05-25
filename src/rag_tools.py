"""
RAGチE�Eルモジュール

MCPサーバ�Eに登録するRAG関連チE�Eルを提供します、E"""

import os
from typing import Dict, Any

from .document_processor import DocumentProcessor
from .embedding_generator import EmbeddingGenerator
from .vector_database import VectorDatabase
from .rag_service import RAGService


def register_rag_tools(server, rag_service: RAGService):
    """
    RAG関連チE�EルをMCPサーバ�Eに登録します、E
    Args:
        server: MCPサーバ�Eのインスタンス
        rag_service: RAGサービスのインスタンス
    """
    # 検索チE�Eルの登録
    server.register_tool(
        name="search",
        description="ベクトル検索を行いまぁE,
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "検索クエリ",
                },
                "limit": {
                    "type": "integer",
                    "description": "返す結果の数�E�デフォルチE 5�E�E,
                    "default": 5,
                },
                "with_context": {
                    "type": "boolean",
                    "description": "前後�Eチャンクも取得するかどぁE���E�デフォルチE true�E�E,
                    "default": True,
                },
                "context_size": {
                    "type": "integer",
                    "description": "前後に取得するチャンク数�E�デフォルチE 1�E�E,
                    "default": 1,
                },
                "full_document": {
                    "type": "boolean",
                    "description": "ドキュメント�E体を取得するかどぁE���E�デフォルチE false�E�E,
                    "default": False,
                },
            },
            "required": ["query"],
        },
        handler=lambda params: search_handler(params, rag_service),
    )

    # ドキュメント数取得ツールの登録
    server.register_tool(
        name="get_document_count",
        description="インチE��クス冁E�Eドキュメント数を取得しまぁE,
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=lambda params: get_document_count_handler(params, rag_service),
    )


def search_handler(params: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """
    ベクトル検索を行うハンドラ関数

    Args:
        params: パラメータ
            - query: 検索クエリ
            - limit: 返す結果の数�E�デフォルチE 5�E�E            - with_context: 前後�Eチャンクも取得するかどぁE���E�デフォルチE true�E�E            - context_size: 前後に取得するチャンク数�E�デフォルチE 1�E�E            - full_document: ドキュメント�E体を取得するかどぁE���E�デフォルチE false�E�E        rag_service: RAGサービスのインスタンス

    Returns:
        検索結果
    """
    query = params.get("query")
    limit = params.get("limit", 5)
    with_context = params.get("with_context", True)
    context_size = params.get("context_size", 1)
    full_document = params.get("full_document", False)

    if not query:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "エラー: 検索クエリが指定されてぁE��せん",
                }
            ],
            "isError": True,
        }

    try:
        # ドキュメント数を確誁E        doc_count = rag_service.get_document_count()
        if doc_count == 0:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "インチE��クスにドキュメントが存在しません、ELIコマンチE`python -m src.cli index` を使用してドキュメントをインチE��クス化してください、E,
                    }
                ],
                "isError": True,
            }

        # 検索を実行（前後�Eチャンクも取得、ドキュメント�E体も取得！E        results = rag_service.search(query, limit, with_context, context_size, full_document)

        if not results:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"クエリ '{query}' に一致する結果が見つかりませんでした",
                    }
                ]
            }

        # 結果をファイルごとにグループ化
        file_groups = {}
        for result in results:
            file_path = result["file_path"]
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(result)

        # 吁E��ループ�EでチャンクインチE��クスでソーチE        for file_path in file_groups:
            file_groups[file_path].sort(key=lambda x: x["chunk_index"])

        # 結果を整形
        content_items = [
            {
                "type": "text",
                "text": f"クエリ '{query}' の検索結果�E�Elen(results)} 件�E�E",
            }
        ]

        # ファイルごとに結果を表示
        for i, (file_path, group) in enumerate(file_groups.items()):
            file_name = os.path.basename(file_path)

            # ファイルヘッダー
            content_items.append(
                {
                    "type": "text",
                    "text": f"\n[{i + 1}] ファイル: {file_name}",
                }
            )

            # 吁E��ャンクを表示
            for j, result in enumerate(group):
                similarity_percent = result.get("similarity", 0) * 100
                is_context = result.get("is_context", False)
                is_full_document = result.get("is_full_document", False)

                # 全斁E��キュメント、コンチE��ストチャンク、検索ヒットチャンクで表示を変えめE                if is_full_document:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n+++ ドキュメント�E斁E��チャンク {result['chunk_index']}) +++\n{result['content']}",
                        }
                    )
                elif is_context:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n--- 前後�EコンチE��スト（チャンク {result['chunk_index']}) ---\n{result['content']}",
                        }
                    )
                else:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n=== 検索ヒット（チャンク {result['chunk_index']}, 類似度: {similarity_percent:.2f}%) ===\n{result['content']}",
                        }
                    )

        return {"content": content_items}

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"検索中にエラーが発生しました: {str(e)}",
                }
            ],
            "isError": True,
        }


def get_document_count_handler(params: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """
    インチE��クス冁E�Eドキュメント数を取得するハンドラ関数

    Args:
        params: パラメータ�E�未使用�E�E        rag_service: RAGサービスのインスタンス

    Returns:
        ドキュメント数
    """
    try:
        # ドキュメント数を取征E        count = rag_service.get_document_count()

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"インチE��クス冁E�Eドキュメント数: {count}",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ドキュメント数の取得中にエラーが発生しました: {str(e)}",
                }
            ],
            "isError": True,
        }


def create_rag_service_from_env() -> RAGService:
    """
    環墁E��数からRAGサービスを作�Eします、E
    Returns:
        RAGサービスのインスタンス
    """
    # 環墁E��数から接続情報を取征E    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")
    postgres_user = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "password")
    postgres_db = os.environ.get("POSTGRES_DB", "ragdb")

    embedding_model = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")

    # コンポ�Eネント�E作�E
    document_processor = DocumentProcessor()
    embedding_generator = EmbeddingGenerator(model_name=embedding_model)
    vector_database = VectorDatabase(
        {
            "host": postgres_host,
            "port": postgres_port,
            "user": postgres_user,
            "password": postgres_password,
            "database": postgres_db,
        }
    )

    # RAGサービスの作�E
    rag_service = RAGService(document_processor, embedding_generator, vector_database)

    return rag_service
