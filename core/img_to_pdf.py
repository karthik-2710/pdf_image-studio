import os
import io
import threading
from typing import List, Optional, Callable, Dict, Any, Tuple
from PIL import Image, ImageOps
import pymupdf as fitz

# Page dimensions in points (72 points = 1 inch)
PAGE_SIZES = {
    "a4": (595.28, 841.89),       # 210 x 297 mm
    "letter": (612.0, 792.0),     # 8.5 x 11 inches
    "legal": (612.0, 1008.0),     # 8.5 x 14 inches
    "a3": (841.89, 1190.55),     # 297 x 420 mm
    "a5": (419.53, 595.28),      # 148 x 210 mm
}

MARGINS = {
    "none": 0.0,
    "small": 18.0,    # ~0.25 in
    "normal": 36.0,   # ~0.5 in
    "large": 54.0     # ~0.75 in
}


# Compression preset configurations
QUALITY_PRESETS = {
    "lossless": {"quality": None, "max_dim": None, "subsampling": None},
    "high": {"quality": 90, "max_dim": None, "subsampling": 0},
    "medium": {"quality": 75, "max_dim": 2560, "subsampling": 1},
    "low": {"quality": 50, "max_dim": 1920, "subsampling": 2},
    "extreme": {"quality": 38, "max_dim": 1600, "subsampling": 2},         # Extreme compression (85-95% smaller, crisp & clear)
    "ultra_extreme": {"quality": 28, "max_dim": 1200, "subsampling": 2},   # Ultra compact (Smallest possible, great for email)
}


def prepare_image_for_pdf(
    image_path: str,
    quality_preset: str = "high",
    custom_max_dim: Optional[int] = None
) -> Tuple[bytes, int, int]:
    """
    Load image, apply EXIF orientation parity, smart high-quality downscaling, and compression.
    """
    cfg = QUALITY_PRESETS.get(quality_preset, QUALITY_PRESETS["high"])
    q = cfg["quality"]
    max_dim = custom_max_dim if custom_max_dim is not None else cfg["max_dim"]
    subsampling = cfg.get("subsampling", 2)

    with Image.open(image_path) as raw_img:
        # Auto transpose based on Windows / EXIF orientation
        img = ImageOps.exif_transpose(raw_img)
        # Check if downscaling is needed
        orig_w, orig_h = img.size
        working_img = img

        if max_dim and max(orig_w, orig_h) > max_dim:
            scale = max_dim / float(max(orig_w, orig_h))
            new_w = max(1, int(orig_w * scale))
            new_h = max(1, int(orig_h * scale))
            working_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        width, height = working_img.size

        # If quality is lossless, preserve original image or clean RGB/PNG
        if q is None or quality_preset == "lossless":
            # For RGBA or P modes, convert to RGB for standard PDF embedding
            if working_img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', working_img.size, (255, 255, 255))
                if working_img.mode == 'RGBA':
                    background.paste(working_img, mask=working_img.split()[3])
                else:
                    background.paste(working_img, mask=working_img.split()[1])
                buffer = io.BytesIO()
                background.save(buffer, format='PNG', optimize=True)
                return buffer.getvalue(), width, height
            elif working_img.mode != 'RGB':
                rgb_img = working_img.convert('RGB')
                buffer = io.BytesIO()
                rgb_img.save(buffer, format='PNG', optimize=True)
                return buffer.getvalue(), width, height
            else:
                # If image was not resized, we can use original bytes directly
                if working_img is img:
                    with open(image_path, 'rb') as f:
                        return f.read(), width, height
                else:
                    buffer = io.BytesIO()
                    working_img.save(buffer, format='JPEG', quality=95, optimize=True)
                    return buffer.getvalue(), width, height
        else:
            # Convert to RGB with white background if transparent
            if working_img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', working_img.size, (255, 255, 255))
                mask = working_img.split()[3] if working_img.mode == 'RGBA' else working_img.split()[1]
                background.paste(working_img, mask=mask)
                rgb_img = background
            elif working_img.mode != 'RGB':
                rgb_img = working_img.convert('RGB')
            else:
                rgb_img = working_img

            buffer = io.BytesIO()
            save_kwargs = {
                "format": "JPEG",
                "quality": q,
                "optimize": True,
                "progressive": True
            }
            if subsampling is not None:
                save_kwargs["subsampling"] = subsampling

            rgb_img.save(buffer, **save_kwargs)
            return buffer.getvalue(), width, height


def calculate_page_rect(
    img_w: int,
    img_h: int,
    page_size_mode: str = "fit_image",  # fit_image, a4, letter, etc.
    orientation: str = "auto",          # auto, portrait, landscape
    margin_mode: str = "none"           # none, small, normal, large
) -> Tuple[fitz.Rect, fitz.Rect]:
    """
    Calculate (page_rect, image_rect) for placing image on PDF page.
    Returns:
        page_rect: Bounding box of the entire PDF page
        image_rect: Bounding box where the image will be positioned on the page
    """
    margin = MARGINS.get(margin_mode, 0.0)

    if page_size_mode == "fit_image":
        # Page size exactly matches the image dimensions
        p_w = float(img_w) + (2 * margin)
        p_h = float(img_h) + (2 * margin)
        page_rect = fitz.Rect(0, 0, p_w, p_h)
        image_rect = fitz.Rect(margin, margin, p_w - margin, p_h - margin)
        return page_rect, image_rect

    # Standard paper sizes (A4, Letter, etc.)
    base_w, base_h = PAGE_SIZES.get(page_size_mode, PAGE_SIZES["a4"])
    
    # Determine orientation
    if orientation == "auto":
        is_img_landscape = img_w > img_h
        if is_img_landscape:
            p_w, p_h = max(base_w, base_h), min(base_w, base_h)
        else:
            p_w, p_h = min(base_w, base_h), max(base_w, base_h)
    elif orientation == "landscape":
        p_w, p_h = max(base_w, base_h), min(base_w, base_h)
    else:  # portrait
        p_w, p_h = min(base_w, base_h), max(base_w, base_h)

    page_rect = fitz.Rect(0, 0, p_w, p_h)
    
    # Available area inside margins
    avail_w = p_w - (2 * margin)
    avail_h = p_h - (2 * margin)

    # Scale image to fit inside available area preserving aspect ratio
    scale = min(avail_w / img_w, avail_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale

    # Center image in page
    offset_x = margin + (avail_w - draw_w) / 2.0
    offset_y = margin + (avail_h - draw_h) / 2.0

    image_rect = fitz.Rect(offset_x, offset_y, offset_x + draw_w, offset_y + draw_h)
    return page_rect, image_rect


def convert_images_to_single_pdf(
    image_paths: List[str],
    output_pdf_path: str,
    page_size: str = "fit_image",
    orientation: str = "auto",
    margin: str = "none",
    quality: str = "high",
    custom_max_dim: Optional[int] = None,
    title: str = "",
    author: str = "Image & PDF Converter Studio",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> Dict[str, Any]:
    """
    Convert a list of images into a single combined PDF document.
    """
    if not image_paths:
        raise ValueError("No images provided for conversion.")

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    doc = fitz.open()

    total_images = len(image_paths)

    try:
        for idx, img_path in enumerate(image_paths):
            if cancel_event and cancel_event.is_set():
                doc.close()
                raise InterruptedError("Conversion cancelled by user.")

            filename = os.path.basename(img_path)
            if progress_callback:
                progress_callback(idx, total_images, f"Processing page {idx + 1}/{total_images}: {filename}")

            # Read, downscale, and compress image data
            img_bytes, img_w, img_h = prepare_image_for_pdf(
                img_path,
                quality_preset=quality,
                custom_max_dim=custom_max_dim
            )
            
            # Compute page layout
            page_rect, img_rect = calculate_page_rect(
                img_w=img_w,
                img_h=img_h,
                page_size_mode=page_size,
                orientation=orientation,
                margin_mode=margin
            )

            # Create page and insert image
            page = doc.new_page(width=page_rect.width, height=page_rect.height)
            page.insert_image(img_rect, stream=img_bytes)

        if cancel_event and cancel_event.is_set():
            doc.close()
            raise InterruptedError("Conversion cancelled by user.")

        if progress_callback:
            progress_callback(total_images, total_images, "Finalizing and optimizing PDF...")

        # Set document metadata
        doc.set_metadata({
            "title": title or os.path.splitext(os.path.basename(output_pdf_path))[0],
            "author": author,
            "creator": "Image & PDF Converter Studio",
            "producer": "PyMuPDF"
        })

        # Save with maximum garbage collection and stream deflation
        doc.save(
            output_pdf_path,
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            clean=True
        )
        doc.close()

        file_size = os.path.getsize(output_pdf_path)

        if progress_callback:
            progress_callback(total_images, total_images, "Completed successfully!")

        return {
            "success": True,
            "output_path": output_pdf_path,
            "pages_count": total_images,
            "file_size": file_size
        }

    except Exception as e:
        if doc and not doc.is_closed:
            doc.close()
        raise e


def convert_images_to_individual_pdfs(
    image_paths: List[str],
    output_directory: str,
    page_size: str = "fit_image",
    orientation: str = "auto",
    margin: str = "none",
    quality: str = "high",
    custom_max_dim: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> List[Dict[str, Any]]:
    """
    Convert each image in the list to its own individual PDF file in the output directory.
    """
    if not image_paths:
        raise ValueError("No images provided for conversion.")

    os.makedirs(output_directory, exist_ok=True)
    results = []
    total_images = len(image_paths)

    for idx, img_path in enumerate(image_paths):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Conversion cancelled by user.")

        filename = os.path.basename(img_path)
        base_name, _ = os.path.splitext(filename)
        out_pdf_path = os.path.join(output_directory, f"{base_name}.pdf")

        if progress_callback:
            progress_callback(idx, total_images, f"Converting {idx + 1}/{total_images}: {filename}")

        res = convert_images_to_single_pdf(
            image_paths=[img_path],
            output_pdf_path=out_pdf_path,
            page_size=page_size,
            orientation=orientation,
            margin=margin,
            quality=quality,
            custom_max_dim=custom_max_dim,
            title=base_name,
            cancel_event=cancel_event
        )
        results.append(res)

    if progress_callback:
        progress_callback(total_images, total_images, f"All {total_images} PDFs generated successfully!")

    return results
