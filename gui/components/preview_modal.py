import os
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
from typing import Dict, Any, List, Optional, Callable
import pymupdf as fitz

from core.file_manager import get_image_metadata, get_pdf_metadata, load_image_with_exif, rotate_image_file_on_disk


class PreviewModal(ctk.CTkToplevel):
    """
    Full-size image & PDF page inspector modal with zoom preview, detailed metadata,
    and quick rotation & editing tools.
    """

    def __init__(
        self,
        parent,
        items: List[Dict[str, Any]],
        current_index: int = 0,
        is_pdf_page: bool = False,
        on_item_updated: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        super().__init__(parent)
        self.items = items
        self.current_index = max(0, min(current_index, len(items) - 1))
        self.is_pdf_page = is_pdf_page
        self.on_item_updated = on_item_updated

        self.title("🔍 Preview Inspector - Image & PDF Studio")
        self.geometry("980x720")
        self.minsize(780, 560)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        self.preview_ctk_img = None

        self._build_ui()
        self._load_current_item()

        # Keyboard bindings
        self.bind("<Left>", lambda e: self._prev_item())
        self.bind("<Right>", lambda e: self._next_item())
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header Bar
        header = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=("gray85", "gray17"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        self.btn_prev = ctk.CTkButton(
            header,
            text="◀ Previous",
            width=85,
            height=32,
            command=self._prev_item
        )
        self.btn_prev.grid(row=0, column=0, padx=(10, 4), pady=8)

        self.btn_next = ctk.CTkButton(
            header,
            text="Next ▶",
            width=85,
            height=32,
            command=self._next_item
        )
        self.btn_next.grid(row=0, column=1, padx=4, pady=8)

        self.title_label = ctk.CTkLabel(
            header,
            text="Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="center"
        )
        self.title_label.grid(row=0, column=2, padx=10, pady=8, sticky="ew")

        # Quick rotate and edit buttons for images
        if not self.is_pdf_page:
            btn_rot_l = ctk.CTkButton(
                header,
                text="↺ 90°",
                width=55,
                height=32,
                font=ctk.CTkFont(size=12),
                command=lambda: self._quick_rotate(-90)
            )
            btn_rot_l.grid(row=0, column=3, padx=3, pady=8)

            btn_rot_r = ctk.CTkButton(
                header,
                text="↻ 90°",
                width=55,
                height=32,
                font=ctk.CTkFont(size=12),
                command=lambda: self._quick_rotate(90)
            )
            btn_rot_r.grid(row=0, column=4, padx=3, pady=8)

            btn_edit = ctk.CTkButton(
                header,
                text="🎨 Edit...",
                width=75,
                height=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#0288d1", "#0277bd"),
                command=self._open_editor
            )
            btn_edit.grid(row=0, column=5, padx=(3, 10), pady=8)

        # 2. Main Viewport (Image Canvas / Label)
        self.viewport_frame = ctk.CTkFrame(self, fg_color=("gray95", "gray12"), corner_radius=8)
        self.viewport_frame.grid(row=1, column=0, padx=15, pady=(10, 5), sticky="nsew")
        self.viewport_frame.pack_propagate(False)

        self.image_label = ctk.CTkLabel(self.viewport_frame, text="Loading preview...", text_color="gray50")
        self.image_label.pack(expand=True, fill="both")

        # 3. Footer / Metadata Details Bar
        footer = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray88", "gray17"))
        footer.grid(row=2, column=0, padx=15, pady=(5, 12), sticky="ew")
        footer.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.meta_dim = ctk.CTkLabel(footer, text="Resolution: -", font=ctk.CTkFont(size=11, weight="bold"))
        self.meta_dim.grid(row=0, column=0, padx=8, pady=4, sticky="w")

        self.meta_size = ctk.CTkLabel(footer, text="File Size: -", font=ctk.CTkFont(size=11))
        self.meta_size.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        self.meta_fmt = ctk.CTkLabel(footer, text="Format: -", font=ctk.CTkFont(size=11))
        self.meta_fmt.grid(row=0, column=2, padx=8, pady=4, sticky="w")

        self.meta_date = ctk.CTkLabel(footer, text="Modified: -", font=ctk.CTkFont(size=11), text_color="gray50")
        self.meta_date.grid(row=0, column=3, padx=8, pady=4, sticky="e")

        self.meta_path = ctk.CTkLabel(footer, text="Path: -", font=ctk.CTkFont(size=10), text_color="gray50", anchor="w")
        self.meta_path.grid(row=1, column=0, columnspan=4, padx=8, pady=(0, 4), sticky="w")

    def _prev_item(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_item()

    def _next_item(self):
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self._load_current_item()

    def _quick_rotate(self, degrees: int):
        if self.is_pdf_page or not self.items:
            return
        item = self.items[self.current_index]
        file_path = item.get("path", "")
        try:
            rotate_image_file_on_disk(file_path, (degrees % 360))
            meta = get_image_metadata(file_path)
            item.update(meta)
            self._load_current_item()
            if self.on_item_updated:
                self.on_item_updated(item)
        except Exception as e:
            messagebox.showerror("Rotate Failed", f"Could not rotate image file:\n{e}")

    def _open_editor(self):
        if self.is_pdf_page or not self.items:
            return
        from gui.components.editor_modal import EditorModal
        item = self.items[self.current_index]
        
        def on_saved(updated_item, edited_img):
            self._load_current_item()
            if self.on_item_updated:
                self.on_item_updated(updated_item)

        EditorModal(self, item_data=item, on_save_callback=on_saved)

    def _load_current_item(self):
        if not self.items or self.current_index >= len(self.items):
            return

        item = self.items[self.current_index]
        total = len(self.items)
        idx_display = self.current_index + 1

        self.btn_prev.configure(state="normal" if self.current_index > 0 else "disabled")
        self.btn_next.configure(state="normal" if self.current_index < total - 1 else "disabled")

        if self.is_pdf_page:
            pdf_path = item.get("pdf_path", "")
            page_idx = item.get("page_index", 0)
            filename = os.path.basename(pdf_path)
            self.title_label.configure(text=f"{filename} — Page {page_idx + 1} ({idx_display}/{total})")

            try:
                doc = fitz.open(pdf_path)
                page = doc[page_idx]
                rect = page.rect
                # Render high-quality 150 DPI preview
                zoom = 150 / 72.0
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()

                # Scale to fit window viewport (max approx 880x520)
                pil_img.thumbnail((880, 520), Image.Resampling.LANCZOS)
                self.preview_ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(pil_img.width, pil_img.height))
                self.image_label.configure(image=self.preview_ctk_img, text="")

                self.meta_dim.configure(text=f"Dimensions: {int(rect.width)} × {int(rect.height)} pt")
                self.meta_size.configure(text=f"Page: {page_idx + 1} of {total}")
                self.meta_fmt.configure(text="PDF Document Page")
                self.meta_date.configure(text="")
                self.meta_path.configure(text=f"Source PDF: {pdf_path}")
            except Exception as e:
                self.image_label.configure(image=None, text=f"Error rendering PDF page: {e}")

        else:
            file_path = item.get("path", "")
            filename = item.get("filename", os.path.basename(file_path))
            self.title_label.configure(text=f"{filename} ({idx_display}/{total})")

            if not os.path.exists(file_path):
                self.image_label.configure(image=None, text="File does not exist.")
                return

            try:
                meta = get_image_metadata(file_path)
                full_img = load_image_with_exif(file_path)
                # Convert for safe viewing
                display_img = full_img.copy()
                if display_img.mode not in ('RGB', 'RGBA'):
                    display_img = display_img.convert('RGBA')

                display_img.thumbnail((880, 520), Image.Resampling.LANCZOS)
                self.preview_ctk_img = ctk.CTkImage(
                    light_image=display_img,
                    dark_image=display_img,
                    size=(display_img.width, display_img.height)
                )
                self.image_label.configure(image=self.preview_ctk_img, text="")

                self.meta_dim.configure(text=f"Resolution: {meta['dimensions']} px")
                self.meta_size.configure(text=f"Size: {meta['size_formatted']}")
                self.meta_fmt.configure(text=f"Format: {meta['format']} ({meta['mode']})")
                self.meta_date.configure(text=f"Modified: {meta['modified_time']}")
                self.meta_path.configure(text=f"Path: {file_path}")

            except Exception as e:
                self.image_label.configure(image=None, text=f"Error loading image: {e}")
