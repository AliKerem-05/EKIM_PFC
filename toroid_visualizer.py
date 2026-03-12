from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

try:
    import plotly.graph_objects as go

    PLOTLY_READY = True
except Exception:
    go = None
    go = None
    PLOTLY_READY = False

from Ferrit_toroid_core_library import ToroidCoreLibrary, ToroidProperties
from wire_lib_solid_awg import SolarisWireLibrary, WireProperties


@dataclass
class ViewStyle:
    core_face_color: str = "#2563EB"
    core_edge_color: str = "#1D4ED8"
    core_highlight_color: str = "#60A5FA"
    core_shadow_color: str = "#1E3A8A"
    wire_color_main: str = "#D97706"
    wire_color_alt: str = "#F59E0B"
    wire_edge_color: str = "#7C2D12"
    bg_color: str = "#FFFFFF"
    text_color: str = "#111827"
    grid_color: str = "#9CA3AF"


PLOTLY_STATIC_ERROR: str | None = None
if PLOTLY_READY:
    try:
        import kaleido  # noqa: F401

        PLOTLY_STATIC_READY = True
    except Exception as exc:
        PLOTLY_STATIC_READY = False
        PLOTLY_STATIC_ERROR = str(exc)
else:
    PLOTLY_STATIC_READY = False


def _timestamp_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")


def _build_output_path(part_number: str, awg: str, turns: int, suffix: str = "", extension: str = ".png") -> Path:
    base_dir = Path(__file__).resolve().parent
    safe_awg = awg.replace("/", "_")
    suffix_text = f"_{suffix}" if suffix else ""
    return base_dir / "gorsellestirme" / f"toroid_{part_number}_awg{safe_awg}_n{turns}_{_timestamp_tag()}{suffix_text}{extension}"


def _default_output_path(part_number: str, awg: str, turns: int) -> Path:
    return _build_output_path(part_number, awg, turns)


def _default_output_path_3d(part_number: str, awg: str, turns: int, extension: str = ".png") -> Path:
    return _build_output_path(part_number, awg, turns, suffix="3d", extension=extension)


def _compute_turn_capacity(core: ToroidProperties, wire_d_mm: float) -> int:
    mean_radius = (core.od_mm + core.id_mm) / 4.0
    pitch = wire_d_mm * 1.12
    return max(1, int((2.0 * math.pi * mean_radius) // pitch))


def _get_wire(awg: str) -> WireProperties:
    wire = SolarisWireLibrary().get_wire(awg)
    if wire is None:
        raise ValueError(f"AWG not found: {awg}")
    return wire


def _add_top_view(
    ax: plt.Axes,
    core: ToroidProperties,
    wire: WireProperties,
    turns: int,
    style: ViewStyle,
) -> tuple[int, int]:
    outer_r = core.od_mm / 2.0
    inner_r = core.id_mm / 2.0

    ax.add_patch(Circle((0, 0), outer_r, facecolor=style.core_face_color, edgecolor=style.core_edge_color, linewidth=2.4, zorder=1))
    ax.add_patch(
        Circle(
            (0, 0),
            (outer_r + inner_r) / 2.0,
            facecolor=style.core_highlight_color,
            edgecolor="none",
            alpha=0.18,
            zorder=1.2,
        )
    )
    ax.add_patch(Circle((0, 0), inner_r, facecolor=style.bg_color, edgecolor=style.core_edge_color, linewidth=2.0, zorder=2))

    wire_r = max(0.14, wire.diameter_mm / 2.0)
    winding_r_outer = outer_r + wire_r * 0.95
    winding_r_inner = max(wire_r * 1.4, inner_r - wire_r * 0.95)

    max_turns = _compute_turn_capacity(core, wire.diameter_mm)
    drawn_turns = max(1, min(turns, max_turns))

    for i in range(drawn_turns):
        theta = 2.0 * math.pi * i / drawn_turns
        color = style.wire_color_main if i % 2 == 0 else style.wire_color_alt
        for radius in (winding_r_outer, winding_r_inner):
            ax.add_patch(
                Circle(
                    (radius * math.cos(theta), radius * math.sin(theta)),
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
    ax.text(x_dim_outer + 1.9, 0, f"OD = {core.od_mm:.2f} mm", rotation=90, ha="left", va="center", fontsize=9, color=style.text_color)

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
    side_clearance_mm: float,
) -> None:
    _ = turns
    outer_w = core.od_mm
    inner_w = core.id_mm
    height = core.height_mm
    leg_w = (outer_w - inner_w) / 2.0
    left_leg_x = -outer_w / 2.0
    right_leg_x = inner_w / 2.0

    for leg_x in (left_leg_x, right_leg_x):
        ax.add_patch(
            Rectangle(
                (leg_x, -height / 2.0),
                leg_w,
                height,
                facecolor=style.core_face_color,
                edgecolor=style.core_edge_color,
                linewidth=2.2,
                zorder=2,
            )
        )

    offset = max(0.12, side_clearance_mm)
    rounding = max(0.7, min(leg_w, height) * 0.16)
    for leg_x in (left_leg_x, right_leg_x):
        ax.add_patch(
            FancyBboxPatch(
                (leg_x - offset, -height / 2.0 - offset),
                leg_w + 2.0 * offset,
                height + 2.0 * offset,
                boxstyle=f"round,pad=0,rounding_size={rounding}",
                facecolor="none",
                edgecolor=style.wire_color_main,
                linewidth=2.0,
                zorder=1,
            )
        )

    margin_x = max(10.0, outer_w * 0.24)
    margin_y = max(4.8, height * 0.75)
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


def _rectangular_core_mesh(core: ToroidProperties) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, str]]:
    outer_r = core.od_mm / 2.0
    inner_r = core.id_mm / 2.0
    half_h = core.height_mm / 2.0

    theta = np.linspace(0.0, 2.0 * math.pi, 160)
    z_vals = np.linspace(-half_h, half_h, 2)
    theta_grid, z_grid = np.meshgrid(theta, z_vals)

    outer_x = outer_r * np.cos(theta_grid)
    outer_y = outer_r * np.sin(theta_grid)
    inner_x = inner_r * np.cos(theta_grid)
    inner_y = inner_r * np.sin(theta_grid)

    r_vals = np.linspace(inner_r, outer_r, 56)
    theta_face, r_grid = np.meshgrid(theta, r_vals)
    top_x = r_grid * np.cos(theta_face)
    top_y = r_grid * np.sin(theta_face)
    top_z = np.full_like(top_x, half_h)
    bottom_z = np.full_like(top_x, -half_h)

    return {
        "outer": (outer_x, outer_y, z_grid, "face"),
        "inner": (inner_x, inner_y, z_grid, "shadow"),
        "top": (top_x, top_y, top_z, "highlight"),
        "bottom": (top_x, top_y, bottom_z, "shadow"),
    }


def _rounded_rect_loop(inner_r: float, outer_r: float, bottom_z: float, top_z: float, corner: float) -> tuple[np.ndarray, np.ndarray]:
    seg = 28
    right_z = np.linspace(bottom_z + corner, top_z - corner, seg)
    arc1 = np.linspace(0.0, math.pi / 2.0, seg)
    top_r = np.linspace(outer_r - corner, inner_r + corner, seg)
    arc2 = np.linspace(math.pi / 2.0, math.pi, seg)
    left_z = np.linspace(top_z - corner, bottom_z + corner, seg)
    arc3 = np.linspace(math.pi, 1.5 * math.pi, seg)
    bottom_r = np.linspace(inner_r + corner, outer_r - corner, seg)
    arc4 = np.linspace(1.5 * math.pi, 2.0 * math.pi, seg)

    rs = [np.full(seg, outer_r)]
    zs = [right_z]

    c1_r, c1_z = outer_r - corner, top_z - corner
    rs.append(c1_r + corner * np.cos(arc1))
    zs.append(c1_z + corner * np.sin(arc1))

    rs.append(top_r)
    zs.append(np.full(seg, top_z))

    c2_r, c2_z = inner_r + corner, top_z - corner
    rs.append(c2_r + corner * np.cos(arc2))
    zs.append(c2_z + corner * np.sin(arc2))

    rs.append(np.full(seg, inner_r))
    zs.append(left_z)

    c3_r, c3_z = inner_r + corner, bottom_z + corner
    rs.append(c3_r + corner * np.cos(arc3))
    zs.append(c3_z + corner * np.sin(arc3))

    rs.append(bottom_r)
    zs.append(np.full(seg, bottom_z))

    c4_r, c4_z = outer_r - corner, bottom_z + corner
    rs.append(c4_r + corner * np.cos(arc4))
    zs.append(c4_z + corner * np.sin(arc4))

    return np.concatenate(rs), np.concatenate(zs)


def _winding_loop_points(core: ToroidProperties, wire: WireProperties, phi: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    outer_r = core.od_mm / 2.0 + wire.diameter_mm * 0.85
    inner_r = core.id_mm / 2.0 - wire.diameter_mm * 0.90
    top_z = core.height_mm / 2.0 + wire.diameter_mm * 0.85
    bottom_z = -top_z
    corner = min((outer_r - inner_r) * 0.22, (top_z - bottom_z) * 0.18)

    r_path, z_path = _rounded_rect_loop(inner_r, outer_r, bottom_z, top_z, corner)
    x = r_path * math.cos(phi)
    y = r_path * math.sin(phi)
    return x, y, z_path


def _tube_from_centerline(xs: np.ndarray, ys: np.ndarray, zs: np.ndarray, wire_radius: float, phi: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    radial_dir = np.array([math.cos(phi), math.sin(phi), 0.0])
    azimuth_dir = np.array([-math.sin(phi), math.cos(phi), 0.0])

    dx = np.gradient(xs)
    dy = np.gradient(ys)
    dz = np.gradient(zs)
    dr = dx * radial_dir[0] + dy * radial_dir[1]

    tangent_2d = np.stack([dr, dz], axis=1)
    tangent_norm = np.linalg.norm(tangent_2d, axis=1)
    tangent_norm[tangent_norm == 0.0] = 1.0
    tangent_2d = tangent_2d / tangent_norm[:, None]

    normal_2d = np.stack([-tangent_2d[:, 1], tangent_2d[:, 0]], axis=1)
    normal_3d = normal_2d[:, 0:1] * radial_dir + normal_2d[:, 1:2] * np.array([0.0, 0.0, 1.0])

    theta = np.linspace(0.0, 2.0 * math.pi, 18)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    center = np.stack([xs, ys, zs], axis=1)
    tube_x = np.zeros((theta.size, xs.size))
    tube_y = np.zeros((theta.size, ys.size))
    tube_z = np.zeros((theta.size, zs.size))

    for i in range(theta.size):
        offset = wire_radius * (cos_t[i] * azimuth_dir + sin_t[i] * normal_3d)
        points = center + offset
        tube_x[i, :] = points[:, 0]
        tube_y[i, :] = points[:, 1]
        tube_z[i, :] = points[:, 2]

    return tube_x, tube_y, tube_z


def _add_plotly_wire_surface(fig: go.Figure, xs: np.ndarray, ys: np.ndarray, zs: np.ndarray, wire_radius: float, phi: float, style: ViewStyle, color: str) -> None:
    tube_x, tube_y, tube_z = _tube_from_centerline(xs, ys, zs, wire_radius, phi)
    fig.add_trace(
        go.Surface(
            x=tube_x,
            y=tube_y,
            z=tube_z,
            showscale=False,
            colorscale=[[0.0, color], [1.0, color]],
            opacity=1.0,
            hoverinfo="skip",
            lighting={"ambient": 0.42, "diffuse": 0.95, "specular": 0.58, "roughness": 0.28, "fresnel": 0.08},
            lightposition={"x": 280, "y": -240, "z": 220},
            contours={"x": {"show": False}, "y": {"show": False}, "z": {"show": False}},
        )
    )


def _build_plotly_3d_figure(
    core: ToroidProperties,
    wire: WireProperties,
    turns: int,
    style: ViewStyle,
) -> tuple[go.Figure, int, int]:
    if not PLOTLY_READY:
        raise RuntimeError("plotly is required for 3D output")

    fig = go.Figure()
    meshes = _rectangular_core_mesh(core)
    for x, y, z, tone in meshes.values():
        color = style.core_face_color
        if tone == "highlight":
            color = style.core_highlight_color
        elif tone == "shadow":
            color = style.core_shadow_color
        fig.add_trace(
            go.Surface(
                x=x,
                y=y,
                z=z,
                showscale=False,
                colorscale=[[0.0, color], [1.0, color]],
                opacity=1.0,
                hoverinfo="skip",
                lighting={"ambient": 0.55, "diffuse": 0.8, "specular": 0.18, "roughness": 0.75},
                lightposition={"x": 300, "y": -240, "z": 220},
            )
        )

    max_turns = _compute_turn_capacity(core, wire.diameter_mm)
    drawn_turns = max(1, min(turns, max_turns))
    wire_radius = max(0.14, wire.diameter_mm / 2.0)
    for i in range(drawn_turns):
        phi = 2.0 * math.pi * i / drawn_turns
        xs, ys, zs = _winding_loop_points(core, wire, phi)
        color = style.wire_color_main if i % 2 == 0 else style.wire_color_alt
        _add_plotly_wire_surface(fig, xs, ys, zs, wire_radius, phi, style, style.wire_edge_color)
        _add_plotly_wire_surface(fig, xs, ys, zs, wire_radius * 0.84, phi, style, color)

    limit_xy = core.od_mm * 0.72
    limit_z = max(core.height_mm * 1.7, wire.diameter_mm * 7.5)
    fig.update_layout(
        title=(
            f"Toroid 3D {core.part_number} | OD={core.od_mm:.2f} mm ID={core.id_mm:.2f} mm H={core.height_mm:.2f} mm | "
            f"AWG {wire.awg} ({wire.diameter_mm:.3f} mm) | Turns req={turns}, drawn={drawn_turns}"
        ),
        paper_bgcolor=style.bg_color,
        plot_bgcolor=style.bg_color,
        margin={"l": 0, "r": 0, "t": 52, "b": 0},
        scene={
            "xaxis": {"title": "X (mm)", "range": [-limit_xy, limit_xy], "backgroundcolor": style.bg_color},
            "yaxis": {"title": "Y (mm)", "range": [-limit_xy, limit_xy], "backgroundcolor": style.bg_color},
            "zaxis": {"title": "Z (mm)", "range": [-limit_z, limit_z], "backgroundcolor": style.bg_color},
            "aspectmode": "manual",
            "aspectratio": {"x": 1, "y": 1, "z": max(0.45, limit_z / limit_xy)},
            "camera": {"eye": {"x": 1.45, "y": -1.65, "z": 0.72}},
        },
    )
    return fig, drawn_turns, max_turns


def _write_plotly_static(fig: go.Figure, out: Path, dpi: int) -> None:
    if not PLOTLY_STATIC_READY:
        raise RuntimeError(f"Static 3D export requires kaleido. Detail: {PLOTLY_STATIC_ERROR}")

    scale = max(1.0, dpi / 100.0)
    fig.write_image(str(out), width=1200, height=900, scale=scale)


def plot_toroid(
    core: ToroidProperties,
    turns: int = 24,
    awg: str = "18",
    out_path: str | None = None,
    dpi: int = 150,
    show: bool = False,
    side_clearance_mm: float = 0.6,
) -> Path:
    wire = _get_wire(awg)
    style = ViewStyle()
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 6.0), facecolor=style.bg_color)
    for ax in axes:
        ax.set_facecolor(style.bg_color)

    drawn_turns, max_turns = _add_top_view(axes[0], core, wire, turns, style)
    _add_side_view(axes[1], core, wire, drawn_turns, style, side_clearance_mm)

    title = (
        f"Toroid {core.part_number} | OD={core.od_mm:.2f} mm ID={core.id_mm:.2f} mm H={core.height_mm:.2f} mm | "
        f"AWG {wire.awg} ({wire.diameter_mm:.3f} mm) | Turns req={turns}, drawn={drawn_turns}"
    )
    fig.suptitle(title, fontsize=12, color=style.text_color, y=0.985)

    if turns > max_turns:
        fig.text(0.50, 0.02, f"Note: Requested turns exceed single-layer geometric capacity ({max_turns}). Showing {drawn_turns} turns.", ha="center", va="center", fontsize=9, color="#991B1B")

    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    out = Path(out_path) if out_path else _default_output_path(core.part_number, awg, turns)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    print(f"Saved: {out.resolve()}")
    if show:
        plt.show()
    plt.close(fig)
    return out


def plot_toroid_3d(
    core: ToroidProperties,
    turns: int = 24,
    awg: str = "18",
    out_path: str | None = None,
    dpi: int = 150,
    show: bool = False,
) -> Path:
    wire = _get_wire(awg)
    style = ViewStyle()
    out = Path(out_path) if out_path else _default_output_path_3d(core.part_number, awg, turns)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, _, _ = _build_plotly_3d_figure(core, wire, turns, style)
    suffix = out.suffix.lower()
    if suffix == ".html":
        fig.write_html(str(out), include_plotlyjs=True, full_html=True)
    elif suffix in {".png", ".pdf", ".svg"}:
        _write_plotly_static(fig, out, dpi)
    else:
        raise ValueError(f"Unsupported 3D output format: {suffix}")

    print(f"Saved: {out.resolve()}")
    if show and suffix != ".html":
        fig.show()
    return out


def plot_toroid_3d_interactive(core: ToroidProperties, turns: int = 24, awg: str = "18", out_path: str | None = None) -> Path:
    out = Path(out_path) if out_path else _default_output_path_3d(core.part_number, awg, turns, extension=".html")
    return plot_toroid_3d(core, turns=turns, awg=awg, out_path=str(out), show=False)


def save_toroid_pdf_bundle(
    core: ToroidProperties,
    turns: int = 24,
    awg: str = "18",
    out_path_2d: str | None = None,
    out_path_3d: str | None = None,
    dpi: int = 150,
) -> tuple[Path, Path]:
    pdf_2d = Path(out_path_2d) if out_path_2d else _build_output_path(core.part_number, awg, turns, extension=".pdf")
    pdf_3d = Path(out_path_3d) if out_path_3d else _default_output_path_3d(core.part_number, awg, turns, extension=".pdf")
    return (
        plot_toroid(core, turns=turns, awg=awg, out_path=str(pdf_2d), dpi=dpi, show=False),
        plot_toroid_3d(core, turns=turns, awg=awg, out_path=str(pdf_3d), dpi=dpi, show=False),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw a realistic toroid visualization with winding.")
    parser.add_argument("--part", required=True, help='Part number (example: "2206").')
    parser.add_argument("--awg", default="18", help='Wire AWG from wire_lib_solid_awg (example: "18").')
    parser.add_argument("--turns", type=int, default=24, help="Requested turn count.")
    parser.add_argument("--output", default=None, help="Output image path (.png/.jpg/.svg/.pdf/.html). If omitted, saves to ./gorsellestirme/.")
    parser.add_argument("--dpi", type=int, default=150, help="Output DPI for saved image.")
    parser.add_argument("--show", action="store_true", help="Show figure after saving.")
    parser.add_argument("--mode", choices=("2d", "3d", "3d-html", "pdf-bundle"), default="2d", help="Visualization mode. 3d/3d-html derive from the same Plotly geometry.")
    parser.add_argument("--side-clearance", type=float, default=0.6, help="Side view winding clearance around each toroid leg in mm.")
    args = parser.parse_args()

    core = ToroidCoreLibrary().get_core(args.part)
    if core is None:
        raise ValueError(f"Part number not found: {args.part}")

    if args.mode == "3d":
        plot_toroid_3d(core, turns=args.turns, awg=args.awg, out_path=args.output, dpi=args.dpi, show=args.show)
    elif args.mode == "3d-html":
        plot_toroid_3d_interactive(core, turns=args.turns, awg=args.awg, out_path=args.output)
    elif args.mode == "pdf-bundle":
        save_toroid_pdf_bundle(core, turns=args.turns, awg=args.awg, out_path_2d=args.output, out_path_3d=None, dpi=args.dpi)
    else:
        plot_toroid(core, turns=args.turns, awg=args.awg, out_path=args.output, dpi=args.dpi, show=args.show, side_clearance_mm=args.side_clearance)


if __name__ == "__main__":
    main()


