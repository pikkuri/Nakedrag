#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGシステムの検索機能を提供するモジュール

このモジュールは、NakedRAGプロジェクトのRAGシステムを使用して、
文書検索からLLMを用いた回答生成までの一連のフローを実行します。
結果はMarkdown形式で返され、MCPサーバーなどのクライアントが利用しやすい形式になっています。
"""

import os
import sys
import tempfile
import shutil
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re

# プロジェクトのルートディレクトリをパスに追加
# 現在のファイルは src/rag/rag_searcher.py なので、二つ上のディレクトリがルート
# これにより、直接実行してもインポートが正常に動作する
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
_root_dir = os.path.dirname(_parent_dir)
sys.path.append(_root_dir)

# dotenvをインポート
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# langchainのインポート
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.chains.llm import LLMChain

# PyTorchのデバイス設定
import torch
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # GPUを使用する場合

# 自作モジュールのインポート
from src.rag.rag_class import RAGSystem
from src.utils.embedding_generator import EmbeddingGenerator
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class RAGSearcher:
    """
    RAGシステムの検索機能を提供するクラス
    
    このクラスは以下の機能を提供します：
    1. ユーザークエリの理解と検索クエリへの変換
    2. 検索クエリを使用したRAGデータベースの検索
    3. 検索結果を使用した回答の生成
    4. 結果のMarkdown形式での出力
    """
    
    def __init__(self, 
                 llm_model: str = "gemma3:12b",
                 embedding_model: str = "intfloat/multilingual-e5-large",
                 temperature: float = 0.1,
                 similarity_threshold: float = 0.7,
                 top_k: int = 20):
        """
        RAG検索の初期化
        
        Args:
            llm_model (str): LLMモデル名
            embedding_model (str): 埋め込みモデル名
            temperature (float): LLMの温度パラメータ
            similarity_threshold (float): 検索の類似度閾値
            top_k (int): 検索結果の上位件数
        """
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.temperature = temperature
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        
        # RAGシステムの初期化
        self.rag_system = RAGSystem(
            embedding_model=embedding_model
        )
        
        # RAGSystemから埋め込みジェネレーターを取得する
        # 初期化されていない場合は初期化を促す
        self.rag_system._init_embedding_generator()
        self.embedding_generator = self.rag_system.embedding_generator
        
        # PyTorchのデバイス設定
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"PyTorchデバイス: {self.device}")
        
        # Ollamaの初期化
        try:
            # 環境変数からOllama設定を取得
            ollama_base_url = os.getenv('OLLAMA_BASE_URL')
            ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
            ollama_port = os.getenv('OLLAMA_PORT', '11434')
            
            # クライアント接続用にホスト名を調整
            # 0.0.0.0はサーバー側のリッスン設定であり、クライアントからの接続には使用できない
            if ollama_host == '0.0.0.0':
                client_host = 'localhost'
            else:
                client_host = ollama_host
            
            # base_urlが設定されている場合はそれを使用、そうでなければhost/portから構築
            if ollama_base_url:
                base_url = ollama_base_url
            else:
                # ホスト名にポート番号が含まれていないか確認
                if ':' in client_host:
                    # ホスト部分にすでにポートが含まれている場合は、そのまま使用
                    base_url = f"http://{client_host}"
                else:
                    # 通常のホスト名とポートの組み合わせ
                    base_url = f"http://{client_host}:{ollama_port}"
                
            # Ollamaクライアントの初期化
            self.llm = Ollama(model=llm_model, temperature=temperature, base_url=base_url)
            
            # Ollamaサーバーの接続確認
            import requests
            # クライアント接続用のURLを使用
            response = requests.get(f"{base_url}/api/version")
            if response.status_code == 200:
                logger.info(f"Ollamaサーバー接続成功: {response.json()}")
            else:
                logger.warning("Ollamaサーバーは起動していますが、応答が不正です")
        except Exception as e:
            logger.error(f"Ollamaの初期化中にエラーが発生しました: {e}")
            raise Exception("Ollamaサーバーに接続できません。サーバーが起動しているか確認してください。")
        
        logger.info(f"RAG検索を初期化しました。LLMモデル: {llm_model}, 埋め込みモデル: {embedding_model}")

    def understand_query(self, user_query: str) -> str:
        """
        ユーザークエリを理解し、検索クエリに変換します
        
        Args:
            user_query (str): ユーザーからの質問
            
        Returns:
            str: 検索用に最適化されたクエリ
        """
        logger.info(f"ユーザークエリの理解を開始します: {user_query}")
        
        try:
            # プロンプトテンプレートの作成
            understand_prompt = PromptTemplate(
                input_variables=["query"],
                template="""
                あなたはRAGシステムの一部として、ユーザーの質問を理解し、検索クエリに変換する役割を担っています。
                
                ユーザーの質問: {query}
                
                この質問を理解し、関連文書を検索するための最適なキーワードに変換してください。
                キーワードは日本語で、スペースで区切って提供してください。
                余分な説明は不要です。キーワードのみを返してください。
                
                検索キーワード:
                """
            )
            
            # LLMChainの作成と実行
            understand_chain = LLMChain(llm=self.llm, prompt=understand_prompt)
            search_query = understand_chain.invoke({"query": user_query})["text"].strip()
            
            logger.info(f"検索クエリに変換しました: {search_query}")
            return search_query
        except Exception as e:
            logger.error(f"クエリ理解中にエラーが発生しました: {e}", exc_info=True)
            # エラーが発生した場合は、元のクエリをそのまま返す
            logger.info(f"元のクエリを使用します: {user_query}")
            return user_query

    def search_documents(self, search_query: str) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
        """
        検索クエリを使用してRAGデータベースを検索します
        
        Args:
            search_query (str): 検索クエリ
            
        Returns:
            Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]: 検索結果とソースリスト
        """
        logger.info(f"検索を実行します: {search_query}")
        
        # 検索クエリの埋め込みベクトルを生成
        search_results = self.rag_system.search(
            query=search_query,
            limit=self.top_k,
            similarity_threshold=self.similarity_threshold
        )
        
        # ソースリストの作成
        sources = []
        unique_filepaths = set()  # 重複排除用のセット
        for result in search_results:
            filename = result.get('filename', 'unknown')
            filepath = result.get('filepath', '')
            
            # original_filepathがあればそれを優先
            original_filepath = result.get('original_filepath', '')
            if original_filepath:
                # 常にoriginal_filepathを使用し、存在確認はコピー処理時に行う
                filepath = original_filepath
                logger.info(f"検索結果 {filename} のoriginal_filepathを使用: {original_filepath}")
            else:
                logger.info(f"検索結果 {filename} のfilepathを使用: {filepath} (original_filepathなし)")
            
            # 重複チェック - 同じファイルパスは追加しない
            normalized_path = os.path.normpath(filepath)
            if normalized_path not in unique_filepaths:
                unique_filepaths.add(normalized_path)
                sources.append((filename, filepath))
                logger.debug(f"ソースリストに追加: {filename}, {filepath}")
            else:
                logger.debug(f"重複のためスキップ: {filename}, {filepath}")
        
        logger.info(f"検索結果: {len(search_results)}件, 重複排除後のソース数: {len(sources)}件")
        return search_results, sources

    def generate_answer(self, search_results: List[Dict[str, Any]], sources: List[Tuple[str, str]], user_query: str) -> str:
        """
        検索結果を使用して回答を生成します
        
        Args:
            search_results (List[Dict[str, Any]]): 検索結果
            sources (List[Tuple[str, str]]): ソースリスト
            user_query (str): ユーザーからの質問
            
        Returns:
            str: 生成された回答
        """
        logger.info("回答の生成を開始します")
        
        try:
            # 検索結果からコンテキストを作成
            context_items = []
            for i, result in enumerate(search_results):
                # チャンク番号、テキスト、ファイル名を含める
                context_items.append(f"チャンク {i+1} (ファイル: {result.get('filename', '不明')}):\n{result['text']}")
            
            context = "\n\n".join(context_items)
            
            # ソースリストの文字列を作成
            sources_str = "\n".join([f"- {filename} ({filepath})" for filename, filepath in sources])
            
            # 回答生成のためのプロンプトテンプレート
            answer_prompt = PromptTemplate(
                input_variables=["query", "context", "sources"],
                template="""
                あなたはRAGシステムの一部として、検索結果を基に質問に回答する役割を担っています。
                
                ユーザーの質問: {query}
                
                以下の検索結果を使用して、質問に対する回答を生成してください。
                検索結果に含まれる情報のみを使用し、含まれていない情報については「情報がありません」と正直に答えてください。
                
                検索結果:
                {context}
                
                回答は以下の形式で提供してください:
                1. 質問に対する直接的な回答
                2. 回答の詳細な説明
                3. 参照したソース: 各チャンクの内容を簡潔に要約し、どのファイルから取得したかを明記してください
                
                回答:
                """
            )
            
            # LLMChainの作成と実行
            answer_chain = LLMChain(llm=self.llm, prompt=answer_prompt)
            answer = answer_chain.invoke({
                "query": user_query,
                "context": context,
                "sources": sources_str
            })["text"].strip()
            
            logger.info("回答の生成が完了しました")
            return answer
        except Exception as e:
            logger.error(f"回答生成中にエラーが発生しました: {e}", exc_info=True)
            # エラーが発生した場合は検索結果のみを返す
            summary = "\n\n".join([f"検索結果 {i+1}:\n{result['text'][:300]}..." for i, result in enumerate(search_results)])
            return f"LLMによる回答生成中にエラーが発生しました: {str(e)}\n\n検索結果の要約:\n{summary}"

    def run_search_flow(self, user_query: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        検索フロー全体を実行します
        
        Args:
            user_query (str): ユーザーからの質問
            
        Returns:
            Tuple[str, List[Tuple[str, str]]]: 生成された回答とソースリスト
        """
        logger.info(f"検索フローを開始します。ユーザークエリ: {user_query}")
        
        try:
            # 1. ユーザークエリの理解
            search_query = self.understand_query(user_query)
            
            # 2. 検索の実行
            search_results, sources = self.search_documents(search_query)
            
            # 検索結果がない場合
            if not search_results:
                logger.warning("検索結果が見つかりませんでした")
                return "検索結果が見つかりませんでした。別のクエリを試してください。", []
            
            # 3. 回答生成
            answer = self.generate_answer(search_results, sources, user_query)
            
            logger.info("検索フローが完了しました")
            return answer, sources
        
        except Exception as e:
            logger.error(f"検索フロー中にエラーが発生しました: {e}", exc_info=True)
            return f"エラーが発生しました: {str(e)}", []

    def search(self, query: str, top_k: int = None, similarity_threshold: float = None) -> str:
        """
        ユーザークエリに対して検索を実行し、Markdown形式の結果を返します
        
        Args:
            query (str): ユーザークエリ
            top_k (int, optional): 検索結果の上位件数。指定しない場合はインスタンス作成時の値を使用
            similarity_threshold (float, optional): 検索の類似度閾値。指定しない場合はインスタンス作成時の値を使用
            
        Returns:
            str: Markdown形式の検索結果
        """
        # パラメータの更新（一時的）
        original_top_k = self.top_k
        original_threshold = self.similarity_threshold
        
        if top_k is not None:
            self.top_k = top_k
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
        
        try:
            # 検索フローの実行
            answer, sources = self.run_search_flow(query)
            
            # Markdown形式の結果を作成
            md_result = f"# 検索結果: {query}\n\n"
            md_result += f"## 回答\n\n{answer}\n\n"
            
            # 参照ソースの追加
            if sources:
                md_result += "## 参照ソース\n\n"
                for i, (filename, filepath) in enumerate(sources):
                    md_result += f"{i+1}. **{filename}** - `{filepath}`\n"
            
            # 検索パラメータの追加
            md_result += f"\n## 検索パラメータ\n\n"
            md_result += f"- 検索件数: {self.top_k}\n"
            md_result += f"- 類似度閾値: {self.similarity_threshold}\n"
            md_result += f"- LLMモデル: {self.llm_model}\n"
            md_result += f"- 埋め込みモデル: {self.embedding_model}\n"
            
            return md_result
        
        finally:
            # 元のパラメータに戻す
            self.top_k = original_top_k
            self.similarity_threshold = original_threshold


def search(query: str, top_k: int = 20, similarity_threshold: float = 0.7) -> str:
    """
    ユーザークエリに対して検索を実行し、Markdown形式の結果を返す便利関数
    
    Args:
        query (str): ユーザークエリ
        top_k (int): 検索結果の上位件数
        similarity_threshold (float): 検索の類似度閾値
        
    Returns:
        str: Markdown形式の検索結果
    """
    try:
        # 環境変数から設定を読み込み
        llm_model = os.getenv('OLLAMA_MODEL', 'gemma3:12b')
        embedding_model = os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large')
        temperature = float(os.getenv('LLM_TEMPERATURE', '0.1'))
        
        # RAGSearcherの初期化
        searcher = RAGSearcher(
            llm_model=llm_model,
            embedding_model=embedding_model,
            temperature=temperature,
            similarity_threshold=similarity_threshold,
            top_k=top_k
        )
        
        # 検索の実行
        return searcher.search(query, top_k, similarity_threshold)
    
    except Exception as e:
        logger.error(f"検索中にエラーが発生しました: {e}", exc_info=True)
        return f"# エラー\n\n検索中にエラーが発生しました: {str(e)}"


def main():
    """
    コマンドラインからの実行用メイン関数
    """
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='RAG検索')
    parser.add_argument('query', type=str, help='検索クエリ')
    parser.add_argument('--top-k', type=int, default=20,
                        help='検索結果の上位件数 (デフォルト: 20)')
    parser.add_argument('--similarity-threshold', type=float, default=0.7,
                        help='検索の類似度閾値 (デフォルト: 0.7)')
    parser.add_argument('--llm-model', type=str, default=os.getenv('OLLAMA_MODEL', 'gemma3:12b'),
                        help='LLMモデル名 (デフォルト: 環境変数またはgemma3:12b)')
    parser.add_argument('--embedding-model', type=str, 
                        default=os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large'),
                        help='埋め込みモデル名 (デフォルト: 環境変数またはintfloat/multilingual-e5-large)')
    parser.add_argument('--temperature', type=float, default=float(os.getenv('LLM_TEMPERATURE', '0.1')),
                        help='LLMの温度パラメータ (デフォルト: 環境変数または0.1)')
    parser.add_argument('--output', type=str, help='結果を保存するファイルパス (指定しない場合は標準出力)')
    
    args = parser.parse_args()
    
    try:
        # RAGSearcherの初期化
        searcher = RAGSearcher(
            llm_model=args.llm_model,
            embedding_model=args.embedding_model,
            temperature=args.temperature,
            similarity_threshold=args.similarity_threshold,
            top_k=args.top_k
        )
        
        # 検索の実行
        result = searcher.search(args.query)
        
        # 結果の出力
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"検索結果を {args.output} に保存しました。")
        else:
            print(result)
    
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
