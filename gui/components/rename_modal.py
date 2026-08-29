import os
import customtkinter as ctk
from typing import List, Dict, Any, Callable, Optional

from core.file_manager import (
    safe_rename_file,
    generate_batch_rename_plan,
    apply_batch_rename,
    sanitize_filename
)


class SingleRenameModal(ctk.CTkToplevel):
    """
    Dialog for renaming a single image file on disk.
    """

    def __init__(
        self,
        parent,
        item_data: Dict[str, Any],
        on_success: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        super().__init__(parent)
        self.item_data = item_data
        self.on_success = on_success

        self.title("✏ Rename File")
        self.geometry("520x260")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.old_path = item_data.get("path", "")
        self.filename = os.path.basename(self.old_path)
        self.base_name, self.ext = os.path.splitext(self.filename)

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Rename Image File",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(padx=20, pady=(15, 5), anchor="w")

        info = ctk.CTkLabel(
            self,
            text=f"Current: {self.filename}",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        info.pack(padx=20, pady=(0, 15), anchor="w")

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)

        self.name_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter new filename",
            height=36,
            font=ctk.CTkFont(size=13)
        )
        self.name_entry.insert(0, self.base_name)
        self.name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.name_entry.focus()
        self.name_entry.bind("<Return>", lambda e: self._save_rename())

        ext_label = ctk.CTkLabel(
            input_frame,
            text=self.ext,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("gray85", "gray25"),
            corner_radius=6,
            width=50,
            height=36
        )
        ext_label.grid(row=0, column=1)

        self.error_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#e53935", "#ff5252")
        )
        self.error_label.pack(padx=20, pady=(5, 10), anchor="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 15))

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            fg_color=("gray75", "gray30"),
            text_color=("gray10", "gray90"),
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_save = ctk.CTkButton(
            btn_frame,
            text="Save Rename",
            width=120,
            fg_color=("#3a7ebf", "#1f538d"),
            command=self._save_rename
        )
        btn_save.pack(side="right")

    def _save_rename(self):
        new_base = self.name_entry.get().strip()
        if not new_base:
            self.error_label.configure(text="Filename cannot be empty.")
            return

        new_full_name = f"{new_base}{self.ext}"
        try:
            new_path = safe_rename_file(self.old_path, new_full_name)
            self.item_data["path"] = new_path
            self.item_data["filename"] = os.path.basename(new_path)
            if self.on_success:
                self.on_success(self.item_data)
            self.destroy()
        except Exception as e:
            self.error_label.configure(text=f"Rename failed: {e}")


class BatchRenameModal(ctk.CTkToplevel):
    """
    Modal dialog for batch renaming multiple selected images with real-time preview table.
    """

    def __init__(
        self,
        parent,
        items: List[Dict[str, Any]],
        on_success: Optional[Callable[[List[Dict[str, Any]]], None]] = None
    ):
        super().__init__(parent)
        self.items = items
        self.on_success = on_success

        self.title("🏷 Batch Rename Images - Image & PDF Studio")
        self.geometry("820x620")
        self.minsize(700, 500)
        self.transient(parent)
        self.grab_set()

        self.current_plan: List[Dict[str, str]] = []

        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="ew")

        ctk.CTkLabel(
            header,
            text=f"Batch Rename ({len(self.items)} selected images)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        # 2. Rename Options Panel
        opt_box = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray90", "gray17"))
        opt_box.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        opt_box.grid_columnconfigure((1, 3), weight=1)

        # Mode Selector
        ctk.CTkLabel(opt_box, text="Mode:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=12, pady=10, sticky="w")
        self.mode_var = ctk.StringVar(value="numbering")
        self.mode_menu = ctk.CTkOptionMenu(
            opt_box,
            values=["Sequential Numbering", "Prefix & Suffix", "Find & Replace", "Custom Template"],
            command=self._on_mode_change,
            width=180
        )
        self.mode_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Fields container (switches based on mode)
        self.fields_frame = ctk.CTkFrame(opt_box, fg_color="transparent")
        self.fields_frame.grid(row=1, column=0, columnspan=4, padx=12, pady=(0, 10), sticky="ew")
        self._build_mode_fields()

        # 3. Live Preview Section
        preview_container = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray92", "gray14"))
        preview_container.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        preview_container.grid_rowconfigure(1, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)

        # Table Header
        tbl_hdr = ctk.CTkFrame(preview_container, height=32, corner_radius=4, fg_color=("gray82", "gray22"))
        tbl_hdr.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")
        tbl_hdr.grid_columnconfigure(1, weight=1)
        tbl_hdr.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(tbl_hdr, text="#", width=40, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=4)
        ctk.CTkLabel(tbl_hdr, text="Original Name", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=0, column=1, padx=8, sticky="w")
        ctk.CTkLabel(tbl_hdr, text="New Proposed Name", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=0, column=2, padx=8, sticky="w")

        # Scrollable Preview List
        self.preview_scroll = ctk.CTkScrollableFrame(preview_container, fg_color="transparent")
        self.preview_scroll.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self.preview_scroll.grid_columnconfigure(1, weight=1)
        self.preview_scroll.grid_columnconfigure(2, weight=1)

        # 4. Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.grid(row=3, column=0, padx=20, pady=(5, 15), sticky="ew")

        self.status_label = ctk.CTkLabel(bottom_bar, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="left")

        btn_cancel = ctk.CTkButton(
            bottom_bar,
            text="Cancel",
            width=100,
            fg_color=("gray75", "gray30"),
            text_color=("gray10", "gray90"),
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_apply = ctk.CTkButton(
            bottom_bar,
            text=f"Apply Renaming ({len(self.items)} files)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#2e7d32", "#1b5e20"),
            hover_color=("#1b5e20", "#0e3a13"),
            command=self._apply_renaming
        )
        self.btn_apply.pack(side="right")

    def _build_mode_fields(self):
        # Clear previous fields
        for widget in self.fields_frame.winfo_children():
            widget.destroy()

        mode = self.mode_menu.get()

        if mode == "Sequential Numbering":
            ctk.CTkLabel(self.fields_frame, text="Prefix:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.entry_prefix = ctk.CTkEntry(self.fields_frame, placeholder_text="e.g. photo", width=120)
            self.entry_prefix.insert(0, "img")
            self.entry_prefix.grid(row=0, column=1, padx=5, pady=5)
            self.entry_prefix.bind("<KeyRelease>", lambda e: self._update_preview())

            ctk.CTkLabel(self.fields_frame, text="Start Num:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
            self.entry_start = ctk.CTkEntry(self.fields_frame, width=60)
            self.entry_start.insert(0, "1")
            self.entry_start.grid(row=0, column=3, padx=5, pady=5)
            self.entry_start.bind("<KeyRelease>", lambda e: self._update_preview())

            ctk.CTkLabel(self.fields_frame, text="Digits (Padding):").grid(row=0, column=4, padx=5, pady=5, sticky="w")
            self.entry_pad = ctk.CTkEntry(self.fields_frame, width=50)
            self.entry_pad.insert(0, "3")
            self.entry_pad.grid(row=0, column=5, padx=5, pady=5)
            self.entry_pad.bind("<KeyRelease>", lambda e: self._update_preview())

        elif mode == "Prefix & Suffix":
            ctk.CTkLabel(self.fields_frame, text="Add Prefix:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.entry_prefix = ctk.CTkEntry(self.fields_frame, placeholder_text="e.g. new_", width=150)
            self.entry_prefix.grid(row=0, column=1, padx=5, pady=5)
            self.entry_prefix.bind("<KeyRelease>", lambda e: self._update_preview())

            ctk.CTkLabel(self.fields_frame, text="Add Suffix:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
            self.entry_suffix = ctk.CTkEntry(self.fields_frame, placeholder_text="e.g. _edit", width=150)
            self.entry_suffix.grid(row=0, column=3, padx=5, pady=5)
            self.entry_suffix.bind("<KeyRelease>", lambda e: self._update_preview())

        elif mode == "Find & Replace":
            ctk.CTkLabel(self.fields_frame, text="Find Text:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.entry_find = ctk.CTkEntry(self.fields_frame, placeholder_text="Text to search", width=150)
            self.entry_find.grid(row=0, column=1, padx=5, pady=5)
            self.entry_find.bind("<KeyRelease>", lambda e: self._update_preview())

            ctk.CTkLabel(self.fields_frame, text="Replace With:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
            self.entry_replace = ctk.CTkEntry(self.fields_frame, placeholder_text="Replacement text", width=150)
            self.entry_replace.grid(row=0, column=3, padx=5, pady=5)
            self.entry_replace.bind("<KeyRelease>", lambda e: self._update_preview())

        elif mode == "Custom Template":
            ctk.CTkLabel(self.fields_frame, text="Template ({name}, {index}, {date}):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.entry_template = ctk.CTkEntry(self.fields_frame, placeholder_text="{name}_{index}", width=250)
            self.entry_template.insert(0, "{name}_{index}")
            self.entry_template.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            self.entry_template.bind("<KeyRelease>", lambda e: self._update_preview())

    def _on_mode_change(self, choice):
        self._build_mode_fields()
        self._update_preview()

    def _update_preview(self):
        mode_label = self.mode_menu.get()
        file_paths = [item["path"] for item in self.items if "path" in item]

        prefix = getattr(self, "entry_prefix", None).get() if hasattr(self, "entry_prefix") else ""
        suffix = getattr(self, "entry_suffix", None).get() if hasattr(self, "entry_suffix") else ""
        find_text = getattr(self, "entry_find", None).get() if hasattr(self, "entry_find") else ""
        replace_text = getattr(self, "entry_replace", None).get() if hasattr(self, "entry_replace") else ""
        
        try:
            start_num = int(getattr(self, "entry_start", None).get()) if hasattr(self, "entry_start") else 1
        except ValueError:
            start_num = 1

        try:
            pad = int(getattr(self, "entry_pad", None).get()) if hasattr(self, "entry_pad") else 3
        except ValueError:
            pad = 3

        template = getattr(self, "entry_template", None).get() if hasattr(self, "entry_template") else "{name}_{index}"

        mode_map = {
            "Sequential Numbering": "numbering",
            "Prefix & Suffix": "prefix_suffix",
            "Find & Replace": "find_replace",
            "Custom Template": "custom_template"
        }
        pattern_mode = mode_map.get(mode_label, "numbering")

        self.current_plan = generate_batch_rename_plan(
            file_paths=file_paths,
            pattern_mode=pattern_mode,
            prefix=prefix,
            suffix=suffix,
            find_text=find_text,
            replace_text=replace_text,
            start_number=start_num,
            digits_padding=pad,
            template=template
        )

        # Re-render preview scroll rows
        for widget in self.preview_scroll.winfo_children():
            widget.destroy()

        for idx, row in enumerate(self.current_plan):
            bg_color = "transparent" if idx % 2 == 0 else ("gray88", "gray18")
            row_frame = ctk.CTkFrame(self.preview_scroll, fg_color=bg_color, corner_radius=3)
            row_frame.pack(fill="x", pady=1)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)

            ctk.CTkLabel(row_frame, text=str(idx + 1), width=40, font=ctk.CTkFont(size=11), text_color="gray50").grid(row=0, column=0, padx=4)
            ctk.CTkLabel(row_frame, text=row["old_name"], font=ctk.CTkFont(size=12), anchor="w").grid(row=0, column=1, padx=8, sticky="w")
            
            changed = row["old_name"] != row["new_name"]
            text_color = ("#1b5e20", "#81c784") if changed else ("gray30", "gray70")
            ctk.CTkLabel(row_frame, text=row["new_name"], font=ctk.CTkFont(size=12, weight="bold" if changed else "normal"), text_color=text_color, anchor="w").grid(row=0, column=2, padx=8, sticky="w")

    def _apply_renaming(self):
        if not self.current_plan:
            return

        self.btn_apply.configure(state="disabled", text="Renaming...")
        results = apply_batch_rename(self.current_plan)

        # Update parent item references
        path_to_new_path = {r["old_path"]: r["new_path"] for r in results if r["success"]}
        for item in self.items:
            old_p = item.get("path")
            if old_p in path_to_new_path:
                item["path"] = path_to_new_path[old_p]
                item["filename"] = os.path.basename(path_to_new_path[old_p])

        if self.on_success:
            self.on_success(self.items)

        self.destroy()
