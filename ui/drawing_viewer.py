"""
ui/drawing_viewer.py — Drawing Viewer UI Component

Renders the SVG/PNG drawing in the left 3/4 of the Streamlit layout.
Provides zoom controls and basic drawing metadata display.

Requirement: 1.4, 2.1
"""

import base64
import logging
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


def render_drawing_viewer(
    svg_content: str | None,
    dxf_json: dict[str, Any] | None,
    filename: str | None,
) -> None:
    """
    Render the drawing viewer panel.

    If a DXF has been loaded, displays the SVG drawing along with
    basic metadata (entity count, dimensions, layers).
    If not loaded, shows an upload prompt.

    Args:
        svg_content: SVG markup string (from SVG Renderer).
        dxf_json: Parsed DXF data dict (from DXF Parser).
        filename: Original uploaded filename.
    """
    if svg_content is None:
        _render_empty_state()
        return

    # --- Drawing info header ---
    if filename:
        st.markdown(f"**📄 {filename}**")

    if dxf_json:
        _render_metadata_badges(dxf_json)

    # --- SVG display ---
    # Streamlit doesn't natively display SVG; we use an HTML iframe trick
    st.markdown("---")
    st.markdown("**🖼️ Bản Vẽ Kỹ Thuật**")
    _render_svg(svg_content)


def _render_empty_state() -> None:
    """Display upload instructions when no drawing is loaded."""
    st.markdown(
        """
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 60vh;
            color: #888;
            text-align: center;
        ">
            <div style="font-size: 4rem;">📐</div>
            <h3 style="margin-top: 1rem; color: #555;">Chưa có bản vẽ</h3>
            <p>Tải lên file DXF để bắt đầu kiểm tra.</p>
            <p style="font-size: 0.85rem; color: #aaa;">Hỗ trợ định dạng: .dxf</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_metadata_badges(dxf_json: dict[str, Any]) -> None:
    """Display quick-stats badges below the filename."""
    entity_count = len(dxf_json.get("entities", []))
    dim_count = len(dxf_json.get("dimensions", []))
    text_count = len(dxf_json.get("texts", []))
    layer_count = len(dxf_json.get("layers", []))
    metadata = dxf_json.get("metadata", {})
    dxf_version = metadata.get("dxf_version", "?")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Entities", entity_count)
    col2.metric("Kích thước", dim_count)
    col3.metric("Text", text_count)
    col4.metric("Layers", layer_count)
    col5.metric("DXF Ver.", dxf_version)


def _render_svg(svg_content: str) -> None:
    """
    Embed the SVG in a scrollable HTML container.

    Uses an <img src="data:..."> approach which is widely supported
    and avoids XSS risks compared to directly injecting SVG HTML.
    """
    # Encode SVG as base64 data URL
    svg_b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    data_url = f"data:image/svg+xml;base64,{svg_b64}"

    html = f"""
    <div style="
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: auto;
        max-height: 70vh;
        background: white;
        padding: 8px;
        text-align: center;
    ">
        <img
            src="{data_url}"
            alt="Bản vẽ kỹ thuật DXF"
            style="max-width: 100%; height: auto; cursor: zoom-in;"
            onclick="this.style.maxWidth = this.style.maxWidth === '100%' ? '200%' : '100%';"
        />
    </div>
    <p style="font-size: 0.75rem; color: #aaa; margin-top: 4px; text-align: center;">
        Click vào ảnh để phóng to / thu nhỏ
    </p>
    """
    st.markdown(html, unsafe_allow_html=True)
