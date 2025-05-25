# -*- coding: utf-8 -*-
"""
エンベディング生成モジュール

テキストからエンベディングを生成します。
"""

import logging
from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """
    エンベディング生成クラス

    テキストからエンベディングを生成します。

    Attributes:
        model: SentenceTransformerモデル
        logger: ロガー
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        """
        EmbeddingGeneratorのコンストラクタ

        Args:
            model_name: 使用するモデル名（デフォルト: "intfloat/multilingual-e5-large"）
        """
        # ロガーの設定
        self.logger = logging.getLogger("embedding_generator")
        self.logger.setLevel(logging.INFO)

        # モデルの読み込み
        self.logger.info(f"モデル '{model_name}' を読み込んでいます...")
        try:
            self.model = SentenceTransformer(model_name)
            self.logger.info(f"モデル '{model_name}' を読み込みました")
        except Exception as e:
            self.logger.error(f"モデル '{model_name}' の読み込みに失敗しました: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        テキストからエンベディングを生成します。

        Args:
            text: エンベディングを生成するテキスト

        Returns:
            エンベディング（浮動小数点数のリスト）
        """
        if not text:
            self.logger.warning("空のテキストからエンベディングを生成しようとしています")
            return []

        try:
            # テキストの前処理
            # multilingual-e5-largeモデルの場合、クエリには "query: " プレフィックスを追加
            processed_text = f"query: {text}" if "query" not in text.lower() else text

            # エンベディングの生成
            embedding = self.model.encode(processed_text)

            # numpy配列をリストに変換
            embedding_list = embedding.tolist()

            self.logger.debug(f"テキスト '{text[:50]}...' のエンベディングを生成しました")
            return embedding_list

        except Exception as e:
            self.logger.error(f"エンベディングの生成中にエラーが発生しました: {str(e)}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        複数のテキストからエンベディングを生成します。

        Args:
            texts: エンベディングを生成するテキストのリスト

        Returns:
            エンベディングのリスト
        """
        if not texts:
            self.logger.warning("空のテキストリストからエンベディングを生成しようとしています")
            return []

        try:
            # テキストの前処理
            # multilingual-e5-largeモデルの場合、クエリには "query: " プレフィックスを追加
            processed_texts = [f"query: {text}" if "query" not in text.lower() else text for text in texts]

            # エンベディングの生成（バッチ処理）
            embeddings = self.model.encode(processed_texts)

            # numpy配列をリストに変換
            embeddings_list = embeddings.tolist()

            self.logger.info(f"{len(texts)} 個のテキストのエンベディングを生成しました")
            return embeddings_list

        except Exception as e:
            self.logger.error(f"エンベディングの生成中にエラーが発生しました: {str(e)}")
            raise

    def generate_search_embedding(self, query: str) -> List[float]:
        """
        検索クエリからエンベディングを生成します。

        Args:
            query: 検索クエリ

        Returns:
            エンベディング（浮動小数点数のリスト）
        """
        if not query:
            self.logger.warning("空のクエリからエンベディングを生成しようとしています")
            return []

        try:
            # multilingual-e5-largeモデルの場合、クエリには "query: " プレフィックスを追加
            processed_query = f"query: {query}" if "query" not in query.lower() else query

            # エンベディングの生成
            embedding = self.model.encode(processed_query)

            # numpy配列をリストに変換
            embedding_list = embedding.tolist()

            self.logger.debug(f"クエリ '{query}' のエンベディングを生成しました")
            return embedding_list

        except Exception as e:
            self.logger.error(f"クエリエンベディングの生成中にエラーが発生しました: {str(e)}")
            raise