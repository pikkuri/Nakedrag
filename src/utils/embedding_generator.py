# -*- coding: utf-8 -*-
"""
エンベディング生成モジュール

テキストからエンベディングを生成します。
"""

import os
import torch
from typing import List
from sentence_transformers import SentenceTransformer
from src.utils.logger_util import setup_logger


class EmbeddingGenerator:
    """
    エンベディング生成クラス

    テキストからエンベディングを生成します。

    Attributes:
        model: SentenceTransformerモデル
        logger: ロガー
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large", model_dir: str = "./models", device: str = None):
        """
        EmbeddingGeneratorのコンストラクタ

        Args:
            model_name: 使用するモデル名（デフォルト: "intfloat/multilingual-e5-large"）
            model_dir: モデルを保存するディレクトリ（デフォルト: "./models"）
            device: 使用するデバイス（Noneの場合は自動選択）
        """
        # ロガーの設定
        self.logger = setup_logger("embedding_generator")
        
        # デバイスの設定
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.logger.info(f"PyTorchデバイス: {self.device}")
        
        # CUDAが利用可能な場合は詳細情報を表示
        if self.device == "cuda":
            self.logger.info(f"CUDAデバイス数: {torch.cuda.device_count()}")
            self.logger.info(f"CUDAデバイス名: {torch.cuda.get_device_name(0)}")
        
        # モデルディレクトリの作成（存在しない場合）
        os.makedirs(model_dir, exist_ok=True)
        
        # モデルのローカルパスを生成
        model_local_path = os.path.join(model_dir, os.path.basename(model_name))
        
        # モデルの読み込み
        try:
            # まずローカルディレクトリからモデルの読み込みを試みる
            if os.path.exists(model_local_path):
                self.logger.info(f"ローカルからモデル '{model_local_path}' を読み込んでいます...")
                self.model = SentenceTransformer(model_local_path, device=self.device)
                self.logger.info(f"ローカルからモデル '{model_local_path}' を読み込みました")
            else:
                # ローカルにモデルがない場合、オンラインから取得して保存
                self.logger.info(f"オンラインからモデル '{model_name}' を読み込んでいます...")
                self.model = SentenceTransformer(model_name, device=self.device)
                self.logger.info(f"モデル '{model_name}' を読み込みました")
                
                # モデルをローカルに保存
                self.logger.info(f"モデルを '{model_local_path}' に保存しています...")
                self.model.save(model_local_path)
                self.logger.info(f"モデルを '{model_local_path}' に保存しました")
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