"""
modules/region_cropper.py — Region Cropper Module

Given a DXF coordinate region (bounding box) and a PNG rendering of the full
drawing, this module:
  1. Converts DXF coordinates → pixel coordinates
  2. Crops the PNG with optional padding
  3. Upscales the crop for higher-resolution VLM analysis

Requirement: 4.1 – 4.7
"""

import base64
import io
import logging
from dataclasses import dataclass
from typing import Any

from PIL import Image

import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DXFRegion:
    """A rectangular region in DXF coordinate space."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    padding: float = config.CROP_PADDING_DXF_UNITS  # DXF units of padding


@dataclass
class DrawingBounds:
    """
    Maps between DXF coordinate space and pixel space of the rendered PNG.
    Both spaces are axis-aligned but Y may be flipped (image Y grows downward).
    """
    dxf_xmin: float
    dxf_ymin: float
    dxf_xmax: float
    dxf_ymax: float
    img_width_px: int
    img_height_px: int

    @property
    def dxf_width(self) -> float:
        return self.dxf_xmax - self.dxf_xmin

    @property
    def dxf_height(self) -> float:
        return self.dxf_ymax - self.dxf_ymin


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def crop_region(
    png_bytes: bytes,
    region: DXFRegion,
    bounds: DrawingBounds,
    target_width: int = config.CROP_TARGET_WIDTH_PX,
    target_height: int = config.CROP_TARGET_HEIGHT_PX,
) -> bytes:
    """
    Crop a region from the full-drawing PNG and return high-res PNG bytes.

    Args:
        png_bytes: Full-drawing PNG as bytes (from SVG Renderer).
        region: DXF-coordinate bounding box to crop, including padding.
        bounds: Mapping from DXF coords to pixel coords.
        target_width: Desired output width in pixels.
        target_height: Desired output height in pixels.

    Returns:
        Cropped and upscaled PNG as bytes.

    Raises:
        ValueError: If the region is invalid or outside drawing bounds.
    """
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    actual_w, actual_h = img.size

    # Apply padding to the DXF region
    padded = DXFRegion(
        xmin=region.xmin - region.padding,
        ymin=region.ymin - region.padding,
        xmax=region.xmax + region.padding,
        ymax=region.ymax + region.padding,
        padding=0.0,
    )

    # Validate region is within bounds
    if not _region_intersects_bounds(padded, bounds):
        logger.warning(
            "Crop region (%.1f, %.1f, %.1f, %.1f) is outside drawing bounds "
            "(%.1f, %.1f, %.1f, %.1f). Returning full image.",
            padded.xmin, padded.ymin, padded.xmax, padded.ymax,
            bounds.dxf_xmin, bounds.dxf_ymin, bounds.dxf_xmax, bounds.dxf_ymax,
        )
        return png_bytes  # Fallback to full image

    # Clamp region to drawing bounds
    clamped = DXFRegion(
        xmin=max(padded.xmin, bounds.dxf_xmin),
        ymin=max(padded.ymin, bounds.dxf_ymin),
        xmax=min(padded.xmax, bounds.dxf_xmax),
        ymax=min(padded.ymax, bounds.dxf_ymax),
    )

    # Convert DXF → pixel coordinates
    pixel_box = _dxf_region_to_pixel_box(clamped, bounds, actual_w, actual_h)
    left, upper, right, lower = pixel_box

    # Guard against degenerate boxes
    if right <= left or lower <= upper:
        logger.warning("Degenerate crop box %s. Returning full image.", pixel_box)
        return png_bytes

    cropped = img.crop((left, upper, right, lower))
    resized = cropped.resize((target_width, target_height), Image.LANCZOS)

    buf = io.BytesIO()
    resized.save(buf, format="PNG")
    result = buf.getvalue()
    buf.close()

    logger.info(
        "Cropped region (DXF: %.1f,%.1f → %.1f,%.1f) to %dx%d px",
        region.xmin, region.ymin, region.xmax, region.ymax,
        target_width, target_height,
    )
    return result


def png_bytes_to_base64(png_bytes: bytes) -> str:
    """Encode PNG bytes as a base64 string for embedding in OpenAI API calls."""
    return base64.b64encode(png_bytes).decode("utf-8")


def make_drawing_bounds(
    png_bytes: bytes,
    svg_bounds: dict[str, float],
) -> DrawingBounds:
    """
    Construct a DrawingBounds from the PNG image size and SVG/matplotlib axis bounds.

    Args:
        png_bytes: Full-drawing PNG bytes.
        svg_bounds: Dict with keys xmin, xmax, ymin, ymax (from svg_renderer.get_drawing_bounds).

    Returns:
        DrawingBounds instance.
    """
    img = Image.open(io.BytesIO(png_bytes))
    w, h = img.size
    return DrawingBounds(
        dxf_xmin=svg_bounds["xmin"],
        dxf_ymin=svg_bounds["ymin"],
        dxf_xmax=svg_bounds["xmax"],
        dxf_ymax=svg_bounds["ymax"],
        img_width_px=w,
        img_height_px=h,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _dxf_region_to_pixel_box(
    region: DXFRegion,
    bounds: DrawingBounds,
    actual_w: int,
    actual_h: int,
) -> tuple[int, int, int, int]:
    """
    Convert a DXF-coordinate region to a PIL pixel crop box (left, upper, right, lower).

    DXF Y-axis points upward; image Y-axis points downward → flip Y.
    """
    dw = bounds.dxf_width
    dh = bounds.dxf_height

    if dw == 0 or dh == 0:
        return (0, 0, actual_w, actual_h)

    # Normalize to [0, 1] in DXF space
    nx_min = (region.xmin - bounds.dxf_xmin) / dw
    nx_max = (region.xmax - bounds.dxf_xmin) / dw
    ny_min = (region.ymin - bounds.dxf_ymin) / dh  # DXF bottom
    ny_max = (region.ymax - bounds.dxf_ymin) / dh  # DXF top

    # Map to pixel coords (flip Y: image top = DXF top)
    left = int(nx_min * actual_w)
    right = int(nx_max * actual_w)
    upper = int((1.0 - ny_max) * actual_h)  # DXF top → image top (small y)
    lower = int((1.0 - ny_min) * actual_h)  # DXF bottom → image bottom (large y)

    # Clamp to image dimensions
    left = max(0, min(left, actual_w))
    right = max(0, min(right, actual_w))
    upper = max(0, min(upper, actual_h))
    lower = max(0, min(lower, actual_h))

    return (left, upper, right, lower)


def _region_intersects_bounds(region: DXFRegion, bounds: DrawingBounds) -> bool:
    """Return True if the DXF region overlaps with the drawing bounds at all."""
    return (
        region.xmax > bounds.dxf_xmin
        and region.xmin < bounds.dxf_xmax
        and region.ymax > bounds.dxf_ymin
        and region.ymin < bounds.dxf_ymax
    )
