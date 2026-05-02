"""
modules/dxf_parser.py — DXF Parser Module

Reads a DXF file using ezdxf and converts it into a structured JSON-serializable
dictionary. Extracts all entities, layers, blocks, dimensions, text annotations,
and title block metadata without omitting any component.

Requirement: 1.2, 1.3, 1.6, 1.7
"""

import logging
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.document import Drawing
from ezdxf.entities import DXFEntity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_dxf(file_path: str | Path) -> dict[str, Any]:
    """
    Parse a DXF file and return a structured JSON-serializable dictionary.

    Args:
        file_path: Absolute or relative path to the .dxf file.

    Returns:
        A dictionary with keys: metadata, layers, blocks, entities, dimensions,
        texts, title_block, extents.

    Raises:
        ValueError: If the file cannot be parsed by ezdxf.
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        doc: Drawing = ezdxf.readfile(str(file_path))
    except ezdxf.DXFStructureError as exc:
        raise ValueError(f"Lỗi cấu trúc DXF: {exc}") from exc
    except ezdxf.DXFError as exc:
        raise ValueError(f"Không thể đọc file DXF: {exc}") from exc

    logger.info("Parsing DXF file: %s", file_path.name)

    result: dict[str, Any] = {
        "metadata": _extract_metadata(doc, file_path),
        "layers": _extract_layers(doc),
        "blocks": _extract_blocks(doc),
        "entities": _extract_entities(doc),
        "dimensions": _extract_dimensions(doc),
        "texts": _extract_texts(doc),
        "title_block": _extract_title_block(doc),
        "extents": _extract_extents(doc),
    }

    logger.info(
        "DXF parsed: %d entities, %d dimensions, %d text objects",
        len(result["entities"]),
        len(result["dimensions"]),
        len(result["texts"]),
    )
    return result


def count_entities(dxf_json: dict[str, Any]) -> int:
    """Return total entity count for complexity checking."""
    return len(dxf_json.get("entities", []))


# ---------------------------------------------------------------------------
# Private extraction helpers
# ---------------------------------------------------------------------------

def _extract_metadata(doc: Drawing, file_path: Path) -> dict[str, Any]:
    """Extract file-level metadata: version, units, scale, filename."""
    header = doc.header
    return {
        "filename": file_path.name,
        "dxf_version": doc.dxfversion,
        # $INSUNITS: 4 = mm, 2 = cm, 6 = m, 1 = inch, etc.
        "units": header.get("$INSUNITS", 4),
        # $DIMSCALE: overall scale factor for dimensions
        "dim_scale": header.get("$DIMSCALE", 1.0),
        # $LTSCALE: linetype scale
        "lt_scale": header.get("$LTSCALE", 1.0),
        # $MEASUREMENT: 0 = English, 1 = Metric
        "measurement": header.get("$MEASUREMENT", 1),
        # Drawing limits (paper space extents)
        "limits_min": _vec_to_list(header.get("$LIMMIN")),
        "limits_max": _vec_to_list(header.get("$LIMMAX")),
        # First and third angle projection symbol flag
        "first_angle": header.get("$DIMANNO", None),
    }


def _extract_layers(doc: Drawing) -> list[dict[str, Any]]:
    """Extract all layer definitions with name, color, linetype, and visibility."""
    layers = []
    for layer in doc.layers:
        layers.append({
            "name": layer.dxf.name,
            "color": layer.dxf.color,
            "linetype": layer.dxf.get("linetype", "CONTINUOUS"),
            "is_on": layer.is_on(),
            "is_locked": layer.is_locked(),
            "is_frozen": layer.is_frozen(),
            "lineweight": layer.dxf.get("lineweight", -1),
        })
    return layers


def _extract_blocks(doc: Drawing) -> list[dict[str, Any]]:
    """Extract block definitions: name, description, and entity count."""
    blocks = []
    for block in doc.blocks:
        # Skip model/paper space pseudo-blocks
        if block.name.startswith("*"):
            continue
        blocks.append({
            "name": block.name,
            "description": block.block.dxf.get("description", ""),
            "base_point": _vec_to_list(block.block.dxf.base_point),
            "entity_count": len(list(block)),
        })
    return blocks


def _extract_entities(doc: Drawing) -> list[dict[str, Any]]:
    """
    Extract all modelspace entities with their geometric properties.
    Handles: LINE, ARC, CIRCLE, ELLIPSE, LWPOLYLINE, POLYLINE, SPLINE,
    INSERT (block reference), HATCH, LEADER.
    """
    msp = doc.modelspace()
    entities = []
    for entity in msp:
        extracted = _entity_to_dict(entity)
        if extracted:
            entities.append(extracted)
    return entities


def _entity_to_dict(entity: DXFEntity) -> dict[str, Any] | None:
    """Convert a single DXF entity to a dictionary."""
    dxf = entity.dxf
    base: dict[str, Any] = {
        "type": entity.dxftype(),
        "handle": dxf.handle,
        "layer": dxf.get("layer", "0"),
        "color": dxf.get("color", 256),  # 256 = ByLayer
        "linetype": dxf.get("linetype", "BYLAYER"),
        "lineweight": dxf.get("lineweight", -1),
    }

    etype = entity.dxftype()

    try:
        if etype == "LINE":
            base.update({
                "start": _vec_to_list(dxf.start),
                "end": _vec_to_list(dxf.end),
            })
        elif etype == "ARC":
            base.update({
                "center": _vec_to_list(dxf.center),
                "radius": dxf.radius,
                "start_angle": dxf.start_angle,
                "end_angle": dxf.end_angle,
            })
        elif etype == "CIRCLE":
            base.update({
                "center": _vec_to_list(dxf.center),
                "radius": dxf.radius,
            })
        elif etype == "ELLIPSE":
            base.update({
                "center": _vec_to_list(dxf.center),
                "major_axis": _vec_to_list(dxf.major_axis),
                "ratio": dxf.ratio,
            })
        elif etype == "LWPOLYLINE":
            base.update({
                "points": [list(p) for p in entity.get_points()],
                "closed": entity.closed,
            })
        elif etype == "POLYLINE":
            verts = [_vec_to_list(v.dxf.location) for v in entity.vertices]
            base.update({
                "vertices": verts,
                "closed": bool(entity.dxf.flags & 1),
            })
        elif etype == "SPLINE":
            base.update({
                "degree": entity.dxf.degree,
                "control_points": [_vec_to_list(p) for p in entity.control_points],
                "closed": entity.closed,
            })
        elif etype == "INSERT":
            base.update({
                "block_name": dxf.name,
                "insert": _vec_to_list(dxf.insert),
                "x_scale": dxf.get("xscale", 1.0),
                "y_scale": dxf.get("yscale", 1.0),
                "rotation": dxf.get("rotation", 0.0),
            })
        elif etype == "HATCH":
            base.update({
                "pattern_name": dxf.get("pattern_name", ""),
                "solid_fill": dxf.get("solid_fill", 0),
            })
        elif etype == "LEADER":
            base.update({
                "vertices": [_vec_to_list(v) for v in entity.vertices],
            })
        # Unknown entity types are still captured with base info
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not fully extract entity %s (%s): %s", etype, base.get("handle"), exc)

    return base


def _extract_dimensions(doc: Drawing) -> list[dict[str, Any]]:
    """
    Extract all DIMENSION entities with measured value, position, and style.
    Handles: linear, aligned, angular, radial, diameter dimensions.
    """
    msp = doc.modelspace()
    dimensions = []
    for entity in msp.query("DIMENSION"):
        dxf = entity.dxf
        dim: dict[str, Any] = {
            "handle": dxf.handle,
            "layer": dxf.get("layer", "0"),
            "dim_type": int(dxf.get("dimtype", 0)) & 7,  # mask flag bits
            "text_override": dxf.get("text", ""),
            "actual_measurement": dxf.get("actual_measurement", None),
            "defpoint": _vec_to_list(dxf.get("defpoint")),
            "text_midpoint": _vec_to_list(dxf.get("text_midpoint")),
            "dimstyle": dxf.get("dimstyle", "Standard"),
        }
        # Attach geometry points based on dimension type
        try:
            dim["defpoint2"] = _vec_to_list(dxf.get("defpoint2"))
            dim["defpoint3"] = _vec_to_list(dxf.get("defpoint3"))
            dim["defpoint4"] = _vec_to_list(dxf.get("defpoint4"))
        except Exception:  # noqa: BLE001
            pass
        dimensions.append(dim)
    return dimensions


def _extract_texts(doc) -> list[dict[str, Any]]:
    """
    Extract all TEXT and MTEXT entities with content and position.
    Handles attribute differences between TEXT and MTEXT safely.
    """
    msp = doc.modelspace()
    texts = []
    
    for entity in msp.query("TEXT MTEXT"):
        dxf = entity.dxf
        etype = entity.dxftype()
        
        text_entry: dict[str, Any] = {
            "type": etype,
            "handle": dxf.handle,
            "layer": dxf.get("layer", "0"),
            "insert": _vec_to_list(dxf.get("insert", (0, 0, 0))),
        }

        if etype == "TEXT":
            text_entry["content"] = dxf.get("text", "")
            text_entry["height"] = dxf.get("height", 0.0)
            text_entry["rotation"] = dxf.get("rotation", 0.0)
            
        elif etype == "MTEXT":
            text_entry["content"] = entity.plain_text() 
            text_entry["raw_content"] = entity.text 
            text_entry["height"] = dxf.get("char_height", 0.0) 
            text_entry["width"] = dxf.get("width", 0.0)
            text_entry["rotation"] = dxf.get("rotation", 0.0)

        texts.append(text_entry)
        
    return texts


def _extract_title_block(doc: Drawing) -> dict[str, Any]:
    """
    Heuristically extract title block information from paper space entities.
    Looks for text entities inside common title block block references.
    """
    title_block: dict[str, Any] = {
        "found": False,
        "fields": {},
    }

    # Try paper space layout for title block content
    try:
        for layout in doc.layouts:
            if layout.name == "Model":
                continue  # skip model space
            for entity in layout:
                if entity.dxftype() in ("TEXT", "MTEXT"):
                    content = ""
                    if entity.dxftype() == "TEXT":
                        content = entity.dxf.get("text", "")
                    else:
                        content = entity.text
                    if content.strip():
                        title_block["found"] = True
                        # Store all text found in paper space layouts
                        existing = title_block["fields"].get("raw_texts", [])
                        existing.append(content.strip())
                        title_block["fields"]["raw_texts"] = existing
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not extract title block from layouts: %s", exc)

    # Also look for "TITLE", "TITLEBLOCK", "TB" named blocks in modelspace
    try:
        msp = doc.modelspace()
        for entity in msp.query("INSERT"):
            block_name = entity.dxf.get("name", "").upper()
            if any(kw in block_name for kw in ("TITLE", "TB", "TITLEBLK", "FRAME")):
                title_block["found"] = True
                title_block["title_block_block"] = entity.dxf.get("name")
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not find title block insert: %s", exc)

    return title_block


def _extract_extents(doc: Drawing) -> dict[str, Any]:
    """Extract the drawing extents (bounding box) from modelspace."""
    try:
        extents = doc.modelspace().get_extension_dict()
    except Exception:  # noqa: BLE001
        extents = None

    # Use EXTMIN/EXTMAX from header as fallback
    header = doc.header
    return {
        "extmin": _vec_to_list(header.get("$EXTMIN")),
        "extmax": _vec_to_list(header.get("$EXTMAX")),
    }


def _vec_to_list(vec: Any) -> list[float] | None:
    """Convert an ezdxf Vec2/Vec3 or similar to a plain Python list."""
    if vec is None:
        return None
    try:
        return [float(v) for v in vec]
    except (TypeError, ValueError):
        return None
