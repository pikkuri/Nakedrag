"""
繧ｵ繝ｳ繝励Ν繝・・繝ｫ繝｢繧ｸ繝･繝ｼ繝ｫ

MCP繧ｵ繝ｼ繝舌・縺ｫ逋ｻ骭ｲ縺吶ｋ繧ｵ繝ｳ繝励Ν繝・・繝ｫ繧呈署萓帙＠縺ｾ縺吶・"""

import os
import json
import platform
from datetime import datetime
from typing import Dict, Any


def register_example_tools(server):
    """
    繧ｵ繝ｳ繝励Ν繝・・繝ｫ繧樽CP繧ｵ繝ｼ繝舌・縺ｫ逋ｻ骭ｲ縺励∪縺吶・
    Args:
        server: MCP繧ｵ繝ｼ繝舌・縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ
    """
    # 繧ｷ繧ｹ繝・Β諠・ｱ繝・・繝ｫ縺ｮ逋ｻ骭ｲ
    server.register_tool(
        name="get_system_info",
        description="繧ｷ繧ｹ繝・Β諠・ｱ繧貞叙蠕励＠縺ｾ縺・,
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=get_system_info,
    )

    # 迴ｾ蝨ｨ譎ょ綾繝・・繝ｫ縺ｮ逋ｻ骭ｲ
    server.register_tool(
        name="get_current_time",
        description="迴ｾ蝨ｨ縺ｮ譌･譎ゅｒ蜿門ｾ励＠縺ｾ縺・,
        input_schema={
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "譌･譎ゅ・繝輔か繝ｼ繝槭ャ繝茨ｼ井ｾ・ '%Y-%m-%d %H:%M:%S'・・,
                },
            },
            "required": [],
        },
        handler=get_current_time,
    )

    # 繧ｨ繧ｳ繝ｼ繝・・繝ｫ縺ｮ逋ｻ骭ｲ
    server.register_tool(
        name="echo",
        description="蜈･蜉帙＆繧後◆繝・く繧ｹ繝医ｒ縺昴・縺ｾ縺ｾ霑斐＠縺ｾ縺・,
        input_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "繧ｨ繧ｳ繝ｼ縺吶ｋ繝・く繧ｹ繝・,
                },
            },
            "required": ["text"],
        },
        handler=echo,
    )


def get_system_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    繧ｷ繧ｹ繝・Β諠・ｱ繧貞叙蠕励＠縺ｾ縺吶・
    Args:
        params: 繝代Λ繝｡繝ｼ繧ｿ・域悴菴ｿ逕ｨ・・
    Returns:
        繧ｷ繧ｹ繝・Β諠・ｱ
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
                "text": f"繧ｷ繧ｹ繝・Β諠・ｱ:\n{json.dumps(system_info, indent=2, ensure_ascii=False)}",
            }
        ]
    }


def get_current_time(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    迴ｾ蝨ｨ縺ｮ譌･譎ゅｒ蜿門ｾ励＠縺ｾ縺吶・
    Args:
        params: 繝代Λ繝｡繝ｼ繧ｿ
            - format: 譌･譎ゅ・繝輔か繝ｼ繝槭ャ繝茨ｼ医が繝励す繝ｧ繝ｳ・・
    Returns:
        迴ｾ蝨ｨ縺ｮ譌･譎・    """
    time_format = params.get("format", "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now().strftime(time_format)

    return {
        "content": [
            {
                "type": "text",
                "text": f"迴ｾ蝨ｨ縺ｮ譌･譎・ {current_time}",
            }
        ]
    }


def echo(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    蜈･蜉帙＆繧後◆繝・く繧ｹ繝医ｒ縺昴・縺ｾ縺ｾ霑斐＠縺ｾ縺吶・
    Args:
        params: 繝代Λ繝｡繝ｼ繧ｿ
            - text: 繧ｨ繧ｳ繝ｼ縺吶ｋ繝・く繧ｹ繝・
    Returns:
        蜈･蜉帙＆繧後◆繝・く繧ｹ繝・    """
    text = params.get("text", "")

    return {
        "content": [
            {
                "type": "text",
                "text": f"Echo: {text}",
            }
        ]
    }
