# -*- coding: utf-8 -*-
import os
import logging
from pathlib import Path
from markdown_converter import MarkdownConverter
from chunk_processor import clean_text, organize_text_with_llm

def process_documents(
    source_dir: str = "./data/source",
    markdown_dir: str = "./data/markdowns",
    model: str = "gemma3:12b",
    temperature: float = 0.0,
    num_ctx: int = 2048,
    num_predict: int = 1024,
):
    # ログの設定
    logging.basicConfig(filename='process_documents.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s:%(message)s')

    source_path = Path(source_dir)
    markdown_path = Path(markdown_dir)
    markdown_path.mkdir(parents=True, exist_ok=True)

    # 既存のマークダウンファイル名（拡張子なし）を取得
    existing_md_files = {f.stem for f in markdown_path.glob("*.md")}

    # ソースディレクトリ内のファイルを再帰的に取得
    source_files = [f for f in source_path.rglob("*") if f.is_file()]

    # 変換対象のファイルを特定
    files_to_process = [f for f in source_files if f.stem not in existing_md_files]

    converter = MarkdownConverter()

    for file_path in files_to_process:
        try:
            # ファイルをマークダウンに変換
            markdown_content = converter.convert_file_to_markdown(file_path)

            # テキストをクリーンアップ
            cleaned_text = clean_text(markdown_content)

            # LLMでテキストを整形
            organized_text = organize_text_with_llm(
                text=cleaned_text,
                model=model,
                temperature=temperature,
                num_ctx=num_ctx,
                num_predict=num_predict
            )
            
            # マークダウンファイルとして保存
            relative_path = file_path.relative_to(source_path)
            output_file = markdown_path / relative_path.with_suffix('.md')
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(organized_text)

            logging.info(f"Processed and saved: {output_file}")

        except FileNotFoundError as e:
            logging.error(f"File not found: {file_path} - {e}")
        except ValueError as e:
            logging.error(f"Value error processing {file_path}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error processing {file_path}: {e}")

def main():
    try:
        process_documents()
    except Exception as e:
        logging.error(f"error in markdown_maker: {e}")

if __name__ == "__main__":
    main()  