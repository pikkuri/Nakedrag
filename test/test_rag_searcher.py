#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAG Searcherモジュールのテスト用スクリプト

このスクリプトは、src/rag_searcher.pyの機能をテストするためのものです。
コマンドラインから簡単に使用でき、検索結果をファイルに保存することもできます。
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# dotenvをインポート
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 自作モジュールのインポート
from src.rag.rag_searcher import RAGSearcher, search
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)


def test_simple_search(query: str, output_dir: str = "./temp", save_file: bool = True) -> str:
    """
    シンプルな検索テスト関数
    
    Args:
        query (str): 検索クエリ
        output_dir (str): 出力ディレクトリ
        save_file (bool): 結果をファイルに保存するかどうか
        
    Returns:
        str: 検索結果（Markdown形式）
    """
    logger.info(f"シンプルな検索テストを実行します。クエリ: {query}")
    
    try:
        # 検索の実行
        result = search(query)
        
        # 結果の保存
        if save_file:
            # 出力ディレクトリの作成
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # タイムスタンプを含むファイル名の作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{query[:20].replace(' ', '_')}.md"
            if len(filename) > 50:  # ファイル名が長すぎる場合は切り詰める
                filename = filename[:46] + ".md"
            
            file_path = output_path / filename
            
            # ファイルに保存
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result)
            
            logger.info(f"検索結果を保存しました: {file_path}")
            print(f"\n検索結果を保存しました: {file_path}")
        
        return result
    
    except Exception as e:
        logger.error(f"検索中にエラーが発生しました: {e}", exc_info=True)
        return f"# エラー\n\n検索中にエラーが発生しました: {str(e)}"


def test_advanced_search(
    query: str,
    top_k: int = 10,
    similarity_threshold: float = 0.7,
    llm_model: str = None,
    embedding_model: str = None,
    temperature: float = None,
    output_dir: str = "./results",
    save_file: bool = True
) -> str:
    """
    詳細設定可能な検索テスト関数
    
    Args:
        query (str): 検索クエリ
        top_k (int): 検索結果の上位件数
        similarity_threshold (float): 検索の類似度閾値
        llm_model (str): LLMモデル名
        embedding_model (str): 埋め込みモデル名
        temperature (float): LLMの温度パラメータ
        output_dir (str): 出力ディレクトリ
        save_file (bool): 結果をファイルに保存するかどうか
        
    Returns:
        str: 検索結果（Markdown形式）
    """
    logger.info(f"詳細検索テストを実行します。クエリ: {query}")
    
    try:
        # 環境変数からデフォルト値を読み込み
        if llm_model is None:
            llm_model = os.getenv('LLM_MODEL', 'gemma3:12b')
        if embedding_model is None:
            embedding_model = os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large')
        if temperature is None:
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
        result = searcher.search(query)
        
        # 結果の保存
        if save_file:
            # 出力ディレクトリの作成
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # タイムスタンプを含むファイル名の作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{query[:20].replace(' ', '_')}_adv.md"
            if len(filename) > 50:  # ファイル名が長すぎる場合は切り詰める
                filename = filename[:46] + ".md"
            
            file_path = output_path / filename
            
            # ファイルに保存
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(result)
            
            logger.info(f"検索結果を保存しました: {file_path}")
            print(f"\n検索結果を保存しました: {file_path}")
        
        return result
    
    except Exception as e:
        logger.error(f"検索中にエラーが発生しました: {e}", exc_info=True)
        return f"# エラー\n\n検索中にエラーが発生しました: {str(e)}"


def test_search_flow(query: str, output_dir: str = "./temp", save_file: bool = True) -> None:
    """
    検索フローの詳細テスト関数
    
    Args:
        query (str): 検索クエリ
        output_dir (str): 出力ディレクトリ
        save_file (bool): 結果をファイルに保存するかどうか
    """
    logger.info(f"検索フローの詳細テストを実行します。クエリ: {query}")
    
    try:
        # RAGSearcherの初期化
        searcher = RAGSearcher()
        
        # 1. ユーザークエリの理解
        print("\n" + "="*80)
        print("1. ユーザークエリの理解")
        print("="*80)
        search_query = searcher.understand_query(query)
        print(f"元のクエリ: {query}")
        print(f"検索クエリ: {search_query}")
        
        # 2. 検索の実行
        print("\n" + "="*80)
        print("2. 検索の実行")
        print("="*80)
        search_results, sources = searcher.search_documents(search_query)
        print(f"検索結果: {len(search_results)}件")
        print(f"ソース: {len(sources)}件")
        
        # 検索結果の表示
        for i, result in enumerate(search_results[:3]):  # 最初の3件のみ表示
            print(f"\n検索結果 {i+1}:")
            print(f"ファイル名: {result.get('filename', '不明')}")
            print(f"類似度: {result.get('similarity', 0):.4f}")
            print(f"テキスト: {result.get('text', '')[:100]}...")
        
        if len(search_results) > 3:
            print(f"\n... 他 {len(search_results) - 3} 件の検索結果があります")
        
        # 3. 回答生成
        print("\n" + "="*80)
        print("3. 回答生成")
        print("="*80)
        answer = searcher.generate_answer(search_results, sources, query)
        print(answer)
        
        # 結果の保存
        if save_file and search_results:
            # 出力ディレクトリの作成
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # タイムスタンプを含むファイル名の作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{query[:20].replace(' ', '_')}_flow.md"
            if len(filename) > 50:  # ファイル名が長すぎる場合は切り詰める
                filename = filename[:46] + ".md"
            
            file_path = output_path / filename
            
            # Markdown形式の結果を作成
            md_result = f"# 検索フロー詳細: {query}\n\n"
            
            md_result += f"## 1. クエリ理解\n\n"
            md_result += f"元のクエリ: {query}\n\n"
            md_result += f"検索クエリ: {search_query}\n\n"
            
            md_result += f"## 2. 検索結果\n\n"
            md_result += f"検索結果: {len(search_results)}件\n\n"
            
            for i, result in enumerate(search_results):
                md_result += f"### 検索結果 {i+1}\n\n"
                md_result += f"- ファイル名: {result.get('filename', '不明')}\n"
                md_result += f"- パス: {result.get('filepath', '不明')}\n"
                md_result += f"- 元パス: {result.get('original_filepath', '不明')}\n"
                md_result += f"- 類似度: {result.get('similarity', 0):.4f}\n\n"
                md_result += f"```\n{result.get('text', '')}\n```\n\n"
            
            md_result += f"## 3. 回答\n\n{answer}\n\n"
            
            md_result += f"## 4. 参照ソース\n\n"
            for i, (filename, filepath) in enumerate(sources):
                md_result += f"{i+1}. **{filename}** - `{filepath}`\n"
            
            # ファイルに保存
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_result)
            
            logger.info(f"検索フロー詳細を保存しました: {file_path}")
            print(f"\n検索フロー詳細を保存しました: {file_path}")
    
    except Exception as e:
        logger.error(f"検索フロー中にエラーが発生しました: {e}", exc_info=True)
        print(f"エラーが発生しました: {str(e)}")


def main():
    """
    メイン関数
    """
    # .envファイルからデフォルト値を読み込む
    default_temp_dir = os.getenv('TEMP_DIR', './temp')
    
    parser = argparse.ArgumentParser(description='RAG Searcherテスト')
    parser.add_argument('--query', type=str, required=True,
                        help='検索クエリ')
    parser.add_argument('--mode', type=str, choices=['simple', 'advanced', 'flow'], default='simple',
                        help='テストモード (simple: シンプルな検索, advanced: 詳細設定可能な検索, flow: 検索フロー詳細)')
    parser.add_argument('--top-k', type=int, default=20,
                        help='検索結果の上位件数 (デフォルト: 20)')
    parser.add_argument('--similarity-threshold', type=float, default=0.7,
                        help='検索の類似度閾値 (デフォルト: 0.7)')
    parser.add_argument('--llm-model', type=str,
                        help='LLMモデル名 (デフォルト: 環境変数またはgemma3:12b)')
    parser.add_argument('--embedding-model', type=str,
                        help='埋め込みモデル名 (デフォルト: 環境変数またはintfloat/multilingual-e5-large)')
    parser.add_argument('--temperature', type=float,
                        help='LLMの温度パラメータ (デフォルト: 環境変数または0.1)')
    parser.add_argument('--temp-dir', type=str, default=default_temp_dir,
                        help=f'結果を保存する一時ディレクトリ (デフォルト: {default_temp_dir})')
    parser.add_argument('--no-save', action='store_true',
                        help='結果をファイルに保存しない')
    
    args = parser.parse_args()
    
    try:
        # テストモードに応じた関数を実行
        if args.mode == 'simple':
            result = test_simple_search(
                query=args.query,
                output_dir=args.temp_dir,
                save_file=not args.no_save
            )
            if not args.no_save:
                print("\n" + "="*80)
                print("検索結果:")
                print("="*80)
                print(result)
        
        elif args.mode == 'advanced':
            result = test_advanced_search(
                query=args.query,
                top_k=args.top_k,
                similarity_threshold=args.similarity_threshold,
                llm_model=args.llm_model,
                embedding_model=args.embedding_model,
                temperature=args.temperature,
                output_dir=args.temp_dir,
                save_file=not args.no_save
            )
            if not args.no_save:
                print("\n" + "="*80)
                print("検索結果:")
                print("="*80)
                print(result)
        
        elif args.mode == 'flow':
            test_search_flow(
                query=args.query,
                output_dir=args.temp_dir,
                save_file=not args.no_save
            )
    
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
