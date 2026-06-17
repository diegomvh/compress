import platform
from os import mkdir
from os.path import abspath, basename, exists, expanduser, getsize, join
from shutil import move, rmtree
from subprocess import DEVNULL, run
from typing import Tuple
from pypdf import PdfReader, PdfWriter

from rich.console import Console

from utils import convert_size

console = Console()

cache_folder = expanduser("~/Library/Caches/compress/") if platform.system() == "Darwin" else expanduser("~/.cache/compress/")


def compress_pdf_lossless(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    for page in writer.pages:
        # Compress the data streams inside each page (Lossless)
        page.compress_content_streams(level=9) 

    # Eliminate duplicate images/objects and unreferenced data
    writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)

    with open(output_path, "wb") as f:
        writer.write(f)


def compress(file_path: str, workers: int | None = None) -> Tuple:
    file_path = abspath(file_path)
    file_name = basename(file_path)
    before_size = getsize(file_path)

    if exists(cache_folder):
        rmtree(cache_folder)

    mkdir(cache_folder)

    new_file_path = join(cache_folder, file_name)
    compress_pdf_lossless(file_path, new_file_path)

    """
    Quality options:
    - 'screen': Low-res (72 dpi), maximum compression, screen-only.
    - 'ebook': Medium-res (150 dpi), good for digital reading.
    - 'printer': High-res (300 dpi), ideal for physical print.
    """
    quality = 'ebook'
    with console.status("[bold green]Ghostscript..."):
        run(
            [
                "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS=/{quality}",
                "-dNOPAUSE", "-dQUIET", "-dBATCH",
                f"-sOutputFile={new_file_path}", file_path
            ],
            stdout=DEVNULL,
        ).check_returncode()

    after_size = getsize(new_file_path)

    if after_size >= before_size:
        print("File size unchanged")
        return (before_size, before_size)

    move(new_file_path, file_path)

    if exists(cache_folder):
        rmtree(cache_folder)

    print(
        f"Successfully compressed {convert_size(before_size)} -> {convert_size(after_size)}"
    )
    return (before_size, after_size)
