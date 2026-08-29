import os
import datetime
import threading
from typing import List, Optional, Callable, Dict, Any, Set
from PIL import Image
import pymupdf as fitz


def parse_page_range(range_str: str, max_pages: int) -> List[int]:
    """
    Parse a page range string like '1-3, 5, 8-10' or 'all', 'odd', 'even'.
    Returns sorted list of 0-based page indices.
    """
    clean = range_str.strip().lower()
    if not clean or clean == 'all' or clean == '*':
        return list(range(max_pages))
    
    if clean == 'odd':
        return [i for i in range(max_pages) if (i + 1) % 2 != 0]
    
    if clean == 'even':
        return [i for i in range(max_pages) if (i + 1) % 2 == 0]

    selected_pages: Set[int] = set()
    parts = clean.split(',')

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            bounds = part.split('-')
            if len(bounds) == 2:
                try:
                    start = int(bounds[0].strip())
                    end = int(bounds[1].strip())
                    # Convert from 1-based user input to 0-based index
                    start_idx = max(0, min(start, end) - 1)
                    end_idx = min(max_pages - 1, max(start, end) - 1)
                    for p in range(start_idx, end_idx + 1):
                        selected_pages.add(p)
                except ValueError:
                    continue
        else:
            try:
                p_num = int(part)
                idx = p_num - 1
                if 0 <= idx < max_pages:
                    selected_pages.add(idx)
            except ValueError:
                continue

    return sorted(list(selected_pages))


def convert_pdf_to_images(
    pdf_path: str,
    output_directory: str,
    image_format: str = "png",  # png, jpg, webp, tiff, bmp
    dpi: int = 200,
    page_indices: Optional[List[int]] = None,
    page_range_str: Optional[str] = None,
    jpg_quality: int = 90,
    naming_template: str = "{pdf_name}_page_{page:03d}",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> Dict[str, Any]:
    """
    Convert pages of a PDF into high-quality images.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    os.makedirs(output_directory, exist_ok=True)
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    ext = image_format.lower().lstrip('.')
    if ext == 'jpeg':
        ext = 'jpg'

    doc = fitz.open(pdf_path)
    total_doc_pages = len(doc)

    if total_doc_pages == 0:
        doc.close()
        raise ValueError("The selected PDF has no pages.")

    # Determine pages to extract
    if page_indices is not None:
        target_pages = [p for p in page_indices if 0 <= p < total_doc_pages]
    elif page_range_str:
        target_pages = parse_page_range(page_range_str, total_doc_pages)
    else:
        target_pages = list(range(total_doc_pages))

    if not target_pages:
        doc.close()
        raise ValueError("No valid pages selected for conversion.")

    # Scale factor from 72 DPI base
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    generated_files = []
    total_to_convert = len(target_pages)
    today_str = datetime.date.today().strftime('%Y%m%d')

    try:
        for idx, page_num in enumerate(target_pages):
            if cancel_event and cancel_event.is_set():
                doc.close()
                raise InterruptedError("Conversion cancelled by user.")

            user_page_num = page_num + 1
            status_msg = f"Rendering page {user_page_num}/{total_doc_pages} ({idx + 1}/{total_to_convert})..."
            if progress_callback:
                progress_callback(idx, total_to_convert, status_msg)

            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            # Format output filename
            # Support variables: {pdf_name}, {page}, {page_1}, {index}, {date}
            filename_str = naming_template
            filename_str = filename_str.replace("{pdf_name}", pdf_basename)
            filename_str = filename_str.replace("{date}", today_str)
            filename_str = filename_str.replace("{index}", str(idx + 1).zfill(3))
            
            if "{page:03d}" in filename_str:
                filename_str = filename_str.replace("{page:03d}", str(user_page_num).zfill(3))
            elif "{page:02d}" in filename_str:
                filename_str = filename_str.replace("{page:02d}", str(user_page_num).zfill(2))
            else:
                filename_str = filename_str.replace("{page}", str(user_page_num))
                filename_str = filename_str.replace("{page_1}", str(user_page_num))

            out_filename = f"{filename_str}.{ext}"
            out_filepath = os.path.join(output_directory, out_filename)

            # Save image
            if ext in ('png', 'jpg', 'jpeg', 'bmp', 'tiff'):
                if ext in ('jpg', 'jpeg'):
                    # Save via Pillow to enforce custom JPG quality
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img.save(out_filepath, "JPEG", quality=jpg_quality, optimize=True)
                else:
                    pix.save(out_filepath)
            elif ext == 'webp':
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(out_filepath, "WEBP", quality=jpg_quality)
            else:
                pix.save(out_filepath)

            generated_files.append(out_filepath)

        doc.close()

        if progress_callback:
            progress_callback(total_to_convert, total_to_convert, f"Successfully converted {total_to_convert} pages!")

        return {
            "success": True,
            "pdf_name": pdf_basename,
            "output_directory": output_directory,
            "converted_count": total_to_convert,
            "files": generated_files
        }

    except Exception as e:
        if doc and not doc.is_closed:
            doc.close()
        raise e
