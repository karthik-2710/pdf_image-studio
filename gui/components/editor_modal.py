import os
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
from typing import Dict, Any, Callable, Optional, Tuple

from core.file_manager import (
    load_image_with_exif,
    apply_image_adjustments,
    save_image_to_disk,
    get_image_metadata,
    format_file_size
)


class EditorModal(ctk.CTkToplevel):
    """
    Comprehensive in-app Image Editor with rotation, flipping, cropping,
    brightness/contrast/sharpness adjustments, document scan filter, and disk saving.
    """

    def __init__(
        self,
        parent,
        item_data: Dict[str, Any],
        on_save_callback: Optional[Callable[[Dict[str, Any], Image.Image], None]] = None
    ):
        super().__init__(parent)
        self.item_data = item_data
        self.file_path = item_data.get("path", "")
        self.on_save_callback = on_save_callback

        self.title(f"🎨 Image Editor — {os.path.basename(self.file_path)}")
        self.geometry("1080x740")
        self.minsize(880, 600)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        # State variables
        self.original_img: Optional[Image.Image] = None
        self.current_edited_img: Optional[Image.Image] = None
        self.preview_ctk_img: Optional[ctk.CTkImage] = None

        self.rotation_degrees = 0
        self.flip_horizontal = False
        self.flip_vertical = False
        self.filter_mode = "normal"

        self._load_source_image()
        self._build_ui()
        self._render_preview()

        # Keyboard shortcuts
        self.bind("<Control-s>", lambda e: self._save_overwrite_disk())
        self.bind("<Escape>", lambda e: self.destroy())

    def _load_source_image(self):
        try:
            self.original_img = load_image_with_exif(self.file_path)
            self.current_edited_img = self.original_img.copy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image for editing:\n{e}")
            self.destroy()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=3)  # Preview Viewport
        self.grid_columnconfigure(1, weight=1)  # Controls Panel
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ==========================================
        # LEFT: Viewport Canvas / Frame
        # ==========================================
        left_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "#13151b"))
        left_frame.grid(row=0, column=0, padx=(15, 8), pady=12, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # Top viewport toolbar info
        vp_hdr = ctk.CTkFrame(left_frame, height=36, fg_color="transparent")
        vp_hdr.grid(row=0, column=0, padx=12, pady=6, sticky="ew")

        self.lbl_dims = ctk.CTkLabel(
            vp_hdr,
            text=f"Resolution: {self.original_img.width} × {self.original_img.height}",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_dims.pack(side="left")

        self.lbl_status_hint = ctk.CTkLabel(
            vp_hdr,
            text="Double click or use sliders to edit",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        self.lbl_status_hint.pack(side="right")

        # Preview Container
        self.preview_box = ctk.CTkFrame(left_frame, fg_color=("gray90", "#1c1e24"), corner_radius=8)
        self.preview_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.preview_box.pack_propagate(False)

        self.image_label = ctk.CTkLabel(self.preview_box, text="")
        self.image_label.pack(expand=True, fill="both")

        # ==========================================
        # RIGHT: Controls & Adjustments Sidebar
        # ==========================================
        ctrl_panel = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray88", "gray17"))
        ctrl_panel.grid(row=0, column=1, padx=(0, 15), pady=12, sticky="nsew")
        ctrl_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ctrl_panel, text="🛠 Image Tools", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 8))

        # --- SECTION 1: ROTATION & FLIP ---
        sec_rot = ctk.CTkFrame(ctrl_panel, fg_color=("gray82", "gray22"), corner_radius=8)
        sec_rot.pack(fill="x", padx=6, pady=6)

        ctk.CTkLabel(sec_rot, text="🔄 Orientation & Flip", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        rot_btn_row = ctk.CTkFrame(sec_rot, fg_color="transparent")
        rot_btn_row.pack(fill="x", padx=8, pady=(0, 4))
        rot_btn_row.grid_columnconfigure((0, 1, 2), weight=1)

        btn_rot_ccw = ctk.CTkButton(
            rot_btn_row,
            text="↺ 90° Left",
            height=30,
            font=ctk.CTkFont(size=11),
            command=lambda: self._rotate_step(-90)
        )
        btn_rot_ccw.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        btn_rot_cw = ctk.CTkButton(
            rot_btn_row,
            text="↻ 90° Right",
            height=30,
            font=ctk.CTkFont(size=11),
            command=lambda: self._rotate_step(90)
        )
        btn_rot_cw.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        btn_rot_180 = ctk.CTkButton(
            rot_btn_row,
            text="⟲ 180°",
            height=30,
            font=ctk.CTkFont(size=11),
            command=lambda: self._rotate_step(180)
        )
        btn_rot_180.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        flip_btn_row = ctk.CTkFrame(sec_rot, fg_color="transparent")
        flip_btn_row.pack(fill="x", padx=8, pady=(0, 8))
        flip_btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_flip_h = ctk.CTkButton(
            flip_btn_row,
            text="⇄ Flip Horizontal",
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray30"),
            text_color=("gray10", "gray95"),
            command=self._toggle_flip_h
        )
        self.btn_flip_h.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        self.btn_flip_v = ctk.CTkButton(
            flip_btn_row,
            text="⇅ Flip Vertical",
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray30"),
            text_color=("gray10", "gray95"),
            command=self._toggle_flip_v
        )
        self.btn_flip_v.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        # --- SECTION 2: CROP & MARGINS ---
        sec_crop = ctk.CTkFrame(ctrl_panel, fg_color=("gray82", "gray22"), corner_radius=8)
        sec_crop.pack(fill="x", padx=6, pady=6)

        ctk.CTkLabel(sec_crop, text="✂ Crop / Trim Margins", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        # Crop Left & Right Sliders
        ctk.CTkLabel(sec_crop, text="Trim Left / Right (%):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        self.slider_crop_lr = ctk.CTkSlider(sec_crop, from_=0, to=30, number_of_steps=30, command=lambda v: self._apply_and_render())
        self.slider_crop_lr.set(0)
        self.slider_crop_lr.pack(fill="x", padx=10, pady=(0, 4))

        # Crop Top & Bottom Sliders
        ctk.CTkLabel(sec_crop, text="Trim Top / Bottom (%):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        self.slider_crop_tb = ctk.CTkSlider(sec_crop, from_=0, to=30, number_of_steps=30, command=lambda v: self._apply_and_render())
        self.slider_crop_tb.set(0)
        self.slider_crop_tb.pack(fill="x", padx=10, pady=(0, 8))

        # --- SECTION 3: COLOR ENHANCEMENTS & FILTERS ---
        sec_adj = ctk.CTkFrame(ctrl_panel, fg_color=("gray82", "gray22"), corner_radius=8)
        sec_adj.pack(fill="x", padx=6, pady=6)

        ctk.CTkLabel(sec_adj, text="✨ Enhancements & Scan Filters", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        # Filter mode selector
        ctk.CTkLabel(sec_adj, text="Filter Mode:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(2, 0))
        self.opt_filter = ctk.CTkOptionMenu(
            sec_adj,
            values=[
                "Normal (Original Colors)",
                "📄 Document Scan (High-Contrast Text)",
                "⚫ Grayscale (Black & White)",
                "🌅 Warm Filter",
                "❄️ Cool Filter"
            ],
            command=self._on_filter_changed
        )
        self.opt_filter.set("Normal (Original Colors)")
        self.opt_filter.pack(fill="x", padx=10, pady=(0, 8))

        # Brightness Slider
        self.lbl_brightness = ctk.CTkLabel(sec_adj, text="Brightness (1.00x):", font=ctk.CTkFont(size=11))
        self.lbl_brightness.pack(anchor="w", padx=10, pady=(2, 0))
        self.slider_bright = ctk.CTkSlider(sec_adj, from_=0.5, to=1.5, number_of_steps=20, command=self._on_bright_slider)
        self.slider_bright.set(1.0)
        self.slider_bright.pack(fill="x", padx=10, pady=(0, 4))

        # Contrast Slider
        self.lbl_contrast = ctk.CTkLabel(sec_adj, text="Contrast (1.00x):", font=ctk.CTkFont(size=11))
        self.lbl_contrast.pack(anchor="w", padx=10, pady=(2, 0))
        self.slider_contrast = ctk.CTkSlider(sec_adj, from_=0.5, to=2.0, number_of_steps=30, command=self._on_contrast_slider)
        self.slider_contrast.set(1.0)
        self.slider_contrast.pack(fill="x", padx=10, pady=(0, 4))

        # Sharpness Slider
        self.lbl_sharp = ctk.CTkLabel(sec_adj, text="Sharpness (1.00x):", font=ctk.CTkFont(size=11))
        self.lbl_sharp.pack(anchor="w", padx=10, pady=(2, 0))
        self.slider_sharp = ctk.CTkSlider(sec_adj, from_=0.0, to=3.0, number_of_steps=30, command=self._on_sharp_slider)
        self.slider_sharp.set(1.0)
        self.slider_sharp.pack(fill="x", padx=10, pady=(0, 8))

        # Reset All Button
        btn_reset = ctk.CTkButton(
            ctrl_panel,
            text="↺ Reset All Edits",
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray28"),
            text_color=("gray10", "gray95"),
            command=self._reset_all_edits
        )
        btn_reset.pack(fill="x", padx=6, pady=8)

        # ==========================================
        # BOTTOM BAR: Save & Overwrite Actions
        # ==========================================
        bottom_bar = ctk.CTkFrame(self, height=52, corner_radius=0, fg_color=("gray85", "gray17"))
        bottom_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bottom_bar.grid_columnconfigure(0, weight=1)

        lbl_save_hint = ctk.CTkLabel(
            bottom_bar,
            text="💡 Tip: 'Save & Overwrite' updates the image file in your Windows folder immediately.",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        lbl_save_hint.pack(side="left", padx=15)

        btn_cancel = ctk.CTkButton(
            bottom_bar,
            text="Cancel",
            width=90,
            height=34,
            fg_color=("gray75", "gray30"),
            text_color=("gray10", "gray90"),
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(5, 15), pady=8)

        btn_save_copy = ctk.CTkButton(
            bottom_bar,
            text="💾 Save as Copy...",
            width=130,
            height=34,
            fg_color=("gray70", "gray35"),
            text_color=("gray10", "gray95"),
            command=self._save_as_new_copy
        )
        btn_save_copy.pack(side="right", padx=5, pady=8)

        btn_save_overwrite = ctk.CTkButton(
            bottom_bar,
            text="💾 Save & Overwrite File",
            width=170,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#2e7d32", "#1b5e20"),
            hover_color=("#1b5e20", "#0e3a13"),
            command=self._save_overwrite_disk
        )
        btn_save_overwrite.pack(side="right", padx=5, pady=8)

    # ----------------------------------------------------
    # Transformations & Adjustments Handlers
    # ----------------------------------------------------
    def _rotate_step(self, degrees: int):
        self.rotation_degrees = (self.rotation_degrees + degrees) % 360
        self._apply_and_render()

    def _toggle_flip_h(self):
        self.flip_horizontal = not self.flip_horizontal
        self.btn_flip_h.configure(fg_color=("#3a7ebf", "#1f538d") if self.flip_horizontal else ("gray75", "gray30"))
        self._apply_and_render()

    def _toggle_flip_v(self):
        self.flip_vertical = not self.flip_vertical
        self.btn_flip_v.configure(fg_color=("#3a7ebf", "#1f538d") if self.flip_vertical else ("gray75", "gray30"))
        self._apply_and_render()

    def _on_filter_changed(self, choice: str):
        if "Document Scan" in choice:
            self.filter_mode = "document_scan"
        elif "Grayscale" in choice:
            self.filter_mode = "grayscale"
        elif "Warm" in choice:
            self.filter_mode = "warm"
        elif "Cool" in choice:
            self.filter_mode = "cool"
        else:
            self.filter_mode = "normal"
        self._apply_and_render()

    def _on_bright_slider(self, val: float):
        self.lbl_brightness.configure(text=f"Brightness ({val:.2f}x):")
        self._apply_and_render()

    def _on_contrast_slider(self, val: float):
        self.lbl_contrast.configure(text=f"Contrast ({val:.2f}x):")
        self._apply_and_render()

    def _on_sharp_slider(self, val: float):
        self.lbl_sharp.configure(text=f"Sharpness ({val:.2f}x):")
        self._apply_and_render()

    def _apply_and_render(self):
        if not self.original_img:
            return

        # Calculate crop box if sliders > 0
        w, h = self.original_img.size
        trim_lr = self.slider_crop_lr.get() / 100.0
        trim_tb = self.slider_crop_tb.get() / 100.0

        crop_box = None
        if trim_lr > 0 or trim_tb > 0:
            crop_l = int(w * trim_lr)
            crop_r = int(w * (1.0 - trim_lr))
            crop_t = int(h * trim_tb)
            crop_b = int(h * (1.0 - trim_tb))
            crop_box = (crop_l, crop_t, crop_r, crop_b)

        brightness = self.slider_bright.get()
        contrast = self.slider_contrast.get()
        sharpness = self.slider_sharp.get()

        self.current_edited_img = apply_image_adjustments(
            img=self.original_img,
            rotation=self.rotation_degrees,
            flip_h=self.flip_horizontal,
            flip_v=self.flip_vertical,
            crop_box=crop_box,
            brightness=brightness,
            contrast=contrast,
            sharpness=sharpness,
            filter_mode=self.filter_mode
        )

        self._render_preview()

    def _render_preview(self):
        if not self.current_edited_img:
            return

        cur_w, cur_h = self.current_edited_img.size
        self.lbl_dims.configure(text=f"Resolution: {cur_w} × {cur_h} px")

        # Scale to fit preview box (approx 680x550 max)
        disp_img = self.current_edited_img.copy()
        if disp_img.mode not in ('RGB', 'RGBA'):
            disp_img = disp_img.convert('RGBA')

        disp_img.thumbnail((720, 560), Image.Resampling.LANCZOS)
        self.preview_ctk_img = ctk.CTkImage(light_image=disp_img, dark_image=disp_img, size=(disp_img.width, disp_img.height))
        self.image_label.configure(image=self.preview_ctk_img, text="")

    def _reset_all_edits(self):
        self.rotation_degrees = 0
        self.flip_horizontal = False
        self.flip_vertical = False
        self.filter_mode = "normal"
        self.opt_filter.set("Normal (Original Colors)")
        self.slider_bright.set(1.0)
        self.lbl_brightness.configure(text="Brightness (1.00x):")
        self.slider_contrast.set(1.0)
        self.lbl_contrast.configure(text="Contrast (1.00x):")
        self.slider_sharp.set(1.0)
        self.lbl_sharp.configure(text="Sharpness (1.00x):")
        self.slider_crop_lr.set(0)
        self.slider_crop_tb.set(0)
        self.btn_flip_h.configure(fg_color=("gray75", "gray30"))
        self.btn_flip_v.configure(fg_color=("gray75", "gray30"))

        if self.original_img:
            self.current_edited_img = self.original_img.copy()
            self._render_preview()

    # ----------------------------------------------------
    # Disk Saving Handlers
    # ----------------------------------------------------
    def _save_overwrite_disk(self):
        if not self.current_edited_img:
            return

        confirm = messagebox.askyesno(
            "Confirm Overwrite",
            f"Are you sure you want to save and overwrite the original file:\n\n{os.path.basename(self.file_path)}\n\nThis will update the file in its folder on disk.",
            icon="question"
        )
        if not confirm:
            return

        try:
            save_image_to_disk(self.current_edited_img, self.file_path)
            # Update item metadata in queue
            meta = get_image_metadata(self.file_path)
            self.item_data.update(meta)

            if self.on_save_callback:
                self.on_save_callback(self.item_data, self.current_edited_img)

            messagebox.showinfo("Saved", f"Successfully saved and updated '{os.path.basename(self.file_path)}' on disk!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save image to disk:\n{e}")

    def _save_as_new_copy(self):
        if not self.current_edited_img:
            return

        dirname, filename = os.path.split(self.file_path)
        base, ext = os.path.splitext(filename)
        default_target = os.path.join(dirname, f"{base}_edited{ext}")

        target_path = filedialog.asksaveasfilename(
            initialdir=dirname,
            initialfile=os.path.basename(default_target),
            defaultextension=ext,
            filetypes=[("Image Files", f"*{ext}"), ("All Files", "*.*")]
        )
        if not target_path:
            return

        try:
            save_image_to_disk(self.current_edited_img, target_path)
            meta = get_image_metadata(target_path)
            self.item_data.update(meta)

            if self.on_save_callback:
                self.on_save_callback(self.item_data, self.current_edited_img)

            messagebox.showinfo("Saved Copy", f"Saved new copy to:\n{target_path}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save copy:\n{e}")
