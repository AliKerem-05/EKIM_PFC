from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from toroid_core_library import ToroidCoreLibrary, ToroidProperties
from wire_lib_solid_awg import SolarisWireLibrary, WireProperties


@dataclass
class ViewStyle:
    # Vivid, non-pastel look
    core_face_color: str = "#1F2937"
    core_edge_color: str = "#0B1220"
    core_highlight_color: str = "#3C4B60"
    wire_color_main: str = "#D97706"
    wire_color_alt: str = "#F59E0B"
    wire_edge_color: str = "#7C2D12"
    bg_color: str = "#FFFFFF"
    text_color: str = "#111827"
    grid_color: str = "#9CA3AF"


def _default_output_path(part_number: str, awg: str, turns: int) -> Path:
    base_dir = Path(__file__).resolve().parent
    safe_awg = awg.replace("/", "_")
    return base_dir / "gorsellestirme" / f"toroid_{part_number}_awg{safe_awg}_n{turns}.png"


def _compute_turn_capacity(core: ToroidProperties, wire_d_mm: float) -> int:
    mean_radius = (core.od_mm + core.id_mm) / 4.0
    pitch = wire_d_mm * 1.12
    return max(1, int((2.0 * math.pi * mean_radius) // pitch))


def _add_top_view(
    ax: plt.Axes,
    core: ToroidProperties,
    wire: WireProperties,
    turns: int,
    style: ViewStyle,
) -> tuple[int, int]:
    outer_r = core.od_mm / 2.0
    inner_r = core.id_mm / 2.0

    ax.add_patch(
        Circle(
            (0, 0),
            outer_r,
            facecolor=style.core_face_color,
            edgecolor=style.core_edge_color,
            linewidth=2.4,
            zorder=1,
        )
    )
    ax.add_patch(
        Circle(
            (0, 0),
            (outer_r + inner_r) / 2.0,
            facecolor=style.core_highlight_color,
            edgecolor="none",
            alpha=0.32,
            zorder=1.2,
        )
    )
    ax.add_patch(
        Circle(
            (0, 0),
            inner_r,
            facecolor=style.bg_color,
            edgecolor=style.core_edge_color,
            linewidth=2.0,
            zorder=2,
        )
    )

    wire_r = max(0.14, wire.diameter_mm / 2.0)
    winding_r_outer = outer_r + wire_r * 0.95
    # Inner crossing points are visible at hole edge.
    winding_r_inner = max(wire_r * 1.4, inner_r - wire_r * 0.95)

    max_turns = _compute_turn_capacity(core, wire.diameter_mm)
    drawn_turns = max(1, min(turns, max_turns))

    for i in range(drawn_turns):
        theta = 2.0 * math.pi * i / drawn_turns
        color = style.wire_color_main if i % 2 == 0 else style.wire_color_alt

        x_outer = winding_r_outer * math.cos(theta)
        y_outer = winding_r_outer * math.sin(theta)
        ax.add_patch(
            Circle(
                (x_outer, y_outer),
                wire_r,
                facecolor=color,
                edgecolor=style.wire_edge_color,
                linewidth=0.8,
                zorder=3,
            )
        )

        x_inner = winding_r_inner * math.cos(theta)
        y_inner = winding_r_inner * math.sin(theta)
        ax.add_patch(
            Circle(
                (x_inner, y_inner),
                wire_r,
                facecolor=color,
                edgecolor=style.wire_edge_color,
                linewidth=0.8,
                zorder=3,
            )
        )

    margin = max(8.0, core.od_mm * 0.24)
    ax.set_xlim(-(outer_r + margin), outer_r + margin)
    ax.set_ylim(-(outer_r + margin), outer_r + margin)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Top View (OD/ID + Winding)", color=style.text_color, fontsize=11)
    ax.set_xlabel("mm", color=style.text_color)
    ax.set_ylabel("mm", color=style.text_color)
    ax.grid(True, alpha=0.35, linestyle="--", color=style.grid_color)

    x_dim_outer = outer_r + margin * 0.50
    ax.plot([x_dim_outer, x_dim_outer], [-outer_r, outer_r], color=style.text_color, linewidth=1.2)
    ax.plot([x_dim_outer - 1.5, x_dim_outer + 1.5], [-outer_r, -outer_r], color=style.text_color, linewidth=1.2)
    ax.plot([x_dim_outer - 1.5, x_dim_outer + 1.5], [outer_r, outer_r], color=style.text_color, linewidth=1.2)
    ax.text(
        x_dim_outer + 1.9,
        0,
        f"OD = {core.od_mm:.2f} mm",
        rotation=90,
        ha="left",
        va="center",
        fontsize=9,
        color=style.text_color,
    )

    y_dim_inner = 0.0
    ax.plot([-inner_r, inner_r], [y_dim_inner, y_dim_inner], color=style.text_color, linewidth=1.2)
    ax.plot([-inner_r, -inner_r], [y_dim_inner - 1.2, y_dim_inner + 1.2], color=style.text_color, linewidth=1.2)
    ax.plot([inner_r, inner_r], [y_dim_inner - 1.2, y_dim_inner + 1.2], color=style.text_color, linewidth=1.2)
    ax.text(
        0,
        y_dim_inner + 1.7,
        f"ID = {core.id_mm:.2f} mm",
        ha="center",
        va="bottom",
        fontsize=9,
        color=style.text_color,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7, "pad": 1.4},
    )

    return drawn_turns, max_turns


def _add_side_view(
    ax: plt.Axes,
    core: ToroidProperties,
    wire: WireProperties,
    turns: int,
    style: ViewStyle,
) -> None:
    _ = turns
    outer_w = core.od_mm
    inner_w = core.id_mm
    height = core.height_mm
    ring_thickness_x = (outer_w - inner_w) / 2.0

    ax.add_patch(
        Rectangle(
            (-outer_w / 2.0, -height / 2.0),
            ring_thickness_x,
            height,
            facecolor=style.core_face_color,
            edgecolor=style.core_edge_color,
            linewidth=2.2,
            zorder=1,
        )
    )
    ax.add_patch(
        Rectangle(
            (inner_w / 2.0, -height / 2.0),
            ring_thickness_x,
            height,
            facecolor=style.core_face_color,
            edgecolor=style.core_edge_color,
            linewidth=2.2,
            zorder=1,
        )
    )

    # One section-loop (single winding) instead of stacked circles.
    wire_r = max(0.12, wire.diameter_mm / 2.0)
    x_left = -outer_w / 2.0 - wire_r * 1.6
    x_right = outer_w / 2.0 + wire_r * 1.6
    y_top = height / 2.0 + wire_r * 1.25
    y_bottom = -height / 2.0 - wire_r * 1.25

    ax.plot([x_left, x_left], [y_bottom, y_top], color=style.wire_color_main, linewidth=2.4, zorder=3)
    ax.plot([x_right, x_right], [y_bottom, y_top], color=style.wire_color_main, linewidth=2.4, zorder=3)
    ax.plot([x_left, x_right], [y_top, y_top], color=style.wire_color_main, linewidth=2.4, zorder=3)
    ax.plot([x_left, x_right], [y_bottom, y_bottom], color=style.wire_color_main, linewidth=2.4, zorder=3)

    margin_x = max(10.0, outer_w * 0.24)
    margin_y = max(4.2, height * 0.45)
    ax.set_xlim(-(outer_w / 2.0 + margin_x), outer_w / 2.0 + margin_x)
    ax.set_ylim(-(height / 2.0 + margin_y), height / 2.0 + margin_y)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Side View (Height + Winding)", color=style.text_color, fontsize=11)
    ax.set_xlabel("mm", color=style.text_color)
    ax.set_ylabel("mm", color=style.text_color)
    ax.grid(True, alpha=0.35, linestyle="--", color=style.grid_color)

    x_dim = outer_w / 2.0 + margin_x * 0.36
    ax.plot([x_dim, x_dim], [-height / 2.0, height / 2.0], color=style.text_color, linewidth=1.2)
    ax.plot([x_dim - 1.45, x_dim + 1.45], [-height / 2.0, -height / 2.0], color=style.text_color, linewidth=1.2)
    ax.plot([x_dim - 1.45, x_dim + 1.45], [height / 2.0, height / 2.0], color=style.text_color, linewidth=1.2)
    ax.text(
        x_dim + 2.15,
        0,
        f"H = {core.height_mm:.2f} mm",
        rotation=90,
        ha="left",
        va="center",
        fontsize=9,
        color=style.text_color,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.65, "pad": 1.2},
    )


def plot_toroid(
    core: ToroidProperties,
    turns: int = 24,
    awg: str = "18",
    out_path: str | None = None,
    dpi: int = 150,
    show: bool = False,
) -> Path:
    wire_lib = SolarisWireLibrary()
    wire = wire_lib.get_wire(awg)
    if wire is None:
        raise ValueError(f"AWG not found: {awg}")

    style = ViewStyle()
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 6.0), facecolor=style.bg_color)
    for ax in axes:
        ax.set_facecolor(style.bg_color)

    drawn_turns, max_turns = _add_top_view(axes[0], core, wire, turns, style)
    _add_side_view(axes[1], core, wire, drawn_turns, style)

    title = (
        f"Toroid {core.part_number} | OD={core.od_mm:.2f} mm ID={core.id_mm:.2f} mm H={core.height_mm:.2f} mm | "
        f"AWG {wire.awg} ({wire.diameter_mm:.3f} mm) | Turns req={turns}, drawn={drawn_turns}"
    )
    fig.suptitle(title, fontsize=12, color=style.text_color, y=0.985)

    if turns > max_turns:
        fig.text(
            0.50,
            0.02,
            f"Note: Requested turns exceed single-layer geometric capacity ({max_turns}). Showing {drawn_turns} turns.",
            ha="center",
            va="center",
            fontsize=9,
            color="#991B1B",
        )

    fig.tight_layout(rect=[0, 0.05, 1, 0.95])

    out = Path(out_path) if out_path else _default_output_path(core.part_number, awg, turns)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    print(f"Saved: {out.resolve()}")

    if show:
        plt.show()

    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw a realistic toroid visualization with winding.")
    parser.add_argument("--part", required=True, help='Part number (example: "2206").')
    parser.add_argument("--awg", default="18", help='Wire AWG from wire_lib_solid_awg (example: "18").')
    parser.add_argument("--turns", type=int, default=24, help="Requested turn count.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output image path (.png/.jpg/.svg). If omitted, saves to ./gorsellestirme/.",
    )
    parser.add_argument("--dpi", type=int, default=150, help="Output DPI for saved image.")
    parser.add_argument("--show", action="store_true", help="Show figure after saving.")
    args = parser.parse_args()

    lib = ToroidCoreLibrary()
    core = lib.get_core(args.part)
    if core is None:
        raise ValueError(f"Part number not found: {args.part}")

    plot_toroid(core, turns=args.turns, awg=args.awg, out_path=args.output, dpi=args.dpi, show=args.show)


if __name__ == "__main__":
    main()
