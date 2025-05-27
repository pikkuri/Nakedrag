# -*- coding: utf-8 -*-
# vector_database.py

import logging
import os
import glob
import json
import pathlib
from typing import List, Dict, Any, Tuple, Optional
from psycopg2.extras import execute_batch

from base_database import BaseDatabase
from chunk_processor import clean_text, chunk_splitter
from embedding_generator import EmbeddingGenerator

class VectorDatabase(BaseDatabase):
    """
    Markdownファイルをベクトル化して格納するデータベース。
    ./data/markdowns内のmdファイルを全てRAGで使用するベクトルの形に変換し、データを蓄積します。
    """

    def __init__(self, db_config: Dict[str, Any], dimension: int = 1024, markdown_dir: str = "./data/markdowns",
                 model_name: str = "intfloat/multilingual-e5-large", chunk_size: int = 500, chunk_overlap: int = 100):
        """
        ベクトルデータベースの初期化。

        Args:
            db_config (dict): データベース接続設定。
            dimension (int): ベクトルの次元数。
            markdown_dir (str): Markdownファイルが格納されているディレクトリ。
            model_name (str): 埋め込みベクトル生成に使用するモデル名。
            chunk_size (int): チャンクのサイズ。
            chunk_overlap (int): チャンクの重複サイズ。
        """
        super().__init__(db_config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dimension = dimension
        self.table_name = "vector_embeddings"
        self.markdown_dir = markdown_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_generator: Optional[EmbeddingGenerator] = None
        self.model_name = model_name

    def create_table(self) -> None:
        """
        Markdownファイルのテキストとベクトルを格納するテーブルを作成します。
        """
        self.execute_query("CREATE EXTENSION IF NOT EXISTS vector;", fetch=False)
        query = f'''
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            chunk_text TEXT NOT NULL,
            embedding VECTOR({self.dimension}) NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        self.execute_query(query, fetch=False)
        self.commit()
        self.logger.info(f"テーブル '{self.table_name}' を作成しました。")

    def store_markdown_chunk(self, chunk_text: str, embedding: List[float], filename: str, filepath: str, chunk_index: int) -> Optional[int]:
        """
        Markdownのチャンクとそのベクトル埋め込みを保存します。

        Args:
            chunk_text (str): Markdownテキストのチャンク。
            embedding (list): ベクトル埋め込み。
            filename (str): ファイル名。
            filepath (str): ファイルパス。
            chunk_index (int): チャンクのインデックス。

        Returns:
            int: 挿入されたチャンクのID。
        """
        try:
            query = f'''
            INSERT INTO {self.table_name} (chunk_text, embedding, filename, filepath, chunk_index)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            '''
            result = self.execute_query(query, (chunk_text, embedding, filename, filepath, chunk_index))
            return result[0][0] if result else None
        except Exception as e:
            self.logger.error(f"チャンクの挿入中にエラーが発生しました: {e}")
            return None

    def store_markdown_chunks(self, chunks: List[Dict[str, Any]]) -> List[int]:
        """
        複数のMarkdownチャンクを一括して保存します。

        Args:
            chunks (list): 保存するチャンクのリスト。各チャンクは
                          {'chunk_text': str, 'embedding': list, 'filename': str, 'filepath': str, 'chunk_index': int} の形式。

        Returns:
            list: 挿入されたチャンクのIDリスト。
        """
        if not chunks:
            return []

        data_to_insert = []
        for chunk in chunks:
            chunk_text = chunk.get('chunk_text', '')
            embedding = chunk.get('embedding', [])
            filename = chunk.get('filename', '')
            filepath = chunk.get('filepath', '')
            chunk_index = chunk.get('chunk_index', 0)
            data_to_insert.append((chunk_text, embedding, filename, filepath, chunk_index))

        try:
            with self.get_cursor() as cursor:
                query = f'''
                INSERT INTO {self.table_name} (chunk_text, embedding, filename, filepath, chunk_index)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                '''
                execute_batch(cursor, query, data_to_insert, page_size=100)
                self.connection.commit()

                cursor.execute(f'''
                SELECT id FROM {self.table_name}
                WHERE (chunk_text, filename, filepath) IN (
                    {','.join(['(%s, %s, %s)'] * len(chunks))}
                )
                ORDER BY id DESC
                LIMIT {len(chunks)}
                ''', [val for chunk in data_to_insert for val in (chunk[0], chunk[2], chunk[3])])

                ids = [row[0] for row in cursor.fetchall()]
                return ids
        except Exception as e:
            self.logger.error(f"チャンクの一括挿入中にエラーが発生しました: {e}")
            return []

    def get_all_vectors(self) -> List[Tuple]:
        """
        データベースから全てのベクトルを取得します。

        Returns:
            list: 全てのベクトルデータ。
        """
        query = f"SELECT id, chunk_text, embedding, filename, filepath, chunk_index FROM {self.table_name};"
        return self.execute_query(query)

    def get_file_vectors(self, filepath: str) -> List[Tuple]:
        """
        特定のファイルに関連するベクトルを取得します。

        Args:
            filepath (str): ファイルパス。

        Returns:
            list: ファイルに関連するベクトルデータ。
        """
        query = f"SELECT id, chunk_text, embedding, filename, filepath, chunk_index FROM {self.table_name} WHERE filepath = %s;"
        return self.execute_query(query, (filepath,))

    def get_processed_files(self) -> List[str]:
        """
        すでに処理されたファイルのリストを取得します。

        Returns:
            list: 処理済みファイルのパスリスト。
        """
        query = f"SELECT DISTINCT filepath FROM {self.table_name};"
        result = self.execute_query(query)
        return [row[0] for row in result] if result else []

    def delete_file_vectors(self, filepath: str) -> int:
        """
        特定のファイルに関連するベクトルを削除します。

        Args:
            filepath (str): 削除するファイルのパス。

        Returns:
            int: 削除されたベクトルの数。
        """
        try:
            count_query = f"SELECT COUNT(*) FROM {self.table_name} WHERE filepath = %s;"
            count_result = self.execute_query(count_query, (filepath,))
            count = count_result[0][0] if count_result else 0

            query = f"DELETE FROM {self.table_name} WHERE filepath = %s;"
            self.execute_query(query, (filepath,), fetch=False)

            return count
        except Exception as e:
            self.logger.error(f"ファイルのベクトル削除中にエラーが発生しました: {e}")
            return 0

    def clear_table(self) -> bool:
        """
        テーブルの全データを削除します。

        Returns:
            bool: 成功したかどうか。
        """
        try:
            query = f"TRUNCATE TABLE {self.table_name} RESTART IDENTITY;"
            self.execute_query(query, fetch=False)
            self.logger.info(f"テーブル '{self.table_name}' の全データを削除しました。")
            return True
        except Exception as e:
            self.logger.error(f"テーブルのクリア中にエラーが発生しました: {e}")
            return False

    def _init_embedding_generator(self) -> None:
        """
        埋め込みベクトル生成器を初期化します。
        """
        if self.embedding_generator is None:
            self.logger.info(f"埋め込みベクトル生成器を初期化しています。モデル: {self.model_name}")
            self.embedding_generator = EmbeddingGenerator(model_name=self.model_name)

    def _read_markdown_file(self, file_path: str) -> str:
        """
        Markdownファイルを読み込みます。

        Args:
            file_path (str): ファイルパス。

        Returns:
            str: ファイルの内容。
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            self.logger.error(f"ファイル '{file_path}' の読み込み中にエラーが発生しました: {e}")
            return ""

    
    def _process_markdown_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Markdownファイルを処理し、チャンク化して埋め込みベクトルを生成します。
        
        Args:
            file_path (str): ファイルパス。
            
        Returns:
            List[Dict[str, Any]]: チャンクと埋め込みベクトルのリスト。
        """
        # 埋め込みベクトル生成器を初期化
        self._init_embedding_generator()
        
        # ファイル情報を取得
        file_path_obj = pathlib.Path(file_path)
        filename = file_path_obj.name
        filepath = str(file_path_obj.absolute())
        
        # ファイルを読み込む
        content = self._read_markdown_file(file_path)
        if not content:
            return []
        
        # テキストをクリーンアップ
        cleaned_text = clean_text(content)
        
        # テキストをチャンク化
        chunks = chunk_splitter(cleaned_text, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        
        self.logger.info(f"ファイル '{filename}' を {len(chunks)} 個のチャンクに分割しました。")
        
        # 各チャンクの埋め込みベクトルを生成
        result = []
        embeddings = self.embedding_generator.generate_embeddings(chunks)
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            result.append({
                'chunk_text': chunk,
                'embedding': embedding,
                'filename': filename,
                'filepath': filepath,
                'chunk_index': i
            })
        
        return result
    
    def process_markdown_directory(self) -> int:
        """
        Markdownディレクトリ内の全ての.mdファイルを処理します。
        
        Returns:
            int: 処理されたチャンクの総数。
        """
        # ディレクトリが存在するか確認
        if not os.path.exists(self.markdown_dir):
            self.logger.error(f"ディレクトリ '{self.markdown_dir}' が存在しません。")
            return 0
        
        # すでに処理されたファイルのリストを取得
        processed_files = self.get_processed_files()
        
        # .mdファイルを検索
        md_files = glob.glob(os.path.join(self.markdown_dir, "**/*.md"), recursive=True)
        
        if not md_files:
            self.logger.warning(f"ディレクトリ '{self.markdown_dir}' にMarkdownファイルが見つかりません。")
            return 0
        
        # 各ファイルを処理
        total_chunks = 0
        for file_path in md_files:
            abs_path = str(pathlib.Path(file_path).absolute())
            
            # すでに処理済みのファイルはスキップ
            if abs_path in processed_files:
                self.logger.info(f"ファイル '{file_path}' はすでに処理済みのためスキップします。")
                continue
            
            # ファイルを処理
            self.logger.info(f"ファイル '{file_path}' を処理しています...")
            chunks = self._process_markdown_file(file_path)
            
            if chunks:
                # チャンクをデータベースに格納
                self.store_markdown_chunks(chunks)
                total_chunks += len(chunks)
                self.logger.info(f"ファイル '{file_path}' の {len(chunks)} 個のチャンクを格納しました。")
        
        self.logger.info(f"合計 {total_chunks} 個のチャンクを格納しました。")
        return total_chunks
    
    def update_markdown_directory(self) -> Tuple[int, int, int]:
        """
        Markdownディレクトリ内のファイルを更新します。
        新しいファイルを処理し、削除されたファイルのデータを削除します。
        
        Returns:
            Tuple[int, int, int]: (新規チャンク数, 更新チャンク数, 削除チャンク数)。
        """
        # ディレクトリが存在するか確認
        if not os.path.exists(self.markdown_dir):
            self.logger.error(f"ディレクトリ '{self.markdown_dir}' が存在しません。")
            return (0, 0, 0)
        
        # すでに処理されたファイルのリストを取得
        processed_files = self.get_processed_files()
        
        # 現在の.mdファイルを検索
        current_md_files = [str(pathlib.Path(f).absolute()) for f in 
                           glob.glob(os.path.join(self.markdown_dir, "**/*.md"), recursive=True)]
        
        # 新規ファイル、変更されたファイル、削除されたファイルを特定
        new_files = [f for f in current_md_files if f not in processed_files]
        deleted_files = [f for f in processed_files if f not in current_md_files]
        
        # 変更されたファイルをチェックするためには、タイムスタンプなどの追加情報が必要
        # ここでは簡略化のため、変更されたファイルを再処理する機能は実装しない
        
        # 新規ファイルを処理
        new_chunks = 0
        for file_path in new_files:
            self.logger.info(f"新規ファイル '{file_path}' を処理しています...")
            chunks = self._process_markdown_file(file_path)
            
            if chunks:
                # チャンクをデータベースに格納
                self.store_markdown_chunks(chunks)
                new_chunks += len(chunks)
                self.logger.info(f"ファイル '{file_path}' の {len(chunks)} 個のチャンクを格納しました。")
        
        # 削除されたファイルのデータを削除
        deleted_chunks = 0
        for file_path in deleted_files:
            self.logger.info(f"削除されたファイル '{file_path}' のデータを削除しています...")
            count = self.delete_file_vectors(file_path)
            deleted_chunks += count
            self.logger.info(f"ファイル '{file_path}' の {count} 個のチャンクを削除しました。")
        
        self.logger.info(f"更新結果: {new_chunks} 個の新規チャンク、{deleted_chunks} 個の削除チャンク")
        return (new_chunks, 0, deleted_chunks)
