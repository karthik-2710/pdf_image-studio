import os
import customtkinter as ctk
from PIL import Image, ImageTk
from typing import Callable, Optional, Dict, Any

from core.file_manager import generate_image_thumbnail, generate_pdf_page_thumbnail, format_file_size
from gui.theme import (
    BG_CARD,
    BG_CARD_ALT,
    BG_CONTAINER,
    BORDER_CARD,
    BORDER_SUBTLE,
    BORDER_ACTIVE,
    TEXT_MAIN,
    TEXT_MUTED,
    TEXT_DIM,
    TEXT_INVERSE,
    ACCENT_EMERALD,
    ACCENT_EMERALD_HOVER,
    ACCENT_TEAL,
    ACCENT_TEAL_HOVER,
    ACCENT_AMBER,
    ACCENT_AMBER_HOVER,
    ACCENT_ROSE,
    ACCENT_ROSE_HOVER,
    BTN_NEUTRAL_BG,
    BTN_NEUTRAL_HOVER,
    BTN_NEUTRAL_TEXT,
    BTN_DANGER_BG,
    BTN_DANGER_HOVER,
    BTN_DANGER_TEXT,
    BADGE_STYLES,
    RADIUS_CARD,
    RADIUS_CONTROL,
    RADIUS_BTN,
    RADIUS_PILL,
    RADIUS_BADGE,
    font_title,
    font_body,
    font_body_bold,
    font_caption,
    font_caption_bold,
    font_badge,
    font_mono
)


class ItemCard(ctk.CTkFrame):
    """
    Modern, sleek card representing an image file or PDF page in the visual queue.
    Designed with structured hierarchy, responsive buttons, format badges, and live selection border.
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
        on_rotate_cw: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_rotate_ccw: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_edit: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_remove: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_delete: Optional[Callable[[Dict[str, Any]], None]] = None,
        is_pdf_page: bool = False,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=BORDER_CARD,
            fg_color=BG_CARD,
            **kwargs
        )

        self.item_data = item_data
        self.index = index
        self.total_items = total_items
        self.is_pdf_page = is_pdf_page

        self.on_select = on_select
        self.on_preview = on_preview
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down
        self.on_rename = on_rename
        self.on_rotate_cw = on_rotate_cw
        self.on_rotate_ccw = on_rotate_ccw
        self.on_edit = on_edit
        self.on_remove = on_remove
        self.on_delete = on_delete

        self.is_selected = item_data.get("selected", True)
        self.thumb_image = None
        self.ctk_image = None

        self._build_ui()

    def _build_ui(self):
        # Configure card layout
        self.grid_columnconfigure(2, weight=1)

        # ----------------------------------------------------
        # 1. Selection Checkbox & Index Badge
        # ----------------------------------------------------
        left_ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_ctrl_frame.grid(row=0, column=0, padx=(10, 4), pady=8, sticky="nsw")

        self.check_var = ctk.BooleanVar(value=self.is_selected)
        self.checkbox = ctk.CTkCheckBox(
            left_ctrl_frame,
            text="",
            variable=self.check_var,
            width=20,
            command=self._handle_check_changed,
            checkbox_width=18,
            checkbox_height=18,
            border_width=2,
            fg_color=ACCENT_EMERALD,
            hover_color=ACCENT_EMERALD_HOVER,
            border_color=BORDER_SUBTLE,
            corner_radius=4
        )
        self.checkbox.pack(side="left", padx=(0, 4))

        badge_text = f"P.{self.index + 1}" if self.is_pdf_page else f"#{self.index + 1}"
        self.badge = ctk.CTkLabel(
            left_ctrl_frame,
            text=badge_text,
            font=font_caption_bold(),
            fg_color=("#ECFDF5", "#064E3B"),
            text_color=("#059669", "#34D399"),
            corner_radius=RADIUS_PILL,
            width=36,
            height=24
        )
        self.badge.pack(side="left", padx=2)

        # ----------------------------------------------------
        # 2. Thumbnail Preview Box
        # ----------------------------------------------------
        thumb_frame = ctk.CTkFrame(
            self,
            width=76,
            height=76,
            corner_radius=RADIUS_CONTROL,
            fg_color=BG_CONTAINER,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        thumb_frame.grid(row=0, column=1, padx=6, pady=8)
        thumb_frame.pack_propagate(False)

        self.thumb_label = ctk.CTkLabel(thumb_frame, text="...", font=font_caption(), text_color=TEXT_DIM)
        self.thumb_label.pack(expand=True, fill="both")
        self.thumb_label.bind("<Button-1>", lambda e: self._handle_preview())
        self.thumb_label.configure(cursor="hand2")

        # Load thumbnail
        self._load_thumbnail()

        # ----------------------------------------------------
        # 3. File Info / Details Column
        # ----------------------------------------------------
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")

        # Filename
        filename = self.item_data.get("filename", os.path.basename(self.item_data.get("path", "")))
        display_name = filename if len(filename) <= 38 else filename[:24] + "..." + filename[-11:]

        self.name_label = ctk.CTkLabel(
            info_frame,
            text=display_name,
            font=font_title(),
            anchor="w",
            text_color=TEXT_MAIN
        )
        self.name_label.pack(anchor="w", pady=(1, 3))

        # Metadata Tags & Badges Row
        dims = self.item_data.get("dimensions", "Unknown")
        size_str = self.item_data.get("size_formatted", "")
        fmt = self.item_data.get("format", "IMG").upper()

        meta_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        meta_row.pack(anchor="w", pady=(0, 2))

        # Format Badge
        badge_cfg = BADGE_STYLES.get(fmt, BADGE_STYLES["DEFAULT"])
        self.fmt_badge = ctk.CTkLabel(
            meta_row,
            text=f" {fmt} ",
            font=font_badge(),
            fg_color=badge_cfg["bg"],
            text_color=badge_cfg["fg"],
            corner_radius=RADIUS_BADGE,
            height=18
        )
        self.fmt_badge.pack(side="left", padx=(0, 6))

        # Dimensions & Size Text
        if self.is_pdf_page:
            meta_str = f"Page {self.index + 1} • {dims}"
        else:
            meta_str = f"{dims} • {size_str}"

        self.meta_label = ctk.CTkLabel(
            meta_row,
            text=meta_str,
            font=font_caption(),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        self.meta_label.pack(side="left")

        # Directory path hint
        path_hint = self.item_data.get("path", "")
        if path_hint and not self.is_pdf_page:
            dir_hint = os.path.dirname(path_hint)
            if len(dir_hint) > 46:
                dir_hint = dir_hint[:20] + "..." + dir_hint[-22:]
            self.path_label = ctk.CTkLabel(
                info_frame,
                text=dir_hint,
                font=font_badge(),
                text_color=TEXT_DIM,
                anchor="w"
            )
            self.path_label.pack(anchor="w")

        # ----------------------------------------------------
        # 4. Micro-Action Toolbar
        # ----------------------------------------------------
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=0, column=3, padx=(4, 12), pady=8, sticky="nse")

        # Preview Button
        self.btn_preview = ctk.CTkButton(
            action_frame,
            text="👁 Preview",
            width=70,
            height=28,
            font=font_caption_bold(),
            fg_color=ACCENT_TEAL,
            text_color=TEXT_INVERSE,
            hover_color=ACCENT_TEAL_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._handle_preview
        )
        self.btn_preview.pack(side="left", padx=2)

        if not self.is_pdf_page:
            # Rotate CCW (Left)
            self.btn_rot_ccw = ctk.CTkButton(
                action_frame,
                text="↺",
                width=28,
                height=28,
                font=font_body_bold(),
                fg_color=BTN_NEUTRAL_BG,
                text_color=BTN_NEUTRAL_TEXT,
                hover_color=ACCENT_EMERALD_HOVER,
                corner_radius=RADIUS_BTN,
                command=lambda: self.on_rotate_ccw(self.item_data) if self.on_rotate_ccw else None
            )
            self.btn_rot_ccw.pack(side="left", padx=2)

            # Rotate CW (Right)
            self.btn_rot_cw = ctk.CTkButton(
                action_frame,
                text="↻",
                width=28,
                height=28,
                font=font_body_bold(),
                fg_color=BTN_NEUTRAL_BG,
                text_color=BTN_NEUTRAL_TEXT,
                hover_color=ACCENT_EMERALD_HOVER,
                corner_radius=RADIUS_BTN,
                command=lambda: self.on_rotate_cw(self.item_data) if self.on_rotate_cw else None
            )
            self.btn_rot_cw.pack(side="left", padx=2)

            # Edit Studio Button
            self.btn_edit = ctk.CTkButton(
                action_frame,
                text="🎨 Edit",
                width=56,
                height=28,
                font=font_caption_bold(),
                fg_color=ACCENT_AMBER,
                text_color=TEXT_INVERSE,
                hover_color=ACCENT_AMBER_HOVER,
                corner_radius=RADIUS_BTN,
                command=lambda: self.on_edit(self.item_data) if self.on_edit else None
            )
            self.btn_edit.pack(side="left", padx=2)

            # Reorder Up
            self.btn_up = ctk.CTkButton(
                action_frame,
                text="▲",
                width=28,
                height=28,
                font=font_caption(),
                fg_color=BTN_NEUTRAL_BG,
                text_color=BTN_NEUTRAL_TEXT,
                hover_color=BTN_NEUTRAL_HOVER,
                corner_radius=RADIUS_BTN,
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
                font=font_caption(),
                fg_color=BTN_NEUTRAL_BG,
                text_color=BTN_NEUTRAL_TEXT,
                hover_color=BTN_NEUTRAL_HOVER,
                corner_radius=RADIUS_BTN,
                state="normal" if self.index < self.total_items - 1 else "disabled",
                command=lambda: self.on_move_down(self.index) if self.on_move_down else None
            )
            self.btn_down.pack(side="left", padx=2)

            # Rename Button
            self.btn_rename = ctk.CTkButton(
                action_frame,
                text="✏ Rename",
                width=70,
                height=28,
                font=font_caption(),
                fg_color=BTN_NEUTRAL_BG,
                text_color=BTN_NEUTRAL_TEXT,
                hover_color=BTN_NEUTRAL_HOVER,
                corner_radius=RADIUS_BTN,
                command=lambda: self.on_rename(self.item_data) if self.on_rename else None
            )
            self.btn_rename.pack(side="left", padx=2)

            # Remove from queue (Non-destructive)
            self.btn_remove = ctk.CTkButton(
                action_frame,
                text="✕",
                width=28,
                height=28,
                font=font_body_bold(),
                fg_color=BTN_NEUTRAL_BG,
                text_color=TEXT_MUTED,
                hover_color=BTN_DANGER_BG,
                corner_radius=RADIUS_BTN,
                command=lambda: self.on_remove(self.item_data) if self.on_remove else None
            )
            self.btn_remove.pack(side="left", padx=2)

            # Delete from Disk (Permanent)
            self.btn_delete = ctk.CTkButton(
                action_frame,
                text="🗑",
                width=28,
                height=28,
                font=font_caption(),
                fg_color=BTN_DANGER_BG,
                text_color=BTN_DANGER_TEXT,
                hover_color=ACCENT_ROSE_HOVER,
                corner_radius=RADIUS_BTN,
                command=lambda: self.on_delete(self.item_data) if self.on_delete else None
            )
            self.btn_delete.pack(side="left", padx=2)

        self._update_highlight()

    def _load_thumbnail(self):
        try:
            if self.is_pdf_page:
                pdf_path = self.item_data.get("pdf_path", "")
                page_idx = self.item_data.get("page_index", 0)
                pil_img = generate_pdf_page_thumbnail(pdf_path, page_number=page_idx, max_size=(74, 74))
            else:
                img_path = self.item_data.get("path", "")
                pil_img = generate_image_thumbnail(img_path, max_size=(74, 74))

            if pil_img:
                self.ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(pil_img.width, pil_img.height))
                self.thumb_label.configure(image=self.ctk_image, text="")
            else:
                self.thumb_label.configure(text="🖼", font=ctk.CTkFont(size=20))
        except Exception:
            self.thumb_label.configure(text="⚠️", font=ctk.CTkFont(size=14))

    def _handle_check_changed(self):
        self.is_selected = self.check_var.get()
        self.item_data["selected"] = self.is_selected
        self._update_highlight()
        if self.on_select:
            self.on_select(self.item_data, self.is_selected)

    def _update_highlight(self):
        if self.is_selected:
            self.configure(border_color=BORDER_ACTIVE, border_width=2)
        else:
            self.configure(border_color=BORDER_CARD, border_width=1)

    def _handle_preview(self):
        if self.on_preview:
            self.on_preview(self.item_data)

    def reload_thumbnail(self):
        """Reload thumbnail and metadata labels after an edit or rotation."""
        self._load_thumbnail()
        dims = self.item_data.get("dimensions", "Unknown")
        size_str = self.item_data.get("size_formatted", "")
        fmt = self.item_data.get("format", "IMG").upper()
        if not self.is_pdf_page:
            self.meta_label.configure(text=f"{dims} • {size_str}")
            filename = self.item_data.get("filename", os.path.basename(self.item_data.get("path", "")))
            display_name = filename if len(filename) <= 38 else filename[:24] + "..." + filename[-11:]
            self.name_label.configure(text=display_name)
            badge_cfg = BADGE_STYLES.get(fmt, BADGE_STYLES["DEFAULT"])
            self.fmt_badge.configure(text=f" {fmt} ", fg_color=badge_cfg["bg"], text_color=badge_cfg["fg"])

    def set_selected(self, selected: bool):
        self.check_var.set(selected)
        self.is_selected = selected
        self.item_data["selected"] = selected
        self._update_highlight()
