"""
RAG繝・・繝ｫ繝｢繧ｸ繝･繝ｼ繝ｫ

MCP繧ｵ繝ｼ繝舌・縺ｫ逋ｻ骭ｲ縺吶ｋRAG髢｢騾｣繝・・繝ｫ繧呈署萓帙＠縺ｾ縺吶・"""

import os
from typing import Dict, Any

from .document_processor import DocumentProcessor
from .embedding_generator import EmbeddingGenerator
from .vector_database import VectorDatabase
from .rag_service import RAGService


def register_rag_tools(server, rag_service: RAGService):
    """
    RAG髢｢騾｣繝・・繝ｫ繧樽CP繧ｵ繝ｼ繝舌・縺ｫ逋ｻ骭ｲ縺励∪縺吶・
    Args:
        server: MCP繧ｵ繝ｼ繝舌・縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
        rag_service: RAG繧ｵ繝ｼ繝薙せ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
    """
    # 讀懃ｴ｢繝・・繝ｫ縺ｮ逋ｻ骭ｲ
    server.register_tool(
        name="search",
        description="繝吶け繝医Ν讀懃ｴ｢繧定｡後＞縺ｾ縺・,
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "讀懃ｴ｢繧ｯ繧ｨ繝ｪ",
                },
                "limit": {
                    "type": "integer",
                    "description": "霑斐☆邨先棡縺ｮ謨ｰ・医ョ繝輔か繝ｫ繝・ 5・・,
                    "default": 5,
                },
                "with_context": {
                    "type": "boolean",
                    "description": "蜑榊ｾ後・繝√Ε繝ｳ繧ｯ繧ょ叙蠕励☆繧九°縺ｩ縺・°・医ョ繝輔か繝ｫ繝・ true・・,
                    "default": True,
                },
                "context_size": {
                    "type": "integer",
                    "description": "蜑榊ｾ後↓蜿門ｾ励☆繧九メ繝｣繝ｳ繧ｯ謨ｰ・医ョ繝輔か繝ｫ繝・ 1・・,
                    "default": 1,
                },
                "full_document": {
                    "type": "boolean",
                    "description": "繝峨く繝･繝｡繝ｳ繝亥・菴薙ｒ蜿門ｾ励☆繧九°縺ｩ縺・°・医ョ繝輔か繝ｫ繝・ false・・,
                    "default": False,
                },
            },
            "required": ["query"],
        },
        handler=lambda params: search_handler(params, rag_service),
    )

    # 繝峨く繝･繝｡繝ｳ繝域焚蜿門ｾ励ヤ繝ｼ繝ｫ縺ｮ逋ｻ骭ｲ
    server.register_tool(
        name="get_document_count",
        description="繧､繝ｳ繝・ャ繧ｯ繧ｹ蜀・・繝峨く繝･繝｡繝ｳ繝域焚繧貞叙蠕励＠縺ｾ縺・,
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=lambda params: get_document_count_handler(params, rag_service),
    )


def search_handler(params: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """
    繝吶け繝医Ν讀懃ｴ｢繧定｡後≧繝上Φ繝峨Λ髢｢謨ｰ

    Args:
        params: 繝代Λ繝｡繝ｼ繧ｿ
            - query: 讀懃ｴ｢繧ｯ繧ｨ繝ｪ
            - limit: 霑斐☆邨先棡縺ｮ謨ｰ・医ョ繝輔か繝ｫ繝・ 5・・            - with_context: 蜑榊ｾ後・繝√Ε繝ｳ繧ｯ繧ょ叙蠕励☆繧九°縺ｩ縺・°・医ョ繝輔か繝ｫ繝・ true・・            - context_size: 蜑榊ｾ後↓蜿門ｾ励☆繧九メ繝｣繝ｳ繧ｯ謨ｰ・医ョ繝輔か繝ｫ繝・ 1・・            - full_document: 繝峨く繝･繝｡繝ｳ繝亥・菴薙ｒ蜿門ｾ励☆繧九°縺ｩ縺・°・医ョ繝輔か繝ｫ繝・ false・・        rag_service: RAG繧ｵ繝ｼ繝薙せ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ

    Returns:
        讀懃ｴ｢邨先棡
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
                    "text": "繧ｨ繝ｩ繝ｼ: 讀懃ｴ｢繧ｯ繧ｨ繝ｪ縺梧欠螳壹＆繧後※縺・∪縺帙ｓ",
                }
            ],
            "isError": True,
        }

    try:
        # 繝峨く繝･繝｡繝ｳ繝域焚繧堤｢ｺ隱・        doc_count = rag_service.get_document_count()
        if doc_count == 0:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "繧､繝ｳ繝・ャ繧ｯ繧ｹ縺ｫ繝峨く繝･繝｡繝ｳ繝医′蟄伜惠縺励∪縺帙ｓ縲・LI繧ｳ繝槭Φ繝・`python -m src.cli index` 繧剃ｽｿ逕ｨ縺励※繝峨く繝･繝｡繝ｳ繝医ｒ繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹悶＠縺ｦ縺上□縺輔＞縲・,
                    }
                ],
                "isError": True,
            }

        # 讀懃ｴ｢繧貞ｮ溯｡鯉ｼ亥燕蠕後・繝√Ε繝ｳ繧ｯ繧ょ叙蠕励√ラ繧ｭ繝･繝｡繝ｳ繝亥・菴薙ｂ蜿門ｾ暦ｼ・        results = rag_service.search(query, limit, with_context, context_size, full_document)

        if not results:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"繧ｯ繧ｨ繝ｪ '{query}' 縺ｫ荳閾ｴ縺吶ｋ邨先棡縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縺ｧ縺励◆",
                    }
                ]
            }

        # 邨先棡繧偵ヵ繧｡繧､繝ｫ縺斐→縺ｫ繧ｰ繝ｫ繝ｼ繝怜喧
        file_groups = {}
        for result in results:
            file_path = result["file_path"]
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(result)

        # 蜷・げ繝ｫ繝ｼ繝怜・縺ｧ繝√Ε繝ｳ繧ｯ繧､繝ｳ繝・ャ繧ｯ繧ｹ縺ｧ繧ｽ繝ｼ繝・        for file_path in file_groups:
            file_groups[file_path].sort(key=lambda x: x["chunk_index"])

        # 邨先棡繧呈紛蠖｢
        content_items = [
            {
                "type": "text",
                "text": f"繧ｯ繧ｨ繝ｪ '{query}' 縺ｮ讀懃ｴ｢邨先棡・・len(results)} 莉ｶ・・",
            }
        ]

        # 繝輔ぃ繧､繝ｫ縺斐→縺ｫ邨先棡繧定｡ｨ遉ｺ
        for i, (file_path, group) in enumerate(file_groups.items()):
            file_name = os.path.basename(file_path)

            # 繝輔ぃ繧､繝ｫ繝倥ャ繝繝ｼ
            content_items.append(
                {
                    "type": "text",
                    "text": f"\n[{i + 1}] 繝輔ぃ繧､繝ｫ: {file_name}",
                }
            )

            # 蜷・メ繝｣繝ｳ繧ｯ繧定｡ｨ遉ｺ
            for j, result in enumerate(group):
                similarity_percent = result.get("similarity", 0) * 100
                is_context = result.get("is_context", False)
                is_full_document = result.get("is_full_document", False)

                # 蜈ｨ譁・ラ繧ｭ繝･繝｡繝ｳ繝医√さ繝ｳ繝・く繧ｹ繝医メ繝｣繝ｳ繧ｯ縲∵､懃ｴ｢繝偵ャ繝医メ繝｣繝ｳ繧ｯ縺ｧ陦ｨ遉ｺ繧貞､峨∴繧・                if is_full_document:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n+++ 繝峨く繝･繝｡繝ｳ繝亥・譁・ｼ医メ繝｣繝ｳ繧ｯ {result['chunk_index']}) +++\n{result['content']}",
                        }
                    )
                elif is_context:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n--- 蜑榊ｾ後・繧ｳ繝ｳ繝・く繧ｹ繝茨ｼ医メ繝｣繝ｳ繧ｯ {result['chunk_index']}) ---\n{result['content']}",
                        }
                    )
                else:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n=== 讀懃ｴ｢繝偵ャ繝茨ｼ医メ繝｣繝ｳ繧ｯ {result['chunk_index']}, 鬘樔ｼｼ蠎ｦ: {similarity_percent:.2f}%) ===\n{result['content']}",
                        }
                    )

        return {"content": content_items}

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"讀懃ｴ｢荳ｭ縺ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆: {str(e)}",
                }
            ],
            "isError": True,
        }


def get_document_count_handler(params: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """
    繧､繝ｳ繝・ャ繧ｯ繧ｹ蜀・・繝峨く繝･繝｡繝ｳ繝域焚繧貞叙蠕励☆繧九ワ繝ｳ繝峨Λ髢｢謨ｰ

    Args:
        params: 繝代Λ繝｡繝ｼ繧ｿ・域悴菴ｿ逕ｨ・・        rag_service: RAG繧ｵ繝ｼ繝薙せ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ

    Returns:
        繝峨く繝･繝｡繝ｳ繝域焚
    """
    try:
        # 繝峨く繝･繝｡繝ｳ繝域焚繧貞叙蠕・        count = rag_service.get_document_count()

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"繧､繝ｳ繝・ャ繧ｯ繧ｹ蜀・・繝峨く繝･繝｡繝ｳ繝域焚: {count}",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"繝峨く繝･繝｡繝ｳ繝域焚縺ｮ蜿門ｾ嶺ｸｭ縺ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆: {str(e)}",
                }
            ],
            "isError": True,
        }


def create_rag_service_from_env() -> RAGService:
    """
    迺ｰ蠅・､画焚縺九ｉRAG繧ｵ繝ｼ繝薙せ繧剃ｽ懈・縺励∪縺吶・
    Returns:
        RAG繧ｵ繝ｼ繝薙せ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
    """
    # 迺ｰ蠅・､画焚縺九ｉ謗･邯壽ュ蝣ｱ繧貞叙蠕・    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")
    postgres_user = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "password")
    postgres_db = os.environ.get("POSTGRES_DB", "ragdb")

    embedding_model = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")

    # 繧ｳ繝ｳ繝昴・繝阪Φ繝医・菴懈・
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

    # RAG繧ｵ繝ｼ繝薙せ縺ｮ菴懈・
    rag_service = RAGService(document_processor, embedding_generator, vector_database)

    return rag_service
