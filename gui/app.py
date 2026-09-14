import os
import sys
import customtkinter as ctk
from PIL import Image

from gui.theme import (
    BG_APP,
    BG_SIDEBAR,
    BG_CARD,
    BORDER_SUBTLE,
    BORDER_CARD,
    TEXT_MAIN,
    TEXT_MUTED,
    TEXT_DIM,
    ACCENT_EMERALD,
    ACCENT_EMERALD_HOVER,
    BTN_NEUTRAL_BG,
    BTN_NEUTRAL_HOVER,
    BTN_NEUTRAL_TEXT,
    RADIUS_CONTAINER,
    RADIUS_CARD,
    RADIUS_BTN,
    RADIUS_INPUT,
    RADIUS_PILL,
    RADIUS_BADGE,
    font_brand,
    font_h2,
    font_title,
    font_body,
    font_body_bold,
    font_caption,
    font_caption_bold,
    font_badge
)
from gui.img_to_pdf_tab import ImgToPdfTab
from gui.pdf_to_img_tab import PdfToImgTab


class App(ctk.CTk):
    """
    Main application shell for Image & PDF Converter Studio.
    Designed with a modern SaaS desktop dashboard aesthetic, responsive grid,
    and unified design tokens.
    """

    def __init__(self):
        super().__init__()

        # Window Appearance & Geometry
        self.title("⚡ PDF Studio Pro — Image & PDF Workspace")
        self.geometry("1240x820")
        self.minsize(1024, 680)

        # Set default theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        # Base background
        self.configure(fg_color=BG_APP)

        # Window Icon
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(sys.executable), "assets", "app_icon.ico")

        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Configure Grid Layout (2 Columns: Sidebar + Main Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_tab = "img_to_pdf"

        self._build_sidebar()
        self._build_main_container()
        self._show_tab("img_to_pdf")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=236,
            corner_radius=0,
            fg_color=BG_SIDEBAR,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)
        self.sidebar.grid_propagate(False)

        # ----------------------------------------------------
        # Brand Header Card
        # ----------------------------------------------------
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=16, pady=(20, 16), sticky="ew")

        logo_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        logo_row.pack(anchor="w")

        lbl_icon = ctk.CTkLabel(
            logo_row,
            text="⚡",
            font=font_brand(),
            text_color=ACCENT_EMERALD
        )
        lbl_icon.pack(side="left", padx=(0, 6))

        lbl_logo = ctk.CTkLabel(
            logo_row,
            text="PDF Studio",
            font=font_brand(),
            text_color=TEXT_MAIN
        )
        lbl_logo.pack(side="left")

        pro_badge = ctk.CTkLabel(
            logo_row,
            text="PRO",
            font=font_badge(),
            fg_color=("#ECFDF5", "#064E3B"),
            text_color=("#059669", "#34D399"),
            corner_radius=RADIUS_BADGE,
            width=32,
            height=18
        )
        pro_badge.pack(side="left", padx=(6, 0))

        lbl_sub = ctk.CTkLabel(
            brand_frame,
            text="Image ⇄ PDF Conversion Suite",
            font=font_caption(),
            text_color=TEXT_MUTED
        )
        lbl_sub.pack(anchor="w", pady=(3, 0))

        # ----------------------------------------------------
        # Navigation Section
        # ----------------------------------------------------
        lbl_nav_hdr = ctk.CTkLabel(
            self.sidebar,
            text="WORKSPACES",
            font=font_badge(),
            text_color=TEXT_DIM
        )
        lbl_nav_hdr.grid(row=1, column=0, padx=18, pady=(8, 4), sticky="w")

        # Navigation Buttons (Pill styling)
        self.btn_nav_img_to_pdf = ctk.CTkButton(
            self.sidebar,
            text="🖼   Images to PDF",
            height=40,
            font=font_title(),
            anchor="w",
            corner_radius=RADIUS_BTN,
            command=lambda: self._show_tab("img_to_pdf")
        )
        self.btn_nav_img_to_pdf.grid(row=2, column=0, padx=12, pady=3, sticky="ew")

        self.btn_nav_pdf_to_img = ctk.CTkButton(
            self.sidebar,
            text="📄   PDF to Images",
            height=40,
            font=font_title(),
            anchor="w",
            corner_radius=RADIUS_BTN,
            command=lambda: self._show_tab("pdf_to_img")
        )
        self.btn_nav_pdf_to_img.grid(row=3, column=0, padx=12, pady=3, sticky="ew")

        # Sidebar Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_SUBTLE)
        sep.grid(row=4, column=0, padx=16, pady=14, sticky="ew")

        # ----------------------------------------------------
        # Quick Features & Shortcuts Card
        # ----------------------------------------------------
        features_box = ctk.CTkFrame(
            self.sidebar,
            corner_radius=RADIUS_CARD,
            fg_color=BTN_NEUTRAL_BG,
            border_width=1,
            border_color=BORDER_CARD
        )
        features_box.grid(row=5, column=0, padx=12, pady=4, sticky="nsew")

        ctk.CTkLabel(
            features_box,
            text="⚡ Studio Highlights",
            font=font_caption_bold(),
            text_color=ACCENT_EMERALD
        ).pack(anchor="w", padx=12, pady=(10, 6))

        features_list = [
            ("🎨 Image Studio", "Rotate, crop & filters"),
            ("⚡ Compression", "Extreme 90% size reduction"),
            ("🏷 Batch Rename", "Pattern & sequence tools"),
            ("🔍 DPI Controls", "72 up to 600 DPI output")
        ]

        for title, desc in features_list:
            item_row = ctk.CTkFrame(features_box, fg_color="transparent")
            item_row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(
                item_row,
                text=title,
                font=font_caption_bold(),
                text_color=TEXT_MAIN,
                anchor="w"
            ).pack(anchor="w")
            ctk.CTkLabel(
                item_row,
                text=desc,
                font=font_badge(),
                text_color=TEXT_MUTED,
                anchor="w"
            ).pack(anchor="w")

        # ----------------------------------------------------
        # Bottom Appearance & System Footer
        # ----------------------------------------------------
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.grid(row=6, column=0, padx=12, pady=12, sticky="ew")

        ctk.CTkLabel(
            bottom_frame,
            text="APPEARANCE",
            font=font_badge(),
            text_color=TEXT_DIM
        ).pack(anchor="w", padx=4, pady=(0, 4))

        self.theme_menu = ctk.CTkOptionMenu(
            bottom_frame,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode,
            height=30,
            font=font_caption(),
            fg_color=BTN_NEUTRAL_BG,
            text_color=TEXT_MAIN,
            button_color=BORDER_SUBTLE,
            button_hover_color=BORDER_CARD,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_MAIN,
            corner_radius=RADIUS_INPUT
        )
        self.theme_menu.set("Dark")
        self.theme_menu.pack(fill="x", padx=2, pady=(0, 8))

        status_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=4)

        ctk.CTkLabel(
            status_row,
            text="🟢 Engine Ready",
            font=font_badge(),
            text_color=("#059669", "#34D399")
        ).pack(side="left")

        ctk.CTkLabel(
            status_row,
            text="v2.1",
            font=font_badge(),
            text_color=TEXT_DIM
        ).pack(side="right")

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
        self.current_tab = tab_name
        if tab_name == "img_to_pdf":
            self.tab_img_to_pdf.tkraise()
            self.btn_nav_img_to_pdf.configure(
                fg_color=ACCENT_EMERALD,
                text_color="#FFFFFF",
                hover_color=ACCENT_EMERALD_HOVER
            )
            self.btn_nav_pdf_to_img.configure(
                fg_color="transparent",
                text_color=TEXT_MUTED,
                hover_color=BTN_NEUTRAL_BG
            )
        else:
            self.tab_pdf_to_img.tkraise()
            self.btn_nav_pdf_to_img.configure(
                fg_color=ACCENT_EMERALD,
                text_color="#FFFFFF",
                hover_color=ACCENT_EMERALD_HOVER
            )
            self.btn_nav_img_to_pdf.configure(
                fg_color="transparent",
                text_color=TEXT_MUTED,
                hover_color=BTN_NEUTRAL_BG
            )

    def _change_appearance_mode(self, mode: str):
        ctk.set_appearance_mode(mode)
