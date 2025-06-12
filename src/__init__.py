#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NakedRAGパッケージ

シンプルなRAG（Retrieval-Augmented Generation）システムを提供します。
"""

# サブパッケージをエクスポート
from . import agents
from . import rag
from . import server
from . import utils

# 主要クラスを直接エクスポート
from .agents import LibrarianAgent, PromptManager
from .rag import RAGSystem, RAGSearcher
from .server import mcp, run_server
from .utils import setup_logger
