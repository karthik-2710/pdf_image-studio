import os
import re
import datetime
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pymupdf as fitz

SUPPORTED_IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp', '.bmp', 
    '.tiff', '.tif', '.gif', '.ico', '.jfif', '.ppm', '.pnm'
}
SUPPORTED_PDF_EXTENSIONS = {'.pdf'}


def is_valid_image_file(file_path: str) -> bool:
    """Check if file has a supported image extension and exists."""
    if not os.path.isfile(file_path):
        return False
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_IMAGE_EXTENSIONS


def is_valid_pdf_file(file_path: str) -> bool:
    """Check if file has a supported PDF extension and exists."""
    if not os.path.isfile(file_path):
        return False
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_PDF_EXTENSIONS


def format_file_size(size_in_bytes: int) -> str:
    """Convert bytes to human-readable string (KB, MB, GB)."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"


def load_image_with_exif(file_path: str) -> Image.Image:
    """
    Load an image from disk and automatically apply EXIF orientation transposition
    so it matches Windows Explorer / camera orientation parity.
    """
    img = Image.open(file_path)
    # Apply EXIF transpose so rotations done in Windows File Explorer or cameras are rendered correctly
    img = ImageOps.exif_transpose(img)
    return img


def get_image_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from an image file with correct EXIF orientation dimensions."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = os.stat(file_path)
    size_bytes = stat.st_size
    mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    width, height = 0, 0
    mode = "Unknown"
    format_name = ext.replace('.', '').upper()

    try:
        with load_image_with_exif(file_path) as img:
            width, height = img.size
            mode = img.mode
            if getattr(img, "format", None):
                format_name = img.format
    except Exception as e:
        pass

    return {
        "path": file_path,
        "filename": filename,
        "extension": ext,
        "size_bytes": size_bytes,
        "size_formatted": format_file_size(size_bytes),
        "width": width,
        "height": height,
        "dimensions": f"{width} × {height}" if width and height else "Unknown",
        "mode": mode,
        "format": format_name,
        "modified_time": mod_time
    }


def get_pdf_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata and page count from a PDF file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = os.stat(file_path)
    size_bytes = stat.st_size
    mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    filename = os.path.basename(file_path)

    page_count = 0
    title = ""
    author = ""
    first_page_dims = "Unknown"

    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        meta = doc.metadata or {}
        title = meta.get("title", "") or ""
        author = meta.get("author", "") or ""
        if page_count > 0:
            first_page = doc[0]
            rect = first_page.rect
            first_page_dims = f"{int(rect.width)} × {int(rect.height)} pt"
        doc.close()
    except Exception as e:
        pass

    return {
        "path": file_path,
        "filename": filename,
        "size_bytes": size_bytes,
        "size_formatted": format_file_size(size_bytes),
        "page_count": page_count,
        "title": title,
        "author": author,
        "dimensions": first_page_dims,
        "modified_time": mod_time
    }


def generate_image_thumbnail(file_path: str, max_size: Tuple[int, int] = (160, 160)) -> Optional[Image.Image]:
    """Generate a Pillow thumbnail preserving aspect ratio and EXIF orientation."""
    try:
        img = load_image_with_exif(file_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')
        return img
    except Exception:
        return None


def apply_image_adjustments(
    img: Image.Image,
    rotation: int = 0,               # 0, 90, 180, 270 (clockwise)
    flip_h: bool = False,
    flip_v: bool = False,
    crop_box: Optional[Tuple[int, int, int, int]] = None, # (left, top, right, bottom)
    brightness: float = 1.0,        # 1.0 is original
    contrast: float = 1.0,          # 1.0 is original
    sharpness: float = 1.0,         # 1.0 is original
    filter_mode: str = "normal"     # 'normal', 'grayscale', 'document_scan', 'warm', 'cool'
) -> Image.Image:
    """
    Apply a complete pipeline of image edits: rotation, flipping, cropping,
    brightness/contrast/sharpness enhancement, and document scanning filters.
    """
    res = img.copy()

    # 1. Cropping
    if crop_box:
        l, t, r, b = crop_box
        w, h = res.size
        # Clamp bounds
        l = max(0, min(l, w - 1))
        t = max(0, min(t, h - 1))
        r = max(l + 1, min(r, w))
        b = max(t + 1, min(b, h))
        res = res.crop((l, t, r, b))

    # 2. Rotation (Clockwise)
    norm_rot = rotation % 360
    if norm_rot == 90:
        res = res.transpose(Image.Transpose.ROTATE_270)
    elif norm_rot == 180:
        res = res.transpose(Image.Transpose.ROTATE_180)
    elif norm_rot == 270:
        res = res.transpose(Image.Transpose.ROTATE_90)

    # 3. Flips
    if flip_h:
        res = res.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if flip_v:
        res = res.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    # 4. Filters & Enhancements
    if filter_mode == "grayscale":
        res = ImageOps.grayscale(res).convert("RGB")
    elif filter_mode == "document_scan":
        # Enhanced Black & White document scan: convert to grayscale, boost contrast, sharpen
        gray = ImageOps.grayscale(res)
        # Apply autocontrast
        enhanced_gray = ImageOps.autocontrast(gray, cutoff=2)
        # Sharpness boost
        enhancer = ImageEnhance.Sharpness(enhanced_gray)
        sharp = enhancer.enhance(1.8)
        # Contrast boost
        c_enhancer = ImageEnhance.Contrast(sharp)
        res = c_enhancer.enhance(1.5).convert("RGB")
    elif filter_mode == "warm":
        if res.mode != "RGB":
            res = res.convert("RGB")
        r, g, b = res.split()
        r = r.point(lambda i: min(255, int(i * 1.1)))
        b = b.point(lambda i: int(i * 0.9))
        res = Image.merge("RGB", (r, g, b))
    elif filter_mode == "cool":
        if res.mode != "RGB":
            res = res.convert("RGB")
        r, g, b = res.split()
        r = r.point(lambda i: int(i * 0.9))
        b = b.point(lambda i: min(255, int(i * 1.15)))
        res = Image.merge("RGB", (r, g, b))

    # 5. Brightness adjustment
    if abs(brightness - 1.0) > 0.01:
        enhancer = ImageEnhance.Brightness(res)
        res = enhancer.enhance(brightness)

    # 6. Contrast adjustment
    if abs(contrast - 1.0) > 0.01:
        enhancer = ImageEnhance.Contrast(res)
        res = enhancer.enhance(contrast)

    # 7. Sharpness adjustment
    if abs(sharpness - 1.0) > 0.01:
        enhancer = ImageEnhance.Sharpness(res)
        res = enhancer.enhance(sharpness)

    return res


def save_image_to_disk(img: Image.Image, target_path: str, quality: int = 95) -> str:
    """
    Save modified Pillow image to disk with appropriate format settings and atomic write safety.
    """
    ext = os.path.splitext(target_path)[1].lower()
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    # Prepare image mode for format
    save_img = img
    if ext in ('.jpg', '.jpeg', '.jfif'):
        if save_img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', save_img.size, (255, 255, 255))
            mask = save_img.split()[3] if save_img.mode == 'RGBA' else None
            bg.paste(save_img, mask=mask)
            save_img = bg
        elif save_img.mode != 'RGB':
            save_img = save_img.convert('RGB')
        save_img.save(target_path, format="JPEG", quality=quality, optimize=True)
    elif ext == '.png':
        save_img.save(target_path, format="PNG", optimize=True)
    elif ext == '.webp':
        save_img.save(target_path, format="WEBP", quality=quality)
    elif ext in ('.tiff', '.tif'):
        save_img.save(target_path, format="TIFF")
    elif ext == '.bmp':
        if save_img.mode not in ('RGB', 'L'):
            save_img = save_img.convert('RGB')
        save_img.save(target_path, format="BMP")
    else:
        # Default fallback
        save_img.save(target_path)

    return target_path


def rotate_image_file_on_disk(file_path: str, degrees: int = 90) -> str:
    """
    Directly rotate an image file on disk by specified degrees (e.g. 90, 180, 270)
    and save it back to disk.
    """
    img = load_image_with_exif(file_path)
    rotated = apply_image_adjustments(img, rotation=degrees)
    save_image_to_disk(rotated, file_path)
    return file_path


def generate_pdf_page_thumbnail(pdf_path: str, page_number: int = 0, max_size: Tuple[int, int] = (160, 160)) -> Optional[Image.Image]:
    """Render a thumbnail of a specific PDF page using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        if page_number < 0 or page_number >= len(doc):
            doc.close()
            return None
        page = doc[page_number]
        
        # Calculate scale to fit max_size
        rect = page.rect
        scale = min(max_size[0] / rect.width, max_size[1] / rect.height) if rect.width and rect.height else 1.0
        matrix = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except Exception:
        return None


def sanitize_filename(name: str) -> str:
    """Remove invalid filesystem characters from filename."""
    # Replace Windows invalid filename chars: < > : " / \ | ? *
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', name).strip()
    return cleaned if cleaned else "unnamed"


def safe_rename_file(old_path: str, new_name_with_ext: str) -> str:
    """
    Safely rename a file on disk.
    Returns the new full path.
    """
    if not os.path.exists(old_path):
        raise FileNotFoundError(f"Source file does not exist: {old_path}")
    
    directory = os.path.dirname(old_path)
    clean_name = sanitize_filename(new_name_with_ext)
    new_path = os.path.join(directory, clean_name)

    if new_path == old_path:
        return old_path

    # If destination exists, generate a unique variant
    if os.path.exists(new_path):
        name_part, ext_part = os.path.splitext(clean_name)
        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(directory, f"{name_part}_{counter}{ext_part}")
            counter += 1

    os.rename(old_path, new_path)
    return new_path


def generate_batch_rename_plan(
    file_paths: List[str],
    pattern_mode: str,  # 'prefix_suffix', 'find_replace', 'numbering', 'custom_template'
    prefix: str = "",
    suffix: str = "",
    find_text: str = "",
    replace_text: str = "",
    start_number: int = 1,
    digits_padding: int = 3,
    template: str = "{name}_{index}"  # available variables: {name}, {index}, {date}
) -> List[Dict[str, str]]:
    """
    Compute proposed old_path -> new_name rename plan for previewing in UI.
    """
    plan = []
    for idx, path in enumerate(file_paths):
        filename = os.path.basename(path)
        base_name, ext = os.path.splitext(filename)
        current_num = start_number + idx
        num_str = str(current_num).zfill(digits_padding)

        if pattern_mode == 'prefix_suffix':
            new_base = f"{prefix}{base_name}{suffix}"
        elif pattern_mode == 'find_replace':
            if find_text:
                new_base = base_name.replace(find_text, replace_text)
            else:
                new_base = base_name
        elif pattern_mode == 'numbering':
            prefix_part = f"{prefix}_" if prefix else ""
            suffix_part = f"_{suffix}" if suffix else ""
            new_base = f"{prefix_part}{num_str}{suffix_part}"
        elif pattern_mode == 'custom_template':
            today_str = datetime.date.today().strftime('%Y%m%d')
            new_base = template.replace("{name}", base_name)
            new_base = new_base.replace("{index}", num_str)
            new_base = new_base.replace("{date}", today_str)
        else:
            new_base = base_name

        new_name = sanitize_filename(f"{new_base}{ext}")
        plan.append({
            "old_path": path,
            "old_name": filename,
            "new_name": new_name,
            "directory": os.path.dirname(path)
        })
    return plan


def apply_batch_rename(plan: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Execute batch renaming with two-step safety to avoid collisions.
    Returns list of results with updated paths.
    """
    results = []
    temp_rename_map = []
    
    # Step 1: Rename to temporary names to avoid collision loops
    for item in plan:
        old_path = item["old_path"]
        new_name = item["new_name"]
        directory = item["directory"]
        
        if not os.path.exists(old_path):
            results.append({"old_path": old_path, "new_path": old_path, "success": False, "error": "File not found"})
            continue
            
        target_path = os.path.join(directory, new_name)
        if old_path == target_path:
            results.append({"old_path": old_path, "new_path": old_path, "success": True, "error": None})
            continue

        temp_name = f"__tmp_rename_{os.urandom(6).hex()}_{os.path.basename(old_path)}"
        temp_path = os.path.join(directory, temp_name)
        
        try:
            os.rename(old_path, temp_path)
            temp_rename_map.append((temp_path, target_path, old_path))
        except Exception as e:
            results.append({"old_path": old_path, "new_path": old_path, "success": False, "error": str(e)})

    # Step 2: Rename from temp names to final targets
    for temp_path, target_path, original_old_path in temp_rename_map:
        try:
            # Check if target exists
            final_path = target_path
            if os.path.exists(final_path):
                dirname = os.path.dirname(final_path)
                basename, ext = os.path.splitext(os.path.basename(final_path))
                c = 1
                while os.path.exists(final_path):
                    final_path = os.path.join(dirname, f"{basename}_{c}{ext}")
                    c += 1
            os.rename(temp_path, final_path)
            results.append({"old_path": original_old_path, "new_path": final_path, "success": True, "error": None})
        except Exception as e:
            # Try to restore original name
            try:
                os.rename(temp_path, original_old_path)
            except Exception:
                pass
            results.append({"old_path": original_old_path, "new_path": original_old_path, "success": False, "error": str(e)})

    return results


def safe_delete_file(file_path: str) -> bool:
    """Safely delete a file from disk with error handling."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        raise OSError(f"Could not delete file {file_path}: {e}")
