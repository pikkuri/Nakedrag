# -*- coding: utf-8 -*-
# rag_database.py
from src.rag.base_database import BaseDatabase
import numpy as np
import psycopg2
import os
from psycopg2.extras import execute_batch
from typing import Dict, List, Tuple, Any, Optional, Union
from src.utils.logger_util import setup_logger

class RAGDatabase(BaseDatabase):
    """
    RAG（Retrieval-Augmented Generation）用のデータベース操作を提供するクラス
    BaseDatabase を継承し、RAG特有の機能を追加します
    実際にRAGが参照するデータベースとして機能し、vector_database.pyからデータを取得して
    埋め込みベクトルをL2ノルム正規化した上で格納します
    """
    
    def __init__(self, db_config, dimension=1024, vector_db_config=None):
        """
        RAGデータベースの初期化
        
        Args:
            db_config (dict): データベース接続設定
            dimension (int): ベクトルの次元数
            vector_db_config (dict, optional): ベクトルデータベースの接続設定。Noneの場合は環境変数から取得
        """
        super().__init__(db_config)
        self.logger = setup_logger(self.__class__.__name__)
        self.table_name = "rag_documents"
        self.dimension = dimension
        
        # ベクトルデータベースの接続設定
        if vector_db_config is None:
            self.vector_db_config = {
                'dbname': os.getenv('VECTOR_DB', 'vector_db'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': os.getenv('POSTGRES_PORT', '5432')
            }
        else:
            self.vector_db_config = vector_db_config
    
    def create_table(self):
        """
        RAG用のドキュメントテーブルを作成します。
        """
        try:
            # pgvectorエクステンションが必要
            self.execute_query("CREATE EXTENSION IF NOT EXISTS vector;", fetch=False)
            
            query = f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id SERIAL PRIMARY KEY,
                chunk_text TEXT NOT NULL,
                embedding VECTOR({self.dimension}) NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                original_filepath TEXT,
                chunk_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            '''
            self.execute_query(query, fetch=False)
            self.commit()
            self.logger.info(f"テーブル '{self.table_name}' を作成しました。")
            return True
        except Exception as e:
            self.logger.error(f"テーブル作成中にエラーが発生しました: {e}")
            return False
        
        # 注意: インデックスはデータ挿入後に作成するため、ここでは作成しません
    
    def reset_table(self):
        """
        テーブルをリセットする（全データを削除し、テーブルを再作成する）
        """
        try:
            # テーブルを削除
            drop_query = f"DROP TABLE IF EXISTS {self.table_name};"
            self.execute_query(drop_query, fetch=False)
            # execute_queryは内部でコミットを行うようになったので、ここでのコミットは不要
            self.logger.info(f"テーブル '{self.table_name}' を削除しました。")
            
            # テーブルを再作成
            self.create_table()
            return True
        except Exception as e:
            self.logger.error(f"テーブルのリセット中にエラーが発生しました: {e}")
            return False
    
    def _normalize_embedding(self, embedding) -> List[float]:
        """
        埋め込みベクトルをL2ノルムで正規化します。
        文字列形式の埋め込みベクトルも処理できます。
        
        Args:
            embedding (Union[List[float], str]): 正規化する埋め込みベクトル。
            
        Returns:
            List[float]: 正規化された埋め込みベクトル。
        """
        try:
            # 文字列形式の場合は変換
            if isinstance(embedding, str):
                # 文字列から配列に変換
                if embedding.startswith('[') and embedding.endswith(']'):
                    # JSON形式の場合
                    import json
                    embedding = json.loads(embedding)
                else:
                    # カンマ区切りの場合
                    embedding = [float(x.strip()) for x in embedding.strip('[]').split(',')]
            
            # numpy配列に変換
            embedding_array = np.array(embedding, dtype=np.float32)
            
            # ゼロベクトルのチェック
            norm = np.linalg.norm(embedding_array)
            if norm < 1e-10:  # ほぼゼロの場合
                self.logger.warning("ゼロベクトルが検出されました。正規化をスキップします。")
                return embedding_array.tolist()
            
            # L2正規化
            normalized = embedding_array / norm
            
            return normalized.tolist()
        except Exception as e:
            self.logger.error(f"埋め込みベクトルの正規化中にエラーが発生しました: {e}")
            # エラーが発生した場合は元のベクトルをそのまま返す
            if isinstance(embedding, list):
                return embedding
            else:
                # 変換できない場合はゼロベクトルを返す
                return [0.0] * self.dimension
    
    def build_from_vector_database(self):
        """
        ベクトルデータベースから直接データを取得し、検索用に最適化して格納します。
        
        以下の処理を行います：
        1. ベクトルデータベースから生のチャンクデータとベクトルを取得
        2. ベクトルをL2ノルム正規化
        3. 検索用のメタデータを整理（ファイルパス、チャンクインデックスなど）
        4. 正規化・最適化されたデータをRAGデータベースに格納
        
        vector_database.pyはデータの蓄積用、このデータベースは検索用に最適化されます。
        
        Returns:
            int: 格納されたドキュメントの数。
        """
        # テーブルをリセット
        if not self.reset_table():
            self.logger.error("テーブルのリセットに失敗しました。")
            return 0
        
        vector_conn = None
        vector_cursor = None
        
        try:
            # ベクトルデータベースに直接接続
            vector_conn = psycopg2.connect(**self.vector_db_config)
            vector_cursor = vector_conn.cursor()
            
            # vector_embeddingsテーブルから全てのデータを取得
            vector_cursor.execute("""
                SELECT COUNT(*) FROM vector_embeddings
            """)
            count_result = vector_cursor.fetchone()
            total_count = count_result[0] if count_result else 0
            
            if total_count == 0:
                self.logger.warning("ベクトルデータベースにデータがありません。")
                return 0
                
            self.logger.info(f"ベクトルデータベースから {total_count} 件のデータを取得します。")
            
            # バッチ処理のためのサイズを設定
            batch_size = 1000
            processed_count = 0
            
            # バッチ処理でデータを取得して格納
            for offset in range(0, total_count, batch_size):
                self.logger.info(f"バッチ処理: {offset} - {min(offset + batch_size, total_count)} / {total_count}")
                
                # テーブルのカラム情報を取得して、カラム名を確認
                vector_cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'vector_embeddings' AND table_schema = 'public';
                """)
                columns = vector_cursor.fetchall()
                column_names = [col[0] for col in columns]
                
                # ファイル名とパスのカラム名を確認
                filename_column = "filename" if "filename" in column_names else "source_filename"
                filepath_column = "filepath" if "filepath" in column_names else "source_filepath"
                has_chunk_index = "chunk_index" in column_names
                has_original_filepath = "original_filepath" in column_names
                
                self.logger.info(f"使用するカラム名: ファイル名={filename_column}, パス={filepath_column}, chunk_index存在={has_chunk_index}, original_filepath存在={has_original_filepath}")
                
                # クエリを構築
                if has_chunk_index and has_original_filepath:
                    query = f"""
                        SELECT id, chunk_text, embedding, {filename_column}, {filepath_column}, chunk_index, original_filepath 
                        FROM vector_embeddings
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """
                elif has_chunk_index:
                    query = f"""
                        SELECT id, chunk_text, embedding, {filename_column}, {filepath_column}, chunk_index 
                        FROM vector_embeddings
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """
                elif has_original_filepath:
                    query = f"""
                        SELECT id, chunk_text, embedding, {filename_column}, {filepath_column}, original_filepath 
                        FROM vector_embeddings
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """
                else:
                    query = f"""
                        SELECT id, chunk_text, embedding, {filename_column}, {filepath_column} 
                        FROM vector_embeddings
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """
                
                # バッチでデータを取得
                vector_cursor.execute(query, (batch_size, offset))
                vectors_batch = vector_cursor.fetchall()
                
                # バッチ処理用のデータを準備
                batch_data = []
                for vector in vectors_batch:
                    # カラムの組み合わせによって処理を分ける
                    if has_chunk_index and has_original_filepath:
                        vec_id, chunk_text, embedding, filename, filepath, chunk_index, original_filepath = vector
                    elif has_chunk_index:
                        vec_id, chunk_text, embedding, filename, filepath, chunk_index = vector
                        original_filepath = None
                    elif has_original_filepath:
                        vec_id, chunk_text, embedding, filename, filepath, original_filepath = vector
                        chunk_index = None
                    else:
                        vec_id, chunk_text, embedding, filename, filepath = vector
                        chunk_index = None
                        original_filepath = None
                    
                    # 埋め込みベクトルを正規化
                    normalized_embedding = self._normalize_embedding(embedding)
                    batch_data.append((chunk_text, normalized_embedding, filename, filepath, original_filepath, chunk_index))
                
                # バッチで挿入
                with self.get_cursor() as cursor:
                    query = f'''
                    INSERT INTO {self.table_name} (chunk_text, embedding, filename, filepath, original_filepath, chunk_index)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    '''
                    execute_batch(cursor, query, batch_data, page_size=100)
                    self.connection.commit()
                
                processed_count += len(vectors_batch)
            
            # データ挿入後にインデックスを作成
            if processed_count > 0:
                self.logger.info("データ挿入完了後に検索インデックスを作成します。")
                self.create_search_index()
            
            self.logger.info(f"{processed_count}件のドキュメントをRAGデータベースに格納しました。")
            return processed_count
            
        except Exception as e:
            self.logger.error(f"ベクトルデータベースからのデータ取得中にエラーが発生しました: {e}")
            return 0
        finally:
            # リソースの確実な解放
            if vector_cursor:
                vector_cursor.close()
            if vector_conn:
                vector_conn.close()
    
    def create_search_index(self):
        """
        検索用のIVFFLATインデックスを作成します。
        データ量に応じてクラスタ数(lists)を動的に設定します。
        """
        try:
            # 既存のインデックスを削除
            drop_index_query = f"DROP INDEX IF EXISTS {self.table_name}_embedding_idx;"
            self.execute_query(drop_index_query, fetch=False)
            
            # データ量を取得して最適なクラスタ数を計算
            count_query = f"SELECT COUNT(*) FROM {self.table_name};"
            count_result = self.execute_query(count_query)
            row_count = count_result[0][0] if count_result else 0
            
            # データ量に応じてクラスタ数を設定
            # 少量データ（1000件未満）: 10クラスタ
            # 中量データ: sqrt(n)を目安
            # 大量データ（100万件以上）: 1000クラスタ
            if row_count < 1000:
                lists = 10
            elif row_count < 1000000:
                lists = int(np.sqrt(row_count))
            else:
                lists = 1000
                
            self.logger.info(f"データ量 {row_count} 件に対して {lists} クラスタでインデックスを作成します。")
            
            # 新しいインデックスを作成
            index_query = f'''
            CREATE INDEX {self.table_name}_embedding_idx 
            ON {self.table_name} 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = {lists});
            '''
            self.execute_query(index_query, fetch=False)
            self.logger.info(f"テーブル '{self.table_name}' にivfflat検索インデックスを作成しました。")
            return True
        except Exception as e:
            self.logger.error(f"検索インデックスの作成中にエラーが発生しました: {e}")
            return False
    
    def insert_document(self, text, embedding, filename, filepath, chunk_index=None):
        """
        ドキュメントをRAGテーブルに挿入します。
        
        Args:
            text (str): テキストチャンク。
            embedding (list): ベクトル埋め込み。
            filename (str): ファイル名。
            filepath (str): ファイルパス。
            chunk_index (int, optional): チャンクのインデックス。
            
        Returns:
            int: 挿入されたドキュメントのID。エラー時はNone。
        """
        try:
            # 埋め込みベクトルを正規化
            normalized_embedding = self._normalize_embedding(embedding)
            
            query = f'''
            INSERT INTO {self.table_name} (chunk_text, embedding, filename, filepath, chunk_index)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            '''
            result = self.execute_query(query, (text, normalized_embedding, filename, filepath, chunk_index))
            
            if result:
                doc_id = result[0][0]
                self.logger.debug(f"ID {doc_id} のドキュメントを挿入しました。")
                return doc_id
            return None
        except Exception as e:
            self.logger.error(f"ドキュメントの挿入中にエラーが発生しました: {e}")
            return None
    
    def search_similar(self, query_embedding: List[float], limit: int = 5, probes: Optional[int] = None, similarity_threshold: float = 0.0) -> List[Tuple]:
        """
        ivfflatインデックスを使用して類似ドキュメントを高速に検索します。
        
        Args:
            query_embedding (List[float]): 検索クエリのベクトル埋め込み。
            limit (int): 返す結果の最大数。
            probes (Optional[int]): 検索時に調査するクラスタ数。Noneの場合は自動設定。
            similarity_threshold (float): 類似度の最小閾値。0～1の間で指定し、この値以上の類似度を持つ結果のみ返します。
            
        Returns:
            List[Tuple]: 類似度順に並べられたドキュメントのリスト。
        """
        try:
            # クエリベクトルを正規化
            normalized_query = self._normalize_embedding(query_embedding)
            
            # インデックス情報を取得してprobesパラメータを設定
            if probes is None:
                # まずインデックスのクラスタ数を取得
                index_query = f"""
                SELECT indexdef FROM pg_indexes 
                WHERE tablename = '{self.table_name}' AND indexname = '{self.table_name}_embedding_idx';
                """
                index_result = self.execute_query(index_query)
                
                # デフォルトのクラスタ数
                lists = 100
                
                # インデックス定義からlistsパラメータを抽出
                if index_result:
                    indexdef = index_result[0][0]
                    import re
                    lists_match = re.search(r'WITH \(lists = (\d+)\)', indexdef)
                    if lists_match:
                        lists = int(lists_match.group(1))
                
                # pgvectorの推奨に従い、probesの初期値をsqrt(lists)に設定
                probes = int(np.sqrt(lists))
                
                # データ量に応じて調整
                count_query = f"SELECT COUNT(*) FROM {self.table_name};"
                count_result = self.execute_query(count_query)
                row_count = count_result[0][0] if count_result else 0
                
                # データ量が多い場合は、精度を高めるためにクラスタ数を増やす
                if row_count > 100000:
                    probes = max(probes, 20)  # 大量データの場合は最低20クラスタ
                
                self.logger.debug(f"クラスタ数 {lists} に対して probes={probes} で検索します。")
            
            # ivfflatインデックスの検索パラメータを設定
            self.execute_query(f"SET ivfflat.probes = {probes};", fetch=False)
            
            # 閾値を考慮して検索クエリを构築
            # 最初に多めに結果を取得し、後でフィルタリングするための上限
            search_limit = max(limit * 3, 20)  # 最低でも20件取得
            
            # 埋め込みベクトルをPGVECTOR形式に変換
            vector_str = f"'[{','.join(map(str, normalized_query))}]'::vector({self.dimension})"
            
            # テーブルにoriginal_filepathカラムが存在するか確認
            column_check_query = f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{self.table_name}' AND column_name = 'original_filepath';
            """
            column_check_result = self.execute_query(column_check_query)
            column_exists = len(column_check_result) > 0
            
            # コサイン類似度を使用して検索（カラムの存在に応じてクエリを調整）
            if column_exists:
                self.logger.debug(f"テーブル '{self.table_name}' にoriginal_filepathカラムが存在します。")
                query = f'''
                SELECT id, chunk_text, filename, filepath, original_filepath, chunk_index, 1 - (embedding <=> {vector_str}) as similarity
                FROM {self.table_name}
                WHERE 1 - (embedding <=> {vector_str}) >= {similarity_threshold}
                ORDER BY similarity DESC
                LIMIT {search_limit};
                '''
                results = self.execute_query(query)
                
                # 結果がない場合は空リストを返す
                if not results:
                    return []
                
                # 閾値でフィルタリングし、limitまでの結果を返す
                filtered_results = [r for r in results if r[6] >= similarity_threshold]
                limited_results = filtered_results[:limit]
                
            else:
                self.logger.debug(f"テーブル '{self.table_name}' にoriginal_filepathカラムが存在しません。")
                query = f'''
                SELECT id, chunk_text, filename, filepath, chunk_index, 1 - (embedding <=> {vector_str}) as similarity
                FROM {self.table_name}
                WHERE 1 - (embedding <=> {vector_str}) >= {similarity_threshold}
                ORDER BY similarity DESC
                LIMIT {search_limit};
                '''
                results = self.execute_query(query)
                
                # 結果がない場合は空リストを返す
                if not results:
                    return []
                
                # 閾値でフィルタリングし、limitまでの結果を返す
                filtered_results = [r for r in results if r[5] >= similarity_threshold]
                limited_results = filtered_results[:limit]
            
            # フィルタリング後の結果数をログに出力
            self.logger.debug(f"検索結果: 全{len(results)}件中{len(filtered_results)}件が閾値{similarity_threshold}以上、返却件数: {len(limited_results)}/{limit}")
            
            return limited_results
        
        except Exception as e:
            self.logger.error(f"類似ドキュメント検索中にエラーが発生しました: {e}", exc_info=True)
            return []
    
    def search_similar_exact(self, query_embedding: List[float], limit: int = 5, similarity_threshold: float = 0.0) -> List[Tuple]:
        """
        インデックスを使用せずに正確な類似ドキュメント検索を行います。
{{ ... }}
        
        Args:
            query_embedding (List[float]): 検索クエリのベクトル埋め込み。
            limit (int): 返す結果の最大数。
            similarity_threshold (float): 類似度の最小閾値。0～1の間で指定し、この値以上の類似度を持つ結果のみ返します。
            
        Returns:
            List[Tuple]: 類似度順に並べられたドキュメントのリスト。
        """
        # 検索設定を保存
        original_settings = {}
        
        try:
            # クエリベクトルを正規化
            normalized_query = self._normalize_embedding(query_embedding)
            
            # PostgreSQLのクエリプランナーの設定を保存
            original_settings = {}
            for setting in ['enable_indexscan', 'enable_seqscan']:
                result = self.execute_query(f"SHOW {setting};")
                if result:
                    original_settings[setting] = result[0][0]
            
            # インデックススキャンを無効化し、シーケンシャルスキャンを有効化
            self.execute_query("SET enable_indexscan = off;", fetch=False)
            self.execute_query("SET enable_seqscan = on;", fetch=False)
            
            # 閾値を考慮して検索クエリを构築
            search_limit = max(limit * 3, 20)  # 最低でも20件取得
            
            # 埋め込みベクトルをPGVECTOR形式に変換
            vector_str = f"'[{','.join(map(str, normalized_query))}]'::vector({self.dimension})"
            
            # テーブルにoriginal_filepathカラムが存在するか確認
            column_check_query = f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{self.table_name}' AND column_name = 'original_filepath';
            """
            column_exists = self.execute_query(column_check_query)
            
            # カラムの存在に応じてクエリを調整
            if column_exists:
                self.logger.debug(f"テーブル '{self.table_name}' にoriginal_filepathカラムが存在します。")
                query = f'''
                SELECT id, chunk_text, filename, filepath, original_filepath, chunk_index, 1 - (embedding <=> {vector_str}) as similarity
                FROM {self.table_name}
                WHERE 1 - (embedding <=> {vector_str}) >= {similarity_threshold}
                ORDER BY similarity DESC
                LIMIT {search_limit};
                '''
                results = self.execute_query(query)
                
                # 結果がない場合は空リストを返す
                if not results:
                    return []
                
                # 閾値でフィルタリングし、limitまでの結果を返す
                filtered_results = [r for r in results if r[6] >= similarity_threshold]
            else:
                self.logger.debug(f"テーブル '{self.table_name}' にoriginal_filepathカラムが存在しません。")
                query = f'''
                SELECT id, chunk_text, filename, filepath, chunk_index, 1 - (embedding <=> {vector_str}) as similarity
                FROM {self.table_name}
                ORDER BY similarity DESC
                LIMIT {search_limit};
                '''
                results = self.execute_query(query)
                
                # 結果がない場合は空リストを返す
                if not results:
                    return []
                
                # 閾値でフィルタリングし、limitまでの結果を返す
                filtered_results = [r for r in results if r[5] >= similarity_threshold]
            
            # フィルタリング後の結果数をログに出力
            self.logger.debug(f"正確検索結果: 全{len(results)}件中{len(filtered_results)}件が閾値{similarity_threshold}以上")
            
            return filtered_results[:limit]
            
        except Exception as e:
            self.logger.error(f"正確検索中にエラーが発生しました: {e}")
            return []
        finally:
            # 元の設定に戻す
            for setting, value in original_settings.items():
                self.execute_query(f"SET {setting} = {value};", fetch=False)
    
    def get_document_by_id(self, doc_id):
        """
        IDによりドキュメントを取得します。
        
        Args:
            doc_id (int): ドキュメントID。
            
        Returns:
            tuple: ドキュメント情報。見つからない場合はNone。
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = %s;"
            result = self.execute_query(query, (doc_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"ID {doc_id} のドキュメント取得中にエラーが発生しました: {e}")
            return None
    
    def get_document_count(self):
        """
        ドキュメントの総数を取得する
        
        Returns:
            int: ドキュメントの総数
        """
        query = f"SELECT COUNT(*) FROM {self.table_name};"
        result = self.execute_query(query)
        return result[0][0] if result else 0
    
    def get_unique_sources(self):
        """
        ユニークなファイルのリストを取得します。
        
        Returns:
            list: ファイルのリスト（ファイル名とパス）。
        """
        try:
            query = f"SELECT DISTINCT filename, filepath FROM {self.table_name};"
            return self.execute_query(query)
        except Exception as e:
            self.logger.error(f"ユニークファイルリストの取得中にエラーが発生しました: {e}")
            return []
    
    def delete_document(self, doc_id):
        """
        ドキュメントを削除します。
        
        Args:
            doc_id (int): 削除するドキュメントのID。
            
        Returns:
            bool: 削除が成功したかどうか。
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = %s;"
            self.execute_query(query, (doc_id,), fetch=False)
            self.logger.info(f"ID {doc_id} のドキュメントを削除しました。")
            return True
        except Exception as e:
            self.logger.error(f"ID {doc_id} のドキュメント削除中にエラーが発生しました: {e}")
            return False
