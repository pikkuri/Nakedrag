# -*- coding: utf-8 -*-
# base_database.py
import psycopg2
from contextlib import contextmanager
from src.utils.logger_util import setup_logger

class BaseDatabase:
    def __init__(self, db_config):
        """
        PostgreSQLデータベースの基本操作を提供する基底クラス
        
        Args:
            db_config (dict): データベース接続設定 (host, database, user, password, port)
        """
        self.db_config = db_config
        self.connection = None
        self.logger = setup_logger(self.__class__.__name__)
    
    def connect(self):
        """
        データベースに接続する
        """
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.logger.info("データベースに接続しました。")
        except Exception as e:
            self.logger.error(f"接続エラー: {e}")
            raise
    
    def disconnect(self):
        """
        データベースから切断する
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("データベースから切断しました。")
    
    @contextmanager
    def get_connection(self):
        """
        コネクションのコンテキストマネージャ
        """
        if not self.connection:
            self.connect()
        try:
            yield self.connection
        finally:
            pass  # 接続は明示的に閉じない (disconnect()で閉じる)
    
    @contextmanager
    def get_cursor(self):
        """
        カーソルのコンテキストマネージャ
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                yield cursor
    
    def execute_query(self, query, params=None, fetch=True):
        """
        SQLクエリを実行する
        
        Args:
            query (str): 実行するSQLクエリ
            params (tuple, dict, None): クエリパラメータ
            fetch (bool): 結果を取得するかどうか
            
        Returns:
            list: クエリ結果（fetch=Trueの場合）
        """
        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"クエリ実行中にエラーが発生しました: {e}")
                raise
        
    def execute_many(self, query, params_list):
        """
        複数のパラメータセットでSQLクエリを実行する
        
        Args:
            query (str): 実行するSQLクエリ
            params_list (list): パラメータのリスト
        """
        with self.get_cursor() as cursor:
            try:
                execute_batch(cursor, query, params_list)
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"バッチ実行中にエラーが発生しました: {e}")
                raise
    
    def commit(self):
        """
        トランザクションをコミットする
        """
        if self.connection:
            self.connection.commit()
            self.logger.debug("トランザクションをコミットしました。")
    
    def rollback(self):
        """
        トランザクションをロールバックする
        """
        if self.connection:
            self.connection.rollback()
            self.logger.debug("トランザクションをロールバックしました。")
    
    def table_exists(self, table_name):
        """
        テーブルが存在するかチェックする
        
        Args:
            table_name (str): チェックするテーブル名
            
        Returns:
            bool: テーブルが存在する場合True
        """
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
        """
        result = self.execute_query(query, (table_name,))
        return result[0][0] if result else False
