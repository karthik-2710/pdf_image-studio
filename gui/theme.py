"""
Centralized Theme & Design System for Image & PDF Converter Studio.
Provides unified color tokens, font hierarchies, radii, and component styling presets.
"""

import customtkinter as ctk

# ============================================================================
# 1. COLOR PALETTE (Dark Obsidian & Crisp Slate)
# ============================================================================

# Surface & Canvas Backgrounds (Light Mode, Dark Mode)
BG_APP = ("#F8FAFC", "#090D16")
BG_SIDEBAR = ("#FFFFFF", "#0D131F")
BG_CARD = ("#FFFFFF", "#121A2A")
BG_CARD_ALT = ("#F8FAFC", "#172235")
BG_CONTAINER = ("#F1F5F9", "#0B101B")
BG_INPUT = ("#FFFFFF", "#0B101B")
BG_HOVER_ROW = ("#F1F5F9", "#162032")
BG_MODAL = ("#F8FAFC", "#090D16")

# Structural Borders
BORDER_SUBTLE = ("#E2E8F0", "#1E293B")
BORDER_CARD = ("#E2E8F0", "#222F43")
BORDER_FOCUS = ("#10B981", "#10B981")
BORDER_ACTIVE = ("#10B981", "#10B981")
BORDER_ERROR = ("#EF4444", "#EF4444")

# Typography & Text Colors
TEXT_MAIN = ("#0F172A", "#F8FAFC")
TEXT_MUTED = ("#475569", "#94A3B8")
TEXT_DIM = ("#94A3B8", "#64748B")
TEXT_INVERSE = "#FFFFFF"

# Accent Colors
ACCENT_EMERALD = "#10B981"
ACCENT_EMERALD_HOVER = "#059669"
ACCENT_EMERALD_ACTIVE = "#047857"

ACCENT_TEAL = "#0D9488"
ACCENT_TEAL_HOVER = "#0F766E"

ACCENT_AMBER = "#D97706"
ACCENT_AMBER_HOVER = "#B45309"

ACCENT_ROSE = "#EF4444"
ACCENT_ROSE_HOVER = "#DC2626"
ACCENT_ROSE_TEXT = ("#DC2626", "#F87171")

# Button Styles
BTN_NEUTRAL_BG = ("#F1F5F9", "#1E293B")
BTN_NEUTRAL_HOVER = ("#E2E8F0", "#2D3D54")
BTN_NEUTRAL_TEXT = ("#0F172A", "#F8FAFC")

BTN_DANGER_BG = ("#FEE2E2", "#351519")
BTN_DANGER_HOVER = ("#FECACA", "#541B23")
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
# 2. GEOMETRIC RADII
# ============================================================================
RADIUS_WINDOW = 14
RADIUS_MODAL = 12
RADIUS_CONTAINER = 12
RADIUS_CARD = 10
RADIUS_CONTROL = 8
RADIUS_BTN = 8
RADIUS_INPUT = 6
RADIUS_PILL = 6
RADIUS_BADGE = 4

# ============================================================================
# 3. TYPOGRAPHY HIERARCHY (Segoe UI)
# ============================================================================
FONT_FAMILY = "Segoe UI"


def font_brand():
    return ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold")


def font_h1():
    return ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold")


def font_h2():
    return ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold")


def font_title():
    return ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")


def font_body():
    return ctk.CTkFont(family=FONT_FAMILY, size=12, weight="normal")


def font_body_bold():
    return ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")


def font_caption():
    return ctk.CTkFont(family=FONT_FAMILY, size=11, weight="normal")


def font_caption_bold():
    return ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")


def font_badge():
    return ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")


def font_mono(size=11):
    return ctk.CTkFont(family="Consolas", size=size, weight="normal")
