# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
from typing import Optional
import logging

# 仮想環境のサイトパッケージディレクトリをパスに追加
venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'Lib', 'site-packages')
if os.path.exists(venv_path) and venv_path not in sys.path:
    sys.path.append(venv_path)

# markitdownをインポート
try:
    import markitdown
except ImportError as e:
    print(f"markitdownのインポートに失敗しました: {e}")
    print(f"現在のPythonパス: {sys.path}")
    raise

class MarkdownConverter:
    """
    様々なファイルをMarkdown形式に変換するクラス。
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf": "PDF",
        ".doc": "Word",
        ".docx": "Word",
        ".ppt": "PowerPoint",
        ".pptx": "PowerPoint",
        ".html": "HTML",
        ".json": "JSON",
        ".csv": "CSV",
        ".xlsx": "Excel",
        ".xls": "Excel",
        ".txt": "Text",
        ".md": "Markdown",
        ".markdown": "Markdown",
        ".mp3": "Audio",
        ".wav": "Audio",
        ".m4a": "Audio",
        ".aiff": "Audio",
        ".flac": "Audio",
    }

    def __init__(self, model: Optional[str] = None):
        """
        コンストラクタ。

        Args:
            model: 使用するLLMモデル名（例: 'gemma3:12b'）。Noneの場合、デフォルトモデルを使用。
        """
        self.logger = logging.getLogger("MarkdownConverter")
        self.logger.setLevel(logging.INFO)
        self.model = model
        self.converter = markitdown.MarkItDown(model=model) if model else markitdown.MarkItDown()

    def convert_file_to_markdown(self, file_path: str) -> Optional[str]:
        """
        指定されたファイルをMarkdown形式に変換する。

        Args:
            file_path: 変換するファイルのパス。

        Returns:
            Markdown形式の文字列。変換できない場合はNone。
        """
        ext = Path(file_path).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            self.logger.warning(f"サポートされていないファイル形式: {file_path}")
            return None

        try:
            # Windowsパスを正しいファイルURIに変換
            abs_path = os.path.abspath(file_path)
            # バックスラッシュをスラッシュに変換し、適切なファイルURIの形式にする
            path_with_slashes = abs_path.replace('\\', '/')
            file_uri = f"file:///{path_with_slashes}"
            self.logger.info(f"変換するファイルURI: {file_uri}")
            markdown_content = self.converter.convert_uri(file_uri).markdown
            markdown_content = markdown_content.replace("\x00", "")
            self.logger.info(f"ファイルをMarkdownに変換しました: {file_path}")
            return markdown_content
        except Exception as e:
            self.logger.error(f"Markdown変換中にエラーが発生しました: {file_path} - {str(e)}")
            return None
