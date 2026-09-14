import os
import subprocess
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import List, Dict, Any, Optional

from core.file_manager import (
    is_valid_image_file,
    get_image_metadata,
    safe_delete_file,
    rotate_image_file_on_disk,
    SUPPORTED_IMAGE_EXTENSIONS
)
from core.img_to_pdf import (
    convert_images_to_single_pdf,
    convert_images_to_individual_pdfs
)
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
    ACCENT_AMBER,
    ACCENT_AMBER_HOVER,
    ACCENT_ROSE,
    BTN_NEUTRAL_BG,
    BTN_NEUTRAL_HOVER,
    BTN_NEUTRAL_TEXT,
    BTN_DANGER_BG,
    BTN_DANGER_HOVER,
    BTN_DANGER_TEXT,
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
from gui.components.rename_modal import SingleRenameModal, BatchRenameModal
from gui.components.editor_modal import EditorModal


class ImgToPdfTab(ctk.CTkFrame):
    """
    Complete Images to PDF Converter Workspace with visual queue,
    reordering, batch renaming, page formatting, and live conversion feedback.
    Designed with unified design system tokens and responsive SaaS layout.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.images_queue: List[Dict[str, Any]] = []
        self.conversion_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.last_output_path: Optional[str] = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------------------------------------------
        # 1. Top Action Toolbar
        # ----------------------------------------------------
        toolbar = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_CONTAINER,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        toolbar.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        # Left action buttons
        btn_add_files = ctk.CTkButton(
            toolbar,
            text="➕ Add Images",
            width=115,
            height=34,
            font=font_caption_bold(),
            fg_color=ACCENT_EMERALD,
            hover_color=ACCENT_EMERALD_HOVER,
            text_color=TEXT_INVERSE,
            corner_radius=RADIUS_BTN,
            command=self._choose_images
        )
        btn_add_files.pack(side="left", padx=(12, 4), pady=8)

        btn_add_folder = ctk.CTkButton(
            toolbar,
            text="📁 Add Folder",
            width=105,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._choose_folder
        )
        btn_add_folder.pack(side="left", padx=3, pady=8)

        # Rotate Quick Action Buttons
        btn_rot_ccw_all = ctk.CTkButton(
            toolbar,
            text="↺ Rotate Left",
            width=96,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=ACCENT_EMERALD_HOVER,
            corner_radius=RADIUS_BTN,
            command=lambda: self._rotate_selected_images(270)
        )
        btn_rot_ccw_all.pack(side="left", padx=3, pady=8)

        btn_rot_cw_all = ctk.CTkButton(
            toolbar,
            text="↻ Rotate Right",
            width=102,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=ACCENT_EMERALD_HOVER,
            corner_radius=RADIUS_BTN,
            command=lambda: self._rotate_selected_images(90)
        )
        btn_rot_cw_all.pack(side="left", padx=3, pady=8)

        btn_batch_rename = ctk.CTkButton(
            toolbar,
            text="🏷 Batch Rename",
            width=115,
            height=34,
            font=font_caption_bold(),
            fg_color=ACCENT_AMBER,
            text_color=TEXT_INVERSE,
            hover_color=ACCENT_AMBER_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._open_batch_rename
        )
        btn_batch_rename.pack(side="left", padx=3, pady=8)

        # Selection controls
        btn_select_all = ctk.CTkButton(
            toolbar,
            text="Select All",
            width=75,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=lambda: self._set_all_selected(True)
        )
        btn_select_all.pack(side="left", padx=2, pady=8)

        btn_deselect_all = ctk.CTkButton(
            toolbar,
            text="Deselect All",
            width=82,
            height=34,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=lambda: self._set_all_selected(False)
        )
        btn_deselect_all.pack(side="left", padx=2, pady=8)

        # Sort Dropdown
        ctk.CTkLabel(
            toolbar,
            text="Sort:",
            font=font_caption(),
            text_color=TEXT_MUTED
        ).pack(side="left", padx=(8, 2))

        self.sort_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)", "Size (Largest)", "Reverse Order"],
            width=130,
            height=32,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            button_color=BORDER_SUBTLE,
            button_hover_color=BORDER_CARD,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT,
            command=self._sort_queue
        )
        self.sort_menu.pack(side="left", padx=2, pady=8)

        # Right utility buttons
        btn_clear = ctk.CTkButton(
            toolbar,
            text="🧹 Clear All",
            width=90,
            height=34,
            font=font_caption_bold(),
            fg_color=BTN_DANGER_BG,
            text_color=BTN_DANGER_TEXT,
            hover_color=BTN_DANGER_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._clear_queue
        )
        btn_clear.pack(side="right", padx=(5, 12), pady=8)

        # ----------------------------------------------------
        # 2. Main Workspace: Split View (Queue List + Settings)
        # ----------------------------------------------------
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=1, column=0, padx=16, pady=4, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=3)  # Image Queue (left)
        workspace.grid_columnconfigure(1, weight=1)  # Options Panel (right)
        workspace.grid_rowconfigure(0, weight=1)

        # LEFT: Scrollable Images Queue List Container
        queue_container = ctk.CTkFrame(
            workspace,
            corner_radius=RADIUS_CONTAINER,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        queue_container.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        queue_container.grid_rowconfigure(1, weight=1)
        queue_container.grid_columnconfigure(0, weight=1)

        # Queue Subheader with count
        q_hdr = ctk.CTkFrame(queue_container, height=42, fg_color="transparent")
        q_hdr.grid(row=0, column=0, padx=14, pady=(10, 4), sticky="ew")

        self.lbl_queue_count = ctk.CTkLabel(
            q_hdr,
            text="0 images loaded",
            font=font_title(),
            text_color=TEXT_MAIN
        )
        self.lbl_queue_count.pack(side="left")

        self.lbl_selected_count = ctk.CTkLabel(
            q_hdr,
            text="(0 selected for PDF)",
            font=font_caption(),
            text_color=ACCENT_EMERALD
        )
        self.lbl_selected_count.pack(side="left", padx=8)

        # Scrollable Frame for Item Cards
        self.cards_scroll = ctk.CTkScrollableFrame(queue_container, fg_color="transparent")
        self.cards_scroll.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        # Empty State Placeholder
        self._render_empty_state()

        # RIGHT: Conversion Settings & Export Panel
        settings_panel = ctk.CTkScrollableFrame(
            workspace,
            corner_radius=RADIUS_CONTAINER,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        settings_panel.grid(row=0, column=1, sticky="nsew")
        settings_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            settings_panel,
            text="⚙ PDF Settings",
            font=font_h1(),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=12, pady=(12, 10))

        # --- CARD 1: Page Geometry ---
        sec_geom = ctk.CTkFrame(settings_panel, corner_radius=RADIUS_CARD, fg_color=BG_CARD_ALT, border_width=1, border_color=BORDER_CARD)
        sec_geom.pack(fill="x", padx=6, pady=5)

        ctk.CTkLabel(sec_geom, text="📐 Page Layout & Geometry", font=font_caption_bold(), text_color=TEXT_MAIN).pack(anchor="w", padx=10, pady=(8, 4))

        # Output Mode
        ctk.CTkLabel(sec_geom, text="Output Mode:", font=font_caption(), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 2))
        self.opt_mode = ctk.CTkSegmentedButton(
            sec_geom,
            values=["Single Combined PDF", "Individual PDFs"],
            font=font_caption_bold(),
            selected_color=ACCENT_EMERALD,
            selected_hover_color=ACCENT_EMERALD_HOVER,
            command=self._on_output_mode_change
        )
        self.opt_mode.set("Single Combined PDF")
        self.opt_mode.pack(fill="x", padx=10, pady=(0, 8))

        # Page Size
        ctk.CTkLabel(sec_geom, text="Page Size:", font=font_caption(), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 2))
        self.opt_page_size = ctk.CTkOptionMenu(
            sec_geom,
            values=["Fit to Image (Original)", "A4 (Standard Document)", "US Letter", "A3", "A5"],
            font=font_caption(),
            fg_color=BG_INPUT,
            text_color=TEXT_MAIN,
            button_color=BORDER_SUBTLE,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT
        )
        self.opt_page_size.set("Fit to Image (Original)")
        self.opt_page_size.pack(fill="x", padx=10, pady=(0, 8))

        # Orientation
        ctk.CTkLabel(sec_geom, text="Orientation:", font=font_caption(), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 2))
        self.opt_orientation = ctk.CTkOptionMenu(
            sec_geom,
            values=["Auto (Match Image)", "Portrait", "Landscape"],
            font=font_caption(),
            fg_color=BG_INPUT,
            text_color=TEXT_MAIN,
            button_color=BORDER_SUBTLE,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT
        )
        self.opt_orientation.set("Auto (Match Image)")
        self.opt_orientation.pack(fill="x", padx=10, pady=(0, 8))

        # Margins
        ctk.CTkLabel(sec_geom, text="Margins:", font=font_caption(), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 2))
        self.opt_margin = ctk.CTkOptionMenu(
            sec_geom,
            values=["None (Edge-to-Edge)", "Small (0.25 in)", "Normal (0.5 in)", "Large (0.75 in)"],
            font=font_caption(),
            fg_color=BG_INPUT,
            text_color=TEXT_MAIN,
            button_color=BORDER_SUBTLE,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT
        )
        self.opt_margin.set("None (Edge-to-Edge)")
        self.opt_margin.pack(fill="x", padx=10, pady=(0, 8))

        # --- CARD 2: Compression & Optimization ---
        sec_comp = ctk.CTkFrame(settings_panel, corner_radius=RADIUS_CARD, fg_color=BG_CARD_ALT, border_width=1, border_color=BORDER_CARD)
        sec_comp.pack(fill="x", padx=6, pady=5)

        ctk.CTkLabel(sec_comp, text="⚡ Compression & Quality", font=font_caption_bold(), text_color=TEXT_MAIN).pack(anchor="w", padx=10, pady=(8, 4))

        # Quality Preset
        ctk.CTkLabel(sec_comp, text="Quality Preset:", font=font_caption(), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 2))
        self.opt_quality = ctk.CTkOptionMenu(
            sec_comp,
            values=[
                "Extreme Compression (Tiny Size • Crisp Text)",
                "Ultra Compact / Email (Smallest Size • Max Compression)",
                "High Quality (JPEG 90 - Standard)",
                "Medium Quality (JPEG 75)",
                "Low / Web Size (JPEG 50)",
                "Lossless (Original Quality / No Compression)"
            ],
            font=font_caption(),
            fg_color=BG_INPUT,
            text_color=TEXT_MAIN,
            button_color=BORDER_SUBTLE,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT
        )
        self.opt_quality.set("High Quality (JPEG 90 - Standard)")
        self.opt_quality.pack(fill="x", padx=10, pady=(0, 8))

        # Max Resolution Limit
        ctk.CTkLabel(sec_comp, text="Max Image Resolution:", font=font_caption(), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 2))
        self.opt_max_dim = ctk.CTkOptionMenu(
            sec_comp,
            values=[
                "Auto (Based on Quality Preset)",
                "Full HD (Max 1920 px)",
                "Compact (Max 1600 px)",
                "Mobile / Web (Max 1280 px)",
                "Ultra Small (Max 1024 px)",
                "Original Pixels (No Downscaling)"
            ],
            font=font_caption(),
            fg_color=BG_INPUT,
            text_color=TEXT_MAIN,
            button_color=BORDER_SUBTLE,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT
        )
        self.opt_max_dim.set("Auto (Based on Quality Preset)")
        self.opt_max_dim.pack(fill="x", padx=10, pady=(0, 8))

        # --- CARD 3: Destination & Metadata ---
        sec_dest = ctk.CTkFrame(settings_panel, corner_radius=RADIUS_CARD, fg_color=BG_CARD_ALT, border_width=1, border_color=BORDER_CARD)
        sec_dest.pack(fill="x", padx=6, pady=5)

        ctk.CTkLabel(sec_dest, text="💾 Destination & Output", font=font_caption_bold(), text_color=TEXT_MAIN).pack(anchor="w", padx=10, pady=(8, 4))

        # PDF Document Title
        ctk.CTkLabel(sec_dest, text="Document Title:", font=font_caption(), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 2))
        self.entry_doc_title = ctk.CTkEntry(
            sec_dest,
            placeholder_text="e.g. My Document",
            height=32,
            font=font_caption(),
            fg_color=BG_INPUT,
            border_color=BORDER_SUBTLE,
            corner_radius=RADIUS_INPUT
        )
        self.entry_doc_title.pack(fill="x", padx=10, pady=(0, 8))

        # Output Target Picker
        self.lbl_output_target = ctk.CTkLabel(sec_dest, text="Output PDF File:", font=font_caption(), text_color=TEXT_MUTED)
        self.lbl_output_target.pack(anchor="w", padx=10, pady=(2, 2))

        target_row = ctk.CTkFrame(sec_dest, fg_color="transparent")
        target_row.pack(fill="x", padx=10, pady=(0, 10))
        target_row.grid_columnconfigure(0, weight=1)

        self.entry_output_path = ctk.CTkEntry(
            target_row,
            placeholder_text="Choose destination...",
            height=32,
            font=font_caption(),
            fg_color=BG_INPUT,
            border_color=BORDER_SUBTLE,
            corner_radius=RADIUS_INPUT
        )
        self.entry_output_path.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_browse_output = ctk.CTkButton(
            target_row,
            text="📂 Browse",
            width=76,
            height=32,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            hover_color=BTN_NEUTRAL_HOVER,
            text_color=BTN_NEUTRAL_TEXT,
            corner_radius=RADIUS_INPUT,
            command=self._browse_output_target
        )
        self.btn_browse_output.grid(row=0, column=1)

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
            text="Ready. Select images and click '⚡ Convert to PDF'.",
            font=font_caption(),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.progress_bar = ctk.CTkProgressBar(
            prog_frame,
            height=8,
            progress_color=ACCENT_EMERALD,
            fg_color=BORDER_SUBTLE,
            corner_radius=4
        )
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=1, column=0, sticky="ew")

        # Action Buttons frame
        actions_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        actions_frame.grid(row=0, column=1, padx=16, pady=10, sticky="e")

        self.btn_open_file = ctk.CTkButton(
            actions_frame,
            text="📄 Open PDF",
            width=110,
            height=38,
            font=font_caption_bold(),
            fg_color=ACCENT_EMERALD_ACTIVE,
            hover_color=ACCENT_EMERALD_HOVER,
            text_color=TEXT_INVERSE,
            corner_radius=RADIUS_BTN,
            command=self._open_last_output_file
        )
        # Hidden until conversion succeeds

        self.btn_open_folder = ctk.CTkButton(
            actions_frame,
            text="📁 Open Folder",
            width=115,
            height=38,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._open_last_output_folder
        )
        # Hidden until conversion succeeds

        self.btn_convert = ctk.CTkButton(
            actions_frame,
            text="⚡ Convert to PDF",
            width=180,
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
            text="🖼",
            font=ctk.CTkFont(size=42)
        )
        icon_badge.pack(pady=(0, 8))

        ctk.CTkLabel(
            empty_box,
            text="Add Images to Build Your PDF",
            font=font_h2(),
            text_color=TEXT_MAIN
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            empty_box,
            text="Select multiple images or entire directories. Reorder, rotate, crop, and compress with ease.",
            font=font_caption(),
            text_color=TEXT_MUTED
        ).pack(pady=(0, 16))

        btn_row = ctk.CTkFrame(empty_box, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row,
            text="➕ Add Images",
            width=120,
            height=36,
            font=font_caption_bold(),
            fg_color=ACCENT_EMERALD,
            hover_color=ACCENT_EMERALD_HOVER,
            text_color=TEXT_INVERSE,
            corner_radius=RADIUS_BTN,
            command=self._choose_images
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_row,
            text="📁 Add Folder",
            width=110,
            height=36,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=BTN_NEUTRAL_TEXT,
            hover_color=BTN_NEUTRAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._choose_folder
        ).pack(side="left", padx=4)

    # ----------------------------------------------------
    # Queue Management & Actions
    # ----------------------------------------------------
    def _choose_images(self):
        file_types = [
            ("Supported Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif *.jfif *.gif"),
            ("All Files", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Select Images to Convert", filetypes=file_types)
        if files:
            self._add_image_paths(files)

    def _choose_folder(self):
        folder = filedialog.askdirectory(title="Select Folder Containing Images")
        if folder:
            image_paths = []
            for root, _, filenames in os.walk(folder):
                for f in sorted(filenames):
                    full_p = os.path.join(root, f)
                    if is_valid_image_file(full_p):
                        image_paths.append(full_p)
            if image_paths:
                self._add_image_paths(image_paths)
            else:
                messagebox.showinfo("No Images Found", f"No supported image files found in '{folder}'.")

    def _add_image_paths(self, paths: List[str]):
        existing_paths = {item["path"] for item in self.images_queue}
        new_count = 0

        for p in paths:
            norm_p = os.path.normpath(p)
            if norm_p not in existing_paths and is_valid_image_file(norm_p):
                try:
                    meta = get_image_metadata(norm_p)
                    meta["selected"] = True
                    self.images_queue.append(meta)
                    existing_paths.add(norm_p)
                    new_count += 1
                except Exception:
                    pass

        if new_count > 0:
            # If no output path set yet, default to first image folder
            if not self.entry_output_path.get().strip() and self.images_queue:
                first_dir = os.path.dirname(self.images_queue[0]["path"])
                default_out = os.path.join(first_dir, "combined_document.pdf")
                self.entry_output_path.delete(0, "end")
                self.entry_output_path.insert(0, default_out)

            self._refresh_queue_ui()
            self._update_status(f"Added {new_count} new images.")

    def _refresh_queue_ui(self):
        # Clear existing cards
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()

        total = len(self.images_queue)
        selected_count = sum(1 for item in self.images_queue if item.get("selected", True))

        self.lbl_queue_count.configure(text=f"{total} image{'s' if total != 1 else ''} loaded")
        self.lbl_selected_count.configure(text=f"({selected_count} selected for PDF)")

        if total == 0:
            self._render_empty_state()
            return

        for idx, item in enumerate(self.images_queue):
            card = ItemCard(
                self.cards_scroll,
                item_data=item,
                index=idx,
                total_items=total,
                on_select=self._on_item_select,
                on_preview=self._on_item_preview,
                on_move_up=self._on_item_move_up,
                on_move_down=self._on_item_move_down,
                on_rename=self._on_item_rename,
                on_rotate_cw=self._on_item_rotate_cw,
                on_rotate_ccw=self._on_item_rotate_ccw,
                on_edit=self._on_item_edit,
                on_remove=self._on_item_remove,
                on_delete=self._on_item_delete
            )
            card.pack(fill="x", pady=3, padx=4)

    def _on_item_select(self, item_data: Dict[str, Any], is_selected: bool):
        selected_count = sum(1 for item in self.images_queue if item.get("selected", True))
        self.lbl_selected_count.configure(text=f"({selected_count} selected for PDF)")

    def _set_all_selected(self, select: bool):
        for item in self.images_queue:
            item["selected"] = select
        self._refresh_queue_ui()

    def _on_item_preview(self, item_data: Dict[str, Any]):
        try:
            current_idx = self.images_queue.index(item_data)
        except ValueError:
            current_idx = 0
        PreviewModal(
            self,
            items=self.images_queue,
            current_index=current_idx,
            is_pdf_page=False,
            on_item_updated=lambda updated: self._refresh_queue_ui()
        )

    def _on_item_rotate_cw(self, item_data: Dict[str, Any]):
        file_path = item_data.get("path", "")
        try:
            rotate_image_file_on_disk(file_path, 90)
            meta = get_image_metadata(file_path)
            item_data.update(meta)
            self._refresh_queue_ui()
            self._update_status(f"Rotated '{item_data.get('filename')}' 90° Clockwise.")
        except Exception as e:
            messagebox.showerror("Rotation Failed", f"Could not rotate image file:\n{e}")

    def _on_item_rotate_ccw(self, item_data: Dict[str, Any]):
        file_path = item_data.get("path", "")
        try:
            rotate_image_file_on_disk(file_path, 270)
            meta = get_image_metadata(file_path)
            item_data.update(meta)
            self._refresh_queue_ui()
            self._update_status(f"Rotated '{item_data.get('filename')}' 90° Counter-Clockwise.")
        except Exception as e:
            messagebox.showerror("Rotation Failed", f"Could not rotate image file:\n{e}")

    def _on_item_edit(self, item_data: Dict[str, Any]):
        EditorModal(self, item_data=item_data, on_save_callback=self._on_item_edited)

    def _on_item_edited(self, updated_item: Dict[str, Any], edited_img):
        self._refresh_queue_ui()
        self._update_status(f"Updated '{updated_item.get('filename')}' on disk.")

    def _rotate_selected_images(self, degrees: int):
        selected = [item for item in self.images_queue if item.get("selected", True)]
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one image to rotate.")
            return

        success_count = 0
        for item in selected:
            try:
                rotate_image_file_on_disk(item["path"], degrees % 360)
                meta = get_image_metadata(item["path"])
                item.update(meta)
                success_count += 1
            except Exception:
                pass

        self._refresh_queue_ui()
        direction_name = "Right (90° CW)" if (degrees % 360) == 90 else "Left (90° CCW)"
        self._update_status(f"Rotated {success_count} image(s) {direction_name} and saved to disk.")

    def _on_item_move_up(self, index: int):
        if index > 0:
            self.images_queue[index], self.images_queue[index - 1] = self.images_queue[index - 1], self.images_queue[index]
            self._refresh_queue_ui()

    def _on_item_move_down(self, index: int):
        if index < len(self.images_queue) - 1:
            self.images_queue[index], self.images_queue[index + 1] = self.images_queue[index + 1], self.images_queue[index]
            self._refresh_queue_ui()

    def _on_item_rename(self, item_data: Dict[str, Any]):
        SingleRenameModal(self, item_data=item_data, on_success=lambda updated: self._refresh_queue_ui())

    def _open_batch_rename(self):
        selected_items = [item for item in self.images_queue if item.get("selected", True)]
        if not selected_items:
            messagebox.showwarning("No Items Selected", "Please select at least one image to batch rename.")
            return
        BatchRenameModal(self, items=selected_items, on_success=lambda updated: self._refresh_queue_ui())

    def _on_item_remove(self, item_data: Dict[str, Any]):
        if item_data in self.images_queue:
            self.images_queue.remove(item_data)
            self._refresh_queue_ui()
            self._update_status(f"Removed '{item_data.get('filename')}' from queue.")

    def _on_item_delete(self, item_data: Dict[str, Any]):
        filename = item_data.get("filename", "this file")
        confirm = messagebox.askyesno(
            "Confirm Delete from Disk",
            f"Are you sure you want to permanently delete:\n\n{filename}\n\nfrom your hard drive? This cannot be undone.",
            icon="warning"
        )
        if confirm:
            try:
                safe_delete_file(item_data["path"])
                if item_data in self.images_queue:
                    self.images_queue.remove(item_data)
                self._refresh_queue_ui()
                self._update_status(f"Deleted '{filename}' from disk.")
            except Exception as e:
                messagebox.showerror("Delete Failed", f"Could not delete file:\n{e}")

    def _clear_queue(self):
        if not self.images_queue:
            return
        confirm = messagebox.askyesno("Clear Queue", "Clear all images from the conversion queue?")
        if confirm:
            self.images_queue.clear()
            self._refresh_queue_ui()
            self._update_status("Queue cleared.")

    def _sort_queue(self, sort_by: str):
        if not self.images_queue:
            return
        if sort_by == "Name (A-Z)":
            self.images_queue.sort(key=lambda x: x.get("filename", "").lower())
        elif sort_by == "Name (Z-A)":
            self.images_queue.sort(key=lambda x: x.get("filename", "").lower(), reverse=True)
        elif sort_by == "Date (Newest)":
            self.images_queue.sort(key=lambda x: x.get("modified_time", ""), reverse=True)
        elif sort_by == "Date (Oldest)":
            self.images_queue.sort(key=lambda x: x.get("modified_time", ""))
        elif sort_by == "Size (Largest)":
            self.images_queue.sort(key=lambda x: x.get("size_bytes", 0), reverse=True)
        elif sort_by == "Reverse Order":
            self.images_queue.reverse()
        self._refresh_queue_ui()

    def _on_output_mode_change(self, mode: str):
        if mode == "Single Combined PDF":
            self.lbl_output_target.configure(text="Output PDF File:")
            cur_path = self.entry_output_path.get().strip()
            if cur_path and not cur_path.lower().endswith(".pdf"):
                self.entry_output_path.delete(0, "end")
                self.entry_output_path.insert(0, os.path.join(cur_path, "combined_document.pdf"))
        else:
            self.lbl_output_target.configure(text="Output Destination Directory:")
            cur_path = self.entry_output_path.get().strip()
            if cur_path and cur_path.lower().endswith(".pdf"):
                self.entry_output_path.delete(0, "end")
                self.entry_output_path.insert(0, os.path.dirname(cur_path))

    def _browse_output_target(self):
        is_single = self.opt_mode.get() == "Single Combined PDF"
        if is_single:
            path = filedialog.asksaveasfilename(
                title="Choose Output PDF Path",
                defaultextension=".pdf",
                filetypes=[("PDF Document", "*.pdf")]
            )
        else:
            path = filedialog.askdirectory(title="Choose Output Directory for PDFs")

        if path:
            self.entry_output_path.delete(0, "end")
            self.entry_output_path.insert(0, path)

    # ----------------------------------------------------
    # Conversion Execution
    # ----------------------------------------------------
    def _start_conversion(self):
        selected_items = [item for item in self.images_queue if item.get("selected", True)]
        if not selected_items:
            messagebox.showwarning("No Images Selected", "Please add and select at least one image to convert.")
            return

        out_target = self.entry_output_path.get().strip()
        if not out_target:
            messagebox.showwarning("Output Path Required", "Please specify an output path or destination folder.")
            return

        # Settings
        mode = self.opt_mode.get()
        size_label = self.opt_page_size.get()
        size_map = {
            "Fit to Image (Original)": "fit_image",
            "A4 (Standard Document)": "a4",
            "US Letter": "letter",
            "A3": "a3",
            "A5": "a5"
        }
        page_size = size_map.get(size_label, "fit_image")

        ori_label = self.opt_orientation.get()
        ori_map = {
            "Auto (Match Image)": "auto",
            "Portrait": "portrait",
            "Landscape": "landscape"
        }
        orientation = ori_map.get(ori_label, "auto")

        margin_label = self.opt_margin.get()
        margin_map = {
            "None (Edge-to-Edge)": "none",
            "Small (0.25 in)": "small",
            "Normal (0.5 in)": "normal",
            "Large (0.75 in)": "large"
        }
        margin = margin_map.get(margin_label, "none")

        qual_label = self.opt_quality.get()
        qual_map = {
            "Extreme Compression (Tiny Size • Crisp Text)": "extreme",
            "Ultra Compact / Email (Smallest Size • Max Compression)": "ultra_extreme",
            "High Quality (JPEG 90 - Standard)": "high",
            "Medium Quality (JPEG 75)": "medium",
            "Low / Web Size (JPEG 50)": "low",
            "Lossless (Original Quality / No Compression)": "lossless"
        }
        quality = qual_map.get(qual_label, "high")

        dim_label = self.opt_max_dim.get()
        dim_map = {
            "Auto (Based on Quality Preset)": None,
            "Full HD (Max 1920 px)": 1920,
            "Compact (Max 1600 px)": 1600,
            "Mobile / Web (Max 1280 px)": 1280,
            "Ultra Small (Max 1024 px)": 1024,
            "Original Pixels (No Downscaling)": None
        }
        custom_max_dim = dim_map.get(dim_label, None)
        doc_title = self.entry_doc_title.get().strip()

        img_paths = [item["path"] for item in selected_items]

        # Lock UI
        self.btn_convert.configure(state="disabled", text="⚡ Converting...")
        self.btn_open_file.pack_forget()
        self.btn_open_folder.pack_forget()
        self.progress_bar.set(0.0)
        self.cancel_event.clear()

        # Run conversion in background thread
        def run():
            try:
                if mode == "Single Combined PDF":
                    # Ensure .pdf extension
                    final_pdf = out_target if out_target.lower().endswith(".pdf") else f"{out_target}.pdf"
                    res = convert_images_to_single_pdf(
                        image_paths=img_paths,
                        output_pdf_path=final_pdf,
                        page_size=page_size,
                        orientation=orientation,
                        margin=margin,
                        quality=quality,
                        custom_max_dim=custom_max_dim,
                        title=doc_title,
                        progress_callback=self._async_progress,
                        cancel_event=self.cancel_event
                    )
                    self.last_output_path = final_pdf
                    self.after(0, lambda: self._on_conversion_success(f"PDF generated: {os.path.basename(final_pdf)} ({len(img_paths)} pages)"))
                else:
                    convert_images_to_individual_pdfs(
                        image_paths=img_paths,
                        output_directory=out_target,
                        page_size=page_size,
                        orientation=orientation,
                        margin=margin,
                        quality=quality,
                        custom_max_dim=custom_max_dim,
                        progress_callback=self._async_progress,
                        cancel_event=self.cancel_event
                    )
                    self.last_output_path = out_target
                    self.after(0, lambda: self._on_conversion_success(f"Converted {len(img_paths)} images to individual PDFs!"))

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
        self.btn_convert.configure(state="normal", text="⚡ Convert to PDF")

        # Show result action buttons
        if self.last_output_path and os.path.isfile(self.last_output_path):
            self.btn_open_file.pack(side="left", padx=4)
        self.btn_open_folder.pack(side="left", padx=4)

        messagebox.showinfo("Success", f"{message}\n\nSaved to:\n{self.last_output_path}")

    def _on_conversion_error(self, err: Exception):
        self.progress_bar.set(0.0)
        self.status_label.configure(text=f"❌ Error: {err}", text_color=("#EF4444", "#F87171"))
        self.btn_convert.configure(state="normal", text="⚡ Convert to PDF")
        messagebox.showerror("Conversion Failed", f"An error occurred during conversion:\n\n{err}")

    def _open_last_output_file(self):
        if self.last_output_path and os.path.exists(self.last_output_path):
            if os.path.isfile(self.last_output_path):
                os.startfile(self.last_output_path)
            else:
                os.startfile(self.last_output_path)

    def _open_last_output_folder(self):
        if self.last_output_path:
            folder = os.path.dirname(self.last_output_path) if os.path.isfile(self.last_output_path) else self.last_output_path
            if os.path.exists(folder):
                os.startfile(folder)

    def _update_status(self, text: str):
        self.status_label.configure(text=text, text_color=TEXT_MAIN)
