#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGシステムメインクラス

このモジュールは、NakedRAGプロジェクトの主要機能を統合したメインクラスを提供します。
以下の機能を統合しています：
- Markdownファイルの生成（markdowns_maker.py）
- データベースの初期構築（database_maker.py）
- データベースの更新（database_updater.py）
- RAG検索機能
"""

import os
import sys
import argparse
from typing import Dict, Any, List, Tuple, Optional, Set
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 各モジュールのインポート
from src.rag.markdowns_maker import process_documents
from src.rag.database_maker import (
    ensure_directory_exists, 
    create_database, 
    enable_pgvector_extension, 
    create_rag_table, 
    create_vector_table
)
from src.rag.database_updater import (
    setup_db_config, 
    synchronize_databases
)
from src.rag.rag_database import RAGDatabase
from src.rag.vector_database import VectorDatabase
from src.utils.embedding_generator import EmbeddingGenerator
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class RAGSystem:
    """
    RAGシステムの主要機能を統合したメインクラス
    
    このクラスは以下の機能を提供します：
    1. ソースファイルからMarkdownファイルの生成
    2. データベースの初期構築
    3. データベースの更新
    4. RAG検索機能
    """
    
    def __init__(self, 
                 source_dir: str = "./data/source",
                 markdown_dir: str = "./data/markdowns",
                 db_config: Optional[Dict[str, Any]] = None,
                 llm_model: str = "gemma3:12b",
                 embedding_model: str = "intfloat/multilingual-e5-large",
                 chunk_size: int = 500,
                 chunk_overlap: int = 100):
        """
        RAGシステムの初期化
        
        Args:
            source_dir (str): ソースファイルのディレクトリパス
            markdown_dir (str): Markdownファイルのディレクトリパス
            db_config (Dict[str, Any], optional): データベース接続設定
            llm_model (str): LLMモデル名
            embedding_model (str): 埋め込みモデル名
            chunk_size (int): チャンクのサイズ
            chunk_overlap (int): チャンクの重複サイズ
        """
        # .envファイルから環境変数を読み込む
        load_dotenv()
        
        self.source_dir = source_dir
        self.markdown_dir = markdown_dir
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # データベース設定
        self.db_config = db_config if db_config is not None else setup_db_config()
        
        # データベースインスタンス
        self.rag_db = None
        self.vector_db = None
        
        # 埋め込みジェネレーター
        self.embedding_generator = None
        
        logger.info(f"RAGシステムを初期化しました。ソースディレクトリ: {source_dir}, Markdownディレクトリ: {markdown_dir}")
    
    def generate_markdowns(self, 
                          temperature: float = 0.0,
                          num_ctx: int = 2048,
                          num_predict: int = 1024) -> None:
        """
        ソースファイルからMarkdownファイルを生成します
        
        Args:
            temperature (float): LLMの温度パラメータ
            num_ctx (int): コンテキストウィンドウサイズ
            num_predict (int): 予測トークン数
        """
        logger.info("Markdownファイルの生成を開始します。")
        
        try:
            # ソースディレクトリとMarkdownディレクトリの存在確認
            ensure_directory_exists(self.source_dir)
            ensure_directory_exists(self.markdown_dir)
            
            # Markdownファイルの生成
            process_documents(
                source_dir=self.source_dir,
                output_dir=self.markdown_dir,
                model=self.llm_model,
                temperature=temperature,
                num_ctx=num_ctx,
                num_predict=num_predict
            )
            
            logger.info("Markdownファイルの生成が完了しました。")
        except Exception as e:
            logger.error(f"Markdownファイルの生成中にエラーが発生しました: {e}", exc_info=True)
            raise
    
    def initialize_database(self) -> None:
        """
        RAGとベクトルデータベースを初期化します
        """
        logger.info("データベースの初期化を開始します。")
        
        try:
            # データベースの作成
            create_database(self.db_config)
            
            # pgvector拡張機能の有効化
            enable_pgvector_extension(self.db_config)
            
            # RAGテーブルの作成
            create_rag_table(self.db_config)
            
            # ベクトルテーブルの作成
            create_vector_table(self.db_config)
            
            logger.info("データベースの初期化が完了しました。")
        except Exception as e:
            logger.error(f"データベースの初期化中にエラーが発生しました: {e}", exc_info=True)
            raise
    
    def update_database(self, 
                       reset_vector: bool = False, 
                       reset_rag: bool = False) -> Tuple[VectorDatabase, RAGDatabase]:
        """
        データベースを更新します
        
        Args:
            reset_vector (bool): ベクトルデータベースをリセットするかどうか
            reset_rag (bool): RAGデータベースをリセットするかどうか
            
        Returns:
            Tuple[VectorDatabase, RAGDatabase]: 更新されたデータベース
        """
        logger.info("データベースの更新を開始します。")
        
        try:
            # 埋め込みベクトル生成器の初期化
            self._init_embedding_generator()
            
            # データベースの同期
            vector_db, rag_db = synchronize_databases(
                self.db_config,
                self.markdown_dir,
                self.embedding_generator,
                reset_vector=reset_vector,
                reset_rag=reset_rag
            )
            
            self.vector_db = vector_db
            self.rag_db = rag_db
            
            logger.info("データベースの更新が完了しました。")
            return vector_db, rag_db
        except Exception as e:
            logger.error(f"データベースの更新中にエラーが発生しました: {e}", exc_info=True)
            raise
    
    def _init_embedding_generator(self) -> None:
        """
        埋め込みベクトル生成器を初期化します
        """
        if self.embedding_generator is None:
            self.embedding_generator = EmbeddingGenerator(model_name=self.embedding_model)
    
    def _init_rag_database(self) -> None:
        """
        RAGデータベースを初期化します
        """
        if self.rag_db is None:
            self.rag_db = RAGDatabase(self.db_config)
    
    def search(self, query: str, limit: int = 5, similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        RAGデータベースで検索を実行します
        
        Args:
            query (str): 検索クエリ
            limit (int): 結果の最大数
            similarity_threshold (float): 類似度の閾値
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        logger.info(f"検索を実行します。クエリ: {query}")
        
        try:
            # 埋め込みベクトル生成器の初期化（既に初期化されている場合はスキップ）
            if self.embedding_generator is None:
                self._init_embedding_generator()
            
            # RAGデータベースの初期化
            self._init_rag_database()
            
            # クエリの埋め込みベクトルを生成
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            # 検索を実行
            results = self.rag_db.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            # 結果を整形
            formatted_results = []
            for result in results:
                # 結果のカラム数に応じて処理を分ける
                if len(result) == 7:  # original_filepathが含まれている場合
                    doc_id, text, filename, filepath, original_filepath, chunk_index, similarity = result
                else:  # 従来の形式
                    doc_id, text, filename, filepath, chunk_index, similarity = result
                    original_filepath = None
                
                formatted_results.append({
                    'id': doc_id,
                    'text': text,
                    'filename': filename,
                    'filepath': filepath,
                    'original_filepath': original_filepath,
                    'chunk_index': chunk_index,
                    'similarity': similarity
                })
            
            logger.info(f"検索結果: {len(formatted_results)}件")
            return formatted_results
        except Exception as e:
            logger.error(f"検索中にエラーが発生しました: {e}", exc_info=True)
            raise
    
    def search_exact(self, query: str, limit: int = 5, similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        RAGデータベースで正確な検索を実行します
        
        Args:
            query (str): 検索クエリ
            limit (int): 結果の最大数
            similarity_threshold (float): 類似度の閾値
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        logger.info(f"正確な検索を実行します。クエリ: {query}")
        
        try:
            # 埋め込みベクトル生成器の初期化（既に初期化されている場合はスキップ）
            if self.embedding_generator is None:
                self._init_embedding_generator()
            
            # RAGデータベースの初期化
            self._init_rag_database()
            
            # クエリの埋め込みベクトルを生成
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            # 検索を実行
            results = self.rag_db.search_similar_exact(
                query_embedding=query_embedding,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            # 結果を整形
            formatted_results = []
            for result in results:
                # 結果のカラム数に応じて処理を分ける
                if len(result) == 7:  # original_filepathが含まれている場合
                    doc_id, text, filename, filepath, original_filepath, chunk_index, similarity = result
                else:  # 従来の形式
                    doc_id, text, filename, filepath, chunk_index, similarity = result
                    original_filepath = None
                
                formatted_results.append({
                    'id': doc_id,
                    'text': text,
                    'filename': filename,
                    'filepath': filepath,
                    'original_filepath': original_filepath,
                    'chunk_index': chunk_index,
                    'similarity': similarity
                })
            
            logger.info(f"検索結果: {len(formatted_results)}件")
            return formatted_results
        except Exception as e:
            logger.error(f"検索中にエラーが発生しました: {e}", exc_info=True)
            raise
    
    def get_document_count(self) -> int:
        """
        RAGデータベース内のドキュメント数を取得します
        
        Returns:
            int: ドキュメント数
        """
        self._init_rag_database()
        return self.rag_db.get_document_count()
    
    def get_unique_sources(self) -> List[Tuple[str, str]]:
        """
        RAGデータベース内のユニークなソースを取得します
        
        Returns:
            List[Tuple[str, str]]: ユニークなソースのリスト（ファイル名とパス）
        """
        self._init_rag_database()
        return self.rag_db.get_unique_sources()
    
    def cleanup(self) -> None:
        """
        リソースをクリーンアップします
        """
        logger.info("リソースのクリーンアップを開始します。")
        
        if self.embedding_generator is not None:
            self.embedding_generator = None
        
        if self.vector_db is not None:
            self.vector_db.disconnect()
            self.vector_db = None
        
        if self.rag_db is not None:
            self.rag_db.disconnect()
            self.rag_db = None
        
        logger.info("リソースのクリーンアップが完了しました。")
    
    def __del__(self):
        """
        デストラクタ
        """
        self.cleanup()


def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description='RAGシステム')
    parser.add_argument('--source-dir', type=str, default='./data/source',
                        help='ソースファイルのディレクトリパス (デフォルト: ./data/source)')
    parser.add_argument('--markdown-dir', type=str, default='./data/markdowns',
                        help='Markdownファイルのディレクトリパス (デフォルト: ./data/markdowns)')
    parser.add_argument('--generate-markdowns', action='store_true',
                        help='Markdownファイルを生成する')
    parser.add_argument('--init-db', action='store_true',
                        help='データベースを初期化する')
    parser.add_argument('--update-db', action='store_true',
                        help='データベースを更新する')
    parser.add_argument('--reset-vector', action='store_true',
                        help='ベクトルデータベースのテーブルをリセットする')
    parser.add_argument('--reset-rag', action='store_true',
                        help='RAGデータベースのテーブルをリセットする')
    parser.add_argument('--reset-all', action='store_true',
                        help='すべてのデータベーステーブルをリセットする')
    parser.add_argument('--search', type=str,
                        help='検索クエリ')
    parser.add_argument('--limit', type=int, default=5,
                        help='検索結果の最大数 (デフォルト: 5)')
    parser.add_argument('--threshold', type=float, default=0.0,
                        help='類似度の閾値 (デフォルト: 0.0)')
    parser.add_argument('--exact-search', action='store_true',
                        help='正確な検索を実行する')
    
    args = parser.parse_args()
    
    try:
        # RAGシステムの初期化
        rag_system = RAGSystem(
            source_dir=args.source_dir,
            markdown_dir=args.markdown_dir
        )
        
        # Markdownファイルの生成
        if args.generate_markdowns:
            rag_system.generate_markdowns()
        
        # データベースの初期化
        if args.init_db:
            rag_system.initialize_database()
        
        # データベースの更新
        if args.update_db:
            reset_vector = args.reset_vector or args.reset_all
            reset_rag = args.reset_rag or args.reset_all
            rag_system.update_database(reset_vector, reset_rag)
        
        # 検索
        if args.search:
            if args.exact_search:
                results = rag_system.search_exact(
                    query=args.search,
                    limit=args.limit,
                    similarity_threshold=args.threshold
                )
            else:
                results = rag_system.search(
                    query=args.search,
                    limit=args.limit,
                    similarity_threshold=args.threshold
                )
            
            # 検索結果の表示
            print(f"\n検索結果 ({len(results)}件):")
            for i, result in enumerate(results, 1):
                print(f"\n結果 {i} (類似度: {result['similarity']:.4f}):")
                print(f"ファイル: {result['filename']} ({result['filepath']})")
                print(f"テキスト: {result['text'][:200]}...")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if 'rag_system' in locals():
            rag_system.cleanup()


if __name__ == "__main__":
    main()
