import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import List, Dict, Any, Optional
import pymupdf as fitz

from core.file_manager import get_pdf_metadata, is_valid_pdf_file
from core.pdf_to_img import convert_pdf_to_images, parse_page_range
from gui.theme import (
    BG_CARD,
    BG_CARD_ALT,
    BG_CONTAINER,
    BG_INPUT,
    BORDER_CARD,
    BORDER_SUBTLE,
    BORDER_ACTIVE,
    TEXT_MAIN,
    TEXT_MUTED,
    TEXT_DIM,
    TEXT_INVERSE,
    ACCENT_EMERALD,
    ACCENT_EMERALD_HOVER,
    ACCENT_EMERALD_ACTIVE,
    ACCENT_TEAL,
    ACCENT_TEAL_HOVER,
    ACCENT_AMBER,
    ACCENT_ROSE,
    BTN_NEUTRAL_BG,
    BTN_NEUTRAL_HOVER,
    BTN_NEUTRAL_TEXT,
    BTN_DANGER_BG,
    RADIUS_CONTAINER,
    RADIUS_CARD,
    RADIUS_CONTROL,
    RADIUS_BTN,
    RADIUS_INPUT,
    RADIUS_PILL,
    RADIUS_BADGE,
    font_h1,
    font_h2,
    font_title,
    font_body,
    font_body_bold,
    font_caption,
    font_caption_bold,
    font_badge
)
from gui.components.item_card import ItemCard
from gui.components.preview_modal import PreviewModal


class PdfToImgTab(ctk.CTkFrame):
    """
    Complete PDF to Images Converter Workspace with visual page browser,
    page range selection, DPI resolution presets, and high-speed rendering.
    Designed with unified design system tokens and responsive SaaS layout.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.current_pdf_path: Optional[str] = None
        self.current_pdf_meta: Optional[Dict[str, Any]] = None
        self.pages_queue: List[Dict[str, Any]] = []
        self.conversion_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.last_output_dir: Optional[str] = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------------------------------------------
        # 1. Top File Selection & Quick Range Toolbar
        # ----------------------------------------------------
        toolbar = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_CONTAINER,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        toolbar.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        btn_select_pdf = ctk.CTkButton(
            toolbar,
            text="📄 Select PDF File",
            width=135,
            height=34,
            font=font_caption_bold(),
            fg_color=ACCENT_EMERALD,
            hover_color=ACCENT_EMERALD_HOVER,
            text_color=TEXT_INVERSE,
            corner_radius=RADIUS_BTN,
            command=self._choose_pdf_file
        )
        btn_select_pdf.pack(side="left", padx=(12, 6), pady=8)

        # Quick Range presets
        btn_all = ctk.CTkButton(
            toolbar,
            text="All Pages",
            width=75,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=lambda: self._set_all_pages(True)
        )
        btn_all.pack(side="left", padx=3, pady=8)

        btn_none = ctk.CTkButton(
            toolbar,
            text="Deselect All",
            width=85,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=lambda: self._set_all_pages(False)
        )
        btn_none.pack(side="left", padx=3, pady=8)

        btn_odd = ctk.CTkButton(
            toolbar,
            text="Odd Pages",
            width=80,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._select_odd_pages
        )
        btn_odd.pack(side="left", padx=3, pady=8)

        btn_even = ctk.CTkButton(
            toolbar,
            text="Even Pages",
            width=85,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._select_even_pages
        )
        btn_even.pack(side="left", padx=3, pady=8)

        # Custom Range Input box
        ctk.CTkLabel(
            toolbar,
            text="Range:",
            font=font_caption(),
            text_color=TEXT_MUTED
        ).pack(side="left", padx=(10, 4))

        self.entry_range = ctk.CTkEntry(
            toolbar,
            placeholder_text="e.g. 1-3, 5, 8",
            width=120,
            height=32,
            font=font_caption(),
            fg_color=BG_INPUT,
            border_color=BORDER_SUBTLE,
            corner_radius=RADIUS_INPUT
        )
        self.entry_range.pack(side="left", padx=3, pady=8)

        btn_apply_range = ctk.CTkButton(
            toolbar,
            text="Apply",
            width=60,
            height=32,
            font=font_caption_bold(),
            fg_color=ACCENT_TEAL,
            hover_color=ACCENT_TEAL_HOVER,
            text_color=TEXT_INVERSE,
            corner_radius=RADIUS_BTN,
            command=self._apply_custom_range
        )
        btn_apply_range.pack(side="left", padx=3, pady=8)

        # ----------------------------------------------------
        # 2. Main Split Workspace (Page Cards Grid + Export Settings)
        # ----------------------------------------------------
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=1, column=0, padx=16, pady=4, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=3)  # Page Browser (left)
        workspace.grid_columnconfigure(1, weight=1)  # Options Panel (right)
        workspace.grid_rowconfigure(0, weight=1)

        # LEFT: Scrollable Pages View Container
        pages_container = ctk.CTkFrame(
            workspace,
            corner_radius=RADIUS_CONTAINER,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        pages_container.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        pages_container.grid_rowconfigure(1, weight=1)
        pages_container.grid_columnconfigure(0, weight=1)

        # PDF Info Header Strip
        self.pdf_info_strip = ctk.CTkFrame(
            pages_container,
            height=44,
            fg_color=BG_CARD_ALT,
            corner_radius=RADIUS_CONTROL,
            border_width=1,
            border_color=BORDER_CARD
        )
        self.pdf_info_strip.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.lbl_pdf_title = ctk.CTkLabel(
            self.pdf_info_strip,
            text="No PDF Loaded",
            font=font_title(),
            text_color=TEXT_MAIN,
            anchor="w"
        )
        self.lbl_pdf_title.pack(side="left", padx=12, pady=6)

        self.lbl_pdf_details = ctk.CTkLabel(
            self.pdf_info_strip,
            text="",
            font=font_caption(),
            text_color=TEXT_MUTED
        )
        self.lbl_pdf_details.pack(side="right", padx=12, pady=6)

        # Scrollable Frame for Page Cards
        self.cards_scroll = ctk.CTkScrollableFrame(pages_container, fg_color="transparent")
        self.cards_scroll.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Empty State Placeholder
        self._render_empty_state()

        # RIGHT: Image Export Settings Panel
        settings_panel = ctk.CTkScrollableFrame(
            workspace,
            corner_radius=RADIUS_CONTAINER,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        settings_panel.grid(row=0, column=1, sticky="nsew")
        settings_panel.grid_columnconfigure(0, weight=1)

        # Section Header
        ctk.CTkLabel(
            settings_panel,
            text="⚙ Export Settings",
            font=font_h1(),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=12, pady=(12, 10))

        # Target Image Format
        fmt_card = ctk.CTkFrame(
            settings_panel,
            corner_radius=RADIUS_CARD,
            fg_color=BG_CARD_ALT,
            border_width=1,
            border_color=BORDER_CARD
        )
        fmt_card.pack(fill="x", padx=6, pady=5)

        ctk.CTkLabel(
            fmt_card,
            text="Image Format",
            font=font_caption_bold(),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self.opt_format = ctk.CTkOptionMenu(
            fmt_card,
            values=[
                "PNG (Lossless / High Quality)",
                "JPG (Photo / Compact)",
                "WEBP (Modern Compressed)",
                "TIFF (Archival / Uncompressed)",
                "BMP (Raw)"
            ],
            height=32,
            font=font_caption(),
            fg_color=BG_INPUT,
            text_color=TEXT_MAIN,
            button_color=BORDER_SUBTLE,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT,
            command=self._on_format_changed
        )
        self.opt_format.set("PNG (Lossless / High Quality)")
        self.opt_format.pack(fill="x", padx=10, pady=(0, 10))

        # Resolution / DPI
        dpi_card = ctk.CTkFrame(
            settings_panel,
            corner_radius=RADIUS_CARD,
            fg_color=BG_CARD_ALT,
            border_width=1,
            border_color=BORDER_CARD
        )
        dpi_card.pack(fill="x", padx=6, pady=5)

        ctk.CTkLabel(
            dpi_card,
            text="Resolution / DPI",
            font=font_caption_bold(),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self.opt_dpi = ctk.CTkOptionMenu(
            dpi_card,
            values=[
                "300 DPI (High Resolution / Print Quality)",
                "150 DPI (Standard Screen Quality)",
                "200 DPI (Crisp Presentation)",
                "72 DPI (Web Draft / Small Size)",
                "600 DPI (Ultra High Precision)"
            ],
            height=32,
            font=font_caption(),
            fg_color=BG_INPUT,
            text_color=TEXT_MAIN,
            button_color=BORDER_SUBTLE,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT
        )
        self.opt_dpi.set("300 DPI (High Resolution / Print Quality)")
        self.opt_dpi.pack(fill="x", padx=10, pady=(0, 10))

        # JPG Quality Slider
        qual_card = ctk.CTkFrame(
            settings_panel,
            corner_radius=RADIUS_CARD,
            fg_color=BG_CARD_ALT,
            border_width=1,
            border_color=BORDER_CARD
        )
        qual_card.pack(fill="x", padx=6, pady=5)

        self.lbl_quality = ctk.CTkLabel(
            qual_card,
            text="JPG / WEBP Quality (90%):",
            font=font_caption_bold(),
            text_color=TEXT_MAIN
        )
        self.lbl_quality.pack(anchor="w", padx=10, pady=(8, 4))

        self.slider_quality = ctk.CTkSlider(
            qual_card,
            from_=10,
            to=100,
            number_of_steps=18,
            progress_color=ACCENT_EMERALD,
            button_color=ACCENT_EMERALD,
            button_hover_color=ACCENT_EMERALD_HOVER,
            command=self._on_slider_quality
        )
        self.slider_quality.set(90)
        self.slider_quality.pack(fill="x", padx=10, pady=(0, 10))

        # Output Naming Template
        name_card = ctk.CTkFrame(
            settings_panel,
            corner_radius=RADIUS_CARD,
            fg_color=BG_CARD_ALT,
            border_width=1,
            border_color=BORDER_CARD
        )
        name_card.pack(fill="x", padx=6, pady=5)

        ctk.CTkLabel(
            name_card,
            text="Naming Template",
            font=font_caption_bold(),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self.entry_naming = ctk.CTkEntry(
            name_card,
            placeholder_text="{pdf_name}_page_{page:03d}",
            height=32,
            font=font_caption(),
            fg_color=BG_INPUT,
            border_color=BORDER_SUBTLE,
            corner_radius=RADIUS_INPUT
        )
        self.entry_naming.insert(0, "{pdf_name}_page_{page:03d}")
        self.entry_naming.pack(fill="x", padx=10, pady=(0, 2))

        ctk.CTkLabel(
            name_card,
            text="Tags: {pdf_name}, {page:03d}, {page}, {date}",
            font=font_badge(),
            text_color=TEXT_DIM
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # Destination Folder Picker
        dest_card = ctk.CTkFrame(
            settings_panel,
            corner_radius=RADIUS_CARD,
            fg_color=BG_CARD_ALT,
            border_width=1,
            border_color=BORDER_CARD
        )
        dest_card.pack(fill="x", padx=6, pady=5)

        ctk.CTkLabel(
            dest_card,
            text="Output Directory",
            font=font_caption_bold(),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=10, pady=(8, 4))

        dest_row = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_row.pack(fill="x", padx=10, pady=(0, 10))
        dest_row.grid_columnconfigure(0, weight=1)

        self.entry_dest_dir = ctk.CTkEntry(
            dest_row,
            placeholder_text="Choose destination folder...",
            height=32,
            font=font_caption(),
            fg_color=BG_INPUT,
            border_color=BORDER_SUBTLE,
            corner_radius=RADIUS_INPUT
        )
        self.entry_dest_dir.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        btn_browse_dest = ctk.CTkButton(
            dest_row,
            text="📂 Browse",
            width=76,
            height=32,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            hover_color=BTN_NEUTRAL_HOVER,
            text_color=BTN_NEUTRAL_TEXT,
            corner_radius=RADIUS_INPUT,
            command=self._browse_dest_dir
        )
        btn_browse_dest.grid(row=0, column=1)

        # ----------------------------------------------------
        # 3. Bottom Progress Bar & Convert Action Bar
        # ----------------------------------------------------
        bottom_bar = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_CONTAINER,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        bottom_bar.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="ew")
        bottom_bar.grid_columnconfigure(0, weight=1)

        # Progress and Status display
        prog_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        prog_frame.grid(row=0, column=0, padx=16, pady=10, sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            prog_frame,
            text="Ready. Select a PDF and click '⚡ Convert PDF to Images'.",
            font=font_caption(),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.progress_bar = ctk.CTkProgressBar(
            prog_frame,
            height=8,
            corner_radius=4,
            progress_color=ACCENT_EMERALD,
            fg_color=BORDER_SUBTLE
        )
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=1, column=0, sticky="ew")

        # Action Buttons frame
        actions_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        actions_frame.grid(row=0, column=1, padx=16, pady=10, sticky="e")

        self.btn_open_folder = ctk.CTkButton(
            actions_frame,
            text="📁 Open Images Folder",
            width=150,
            height=38,
            font=font_caption_bold(),
            fg_color=ACCENT_TEAL,
            hover_color=ACCENT_TEAL_HOVER,
            text_color=TEXT_INVERSE,
            corner_radius=RADIUS_BTN,
            command=self._open_output_folder
        )
        # Hidden until conversion succeeds

        self.btn_convert = ctk.CTkButton(
            actions_frame,
            text="⚡ Convert PDF to Images",
            width=190,
            height=40,
            font=font_title(),
            fg_color=ACCENT_EMERALD,
            hover_color=ACCENT_EMERALD_HOVER,
            text_color=TEXT_INVERSE,
            corner_radius=RADIUS_BTN,
            command=self._start_conversion
        )
        self.btn_convert.pack(side="right")

    # ----------------------------------------------------
    # Empty State Designer
    # ----------------------------------------------------
    def _render_empty_state(self):
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()

        empty_box = ctk.CTkFrame(self.cards_scroll, fg_color="transparent")
        empty_box.pack(expand=True, pady=90)

        icon_badge = ctk.CTkLabel(
            empty_box,
            text="📄",
            font=ctk.CTkFont(size=42)
        )
        icon_badge.pack(pady=(0, 8))

        ctk.CTkLabel(
            empty_box,
            text="Select a PDF to Extract Images",
            font=font_h2(),
            text_color=TEXT_MAIN
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            empty_box,
            text="Extract specific page ranges or all pages into high-resolution PNG, JPG, or WEBP images.",
            font=font_caption(),
            text_color=TEXT_MUTED
        ).pack(pady=(0, 16))

        ctk.CTkButton(
            empty_box,
            text="📄 Select PDF Document",
            width=160,
            height=36,
            font=font_caption_bold(),
            fg_color=ACCENT_EMERALD,
            hover_color=ACCENT_EMERALD_HOVER,
            text_color=TEXT_INVERSE,
            corner_radius=RADIUS_BTN,
            command=self._choose_pdf_file
        ).pack()

    # ----------------------------------------------------
    # PDF Loading & Page Browser
    # ----------------------------------------------------
    def _choose_pdf_file(self):
        file_types = [("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        pdf_path = filedialog.askopenfilename(title="Select PDF Document", filetypes=file_types)
        if pdf_path and is_valid_pdf_file(pdf_path):
            self._load_pdf(pdf_path)

    def _load_pdf(self, pdf_path: str):
        self.current_pdf_path = os.path.normpath(pdf_path)
        try:
            meta = get_pdf_metadata(self.current_pdf_path)
            self.current_pdf_meta = meta
            total_pages = meta.get("page_count", 0)

            if total_pages == 0:
                messagebox.showerror("Invalid PDF", "The selected PDF file contains 0 pages.")
                return

            self.lbl_pdf_title.configure(text=f"📄 {meta['filename']}")
            self.lbl_pdf_details.configure(text=f"{total_pages} Pages • {meta['size_formatted']} • {meta['dimensions']}")

            # Default destination directory to a subfolder named after the PDF
            pdf_dir = os.path.dirname(self.current_pdf_path)
            pdf_stem = os.path.splitext(meta["filename"])[0]
            default_out_dir = os.path.join(pdf_dir, f"{pdf_stem}_images")
            self.entry_dest_dir.delete(0, "end")
            self.entry_dest_dir.insert(0, default_out_dir)

            # Build page queue data
            self.pages_queue.clear()
            for p_idx in range(total_pages):
                self.pages_queue.append({
                    "pdf_path": self.current_pdf_path,
                    "page_index": p_idx,
                    "filename": f"Page {p_idx + 1}",
                    "dimensions": meta.get("dimensions", ""),
                    "selected": True
                })

            self._refresh_pages_ui()
            self._update_status(f"Loaded '{meta['filename']}' ({total_pages} pages).")

        except Exception as e:
            messagebox.showerror("Error Opening PDF", f"Could not load PDF:\n{e}")

    def _refresh_pages_ui(self):
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()

        total = len(self.pages_queue)
        if total == 0:
            self._render_empty_state()
            return

        for idx, item in enumerate(self.pages_queue):
            card = ItemCard(
                self.cards_scroll,
                item_data=item,
                index=idx,
                total_items=total,
                on_select=self._on_page_select,
                on_preview=self._on_page_preview,
                is_pdf_page=True
            )
            card.pack(fill="x", pady=3, padx=4)

    def _on_page_select(self, item_data: Dict[str, Any], is_selected: bool):
        selected_count = sum(1 for item in self.pages_queue if item.get("selected", True))
        total = len(self.pages_queue)
        self.lbl_pdf_details.configure(text=f"{selected_count}/{total} Pages Selected • {self.current_pdf_meta.get('size_formatted', '')}")

    def _on_page_preview(self, item_data: Dict[str, Any]):
        try:
            current_idx = self.pages_queue.index(item_data)
        except ValueError:
            current_idx = 0
        PreviewModal(self, items=self.pages_queue, current_index=current_idx, is_pdf_page=True)

    def _set_all_pages(self, select: bool):
        for item in self.pages_queue:
            item["selected"] = select
        self._refresh_pages_ui()
        self._on_page_select({}, select)

    def _select_odd_pages(self):
        for item in self.pages_queue:
            item["selected"] = ((item["page_index"] + 1) % 2 != 0)
        self._refresh_pages_ui()
        self._on_page_select({}, True)

    def _select_even_pages(self):
        for item in self.pages_queue:
            item["selected"] = ((item["page_index"] + 1) % 2 == 0)
        self._refresh_pages_ui()
        self._on_page_select({}, True)

    def _apply_custom_range(self):
        if not self.pages_queue:
            return
        range_str = self.entry_range.get().strip()
        if not range_str:
            return

        target_indices = set(parse_page_range(range_str, len(self.pages_queue)))
        for item in self.pages_queue:
            item["selected"] = (item["page_index"] in target_indices)

        self._refresh_pages_ui()
        self._on_page_select({}, True)

    def _on_format_changed(self, choice: str):
        is_jpg_webp = "JPG" in choice or "WEBP" in choice
        if is_jpg_webp:
            self.slider_quality.configure(state="normal")
            self.lbl_quality.configure(text_color=TEXT_MAIN)
        else:
            self.slider_quality.configure(state="disabled")
            self.lbl_quality.configure(text_color=TEXT_DIM)

    def _on_slider_quality(self, val: float):
        self.lbl_quality.configure(text=f"JPG / WEBP Quality ({int(val)}%):")

    def _browse_dest_dir(self):
        folder = filedialog.askdirectory(title="Choose Output Directory for Images")
        if folder:
            self.entry_dest_dir.delete(0, "end")
            self.entry_dest_dir.insert(0, folder)

    # ----------------------------------------------------
    # Conversion Execution
    # ----------------------------------------------------
    def _start_conversion(self):
        if not self.current_pdf_path or not os.path.exists(self.current_pdf_path):
            messagebox.showwarning("No PDF Loaded", "Please select a valid PDF file first.")
            return

        selected_pages = [item["page_index"] for item in self.pages_queue if item.get("selected", True)]
        if not selected_pages:
            messagebox.showwarning("No Pages Selected", "Please select at least one page to convert.")
            return

        dest_dir = self.entry_dest_dir.get().strip()
        if not dest_dir:
            messagebox.showwarning("Destination Folder Required", "Please choose an output directory.")
            return

        # Format
        fmt_label = self.opt_format.get()
        fmt_map = {
            "PNG (Lossless / High Quality)": "png",
            "JPG (Photo / Compact)": "jpg",
            "WEBP (Modern Compressed)": "webp",
            "TIFF (Archival / Uncompressed)": "tiff",
            "BMP (Raw)": "bmp"
        }
        image_fmt = fmt_map.get(fmt_label, "png")

        # DPI
        dpi_label = self.opt_dpi.get()
        dpi_map = {
            "300 DPI (High Resolution / Print Quality)": 300,
            "150 DPI (Standard Screen Quality)": 150,
            "200 DPI (Crisp Presentation)": 200,
            "72 DPI (Web Draft / Small Size)": 72,
            "600 DPI (Ultra High Precision)": 600
        }
        dpi = dpi_map.get(dpi_label, 300)
        quality = int(self.slider_quality.get())
        template = self.entry_naming.get().strip() or "{pdf_name}_page_{page:03d}"

        # Lock UI
        self.btn_convert.configure(state="disabled", text="⚡ Rendering Images...")
        self.btn_open_folder.pack_forget()
        self.progress_bar.set(0.0)
        self.cancel_event.clear()

        def run():
            try:
                res = convert_pdf_to_images(
                    pdf_path=self.current_pdf_path,
                    output_directory=dest_dir,
                    image_format=image_fmt,
                    dpi=dpi,
                    page_indices=selected_pages,
                    jpg_quality=quality,
                    naming_template=template,
                    progress_callback=self._async_progress,
                    cancel_event=self.cancel_event
                )
                self.last_output_dir = dest_dir
                self.after(0, lambda: self._on_conversion_success(f"Extracted {res['converted_count']} pages into '{image_fmt.upper()}' images!"))
            except Exception as e:
                self.after(0, lambda err=e: self._on_conversion_error(err))

        self.conversion_thread = threading.Thread(target=run, daemon=True)
        self.conversion_thread.start()

    def _async_progress(self, current: int, total: int, message: str):
        fraction = current / max(1, total)
        self.after(0, lambda: self._update_progress_ui(fraction, message))

    def _update_progress_ui(self, fraction: float, message: str):
        self.progress_bar.set(fraction)
        self.status_label.configure(text=message, text_color=TEXT_MAIN)

    def _on_conversion_success(self, message: str):
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"✅ {message}", text_color=("#059669", "#34D399"))
        self.btn_convert.configure(state="normal", text="⚡ Convert PDF to Images")

        # Show open folder button
        self.btn_open_folder.pack(side="left", padx=4)

        messagebox.showinfo("Conversion Complete", f"{message}\n\nSaved in folder:\n{self.last_output_dir}")

    def _on_conversion_error(self, err: Exception):
        self.progress_bar.set(0.0)
        self.status_label.configure(text=f"❌ Error: {err}", text_color=("#EF4444", "#F87171"))
        self.btn_convert.configure(state="normal", text="⚡ Convert PDF to Images")
        messagebox.showerror("Conversion Failed", f"An error occurred during conversion:\n\n{err}")

    def _open_output_folder(self):
        if self.last_output_dir and os.path.exists(self.last_output_dir):
            os.startfile(self.last_output_dir)

    def _update_status(self, text: str):
        self.status_label.configure(text=text, text_color=TEXT_MAIN)
