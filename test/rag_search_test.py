#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGシステムの検索フローをテストするモジュール

このモジュールは、NakedRAGプロジェクトのRAGシステムを使用して、
文書検索からLLMを用いた回答生成までの一連のフローをテストします。
参照ソースは一時ディレクトリにコピーされ、直接開けるようになっています。
"""

import os
import sys
import argparse
import shutil
import webbrowser
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from src.rag_class import RAGSystem
from src.embedding_generator import EmbeddingGenerator
from src.web_server import RAGWebServer
from src.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class RAGSearchTest:
    """
    RAGシステムの検索フローをテストするクラス
    
    このクラスは以下の機能を提供します：
    1. ユーザークエリの理解と検索クエリへの変換
    2. 検索クエリを使用したRAGデータベースの検索
    3. 検索結果を使用した回答の生成
    """
    
    def __init__(self, 
                 llm_model: str = "gemma3:12b",
                 embedding_model: str = "intfloat/multilingual-e5-large",
                 temperature: float = 0.1,
                 similarity_threshold: float = 0.7,
                 top_k: int = 10):
        """
        RAG検索テストの初期化
        
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
        
        # 埋め込みジェネレーターの初期化
        self.embedding_generator = EmbeddingGenerator(model_name=embedding_model)
        
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
            response = requests.get(f"{base_url}/api/version")
            if response.status_code == 200:
                logger.info(f"Ollamaサーバー接続成功: {response.json()}")
            else:
                logger.warning("Ollamaサーバーは起動していますが、応答が不正です")
        except Exception as e:
            logger.error(f"Ollamaの初期化中にエラーが発生しました: {e}")
            raise Exception("Ollamaサーバーに接続できません。サーバーが起動しているか確認してください。")
        
        logger.info(f"RAG検索テストを初期化しました。LLMモデル: {llm_model}, 埋め込みモデル: {embedding_model}")
    
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
            
            logger.info(f"検索を実行します: {search_query}")
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


def main():
    """
    メイン関数
    """
    # .envファイルからデフォルト値を読み込む
    default_embedding_model = os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large')
    default_temp_dir = os.getenv('TEMP_DIR', './temp')
    default_web_data_dir = os.getenv('WEB_DATA_DIR', './web_data')
    default_web_server_host = os.getenv('WEB_SERVER_HOST', '127.0.0.1')
    default_web_server_port = int(os.getenv('WEB_SERVER_PORT', '5000'))
    default_web_server_enabled = os.getenv('WEB_SERVER_ENABLED', 'false').lower() == 'true'
    
    parser = argparse.ArgumentParser(description='RAG検索テスト')
    parser.add_argument('--query', type=str, required=True,
                        help='検索クエリ')
    parser.add_argument('--llm-model', type=str, default=os.getenv('OLLAMA_MODEL', 'gemma3:12b'),
                        help='LLMモデル名 (デフォルト: 環境変数またはgemma3:12b)')
    parser.add_argument('--embedding-model', type=str, default=default_embedding_model,
                        help=f'埋め込みモデル名 (デフォルト: {default_embedding_model})')
    parser.add_argument('--temperature', type=float, default=float(os.getenv('LLM_TEMPERATURE', '0.1')),
                        help='LLMの温度パラメータ (デフォルト: 環境変数または0.1)')
    parser.add_argument('--similarity-threshold', type=float, default=0.7,
                        help='検索の類似度閾値 (デフォルト: 0.7)')
    parser.add_argument('--top-k', type=int, default=10,
                        help='検索結果の上位件数 (デフォルト: 10)')
    parser.add_argument('--skip-llm', action='store_true',
                        help='LLMの処理をスキップし、検索結果のみを表示する')
    parser.add_argument('--temp-dir', type=str, default=default_temp_dir,
                        help=f'参照ソースのコピーを保存する一時ディレクトリ (デフォルト: {default_temp_dir})')
    parser.add_argument('--no-copy', action='store_true',
                        help='参照ソースのコピーを作成しない')
    
    # Webサーバー関連の引数
    parser.add_argument('--web', action='store_true', default=default_web_server_enabled,
                        help=f'Webサーバーと連携して検索結果を保存する (デフォルト: {default_web_server_enabled})')
    parser.add_argument('--web-data-dir', type=str, default=default_web_data_dir,
                        help=f'Webサーバーのデータディレクトリ (デフォルト: {default_web_data_dir})')
    parser.add_argument('--web-host', type=str, default=default_web_server_host,
                        help=f'Webサーバーのホスト (デフォルト: {default_web_server_host})')
    parser.add_argument('--web-port', type=int, default=default_web_server_port,
                        help=f'Webサーバーのポート番号 (デフォルト: {default_web_server_port})')
    parser.add_argument('--start-web-server', action='store_true',
                        help='Webサーバーを起動する')
    
    args = parser.parse_args()
    
    try:
        # Ollamaサーバーが起動しているか確認
        if not args.skip_llm:
            try:
                import requests
                # 環境変数からOllama設定を取得
                ollama_base_url = os.getenv('OLLAMA_BASE_URL')
                ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
                ollama_port = os.getenv('OLLAMA_PORT', '11434')
                
                # base_urlが設定されている場合はそれを使用、そうでなければhost/portから構築
                if ollama_base_url:
                    base_url = ollama_base_url
                else:
                    base_url = f"http://{ollama_host}:{ollama_port}"
                
                response = requests.get(f"{base_url}/api/version")
                if response.status_code != 200:
                    logger.warning("Ollamaサーバーに接続できません。--skip-llmオプションを使用します。")
                    args.skip_llm = True
            except Exception as e:
                logger.warning(f"Ollamaサーバー接続チェック中にエラー: {e}")
                logger.warning("--skip-llmオプションを使用します。")
                args.skip_llm = True
        
        # 一時ディレクトリの作成
        temp_dir = Path(args.temp_dir)
        if not args.no_copy:
            temp_dir.mkdir(parents=True, exist_ok=True)
            # 前回のファイルを削除
            for file in temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
        
        # RAG検索テストの初期化
        rag_search_test = RAGSearchTest(
            llm_model=args.llm_model,
            embedding_model=args.embedding_model,
            temperature=args.temperature,
            similarity_threshold=args.similarity_threshold,
            top_k=args.top_k
        )
        
        # 検索フローの実行
        if args.skip_llm:
            # LLMをスキップして直接検索を実行
            search_results, sources = rag_search_test.search_documents(args.query)
            if not search_results:
                answer = "検索結果が見つかりませんでした。別のクエリを試してください。"
            else:
                # 検索結果の要約を作成
                summary = "\n\n".join([f"検索結果 {i+1}:\n{result['text'][:300]}..." for i, result in enumerate(search_results)])
                answer = f"LLMをスキップしました。検索結果の要約:\n{summary}"
        else:
            # 通常の検索フローを実行
            answer, sources = rag_search_test.run_search_flow(args.query)
        
        # 参照ソースのコピーを作成
        source_copies = []
        if not args.no_copy and sources:
            for i, (filename, filepath) in enumerate(sources):
                # コピー先のパスを生成
                copy_path = temp_dir / f"{i+1}_{filename}"
                
                # ファイルをコピー
                try:
                    # 詳細なデバッグログ
                    logger.debug(f"処理するファイル: {filename}, パス: {filepath}")
                    
                    # original_filepathかどうかを判断
                    is_original = 'data/source' in filepath.replace('\\', '/') or '\\data\\source' in filepath
                    logger.debug(f"元のソースファイルパスか: {is_original}")
                    
                    # ファイルパスを正規化（OSに合わせてパス区切り文字を統一）
                    normalized_path = os.path.normpath(filepath)
                    logger.debug(f"正規化されたパス: {normalized_path}")
                    
                    # 最初に元のパスでの存在確認
                    file_exists = os.path.exists(normalized_path)
                    logger.debug(f"元のパスでファイルが存在するか: {file_exists}")
                    
                    # 絶対パスで見つからない場合、プロジェクトルートからの相対パスを試す
                    if not file_exists:
                        project_root = Path(__file__).parent.parent.absolute()
                        alternative_path = os.path.join(project_root, normalized_path.lstrip('\/')) 
                        file_exists = os.path.exists(alternative_path)
                        if file_exists:
                            normalized_path = alternative_path
                            logger.info(f"代替パスでファイルを見つけました: {normalized_path}")
                    
                    # data/markdownsのファイルの場合、対応するdata/sourceファイルを優先的に探す
                    if 'data/markdowns' in normalized_path.replace('\\', '/') or '\\data\\markdowns' in normalized_path:
                        # パターン1: data/markdowns → data/source
                        source_path = normalized_path.replace('\\', '/').replace('data/markdowns', 'data/source')
                        source_path = os.path.normpath(source_path)
                        source_exists = os.path.exists(source_path)
                        logger.debug(f"パターン1変換: {source_path}, 存在: {source_exists}")
                        
                        if source_exists:
                            normalized_path = source_path
                            file_exists = True
                            logger.info(f"sourceディレクトリでファイルを見つけました(パターン1): {normalized_path}")
                        else:
                            # パターン2: data\markdowns\markdown → data\source\markdown
                            source_path = re.sub(r'data[/\\]markdowns([/\\]markdown)?', r'data\\source\\markdown', normalized_path)
                            source_exists = os.path.exists(source_path)
                            logger.debug(f"パターン2変換: {source_path}, 存在: {source_exists}")
                            
                            if source_exists:
                                normalized_path = source_path
                                file_exists = True
                                logger.info(f"sourceディレクトリでファイルを見つけました(パターン2): {normalized_path}")
                    
                    # 他のパターンでも見つからない場合は、ファイル名のみで検索
                    if not file_exists:
                        filename_only = os.path.basename(normalized_path)
                        source_dir = os.path.join(project_root, 'data', 'source', 'markdown')
                        source_path = os.path.join(source_dir, filename_only)
                        source_exists = os.path.exists(source_path)
                        logger.debug(f"ファイル名のみでの検索: {source_path}, 存在: {source_exists}")
                        
                        if source_exists:
                            normalized_path = source_path
                            file_exists = True
                            logger.info(f"sourceディレクトリでファイル名のみで見つけました: {normalized_path}")
                        
                    # 最終的なファイルの存在確認と処理
                    if file_exists:
                        # ファイルをコピー
                        shutil.copy2(normalized_path, copy_path)
                        source_copies.append((filename, str(copy_path.absolute())))
                        logger.info(f"ファイルをコピーしました: {normalized_path} -> {copy_path}")
                        
                        # 元のソースファイルかMarkdownファイルかをログに記録
                        if 'data/source' in normalized_path.replace('\\', '/') or '\\data\\source' in normalized_path:
                            logger.info(f"元のソースファイルを使用しました: {normalized_path}")
                        else:
                            logger.info(f"Markdownファイルを使用しました: {normalized_path}")
                    else:
                        # 詳細なログ出力
                        logger.warning(f"ファイルが見つかりません: {filepath}")
                        logger.warning(f"正規化されたパス: {normalized_path}")
                        logger.warning(f"カレントディレクトリ: {os.getcwd()}")
                        logger.warning(f"試行したすべてのパターンで見つかりませんでした。")
                        
                        # 元ファイルが存在しない場合はダミーファイルを作成
                        with open(copy_path, 'w', encoding='utf-8') as f:
                            f.write(f"# {filename}\n\n元ファイルが見つかりませんでした: {filepath}")
                        source_copies.append((filename, str(copy_path.absolute())))
                        logger.warning(f"元ファイルが見つからないため、ダミーファイルを作成しました: {filepath} -> {copy_path}")
                except Exception as e:
                    logger.error(f"ファイルのコピー中にエラーが発生しました: {e}", exc_info=True)
                    source_copies.append((filename, filepath))
        else:
            source_copies = sources
        
        # Webサーバーと連携する場合
        web_result_url = None
        if args.web:
            try:
                # Webサーバーの初期化
                web_server = RAGWebServer(
                    data_dir=args.web_data_dir,
                    host=args.web_host,
                    port=args.web_port
                )
                
                # 検索結果を保存
                result_id = web_server.save_search_result(args.query, answer, sources)
                web_result_url = f"http://{args.web_host}:{args.web_port}/result/{result_id}"
                
                # Webサーバーを起動する場合
                if args.start_web_server:
                    print(f"\nWebサーバーを起動しています...")
                    print(f"ブラウザで検索結果を開くには、以下のURLを使用してください:")
                    print(f"  {web_result_url}")
                    
                    # ブラウザで検索結果を開く
                    webbrowser.open(web_result_url)
                    
                    # Webサーバーを起動
                    web_server.start()
                    return  # Webサーバーが終了したらプログラムも終了
            except Exception as e:
                logger.error(f"Webサーバーとの連携中にエラーが発生しました: {e}")
        
        # 結果の表示
        print("\n" + "="*80)
        print("検索結果:")
        print("="*80)
        print(answer)
        
        print("\n" + "="*80)
        print("参照ソース:")
        print("="*80)
        for filename, filepath in source_copies:
            print(f"- {filename} ({filepath})")
        
        if not args.no_copy and source_copies:
            print("\n参照ソースは一時ディレクトリにコピーされました。ファイルを直接開いて内容を確認できます。")
            print(f"一時ディレクトリ: {temp_dir.absolute()}")
        elif args.no_copy:
            print("\n参照ソースのコピーは作成されませんでした。--no-copyオプションが指定されています。")
        
        # Webサーバーと連携している場合は、URLを表示
        if args.web and web_result_url and not args.start_web_server:
            print("\nWebサーバーに検索結果が保存されました。")
            print(f"Webサーバーが起動していれば、以下のURLでアクセスできます:")
            print(f"  {web_result_url}")
            print("Webサーバーを起動するには、以下のコマンドを実行してください:")
            print(f"  python src/web_server.py --data-dir {args.web_data_dir} --host {args.web_host} --port {args.web_port}")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
