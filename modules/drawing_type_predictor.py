"""
modules/drawing_type_predictor.py — Drawing Type Predictor Module

Analyzes DXF metadata (layer names, scale, block names, title block text,
technical symbols) to predict the Drawing_Type with a confidence score.

If confidence >= DRAWING_TYPE_CONFIDENCE_THRESHOLD → suggest to user for confirmation.
If confidence < threshold → ask the user directly.

Requirement: 2.2, 2.3, 2.6
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DrawingTypePrediction:
    """Result of the drawing type prediction."""
    drawing_type: str       # Predicted type from DRAWING_TYPES list
    confidence: float       # 0.0 – 1.0
    reasoning: str          # Vietnamese explanation of why this type was predicted
    is_confident: bool      # True if confidence >= threshold


# ---------------------------------------------------------------------------
# Keyword dictionaries for heuristic scoring
# ---------------------------------------------------------------------------

# Layer name keywords → drawing type score boosts
_LAYER_KEYWORDS: dict[str, dict[str, float]] = {
    "Cơ khí (Mechanical)": {
        "dim": 2.0, "dimension": 2.0, "centerline": 2.0, "center": 1.5,
        "hidden": 1.5, "section": 1.5, "thread": 2.0, "hatch": 1.0,
        "tolerance": 2.0, "gdt": 2.0, "machining": 2.0, "surface": 1.5,
        "mech": 3.0, "part": 1.5, "assembly": 1.5, "bore": 1.5,
    },
    "Kiến trúc (Architectural)": {
        "wall": 3.0, "door": 2.5, "window": 2.5, "room": 2.5, "floor": 2.0,
        "arch": 2.0, "site": 2.0, "roof": 2.0, "stair": 2.0, "ceiling": 2.0,
        "column": 1.5, "beam": 1.0, "grid": 1.5, "level": 1.5,
    },
    "Điện (Electrical)": {
        "elec": 3.0, "power": 2.5, "circuit": 3.0, "panel": 2.0,
        "wire": 2.5, "cable": 2.5, "conduit": 2.0, "light": 1.5,
        "switch": 2.0, "outlet": 2.0, "voltage": 2.0,
    },
    "Nội thất (Interior)": {
        "furniture": 3.0, "interior": 3.0, "cabinet": 2.5, "kitchen": 2.5,
        "bath": 2.0, "sofa": 2.0, "decor": 2.0, "finish": 1.5,
    },
    "Ống & Đường ống (Piping & Plumbing)": {
        "pipe": 3.0, "piping": 3.0, "plumb": 3.0, "valve": 2.5,
        "fitting": 2.0, "flow": 2.0, "water": 1.5, "drain": 2.0,
        "hvac": 2.5, "duct": 2.5,
    },
    "Kết cấu thép (Structural)": {
        "struct": 3.0, "steel": 3.0, "beam": 2.5, "column": 2.5,
        "truss": 3.0, "frame": 2.0, "foundation": 2.5, "rebar": 2.5,
        "concrete": 2.0, "load": 1.5,
    },
}

# Block name keywords → drawing type score boosts
_BLOCK_KEYWORDS: dict[str, dict[str, float]] = {
    "Cơ khí (Mechanical)": {
        "bolt": 2.0, "nut": 2.0, "screw": 2.0, "gear": 2.5,
        "bearing": 2.5, "spring": 2.0, "weld": 2.0, "roughness": 2.0,
    },
    "Kiến trúc (Architectural)": {
        "north": 2.5, "arrow": 1.5, "window": 2.5, "door": 2.5,
        "bathroom": 2.5, "kitchen": 2.5,
    },
    "Điện (Electrical)": {
        "switch": 2.5, "socket": 2.5, "lamp": 2.5, "panel": 2.5,
        "breaker": 3.0, "transformer": 3.0,
    },
}

# Scale hints → drawing type boosts
_SCALE_HINTS: dict[str, list[float]] = {
    "Cơ khí (Mechanical)": [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0],
    "Kiến trúc (Architectural)": [50.0, 100.0, 200.0, 500.0],
    "Điện (Electrical)": [5.0, 10.0, 20.0, 50.0, 100.0],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_drawing_type(dxf_json: dict[str, Any]) -> DrawingTypePrediction:
    """
    Analyze DXF metadata and predict the drawing type.

    Scoring algorithm:
    1. Score each drawing type based on layer name keyword matches
    2. Adjust score based on block name matches
    3. Adjust score based on drawing scale hints
    4. Normalize scores to get confidence

    Args:
        dxf_json: Parsed DXF data from dxf_parser.parse_dxf()

    Returns:
        DrawingTypePrediction with type, confidence, and Vietnamese reasoning.
    """
    scores: dict[str, float] = {dt: 0.0 for dt in config.DRAWING_TYPES}

    layers = dxf_json.get("layers", [])
    blocks = dxf_json.get("blocks", [])
    metadata = dxf_json.get("metadata", {})
    texts = dxf_json.get("texts", [])
    title_block = dxf_json.get("title_block", {})

    reasons: dict[str, list[str]] = {dt: [] for dt in config.DRAWING_TYPES}

    # --- Step 1: Score from layer names ---
    layer_names = [layer["name"].lower() for layer in layers]
    for drawing_type, keywords in _LAYER_KEYWORDS.items():
        for layer_name in layer_names:
            for kw, boost in keywords.items():
                if kw in layer_name:
                    scores[drawing_type] += boost
                    reasons[drawing_type].append(f"layer '{layer_name}' chứa từ khóa '{kw}'")

    # --- Step 2: Score from block names ---
    block_names = [block["name"].lower() for block in blocks]
    for drawing_type, keywords in _BLOCK_KEYWORDS.items():
        for block_name in block_names:
            for kw, boost in keywords.items():
                if kw in block_name:
                    scores[drawing_type] += boost
                    reasons[drawing_type].append(f"block '{block_name}' chứa từ khóa '{kw}'")

    # --- Step 3: Score from drawing scale (DIMSCALE) ---
    dim_scale = float(metadata.get("dim_scale", 1.0))
    for drawing_type, scale_hints in _SCALE_HINTS.items():
        for hint in scale_hints:
            if abs(dim_scale - hint) / (hint + 1e-9) < 0.1:
                scores[drawing_type] += 1.5
                reasons[drawing_type].append(f"tỷ lệ DIMSCALE={dim_scale:.2f} phù hợp")

    # --- Step 4: Score from text content in title block / texts ---
    all_text = " ".join(
        t.get("content", "") for t in texts
    )
    all_text_lower = all_text.lower()

    _text_score_drawing_type("Cơ khí (Mechanical)", all_text_lower, scores, reasons,
        [("mechanical", 3.0), ("machine", 2.5), ("part", 1.5), ("assembly", 2.0),
         ("tolerance", 2.0), ("material", 1.5)])
    _text_score_drawing_type("Kiến trúc (Architectural)", all_text_lower, scores, reasons,
        [("architectural", 3.0), ("floor plan", 3.0), ("elevation", 2.0),
         ("section", 1.5), ("scale 1:", 1.0)])
    _text_score_drawing_type("Điện (Electrical)", all_text_lower, scores, reasons,
        [("electrical", 3.0), ("schematic", 2.5), ("circuit", 2.5), ("wiring", 3.0)])
    _text_score_drawing_type("Kết cấu thép (Structural)", all_text_lower, scores, reasons,
        [("structural", 3.0), ("steel", 2.5), ("reinforcement", 3.0)])

    # --- Determine winner ---
    total_score = sum(scores.values())
    if total_score < 1e-6:
        # No signals found — return low-confidence unknown
        return DrawingTypePrediction(
            drawing_type="Khác (Other)",
            confidence=0.0,
            reasoning="Không tìm thấy đặc điểm nhận dạng rõ ràng trong metadata bản vẽ.",
            is_confident=False,
        )

    best_type = max(scores, key=lambda dt: scores[dt])
    confidence = scores[best_type] / total_score

    # Build Vietnamese reasoning
    reason_points = reasons[best_type][:5]  # top 5 reasons
    if reason_points:
        reasoning_text = (
            f"Tôi nhận thấy đây có vẻ là bản vẽ **{best_type}** vì:\n"
            + "\n".join(f"- {r}" for r in reason_points)
        )
    else:
        reasoning_text = f"Dự đoán dựa trên các đặc điểm tổng thể của bản vẽ: **{best_type}**."

    is_confident = confidence >= config.DRAWING_TYPE_CONFIDENCE_THRESHOLD

    logger.info(
        "Drawing type prediction: %s (confidence=%.2f, confident=%s)",
        best_type, confidence, is_confident,
    )

    return DrawingTypePrediction(
        drawing_type=best_type,
        confidence=round(confidence, 3),
        reasoning=reasoning_text,
        is_confident=is_confident,
    )


def format_suggestion_message(prediction: DrawingTypePrediction) -> str:
    """
    Format a Vietnamese chat message suggesting the predicted drawing type.

    Returns the message string to be displayed in the Chat_Interface.
    """
    if not prediction.is_confident:
        return config.UI_DRAWING_TYPE_ASK

    return (
        f"{prediction.reasoning}\n\n"
        f"📌 Đề xuất: **{prediction.drawing_type}**\n\n"
        "Bạn xác nhận đây đúng là loại bản vẽ này không? "
        "Nếu không, hãy cho tôi biết loại bản vẽ chính xác để tôi áp dụng đúng tiêu chuẩn kiểm tra."
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _text_score_drawing_type(
    drawing_type: str,
    text: str,
    scores: dict[str, float],
    reasons: dict[str, list[str]],
    keywords: list[tuple[str, float]],
) -> None:
    """Update scores in-place by scanning text for keyword matches."""
    for kw, boost in keywords:
        if kw in text:
            scores[drawing_type] += boost
            reasons[drawing_type].append(f"nội dung text chứa từ khóa '{kw}'")
