"""
modules/session_db.py — Session Database Module

Provides a typed interface over Streamlit's session_state to store and retrieve
all data for the current working session:
  - DXF file info (name, JSON data, PNG bytes, SVG string)
  - Drawing type (predicted + confirmed)
  - Analysis results from each node
  - Chat message history
  - Drawing bounds for region cropper

No external database is used — all data lives in st.session_state for the
lifetime of the Streamlit session.

Requirement: 1.7, 2.4, 2.5, 3.4, 8.5, 11.3
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Chat message model
# ---------------------------------------------------------------------------

@dataclass
class ChatMessage:
    """A single chat message with role and content."""
    role: str   # "user" | "assistant" | "system"
    content: str


# ---------------------------------------------------------------------------
# Session keys (constants to avoid typos)
# ---------------------------------------------------------------------------

_KEY_DXF_FILENAME = "db_dxf_filename"
_KEY_DXF_JSON = "db_dxf_json"
_KEY_DXF_PNG_BYTES = "db_dxf_png_bytes"
_KEY_DXF_SVG = "db_dxf_svg"
_KEY_DRAWING_TYPE_PREDICTED = "db_drawing_type_predicted"
_KEY_DRAWING_TYPE_CONFIRMED = "db_drawing_type_confirmed"
_KEY_DRAWING_BOUNDS = "db_drawing_bounds"
_KEY_ANALYSIS_RESULT = "db_analysis_result"
_KEY_DIMENSION_RESULT = "db_dimension_result"
_KEY_ANNOTATION_RESULT = "db_annotation_result"
_KEY_STANDARD_RESULT = "db_standard_result"
_KEY_SELF_CHECK_RESULT = "db_self_check_result"   # Self-Check node output
_KEY_CHAT_HISTORY = "db_chat_history"
_KEY_AWAITING_TYPE_CONFIRMATION = "db_awaiting_type_confirmation"
_KEY_REVIEW_COMPLETE = "db_review_complete"


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def init_session() -> None:
    """
    Initialize all session keys with default values if they don't exist yet.
    Call this at the top of every Streamlit rerun.
    """
    defaults: dict[str, Any] = {
        _KEY_DXF_FILENAME: None,
        _KEY_DXF_JSON: None,
        _KEY_DXF_PNG_BYTES: None,
        _KEY_DXF_SVG: None,
        _KEY_DRAWING_TYPE_PREDICTED: None,
        _KEY_DRAWING_TYPE_CONFIRMED: None,
        _KEY_DRAWING_BOUNDS: None,
        _KEY_ANALYSIS_RESULT: None,
        _KEY_DIMENSION_RESULT: None,
        _KEY_ANNOTATION_RESULT: None,
        _KEY_STANDARD_RESULT: None,
        _KEY_SELF_CHECK_RESULT: None,
        _KEY_CHAT_HISTORY: [],
        _KEY_AWAITING_TYPE_CONFIRMATION: False,
        _KEY_REVIEW_COMPLETE: False,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ---------------------------------------------------------------------------
# DXF file data
# ---------------------------------------------------------------------------

def save_dxf_data(
    filename: str,
    dxf_json: dict[str, Any],
    png_bytes: bytes,
    svg_content: str,
) -> None:
    """Persist parsed DXF data for this session."""
    st.session_state[_KEY_DXF_FILENAME] = filename
    st.session_state[_KEY_DXF_JSON] = dxf_json
    st.session_state[_KEY_DXF_PNG_BYTES] = png_bytes
    st.session_state[_KEY_DXF_SVG] = svg_content
    logger.info("Session: DXF data saved for file '%s'", filename)


def get_dxf_filename() -> str | None:
    return st.session_state.get(_KEY_DXF_FILENAME)


def get_dxf_json() -> dict[str, Any] | None:
    return st.session_state.get(_KEY_DXF_JSON)


def get_dxf_png_bytes() -> bytes | None:
    return st.session_state.get(_KEY_DXF_PNG_BYTES)


def get_dxf_svg() -> str | None:
    return st.session_state.get(_KEY_DXF_SVG)


def has_dxf_loaded() -> bool:
    """Return True if a DXF file has been successfully loaded."""
    return st.session_state.get(_KEY_DXF_JSON) is not None


# ---------------------------------------------------------------------------
# Drawing type
# ---------------------------------------------------------------------------

def save_drawing_type_predicted(drawing_type: str, reasoning: str, confidence: float) -> None:
    """Save the predictor's output (before user confirmation)."""
    st.session_state[_KEY_DRAWING_TYPE_PREDICTED] = {
        "type": drawing_type,
        "reasoning": reasoning,
        "confidence": confidence,
    }


def save_drawing_type_confirmed(drawing_type: str) -> None:
    """Save the user-confirmed drawing type."""
    st.session_state[_KEY_DRAWING_TYPE_CONFIRMED] = drawing_type
    st.session_state[_KEY_AWAITING_TYPE_CONFIRMATION] = False
    logger.info("Session: Drawing type confirmed as '%s'", drawing_type)


def get_drawing_type_confirmed() -> str | None:
    return st.session_state.get(_KEY_DRAWING_TYPE_CONFIRMED)


def get_drawing_type_predicted() -> dict[str, Any] | None:
    return st.session_state.get(_KEY_DRAWING_TYPE_PREDICTED)


def is_awaiting_type_confirmation() -> bool:
    return bool(st.session_state.get(_KEY_AWAITING_TYPE_CONFIRMATION, False))


def set_awaiting_type_confirmation(value: bool) -> None:
    st.session_state[_KEY_AWAITING_TYPE_CONFIRMATION] = value


def has_drawing_type() -> bool:
    """Return True if drawing type has been confirmed."""
    return st.session_state.get(_KEY_DRAWING_TYPE_CONFIRMED) is not None


# ---------------------------------------------------------------------------
# Drawing bounds (for Region Cropper)
# ---------------------------------------------------------------------------

def save_drawing_bounds(bounds: dict[str, Any]) -> None:
    st.session_state[_KEY_DRAWING_BOUNDS] = bounds


def get_drawing_bounds() -> dict[str, Any] | None:
    return st.session_state.get(_KEY_DRAWING_BOUNDS)


# ---------------------------------------------------------------------------
# Analysis / Checker results
# ---------------------------------------------------------------------------

def save_analysis_result(result: str) -> None:
    st.session_state[_KEY_ANALYSIS_RESULT] = result


def get_analysis_result() -> str | None:
    return st.session_state.get(_KEY_ANALYSIS_RESULT)


def save_dimension_result(result: str) -> None:
    st.session_state[_KEY_DIMENSION_RESULT] = result


def get_dimension_result() -> str | None:
    return st.session_state.get(_KEY_DIMENSION_RESULT)


def save_annotation_result(result: str) -> None:
    st.session_state[_KEY_ANNOTATION_RESULT] = result


def get_annotation_result() -> str | None:
    return st.session_state.get(_KEY_ANNOTATION_RESULT)


def save_standard_result(result: str) -> None:
    st.session_state[_KEY_STANDARD_RESULT] = result


def get_standard_result() -> str | None:
    return st.session_state.get(_KEY_STANDARD_RESULT)


# Self-Check result (Req 8.6)
def save_self_check_result(result: dict[str, Any]) -> None:
    """Persist the Self-Check node output (stats + verified errors)."""
    st.session_state[_KEY_SELF_CHECK_RESULT] = result


def get_self_check_result() -> dict[str, Any] | None:
    """Return the Self-Check result dict, or None if not yet run."""
    return st.session_state.get(_KEY_SELF_CHECK_RESULT)


def save_review_complete(value: bool = True) -> None:
    st.session_state[_KEY_REVIEW_COMPLETE] = value


def is_review_complete() -> bool:
    return bool(st.session_state.get(_KEY_REVIEW_COMPLETE, False))


# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

def add_message(role: str, content: str) -> None:
    """Append a chat message to the history."""
    history: list[dict] = st.session_state.get(_KEY_CHAT_HISTORY, [])
    history.append({"role": role, "content": content})
    st.session_state[_KEY_CHAT_HISTORY] = history


def get_chat_history() -> list[dict[str, str]]:
    """Return the full chat history as a list of role/content dicts."""
    return st.session_state.get(_KEY_CHAT_HISTORY, [])


def clear_results() -> None:
    """
    Clear analysis and checker results (useful when re-running checks after
    a new file upload or user feedback).
    """
    st.session_state[_KEY_ANALYSIS_RESULT] = None
    st.session_state[_KEY_DIMENSION_RESULT] = None
    st.session_state[_KEY_ANNOTATION_RESULT] = None
    st.session_state[_KEY_STANDARD_RESULT] = None
    st.session_state[_KEY_SELF_CHECK_RESULT] = None
    st.session_state[_KEY_REVIEW_COMPLETE] = False
    logger.info("Session: analysis, checker, and self-check results cleared.")
