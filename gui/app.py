import os
import customtkinter as ctk
from PIL import Image

from gui.img_to_pdf_tab import ImgToPdfTab
from gui.pdf_to_img_tab import PdfToImgTab


class App(ctk.CTk):
    """
    Main application window for Image & PDF Converter Studio.
    """

    def __init__(self):
        super().__init__()

        # Window Appearance & Geometry
        self.title("Image & PDF Converter Studio")
        self.geometry("1180x780")
        self.minsize(980, 640)

        # Set default theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Configure Grid Layout (2 Columns: Sidebar + Main Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_container()
        self._show_tab("img_to_pdf")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("gray85", "#181a20"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)
        self.sidebar.grid_propagate(False)

        # App Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=16, pady=(20, 25), sticky="ew")

        lbl_logo = ctk.CTkLabel(
            brand_frame,
            text="⚡ Studio",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1976d2", "#42a5f5")
        )
        lbl_logo.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            brand_frame,
            text="Image ⇄ PDF Converter",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60")
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Navigation Buttons
        self.btn_nav_img_to_pdf = ctk.CTkButton(
            self.sidebar,
            text="🖼  Images to PDF",
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            corner_radius=8,
            command=lambda: self._show_tab("img_to_pdf")
        )
        self.btn_nav_img_to_pdf.grid(row=1, column=0, padx=12, pady=6, sticky="ew")

        self.btn_nav_pdf_to_img = ctk.CTkButton(
            self.sidebar,
            text="📄  PDF to Images",
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            corner_radius=8,
            command=lambda: self._show_tab("pdf_to_img")
        )
        self.btn_nav_pdf_to_img.grid(row=2, column=0, padx=12, pady=6, sticky="ew")

        # Sidebar Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=("gray75", "gray30"))
        sep.grid(row=3, column=0, padx=16, pady=20, sticky="ew")

        # Quick Tips / Feature Highlights Box
        tips_box = ctk.CTkFrame(self.sidebar, corner_radius=8, fg_color=("gray80", "#21242b"))
        tips_box.grid(row=4, column=0, padx=12, pady=5, sticky="ew")

        ctk.CTkLabel(
            tips_box,
            text="💡 Quick Actions",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#1976d2", "#64b5f6")
        ).pack(anchor="w", padx=10, pady=(8, 4))

        tips_text = (
            "• Drag or use ▲/▼ to reorder\n"
            "• 👁 Preview in full resolution\n"
            "• 🏷 Batch rename anytime\n"
            "• 🗑 Safe remove & delete"
        )
        ctk.CTkLabel(
            tips_box,
            text=tips_text,
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray70"),
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # Bottom Theme & Info Section
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.grid(row=6, column=0, padx=12, pady=16, sticky="ew")

        ctk.CTkLabel(bottom_frame, text="Appearance:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=4, pady=(0, 4))
        self.theme_menu = ctk.CTkOptionMenu(
            bottom_frame,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode,
            height=28
        )
        self.theme_menu.set("Dark")
        self.theme_menu.pack(fill="x", padx=2, pady=(0, 10))

        ctk.CTkLabel(
            bottom_frame,
            text="v1.0.0 • Offline & Fast",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        ).pack(anchor="center")

    def _build_main_container(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Tab 1: Images to PDF
        self.tab_img_to_pdf = ImgToPdfTab(self.main_container)
        self.tab_img_to_pdf.grid(row=0, column=0, sticky="nsew")

        # Tab 2: PDF to Images
        self.tab_pdf_to_img = PdfToImgTab(self.main_container)
        self.tab_pdf_to_img.grid(row=0, column=0, sticky="nsew")

    def _show_tab(self, tab_name: str):
        if tab_name == "img_to_pdf":
            self.tab_img_to_pdf.tkraise()
            self.btn_nav_img_to_pdf.configure(fg_color=("#1976d2", "#1f538d"), text_color="white")
            self.btn_nav_pdf_to_img.configure(fg_color="transparent", text_color=("gray10", "gray80"))
        else:
            self.tab_pdf_to_img.tkraise()
            self.btn_nav_pdf_to_img.configure(fg_color=("#1976d2", "#1f538d"), text_color="white")
            self.btn_nav_img_to_pdf.configure(fg_color="transparent", text_color=("gray10", "gray80"))

    def _change_appearance_mode(self, mode: str):
        ctk.set_appearance_mode(mode)
