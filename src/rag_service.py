"""
RAG繧ｵ繝ｼ繝薙せ繝｢繧ｸ繝･繝ｼ繝ｫ

繝峨く繝･繝｡繝ｳ繝亥・逅・√お繝ｳ繝吶ョ繧｣繝ｳ繧ｰ逕滓・縲√・繧ｯ繝医Ν繝・・繧ｿ繝吶・繧ｹ繧堤ｵｱ蜷医＠縺ｦ縲・繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹悶→讀懃ｴ｢縺ｮ讖溯・繧呈署萓帙＠縺ｾ縺吶・"""

import os
import time
import logging
from typing import List, Dict, Any

from .document_processor import DocumentProcessor
from .embedding_generator import EmbeddingGenerator
from .vector_database import VectorDatabase


class RAGService:
    """
    RAG繧ｵ繝ｼ繝薙せ繧ｯ繝ｩ繧ｹ

    繝峨く繝･繝｡繝ｳ繝亥・逅・√お繝ｳ繝吶ョ繧｣繝ｳ繧ｰ逕滓・縲√・繧ｯ繝医Ν繝・・繧ｿ繝吶・繧ｹ繧堤ｵｱ蜷医＠縺ｦ縲・    繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹悶→讀懃ｴ｢縺ｮ讖溯・繧呈署萓帙＠縺ｾ縺吶・
    Attributes:
        document_processor: 繝峨く繝･繝｡繝ｳ繝亥・逅・け繝ｩ繧ｹ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
        embedding_generator: 繧ｨ繝ｳ繝吶ョ繧｣繝ｳ繧ｰ逕滓・繧ｯ繝ｩ繧ｹ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
        vector_database: 繝吶け繝医Ν繝・・繧ｿ繝吶・繧ｹ繧ｯ繝ｩ繧ｹ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
        logger: 繝ｭ繧ｬ繝ｼ
    """

    def __init__(
        self, document_processor: DocumentProcessor, embedding_generator: EmbeddingGenerator, vector_database: VectorDatabase
    ):
        """
        RAGService縺ｮ繧ｳ繝ｳ繧ｹ繝医Λ繧ｯ繧ｿ

        Args:
            document_processor: 繝峨く繝･繝｡繝ｳ繝亥・逅・け繝ｩ繧ｹ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
            embedding_generator: 繧ｨ繝ｳ繝吶ョ繧｣繝ｳ繧ｰ逕滓・繧ｯ繝ｩ繧ｹ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
            vector_database: 繝吶け繝医Ν繝・・繧ｿ繝吶・繧ｹ繧ｯ繝ｩ繧ｹ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
        """
        # 繝ｭ繧ｬ繝ｼ縺ｮ險ｭ螳・        self.logger = logging.getLogger("rag_service")
        self.logger.setLevel(logging.INFO)

        # 繧ｳ繝ｳ繝昴・繝阪Φ繝医・險ｭ螳・        self.document_processor = document_processor
        self.embedding_generator = embedding_generator
        self.vector_database = vector_database

        # 繝・・繧ｿ繝吶・繧ｹ縺ｮ蛻晄悄蛹・        try:
            self.vector_database.initialize_database()
        except Exception as e:
            self.logger.error(f"繝・・繧ｿ繝吶・繧ｹ縺ｮ蛻晄悄蛹悶↓螟ｱ謨励＠縺ｾ縺励◆: {str(e)}")
            raise

    def index_documents(
        self,
        source_dir: str,
        processed_dir: str = None,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        incremental: bool = False,
    ) -> Dict[str, Any]:
        """
        繝・ぅ繝ｬ繧ｯ繝医Μ蜀・・繝輔ぃ繧､繝ｫ繧偵う繝ｳ繝・ャ繧ｯ繧ｹ蛹悶＠縺ｾ縺吶・
        Args:
            source_dir: 繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹悶☆繧九ヵ繧｡繧､繝ｫ縺悟性縺ｾ繧後ｋ繝・ぅ繝ｬ繧ｯ繝医Μ縺ｮ繝代せ
            processed_dir: 蜃ｦ逅・ｸ医∩繝輔ぃ繧､繝ｫ繧剃ｿ晏ｭ倥☆繧九ョ繧｣繝ｬ繧ｯ繝医Μ縺ｮ繝代せ・域欠螳壹′縺ｪ縺・ｴ蜷医・data/processed・・            chunk_size: 繝√Ε繝ｳ繧ｯ繧ｵ繧､繧ｺ・域枚蟄玲焚・・            chunk_overlap: 繝√Ε繝ｳ繧ｯ髢薙・繧ｪ繝ｼ繝舌・繝ｩ繝・・・域枚蟄玲焚・・            incremental: 蟾ｮ蛻・・縺ｿ繧偵う繝ｳ繝・ャ繧ｯ繧ｹ蛹悶☆繧九°縺ｩ縺・°

        Returns:
            繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹悶・邨先棡
                - document_count: 繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹悶＆繧後◆繝峨く繝･繝｡繝ｳ繝域焚
                - processing_time: 蜃ｦ逅・凾髢難ｼ育ｧ抵ｼ・                - success: 謌仙粥縺励◆縺九←縺・°
                - error: 繧ｨ繝ｩ繝ｼ繝｡繝・そ繝ｼ繧ｸ・医お繝ｩ繝ｼ縺檎匱逕溘＠縺溷ｴ蜷茨ｼ・        """
        start_time = time.time()
        document_count = 0

        # 蜃ｦ逅・ｸ医∩繝・ぅ繝ｬ繧ｯ繝医Μ縺ｮ繝・ヵ繧ｩ繝ｫ繝亥､
        if processed_dir is None:
            processed_dir = "data/processed"

        try:
            # 繝・ぅ繝ｬ繧ｯ繝医Μ蜀・・繝輔ぃ繧､繝ｫ繧貞・逅・            if incremental:
                self.logger.info(f"繝・ぅ繝ｬ繧ｯ繝医Μ '{source_dir}' 蜀・・蟾ｮ蛻・ヵ繧｡繧､繝ｫ繧偵う繝ｳ繝・ャ繧ｯ繧ｹ蛹悶＠縺ｦ縺・∪縺・..")
            else:
                self.logger.info(f"繝・ぅ繝ｬ繧ｯ繝医Μ '{source_dir}' 蜀・・繝輔ぃ繧､繝ｫ繧偵う繝ｳ繝・ャ繧ｯ繧ｹ蛹悶＠縺ｦ縺・∪縺・..")

            chunks = self.document_processor.process_directory(
                source_dir, processed_dir, chunk_size, chunk_overlap, incremental
            )

            if not chunks:
                self.logger.warning(f"繝・ぅ繝ｬ繧ｯ繝医Μ '{source_dir}' 蜀・↓蜃ｦ逅・庄閭ｽ縺ｪ繝輔ぃ繧､繝ｫ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縺ｧ縺励◆")
                return {
                    "document_count": 0,
                    "processing_time": time.time() - start_time,
                    "success": True,
                    "message": f"繝・ぅ繝ｬ繧ｯ繝医Μ '{source_dir}' 蜀・↓蜃ｦ逅・庄閭ｽ縺ｪ繝輔ぃ繧､繝ｫ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縺ｧ縺励◆",
                }

            # 繝√Ε繝ｳ繧ｯ縺ｮ繧ｳ繝ｳ繝・Φ繝・°繧峨お繝ｳ繝吶ョ繧｣繝ｳ繧ｰ繧堤函謌・            self.logger.info(f"{len(chunks)} 繝√Ε繝ｳ繧ｯ縺ｮ繧ｨ繝ｳ繝吶ョ繧｣繝ｳ繧ｰ繧堤函謌舌＠縺ｦ縺・∪縺・..")
            texts = [chunk["content"] for chunk in chunks]
            embeddings = self.embedding_generator.generate_embeddings(texts)

            # 繝峨く繝･繝｡繝ｳ繝医ｒ繝・・繧ｿ繝吶・繧ｹ縺ｫ謖ｿ蜈･
            self.logger.info(f"{len(chunks)} 繝√Ε繝ｳ繧ｯ繧偵ョ繝ｼ繧ｿ繝吶・繧ｹ縺ｫ謖ｿ蜈･縺励※縺・∪縺・..")
            documents = []
            for i, chunk in enumerate(chunks):
                documents.append(
                    {
                        "document_id": chunk["document_id"],
                        "content": chunk["content"],
                        "file_path": chunk["file_path"],
                        "chunk_index": chunk["chunk_index"],
                        "embedding": embeddings[i],
                        "metadata": {
                            "file_name": os.path.basename(chunk["file_path"]),
                            "directory": os.path.dirname(chunk["file_path"]),
                            "original_file_path": chunk.get("original_file_path", ""),
                            "directory_suffix": chunk.get("metadata", {}).get("directory_suffix", ""),
                        },
                    }
                )

            self.vector_database.batch_insert_documents(documents)
            document_count = len(documents)

            processing_time = time.time() - start_time
            self.logger.info(f"繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹悶′螳御ｺ・＠縺ｾ縺励◆・・document_count} 繝峨く繝･繝｡繝ｳ繝医＋processing_time:.2f} 遘抵ｼ・)

            return {
                "document_count": document_count,
                "processing_time": processing_time,
                "success": True,
                "message": f"{document_count} 繝峨く繝･繝｡繝ｳ繝医ｒ繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹悶＠縺ｾ縺励◆",
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"繧､繝ｳ繝・ャ繧ｯ繧ｹ蛹紋ｸｭ縺ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆: {str(e)}")

            return {"document_count": document_count, "processing_time": processing_time, "success": False, "error": str(e)}

    def search(
        self, query: str, limit: int = 5, with_context: bool = False, context_size: int = 1, full_document: bool = False
    ) -> List[Dict[str, Any]]:
        """
        繝吶け繝医Ν讀懃ｴ｢繧定｡後＞縺ｾ縺吶・
        Args:
            query: 讀懃ｴ｢繧ｯ繧ｨ繝ｪ
            limit: 霑斐☆邨先棡縺ｮ謨ｰ・医ョ繝輔か繝ｫ繝・ 5・・            with_context: 蜑榊ｾ後・繝√Ε繝ｳ繧ｯ繧ょ叙蠕励☆繧九°縺ｩ縺・°・医ョ繝輔か繝ｫ繝・ False・・            context_size: 蜑榊ｾ後↓蜿門ｾ励☆繧九メ繝｣繝ｳ繧ｯ謨ｰ・医ョ繝輔か繝ｫ繝・ 1・・            full_document: 繝峨く繝･繝｡繝ｳ繝亥・菴薙ｒ蜿門ｾ励☆繧九°縺ｩ縺・°・医ョ繝輔か繝ｫ繝・ False・・
        Returns:
            讀懃ｴ｢邨先棡縺ｮ繝ｪ繧ｹ繝茨ｼ磯未騾｣蠎ｦ鬆・ｼ・                - document_id: 繝峨く繝･繝｡繝ｳ繝・D
                - content: 繧ｳ繝ｳ繝・Φ繝・                - file_path: 繝輔ぃ繧､繝ｫ繝代せ
                - similarity: 鬘樔ｼｼ蠎ｦ
                - metadata: 繝｡繧ｿ繝・・繧ｿ
                - is_context: 繧ｳ繝ｳ繝・く繧ｹ繝医メ繝｣繝ｳ繧ｯ縺九←縺・°・亥燕蠕後・繝√Ε繝ｳ繧ｯ縺ｮ蝣ｴ蜷医・True・・                - is_full_document: 蜈ｨ譁・ラ繧ｭ繝･繝｡繝ｳ繝医°縺ｩ縺・°・医ラ繧ｭ繝･繝｡繝ｳ繝亥・菴薙・蝣ｴ蜷医・True・・        """
        try:
            # 繧ｯ繧ｨ繝ｪ縺九ｉ繧ｨ繝ｳ繝吶ョ繧｣繝ｳ繧ｰ繧堤函謌・            self.logger.info(f"繧ｯ繧ｨ繝ｪ '{query}' 縺ｮ繧ｨ繝ｳ繝吶ョ繧｣繝ｳ繧ｰ繧堤函謌舌＠縺ｦ縺・∪縺・..")
            query_embedding = self.embedding_generator.generate_search_embedding(query)

            # 繝吶け繝医Ν讀懃ｴ｢
            self.logger.info(f"繧ｯ繧ｨ繝ｪ '{query}' 縺ｧ繝吶け繝医Ν讀懃ｴ｢繧貞ｮ溯｡後＠縺ｦ縺・∪縺・..")
            results = self.vector_database.search(query_embedding, limit)

            # 蜑榊ｾ後・繝√Ε繝ｳ繧ｯ繧ょ叙蠕励☆繧句ｴ蜷・            if with_context and context_size > 0:
                context_results = []
                processed_files = set()  # 蜃ｦ逅・ｸ医∩縺ｮ繝輔ぃ繧､繝ｫ縺ｨ繝√Ε繝ｳ繧ｯ縺ｮ邨・∩蜷医ｏ縺帙ｒ險倬鹸

                for result in results:
                    file_path = result["file_path"]
                    chunk_index = result["chunk_index"]
                    file_chunk_key = f"{file_path}_{chunk_index}"

                    # 譌｢縺ｫ蜃ｦ逅・ｸ医∩縺ｮ繝輔ぃ繧､繝ｫ縺ｨ繝√Ε繝ｳ繧ｯ縺ｮ邨・∩蜷医ｏ縺帙・繧ｹ繧ｭ繝・・
                    if file_chunk_key in processed_files:
                        continue

                    processed_files.add(file_chunk_key)

                    # 蜑榊ｾ後・繝√Ε繝ｳ繧ｯ繧貞叙蠕・                    adjacent_chunks = self.vector_database.get_adjacent_chunks(file_path, chunk_index, context_size)
                    context_results.extend(adjacent_chunks)

                # 邨先棡繧偵・繝ｼ繧ｸ
                all_results = results.copy()

                # 驥崎､・ｒ驕ｿ縺代ｋ縺溘ａ縺ｫ縲∵里縺ｫ邨先棡縺ｫ蜷ｫ縺ｾ繧後※縺・ｋ繝峨く繝･繝｡繝ｳ繝・D繧定ｨ倬鹸
                existing_doc_ids = {result["document_id"] for result in all_results}

                # 驥崎､・＠縺ｦ縺・↑縺・さ繝ｳ繝・く繧ｹ繝医メ繝｣繝ｳ繧ｯ縺ｮ縺ｿ繧定ｿｽ蜉
                for context in context_results:
                    if context["document_id"] not in existing_doc_ids:
                        all_results.append(context)
                        existing_doc_ids.add(context["document_id"])

                # 繝輔ぃ繧､繝ｫ繝代せ縺ｨ繝√Ε繝ｳ繧ｯ繧､繝ｳ繝・ャ繧ｯ繧ｹ縺ｧ繧ｽ繝ｼ繝・                all_results.sort(key=lambda x: (x["file_path"], x["chunk_index"]))

                self.logger.info(f"讀懃ｴ｢邨先棡・医さ繝ｳ繝・く繧ｹ繝亥性繧・・ {len(all_results)} 莉ｶ")

                # 繝峨く繝･繝｡繝ｳ繝亥・菴薙ｒ蜿門ｾ励☆繧句ｴ蜷・                if full_document:
                    full_doc_results = []
                    processed_files = set()  # 蜃ｦ逅・ｸ医∩縺ｮ繝輔ぃ繧､繝ｫ繧定ｨ倬鹸

                    # 讀懃ｴ｢邨先棡縺ｫ蜷ｫ縺ｾ繧後ｋ繝輔ぃ繧､繝ｫ縺ｮ蜈ｨ譁・ｒ蜿門ｾ・                    for result in all_results:
                        file_path = result["file_path"]

                        # 譌｢縺ｫ蜃ｦ逅・ｸ医∩縺ｮ繝輔ぃ繧､繝ｫ縺ｯ繧ｹ繧ｭ繝・・
                        if file_path in processed_files:
                            continue

                        processed_files.add(file_path)

                        # 繝輔ぃ繧､繝ｫ縺ｮ蜈ｨ譁・ｒ蜿門ｾ・                        full_doc_chunks = self.vector_database.get_document_by_file_path(file_path)
                        full_doc_results.extend(full_doc_chunks)

                    # 邨先棡繧偵・繝ｼ繧ｸ
                    merged_results = all_results.copy()

                    # 驥崎､・ｒ驕ｿ縺代ｋ縺溘ａ縺ｫ縲∵里縺ｫ邨先棡縺ｫ蜷ｫ縺ｾ繧後※縺・ｋ繝峨く繝･繝｡繝ｳ繝・D繧定ｨ倬鹸
                    existing_doc_ids = {result["document_id"] for result in merged_results}

                    # 驥崎､・＠縺ｦ縺・↑縺・・譁・メ繝｣繝ｳ繧ｯ縺ｮ縺ｿ繧定ｿｽ蜉
                    for doc_chunk in full_doc_results:
                        if doc_chunk["document_id"] not in existing_doc_ids:
                            merged_results.append(doc_chunk)
                            existing_doc_ids.add(doc_chunk["document_id"])

                    # 繝輔ぃ繧､繝ｫ繝代せ縺ｨ繝√Ε繝ｳ繧ｯ繧､繝ｳ繝・ャ繧ｯ繧ｹ縺ｧ繧ｽ繝ｼ繝・                    merged_results.sort(key=lambda x: (x["file_path"], x["chunk_index"]))

                    self.logger.info(f"讀懃ｴ｢邨先棡・亥・譁・性繧・・ {len(merged_results)} 莉ｶ")
                    return merged_results
                else:
                    return all_results
            else:
                # 繝峨く繝･繝｡繝ｳ繝亥・菴薙ｒ蜿門ｾ励☆繧句ｴ蜷・                if full_document:
                    full_doc_results = []
                    processed_files = set()  # 蜃ｦ逅・ｸ医∩縺ｮ繝輔ぃ繧､繝ｫ繧定ｨ倬鹸

                    # 讀懃ｴ｢邨先棡縺ｫ蜷ｫ縺ｾ繧後ｋ繝輔ぃ繧､繝ｫ縺ｮ蜈ｨ譁・ｒ蜿門ｾ・                    for result in results:
                        file_path = result["file_path"]

                        # 譌｢縺ｫ蜃ｦ逅・ｸ医∩縺ｮ繝輔ぃ繧､繝ｫ縺ｯ繧ｹ繧ｭ繝・・
                        if file_path in processed_files:
                            continue

                        processed_files.add(file_path)

                        # 繝輔ぃ繧､繝ｫ縺ｮ蜈ｨ譁・ｒ蜿門ｾ・                        full_doc_chunks = self.vector_database.get_document_by_file_path(file_path)
                        full_doc_results.extend(full_doc_chunks)

                    # 邨先棡繧偵・繝ｼ繧ｸ
                    merged_results = results.copy()

                    # 驥崎､・ｒ驕ｿ縺代ｋ縺溘ａ縺ｫ縲∵里縺ｫ邨先棡縺ｫ蜷ｫ縺ｾ繧後※縺・ｋ繝峨く繝･繝｡繝ｳ繝・D繧定ｨ倬鹸
                    existing_doc_ids = {result["document_id"] for result in merged_results}

                    # 驥崎､・＠縺ｦ縺・↑縺・・譁・メ繝｣繝ｳ繧ｯ縺ｮ縺ｿ繧定ｿｽ蜉
                    for doc_chunk in full_doc_results:
                        if doc_chunk["document_id"] not in existing_doc_ids:
                            merged_results.append(doc_chunk)
                            existing_doc_ids.add(doc_chunk["document_id"])

                    # 繝輔ぃ繧､繝ｫ繝代せ縺ｨ繝√Ε繝ｳ繧ｯ繧､繝ｳ繝・ャ繧ｯ繧ｹ縺ｧ繧ｽ繝ｼ繝・                    merged_results.sort(key=lambda x: (x["file_path"], x["chunk_index"]))

                    self.logger.info(f"讀懃ｴ｢邨先棡・亥・譁・性繧・・ {len(merged_results)} 莉ｶ")
                    return merged_results
                else:
                    self.logger.info(f"讀懃ｴ｢邨先棡: {len(results)} 莉ｶ")
                    return results

        except Exception as e:
            self.logger.error(f"讀懃ｴ｢荳ｭ縺ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆: {str(e)}")
            raise

    def clear_index(self) -> Dict[str, Any]:
        """
        繧､繝ｳ繝・ャ繧ｯ繧ｹ繧偵け繝ｪ繧｢縺励∪縺吶・
        Returns:
            繧ｯ繝ｪ繧｢縺ｮ邨先棡
                - deleted_count: 蜑企勁縺輔ｌ縺溘ラ繧ｭ繝･繝｡繝ｳ繝域焚
                - success: 謌仙粥縺励◆縺九←縺・°
                - error: 繧ｨ繝ｩ繝ｼ繝｡繝・そ繝ｼ繧ｸ・医お繝ｩ繝ｼ縺檎匱逕溘＠縺溷ｴ蜷茨ｼ・        """
        try:
            # 繝・・繧ｿ繝吶・繧ｹ繧偵け繝ｪ繧｢
            self.logger.info("繧､繝ｳ繝・ャ繧ｯ繧ｹ繧偵け繝ｪ繧｢縺励※縺・∪縺・..")
            deleted_count = self.vector_database.clear_database()

            self.logger.info(f"繧､繝ｳ繝・ャ繧ｯ繧ｹ繧偵け繝ｪ繧｢縺励∪縺励◆・・deleted_count} 繝峨く繝･繝｡繝ｳ繝医ｒ蜑企勁・・)
            return {"deleted_count": deleted_count, "success": True, "message": f"{deleted_count} 繝峨く繝･繝｡繝ｳ繝医ｒ蜑企勁縺励∪縺励◆"}

        except Exception as e:
            self.logger.error(f"繧､繝ｳ繝・ャ繧ｯ繧ｹ縺ｮ繧ｯ繝ｪ繧｢荳ｭ縺ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆: {str(e)}")

            return {"deleted_count": 0, "success": False, "error": str(e)}

    def get_document_count(self) -> int:
        """
        繧､繝ｳ繝・ャ繧ｯ繧ｹ蜀・・繝峨く繝･繝｡繝ｳ繝域焚繧貞叙蠕励＠縺ｾ縺吶・
        Returns:
            繝峨く繝･繝｡繝ｳ繝域焚
        """
        try:
            # 繝峨く繝･繝｡繝ｳ繝域焚繧貞叙蠕・            count = self.vector_database.get_document_count()
            self.logger.info(f"繧､繝ｳ繝・ャ繧ｯ繧ｹ蜀・・繝峨く繝･繝｡繝ｳ繝域焚: {count}")
            return count

        except Exception as e:
            self.logger.error(f"繝峨く繝･繝｡繝ｳ繝域焚縺ｮ蜿門ｾ嶺ｸｭ縺ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆: {str(e)}")
            raise
