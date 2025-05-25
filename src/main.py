#!/usr/bin/env python
"""
MCP RAG Server

Model Context Protocol (MCP)に準拠したRAG機�Eを持つPythonサーバ�E
"""

import sys
import os
import argparse
import importlib
import logging
from dotenv import load_dotenv

from .mcp_server import MCPServer
from .example_tool import register_example_tools
from .rag_tools import register_rag_tools, create_rag_service_from_env


def main():
    """
    メイン関数

    コマンドライン引数を解析し、MCPサーバ�Eを起動します、E    """
    # コマンドライン引数の解极E    parser = argparse.ArgumentParser(
        description="MCP RAG Server - Model Context Protocol (MCP)に準拠したRAG機�Eを持つPythonサーバ�E"
    )
    parser.add_argument("--name", default="mcp-rag-server", help="サーバ�E吁E)
    parser.add_argument("--version", default="0.1.0", help="サーバ�Eバ�Eジョン")
    parser.add_argument("--description", default="MCP RAG Server - 褁E��形式�Eドキュメント�ERAG検索", help="サーバ�Eの説昁E)
    parser.add_argument("--module", help="追加のチE�Eルモジュール�E�侁E myapp.tools�E�E)
    args = parser.parse_args()

    # 環墁E��数の読み込み
    load_dotenv()

    # チE��レクトリの作�E
    os.makedirs("logs", exist_ok=True)
    os.makedirs(os.environ.get("SOURCE_DIR", "data/source"), exist_ok=True)
    os.makedirs(os.environ.get("PROCESSED_DIR", "data/processed"), exist_ok=True)

    # ロギングの設宁E    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(os.path.join("logs", "mcp_rag_server.log"), encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("main")

    try:
        # MCPサーバ�Eの作�E
        server = MCPServer()

        # サンプルチE�Eルの登録
        register_example_tools(server)

        # RAGサービスの作�Eと登録
        logger.info("RAGサービスを�E期化してぁE��ぁE..")
        rag_service = create_rag_service_from_env()
        register_rag_tools(server, rag_service)
        logger.info("RAGチE�Eルを登録しました")

        # 追加のチE�Eルモジュールがある場合�E読み込む
        if args.module:
            try:
                module = importlib.import_module(args.module)
                if hasattr(module, "register_tools"):
                    module.register_tools(server)
                    print(f"モジュール '{args.module}' からチE�Eルを登録しました", file=sys.stderr)
                else:
                    print(f"警呁E モジュール '{args.module}' に register_tools 関数が見つかりません", file=sys.stderr)
            except ImportError as e:
                print(f"警呁E モジュール '{args.module}' の読み込みに失敗しました: {str(e)}", file=sys.stderr)

        # MCPサーバ�Eの起勁E        server.start(args.name, args.version, args.description)

    except KeyboardInterrupt:
        print("サーバ�Eを終亁E��ます、E, file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
