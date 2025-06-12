#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
データベース更新モジュール

このモジュールは、ベクトルデータベースとRAGデータベースの内容を更新するための機能を提供します。
既存のデータベースを更新したり、新しいデータを追加したりするためのユーティリティ関数が含まれています。
"""

import os
import sys
import argparse
from typing import Dict, Any, List, Tuple, Optional, Set

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.vector_database import VectorDatabase
from src.rag.rag_database import RAGDatabase
from src.utils.chunk_processor import chunk_splitter
from src.utils.embedding_generator import EmbeddingGenerator
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

def setup_db_config() -> Dict[str, Any]:
    """
    環境変数からデータベース接続設定を取得します。
    
    Returns:
        Dict[str, Any]: データベース接続設定
    """
    return {
        'dbname': os.getenv('POSTGRES_DB', 'postgres'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432'))
    }

def check_table_exists(db_config: Dict[str, Any], table_name: str) -> bool:
    """
    指定されたテーブルが存在するかどうかを確認します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        table_name (str): 確認するテーブル名
        
    Returns:
        bool: テーブルが存在する場合はTrue、それ以外はFalse
    """
    try:
        import psycopg2
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
            """, (table_name,))
            result = cursor.fetchone()
            exists = result[0] if result else False
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"テーブル '{table_name}' の存在確認中にエラーが発生しました: {e}")
        return False

def update_vector_database(db_config: Dict[str, Any], markdown_dir: str, reset_table: bool = False) -> VectorDatabase:
    """
    ベクトルデータベースを更新し、新しいMarkdownファイルを処理します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        markdown_dir (str): Markdownファイルのディレクトリパス
        reset_table (bool): テーブルをリセットするかどうか
        
    Returns:
        VectorDatabase: 更新されたベクトルデータベース
    """
    # ベクトルデータベースの初期化
    vector_db = VectorDatabase(db_config)
    
    # テーブルが存在することを確認
    logger.info("ベクトルデータベーステーブルを作成します（存在しない場合）...")
    vector_db.create_table()
    
    if reset_table:
        logger.info("ベクトルデータベーステーブルをリセットします...")
        vector_db.clear_table()
    else:
        logger.info("既存のベクトルデータベーステーブルを使用します。")
    
    # 既に処理済みのファイルを取得
    processed_files = vector_db.get_processed_files()
    processed_file_paths = set([file_path for file_path in processed_files])
    
    logger.info(f"Markdownディレクトリ '{markdown_dir}' を処理しています...")
    
    # ディレクトリ内のMarkdownファイルを取得
    markdown_files = []
    for root, _, files in os.walk(markdown_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                markdown_files.append(file_path)
    
    # 新しいファイルのみを処理
    new_files = [file_path for file_path in markdown_files if file_path not in processed_file_paths]
    
    if not new_files:
        logger.info("新しいMarkdownファイルはありません。")
        return vector_db
    
    logger.info(f"{len(new_files)}個の新しいMarkdownファイルを処理します。")
    
    # エンベディングジェネレータの初期化
    embedding_generator = EmbeddingGenerator()
    
    # 各Markdownファイルを処理
    total_chunks = 0
    for file_path in new_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ファイル名を取得
            file_name = os.path.basename(file_path)
            
            # テキストをチャンクに分割
            chunks = chunk_splitter(content, chunk_size=500, chunk_overlap=100)
            
            # 各チャンクを処理
            for i, chunk in enumerate(chunks):
                # 埋め込みベクトルを生成
                embedding = embedding_generator.generate_embedding(chunk)
                
                # 元ファイルのパスを取得する
                original_filepath = None
                try:
                    # ファイル名から拡張子を除いたベース名を取得
                    file_basename = os.path.basename(file_path)
                    base_filename_without_ext = os.path.splitext(file_basename)[0]
                    
                    logger.info(f"元ファイルの検索を開始: ファイル名={file_basename}, ベース名={base_filename_without_ext}")
                    
                    # ソースディレクトリのパスを取得
                    source_dir = os.path.join(os.path.dirname(os.path.dirname(markdown_dir)), "source")
                    
                    # ソースディレクトリが存在するか確認
                    if not os.path.exists(source_dir):
                        logger.warning(f"ソースディレクトリ '{source_dir}' が存在しません。")
                        # ディレクトリが存在しない場合は、Markdownファイルの相対パスを設定
                        original_filepath = os.path.relpath(file_path, os.path.dirname(os.path.dirname(markdown_dir)))
                        logger.info(f"ソースディレクトリが存在しないため、フォールバックとして設定した相対パス: {original_filepath}")
                    else:
                        # source_matching.pyのアルゴリズムを使用して元ファイルを検索
                        found = False
                        
                        # 方法1: 完全一致で検索
                        markdown_source_dir = os.path.join(source_dir, "markdown")
                        if os.path.exists(markdown_source_dir):
                            source_file = os.path.join(markdown_source_dir, file_basename)
                            logger.info(f"完全一致でチェック: {source_file}")
                            
                            if os.path.exists(source_file):
                                original_filepath = os.path.relpath(source_file, os.path.dirname(os.path.dirname(markdown_dir)))
                                logger.info(f"完全一致で見つかりました: original_filepath={original_filepath}")
                                found = True
                        
                        # 方法2: ベース名で検索
                        if not found and os.path.exists(markdown_source_dir):
                            try:
                                files_in_markdown_dir = [f for f in os.listdir(markdown_source_dir) if os.path.isfile(os.path.join(markdown_source_dir, f))]
                                logger.debug(f"markdownディレクトリ内のファイル: {files_in_markdown_dir}")
                                
                                for source_file_name in files_in_markdown_dir:
                                    source_base_name = os.path.splitext(source_file_name)[0]
                                    logger.debug(f"比較: {source_base_name} vs {base_filename_without_ext}")
                                    
                                    if source_base_name == base_filename_without_ext:
                                        source_file = os.path.join(markdown_source_dir, source_file_name)
                                        original_filepath = os.path.relpath(source_file, os.path.dirname(os.path.dirname(markdown_dir)))
                                        logger.info(f"ベース名一致で見つかりました: original_filepath={original_filepath}")
                                        found = True
                                        break
                            except Exception as e:
                                logger.error(f"markdownディレクトリの読み取り中にエラーが発生しました: {e}")
                        
                        # 方法3: 全サブディレクトリを検索
                        if not found:
                            for root, dirs, files in os.walk(source_dir):
                                if found:
                                    break
                                
                                for file in files:
                                    source_base_name = os.path.splitext(file)[0]
                                    if source_base_name == base_filename_without_ext:
                                        source_file = os.path.join(root, file)
                                        original_filepath = os.path.relpath(source_file, os.path.dirname(os.path.dirname(markdown_dir)))
                                        logger.info(f"サブディレクトリ内で見つかりました: original_filepath={original_filepath}")
                                        found = True
                                        break
                        
                        # どの方法でも見つからなかった場合
                        if not found:
                            logger.warning(f"ファイル '{file_basename}' に対応するソースファイルが見つかりませんでした。")
                            original_filepath = os.path.relpath(file_path, os.path.dirname(os.path.dirname(markdown_dir)))
                            logger.warning(f"元ファイルが見つからなかったため、フォールバックとして設定した相対パス: {original_filepath}")
                        
                        # デバッグ用に最終的な値をログ出力
                        logger.info(f"最終的なoriginal_filepath: {original_filepath}")
                except Exception as e:
                    logger.error(f"元ファイルパスの取得中にエラーが発生しました: {e}")
                    # エラーが発生した場合は、Markdownファイルの相対パスを設定
                    original_filepath = os.path.relpath(file_path, os.path.dirname(markdown_dir))
                
                # デバッグ用にoriginal_filepathの値を確認
                logger.debug(f"チャンク {i} のoriginal_filepath: {original_filepath}")
                
                # チャンクとその埋め込みベクトルをデータベースに保存
                # original_filepathが必ず設定されていることを確認
                if original_filepath is None or original_filepath == "":
                    # 最終手段として、Markdownファイルの相対パスを設定
                    original_filepath = os.path.relpath(file_path, os.path.dirname(os.path.dirname(markdown_dir)))
                    logger.warning(f"original_filepathが未設定のため、最終的に相対パスを設定: {original_filepath}")
                
                # 文字列型であることを確認
                if not isinstance(original_filepath, str):
                    logger.error(f"original_filepathが文字列型ではありません: {type(original_filepath)}")
                    original_filepath = str(original_filepath)
                
                # 空文字列でないことを確認
                if not original_filepath.strip():
                    logger.error("original_filepathが空文字列です")
                    original_filepath = f"data/markdowns/{os.path.basename(file_path)}"
                
                # 保存前に最終確認
                logger.info(f"データベースに保存するoriginal_filepath: '{original_filepath}'")
                
                # データベースに保存
                try:
                    chunk_id = vector_db.store_markdown_chunk(
                        chunk_text=chunk,
                        embedding=embedding,
                        filename=os.path.basename(file_path),
                        filepath=file_path,
                        original_filepath=original_filepath,
                        chunk_index=i
                    )
                    logger.info(f"チャンクを保存しました。ID: {chunk_id}, original_filepath: '{original_filepath}'")
                except Exception as e:
                    logger.error(f"チャンクの保存中にエラーが発生しました: {e}")
                    # エラーの詳細情報を表示
                    import traceback
                    logger.error(traceback.format_exc())
            
            total_chunks += len(chunks)
            logger.info(f"ファイル '{file_name}' を処理しました。{len(chunks)}個のチャンクを格納しました。")
            
        except Exception as e:
            logger.error(f"ファイル '{file_path}' の処理中にエラーが発生しました: {e}")
    
    logger.info(f"合計 {total_chunks} 個のチャンクを処理しました。")
    return vector_db

def update_rag_database(db_config: Dict[str, Any], vector_db: VectorDatabase, reset_table: bool = False) -> RAGDatabase:
    """
    RAGデータベースを更新し、ベクトルデータベースからデータを取り込みます。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        vector_db (VectorDatabase): ベクトルデータベース
        reset_table (bool): テーブルをリセットするかどうか
        
    Returns:
        RAGDatabase: 更新されたRAGデータベース
    """
    # RAGデータベースの初期化
    rag_db = RAGDatabase(db_config)
    
    if reset_table:
        logger.info("RAGデータベーステーブルをリセットします...")
        rag_db.reset_table()
    else:
        logger.info("既存のRAGデータベーステーブルを使用します。")
    
    # ベクトルデータベースからデータを取り込む
    logger.info("ベクトルデータベースからデータを取り込んでいます...")
    doc_count = rag_db.build_from_vector_database()
    logger.info(f"合計 {doc_count} 個のドキュメントを取り込みました。")
    
    # 検索インデックスの作成
    logger.info("検索インデックスを作成しています...")
    rag_db.create_search_index()
    
    return rag_db

def synchronize_databases(db_config: Dict[str, Any], markdown_dir: str, reset_vector_table: bool = False, reset_rag_table: bool = False) -> Tuple[VectorDatabase, RAGDatabase]:
    """
    ベクトルデータベースとRAGデータベースを同期します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        markdown_dir (str): Markdownファイルのディレクトリパス
        reset_vector_table (bool): ベクトルデータベースのテーブルをリセットするかどうか
        reset_rag_table (bool): RAGデータベースのテーブルをリセットするかどうか
        
    Returns:
        Tuple[VectorDatabase, RAGDatabase]: 更新されたデータベース
    """
    try:
        # ベクトルデータベースの更新
        logger.info("ベクトルデータベースを更新しています...")
        vector_db = update_vector_database(db_config, markdown_dir, reset_vector_table)
        logger.info("ベクトルデータベースの更新が完了しました。")
        
        # RAGデータベースの更新
        logger.info("RAGデータベースを更新しています...")
        rag_db = update_rag_database(db_config, vector_db, reset_rag_table)
        logger.info("RAGデータベースの更新が完了しました。")
        
        # ドキュメント数の確認
        doc_count = rag_db.get_document_count()
        logger.info(f"RAGデータベース内のドキュメント数: {doc_count}")
        
        # ユニークなソースの取得
        sources = rag_db.get_unique_sources()
        logger.info(f"RAGデータベース内のユニークなソース数: {len(sources)}")
        for i, (filename, filepath) in enumerate(sources[:5], 1):
            logger.info(f"ソース {i}: {filename} ({filepath})")
        
        if len(sources) > 5:
            logger.info(f"...他 {len(sources) - 5} 件のソース")
        
        logger.info("データベース同期が正常に完了しました。")
        
        return vector_db, rag_db
        
    except Exception as e:
        logger.error(f"データベース同期中にエラーが発生しました: {e}", exc_info=True)
        raise

def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description='データベース更新ツール')
    parser.add_argument('--markdown-dir', type=str, default='./data/markdowns',
                        help='Markdownファイルのディレクトリパス (デフォルト: ./data/markdowns)')
    parser.add_argument('--reset-vector', action='store_true',
                        help='ベクトルデータベースのテーブルをリセットする')
    parser.add_argument('--reset-rag', action='store_true',
                        help='RAGデータベースのテーブルをリセットする')
    parser.add_argument('--reset-all', action='store_true',
                        help='すべてのデータベーステーブルをリセットする')
    
    args = parser.parse_args()
    
    # 環境変数からデータベース設定を取得
    db_config = setup_db_config()
    
    # リセットフラグの設定
    reset_vector = args.reset_vector or args.reset_all
    reset_rag = args.reset_rag or args.reset_all
    
    try:
        # データベースの同期
        vector_db, rag_db = synchronize_databases(
            db_config, 
            args.markdown_dir, 
            reset_vector, 
            reset_rag
        )
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # 接続のクリーンアップ
        if 'vector_db' in locals():
            vector_db.disconnect()
        if 'rag_db' in locals():
            rag_db.disconnect()

if __name__ == "__main__":
    main()
