"""
サンプルチE�Eルモジュール

MCPサーバ�Eに登録するサンプルチE�Eルを提供します、E"""

import os
import json
import platform
from datetime import datetime
from typing import Dict, Any


def register_example_tools(server):
    """
    サンプルチE�EルをMCPサーバ�Eに登録します、E
    Args:
        server: MCPサーバ�Eのインスタンス
    """
    # シスチE��惁E��チE�Eルの登録
    server.register_tool(
        name="get_system_info",
        description="シスチE��惁E��を取得しまぁE,
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=get_system_info,
    )

    # 現在時刻チE�Eルの登録
    server.register_tool(
        name="get_current_time",
        description="現在の日時を取得しまぁE,
        input_schema={
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "日時�Eフォーマット（侁E '%Y-%m-%d %H:%M:%S'�E�E,
                },
            },
            "required": [],
        },
        handler=get_current_time,
    )

    # エコーチE�Eルの登録
    server.register_tool(
        name="echo",
        description="入力されたチE��ストをそ�Eまま返しまぁE,
        input_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "エコーするチE��スチE,
                },
            },
            "required": ["text"],
        },
        handler=echo,
    )


def get_system_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    シスチE��惁E��を取得します、E
    Args:
        params: パラメータ�E�未使用�E�E
    Returns:
        シスチE��惁E��
    """
    system_info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "cpu_count": os.cpu_count(),
        "platform": platform.platform(),
    }

    return {
        "content": [
            {
                "type": "text",
                "text": f"シスチE��惁E��:\n{json.dumps(system_info, indent=2, ensure_ascii=False)}",
            }
        ]
    }


def get_current_time(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    現在の日時を取得します、E
    Args:
        params: パラメータ
            - format: 日時�Eフォーマット（オプション�E�E
    Returns:
        現在の日晁E    """
    time_format = params.get("format", "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now().strftime(time_format)

    return {
        "content": [
            {
                "type": "text",
                "text": f"現在の日晁E {current_time}",
            }
        ]
    }


def echo(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    入力されたチE��ストをそ�Eまま返します、E
    Args:
        params: パラメータ
            - text: エコーするチE��スチE
    Returns:
        入力されたチE��スチE    """
    text = params.get("text", "")

    return {
        "content": [
            {
                "type": "text",
                "text": f"Echo: {text}",
            }
        ]
    }
