"""
Centralized Theme & Design System for Image & PDF Converter Studio (PDF Studio Pro).
Provides refined SaaS design tokens, typography hierarchy, geometric radii, and component styling.
"""

import customtkinter as ctk

# ============================================================================
# 1. COLOR PALETTE (Obsidian Slate & Emerald Accent)
# ============================================================================

# Surface & Canvas Backgrounds (Light Mode, Dark Mode)
BG_APP = ("#F8FAFC", "#0B0F17")          # Deep obsidian canvas
BG_SIDEBAR = ("#FFFFFF", "#0E1420")      # Sidebar panel
BG_CARD = ("#FFFFFF", "#121A2B")         # Primary elevated cards & inspector
BG_CARD_ALT = ("#F1F5F9", "#172136")     # Secondary grouped surface
BG_INSPECTOR = ("#FFFFFF", "#111827")    # Right inspector panel
BG_CONTAINER = ("#F8FAFC", "#0E1420")    # Sub-containers
BG_INPUT = ("#FFFFFF", "#0C111C")        # Text inputs & dropdown fields
BG_HOVER_ROW = ("#F1F5F9", "#172238")    # Hover row highlight
BG_ACTIVE_ROW = ("#ECFDF5", "#0F2624")   # Active selected card background
BG_MODAL = ("#F8FAFC", "#0B0F17")        # Modal dialog canvas

# Structural Borders
BORDER_SUBTLE = ("#E2E8F0", "#1C2638")   # Clean 1px separator lines
BORDER_CARD = ("#E2E8F0", "#202D42")     # Card perimeter
BORDER_FOCUS = ("#10B981", "#10B981")    # Input focus
BORDER_ACTIVE = ("#10B981", "#10B981")   # Active card selection border
BORDER_ERROR = ("#EF4444", "#EF4444")

# Typography & Text Colors
TEXT_MAIN = ("#0F172A", "#F8FAFC")       # Primary headings & main text
TEXT_MUTED = ("#475569", "#94A3B8")      # Secondary body & labels
TEXT_DIM = ("#94A3B8", "#64748B")        # Helper captions & metadata
TEXT_SECTION = ("#64748B", "#7E91A8")    # Uppercase micro-section headers
TEXT_INVERSE = "#FFFFFF"

# Accent Colors
ACCENT_EMERALD = "#10B981"
ACCENT_EMERALD_HOVER = "#059669"
ACCENT_EMERALD_ACTIVE = "#047857"
ACCENT_EMERALD_SUBTLE = ("#ECFDF5", "#064E3B")

ACCENT_TEAL = "#0EA5E9"
ACCENT_TEAL_HOVER = "#0284C7"

ACCENT_AMBER = "#D97706"
ACCENT_AMBER_HOVER = "#B45309"

ACCENT_ROSE = "#EF4444"
ACCENT_ROSE_HOVER = "#DC2626"
ACCENT_ROSE_TEXT = ("#DC2626", "#F87171")

# Button Styles
BTN_NEUTRAL_BG = ("#F1F5F9", "#1A2436")
BTN_NEUTRAL_HOVER = ("#E2E8F0", "#25344D")
BTN_NEUTRAL_TEXT = ("#1E293B", "#F1F5F9")

BTN_DANGER_BG = ("#FEE2E2", "#2E151A")
BTN_DANGER_HOVER = ("#FECACA", "#481B23")
BTN_DANGER_TEXT = ("#DC2626", "#F87171")

# Badges by File Extension
BADGE_STYLES = {
    "PNG": {"bg": ("#ECFDF5", "#064E3B"), "fg": ("#059669", "#34D399")},
    "JPG": {"bg": ("#FEF3C7", "#451A03"), "fg": ("#D97706", "#FBBF24")},
    "JPEG": {"bg": ("#FEF3C7", "#451A03"), "fg": ("#D97706", "#FBBF24")},
    "WEBP": {"bg": ("#F0FDFA", "#134E4A"), "fg": ("#0D9488", "#2DD4BF")},
    "PDF": {"bg": ("#ECFDF5", "#064E3B"), "fg": ("#059669", "#34D399")},
    "TIFF": {"bg": ("#F1F5F9", "#1E293B"), "fg": ("#475569", "#94A3B8")},
    "BMP": {"bg": ("#F1F5F9", "#1E293B"), "fg": ("#475569", "#94A3B8")},
    "DEFAULT": {"bg": ("#F1F5F9", "#1E293B"), "fg": ("#475569", "#94A3B8")}
}

# ============================================================================
# 2. GEOMETRIC RADII & DIMENSIONS
# ============================================================================
RADIUS_WINDOW = 14
RADIUS_MODAL = 12
RADIUS_CONTAINER = 10
RADIUS_CARD = 8
RADIUS_CONTROL = 6
RADIUS_BTN = 6
RADIUS_INPUT = 6
RADIUS_PILL = 6
RADIUS_BADGE = 4

HEIGHT_HERO_BTN = 42
HEIGHT_ACTION_BTN = 34
HEIGHT_MICRO_BTN = 28
HEIGHT_INPUT = 32

# ============================================================================
# 3. TYPOGRAPHY HIERARCHY (Segoe UI)
# ============================================================================
FONT_FAMILY = "Segoe UI"


def font_brand():
    return ctk.CTkFont(family=FONT_FAMILY, size=17, weight="bold")


def font_h1():
    return ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold")


def font_h2():
    return ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")


def font_title():
    return ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")


def font_body():
    return ctk.CTkFont(family=FONT_FAMILY, size=12, weight="normal")


def font_body_bold():
    return ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")


def font_section_header():
    return ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")


def font_hero_btn():
    return ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")


def font_caption():
    return ctk.CTkFont(family=FONT_FAMILY, size=11, weight="normal")


def font_caption_bold():
    return ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")


def font_badge():
    return ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")


def font_mono(size=11):
    return ctk.CTkFont(family="Consolas", size=size, weight="normal")

