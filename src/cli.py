#!/usr/bin/env python
"""
MCP RAG Server CLI

ã¤ã³ãEã¯ã¹ã®ã¯ãªã¢ã¨ã¤ã³ãEã¯ã¹åãè¡ãããã®ã³ãã³ãã©ã¤ã³ã¤ã³ã¿ã¼ãã§ã¼ã¹
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
    ã­ã®ã³ã°ã®è¨­å®E    """
    # ã­ã°ãE£ã¬ã¯ããªã®ä½æE
    os.makedirs("logs", exist_ok=True)

    # ã­ã®ã³ã°ã®è¨­å®E    logging.basicConfig(
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
    ã¤ã³ãEã¯ã¹ãã¯ãªã¢ãã
    """
    logger = setup_logging()
    logger.info("ã¤ã³ãEã¯ã¹ãã¯ãªã¢ãã¦ãE¾ãE..")

    # ç°å¢E¤æ°ã®èª­ã¿è¾¼ã¿
    load_dotenv()

    # RAGãµã¼ãã¹ã®ä½æE
    rag_service = create_rag_service_from_env()

    # å¦çE¸ã¿ãE£ã¬ã¯ããªã®ãã¹
    processed_dir = os.environ.get("PROCESSED_DIR", "data/processed")

    # ãã¡ã¤ã«ã¬ã¸ã¹ããªã®åé¤
    registry_path = Path(processed_dir) / "file_registry.json"
    if registry_path.exists():
        try:
            registry_path.unlink()
            logger.info(f"ãã¡ã¤ã«ã¬ã¸ã¹ããªãåé¤ãã¾ãã: {registry_path}")
            print(f"ãã¡ã¤ã«ã¬ã¸ã¹ããªãåé¤ãã¾ãã: {registry_path}")
        except Exception as e:
            logger.error(f"ãã¡ã¤ã«ã¬ã¸ã¹ããªã®åé¤ã«å¤±æãã¾ãã: {str(e)}")
            print(f"ãã¡ã¤ã«ã¬ã¸ã¹ããªã®åé¤ã«å¤±æãã¾ãã: {str(e)}")

    # ã¤ã³ãEã¯ã¹ãã¯ãªã¢
    result = rag_service.clear_index()

    if result["success"]:
        logger.info(f"ã¤ã³ãEã¯ã¹ãã¯ãªã¢ãã¾ããEEresult['deleted_count']} ãã­ã¥ã¡ã³ããåé¤EE)
        print(f"ã¤ã³ãEã¯ã¹ãã¯ãªã¢ãã¾ããEEresult['deleted_count']} ãã­ã¥ã¡ã³ããåé¤EE)
    else:
        logger.error(f"ã¤ã³ãEã¯ã¹ã®ã¯ãªã¢ã«å¤±æãã¾ãã: {result.get('error', 'ä¸æEãªã¨ã©ã¼')}")
        print(f"ã¤ã³ãEã¯ã¹ã®ã¯ãªã¢ã«å¤±æãã¾ãã: {result.get('error', 'ä¸æEãªã¨ã©ã¼')}")
        sys.exit(1)


def index_documents(directory_path, chunk_size=500, chunk_overlap=100, incremental=False):
    """
    ãã­ã¥ã¡ã³ããã¤ã³ãEã¯ã¹åããE
    Args:
        directory_path: ã¤ã³ãEã¯ã¹åãããã­ã¥ã¡ã³ããå«ã¾ãããE£ã¬ã¯ããªã®ãã¹
        chunk_size: ãã£ã³ã¯ãµã¤ãºEæå­æ°EE        chunk_overlap: ãã£ã³ã¯éãEãªã¼ããEã©ãEEEæå­æ°EE        incremental: å·®åEEã¿ãã¤ã³ãEã¯ã¹åãããã©ãE
    """
    logger = setup_logging()
    if incremental:
        logger.info(f"ãE£ã¬ã¯ããª '{directory_path}' åEEå·®åEã¡ã¤ã«ãã¤ã³ãEã¯ã¹åãã¦ãE¾ãE..")
    else:
        logger.info(f"ãE£ã¬ã¯ããª '{directory_path}' åEEãã­ã¥ã¡ã³ããã¤ã³ãEã¯ã¹åãã¦ãE¾ãE..")

    # ç°å¢E¤æ°ã®èª­ã¿è¾¼ã¿
    load_dotenv()

    # ãE£ã¬ã¯ããªã®å­å¨ç¢ºèªE    if not os.path.exists(directory_path):
        logger.error(f"ãE£ã¬ã¯ããª '{directory_path}' ãè¦ã¤ããã¾ãã")
        print(f"ã¨ã©ã¼: ãE£ã¬ã¯ããª '{directory_path}' ãè¦ã¤ããã¾ãã")
        sys.exit(1)

    if not os.path.isdir(directory_path):
        logger.error(f"'{directory_path}' ã¯ãE£ã¬ã¯ããªã§ã¯ããã¾ãã")
        print(f"ã¨ã©ã¼: '{directory_path}' ã¯ãE£ã¬ã¯ããªã§ã¯ããã¾ãã")
        sys.exit(1)

    # RAGãµã¼ãã¹ã®ä½æE
    rag_service = create_rag_service_from_env()

    # å¦çE¸ã¿ãE£ã¬ã¯ããªã®ãã¹
    processed_dir = os.environ.get("PROCESSED_DIR", "data/processed")

    # ã¤ã³ãEã¯ã¹åãå®è¡E    if incremental:
        print(f"ãE£ã¬ã¯ããª '{directory_path}' åEEå·®åEã¡ã¤ã«ãã¤ã³ãEã¯ã¹åãã¦ãE¾ãE..")
    else:
        print(f"ãE£ã¬ã¯ããª '{directory_path}' åEEãã­ã¥ã¡ã³ããã¤ã³ãEã¯ã¹åãã¦ãE¾ãE..")

    # é²æç¶æ³ãè¡¨ç¤ºããããã®ã«ã¦ã³ã¿
    processed_files = 0

    # å¦çEã«ãã¡ã¤ã«æ°ãåå¾E    total_files = 0
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file_path)[1].lower()
            if ext in [".md", ".markdown", ".txt", ".pdf", ".ppt", ".pptx", ".doc", ".docx"]:
                total_files += 1

    print(f"åè¨E{total_files} åãEãã¡ã¤ã«ãæ¤ç´¢ãã¾ãã...")

    # åEERAGServiceã®index_documentsã¡ã½ãEãå¼ã³åºãåã«ãE    # DocumentProcessorã®process_directoryã¡ã½ãEããªã¼ããEã©ã¤ããã¦é²æãè¡¨ç¤º
    original_process_directory = rag_service.document_processor.process_directory

    def process_directory_with_progress(source_dir, processed_dir, chunk_size=500, overlap=100, incremental=False):
        nonlocal processed_files
        results = []
        source_directory = Path(source_dir)

        if not source_directory.exists() or not source_directory.is_dir():
            logger.error(f"ãE£ã¬ã¯ããª '{source_dir}' ãè¦ã¤ãããªãEããã£ã¬ã¯ããªã§ã¯ããã¾ãã")
            raise FileNotFoundError(f"ãE£ã¬ã¯ããª '{source_dir}' ãè¦ã¤ãããªãEããã£ã¬ã¯ããªã§ã¯ããã¾ãã")

        # ãµããEããããã¡ã¤ã«æ¡å¼µå­ãå¨ã¦åå¾E        all_extensions = []
        for ext_list in rag_service.document_processor.SUPPORTED_EXTENSIONS.values():
            all_extensions.extend(ext_list)

        # ãã¡ã¤ã«ãæ¤ç´¢
        files = []
        for ext in all_extensions:
            files.extend(list(source_directory.glob(f"**/*{ext}")))

        logger.info(f"ãE£ã¬ã¯ããª '{source_dir}' åE« {len(files)} åãEãã¡ã¤ã«ãè¦ã¤ããã¾ãã")

        # å·®åEEçEEå ´åããã¡ã¤ã«ã¬ã¸ã¹ããªãèª­ã¿è¾¼ã
        if incremental:
            file_registry = rag_service.document_processor.load_file_registry(processed_dir)
            logger.info(f"ãã¡ã¤ã«ã¬ã¸ã¹ããªãã {len(file_registry)} åãEãã¡ã¤ã«æE ±ãèª­ã¿è¾¼ã¿ã¾ãã")

            # å¦çE¯¾è±¡ã®ãã¡ã¤ã«ãç¹å®E            files_to_process = []
            for file_path in files:
                str_path = str(file_path)
                # ãã¡ã¤ã«ã®ã¡ã¿ãEEã¿ãåå¾E                current_metadata = rag_service.document_processor.get_file_metadata(str_path)

                # ã¬ã¸ã¹ããªã«å­å¨ããªãEã¾ããEããã·ã¥å¤ãå¤æ´ããã¦ãEå ´åãEã¿å¦çE                if (
                    str_path not in file_registry
                    or file_registry[str_path]["hash"] != current_metadata["hash"]
                    or file_registry[str_path]["mtime"] != current_metadata["mtime"]
                    or file_registry[str_path]["size"] != current_metadata["size"]
                ):
                    files_to_process.append(file_path)
                    # ã¬ã¸ã¹ããªãæ´æ°
                    file_registry[str_path] = current_metadata

            print(f"å¦çE¯¾è±¡ã®ãã¡ã¤ã«æ°: {len(files_to_process)} / {len(files)}")

            # åEã¡ã¤ã«ãåEçE            for i, file_path in enumerate(files_to_process):
                try:
                    file_results = rag_service.document_processor.process_file(
                        str(file_path), processed_dir, chunk_size, overlap
                    )
                    results.extend(file_results)
                    processed_files += 1
                    print(
                        f"å¦çE¸­... {processed_files}/{len(files_to_process)} ãã¡ã¤ã« ({(processed_files / len(files_to_process) * 100):.1f}%): {file_path}"
                    )
                except Exception as e:
                    logger.error(f"ãã¡ã¤ã« '{file_path}' ã®å¦çE¸­ã«ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}")
                    # ã¨ã©ã¼ãçºçãã¦ãåEçEç¶è¡E                    continue

            # ãã¡ã¤ã«ã¬ã¸ã¹ããªãä¿å­E            rag_service.document_processor.save_file_registry(processed_dir, file_registry)
        else:
            # å·®åEEçE§ãªãE ´åãEå¨ã¦ã®ãã¡ã¤ã«ãåEçE            for i, file_path in enumerate(files):
                try:
                    file_results = rag_service.document_processor.process_file(
                        str(file_path), processed_dir, chunk_size, overlap
                    )
                    results.extend(file_results)
                    processed_files += 1
                    print(
                        f"å¦çE¸­... {processed_files}/{total_files} ãã¡ã¤ã« ({(processed_files / total_files * 100):.1f}%): {file_path}"
                    )
                except Exception as e:
                    logger.error(f"ãã¡ã¤ã« '{file_path}' ã®å¦çE¸­ã«ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}")
                    # ã¨ã©ã¼ãçºçãã¦ãåEçEç¶è¡E                    continue

            # å¨ãã¡ã¤ã«å¦çEEå ´åããæ°ããã¬ã¸ã¹ããªãä½æEãã¦ä¿å­E            file_registry = {}
            for file_path in files:
                str_path = str(file_path)
                file_registry[str_path] = rag_service.document_processor.get_file_metadata(str_path)
            rag_service.document_processor.save_file_registry(processed_dir, file_registry)

        logger.info(f"ãE£ã¬ã¯ããª '{source_dir}' åEEãã¡ã¤ã«ãåEçEã¾ããEåè¨E{len(results)} ãã£ã³ã¯EE)
        return results

    # é²æè¡¨ç¤ºä»ãã®å¦çE¡ã½ãEã«ç½®ãæãE    rag_service.document_processor.process_directory = process_directory_with_progress

    # ã¤ã³ãEã¯ã¹åãå®è¡E    result = rag_service.index_documents(directory_path, processed_dir, chunk_size, chunk_overlap, incremental)

    # åEEã¡ã½ãEã«æ»ãE    rag_service.document_processor.process_directory = original_process_directory

    if result["success"]:
        incremental_text = "å·®åE if incremental else "å¨ã¦"
        logger.info(
            f"ã¤ã³ãEã¯ã¹åãå®äºEã¾ããEEincremental_text}ã®ãã¡ã¤ã«ãåEçE{result['document_count']} ãã­ã¥ã¡ã³ãã{result['processing_time']:.2f} ç§ï¼E
        )
        print(
            f"ã¤ã³ãEã¯ã¹åãå®äºEã¾ããEEincremental_text}ã®ãã¡ã¤ã«ãåEçE¼\n"
            f"- ãã­ã¥ã¡ã³ãæ°: {result['document_count']}\n"
            f"- å¦çEéE {result['processing_time']:.2f} ç§\n"
            f"- ã¡ãE»ã¼ã¸: {result.get('message', '')}"
        )
    else:
        logger.error(f"ã¤ã³ãEã¯ã¹åã«å¤±æãã¾ãã: {result.get('error', 'ä¸æEãªã¨ã©ã¼')}")
        print(
            f"ã¤ã³ãEã¯ã¹åã«å¤±æãã¾ãã\n"
            f"- ã¨ã©ã¼: {result.get('error', 'ä¸æEãªã¨ã©ã¼')}\n"
            f"- å¦çEéE {result['processing_time']:.2f} ç§E
        )
        sys.exit(1)


def get_document_count():
    """
    ã¤ã³ãEã¯ã¹åEEãã­ã¥ã¡ã³ãæ°ãåå¾ããE    """
    logger = setup_logging()
    logger.info("ã¤ã³ãEã¯ã¹åEEãã­ã¥ã¡ã³ãæ°ãåå¾ãã¦ãE¾ãE..")

    # ç°å¢E¤æ°ã®èª­ã¿è¾¼ã¿
    load_dotenv()

    # RAGãµã¼ãã¹ã®ä½æE
    rag_service = create_rag_service_from_env()

    # ãã­ã¥ã¡ã³ãæ°ãåå¾E    try:
        count = rag_service.get_document_count()
        logger.info(f"ã¤ã³ãEã¯ã¹åEEãã­ã¥ã¡ã³ãæ°: {count}")
        print(f"ã¤ã³ãEã¯ã¹åEEãã­ã¥ã¡ã³ãæ°: {count}")
    except Exception as e:
        logger.error(f"ãã­ã¥ã¡ã³ãæ°ã®åå¾ä¸­ã«ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}")
        print(f"ãã­ã¥ã¡ã³ãæ°ã®åå¾ä¸­ã«ã¨ã©ã¼ãçºçãã¾ãã: {str(e)}")
        sys.exit(1)


def main():
    """
    ã¡ã¤ã³é¢æ°

    ã³ãã³ãã©ã¤ã³å¼æ°ãè§£æããE©åEªå¦çEå®è¡ãã¾ããE    """
    # ã³ãã³ãã©ã¤ã³å¼æ°ã®è§£æE    parser = argparse.ArgumentParser(
        description="MCP RAG Server CLI - ã¤ã³ãEã¯ã¹ã®ã¯ãªã¢ã¨ã¤ã³ãEã¯ã¹åãè¡ãããã®ã³ãã³ãã©ã¤ã³ã¤ã³ã¿ã¼ãã§ã¼ã¹"
    )
    subparsers = parser.add_subparsers(dest="command", help="å®è¡ããã³ãã³ãE)

    # clearã³ãã³ãE    subparsers.add_parser("clear", help="ã¤ã³ãEã¯ã¹ãã¯ãªã¢ãã")

    # indexã³ãã³ãE    index_parser = subparsers.add_parser("index", help="ãã­ã¥ã¡ã³ããã¤ã³ãEã¯ã¹åããE)
    index_parser.add_argument(
        "--directory",
        "-d",
        default=os.environ.get("SOURCE_DIR", "./data/source"),
        help="ã¤ã³ãEã¯ã¹åãããã­ã¥ã¡ã³ããå«ã¾ãããE£ã¬ã¯ããªã®ãã¹",
    )
    index_parser.add_argument("--chunk-size", "-s", type=int, default=500, help="ãã£ã³ã¯ãµã¤ãºEæå­æ°EE)
    index_parser.add_argument("--chunk-overlap", "-o", type=int, default=100, help="ãã£ã³ã¯éãEãªã¼ããEã©ãEEEæå­æ°EE)
    index_parser.add_argument("--incremental", "-i", action="store_true", help="å·®åEEã¿ãã¤ã³ãEã¯ã¹åããE)

    # countã³ãã³ãE    subparsers.add_parser("count", help="ã¤ã³ãEã¯ã¹åEEãã­ã¥ã¡ã³ãæ°ãåå¾ããE)

    args = parser.parse_args()

    # ã³ãã³ãã«å¿ããåEçEå®è¡E    if args.command == "clear":
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
