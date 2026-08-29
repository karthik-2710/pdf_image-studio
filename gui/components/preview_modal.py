import os
import customtkinter as ctk
from PIL import Image
from typing import Dict, Any, List, Optional
import pymupdf as fitz

from core.file_manager import get_image_metadata, get_pdf_metadata


class PreviewModal(ctk.CTkToplevel):
    """
    Full-size image & PDF page inspector modal with zoom preview and detailed metadata.
    """

    def __init__(
        self,
        parent,
        items: List[Dict[str, Any]],
        current_index: int = 0,
        is_pdf_page: bool = False
    ):
        super().__init__(parent)
        self.items = items
        self.current_index = max(0, min(current_index, len(items) - 1))
        self.is_pdf_page = is_pdf_page

        self.title("🔍 Preview Inspector - Image & PDF Studio")
        self.geometry("960x700")
        self.minsize(750, 550)

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
        header.grid_columnconfigure(1, weight=1)

        self.btn_prev = ctk.CTkButton(
            header,
            text="◀ Previous",
            width=90,
            height=32,
            command=self._prev_item
        )
        self.btn_prev.grid(row=0, column=0, padx=12, pady=8)

        self.title_label = ctk.CTkLabel(
            header,
            text="Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="center"
        )
        self.title_label.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        self.btn_next = ctk.CTkButton(
            header,
            text="Next ▶",
            width=90,
            height=32,
            command=self._next_item
        )
        self.btn_next.grid(row=0, column=2, padx=12, pady=8)

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
                with Image.open(file_path) as full_img:
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
