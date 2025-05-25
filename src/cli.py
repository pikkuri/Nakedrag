#!/usr/bin/env python
"""
MCP RAG Server CLI

インチE��クスのクリアとインチE��クス化を行うためのコマンドラインインターフェース
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

from .rag_tools import create_rag_service_from_env


def setup_logging():
    """
    ロギングの設宁E    """
    # ログチE��レクトリの作�E
    os.makedirs("logs", exist_ok=True)

    # ロギングの設宁E    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join("logs", "mcp_rag_cli.log"), encoding="utf-8"),
        ],
    )
    return logging.getLogger("cli")


def clear_index():
    """
    インチE��クスをクリアする
    """
    logger = setup_logging()
    logger.info("インチE��クスをクリアしてぁE��ぁE..")

    # 環墁E��数の読み込み
    load_dotenv()

    # RAGサービスの作�E
    rag_service = create_rag_service_from_env()

    # 処琁E��みチE��レクトリのパス
    processed_dir = os.environ.get("PROCESSED_DIR", "data/processed")

    # ファイルレジストリの削除
    registry_path = Path(processed_dir) / "file_registry.json"
    if registry_path.exists():
        try:
            registry_path.unlink()
            logger.info(f"ファイルレジストリを削除しました: {registry_path}")
            print(f"ファイルレジストリを削除しました: {registry_path}")
        except Exception as e:
            logger.error(f"ファイルレジストリの削除に失敗しました: {str(e)}")
            print(f"ファイルレジストリの削除に失敗しました: {str(e)}")

    # インチE��クスをクリア
    result = rag_service.clear_index()

    if result["success"]:
        logger.info(f"インチE��クスをクリアしました�E�Eresult['deleted_count']} ドキュメントを削除�E�E)
        print(f"インチE��クスをクリアしました�E�Eresult['deleted_count']} ドキュメントを削除�E�E)
    else:
        logger.error(f"インチE��クスのクリアに失敗しました: {result.get('error', '不�Eなエラー')}")
        print(f"インチE��クスのクリアに失敗しました: {result.get('error', '不�Eなエラー')}")
        sys.exit(1)


def index_documents(directory_path, chunk_size=500, chunk_overlap=100, incremental=False):
    """
    ドキュメントをインチE��クス化すめE
    Args:
        directory_path: インチE��クス化するドキュメントが含まれるチE��レクトリのパス
        chunk_size: チャンクサイズ�E�文字数�E�E        chunk_overlap: チャンク間�Eオーバ�EラチE�E�E�文字数�E�E        incremental: 差刁E�EみをインチE��クス化するかどぁE��
    """
    logger = setup_logging()
    if incremental:
        logger.info(f"チE��レクトリ '{directory_path}' 冁E�E差刁E��ァイルをインチE��クス化してぁE��ぁE..")
    else:
        logger.info(f"チE��レクトリ '{directory_path}' 冁E�EドキュメントをインチE��クス化してぁE��ぁE..")

    # 環墁E��数の読み込み
    load_dotenv()

    # チE��レクトリの存在確誁E    if not os.path.exists(directory_path):
        logger.error(f"チE��レクトリ '{directory_path}' が見つかりません")
        print(f"エラー: チE��レクトリ '{directory_path}' が見つかりません")
        sys.exit(1)

    if not os.path.isdir(directory_path):
        logger.error(f"'{directory_path}' はチE��レクトリではありません")
        print(f"エラー: '{directory_path}' はチE��レクトリではありません")
        sys.exit(1)

    # RAGサービスの作�E
    rag_service = create_rag_service_from_env()

    # 処琁E��みチE��レクトリのパス
    processed_dir = os.environ.get("PROCESSED_DIR", "data/processed")

    # インチE��クス化を実衁E    if incremental:
        print(f"チE��レクトリ '{directory_path}' 冁E�E差刁E��ァイルをインチE��クス化してぁE��ぁE..")
    else:
        print(f"チE��レクトリ '{directory_path}' 冁E�EドキュメントをインチE��クス化してぁE��ぁE..")

    # 進捗状況を表示するためのカウンタ
    processed_files = 0

    # 処琁E��にファイル数を取征E    total_files = 0
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file_path)[1].lower()
            if ext in [".md", ".markdown", ".txt", ".pdf", ".ppt", ".pptx", ".doc", ".docx"]:
                total_files += 1

    print(f"合訁E{total_files} 個�Eファイルを検索しました...")

    # 允E�ERAGServiceのindex_documentsメソチE��を呼び出す前に、E    # DocumentProcessorのprocess_directoryメソチE��をオーバ�Eライドして進捗を表示
    original_process_directory = rag_service.document_processor.process_directory

    def process_directory_with_progress(source_dir, processed_dir, chunk_size=500, overlap=100, incremental=False):
        nonlocal processed_files
        results = []
        source_directory = Path(source_dir)

        if not source_directory.exists() or not source_directory.is_dir():
            logger.error(f"チE��レクトリ '{source_dir}' が見つからなぁE��、ディレクトリではありません")
            raise FileNotFoundError(f"チE��レクトリ '{source_dir}' が見つからなぁE��、ディレクトリではありません")

        # サポ�Eトするファイル拡張子を全て取征E        all_extensions = []
        for ext_list in rag_service.document_processor.SUPPORTED_EXTENSIONS.values():
            all_extensions.extend(ext_list)

        # ファイルを検索
        files = []
        for ext in all_extensions:
            files.extend(list(source_directory.glob(f"**/*{ext}")))

        logger.info(f"チE��レクトリ '{source_dir}' 冁E�� {len(files)} 個�Eファイルが見つかりました")

        # 差刁E�E琁E�E場合、ファイルレジストリを読み込む
        if incremental:
            file_registry = rag_service.document_processor.load_file_registry(processed_dir)
            logger.info(f"ファイルレジストリから {len(file_registry)} 個�Eファイル惁E��を読み込みました")

            # 処琁E��象のファイルを特宁E            files_to_process = []
            for file_path in files:
                str_path = str(file_path)
                # ファイルのメタチE�Eタを取征E                current_metadata = rag_service.document_processor.get_file_metadata(str_path)

                # レジストリに存在しなぁE��また�Eハッシュ値が変更されてぁE��場合�Eみ処琁E                if (
                    str_path not in file_registry
                    or file_registry[str_path]["hash"] != current_metadata["hash"]
                    or file_registry[str_path]["mtime"] != current_metadata["mtime"]
                    or file_registry[str_path]["size"] != current_metadata["size"]
                ):
                    files_to_process.append(file_path)
                    # レジストリを更新
                    file_registry[str_path] = current_metadata

            print(f"処琁E��象のファイル数: {len(files_to_process)} / {len(files)}")

            # 吁E��ァイルを�E琁E            for i, file_path in enumerate(files_to_process):
                try:
                    file_results = rag_service.document_processor.process_file(
                        str(file_path), processed_dir, chunk_size, overlap
                    )
                    results.extend(file_results)
                    processed_files += 1
                    print(
                        f"処琁E��... {processed_files}/{len(files_to_process)} ファイル ({(processed_files / len(files_to_process) * 100):.1f}%): {file_path}"
                    )
                except Exception as e:
                    logger.error(f"ファイル '{file_path}' の処琁E��にエラーが発生しました: {str(e)}")
                    # エラーが発生しても�E琁E��続衁E                    continue

            # ファイルレジストリを保孁E            rag_service.document_processor.save_file_registry(processed_dir, file_registry)
        else:
            # 差刁E�E琁E��なぁE��合�E全てのファイルを�E琁E            for i, file_path in enumerate(files):
                try:
                    file_results = rag_service.document_processor.process_file(
                        str(file_path), processed_dir, chunk_size, overlap
                    )
                    results.extend(file_results)
                    processed_files += 1
                    print(
                        f"処琁E��... {processed_files}/{total_files} ファイル ({(processed_files / total_files * 100):.1f}%): {file_path}"
                    )
                except Exception as e:
                    logger.error(f"ファイル '{file_path}' の処琁E��にエラーが発生しました: {str(e)}")
                    # エラーが発生しても�E琁E��続衁E                    continue

            # 全ファイル処琁E�E場合も、新しいレジストリを作�Eして保孁E            file_registry = {}
            for file_path in files:
                str_path = str(file_path)
                file_registry[str_path] = rag_service.document_processor.get_file_metadata(str_path)
            rag_service.document_processor.save_file_registry(processed_dir, file_registry)

        logger.info(f"チE��レクトリ '{source_dir}' 冁E�Eファイルを�E琁E��ました�E�合訁E{len(results)} チャンク�E�E)
        return results

    # 進捗表示付きの処琁E��ソチE��に置き換ぁE    rag_service.document_processor.process_directory = process_directory_with_progress

    # インチE��クス化を実衁E    result = rag_service.index_documents(directory_path, processed_dir, chunk_size, chunk_overlap, incremental)

    # 允E�EメソチE��に戻ぁE    rag_service.document_processor.process_directory = original_process_directory

    if result["success"]:
        incremental_text = "差刁E if incremental else "全て"
        logger.info(
            f"インチE��クス化が完亁E��ました�E�Eincremental_text}のファイルを�E琁E��{result['document_count']} ドキュメント、{result['processing_time']:.2f} 秒！E
        )
        print(
            f"インチE��クス化が完亁E��ました�E�Eincremental_text}のファイルを�E琁E��\n"
            f"- ドキュメント数: {result['document_count']}\n"
            f"- 処琁E��閁E {result['processing_time']:.2f} 秒\n"
            f"- メチE��ージ: {result.get('message', '')}"
        )
    else:
        logger.error(f"インチE��クス化に失敗しました: {result.get('error', '不�Eなエラー')}")
        print(
            f"インチE��クス化に失敗しました\n"
            f"- エラー: {result.get('error', '不�Eなエラー')}\n"
            f"- 処琁E��閁E {result['processing_time']:.2f} 私E
        )
        sys.exit(1)


def get_document_count():
    """
    インチE��クス冁E�Eドキュメント数を取得すめE    """
    logger = setup_logging()
    logger.info("インチE��クス冁E�Eドキュメント数を取得してぁE��ぁE..")

    # 環墁E��数の読み込み
    load_dotenv()

    # RAGサービスの作�E
    rag_service = create_rag_service_from_env()

    # ドキュメント数を取征E    try:
        count = rag_service.get_document_count()
        logger.info(f"インチE��クス冁E�Eドキュメント数: {count}")
        print(f"インチE��クス冁E�Eドキュメント数: {count}")
    except Exception as e:
        logger.error(f"ドキュメント数の取得中にエラーが発生しました: {str(e)}")
        print(f"ドキュメント数の取得中にエラーが発生しました: {str(e)}")
        sys.exit(1)


def main():
    """
    メイン関数

    コマンドライン引数を解析し、E��刁E��処琁E��実行します、E    """
    # コマンドライン引数の解极E    parser = argparse.ArgumentParser(
        description="MCP RAG Server CLI - インチE��クスのクリアとインチE��クス化を行うためのコマンドラインインターフェース"
    )
    subparsers = parser.add_subparsers(dest="command", help="実行するコマンチE)

    # clearコマンチE    subparsers.add_parser("clear", help="インチE��クスをクリアする")

    # indexコマンチE    index_parser = subparsers.add_parser("index", help="ドキュメントをインチE��クス化すめE)
    index_parser.add_argument(
        "--directory",
        "-d",
        default=os.environ.get("SOURCE_DIR", "./data/source"),
        help="インチE��クス化するドキュメントが含まれるチE��レクトリのパス",
    )
    index_parser.add_argument("--chunk-size", "-s", type=int, default=500, help="チャンクサイズ�E�文字数�E�E)
    index_parser.add_argument("--chunk-overlap", "-o", type=int, default=100, help="チャンク間�Eオーバ�EラチE�E�E�文字数�E�E)
    index_parser.add_argument("--incremental", "-i", action="store_true", help="差刁E�EみをインチE��クス化すめE)

    # countコマンチE    subparsers.add_parser("count", help="インチE��クス冁E�Eドキュメント数を取得すめE)

    args = parser.parse_args()

    # コマンドに応じた�E琁E��実衁E    if args.command == "clear":
        clear_index()
    elif args.command == "index":
        index_documents(args.directory, args.chunk_size, args.chunk_overlap, args.incremental)
    elif args.command == "count":
        get_document_count()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
