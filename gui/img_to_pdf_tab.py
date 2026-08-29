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
    SUPPORTED_IMAGE_EXTENSIONS
)
from core.img_to_pdf import (
    convert_images_to_single_pdf,
    convert_images_to_individual_pdfs
)
from gui.components.item_card import ItemCard
from gui.components.preview_modal import PreviewModal
from gui.components.rename_modal import SingleRenameModal, BatchRenameModal


class ImgToPdfTab(ctk.CTkFrame):
    """
    Complete Images to PDF Converter Workspace with visual queue,
    reordering, batch renaming, page formatting, and live conversion feedback.
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
        toolbar = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray88", "gray17"))
        toolbar.grid(row=0, column=0, padx=15, pady=(15, 8), sticky="ew")

        # Left action buttons
        btn_add_files = ctk.CTkButton(
            toolbar,
            text="➕ Add Images",
            width=115,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#3a7ebf", "#1f538d"),
            command=self._choose_images
        )
        btn_add_files.pack(side="left", padx=(10, 5), pady=8)

        btn_add_folder = ctk.CTkButton(
            toolbar,
            text="📁 Add Folder",
            width=110,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("gray75", "gray28"),
            text_color=("gray10", "gray95"),
            hover_color=("gray65", "gray38"),
            command=self._choose_folder
        )
        btn_add_folder.pack(side="left", padx=5, pady=8)

        btn_batch_rename = ctk.CTkButton(
            toolbar,
            text="🏷 Batch Rename",
            width=120,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("#e0a800", "#b38600"),
            text_color="black",
            hover_color=("#cc9800", "#997300"),
            command=self._open_batch_rename
        )
        btn_batch_rename.pack(side="left", padx=5, pady=8)

        # Selection controls
        btn_select_all = ctk.CTkButton(
            toolbar,
            text="Select All",
            width=80,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray28"),
            text_color=("gray10", "gray95"),
            command=lambda: self._set_all_selected(True)
        )
        btn_select_all.pack(side="left", padx=3, pady=8)

        btn_deselect_all = ctk.CTkButton(
            toolbar,
            text="Deselect All",
            width=85,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray28"),
            text_color=("gray10", "gray95"),
            command=lambda: self._set_all_selected(False)
        )
        btn_deselect_all.pack(side="left", padx=3, pady=8)

        # Sort Dropdown
        ctk.CTkLabel(toolbar, text="Sort:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 4))
        self.sort_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)", "Size (Largest)", "Reverse Order"],
            width=135,
            height=30,
            command=self._sort_queue
        )
        self.sort_menu.pack(side="left", padx=3, pady=8)

        # Right utility buttons
        btn_clear = ctk.CTkButton(
            toolbar,
            text="🧹 Clear All",
            width=90,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("#d32f2f", "#b71c1c"),
            hover_color=("#b71c1c", "#880e4f"),
            command=self._clear_queue
        )
        btn_clear.pack(side="right", padx=(5, 10), pady=8)

        # ----------------------------------------------------
        # 2. Main Workspace: Split View (Queue List + Settings)
        # ----------------------------------------------------
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=3)  # Image Queue (left)
        workspace.grid_columnconfigure(1, weight=1)  # Options Panel (right)
        workspace.grid_rowconfigure(0, weight=1)

        # LEFT: Scrollable Images Queue List
        queue_container = ctk.CTkFrame(workspace, corner_radius=10, fg_color=("gray90", "gray14"))
        queue_container.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        queue_container.grid_rowconfigure(1, weight=1)
        queue_container.grid_columnconfigure(0, weight=1)

        # Queue Subheader with count
        q_hdr = ctk.CTkFrame(queue_container, height=36, fg_color="transparent")
        q_hdr.grid(row=0, column=0, padx=12, pady=(8, 2), sticky="ew")
        
        self.lbl_queue_count = ctk.CTkLabel(
            q_hdr,
            text="0 images loaded",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray30", "gray80")
        )
        self.lbl_queue_count.pack(side="left")

        self.lbl_selected_count = ctk.CTkLabel(
            q_hdr,
            text="(0 selected for PDF)",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60")
        )
        self.lbl_selected_count.pack(side="left", padx=8)

        # Scrollable Frame for Item Cards
        self.cards_scroll = ctk.CTkScrollableFrame(queue_container, fg_color="transparent")
        self.cards_scroll.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        # Empty State Placeholder
        self.empty_label = ctk.CTkLabel(
            self.cards_scroll,
            text="📁 No Images Selected\n\nClick '➕ Add Images' or '📁 Add Folder' to start building your PDF.",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray50"),
            justify="center"
        )
        self.empty_label.pack(expand=True, pady=100)

        # RIGHT: Conversion Settings & Export Panel
        settings_panel = ctk.CTkScrollableFrame(workspace, corner_radius=10, fg_color=("gray90", "gray17"))
        settings_panel.grid(row=0, column=1, sticky="nsew")
        settings_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(settings_panel, text="⚙ PDF Settings", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=10, pady=(10, 12))

        # Output Mode
        ctk.CTkLabel(settings_panel, text="Output Mode:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(4, 2))
        self.opt_mode = ctk.CTkSegmentedButton(
            settings_panel,
            values=["Single Combined PDF", "Individual PDFs"],
            command=self._on_output_mode_change
        )
        self.opt_mode.set("Single Combined PDF")
        self.opt_mode.pack(fill="x", padx=10, pady=(0, 10))

        # Page Size
        ctk.CTkLabel(settings_panel, text="Page Size:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(4, 2))
        self.opt_page_size = ctk.CTkOptionMenu(
            settings_panel,
            values=["Fit to Image (Original)", "A4 (Standard Document)", "US Letter", "A3", "A5"]
        )
        self.opt_page_size.set("Fit to Image (Original)")
        self.opt_page_size.pack(fill="x", padx=10, pady=(0, 10))

        # Orientation
        ctk.CTkLabel(settings_panel, text="Orientation:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(4, 2))
        self.opt_orientation = ctk.CTkOptionMenu(
            settings_panel,
            values=["Auto (Match Image)", "Portrait", "Landscape"]
        )
        self.opt_orientation.set("Auto (Match Image)")
        self.opt_orientation.pack(fill="x", padx=10, pady=(0, 10))

        # Margins
        ctk.CTkLabel(settings_panel, text="Margins:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(4, 2))
        self.opt_margin = ctk.CTkOptionMenu(
            settings_panel,
            values=["None (Edge-to-Edge)", "Small (0.25 in)", "Normal (0.5 in)", "Large (0.75 in)"]
        )
        self.opt_margin.set("None (Edge-to-Edge)")
        self.opt_margin.pack(fill="x", padx=10, pady=(0, 10))

        # Quality / Compression
        ctk.CTkLabel(settings_panel, text="Image Quality / Compression:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(4, 2))
        self.opt_quality = ctk.CTkOptionMenu(
            settings_panel,
            values=["Lossless (Original / PNG)", "High Quality (JPEG 90)", "Medium Quality (JPEG 75)", "Low / Web Size (JPEG 50)"]
        )
        self.opt_quality.set("High Quality (JPEG 90)")
        self.opt_quality.pack(fill="x", padx=10, pady=(0, 12))

        # PDF Document Title
        ctk.CTkLabel(settings_panel, text="Document Title (Metadata):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(4, 2))
        self.entry_doc_title = ctk.CTkEntry(settings_panel, placeholder_text="e.g. My Document")
        self.entry_doc_title.pack(fill="x", padx=10, pady=(0, 12))

        # Output Target Picker
        self.lbl_output_target = ctk.CTkLabel(settings_panel, text="Output PDF File:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_output_target.pack(anchor="w", padx=10, pady=(4, 2))

        target_row = ctk.CTkFrame(settings_panel, fg_color="transparent")
        target_row.pack(fill="x", padx=10, pady=(0, 15))
        target_row.grid_columnconfigure(0, weight=1)

        self.entry_output_path = ctk.CTkEntry(target_row, placeholder_text="Choose destination...")
        self.entry_output_path.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.btn_browse_output = ctk.CTkButton(
            target_row,
            text="📂",
            width=36,
            height=28,
            command=self._browse_output_target
        )
        self.btn_browse_output.grid(row=0, column=1)

        # ----------------------------------------------------
        # 3. Bottom Progress Bar & Convert Action Bar
        # ----------------------------------------------------
        bottom_bar = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray88", "gray17"))
        bottom_bar.grid(row=2, column=0, padx=15, pady=(8, 15), sticky="ew")
        bottom_bar.grid_columnconfigure(0, weight=1)

        # Progress and Status display
        prog_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        prog_frame.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            prog_frame,
            text="Ready. Select images and click '⚡ Convert to PDF'.",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=12)
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=1, column=0, sticky="ew")

        # Action Buttons frame
        actions_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        actions_frame.grid(row=0, column=1, padx=15, pady=10, sticky="e")

        self.btn_open_file = ctk.CTkButton(
            actions_frame,
            text="📄 Open PDF",
            width=100,
            height=36,
            fg_color=("#388e3c", "#2e7d32"),
            hover_color=("#2e7d32", "#1b5e20"),
            command=self._open_last_output_file
        )
        # Hidden until conversion succeeds

        self.btn_open_folder = ctk.CTkButton(
            actions_frame,
            text="📁 Open Folder",
            width=110,
            height=36,
            fg_color=("gray75", "gray30"),
            text_color=("gray10", "gray95"),
            command=self._open_last_output_folder
        )
        # Hidden until conversion succeeds

        self.btn_convert = ctk.CTkButton(
            actions_frame,
            text="⚡ Convert to PDF",
            width=160,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#1976d2", "#1565c0"),
            hover_color=("#1565c0", "#0d47a1"),
            command=self._start_conversion
        )
        self.btn_convert.pack(side="right")

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
            self.empty_label = ctk.CTkLabel(
                self.cards_scroll,
                text="📁 No Images Selected\n\nClick '➕ Add Images' or '📁 Add Folder' to start building your PDF.",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray50"),
                justify="center"
            )
            self.empty_label.pack(expand=True, pady=100)
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
                on_remove=self._on_item_remove,
                on_delete=self._on_item_delete
            )
            card.pack(fill="x", pady=4, padx=4)

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
        PreviewModal(self, items=self.images_queue, current_index=current_idx, is_pdf_page=False)

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
            "Lossless (Original / PNG)": "lossless",
            "High Quality (JPEG 90)": "high",
            "Medium Quality (JPEG 75)": "medium",
            "Low / Web Size (JPEG 50)": "low"
        }
        quality = qual_map.get(qual_label, "high")
        doc_title = self.entry_doc_title.get().strip()

        img_paths = [item["path"] for item in selected_items]

        # Lock UI
        self.btn_convert.configure(state="disabled", text="Converting...")
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
        self.status_label.configure(text=message)

    def _on_conversion_success(self, message: str):
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"✅ {message}", text_color=("#1b5e20", "#81c784"))
        self.btn_convert.configure(state="normal", text="⚡ Convert to PDF")

        # Show result action buttons
        if self.last_output_path and os.path.isfile(self.last_output_path):
            self.btn_open_file.pack(side="left", padx=4)
        self.btn_open_folder.pack(side="left", padx=4)

        messagebox.showinfo("Success", f"{message}\n\nSaved to:\n{self.last_output_path}")

    def _on_conversion_error(self, err: Exception):
        self.progress_bar.set(0.0)
        self.status_label.configure(text=f"❌ Error: {err}", text_color=("#b71c1c", "#ff8a80"))
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
        self.status_label.configure(text=text, text_color=("gray10", "gray90"))
