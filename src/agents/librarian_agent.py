#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
司書LLMエージェントモジュール

LangChainを使用した司書LLMエージェントを提供します。
ユーザーの質問を理解し、RAGシステムを使用して適切な回答を生成します。
"""

import os
import sys
import logging
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
from langchain.tools import Tool

from src.config.config_manager import ConfigManager
from src.rag.rag_class import RAGSystem
from src.rag.rag_searcher import RAGSearcher
from src.agents.rag_database_info import RAGDatabaseInfo
from src.agents.prompt_manager import PromptManager
from src.agents.rag_database_info import get_database_info
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

# 環境変数の読み込み
load_dotenv()


class LibrarianAgent:
    """
    司書LLMエージェントクラス
    
    ユーザーの質問を理解し、RAGシステムを使用して適切な回答を生成するエージェントです。
    """
    
    def __init__(self, 
                 agent_type: str = "librarian",
                 llm_model: Optional[str] = None,
                 temperature: Optional[float] = None,
                 config_path: Optional[str] = None):
        """
        司書LLMエージェントの初期化
        
        Args:
            agent_type: エージェントの種類（デフォルト: "librarian"）
            llm_model: 使用するLLMモデル（指定がない場合は設定ファイルから読み込み）
            temperature: 生成時の温度パラメータ（指定がない場合は設定ファイルから読み込み）
            config_path: 設定ファイルのパス（デフォルト: "agent_settings.json"）
        """
        # 設定マネージャーの初期化
        self.config_manager = ConfigManager(config_path or "agent_settings.json")
        
        # エージェントタイプの設定
        self.agent_type = agent_type
        
        # エージェント設定の取得
        self.agent_config = self.config_manager.get_agent_config(agent_type)
        if not self.agent_config:
            logger.warning(f"エージェント'{agent_type}'の設定が見つかりません。デフォルト設定を使用します。")
            self.agent_config = {}
        
        # RAG設定の取得
        self.rag_config = self.config_manager.get_rag_config()
        
        # モデル設定の取得（優先順位: 引数 > 設定ファイル > 環境変数 > デフォルト値）
        self.llm_model = llm_model or self.agent_config.get("model") or os.getenv('OLLAMA_MODEL', 'gemma3:12b')
        self.temperature = float(temperature or self.agent_config.get("temperature") or os.getenv('LLM_TEMPERATURE', '0.1'))
        
        # プロンプトマネージャーの取得
        self.prompt_manager = PromptManager(agent_type)
        
        # Ollamaモデルの初期化
        self.llm = ChatOllama(model=self.llm_model, temperature=self.temperature)
        
        # データベース情報の取得
        self.database_info = get_database_info()
        
        # 類似度閾値の設定
        self.similarity_threshold = float(self.rag_config.get("similarity_threshold", 0.8))
        self.max_results = int(self.rag_config.get("max_results", 5))
        
        # RAGSearcherの初期化 - より高度な検索機能を提供
        self.rag_searcher = RAGSearcher(
            llm_model=self.llm_model,
            temperature=self.temperature,
            similarity_threshold=self.similarity_threshold,
            top_k=self.max_results
        )
        
        # 下位互換性のためにrag_systemも保持
        self.rag_system = self.rag_searcher.rag_system
        
        # ツールの設定
        self.tools = self._setup_tools()
        
        # Webサーバーのベースパス（元ソースファイル提供用）
        self.web_base_url = os.getenv('WEB_SERVER_URL', 'http://localhost:8000')
        
        logger.info(f"司書LLMエージェント（{self.agent_type}）を初期化しました: model={self.llm_model}, temperature={self.temperature}")
    
    def _setup_tools(self):
        """
        LangChainエージェントのツールを設定します
        """
        return [
            Tool(
                name="rag_search",
                func=self._rag_search_tool,
                description="RAGシステムを使用してクエリに関連する情報を検索します。ユーザーの質問に関連する情報が必要な場合に使用します。",
                return_direct=False
            )
        ]
    
    def _generate_source_links(self, results: List[Dict[str, Any]]) -> str:
        """
        検索結果から元ソースファイルへのリンクを生成します
        
        Args:
            results: RAG検索結果のリスト
            
        Returns:
            元ソースファイルへのリンクを含むMarkdown形式の文字列
        """
        try:
            # ユニークなソースファイルを抽出
            unique_sources = {}
            for result in results:
                source = result['metadata']['source']
                if source not in unique_sources:
                    # ソースファイル名からWebサーバーのURLを生成
                    file_path = source
                    # URLエンコードされたパスを生成
                    encoded_path = file_path.replace('/', '%2F').replace(' ', '%20')
                    url = f"{self.web_base_url}/sources/{encoded_path}"
                    unique_sources[source] = url
            
            # Markdown形式のリンクリストを生成
            if not unique_sources:
                return "参考資料はありません。"
                
            links = [f"- [{source}]({url})" for source, url in unique_sources.items()]
            return "\n".join(links)
            
        except Exception as e:
            logger.error(f"ソースリンク生成中にエラーが発生しました: {e}", exc_info=True)
            return "参考資料のリンクを生成できませんでした。"
    
    def _generate_source_url(self, filepath: str) -> str:
        """
        ソースファイルのパスからURLを生成します
        
        Args:
            filepath: ソースファイルのパス
            
        Returns:
            生成されたURL
        """
        # 環境変数からWEBサーバーのURLを取得
        web_server_url = os.environ.get("WEB_SERVER_URL", "http://localhost:8000")
        
        # ファイルパスを相対パスに変換
        if filepath.startswith("./"):
            relative_path = filepath
        else:
            # 絶対パスの場合は、プロジェクトルートからの相対パスに変換
            relative_path = os.path.relpath(filepath, ".")
        
        # URLエンコード（バックスラッシュをスラッシュに変換）
        encoded_path = relative_path.replace("\\", "/")
        
        # URLを生成
        source_url = f"{web_server_url}/api/source?path={encoded_path}"
        
        return source_url
    
    def _rag_search_tool(self, query: str, top_k: int = None, similarity_threshold: float = None) -> str:
        """
        RAG検索ツール関数
        
        Args:
            query: 検索クエリ
            top_k: 検索結果の上位件数
            similarity_threshold: 検索の類似度閾値
            
        Returns:
            検索結果（Markdown形式）
        """
        try:
            # デフォルト値の設定
            if top_k is None:
                top_k = self.max_results
            if similarity_threshold is None:
                similarity_threshold = self.similarity_threshold
            
            # 検索クエリの最適化
            optimized_query = self._optimize_search_query(query)
            
            # RAGSearcherを使用して検索を実行
            # searchメソッドはMarkdown形式の結果を直接返す
            result_markdown = self.rag_searcher.search(
                query=optimized_query, 
                top_k=top_k, 
                similarity_threshold=similarity_threshold
            )
            
            # RAGSearcher.searchの結果はすでにMarkdown形式なので、そのまま返す
            return result_markdown
        
        except Exception as e:
            logger.error(f"RAG検索中にエラーが発生しました: {e}", exc_info=True)
            return f"検索中にエラーが発生しました: {str(e)}"
    
    def _optimize_search_query(self, query: str) -> str:
        """
        検索クエリを最適化します
        
        Args:
            query: 元の検索クエリ
            
        Returns:
            最適化された検索クエリ
        """
        # 単純な実装では元のクエリをそのまま返す
        # 将来的には、LLMを使ってクエリを最適化することも可能
        return query
    
    def _get_document_count_tool(self) -> str:
        """
        RAGデータベース内のドキュメント数を取得するツール関数
        
        Returns:
            ドキュメント数の情報（Markdown形式）
        """
        try:
            # ドキュメント数の取得
            count = self.rag_system.get_document_count()
            
            return f"# ドキュメント情報\n\nRAGデータベース内のドキュメント数: {count}"
        except Exception as e:
            logger.error(f"ドキュメント数取得中にエラーが発生しました: {e}", exc_info=True)
            return f"# エラー\n\nドキュメント数取得中にエラーが発生しました: {str(e)}"
    
    def _get_unique_sources_tool(self) -> str:
        """
        RAGデータベース内のユニークなソースを取得するツール関数
        
        Returns:
            ユニークなソースのリスト（Markdown形式）
        """
        try:
            # ユニークなソースの取得
            sources = self.rag_system.get_unique_sources()
            
            # 結果のフォーマット
            sources_text = "# RAGデータベース内のソース一覧\n\n"
            for i, (filename, filepath) in enumerate(sources, 1):
                sources_text += f"{i}. **{filename}** - `{filepath}`\n"
            
            return sources_text
        except Exception as e:
            logger.error(f"ソース一覧取得中にエラーが発生しました: {e}", exc_info=True)
            return f"# エラー\n\nソース一覧取得中にエラーが発生しました: {str(e)}"
    
    def _is_query_in_scope(self, query: str) -> tuple:
        """
        LLMを使用してクエリが知識ベースの範囲内かどうかを判断します
        
        Args:
            query: ユーザークエリ
            
        Returns:
            (範囲内かどうかのブール値, ヒントや提案)
        """
        try:
            # データベース情報を取得
            db_info = self.database_info.get_database_introduction()
            
            # LLMを使って判断
            prompt = f"""以下の知識ベース情報とユーザーの質問を比較し、質問が知識ベースの範囲内かどうかを判断してください。

知識ベース情報:
{db_info}

ユーザーの質問:
{query}

判断結果を「True」または「False」で答え、その理由を簡潔に説明してください。また、質問が範囲外の場合は、知識ベースの範囲内で回答可能な関連質問の例を提案してください。回答は以下の形式でお願いします。

判断: [True/False]
理由: [理由の説明]
提案: [範囲外の場合のみ、関連質問の例を提案]"""
            
            # LLMに問い合わせ
            response = self.llm.invoke(prompt).content
            
            # 結果の解析
            is_in_scope = "True" in response.split("\n")[0]
            
            # 理由と提案を抽出
            reason = ""
            suggestion = ""
            
            for line in response.split("\n"):
                if line.startswith("理由:"):
                    reason = line.replace("理由:", "").strip()
                elif line.startswith("提案:"):
                    suggestion = line.replace("提案:", "").strip()
            
            return (is_in_scope, {"reason": reason, "suggestion": suggestion})
            
        except Exception as e:
            logger.error(f"LLMを使った範囲判断中にエラーが発生しました: {e}", exc_info=True)
            # エラー時はデフォルトで範囲内と判断
            return (True, {"reason": "エラーのためデフォルト判断", "suggestion": ""})
    
    def _parse_rag_search_result(self, result: str) -> dict:
        """
        RAG検索結果を解析し、回答と参照ソースを分離します
        
        Args:
            result: RAG検索結果（Markdown形式）
            
        Returns:
            解析結果を含む辞書
        """
        # 結果をそのまま返すシンプルな実装
        return {
            "raw_result": result,
            "answer": result,
            "sources": []
        }
    
    def process_query(self, query: str) -> str:
        """
        ユーザーからのクエリを処理し、適切な回答を生成します
        
        Args:
            query: ユーザーからのクエリ文字列
            
        Returns:
            生成された回答
        """
        try:
            logger.info(f"クエリを処理します: {query}")
            logger.info(f"使用するLLMモデル: {self.llm_model}")
            
            # LLMを使ってクエリが知識ベースの範囲内かどうかを判断
            is_in_scope, scope_info = self._is_query_in_scope(query)
            
            if not is_in_scope:
                # 範囲外の場合は、その旨を伝え、有益なヒントを提供
                scope_description = self.database_info.config["scope_description"]
                
                # ヒントを含むカスタムメッセージを作成
                out_of_scope_message = f"""申し訳ありませんが、あなたの質問「{query}」は私の知識ベースの範囲外のようです。

    理由: {scope_info["reason"]}

    私は主に{scope_description}に関する質問に答えることができます。"""
                
                # 提案があれば追加
                if scope_info["suggestion"]:
                    out_of_scope_message += f"""

    代わりに、次のような質問はお答えできます:
    {scope_info["suggestion"]}

    このような知識ベースの範囲内の質問をしていただけますか？"""
                
                return out_of_scope_message
            
            # 情報が不十分な場合の処理
            if scope_info.get("suggestion") and "情報が不十分" in scope_info.get("reason", ""):
                insufficient_info_message = f"""あなたの質問「{query}」について回答するには、もう少し情報が必要です。

    {scope_info["reason"]}

    {scope_info["suggestion"]}

    もう少し具体的な質問をしていただけますか？"""
                return insufficient_info_message
            
            # 範囲内の場合は、RAG検索を実行
            logger.info(f"RAG検索を実行します: {query}")
        
            # 設定から検索パラメータを取得
            top_k = int(self.rag_config.get("max_results", 5))
            similarity_threshold = float(self.rag_config.get("similarity_threshold", 0.8))
        
            # RAGSearcherを使用して検索フローを実行
            # run_search_flowメソッドは検索と回答生成を行い、回答とソースリストを返す
            answer, sources = self.rag_searcher.run_search_flow(query)
        
            if not answer or answer.startswith("検索結果が見つかりません"):
                return f"申し訳ありませんが、質問「{query}」に関連する情報は見つかりませんでした。別の質問をお試しください。"
        
            # ソースリンクの生成
            source_links_md = ""
            if sources:
                source_links_md = "## 参考資料\n"
                for i, (filename, filepath) in enumerate(sources):
                    # ソースファイルへのリンクを生成
                    source_url = self._generate_source_url(filepath)
                    source_links_md += f"{i+1}. [{filename}]({source_url})\n"
            
            # 回答にソースリンクが含まれていない場合は追加
            if "## 参考資料" not in answer and source_links_md:
                if not answer.endswith("\n"):
                    answer += "\n\n"
                answer += source_links_md
            
            # 改行を追加して読みやすくする
            if not answer.endswith("\n"):
                answer += "\n\n"
            
            logger.info("クエリ処理が完了しました")
            return answer
        
        except Exception as e:
            logger.error(f"クエリ処理中にエラーが発生しました: {e}", exc_info=True)
            return f"エラーが発生しました: {str(e)}"
        
    def cleanup(self):
        """
        リソースのクリーンアップを行います
        """
        if hasattr(self, 'rag_system'):
            self.rag_system.cleanup()


if __name__ == "__main__":
    # 使用例
    librarian = LibrarianAgent()
    
    try:
        # テスト用のクエリ
        test_query = "人工知能の歴史について教えてください"
        print(f"\n質問: {test_query}")
        
        # クエリの処理
        response = librarian.process_query(test_query)
        print(f"\n回答:\n{response}")
    finally:
        # リソースのクリーンアップ
        librarian.cleanup()
