"""
validator_visualizer.py
=======================
Generates a multi-panel figure that walks through every step of the
RunePathValidator pipeline for a single drawn rune, then saves it as a PNG.

Designed to be called from process_canvas() in refactor.py immediately
after recognize_spell() returns, so it has access to:
  - the raw pygame canvas surface
  - the raw stroke points list
  - the spell name the CNN predicted
  - the validator instance (which already holds all template paths)

Usage (from refactor.py):
    from validator_visualizer import save_validation_viz
    save_validation_viz(canvas_surface, stroke_points, spell_name, validator)

Output:
    eval/validation/<spell_name>_<timestamp>.png
"""

import os
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch
from PIL import Image


OUTPUT_DIR = os.path.join("eval", "validation")


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def save_validation_viz(canvas_surface, stroke_points, spell_name, validator, passed, final_score):
    """
    Build and save the full validation pipeline figure.

    Args:
        canvas_surface  : pygame.Surface — the drawn canvas at game resolution
        stroke_points   : list of (x, y) — raw mouse points collected during drawing
        spell_name      : str — spell the CNN predicted (e.g. "fireball")
        validator       : RunePathValidator instance
        passed          : bool — whether validation passed
        final_score     : float — the combined path_score result
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    template_pts = validator._templates.get(spell_name)
    if template_pts is None:
        print(f"[Viz] No template for '{spell_name}', skipping visualization.")
        return

    # ── Collect all intermediate data ────────────────────────────────────────
    data = _collect_pipeline_data(stroke_points, template_pts, spell_name, validator)

    # ── Build the figure ─────────────────────────────────────────────────────
    fig = _build_figure(canvas_surface, stroke_points, template_pts,
                        spell_name, validator, data, passed, final_score)

    # ── Save ─────────────────────────────────────────────────────────────────
    timestamp = int(time.time())
    fname = os.path.join(OUTPUT_DIR, f"{spell_name}_{timestamp}.png")
    fig.savefig(fname, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[Viz] Saved validation figure → {fname}")


# ─────────────────────────────────────────────────────────────────────────────
# Data collection — run every validator step and capture intermediates
# ─────────────────────────────────────────────────────────────────────────────

def _collect_pipeline_data(stroke_pts, template_pts, spell_name, v):
    """
    Re-run all validator computations and return a dict of every
    intermediate result needed for plotting.
    """
    d = {}

    # Raw point counts
    d["n_raw_input"]    = len(stroke_pts)
    d["n_raw_template"] = len(template_pts)

    # Resampled paths (64 evenly-spaced points)
    d["input_resampled"]    = v.resample(list(stroke_pts))
    d["template_resampled"] = v.resample(list(template_pts))

    # Normalized paths (zero-centred, unit scale)
    d["input_norm"]    = v.normalize(d["input_resampled"])
    d["template_norm"] = v.normalize(d["template_resampled"])

    # Per-point distances between normalized paths (fwd and rev)
    fwd_dists = np.linalg.norm(d["input_norm"] - d["template_norm"],          axis=1)
    rev_dists = np.linalg.norm(d["input_norm"] - d["template_norm"][::-1],    axis=1)
    d["point_dists_fwd"] = fwd_dists
    d["point_dists_rev"] = rev_dists
    d["use_reverse"]     = rev_dists.mean() < fwd_dists.mean()
    d["point_dists"]     = rev_dists if d["use_reverse"] else fwd_dists

    # Turning angle profiles
    d["input_angles"]    = v.turning_angles(d["input_resampled"])
    d["template_angles"] = v.turning_angles(d["template_resampled"])
    d["angle_diffs"]     = np.abs(d["input_angles"] - d["template_angles"])

    # Sub-scores
    d["s_shape"]    = v.shape_score(stroke_pts, template_pts)
    d["s_angle"]    = v.angle_score(stroke_pts, template_pts)
    d["s_length"]   = v.path_length_ratio(stroke_pts, template_pts)

    # Threshold for this spell
    d["threshold"] = v.THRESHOLDS.get(spell_name, v.DEFAULT_THRESHOLD)

    return d


# ─────────────────────────────────────────────────────────────────────────────
# Figure layout
# ─────────────────────────────────────────────────────────────────────────────

def _build_figure(canvas_surface, stroke_pts, template_pts,
                  spell_name, validator, d, passed, final_score):
    """
    Assemble a 4-row × 4-column figure covering:

    Row 0:  Raw canvas | Raw input path | Template path | Skeleton overlay
    Row 1:  Resampled input | Resampled template | Normalized overlay | Point distances
    Row 2:  Input angle profile | Template angle profile | Angle diff | Score breakdown bar
    Row 3:  Full-width verdict banner
    """
    BG   = "#1a1a2e"
    FG   = "#e0e0e0"
    ACC1 = "#f5a623"   # amber  — input
    ACC2 = "#7ed6df"   # cyan   — template
    RED  = "#e84393"
    GRN  = "#2ecc71"

    plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor":   BG,
        "axes.edgecolor":   FG,
        "axes.labelcolor":  FG,
        "xtick.color":      FG,
        "ytick.color":      FG,
        "text.color":       FG,
        "grid.color":       "#333355",
        "grid.linestyle":   "--",
        "grid.alpha":       0.5,
    })

    fig = plt.figure(figsize=(20, 16), facecolor=BG)
    fig.suptitle(
        f"Validator Pipeline  —  '{spell_name.upper()}'",
        fontsize=18, fontweight="bold", color=ACC1, y=0.98
    )

    gs = gridspec.GridSpec(
        4, 4,
        figure=fig,
        hspace=0.55,
        wspace=0.35,
        height_ratios=[3, 3, 3, 1.2],
    )

    # ── Row 0 ─────────────────────────────────────────────────────────────────

    # 0-0  Raw canvas image
    ax00 = fig.add_subplot(gs[0, 0])
    _plot_canvas_image(ax00, canvas_surface, ACC1, FG)
    ax00.set_title("1. Drawn Canvas", color=FG)

    # 0-1  Raw input stroke path
    ax01 = fig.add_subplot(gs[0, 1])
    _plot_path(ax01, stroke_pts, ACC1, f"Raw Input  ({d['n_raw_input']} pts)", FG,
               gradient=True)

    # 0-2  Raw template path
    ax02 = fig.add_subplot(gs[0, 2])
    _plot_path(ax02, template_pts, ACC2, f"Template Path  ({d['n_raw_template']} pts)", FG,
               gradient=True)

    # 0-3  Overlay of raw paths (same coordinate space, normalised for display)
    ax03 = fig.add_subplot(gs[0, 3])
    _plot_overlay_raw(ax03, stroke_pts, template_pts, ACC1, ACC2, FG)
    ax03.set_title("4. Raw Overlay", color=FG)

    # ── Row 1 ─────────────────────────────────────────────────────────────────

    # 1-0  Resampled input (64 evenly-spaced dots)
    ax10 = fig.add_subplot(gs[1, 0])
    _plot_resampled(ax10, d["input_resampled"], ACC1, "5. Resampled Input  (64 pts)", FG)

    # 1-1  Resampled template
    ax11 = fig.add_subplot(gs[1, 1])
    _plot_resampled(ax11, d["template_resampled"], ACC2, "6. Resampled Template  (64 pts)", FG)

    # 1-2  Normalized overlay
    ax12 = fig.add_subplot(gs[1, 2])
    _plot_normalized_overlay(ax12, d["input_norm"], d["template_norm"],
                             d["use_reverse"], ACC1, ACC2, FG)

    # 1-3  Per-point distance heatmap
    ax13 = fig.add_subplot(gs[1, 3])
    _plot_point_distances(ax13, d["point_dists"], d["s_shape"], FG, ACC1)

    # ── Row 2 ─────────────────────────────────────────────────────────────────

    # 2-0  Input turning angles
    ax20 = fig.add_subplot(gs[2, 0])
    _plot_angles(ax20, d["input_angles"], ACC1, "9. Input Turning Angles", FG)

    # 2-1  Template turning angles
    ax21 = fig.add_subplot(gs[2, 1])
    _plot_angles(ax21, d["template_angles"], ACC2, "10. Template Turning Angles", FG)

    # 2-2  Angle difference profile
    ax22 = fig.add_subplot(gs[2, 2])
    _plot_angle_diff(ax22, d["angle_diffs"], d["s_angle"], FG, RED)

    # 2-3  Score breakdown
    ax23 = fig.add_subplot(gs[2, 3])
    _plot_score_breakdown(ax23, d, final_score, FG, GRN, RED, ACC1)

    # ── Row 3 — Verdict banner ────────────────────────────────────────────────
    ax_verdict = fig.add_subplot(gs[3, :])
    _plot_verdict(ax_verdict, spell_name, passed, final_score, d["threshold"],
                  GRN, RED, FG, BG)

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Individual panel renderers
# ─────────────────────────────────────────────────────────────────────────────

def _plot_canvas_image(ax, canvas_surface, accent, fg):
    """Render the pygame canvas surface as an image."""
    try:
        import pygame
        raw  = pygame.image.tostring(canvas_surface, "RGB")
        img  = Image.frombytes("RGB", canvas_surface.get_size(), raw)
        ax.imshow(np.array(img), origin="upper")
    except Exception:
        ax.text(0.5, 0.5, "Canvas\n(pygame not available)",
                ha="center", va="center", color=fg, transform=ax.transAxes)
    ax.axis("off")


def _plot_path(ax, pts, color, title, fg, gradient=False):
    """Plot a raw point path with optional gradient colouring."""
    if not pts:
        return
    xs = [p[0] for p in pts]
    ys = [-p[1] for p in pts]   # flip Y so top-left origin looks natural

    if gradient:
        n = len(xs)
        for i in range(n - 1):
            t    = i / max(n - 2, 1)
            rgba = plt.cm.plasma(0.2 + 0.7 * t)
            ax.plot(xs[i:i+2], ys[i:i+2], color=rgba, linewidth=1.5, solid_capstyle="round")
    else:
        ax.plot(xs, ys, color=color, linewidth=1.5)

    ax.plot(xs[0],  ys[0],  "o", color="#2ecc71", markersize=7, zorder=5, label="start")
    ax.plot(xs[-1], ys[-1], "s", color="#e74c3c", markersize=7, zorder=5, label="end")
    ax.set_title(title, color=fg, fontsize=9)
    ax.set_aspect("equal")
    ax.grid(True)
    ax.legend(fontsize=7, loc="lower right",
              facecolor="#2a2a4a", edgecolor="none", labelcolor=fg)


def _plot_overlay_raw(ax, input_pts, template_pts, c1, c2, fg):
    """Overlay raw input and template in the same canvas coordinate space."""
    def _normalise_for_display(pts):
        arr = np.array(pts, dtype=float)
        arr -= arr.min(axis=0)
        span = arr.max()
        if span > 0:
            arr /= span
        return arr

    inp = _normalise_for_display(input_pts)
    tmp = _normalise_for_display(template_pts)

    ax.plot(inp[:, 0], -inp[:, 1], color=c1, linewidth=1.5, label="Input",    alpha=0.85)
    ax.plot(tmp[:, 0], -tmp[:, 1], color=c2, linewidth=1.5, label="Template", alpha=0.85,
            linestyle="--")
    ax.set_aspect("equal")
    ax.grid(True)
    ax.legend(fontsize=7, facecolor="#2a2a4a", edgecolor="none", labelcolor=fg)


def _plot_resampled(ax, pts, color, title, fg):
    """Show the 64-point resampled path with numbered dots."""
    if not pts:
        return
    xs = [p[0] for p in pts]
    ys = [-p[1] for p in pts]
    ax.plot(xs, ys, color=color, linewidth=1.2, alpha=0.6)
    # Scatter with index-based colour
    sc = ax.scatter(xs, ys, c=range(len(xs)), cmap="plasma",
                    s=30, zorder=4, linewidths=0)
    plt.colorbar(sc, ax=ax, label="point index", shrink=0.7)
    ax.set_title(title, color=fg, fontsize=9)
    ax.set_aspect("equal")
    ax.grid(True)


def _plot_normalized_overlay(ax, inp_norm, tmp_norm, use_reverse, c1, c2, fg):
    """
    Overlay both paths after normalization (zero-centred, unit scale).
    Draw connecting lines between matched point pairs to show alignment error.
    """
    tmpl = tmp_norm[::-1] if use_reverse else tmp_norm

    # Connecting lines between matched points
    for i in range(len(inp_norm)):
        ax.plot([inp_norm[i, 0], tmpl[i, 0]],
                [inp_norm[i, 1], tmpl[i, 1]],
                color="#ffffff", linewidth=0.4, alpha=0.25)

    ax.plot(inp_norm[:, 0], inp_norm[:, 1], color=c1, linewidth=1.8,
            label="Input (norm)", zorder=3)
    ax.plot(tmpl[:, 0],     tmpl[:, 1],     color=c2, linewidth=1.8,
            label="Template (norm)", zorder=3, linestyle="--")

    ax.set_title("7. Normalized Overlay\n(white lines = alignment error)", color=fg, fontsize=9)
    ax.set_aspect("equal")
    ax.grid(True)
    ax.legend(fontsize=7, facecolor="#2a2a4a", edgecolor="none", labelcolor=fg)


def _plot_point_distances(ax, dists, shape_score, fg, accent):
    """Bar chart of per-point geometric distance after normalization."""
    x = np.arange(len(dists))
    bars = ax.bar(x, dists, color=accent, alpha=0.75, width=1.0)
    ax.axhline(dists.mean(), color="#e74c3c", linewidth=1.5,
               linestyle="--", label=f"mean = {dists.mean():.3f}")
    ax.set_xlabel("Point index", fontsize=8)
    ax.set_ylabel("Distance", fontsize=8)
    ax.set_title(f"8. Per-Point Distance\nShape score = {shape_score:.3f}", color=fg, fontsize=9)
    ax.legend(fontsize=7, facecolor="#2a2a4a", edgecolor="none", labelcolor=fg)
    ax.grid(True, axis="y")


def _plot_angles(ax, angles, color, title, fg):
    """Line plot of the turning angle profile."""
    ax.plot(np.degrees(angles), color=color, linewidth=1.5)
    ax.axhline(0, color=fg, linewidth=0.7, alpha=0.4)
    ax.fill_between(range(len(angles)), np.degrees(angles), 0,
                    alpha=0.2, color=color)
    ax.set_xlabel("Point index", fontsize=8)
    ax.set_ylabel("Angle (°)", fontsize=8)
    ax.set_title(title, color=fg, fontsize=9)
    ax.grid(True)


def _plot_angle_diff(ax, diffs_rad, angle_score, fg, red):
    """Show the absolute difference between input and template angle profiles."""
    diffs_deg = np.degrees(diffs_rad)
    ax.fill_between(range(len(diffs_deg)), diffs_deg, color=red, alpha=0.5)
    ax.plot(diffs_deg, color=red, linewidth=1.2)
    ax.axhline(diffs_deg.mean(), color="#f5a623", linewidth=1.5,
               linestyle="--", label=f"mean = {diffs_deg.mean():.1f}°")
    ax.set_xlabel("Point index", fontsize=8)
    ax.set_ylabel("|Δ angle| (°)", fontsize=8)
    ax.set_title(f"11. Angle Difference Profile\nAngle score = {angle_score:.3f}",
                 color=fg, fontsize=9)
    ax.legend(fontsize=7, facecolor="#2a2a4a", edgecolor="none", labelcolor=fg)
    ax.grid(True)


def _plot_score_breakdown(ax, d, final_score, fg, grn, red, accent):
    """
    Horizontal bar chart showing all four sub-scores and the final combined score.
    Bars are colour-coded green/red relative to 0.7 as a rough 'good' threshold.
    """
    labels = ["Shape", "Angle", "Length\nRatio", "FINAL\nSCORE"]
    values = [d["s_shape"], d["s_angle"], d["s_length"], final_score]
    colors = [grn if v >= 0.7 else red for v in values]
    # Final score bar uses accent colour
    colors[-1] = accent

    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, alpha=0.85, height=0.6)

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(min(val + 0.02, 0.98), bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left", fontsize=9,
                color=fg, fontweight="bold")

    ax.set_xlim(0, 1.15)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Score", fontsize=8)
    ax.set_title("12. Score Breakdown", color=fg, fontsize=9)
    ax.axvline(d["threshold"], color="#f5a623", linewidth=1.5,
               linestyle="--", label=f"threshold = {d['threshold']:.2f}")
    ax.legend(fontsize=7, facecolor="#2a2a4a", edgecolor="none", labelcolor=fg)
    ax.grid(True, axis="x")

    # Exponent labels (weights) as annotation
    weights = ["^0.35", "^0.35", "^0.15", "^0.15", "combined"]
    for i, (val, wt) in enumerate(zip(values[:-1], weights[:-1])):
        ax.text(0.01, i, wt, va="center", ha="left", fontsize=7,
                color="#aaaaaa", style="italic")


def _plot_verdict(ax, spell_name, passed, score, threshold, grn, red, fg, bg):
    """Full-width verdict banner at the bottom of the figure."""
    ax.set_facecolor(bg)
    ax.axis("off")

    verdict_color = grn  if passed else red
    verdict_text  = "✓  SPELL RECOGNIZED" if passed else "✗  SPELL REJECTED"

    ax.text(0.5, 0.72, verdict_text,
            transform=ax.transAxes, ha="center", va="center",
            fontsize=22, fontweight="bold", color=verdict_color)

    detail = (
        f"Predicted: {spell_name.upper()}   |   "
        f"Score: {score:.4f}   |   "
        f"Threshold: {threshold:.4f}   |   "
        f"Margin: {score - threshold:+.4f}"
    )
    ax.text(0.5, 0.28, detail,
            transform=ax.transAxes, ha="center", va="center",
            fontsize=12, color=fg)

    # Thin decorative rule above the banner
    ax.axhline(1.0, color=verdict_color, linewidth=2, alpha=0.6,
               xmin=0.05, xmax=0.95)