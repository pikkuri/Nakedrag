"""
RAGサービスモジュール

ドキュメント�E琁E��エンベディング生�E、�EクトルチE�Eタベ�Eスを統合して、EインチE��クス化と検索の機�Eを提供します、E"""

import os
import time
import logging
from typing import List, Dict, Any

from .document_processor import DocumentProcessor
from .embedding_generator import EmbeddingGenerator
from .vector_database import VectorDatabase


class RAGService:
    """
    RAGサービスクラス

    ドキュメント�E琁E��エンベディング生�E、�EクトルチE�Eタベ�Eスを統合して、E    インチE��クス化と検索の機�Eを提供します、E
    Attributes:
        document_processor: ドキュメント�E琁E��ラスのインスタンス
        embedding_generator: エンベディング生�Eクラスのインスタンス
        vector_database: ベクトルチE�Eタベ�Eスクラスのインスタンス
        logger: ロガー
    """

    def __init__(
        self, document_processor: DocumentProcessor, embedding_generator: EmbeddingGenerator, vector_database: VectorDatabase
    ):
        """
        RAGServiceのコンストラクタ

        Args:
            document_processor: ドキュメント�E琁E��ラスのインスタンス
            embedding_generator: エンベディング生�Eクラスのインスタンス
            vector_database: ベクトルチE�Eタベ�Eスクラスのインスタンス
        """
        # ロガーの設宁E        self.logger = logging.getLogger("rag_service")
        self.logger.setLevel(logging.INFO)

        # コンポ�Eネント�E設宁E        self.document_processor = document_processor
        self.embedding_generator = embedding_generator
        self.vector_database = vector_database

        # チE�Eタベ�Eスの初期匁E        try:
            self.vector_database.initialize_database()
        except Exception as e:
            self.logger.error(f"チE�Eタベ�Eスの初期化に失敗しました: {str(e)}")
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
        チE��レクトリ冁E�EファイルをインチE��クス化します、E
        Args:
            source_dir: インチE��クス化するファイルが含まれるチE��レクトリのパス
            processed_dir: 処琁E��みファイルを保存するディレクトリのパス�E�指定がなぁE��合�Edata/processed�E�E            chunk_size: チャンクサイズ�E�文字数�E�E            chunk_overlap: チャンク間�Eオーバ�EラチE�E�E�文字数�E�E            incremental: 差刁E�EみをインチE��クス化するかどぁE��

        Returns:
            インチE��クス化�E結果
                - document_count: インチE��クス化されたドキュメント数
                - processing_time: 処琁E��間（秒！E                - success: 成功したかどぁE��
                - error: エラーメチE��ージ�E�エラーが発生した場合！E        """
        start_time = time.time()
        document_count = 0

        # 処琁E��みチE��レクトリのチE��ォルト値
        if processed_dir is None:
            processed_dir = "data/processed"

        try:
            # チE��レクトリ冁E�Eファイルを�E琁E            if incremental:
                self.logger.info(f"チE��レクトリ '{source_dir}' 冁E�E差刁E��ァイルをインチE��クス化してぁE��ぁE..")
            else:
                self.logger.info(f"チE��レクトリ '{source_dir}' 冁E�EファイルをインチE��クス化してぁE��ぁE..")

            chunks = self.document_processor.process_directory(
                source_dir, processed_dir, chunk_size, chunk_overlap, incremental
            )

            if not chunks:
                self.logger.warning(f"チE��レクトリ '{source_dir}' 冁E��処琁E��能なファイルが見つかりませんでした")
                return {
                    "document_count": 0,
                    "processing_time": time.time() - start_time,
                    "success": True,
                    "message": f"チE��レクトリ '{source_dir}' 冁E��処琁E��能なファイルが見つかりませんでした",
                }

            # チャンクのコンチE��チE��らエンベディングを生戁E            self.logger.info(f"{len(chunks)} チャンクのエンベディングを生成してぁE��ぁE..")
            texts = [chunk["content"] for chunk in chunks]
            embeddings = self.embedding_generator.generate_embeddings(texts)

            # ドキュメントをチE�Eタベ�Eスに挿入
            self.logger.info(f"{len(chunks)} チャンクをデータベ�Eスに挿入してぁE��ぁE..")
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
            self.logger.info(f"インチE��クス化が完亁E��ました�E�Edocument_count} ドキュメント、{processing_time:.2f} 秒！E)

            return {
                "document_count": document_count,
                "processing_time": processing_time,
                "success": True,
                "message": f"{document_count} ドキュメントをインチE��クス化しました",
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"インチE��クス化中にエラーが発生しました: {str(e)}")

            return {"document_count": document_count, "processing_time": processing_time, "success": False, "error": str(e)}

    def search(
        self, query: str, limit: int = 5, with_context: bool = False, context_size: int = 1, full_document: bool = False
    ) -> List[Dict[str, Any]]:
        """
        ベクトル検索を行います、E
        Args:
            query: 検索クエリ
            limit: 返す結果の数�E�デフォルチE 5�E�E            with_context: 前後�Eチャンクも取得するかどぁE���E�デフォルチE False�E�E            context_size: 前後に取得するチャンク数�E�デフォルチE 1�E�E            full_document: ドキュメント�E体を取得するかどぁE���E�デフォルチE False�E�E
        Returns:
            検索結果のリスト（関連度頁E��E                - document_id: ドキュメンチED
                - content: コンチE��チE                - file_path: ファイルパス
                - similarity: 類似度
                - metadata: メタチE�Eタ
                - is_context: コンチE��ストチャンクかどぁE���E�前後�Eチャンクの場合�ETrue�E�E                - is_full_document: 全斁E��キュメントかどぁE���E�ドキュメント�E体�E場合�ETrue�E�E        """
        try:
            # クエリからエンベディングを生戁E            self.logger.info(f"クエリ '{query}' のエンベディングを生成してぁE��ぁE..")
            query_embedding = self.embedding_generator.generate_search_embedding(query)

            # ベクトル検索
            self.logger.info(f"クエリ '{query}' でベクトル検索を実行してぁE��ぁE..")
            results = self.vector_database.search(query_embedding, limit)

            # 前後�Eチャンクも取得する場吁E            if with_context and context_size > 0:
                context_results = []
                processed_files = set()  # 処琁E��みのファイルとチャンクの絁E��合わせを記録

                for result in results:
                    file_path = result["file_path"]
                    chunk_index = result["chunk_index"]
                    file_chunk_key = f"{file_path}_{chunk_index}"

                    # 既に処琁E��みのファイルとチャンクの絁E��合わせ�EスキチE�E
                    if file_chunk_key in processed_files:
                        continue

                    processed_files.add(file_chunk_key)

                    # 前後�Eチャンクを取征E                    adjacent_chunks = self.vector_database.get_adjacent_chunks(file_path, chunk_index, context_size)
                    context_results.extend(adjacent_chunks)

                # 結果を�Eージ
                all_results = results.copy()

                # 重褁E��避けるために、既に結果に含まれてぁE��ドキュメンチEDを記録
                existing_doc_ids = {result["document_id"] for result in all_results}

                # 重褁E��てぁE��ぁE��ンチE��ストチャンクのみを追加
                for context in context_results:
                    if context["document_id"] not in existing_doc_ids:
                        all_results.append(context)
                        existing_doc_ids.add(context["document_id"])

                # ファイルパスとチャンクインチE��クスでソーチE                all_results.sort(key=lambda x: (x["file_path"], x["chunk_index"]))

                self.logger.info(f"検索結果�E�コンチE��スト含む�E�E {len(all_results)} 件")

                # ドキュメント�E体を取得する場吁E                if full_document:
                    full_doc_results = []
                    processed_files = set()  # 処琁E��みのファイルを記録

                    # 検索結果に含まれるファイルの全斁E��取征E                    for result in all_results:
                        file_path = result["file_path"]

                        # 既に処琁E��みのファイルはスキチE�E
                        if file_path in processed_files:
                            continue

                        processed_files.add(file_path)

                        # ファイルの全斁E��取征E                        full_doc_chunks = self.vector_database.get_document_by_file_path(file_path)
                        full_doc_results.extend(full_doc_chunks)

                    # 結果を�Eージ
                    merged_results = all_results.copy()

                    # 重褁E��避けるために、既に結果に含まれてぁE��ドキュメンチEDを記録
                    existing_doc_ids = {result["document_id"] for result in merged_results}

                    # 重褁E��てぁE��ぁE�E斁E��ャンクのみを追加
                    for doc_chunk in full_doc_results:
                        if doc_chunk["document_id"] not in existing_doc_ids:
                            merged_results.append(doc_chunk)
                            existing_doc_ids.add(doc_chunk["document_id"])

                    # ファイルパスとチャンクインチE��クスでソーチE                    merged_results.sort(key=lambda x: (x["file_path"], x["chunk_index"]))

                    self.logger.info(f"検索結果�E��E斁E��む�E�E {len(merged_results)} 件")
                    return merged_results
                else:
                    return all_results
            else:
                # ドキュメント�E体を取得する場吁E                if full_document:
                    full_doc_results = []
                    processed_files = set()  # 処琁E��みのファイルを記録

                    # 検索結果に含まれるファイルの全斁E��取征E                    for result in results:
                        file_path = result["file_path"]

                        # 既に処琁E��みのファイルはスキチE�E
                        if file_path in processed_files:
                            continue

                        processed_files.add(file_path)

                        # ファイルの全斁E��取征E                        full_doc_chunks = self.vector_database.get_document_by_file_path(file_path)
                        full_doc_results.extend(full_doc_chunks)

                    # 結果を�Eージ
                    merged_results = results.copy()

                    # 重褁E��避けるために、既に結果に含まれてぁE��ドキュメンチEDを記録
                    existing_doc_ids = {result["document_id"] for result in merged_results}

                    # 重褁E��てぁE��ぁE�E斁E��ャンクのみを追加
                    for doc_chunk in full_doc_results:
                        if doc_chunk["document_id"] not in existing_doc_ids:
                            merged_results.append(doc_chunk)
                            existing_doc_ids.add(doc_chunk["document_id"])

                    # ファイルパスとチャンクインチE��クスでソーチE                    merged_results.sort(key=lambda x: (x["file_path"], x["chunk_index"]))

                    self.logger.info(f"検索結果�E��E斁E��む�E�E {len(merged_results)} 件")
                    return merged_results
                else:
                    self.logger.info(f"検索結果: {len(results)} 件")
                    return results

        except Exception as e:
            self.logger.error(f"検索中にエラーが発生しました: {str(e)}")
            raise

    def clear_index(self) -> Dict[str, Any]:
        """
        インチE��クスをクリアします、E
        Returns:
            クリアの結果
                - deleted_count: 削除されたドキュメント数
                - success: 成功したかどぁE��
                - error: エラーメチE��ージ�E�エラーが発生した場合！E        """
        try:
            # チE�Eタベ�Eスをクリア
            self.logger.info("インチE��クスをクリアしてぁE��ぁE..")
            deleted_count = self.vector_database.clear_database()

            self.logger.info(f"インチE��クスをクリアしました�E�Edeleted_count} ドキュメントを削除�E�E)
            return {"deleted_count": deleted_count, "success": True, "message": f"{deleted_count} ドキュメントを削除しました"}

        except Exception as e:
            self.logger.error(f"インチE��クスのクリア中にエラーが発生しました: {str(e)}")

            return {"deleted_count": 0, "success": False, "error": str(e)}

    def get_document_count(self) -> int:
        """
        インチE��クス冁E�Eドキュメント数を取得します、E
        Returns:
            ドキュメント数
        """
        try:
            # ドキュメント数を取征E            count = self.vector_database.get_document_count()
            self.logger.info(f"インチE��クス冁E�Eドキュメント数: {count}")
            return count

        except Exception as e:
            self.logger.error(f"ドキュメント数の取得中にエラーが発生しました: {str(e)}")
            raise
