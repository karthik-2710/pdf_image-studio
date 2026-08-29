import os
import customtkinter as ctk
from PIL import Image, ImageTk
from typing import Callable, Optional, Dict, Any

from core.file_manager import generate_image_thumbnail, generate_pdf_page_thumbnail, format_file_size


class ItemCard(ctk.CTkFrame):
    """
    Interactive card representing an image file or PDF page in the visual queue.
    """

    def __init__(
        self,
        master,
        item_data: Dict[str, Any],
        index: int,
        total_items: int,
        on_select: Optional[Callable[[Dict[str, Any], bool], None]] = None,
        on_preview: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_move_up: Optional[Callable[[int], None]] = None,
        on_move_down: Optional[Callable[[int], None]] = None,
        on_rename: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_remove: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_delete: Optional[Callable[[Dict[str, Any]], None]] = None,
        is_pdf_page: bool = False,
        **kwargs
    ):
        super().__init__(master, corner_radius=10, border_width=1, border_color=("gray75", "gray28"), fg_color=("gray92", "#23262d"), **kwargs)

        self.item_data = item_data
        self.index = index
        self.total_items = total_items
        self.is_pdf_page = is_pdf_page

        self.on_select = on_select
        self.on_preview = on_preview
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down
        self.on_rename = on_rename
        self.on_remove = on_remove
        self.on_delete = on_delete

        self.is_selected = item_data.get("selected", True)
        self.thumb_image = None
        self.ctk_image = None

        self._build_ui()

    def _build_ui(self):
        # Configure card layout
        self.grid_columnconfigure(2, weight=1)

        # 1. Selection Checkbox & Index Badge Frame
        left_ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_ctrl_frame.grid(row=0, column=0, padx=(10, 5), pady=8, sticky="nsw")

        self.check_var = ctk.BooleanVar(value=self.is_selected)
        self.checkbox = ctk.CTkCheckBox(
            left_ctrl_frame,
            text="",
            variable=self.check_var,
            width=20,
            command=self._handle_check_changed,
            checkbox_width=20,
            checkbox_height=20,
            border_width=2
        )
        self.checkbox.pack(side="left", padx=(0, 5))

        badge_text = f"P.{self.index + 1}" if self.is_pdf_page else f"#{self.index + 1}"
        self.badge = ctk.CTkLabel(
            left_ctrl_frame,
            text=badge_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#3a7ebf", "#1f538d"),
            text_color="white",
            corner_radius=6,
            width=36,
            height=24
        )
        self.badge.pack(side="left", padx=2)

        # 2. Thumbnail Preview Box
        thumb_frame = ctk.CTkFrame(self, width=80, height=80, corner_radius=6, fg_color=("gray85", "gray16"))
        thumb_frame.grid(row=0, column=1, padx=8, pady=8)
        thumb_frame.pack_propagate(False)

        self.thumb_label = ctk.CTkLabel(thumb_frame, text="Loading...", text_color="gray50")
        self.thumb_label.pack(expand=True, fill="both")
        self.thumb_label.bind("<Button-1>", lambda e: self._handle_preview())
        self.thumb_label.configure(cursor="hand2")

        # Load thumbnail asynchronously or safely
        self._load_thumbnail()

        # 3. File Info / Details Frame
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")

        # Filename
        filename = self.item_data.get("filename", os.path.basename(self.item_data.get("path", "")))
        display_name = filename if len(filename) <= 38 else filename[:25] + "..." + filename[-10:]
        
        self.name_label = ctk.CTkLabel(
            info_frame,
            text=display_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            text_color=("gray10", "gray95")
        )
        self.name_label.pack(anchor="w", pady=(2, 2))

        # Metadata Details Line
        dims = self.item_data.get("dimensions", "Unknown")
        size_str = self.item_data.get("size_formatted", "")
        fmt = self.item_data.get("format", "")
        
        if self.is_pdf_page:
            meta_str = f"Page {self.index + 1} • {dims}"
        else:
            meta_str = f"{fmt} • {dims} • {size_str}"

        self.meta_label = ctk.CTkLabel(
            info_frame,
            text=meta_str,
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.meta_label.pack(anchor="w")

        # Full path tooltip/display hint
        path_hint = self.item_data.get("path", "")
        if path_hint and not self.is_pdf_page:
            dir_hint = os.path.dirname(path_hint)
            if len(dir_hint) > 45:
                dir_hint = dir_hint[:20] + "..." + dir_hint[-22:]
            self.path_label = ctk.CTkLabel(
                info_frame,
                text=dir_hint,
                font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray50"),
                anchor="w"
            )
            self.path_label.pack(anchor="w")

        # 4. Action Buttons (Preview, Move Up, Move Down, Rename, Remove, Delete)
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=0, column=3, padx=(5, 12), pady=8, sticky="nse")

        # Preview Button
        self.btn_preview = ctk.CTkButton(
            action_frame,
            text="👁 Preview",
            width=70,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray35"),
            command=self._handle_preview
        )
        self.btn_preview.pack(side="left", padx=3)

        if not self.is_pdf_page:
            # Reorder Up
            self.btn_up = ctk.CTkButton(
                action_frame,
                text="▲",
                width=28,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=("gray80", "gray25"),
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray35"),
                state="normal" if self.index > 0 else "disabled",
                command=lambda: self.on_move_up(self.index) if self.on_move_up else None
            )
            self.btn_up.pack(side="left", padx=2)

            # Reorder Down
            self.btn_down = ctk.CTkButton(
                action_frame,
                text="▼",
                width=28,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=("gray80", "gray25"),
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray35"),
                state="normal" if self.index < self.total_items - 1 else "disabled",
                command=lambda: self.on_move_down(self.index) if self.on_move_down else None
            )
            self.btn_down.pack(side="left", padx=2)

            # Rename Button
            self.btn_rename = ctk.CTkButton(
                action_frame,
                text="✏ Rename",
                width=72,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=("#e0a800", "#b38600"),
                text_color="black",
                hover_color=("#cc9800", "#997300"),
                command=lambda: self.on_rename(self.item_data) if self.on_rename else None
            )
            self.btn_rename.pack(side="left", padx=3)

            # Remove from queue (Non-destructive)
            self.btn_remove = ctk.CTkButton(
                action_frame,
                text="✕",
                width=28,
                height=28,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("gray80", "gray25"),
                text_color=("gray20", "gray80"),
                hover_color=("#e57373", "#d32f2f"),
                command=lambda: self.on_remove(self.item_data) if self.on_remove else None
            )
            self.btn_remove.pack(side="left", padx=2)

            # Delete from Disk
            self.btn_delete = ctk.CTkButton(
                action_frame,
                text="🗑",
                width=28,
                height=28,
                font=ctk.CTkFont(size=12),
                fg_color=("#ffcdd2", "#4a1c1c"),
                text_color=("#b71c1c", "#ff8a80"),
                hover_color=("#e53935", "#b71c1c"),
                command=lambda: self.on_delete(self.item_data) if self.on_delete else None
            )
            self.btn_delete.pack(side="left", padx=2)

        self._update_highlight()

    def _load_thumbnail(self):
        try:
            if self.is_pdf_page:
                pdf_path = self.item_data.get("pdf_path", "")
                page_idx = self.item_data.get("page_index", 0)
                pil_img = generate_pdf_page_thumbnail(pdf_path, page_number=page_idx, max_size=(76, 76))
            else:
                img_path = self.item_data.get("path", "")
                pil_img = generate_image_thumbnail(img_path, max_size=(76, 76))

            if pil_img:
                self.ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(pil_img.width, pil_img.height))
                self.thumb_label.configure(image=self.ctk_image, text="")
            else:
                self.thumb_label.configure(text="🖼", font=ctk.CTkFont(size=20))
        except Exception:
            self.thumb_label.configure(text="⚠️", font=ctk.CTkFont(size=16))

    def _handle_check_changed(self):
        self.is_selected = self.check_var.get()
        self.item_data["selected"] = self.is_selected
        self._update_highlight()
        if self.on_select:
            self.on_select(self.item_data, self.is_selected)

    def _update_highlight(self):
        if self.is_selected:
            self.configure(border_color=("#3a7ebf", "#1f538d"), border_width=2)
        else:
            self.configure(border_color=("gray75", "gray28"), border_width=1)

    def _handle_preview(self):
        if self.on_preview:
            self.on_preview(self.item_data)

    def set_selected(self, selected: bool):
        self.check_var.set(selected)
        self.is_selected = selected
        self.item_data["selected"] = selected
        self._update_highlight()
