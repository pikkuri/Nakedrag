"""
RAGãEEã«ã¢ã¸ã¥ã¼ã«

MCPãµã¼ããEã«ç»é²ããRAGé¢é£ãEEã«ãæä¾ãã¾ããE"""

import os
from typing import Dict, Any

from .document_processor import DocumentProcessor
from .embedding_generator import EmbeddingGenerator
from .vector_database import VectorDatabase
from .rag_service import RAGService


def register_rag_tools(server, rag_service: RAGService):
    """
    RAGé¢é£ãEEã«ãMCPãµã¼ããEã«ç»é²ãã¾ããE
    Args:
        server: MCPãµã¼ããEã®ã¤ã³ã¹ã¿ã³ã¹
        rag_service: RAGãµã¼ãã¹ã®ã¤ã³ã¹ã¿ã³ã¹
    """
    # æ¤ç´¢ãEEã«ã®ç»é²
    server.register_tool(
        name="search",
        description="ãã¯ãã«æ¤ç´¢ãè¡ãã¾ãE,
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "æ¤ç´¢ã¯ã¨ãª",
                },
                "limit": {
                    "type": "integer",
                    "description": "è¿ãçµæã®æ°Eããã©ã«ãE 5EE,
                    "default": 5,
                },
                "with_context": {
                    "type": "boolean",
                    "description": "åå¾ãEãã£ã³ã¯ãåå¾ãããã©ãEEããã©ã«ãE trueEE,
                    "default": True,
                },
                "context_size": {
                    "type": "integer",
                    "description": "åå¾ã«åå¾ãããã£ã³ã¯æ°Eããã©ã«ãE 1EE,
                    "default": 1,
                },
                "full_document": {
                    "type": "boolean",
                    "description": "ãã­ã¥ã¡ã³ãåEä½ãåå¾ãããã©ãEEããã©ã«ãE falseEE,
                    "default": False,
                },
            },
            "required": ["query"],
        },
        handler=lambda params: search_handler(params, rag_service),
    )

    # ãã­ã¥ã¡ã³ãæ°åå¾ãã¼ã«ã®ç»é²
    server.register_tool(
        name="get_document_count",
        description="ã¤ã³ãEã¯ã¹åEEãã­ã¥ã¡ã³ãæ°ãåå¾ãã¾ãE,
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=lambda params: get_document_count_handler(params, rag_service),
    )


def search_handler(params: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """
    ãã¯ãã«æ¤ç´¢ãè¡ããã³ãã©é¢æ°

    Args:
        params: ãã©ã¡ã¼ã¿
            - query: æ¤ç´¢ã¯ã¨ãª
            - limit: è¿ãçµæã®æ°Eããã©ã«ãE 5EE            - with_context: åå¾ãEãã£ã³ã¯ãåå¾ãããã©ãEEããã©ã«ãE trueEE            - context_size: åå¾ã«åå¾ãããã£ã³ã¯æ°Eããã©ã«ãE 1EE            - full_document: ãã­ã¥ã¡ã³ãåEä½ãåå¾ãããã©ãEEããã©ã«ãE falseEE        rag_service: RAGãµã¼ãã¹ã®ã¤ã³ã¹ã¿ã³ã¹

    Returns:
        æ¤ç´¢çµæ
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
                    "text": "ã¨ã©ã¼: æ¤ç´¢ã¯ã¨ãªãæå®ããã¦ãE¾ãã",
                }
            ],
            "isError": True,
        }

    try:
        # ãã­ã¥ã¡ã³ãæ°ãç¢ºèªE        doc_count = rag_service.get_document_count()
        if doc_count == 0:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "ã¤ã³ãEã¯ã¹ã«ãã­ã¥ã¡ã³ããå­å¨ãã¾ãããELIã³ãã³ãE`python -m src.cli index` ãä½¿ç¨ãã¦ãã­ã¥ã¡ã³ããã¤ã³ãEã¯ã¹åãã¦ãã ãããE,
                    }
                ],
                "isError": True,
            }

        # æ¤ç´¢ãå®è¡ï¼åå¾ãEãã£ã³ã¯ãåå¾ããã­ã¥ã¡ã³ãåEä½ãåå¾ï¼E        results = rag_service.search(query, limit, with_context, context_size, full_document)

        if not results:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"ã¯ã¨ãª '{query}' ã«ä¸è´ããçµæãè¦ã¤ããã¾ããã§ãã",
                    }
                ]
            }

        # çµæããã¡ã¤ã«ãã¨ã«ã°ã«ã¼ãå
        file_groups = {}
        for result in results:
            file_path = result["file_path"]
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(result)

        # åE°ã«ã¼ãåEã§ãã£ã³ã¯ã¤ã³ãEã¯ã¹ã§ã½ã¼ãE        for file_path in file_groups:
            file_groups[file_path].sort(key=lambda x: x["chunk_index"])

        # çµæãæ´å½¢
        content_items = [
            {
                "type": "text",
                "text": f"ã¯ã¨ãª '{query}' ã®æ¤ç´¢çµæEElen(results)} ä»¶EE",
            }
        ]

        # ãã¡ã¤ã«ãã¨ã«çµæãè¡¨ç¤º
        for i, (file_path, group) in enumerate(file_groups.items()):
            file_name = os.path.basename(file_path)

            # ãã¡ã¤ã«ãããã¼
            content_items.append(
                {
                    "type": "text",
                    "text": f"\n[{i + 1}] ãã¡ã¤ã«: {file_name}",
                }
            )

            # åEã£ã³ã¯ãè¡¨ç¤º
            for j, result in enumerate(group):
                similarity_percent = result.get("similarity", 0) * 100
                is_context = result.get("is_context", False)
                is_full_document = result.get("is_full_document", False)

                # å¨æEã­ã¥ã¡ã³ããã³ã³ãE­ã¹ããã£ã³ã¯ãæ¤ç´¢ããããã£ã³ã¯ã§è¡¨ç¤ºãå¤ããE                if is_full_document:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n+++ ãã­ã¥ã¡ã³ãåEæE¼ãã£ã³ã¯ {result['chunk_index']}) +++\n{result['content']}",
                        }
                    )
                elif is_context:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n--- åå¾ãEã³ã³ãE­ã¹ãï¼ãã£ã³ã¯ {result['chunk_index']}) ---\n{result['content']}",
                        }
                    )
                else:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n=== æ¤ç´¢ãããï¼ãã£ã³ã¯ {result['chunk_index']}, é¡ä¼¼åº¦: {similarity_percent:.2f}%) ===\n{result['content']}",
                        }
                    )

        return {"content": content_items}

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"æ¤ç´¢ä¸­ã«ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}",
                }
            ],
            "isError": True,
        }


def get_document_count_handler(params: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """
    ã¤ã³ãEã¯ã¹åEEãã­ã¥ã¡ã³ãæ°ãåå¾ãããã³ãã©é¢æ°

    Args:
        params: ãã©ã¡ã¼ã¿Eæªä½¿ç¨EE        rag_service: RAGãµã¼ãã¹ã®ã¤ã³ã¹ã¿ã³ã¹

    Returns:
        ãã­ã¥ã¡ã³ãæ°
    """
    try:
        # ãã­ã¥ã¡ã³ãæ°ãåå¾E        count = rag_service.get_document_count()

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ã¤ã³ãEã¯ã¹åEEãã­ã¥ã¡ã³ãæ°: {count}",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ãã­ã¥ã¡ã³ãæ°ã®åå¾ä¸­ã«ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}",
                }
            ],
            "isError": True,
        }


def create_rag_service_from_env() -> RAGService:
    """
    ç°å¢E¤æ°ããRAGãµã¼ãã¹ãä½æEãã¾ããE
    Returns:
        RAGãµã¼ãã¹ã®ã¤ã³ã¹ã¿ã³ã¹
    """
    # ç°å¢E¤æ°ããæ¥ç¶æå ±ãåå¾E    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")
    postgres_user = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "password")
    postgres_db = os.environ.get("POSTGRES_DB", "ragdb")

    embedding_model = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")

    # ã³ã³ããEãã³ããEä½æE
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

    # RAGãµã¼ãã¹ã®ä½æE
    rag_service = RAGService(document_processor, embedding_generator, vector_database)

    return rag_service
