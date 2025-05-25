"""
MCPサーバ�Eモジュール

Model Context Protocol (MCP)に準拠したサーバ�Eを提供します、EJSON-RPC over stdioを使用してクライアントから�Eリクエストを処琁E��ます、E"""

import sys
import json
import logging
from typing import Dict, Any, List, Callable
from pathlib import Path


class MCPServer:
    """
    Model Context Protocol (MCP)に準拠したサーバ�Eクラス

    JSON-RPC over stdioを使用してクライアントから�Eリクエストを処琁E��ます、E
    Attributes:
        tools: 登録されたツールのチE��クショナリ
        logger: ロガー
    """

    def __init__(self):
        """
        MCPServerのコンストラクタ
        """
        self.tools = {}
        self.tool_handlers = {}

        # ロガーの設宁E        self.logger = logging.getLogger("mcp_server")
        self.logger.setLevel(logging.INFO)

        # ファイルハンドラの設宁E        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "mcp_server.log")
        file_handler.setLevel(logging.INFO)

        # フォーマッタの設宁E        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # ハンドラの追加
        self.logger.addHandler(file_handler)

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable):
        """
        チE�Eルを登録します、E
        Args:
            name: チE�Eル吁E            description: チE�Eルの説昁E            input_schema: 入力スキーチE            handler: チE�Eルのハンドラ関数
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self.tool_handlers[name] = handler
        self.logger.info(f"チE�Eル '{name}' を登録しました")

    def start(self, server_name: str = "mcp-server-python", version: str = "0.1.0", description: str = "Python MCP Server"):
        """
        サーバ�Eを起動し、stdioからのリクエストをリチE��ンします、E
        Args:
            server_name: サーバ�E吁E            version: バ�Eジョン
            description: 説昁E        """
        self.logger.info(f"MCPサーバ�E '{server_name}' を起動しました")

        # サーバ�E惁E��を�E劁E        self._send_response(
            {
                "jsonrpc": "2.0",
                "method": "server/info",
                "params": {
                    "name": server_name,
                    "version": version,
                    "description": description,
                    "tools": self._get_tools(),
                    "resources": self._get_resources(),
                },
            }
        )

        # チE�Eル惁E��を�E劁E        self._send_response(
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {
                    "tools": self._get_tools(),
                },
            }
        )

        # リクエストをリチE��ン
        while True:
            try:
                # 標準�E力からリクエストを読み込む
                request_line = sys.stdin.readline()
                if not request_line:
                    break

                # リクエストをパ�Eス
                request = json.loads(request_line)
                self.logger.info(f"リクエストを受信しました: {request}")

                # リクエストを処琁E                self._handle_request(request)

            except json.JSONDecodeError:
                self.logger.error("JSONのパ�Eスに失敗しました")
                self._send_error(-32700, "Parse error", None)

            except Exception as e:
                self.logger.error(f"エラーが発生しました: {str(e)}")
                self._send_error(-32603, f"Internal error: {str(e)}", None)

    def _handle_request(self, request: Dict[str, Any]):
        """
        リクエストを処琁E��ます、E
        Args:
            request: JSONリクエスチE        """
        # リクエスト�EバリチE�Eション
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            self._send_error(-32600, "Invalid Request", request.get("id"))
            return

        if "method" not in request:
            self._send_error(-32600, "Method not specified", request.get("id"))
            return

        # メソチE��の取征E        method = request["method"]
        params = request.get("params", {})
        request_id = request.get("id")

        # メソチE��の処琁E        if method == "initialize":
            self._handle_initialize(params, request_id)
        elif method == "tools/list":
            self._handle_tools_list(request_id)
        elif method == "tools/call":
            self._handle_tools_call(params, request_id)
        elif method == "notifications/initialized":
            self._handle_notifications_initialized(params, request_id)
        elif method == "resources/list":
            self._handle_resources_list(request_id)
        elif method == "resources/templates/list":
            self._handle_resources_templates_list(request_id)
        else:
            # 登録されたツールを直接呼び出ぁE            if method in self.tool_handlers:
                try:
                    result = self.tool_handlers[method](params)
                    self._send_result(result, request_id)
                except Exception as e:
                    self._send_error(-32603, f"Tool execution error: {str(e)}", request_id)
            else:
                self._send_error(-32601, f"Method not found: {method}", request_id)

    def _handle_initialize(self, params: Dict[str, Any], request_id: Any):
        """
        initializeメソチE��を�E琁E��ます、E
        Args:
            params: リクエストパラメータ
            request_id: リクエスチED
        """
        # クライアント情報を取得（オプション�E�E        client_name = params.get("client_name", "unknown")
        client_version = params.get("client_version", "unknown")

        self.logger.info(f"クライアンチE'{client_name} {client_version}' が接続しました")

        # サーバ�Eの機�Eを返す
        response = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-server-python", "version": "0.1.0", "description": "Python MCP Server"},
            "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False, "subscribe": False}},
            "instructions": "Python MCPサーバ�Eを使用する際�E注意点:\n1. 吁E��ールの入力パラメータを確認してください、En2. エラーが発生した場合�Eログを確認してください、E,
        }

        self._send_result(response, request_id)

        # チE�Eル惁E��を送信
        self._send_response(
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {
                    "tools": self._get_tools(),
                },
            }
        )

    def _send_result(self, result: Any, request_id: Any):
        """
        成功レスポンスを送信します、E
        Args:
            result: レスポンス結果
            request_id: リクエスチED
        """
        response = {"jsonrpc": "2.0", "result": result, "id": request_id}

        self._send_response(response)

    def _send_error(self, code: int, message: str, request_id: Any):
        """
        エラーレスポンスを送信します、E
        Args:
            code: エラーコーチE            message: エラーメチE��ージ
            request_id: リクエスチED
        """
        response = {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": request_id}

        self._send_response(response)

    def _send_response(self, response: Dict[str, Any]):
        """
        レスポンスを標準�E力に送信します、E
        Args:
            response: レスポンス
        """
        response_json = json.dumps(response)
        print(response_json, flush=True)
        self.logger.info(f"レスポンスを送信しました: {response_json}")

    def _get_tools(self) -> List[Dict[str, Any]]:
        """
        サーバ�Eが提供するツールの一覧を取得します、E
        Returns:
            チE�Eルの一覧
        """
        return list(self.tools.values())

    def _handle_tools_call(self, params: Dict[str, Any], request_id: Any):
        """
        tools/callメソチE��を�E琁E��ます、E
        Args:
            params: リクエストパラメータ
            request_id: リクエスチED
        """
        # パラメータのバリチE�Eション
        if "name" not in params:
            self._send_error(-32602, "Invalid params: name is required", request_id)
            return

        if "arguments" not in params:
            self._send_error(-32602, "Invalid params: arguments is required", request_id)
            return

        tool_name = params["name"]
        arguments = params["arguments"]

        # チE�Eルの処琁E        if tool_name in self.tool_handlers:
            try:
                result = self.tool_handlers[tool_name](arguments)
                if isinstance(result, dict) and "content" in result:
                    self._send_result(result, request_id)
                else:
                    # 結果をコンチE��チE��式に変換
                    content = [{"type": "text", "text": str(result)}]
                    self._send_result({"content": content}, request_id)
            except Exception as e:
                self.logger.error(f"チE�Eル '{tool_name}' の実行中にエラーが発生しました: {str(e)}")
                self._send_result(
                    {
                        "content": [{"type": "text", "text": f"チE�Eルの実行中にエラーが発生しました: {str(e)}"}],
                        "isError": True,
                    },
                    request_id,
                )
        else:
            self._send_result(
                {"content": [{"type": "text", "text": f"チE�Eルが見つかりません: {tool_name}"}], "isError": True}, request_id
            )

    def _handle_tools_list(self, request_id: Any):
        """
        tools/listメソチE��を�E琁E��ます、E
        Args:
            request_id: リクエスチED
        """
        tools = self._get_tools()
        self._send_result({"tools": tools}, request_id)

    def _handle_notifications_initialized(self, params: Dict[str, Any], request_id: Any):
        """
        notifications/initializedメソチE��を�E琁E��ます、E        クライアント�E初期化完亁E��知を�E琁E��ます、E
        Args:
            params: リクエストパラメータ
            request_id: リクエスチED
        """
        self.logger.info("クライアント�E初期化が完亁E��ました")
        # 通知なのでレスポンスは不要E        # ただし、エラーが発生した場合�Eエラーレスポンスを返す忁E��がある
        if request_id is not None:
            self._send_result({}, request_id)

    def _handle_resources_list(self, request_id: Any):
        """
        resources/listメソチE��を�E琁E��ます、E        利用可能なリソースの一覧を返します、E
        Args:
            request_id: リクエスチED
        """
        resources = self._get_resources()
        self._send_result({"resources": resources}, request_id)

    def _handle_resources_templates_list(self, request_id: Any):
        """
        resources/templates/listメソチE��を�E琁E��ます、E        利用可能なリソースチE��プレート�E一覧を返します、E
        Args:
            request_id: リクエスチED
        """
        templates = self._get_resource_templates()
        self._send_result({"templates": templates}, request_id)

    def _get_resources(self) -> List[Dict[str, Any]]:
        """
        サーバ�Eが提供するリソースの一覧を取得します、E
        Returns:
            リソースの一覧
        """
        return []

    def _get_resource_templates(self) -> List[Dict[str, Any]]:
        """
        サーバ�Eが提供するリソースチE��プレート�E一覧を取得します、E
        Returns:
            リソースチE��プレート�E一覧
        """
        return []
