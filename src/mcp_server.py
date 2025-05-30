"""
MCPãµã¼ããEã¢ã¸ã¥ã¼ã«

Model Context Protocol (MCP)ã«æºæ ãããµã¼ããEãæä¾ãã¾ããEJSON-RPC over stdioãä½¿ç¨ãã¦ã¯ã©ã¤ã¢ã³ããããEãªã¯ã¨ã¹ããå¦çEã¾ããE"""

import sys
import json
import logging
from typing import Dict, Any, List, Callable
from pathlib import Path


class MCPServer:
    """
    Model Context Protocol (MCP)ã«æºæ ãããµã¼ããEã¯ã©ã¹

    JSON-RPC over stdioãä½¿ç¨ãã¦ã¯ã©ã¤ã¢ã³ããããEãªã¯ã¨ã¹ããå¦çEã¾ããE
    Attributes:
        tools: ç»é²ããããã¼ã«ã®ãE£ã¯ã·ã§ããª
        logger: ã­ã¬ã¼
    """

    def __init__(self):
        """
        MCPServerã®ã³ã³ã¹ãã©ã¯ã¿
        """
        self.tools = {}
        self.tool_handlers = {}

        # ã­ã¬ã¼ã®è¨­å®E        self.logger = logging.getLogger("mcp_server")
        self.logger.setLevel(logging.INFO)

        # ãã¡ã¤ã«ãã³ãã©ã®è¨­å®E        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "mcp_server.log")
        file_handler.setLevel(logging.INFO)

        # ãã©ã¼ããã¿ã®è¨­å®E        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # ãã³ãã©ã®è¿½å 
        self.logger.addHandler(file_handler)

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable):
        """
        ãEEã«ãç»é²ãã¾ããE
        Args:
            name: ãEEã«åE            description: ãEEã«ã®èª¬æE            input_schema: å¥åã¹ã­ã¼ãE            handler: ãEEã«ã®ãã³ãã©é¢æ°
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self.tool_handlers[name] = handler
        self.logger.info(f"ãEEã« '{name}' ãç»é²ãã¾ãã")

    def start(self, server_name: str = "mcp-server-python", version: str = "0.1.0", description: str = "Python MCP Server"):
        """
        ãµã¼ããEãèµ·åããstdioããã®ãªã¯ã¨ã¹ãããªãE¹ã³ãã¾ããE
        Args:
            server_name: ãµã¼ããEåE            version: ããEã¸ã§ã³
            description: èª¬æE        """
        self.logger.info(f"MCPãµã¼ããE '{server_name}' ãèµ·åãã¾ãã")

        # ãµã¼ããEæE ±ãåEåE        self._send_response(
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

        # ãEEã«æE ±ãåEåE        self._send_response(
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {
                    "tools": self._get_tools(),
                },
            }
        )

        # ãªã¯ã¨ã¹ãããªãE¹ã³
        while True:
            try:
                # æ¨æºåEåãããªã¯ã¨ã¹ããèª­ã¿è¾¼ã
                request_line = sys.stdin.readline()
                if not request_line:
                    break

                # ãªã¯ã¨ã¹ããããEã¹
                request = json.loads(request_line)
                self.logger.info(f"ãªã¯ã¨ã¹ããåä¿¡ãã¾ãã: {request}")

                # ãªã¯ã¨ã¹ããå¦çE                self._handle_request(request)

            except json.JSONDecodeError:
                self.logger.error("JSONã®ããEã¹ã«å¤±æãã¾ãã")
                self._send_error(-32700, "Parse error", None)

            except Exception as e:
                self.logger.error(f"ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}")
                self._send_error(-32603, f"Internal error: {str(e)}", None)

    def _handle_request(self, request: Dict[str, Any]):
        """
        ãªã¯ã¨ã¹ããå¦çEã¾ããE
        Args:
            request: JSONãªã¯ã¨ã¹ãE        """
        # ãªã¯ã¨ã¹ããEããªãEEã·ã§ã³
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            self._send_error(-32600, "Invalid Request", request.get("id"))
            return

        if "method" not in request:
            self._send_error(-32600, "Method not specified", request.get("id"))
            return

        # ã¡ã½ãEã®åå¾E        method = request["method"]
        params = request.get("params", {})
        request_id = request.get("id")

        # ã¡ã½ãEã®å¦çE        if method == "initialize":
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
            # ç»é²ããããã¼ã«ãç´æ¥å¼ã³åºãE            if method in self.tool_handlers:
                try:
                    result = self.tool_handlers[method](params)
                    self._send_result(result, request_id)
                except Exception as e:
                    self._send_error(-32603, f"Tool execution error: {str(e)}", request_id)
            else:
                self._send_error(-32601, f"Method not found: {method}", request_id)

    def _handle_initialize(self, params: Dict[str, Any], request_id: Any):
        """
        initializeã¡ã½ãEãåEçEã¾ããE
        Args:
            params: ãªã¯ã¨ã¹ããã©ã¡ã¼ã¿
            request_id: ãªã¯ã¨ã¹ãED
        """
        # ã¯ã©ã¤ã¢ã³ãæå ±ãåå¾ï¼ãªãã·ã§ã³EE        client_name = params.get("client_name", "unknown")
        client_version = params.get("client_version", "unknown")

        self.logger.info(f"ã¯ã©ã¤ã¢ã³ãE'{client_name} {client_version}' ãæ¥ç¶ãã¾ãã")

        # ãµã¼ããEã®æ©èEãè¿ã
        response = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-server-python", "version": "0.1.0", "description": "Python MCP Server"},
            "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False, "subscribe": False}},
            "instructions": "Python MCPãµã¼ããEãä½¿ç¨ããéãEæ³¨æç¹:\n1. åEã¼ã«ã®å¥åãã©ã¡ã¼ã¿ãç¢ºèªãã¦ãã ãããEn2. ã¨ã©ã¼ãçºçããå ´åãEã­ã°ãç¢ºèªãã¦ãã ãããE,
        }

        self._send_result(response, request_id)

        # ãEEã«æE ±ãéä¿¡
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
        æåã¬ã¹ãã³ã¹ãéä¿¡ãã¾ããE
        Args:
            result: ã¬ã¹ãã³ã¹çµæ
            request_id: ãªã¯ã¨ã¹ãED
        """
        response = {"jsonrpc": "2.0", "result": result, "id": request_id}

        self._send_response(response)

    def _send_error(self, code: int, message: str, request_id: Any):
        """
        ã¨ã©ã¼ã¬ã¹ãã³ã¹ãéä¿¡ãã¾ããE
        Args:
            code: ã¨ã©ã¼ã³ã¼ãE            message: ã¨ã©ã¼ã¡ãE»ã¼ã¸
            request_id: ãªã¯ã¨ã¹ãED
        """
        response = {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": request_id}

        self._send_response(response)

    def _send_response(self, response: Dict[str, Any]):
        """
        ã¬ã¹ãã³ã¹ãæ¨æºåEåã«éä¿¡ãã¾ããE
        Args:
            response: ã¬ã¹ãã³ã¹
        """
        response_json = json.dumps(response)
        print(response_json, flush=True)
        self.logger.info(f"ã¬ã¹ãã³ã¹ãéä¿¡ãã¾ãã: {response_json}")

    def _get_tools(self) -> List[Dict[str, Any]]:
        """
        ãµã¼ããEãæä¾ãããã¼ã«ã®ä¸è¦§ãåå¾ãã¾ããE
        Returns:
            ãEEã«ã®ä¸è¦§
        """
        return list(self.tools.values())

    def _handle_tools_call(self, params: Dict[str, Any], request_id: Any):
        """
        tools/callã¡ã½ãEãåEçEã¾ããE
        Args:
            params: ãªã¯ã¨ã¹ããã©ã¡ã¼ã¿
            request_id: ãªã¯ã¨ã¹ãED
        """
        # ãã©ã¡ã¼ã¿ã®ããªãEEã·ã§ã³
        if "name" not in params:
            self._send_error(-32602, "Invalid params: name is required", request_id)
            return

        if "arguments" not in params:
            self._send_error(-32602, "Invalid params: arguments is required", request_id)
            return

        tool_name = params["name"]
        arguments = params["arguments"]

        # ãEEã«ã®å¦çE        if tool_name in self.tool_handlers:
            try:
                result = self.tool_handlers[tool_name](arguments)
                if isinstance(result, dict) and "content" in result:
                    self._send_result(result, request_id)
                else:
                    # çµæãã³ã³ãE³ãE½¢å¼ã«å¤æ
                    content = [{"type": "text", "text": str(result)}]
                    self._send_result({"content": content}, request_id)
            except Exception as e:
                self.logger.error(f"ãEEã« '{tool_name}' ã®å®è¡ä¸­ã«ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}")
                self._send_result(
                    {
                        "content": [{"type": "text", "text": f"ãEEã«ã®å®è¡ä¸­ã«ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}"}],
                        "isError": True,
                    },
                    request_id,
                )
        else:
            self._send_result(
                {"content": [{"type": "text", "text": f"ãEEã«ãè¦ã¤ããã¾ãã: {tool_name}"}], "isError": True}, request_id
            )

    def _handle_tools_list(self, request_id: Any):
        """
        tools/listã¡ã½ãEãåEçEã¾ããE
        Args:
            request_id: ãªã¯ã¨ã¹ãED
        """
        tools = self._get_tools()
        self._send_result({"tools": tools}, request_id)

    def _handle_notifications_initialized(self, params: Dict[str, Any], request_id: Any):
        """
        notifications/initializedã¡ã½ãEãåEçEã¾ããE        ã¯ã©ã¤ã¢ã³ããEåæåå®äºEç¥ãåEçEã¾ããE
        Args:
            params: ãªã¯ã¨ã¹ããã©ã¡ã¼ã¿
            request_id: ãªã¯ã¨ã¹ãED
        """
        self.logger.info("ã¯ã©ã¤ã¢ã³ããEåæåãå®äºEã¾ãã")
        # éç¥ãªã®ã§ã¬ã¹ãã³ã¹ã¯ä¸è¦E        # ãã ããã¨ã©ã¼ãçºçããå ´åãEã¨ã©ã¼ã¬ã¹ãã³ã¹ãè¿ãå¿E¦ããã
        if request_id is not None:
            self._send_result({}, request_id)

    def _handle_resources_list(self, request_id: Any):
        """
        resources/listã¡ã½ãEãåEçEã¾ããE        å©ç¨å¯è½ãªãªã½ã¼ã¹ã®ä¸è¦§ãè¿ãã¾ããE
        Args:
            request_id: ãªã¯ã¨ã¹ãED
        """
        resources = self._get_resources()
        self._send_result({"resources": resources}, request_id)

    def _handle_resources_templates_list(self, request_id: Any):
        """
        resources/templates/listã¡ã½ãEãåEçEã¾ããE        å©ç¨å¯è½ãªãªã½ã¼ã¹ãE³ãã¬ã¼ããEä¸è¦§ãè¿ãã¾ããE
        Args:
            request_id: ãªã¯ã¨ã¹ãED
        """
        templates = self._get_resource_templates()
        self._send_result({"templates": templates}, request_id)

    def _get_resources(self) -> List[Dict[str, Any]]:
        """
        ãµã¼ããEãæä¾ãããªã½ã¼ã¹ã®ä¸è¦§ãåå¾ãã¾ããE
        Returns:
            ãªã½ã¼ã¹ã®ä¸è¦§
        """
        return []

    def _get_resource_templates(self) -> List[Dict[str, Any]]:
        """
        ãµã¼ããEãæä¾ãããªã½ã¼ã¹ãE³ãã¬ã¼ããEä¸è¦§ãåå¾ãã¾ããE
        Returns:
            ãªã½ã¼ã¹ãE³ãã¬ã¼ããEä¸è¦§
        """
        return []
