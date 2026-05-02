"""
modules/svg_renderer.py — SVG Renderer Module

Converts a DXF file to an SVG string using ezdxf's drawing (matplotlib-based)
add-on. Also provides an image export method (PNG) used by the Region Cropper.

Requirement: 1.3, 1.4, 4.2
"""

import io
import logging
import tempfile
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def dxf_to_svg(file_path: str | Path) -> str:
    """
    Convert a DXF file to an SVG string.

    Uses ezdxf's drawing add-on with the Matplotlib backend to render
    all modelspace entities to SVG format.

    Args:
        file_path: Path to the DXF file.

    Returns:
        SVG content as a UTF-8 string.

    Raises:
        ValueError: If the DXF file cannot be rendered.
    """
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend, must be set before pyplot
    import matplotlib.pyplot as plt

    file_path = Path(file_path)

    try:
        doc = ezdxf.readfile(str(file_path))
    except Exception as exc:
        raise ValueError(f"Không thể đọc file DXF để render SVG: {exc}") from exc

    # Create a figure with a white background; size will be auto-adjusted
    fig = plt.figure(figsize=(16, 12), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1], facecolor="white")
    ax.set_aspect("equal")

    try:
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
    except Exception as exc:
        plt.close(fig)
        raise ValueError(f"Lỗi khi render bản vẽ DXF sang SVG: {exc}") from exc

    # Tighten the layout and export to SVG string
    ax.autoscale()
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    svg_content = buf.getvalue()
    buf.close()

    logger.info("SVG rendered successfully for: %s (%d chars)", file_path.name, len(svg_content))
    return svg_content


def dxf_to_png_bytes(
    file_path: str | Path,
    dpi: int = 150,
    facecolor: str = "white",
) -> bytes:
    """
    Convert a DXF file to a PNG image and return raw bytes.

    Used by Region Cropper to produce a rasterized version of the drawing
    that can be cropped and resized with Pillow.

    Args:
        file_path: Path to the DXF file.
        dpi: Resolution in dots-per-inch. Higher = sharper, larger file.
        facecolor: Background color of the output image.

    Returns:
        PNG image as bytes.

    Raises:
        ValueError: If rendering fails.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    file_path = Path(file_path)

    try:
        doc = ezdxf.readfile(str(file_path))
    except Exception as exc:
        raise ValueError(f"Không thể đọc file DXF để render PNG: {exc}") from exc

    fig = plt.figure(figsize=(16, 12), facecolor=facecolor)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=facecolor)
    ax.set_aspect("equal")

    try:
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
    except Exception as exc:
        plt.close(fig)
        raise ValueError(f"Lỗi render DXF sang PNG: {exc}") from exc

    ax.autoscale()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor=facecolor)
    plt.close(fig)

    png_bytes = buf.getvalue()
    buf.close()

    logger.info(
        "PNG rendered: %s at %d dpi (%d bytes)", file_path.name, dpi, len(png_bytes)
    )
    return png_bytes


def get_drawing_bounds(doc_or_path: Any) -> dict[str, float] | None:
    """
    Retrieve the bounding box of the modelspace drawing in DXF coordinates.

    Returns a dict with keys: xmin, ymin, xmax, ymax.
    Returns None if bounds cannot be determined.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        if isinstance(doc_or_path, (str, Path)):
            doc = ezdxf.readfile(str(doc_or_path))
        else:
            doc = doc_or_path

        fig = plt.figure(figsize=(1, 1))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
        ax.autoscale()

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        plt.close(fig)

        return {
            "xmin": xlim[0],
            "xmax": xlim[1],
            "ymin": ylim[0],
            "ymax": ylim[1],
            "width": xlim[1] - xlim[0],
            "height": ylim[1] - ylim[0],
        }
    except Exception as exc:
        logger.warning("Could not determine drawing bounds: %s", exc)
        return None
