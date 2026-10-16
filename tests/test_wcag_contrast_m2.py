"""
Test: test_wcag_contrast_m2.py
Purpose: Calculate WCAG 2.1 AA relative luminance and contrast ratio for all text color / background color pairs
across Light, Dark, and High Contrast themes.
Verifies against WCAG 2.1 AA thresholds:
- Normal text (<18pt / <14pt bold): >= 4.5:1 (Success Criterion 1.4.3)
- Large text (>=18pt or >=14pt bold) / UI components: >= 3.0:1 (Success Criterion 1.4.3 / 1.4.11)
"""

import sys
import math

def parse_color(c_str):
    """Parses hex (#rrggbb, #rgb) or rgb/rgba string into (r, g, b, a) in [0, 1]."""
    c_str = c_str.strip().lower()
    if c_str.startswith("#"):
        hex_val = c_str.lstrip("#")
        if len(hex_val) == 3:
            r = int(hex_val[0]*2, 16) / 255.0
            g = int(hex_val[1]*2, 16) / 255.0
            b = int(hex_val[2]*2, 16) / 255.0
            return (r, g, b, 1.0)
        elif len(hex_val) == 6:
            r = int(hex_val[0:2], 16) / 255.0
            g = int(hex_val[2:4], 16) / 255.0
            b = int(hex_val[4:6], 16) / 255.0
            return (r, g, b, 1.0)
    elif c_str.startswith("rgba"):
        parts = c_str[4:].strip("()").split(",")
        r = float(parts[0]) / 255.0
        g = float(parts[1]) / 255.0
        b = float(parts[2]) / 255.0
        a = float(parts[3])
        return (r, g, b, a)
    elif c_str.startswith("rgb"):
        parts = c_str[3:].strip("()").split(",")
        r = float(parts[0]) / 255.0
        g = float(parts[1]) / 255.0
        b = float(parts[2]) / 255.0
        return (r, g, b, 1.0)
    raise ValueError(f"Unknown color format: {c_str}")

def composite(fg_rgba, bg_rgba):
    """Composites foreground over background using standard alpha blending."""
    r_fg, g_fg, b_fg, a_fg = fg_rgba
    r_bg, g_bg, b_bg, a_bg = bg_rgba
    a_out = a_fg + a_bg * (1.0 - a_fg)
    if a_out == 0:
        return (0.0, 0.0, 0.0, 0.0)
    r_out = (r_fg * a_fg + r_bg * a_bg * (1.0 - a_fg)) / a_out
    g_out = (g_fg * a_fg + g_bg * a_bg * (1.0 - a_fg)) / a_out
    b_out = (b_fg * a_fg + b_bg * a_bg * (1.0 - a_fg)) / a_out
    return (r_out, g_out, b_out, a_out)

def srgb_channel_luminance(c):
    if c <= 0.03928:
        return c / 12.92
    else:
        return math.pow((c + 0.055) / 1.055, 2.4)

def relative_luminance(rgba):
    r_lin = srgb_channel_luminance(rgba[0])
    g_lin = srgb_channel_luminance(rgba[1])
    b_lin = srgb_channel_luminance(rgba[2])
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def contrast_ratio(color1, color2, base_bg=None):
    c1 = parse_color(color1)
    c2 = parse_color(color2)
    if c2[3] < 1.0 and base_bg is not None:
        c2 = composite(c2, parse_color(base_bg))
    if c1[3] < 1.0 and base_bg is not None:
        c1 = composite(c1, parse_color(base_bg))
    l1 = relative_luminance(c1)
    l2 = relative_luminance(c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def run_tests():
    print("=" * 80)
    print("WCAG 2.1 AA CONTRAST RATIO AUDIT (Milestone 2 Stress Test)")
    print("=" * 80)

    # Test cases: (category, description, fg_color, bg_color, base_bg_for_alpha, min_ratio, item_type)
    test_cases = [
        # --- 1. LIGHT THEME TOKENS ---
        ("LIGHT", "--ink on --paper", "#14171a", "#faf8f5", None, 4.5, "body"),
        ("LIGHT", "--ink on --paper-soft", "#14171a", "#f4efe6", None, 4.5, "body"),
        ("LIGHT", "--ink on --paper-card", "#14171a", "#ffffff", None, 4.5, "body"),
        ("LIGHT", "--ink-secondary on --paper", "#3d4547", "#faf8f5", None, 4.5, "body"),
        ("LIGHT", "--ink-secondary on --paper-soft", "#3d4547", "#f4efe6", None, 4.5, "body"),
        ("LIGHT", "--ink-secondary on --paper-card", "#3d4547", "#ffffff", None, 4.5, "body"),
        ("LIGHT", "--muted on --paper", "#556265", "#faf8f5", None, 4.5, "body"),
        ("LIGHT", "--muted on --paper-soft", "#556265", "#f4efe6", None, 4.5, "body"),
        ("LIGHT", "--muted on --paper-card", "#556265", "#ffffff", None, 4.5, "body"),
        ("LIGHT", "--gold-text on --paper", "#875f00", "#faf8f5", None, 4.5, "body"),
        ("LIGHT", "--gold-text on --gold-bg", "#875f00", "#fbf4e4", None, 4.5, "body"),
        ("LIGHT", "--teal on --teal-bg", "#146e66", "#e6f3f0", None, 4.5, "body"),
        ("LIGHT", "--crimson on --crimson-bg", "#9b2226", "#fbebee", None, 4.5, "body"),
        ("LIGHT", "--forest on --forest-bg", "#2d6a4f", "#e9f5ee", None, 4.5, "body"),
        ("LIGHT", ":focus-visible on --paper", "#002b49", "#faf8f5", None, 3.0, "ui"),

        # --- 2. LIGHT THEME COMPONENTS ---
        ("LIGHT", ".btn-pill (white on --navy)", "#ffffff", "#002b49", None, 4.5, "body"),
        ("LIGHT", ".btn-hero-primary (white on #875f00)", "#ffffff", "#875f00", None, 4.5, "body"),
        ("LIGHT", ".btn-hero-secondary (--navy on --paper-card)", "#002b49", "#ffffff", None, 4.5, "body"),
        ("LIGHT", ".btn-hero-share (--ink-secondary on --paper-soft)", "#3d4547", "#f4efe6", None, 4.5, "body"),
        ("LIGHT", ".data-table th (--navy on #f7f4ee)", "#002b49", "#f7f4ee", None, 4.5, "body"),

        # --- 3. DARK THEME TOKENS ---
        ("DARK", "--ink on --paper", "#f8fafc", "#04142b", None, 4.5, "body"),
        ("DARK", "--ink on --paper-soft", "#f8fafc", "#071f43", None, 4.5, "body"),
        ("DARK", "--ink on --paper-card", "#f8fafc", "#0a2652", None, 4.5, "body"),
        ("DARK", "--ink-secondary on --paper", "#cbd5e1", "#04142b", None, 4.5, "body"),
        ("DARK", "--ink-secondary on --paper-soft", "#cbd5e1", "#071f43", None, 4.5, "body"),
        ("DARK", "--ink-secondary on --paper-card", "#cbd5e1", "#0a2652", None, 4.5, "body"),
        ("DARK", "--muted on --paper", "#94a3b8", "#04142b", None, 4.5, "body"),
        ("DARK", "--muted on --paper-soft", "#94a3b8", "#071f43", None, 4.5, "body"),
        ("DARK", "--muted on --paper-card", "#94a3b8", "#0a2652", None, 4.5, "body"),
        ("DARK", "--gold-text on --gold-bg", "#f59e0b", "rgba(245, 158, 11, 0.15)", "#04142b", 4.5, "body"),
        ("DARK", "--teal on --teal-bg", "#10b981", "rgba(16, 185, 129, 0.15)", "#04142b", 4.5, "body"),
        ("DARK", "--crimson on --crimson-bg", "#f87171", "rgba(239, 68, 68, 0.15)", "#04142b", 4.5, "body"),
        ("DARK", "--forest on --forest-bg", "#34d399", "rgba(52, 211, 153, 0.15)", "#04142b", 4.5, "body"),
        ("DARK", ":focus-visible on --paper", "#38bdf8", "#04142b", None, 3.0, "ui"),

        # --- 4. DARK THEME CONTROLS & COMPONENTS ---
        ("DARK", "Inputs (.form-input color on bg)", "#f8fafc", "#071f43", None, 4.5, "body"),
        ("DARK", "Table header (.data-table th)", "#38bdf8", "#071f43", None, 4.5, "body"),
        ("DARK", "Table hover row (.data-table tr:hover td)", "#f8fafc", "#0d3166", None, 4.5, "body"),
        ("DARK", ".btn-hero-secondary (#38bdf8 on #0a2652)", "#38bdf8", "#0a2652", None, 4.5, "body"),
        ("DARK", ".btn-hero-share (#cbd5e1 on #071f43)", "#cbd5e1", "#071f43", None, 4.5, "body"),
        ("DARK", ".hero-status-pill (#cbd5e1 on #0a2652)", "#cbd5e1", "#0a2652", None, 4.5, "body"),

        # --- 5. DARK THEME BUTTONS WITH EXPLICIT OVERRIDES (#04142b on #38bdf8 / #f59e0b) ---
        ("DARK", ".btn-hero-primary (#04142b on --gold #f59e0b)", "#04142b", "#f59e0b", None, 4.5, "body"),
        ("DARK", ".btn-pill (#04142b on dark --navy #38bdf8)", "#04142b", "#38bdf8", None, 4.5, "body"),
        ("DARK", ".story-tab-btn.active (#04142b on dark --navy #38bdf8)", "#04142b", "#38bdf8", None, 4.5, "body"),
        ("DARK", ".layer-btn.active (#04142b on dark --navy #38bdf8)", "#04142b", "#38bdf8", None, 4.5, "body"),
        ("DARK", ".btn-modal-primary (#04142b on dark --navy #38bdf8)", "#04142b", "#38bdf8", None, 4.5, "body"),
        ("DARK", ".btn-footer-cta (#04142b on dark --navy #38bdf8)", "#04142b", "#38bdf8", None, 4.5, "body"),
        ("DARK", ".btn-export-csv (#04142b on dark --navy #38bdf8)", "#04142b", "#38bdf8", None, 4.5, "body"),
        ("DARK", ".floating-guide-btn (#04142b on dark --navy #38bdf8)", "#04142b", "#38bdf8", None, 4.5, "body"),
        ("DARK", ".skip-link (#04142b on dark --navy #38bdf8)", "#04142b", "#38bdf8", None, 4.5, "body"),

        # --- 6. CONTRAST THEME COMPONENTS (#000000 on #ffff00) ---
        ("CONTRAST", "Body text (white on black)", "#ffffff", "#000000", None, 4.5, "body"),
        ("CONTRAST", "Yellow text (yellow on black)", "#ffff00", "#000000", None, 4.5, "body"),
        ("CONTRAST", ".btn-hero-primary (black on yellow)", "#000000", "#ffff00", None, 4.5, "body"),
        ("CONTRAST", ".btn-hero-secondary (yellow on black)", "#ffff00", "#000000", None, 4.5, "body"),
        ("CONTRAST", ".btn-pill (black on contrast --navy #ffff00)", "#000000", "#ffff00", None, 4.5, "body"),
        ("CONTRAST", ".story-tab-btn.active (black on contrast --navy #ffff00)", "#000000", "#ffff00", None, 4.5, "body"),
        ("CONTRAST", ".layer-btn.active (black on contrast --navy #ffff00)", "#000000", "#ffff00", None, 4.5, "body"),
        ("CONTRAST", ".skip-link (black on contrast --navy #ffff00)", "#000000", "#ffff00", None, 4.5, "body"),
        ("CONTRAST", ".btn-modal-primary (black on contrast --navy #ffff00)", "#000000", "#ffff00", None, 4.5, "body"),
        ("CONTRAST", ".btn-footer-cta (black on contrast --navy #ffff00)", "#000000", "#ffff00", None, 4.5, "body"),

        # --- 7. PROVIDER CATEGORY BADGES ---
        ("BADGES", ".prov-badge.erp (#991b1b on #fee2e2)", "#991b1b", "#fee2e2", None, 4.5, "body"),
        ("BADGES", ".prov-badge.telecom (#0369a1 on #e0f2fe)", "#0369a1", "#e0f2fe", None, 4.5, "body"),
        ("BADGES", ".prov-badge.hardware (#92400e on #fef3c7)", "#92400e", "#fef3c7", None, 4.5, "body"),
        ("BADGES", ".prov-badge.cloud (#166534 on #dcfce7)", "#166534", "#dcfce7", None, 4.5, "body"),
        ("BADGES", ".prov-badge.seguridad (#6b21a8 on #f3e8ff)", "#6b21a8", "#f3e8ff", None, 4.5, "body"),
        ("BADGES", ".prov-badge.consultoria (#334155 on #f1f5f9)", "#334155", "#f1f5f9", None, 4.5, "body"),
        ("BADGES", ".prov-badge.general (#475569 on #f1f5f9)", "#475569", "#f1f5f9", None, 4.5, "body"),
    ]

    failures = []
    passes = []

    print(f"{'Theme':<10} | {'Component / Pair':<50} | {'Ratio':<8} | {'Min Req':<8} | {'Status'}")
    print("-" * 90)

    for theme, desc, fg, bg, base_bg, min_r, item_type in test_cases:
        ratio = contrast_ratio(fg, bg, base_bg)
        status = "PASS" if ratio >= min_r else "FAIL"
        print(f"{theme:<10} | {desc:<50} | {ratio:>6.2f}:1 | {min_r:>6.2f}:1 | {status}")
        if status == "FAIL":
            failures.append((theme, desc, ratio, min_r, fg, bg))
        else:
            passes.append((theme, desc, ratio, min_r))

    print("-" * 90)
    print(f"Total pairs tested: {len(test_cases)}")
    print(f"Passed: {len(passes)}")
    print(f"Failed: {len(failures)}")

    if failures:
        print("\n=== VERIFIED WCAG 2.1 AA CONTRAST FAILURES ===")
        for theme, desc, ratio, min_r, fg, bg in failures:
            print(f"- [{theme}] {desc}: {ratio:.2f}:1 (Required >= {min_r:.1f}:1). Colors: fg={fg}, bg={bg}")
        return False
    else:
        print("\nAll contrast tests passed!")
        return True

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
