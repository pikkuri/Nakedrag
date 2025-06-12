# -*- coding: utf-8 -*-
import os
from pathlib import Path
from src.rag.markdown_converter import MarkdownConverter
from src.utils.chunk_processor import clean_text, organize_text_with_llm
from src.utils.logger_util import setup_logger

def process_documents(
    source_dir: str = "./data/source",
    markdown_dir: str = "./data/markdowns",
    model: str = "gemma3:12b",
    temperature: float = 0.0,
    num_ctx: int = 2048,
    num_predict: int = 1024,
    debug: bool = False,
):
    # ロガーの設定
    logger = setup_logger(__name__)
    
    # デバッグモードの通知
    if debug:
        logger.debug("デバッグモードが有効です")

    source_path = Path(source_dir)
    markdown_path = Path(markdown_dir)
    markdown_path.mkdir(parents=True, exist_ok=True)

    # 既存のマークダウンファイル名（拡張子なし）を取得
    existing_md_files = {f.stem for f in markdown_path.glob("*.md")}

    # ソースディレクトリ内のファイルを再帰的に取得
    source_files = [f for f in source_path.rglob("*") if f.is_file()]

    # 変換対象のファイルを特定
    files_to_process = [f for f in source_files if f.stem not in existing_md_files]
    
    logger.info(f"変換対象ファイル数: {len(files_to_process)}")
    if debug:
        for f in files_to_process:
            logger.debug(f"  変換対象ファイル: {f}")

    converter = MarkdownConverter()

    for file_path in files_to_process:
        try:
            # ファイルをマークダウンに変換
            markdown_content = converter.convert_file_to_markdown(file_path)

            # テキストをクリーンアップ
            cleaned_text = clean_text(markdown_content)

            # LLMでテキストを整形
            if debug:
                logger.debug(f"LLMでテキストを整形します")
            organized_text = organize_text_with_llm(
                text=cleaned_text,
                model=model,
                temperature=temperature,
                num_ctx=num_ctx,
                num_predict=num_predict
            )
            
            # マークダウンファイルとして保存
            # ソースファイルの相対パスを取得
            relative_path = Path(os.path.relpath(file_path, start=source_path))
            if debug:
                logger.debug(f"ソースファイルの相対パス: {relative_path}")
            
            # ソースファイルがsource/markdown/内にある場合は、markdownsディレクトリ直下に保存する
            if str(relative_path).startswith('markdown'):
                # 'markdown/'を除去して、markdowns直下に保存
                file_name = os.path.basename(str(relative_path))
                # ファイル名から拡張子を除去し、.mdを追加
                base_name = os.path.splitext(file_name)[0]
                output_file = markdown_path / f"{base_name}.md"
                if debug:
                    logger.debug(f"markdownディレクトリ内のファイルを処理: {file_name}")
            else:
                # それ以外のファイルは元のディレクトリ構造を維持
                output_file = markdown_path / relative_path.with_suffix('.md')
                if debug:
                    logger.debug(f"通常パスで処理: {relative_path}")
            
            if debug:
                logger.debug(f"保存先ファイルパス: {output_file}")
                logger.debug(f"保存先ディレクトリ: {output_file.parent}")
            
            # 保存先ディレクトリが存在するか確認
            if not output_file.parent.exists():
                if debug:
                    logger.debug(f"保存先ディレクトリが存在しないため作成します: {output_file.parent}")
                
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # ファイルに書き込み
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(organized_text)
                if debug:
                    logger.debug(f"ファイルに書き込み成功: {output_file}")
            except Exception as e:
                logger.error(f"ファイル書き込み中にエラーが発生しました: {e}")
                raise

            logger.info(f"Processed and saved: {output_file}")

        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path} - {e}")
        except ValueError as e:
            logger.error(f"Value error processing {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")

def main():
    # ロガーの設定
    logger = setup_logger(__name__)
    
    try:
        # debugパラメータを指定することで詳細なログを出力可能
        # デフォルトはデバッグモード無効
        process_documents(debug=False)
    except Exception as e:
        logger.error(f"error in markdown_maker: {e}")
        # スタックトレースも出力
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()