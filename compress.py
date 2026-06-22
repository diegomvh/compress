import argparse
import os
import sys

from rich.console import Console

from history import history
from office import compress as compress_office
from pdf import compress as compress_pdf
from images import _IMAGE_EXTS, compress_image
from utils import find_files, convert_size

console = Console(highlighter=None)
EXTS = (".docx", ".pptx", ".xlsx") + (".pdf", ) + tuple(_IMAGE_EXTS)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Losslessly compress images in Office documents (docx/pptx/xlsx), PDF files, and standalone images."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="files or directories to compress",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        metavar="N",
        help=f"number of parallel workers (default: min(4, cpu_count) = {min(4, os.cpu_count() or 4)})",
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="disable parallel compression",
    )
    args = parser.parse_args()

    if args.no_parallel:
        workers = 1
    else:
        workers = args.workers

    his = history("process_history.csv")
    his.clean_up()

    file_paths = []
    unchanged_files = 0

    for file_path in find_files(args.paths, EXTS):
        if not his.file_in_history(file_path):
            file_paths.append(file_path)
        else:
            unchanged_files += 1

    file_cnt = len(file_paths)
    console.print(
        f"Found {file_cnt} file(s) to compress and {unchanged_files} file(s) skipped.",
        style="bold",
    )

    if file_cnt == 0:
        sys.exit()

    before_size_sum = 0
    after_size_sum = 0

    try:
        for i, file_path in enumerate(file_paths, start=1):
            print(f"[{i}/{file_cnt}] Processing {file_path}")
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                result = compress_pdf(file_path, workers=workers)
            elif ext in _IMAGE_EXTS:
                result = compress_image(file_path, workers=workers)
            else: 
                result = compress_office(file_path, workers=workers)
            his.add_history(file_path)
            before_size_sum += result[0]
            after_size_sum += result[1]
    except Exception as e:
        print(e)
    finally:
        if before_size_sum == 0:
            sys.exit()

        console.print(
            f"Total compressed {convert_size(before_size_sum - after_size_sum)}",
            style="bold green",
        )
        console.print(
            f"Compression rate {round(100 * (before_size_sum - after_size_sum) / before_size_sum, 2)}%",
            style="bold green",
        )


if __name__ == "__main__":
    main()
