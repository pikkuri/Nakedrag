#!/usr/bin/env python
# -*- coding: utf-8 -*-
# inspect_databases.py

import os
import sys
import argparse
import pathlib
from typing import Dict, Any, List, Tuple, Optional
from tabulate import tabulate

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# srcモジュールをインポート
from src.rag.vector_database import VectorDatabase
from src.rag.rag_database import RAGDatabase
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

def setup_db_config() -> Dict[str, Any]:
    """
    データベース接続設定を返します。
    環境変数から設定を取得するか、デフォルト値を使用します。
    
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

def inspect_vector_database(db_config: Dict[str, Any]) -> None:
    """
    ベクトルデータベースの内容を検査して表示します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
    """
    logger.info("ベクトルデータベースを検査しています...")
    
    try:
        # ベクトルデータベースの初期化
        vector_db = VectorDatabase(
            db_config=db_config,
            dimension=1024
        )
        
        # テーブル構造の取得
        logger.info("テーブル構造:")
        table_structure = vector_db.execute_query(f"""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = '{vector_db.table_name}'
        ORDER BY ordinal_position;
        """)
        
        if table_structure:
            headers = ["カラム名", "データ型", "最大長"]
            print(tabulate(table_structure, headers=headers, tablefmt="grid"))
            
            # カラム名を取得してマッピング
            column_names = [col[0] for col in table_structure]
            
            # ファイル名のカラム名を確認
            filename_column = "filename" if "filename" in column_names else "source_filename"
            filepath_column = "filepath" if "filepath" in column_names else "source_filepath"
            
            # chunk_indexカラムが存在するか確認
            has_chunk_index = "chunk_index" in column_names
            
            logger.info(f"使用するカラム名: ファイル名={filename_column}, パス={filepath_column}, chunk_index存在={has_chunk_index}")
        else:
            logger.warning(f"テーブル '{vector_db.table_name}' が存在しないか、構造情報を取得できません。")
            return
        
        # レコード数の取得
        record_count = vector_db.execute_query(f"SELECT COUNT(*) FROM {vector_db.table_name};")
        if record_count:
            logger.info(f"レコード数: {record_count[0][0]}")
        
        # ユニークなファイル数の取得
        unique_files_query = f"SELECT COUNT(DISTINCT {filename_column}) FROM {vector_db.table_name};"
        unique_files = vector_db.execute_query(unique_files_query)
        if unique_files:
            logger.info(f"ユニークなファイル数: {unique_files[0][0]}")
            
        # original_filepathの状況を確認
        if "original_filepath" in column_names:
            # original_filepathがnullでないレコード数を取得
            not_null_query = f"SELECT COUNT(*) FROM {vector_db.table_name} WHERE original_filepath IS NOT NULL;"
            not_null_count = vector_db.execute_query(not_null_query)
            
            if not_null_count:
                logger.info(f"original_filepathが設定されているレコード数: {not_null_count[0][0]} / {record_count[0][0]}")
                
            # original_filepathのサンプルを取得
            sample_query = f"SELECT DISTINCT original_filepath FROM {vector_db.table_name} WHERE original_filepath IS NOT NULL LIMIT 10;"
            samples = vector_db.execute_query(sample_query)
            
            if samples:
                logger.info("original_filepathのサンプル:")
                for i, (filepath,) in enumerate(samples, 1):
                    logger.info(f"  {i}. {filepath}")
        
        # ファイル一覧の取得（original_filepathを含む）
        if "original_filepath" in column_names:
            files_query = f"SELECT DISTINCT {filename_column}, COUNT(*) as chunk_count, original_filepath FROM {vector_db.table_name} GROUP BY {filename_column}, original_filepath ORDER BY {filename_column} LIMIT 20;"
        else:
            files_query = f"SELECT DISTINCT {filename_column}, COUNT(*) as chunk_count FROM {vector_db.table_name} GROUP BY {filename_column} ORDER BY {filename_column} LIMIT 20;"
            
        files = vector_db.execute_query(files_query)
        if files:
            logger.info("ファイル一覧 (最大20件):")
            if "original_filepath" in column_names:
                headers = ["ファイル名", "チャンク数", "元ファイルパス"]
            else:
                headers = ["ファイル名", "チャンク数"]
            print(tabulate(files, headers=headers, tablefmt="grid"))
        
        # サンプルデータの取得
        logger.info("サンプルデータ (最初の5件):")
        
        # chunk_indexカラムがある場合とない場合でクエリを分ける
        if has_chunk_index:
            sample_query = f"""
            SELECT id, chunk_text, {filename_column}, {filepath_column}, 
                   {"original_filepath," if "original_filepath" in column_names else ""}
                   {"chunk_index," if has_chunk_index else ""} created_at
            FROM {vector_db.table_name}
            ORDER BY id
            LIMIT 5;
            """
        else:
            sample_query = f"""
            SELECT id, chunk_text, {filename_column}, {filepath_column}, 
                   {"original_filepath," if "original_filepath" in column_names else ""}
                   created_at
            FROM {vector_db.table_name}
            ORDER BY id
            LIMIT 5;
            """
        
        sample_data = vector_db.execute_query(sample_query)
        
        if sample_data:
            # テキストを短く切り詰める
            formatted_data = []
            for row in sample_data:
                formatted_row = list(row)
                # チャンクテキストを50文字に制限
                if len(str(formatted_row[1])) > 50:
                    formatted_row[1] = str(formatted_row[1])[:47] + "..."
                formatted_data.append(formatted_row)
            
            if has_chunk_index:
                headers = ["ID", "チャンクテキスト", "ファイル名", "ファイルパス", "元ファイルパス", "チャンクインデックス", "作成日時"]
            else:
                headers = ["ID", "チャンクテキスト", "ファイル名", "ファイルパス", "元ファイルパス", "作成日時"]
            
            print(tabulate(formatted_data, headers=headers, tablefmt="grid"))
        
        # ベクトルのサンプルデータ
        logger.info("ベクトルサンプル (最初のレコードの最初の10要素):")
        vector_sample = vector_db.execute_query(f"""
        SELECT embedding
        FROM {vector_db.table_name}
        ORDER BY id
        LIMIT 1;
        """)
        
        if vector_sample and vector_sample[0][0]:
            vector = vector_sample[0][0]
            # ベクトルの最初の10要素を表示
            print(vector[:10])
            logger.info(f"ベクトル次元数: {len(vector)}")
        
    except Exception as e:
        logger.error(f"ベクトルデータベース検査中にエラーが発生しました: {e}", exc_info=True)
    finally:
        if 'vector_db' in locals():
            vector_db.disconnect()

def inspect_rag_database(db_config: Dict[str, Any]) -> None:
    """
    RAGデータベースの内容を検査して表示します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
    """
    logger.info("RAGデータベースを検査しています...")
    
    try:
        # RAGデータベースの初期化
        rag_db = RAGDatabase(
            db_config=db_config,
            dimension=1024
        )
        
        # テーブル構造の取得
        logger.info("テーブル構造:")
        table_structure = rag_db.execute_query(f"""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = '{rag_db.table_name}'
        ORDER BY ordinal_position;
        """)
        
        if table_structure:
            headers = ["カラム名", "データ型", "最大長"]
            print(tabulate(table_structure, headers=headers, tablefmt="grid"))
            
            # カラム名のリストを取得
            column_names = [col[0] for col in table_structure]
            
            # original_filepathカラムの存在確認
            has_original_filepath = "original_filepath" in column_names
            logger.info(f"original_filepathカラムの存在: {has_original_filepath}")
            
            # カラム名を確認
            filename_column = "filename" if "filename" in column_names else "source_filename"
            filepath_column = "filepath" if "filepath" in column_names else "source_filepath"
            chunk_text_column = "chunk_text" if "chunk_text" in column_names else "original_text"
            
            logger.info(f"使用するカラム名: ファイル名={filename_column}, パス={filepath_column}, チャンクテキスト={chunk_text_column}")
        else:
            logger.warning(f"テーブル '{rag_db.table_name}' が存在しないか、構造情報を取得できません。")
        
        # レコード数の取得
        record_count = rag_db.get_document_count()
        logger.info(f"ドキュメント数: {record_count}")
        
        # ユニークなソースの取得
        sources = rag_db.get_unique_sources()
        logger.info(f"ユニークなソース数: {len(sources)}")
        
        if sources:
            logger.info("ソース一覧 (最初の10件):")
            headers = ["ファイル名", "ファイルパス"]
            print(tabulate(sources[:10], headers=headers, tablefmt="grid"))
            if len(sources) > 10:
                logger.info(f"...他 {len(sources) - 10} 件")
        
        # original_filepathの状況を確認
        if "original_filepath" in column_names:
            # original_filepathがnullでないレコード数を取得
            not_null_query = f"SELECT COUNT(*) FROM {rag_db.table_name} WHERE original_filepath IS NOT NULL;"
            not_null_count = rag_db.execute_query(not_null_query)
            
            if not_null_count:
                logger.info(f"original_filepathが設定されているレコード数: {not_null_count[0][0]} / {record_count}")
                
            # original_filepathのサンプルを取得
            sample_query = f"SELECT DISTINCT original_filepath FROM {rag_db.table_name} WHERE original_filepath IS NOT NULL LIMIT 10;"
            samples = rag_db.execute_query(sample_query)
            
            if samples:
                logger.info("original_filepathのサンプル:")
                for i, (filepath,) in enumerate(samples, 1):
                    logger.info(f"  {i}. {filepath}")
        
        # サンプルデータの取得
        record_count_value = record_count[0][0] if isinstance(record_count, list) else record_count
        if record_count and record_count_value > 0:
            logger.info("サンプルデータ (最初の5件):")
            
            if "original_filepath" in column_names:
                sample_query = f"""
                SELECT id, chunk_text, {filename_column}, {filepath_column}, original_filepath,
                       chunk_index, created_at
                FROM {rag_db.table_name}
                ORDER BY id
                LIMIT 5;
                """
            else:
                sample_query = f"""
                SELECT id, chunk_text, {filename_column}, {filepath_column},
                       chunk_index, created_at
                FROM {rag_db.table_name}
                ORDER BY id
                LIMIT 5;
                """
            
            sample_data = rag_db.execute_query(sample_query)
            
            if sample_data:
                # テキストを短く切り詰める
                formatted_data = []
                for row in sample_data:
                    formatted_row = list(row)
                    # チャンクテキストを50文字に制限
                    if len(str(formatted_row[1])) > 50:
                        formatted_row[1] = str(formatted_row[1])[:47] + "..."
                    formatted_data.append(formatted_row)
                
                if "original_filepath" in column_names:
                    headers = ["ID", "チャンクテキスト", "ファイル名", "ファイルパス", "元ファイルパス", "チャンクインデックス", "作成日時"]
                else:
                    headers = ["ID", "チャンクテキスト", "ファイル名", "ファイルパス", "チャンクインデックス", "作成日時"]
                
                print(tabulate(formatted_data, headers=headers, tablefmt="grid"))
            
            # ベクトルのサンプルデータ
            logger.info("ベクトルサンプル (最初のレコードの最初の10要素):")
            vector_sample = rag_db.execute_query(f"""
            SELECT embedding
            FROM {rag_db.table_name}
            ORDER BY id
            LIMIT 1;
            """)
            
            if vector_sample and vector_sample[0][0]:
                vector = vector_sample[0][0]
                # ベクトルの最初の10要素を表示
                print(vector[:10])
                logger.info(f"ベクトル次元数: {len(vector)}")
        
        # 検索インデックスの確認
        logger.info("検索インデックス情報:")
        index_info = rag_db.execute_query(f"""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = '{rag_db.table_name}';
        """)
        
        if index_info:
            headers = ["インデックス名", "インデックス定義"]
            print(tabulate(index_info, headers=headers, tablefmt="grid"))
        else:
            logger.warning(f"テーブル '{rag_db.table_name}' にインデックスが見つかりません。")
        
    except Exception as e:
        logger.error(f"RAGデータベース検査中にエラーが発生しました: {e}", exc_info=True)
    finally:
        if 'rag_db' in locals():
            rag_db.disconnect()

def inspect_search_parameters() -> None:
    """
    RAGSearchTestクラスの検索パラメータ設定を検査して表示します。
    """
    logger.info("RAGSearchTestクラスの検索パラメータを検査しています...")
    
    try:
        # test/rag_search_test.pyのパスを取得
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_test_path = os.path.join(script_dir, 'rag_search_test.py')
        
        if not os.path.exists(search_test_path):
            logger.warning(f"ファイル '{search_test_path}' が見つかりません。")
            return
        
        # ファイルを読み込んで__init__メソッドを探す
        with open(search_test_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # __init__メソッドのパラメータを正規表現で抽出
        import re
        init_pattern = r"def __init__\(self,[^)]*similarity_threshold: float = ([0-9.]+),[^)]*top_k: int = ([0-9]+)\)"
        match = re.search(init_pattern, content)
        
        if match:
            similarity_threshold = match.group(1)
            top_k = match.group(2)
            
            logger.info(f"検索パラメータ設定:")
            print(tabulate([
                ["similarity_threshold", similarity_threshold],
                ["top_k", top_k]
            ], headers=["パラメータ", "値"], tablefmt="grid"))
        else:
            logger.warning("検索パラメータの設定が見つかりませんでした。")
    
    except Exception as e:
        logger.error(f"検索パラメータの検査中にエラーが発生しました: {e}", exc_info=True)

def main():
    """
    メイン関数。コマンドライン引数に基づいて、ベクトルデータベースまたはRAGデータベース、
    あるいは両方のデータベースを検査します。
    """
    parser = argparse.ArgumentParser(description='ベクトルデータベースとRAGデータベースの内容を検査します。')
    parser.add_argument('--vector', action='store_true', help='ベクトルデータベースを検査します')
    parser.add_argument('--rag', action='store_true', help='RAGデータベースを検査します')
    parser.add_argument('--all', action='store_true', help='両方のデータベースを検査します')
    parser.add_argument('--params', action='store_true', help='RAGSearchTestクラスの検索パラメータを検査します')
    parser.add_argument('--original-paths', action='store_true', help='original_filepathの詳細情報のみを表示します')
    
    args = parser.parse_args()
    
    # デフォルトでは両方のデータベースを検査
    if not (args.vector or args.rag or args.all or args.params or args.original_paths):
        args.all = True
    
    # データベース接続設定
    vector_db_config = setup_db_config()
    vector_db_config['dbname'] = os.getenv('VECTOR_DB', 'vector_db')
    
    rag_db_config = setup_db_config()
    rag_db_config['dbname'] = os.getenv('RAG_DB', 'rag_db')
    
    try:
        # original_filepathのみの詳細表示
        if args.original_paths:
            # ベクトルデータベースのoriginal_filepathを表示
            vector_db = VectorDatabase(db_config=vector_db_config)
            logger.info("ベクトルデータベースのoriginal_filepath情報:")
            
            # カラムが存在するか確認
            column_check = vector_db.execute_query("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'vector_embeddings' AND column_name = 'original_filepath';
            """)
            
            if column_check:
                # レコード数を取得
                total_count = vector_db.execute_query("SELECT COUNT(*) FROM vector_embeddings;")
                not_null_count = vector_db.execute_query("SELECT COUNT(*) FROM vector_embeddings WHERE original_filepath IS NOT NULL;")
                
                if total_count and not_null_count:
                    logger.info(f"original_filepathが設定されているレコード数: {not_null_count[0][0]} / {total_count[0][0]}")
                
                # サンプルを取得
                samples = vector_db.execute_query("""
                SELECT filename, filepath, original_filepath 
                FROM vector_embeddings 
                WHERE original_filepath IS NOT NULL 
                GROUP BY filename, filepath, original_filepath 
                ORDER BY filename 
                LIMIT 50;
                """)
                
                if samples:
                    headers = ["ファイル名", "ファイルパス", "元ファイルパス"]
                    print(tabulate(samples, headers=headers, tablefmt="grid"))
            else:
                logger.warning("vector_embeddingsテーブルにoriginal_filepathカラムが存在しません")
            
            vector_db.disconnect()
            
            print("\n" + "="*80 + "\n")
            
            # RAGデータベースのoriginal_filepathを表示
            rag_db = RAGDatabase(db_config=rag_db_config)
            logger.info("RAGデータベースのoriginal_filepath情報:")
            
            # カラムが存在するか確認
            column_check = rag_db.execute_query("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'rag_documents' AND column_name = 'original_filepath';
            """)
            
            if column_check:
                # レコード数を取得
                total_count = rag_db.execute_query("SELECT COUNT(*) FROM rag_documents;")
                not_null_count = rag_db.execute_query("SELECT COUNT(*) FROM rag_documents WHERE original_filepath IS NOT NULL;")
                
                if total_count and not_null_count:
                    logger.info(f"original_filepathが設定されているレコード数: {not_null_count[0][0]} / {total_count[0][0]}")
                
                # サンプルを取得
                samples = rag_db.execute_query("""
                SELECT filename, filepath, original_filepath 
                FROM rag_documents 
                WHERE original_filepath IS NOT NULL 
                GROUP BY filename, filepath, original_filepath 
                ORDER BY filename 
                LIMIT 50;
                """)
                
                if samples:
                    headers = ["ファイル名", "ファイルパス", "元ファイルパス"]
                    print(tabulate(samples, headers=headers, tablefmt="grid"))
            else:
                logger.warning("rag_documentsテーブルにoriginal_filepathカラムが存在しません")
            
            rag_db.disconnect()
        else:
            # 通常の検査処理
            # 検索パラメータの検査
            if args.params:
                inspect_search_parameters()
                if args.vector or args.rag or args.all:
                    print("\n" + "="*80 + "\n")
            
            # ベクトルデータベースの検査
            if args.vector or args.all:
                inspect_vector_database(vector_db_config)
                if args.rag or args.all:
                    print("\n" + "="*80 + "\n")
            
            # RAGデータベースの検査
            if args.rag or args.all:
                inspect_rag_database(rag_db_config)
    
    except Exception as e:
        logger.error(f"データベース検査中にエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    main()
