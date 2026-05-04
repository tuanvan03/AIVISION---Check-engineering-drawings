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
import contextvars
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session Backend System (Bridge)
# ---------------------------------------------------------------------------

@runtime_checkable
class SessionBackend(Protocol):
    """Protocol for session storage backends."""
    def __getitem__(self, key: str) -> Any: ...
    def __setitem__(self, key: str, value: Any) -> None: ...
    def __contains__(self, key: str) -> bool: ...
    def get(self, key: str, default: Any = None) -> Any: ...

class StreamlitBackend:
    """Backend that uses Streamlit's session_state."""
    def __init__(self, session_state: Any):
        self._state = session_state
    def __getitem__(self, key: str) -> Any: return self._state[key]
    def __setitem__(self, key: str, value: Any) -> None: self._state[key] = value
    def __contains__(self, key: str) -> bool: return key in self._state
    def get(self, key: str, default: Any = None) -> Any: return self._state.get(key, default)

class DictBackend:
    """Backend that uses a plain Python dictionary (for FastAPI/Background tasks)."""
    def __init__(self):
        self._data: dict[str, Any] = {}
        # Auto-initialize defaults like init_session would
        self._init_defaults()
    
    def _init_defaults(self):
        self._data.update({
            KEY_DXF_FILENAME: None,
            KEY_DXF_JSON: None,
            KEY_DXF_PNG_BYTES: None,
            KEY_DXF_SVG: None,
            KEY_DRAWING_TYPE_PREDICTED: None,
            KEY_DRAWING_TYPE_CONFIRMED: None,
            KEY_DRAWING_BOUNDS: None,
            KEY_ANALYSIS_RESULT: None,
            KEY_DIMENSION_RESULT: None,
            KEY_ANNOTATION_RESULT: None,
            KEY_STANDARD_RESULT: None,
            KEY_SELF_CHECK_RESULT: None,
            KEY_CHAT_HISTORY: [],
            KEY_AWAITING_TYPE_CONFIRMATION: False,
            KEY_REVIEW_COMPLETE: False,
        })

    def __getitem__(self, key: str) -> Any: return self._data[key]
    def __setitem__(self, key: str, value: Any) -> None: self._data[key] = value
    def __contains__(self, key: str) -> bool: return key in self._data
    def get(self, key: str, default: Any = None) -> Any: return self._data.get(key, default)
    def to_dict(self) -> dict[str, Any]: return self._data.copy()

_backend_var: contextvars.ContextVar[Optional[SessionBackend]] = contextvars.ContextVar("session_backend", default=None)

def set_backend(backend: Optional[SessionBackend]) -> None:
    """Set the active session backend for the current context."""
    _backend_var.set(backend)

def _get_backend() -> SessionBackend:
    """Retrieve the active backend or auto-detect Streamlit."""
    backend = _backend_var.get()
    if backend is None:
        try:
            import streamlit as st
            # Try to access session_state to trigger the 'No Streamlit context' error if not in ST
            _ = st.session_state
            backend = StreamlitBackend(st.session_state)
            set_backend(backend)
        except (ImportError, Exception):
            raise RuntimeError("No session backend configured and Streamlit not available.")
    return backend


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

KEY_DXF_FILENAME = "db_dxf_filename"
KEY_DXF_JSON = "db_dxf_json"
KEY_DXF_PNG_BYTES = "db_dxf_png_bytes"
KEY_DXF_SVG = "db_dxf_svg"
KEY_DRAWING_TYPE_PREDICTED = "db_drawing_type_predicted"
KEY_DRAWING_TYPE_CONFIRMED = "db_drawing_type_confirmed"
KEY_DRAWING_BOUNDS = "db_drawing_bounds"
KEY_ANALYSIS_RESULT = "db_analysis_result"
KEY_DIMENSION_RESULT = "db_dimension_result"
KEY_ANNOTATION_RESULT = "db_annotation_result"
KEY_STANDARD_RESULT = "db_standard_result"
KEY_SELF_CHECK_RESULT = "db_self_check_result"   # Self-Check node output
KEY_CHAT_HISTORY = "db_chat_history"
KEY_AWAITING_TYPE_CONFIRMATION = "db_awaiting_type_confirmation"
KEY_REVIEW_COMPLETE = "db_review_complete"


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def init_session() -> None:
    """
    Initialize all session keys with default values if they don't exist yet.
    """
    backend = _get_backend()
    defaults: dict[str, Any] = {
        KEY_DXF_FILENAME: None,
        KEY_DXF_JSON: None,
        KEY_DXF_PNG_BYTES: None,
        KEY_DXF_SVG: None,
        KEY_DRAWING_TYPE_PREDICTED: None,
        KEY_DRAWING_TYPE_CONFIRMED: None,
        KEY_DRAWING_BOUNDS: None,
        KEY_ANALYSIS_RESULT: None,
        KEY_DIMENSION_RESULT: None,
        KEY_ANNOTATION_RESULT: None,
        KEY_STANDARD_RESULT: None,
        KEY_SELF_CHECK_RESULT: None,
        KEY_CHAT_HISTORY: [],
        KEY_AWAITING_TYPE_CONFIRMATION: False,
        KEY_REVIEW_COMPLETE: False,
    }
    for key, default in defaults.items():
        if key not in backend:
            backend[key] = default


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
    backend = _get_backend()
    backend[KEY_DXF_FILENAME] = filename
    backend[KEY_DXF_JSON] = dxf_json
    backend[KEY_DXF_PNG_BYTES] = png_bytes
    backend[KEY_DXF_SVG] = svg_content
    logger.info("Session: DXF data saved for file '%s'", filename)


def get_dxf_filename() -> str | None:
    return _get_backend().get(KEY_DXF_FILENAME)


def get_dxf_json() -> dict[str, Any] | None:
    return _get_backend().get(KEY_DXF_JSON)


def get_dxf_png_bytes() -> bytes | None:
    return _get_backend().get(KEY_DXF_PNG_BYTES)


def get_dxf_svg() -> str | None:
    return _get_backend().get(KEY_DXF_SVG)


def has_dxf_loaded() -> bool:
    """Return True if a DXF file has been successfully loaded."""
    return _get_backend().get(KEY_DXF_JSON) is not None


# ---------------------------------------------------------------------------
# Drawing type
# ---------------------------------------------------------------------------

def save_drawing_type_predicted(drawing_type: str, reasoning: str, confidence: float) -> None:
    """Save the predictor's output (before user confirmation)."""
    _get_backend()[KEY_DRAWING_TYPE_PREDICTED] = {
        "type": drawing_type,
        "reasoning": reasoning,
        "confidence": confidence,
    }


def save_drawing_type_confirmed(drawing_type: str) -> None:
    """Save the user-confirmed drawing type."""
    backend = _get_backend()
    backend[KEY_DRAWING_TYPE_CONFIRMED] = drawing_type
    backend[KEY_AWAITING_TYPE_CONFIRMATION] = False
    logger.info("Session: Drawing type confirmed as '%s'", drawing_type)


def get_drawing_type_confirmed() -> str | None:
    return _get_backend().get(KEY_DRAWING_TYPE_CONFIRMED)


def get_drawing_type_predicted() -> dict[str, Any] | None:
    return _get_backend().get(KEY_DRAWING_TYPE_PREDICTED)


def is_awaiting_type_confirmation() -> bool:
    return bool(_get_backend().get(KEY_AWAITING_TYPE_CONFIRMATION, False))


def set_awaiting_type_confirmation(value: bool) -> None:
    _get_backend()[KEY_AWAITING_TYPE_CONFIRMATION] = value


def has_drawing_type() -> bool:
    """Return True if drawing type has been confirmed."""
    return _get_backend().get(KEY_DRAWING_TYPE_CONFIRMED) is not None


# ---------------------------------------------------------------------------
# Drawing bounds (for Region Cropper)
# ---------------------------------------------------------------------------

def save_drawing_bounds(bounds: dict[str, Any]) -> None:
    _get_backend()[KEY_DRAWING_BOUNDS] = bounds


def get_drawing_bounds() -> dict[str, Any] | None:
    return _get_backend().get(KEY_DRAWING_BOUNDS)


# ---------------------------------------------------------------------------
# Analysis / Checker results
# ---------------------------------------------------------------------------

def save_analysis_result(result: str) -> None:
    _get_backend()[KEY_ANALYSIS_RESULT] = result


def get_analysis_result() -> str | None:
    return _get_backend().get(KEY_ANALYSIS_RESULT)


def save_dimension_result(result: str) -> None:
    _get_backend()[KEY_DIMENSION_RESULT] = result


def get_dimension_result() -> str | None:
    return _get_backend().get(KEY_DIMENSION_RESULT)


def save_annotation_result(result: str) -> None:
    _get_backend()[KEY_ANNOTATION_RESULT] = result


def get_annotation_result() -> str | None:
    return _get_backend().get(KEY_ANNOTATION_RESULT)


def save_standard_result(result: str) -> None:
    _get_backend()[KEY_STANDARD_RESULT] = result


def get_standard_result() -> str | None:
    return _get_backend().get(KEY_STANDARD_RESULT)


# Self-Check result (Req 8.6)
def save_self_check_result(result: dict[str, Any]) -> None:
    """Persist the Self-Check node output (stats + verified errors)."""
    _get_backend()[KEY_SELF_CHECK_RESULT] = result


def get_self_check_result() -> dict[str, Any] | None:
    """Return the Self-Check result dict, or None if not yet run."""
    return _get_backend().get(KEY_SELF_CHECK_RESULT)


def save_review_complete(value: bool = True) -> None:
    _get_backend()[KEY_REVIEW_COMPLETE] = value


def is_review_complete() -> bool:
    return bool(_get_backend().get(KEY_REVIEW_COMPLETE, False))


# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

def add_message(role: str, content: str) -> None:
    """Append a chat message to the history."""
    backend = _get_backend()
    history: list[dict] = backend.get(KEY_CHAT_HISTORY, [])
    history.append({"role": role, "content": content})
    backend[KEY_CHAT_HISTORY] = history


def get_chat_history() -> list[dict[str, str]]:
    """Return the full chat history as a list of role/content dicts."""
    return _get_backend().get(KEY_CHAT_HISTORY, [])


def clear_results() -> None:
    """
    Clear analysis and checker results (useful when re-running checks after
    a new file upload or user feedback).
    """
    backend = _get_backend()
    backend[KEY_ANALYSIS_RESULT] = None
    backend[KEY_DIMENSION_RESULT] = None
    backend[KEY_ANNOTATION_RESULT] = None
    backend[KEY_STANDARD_RESULT] = None
    backend[KEY_SELF_CHECK_RESULT] = None
    backend[KEY_REVIEW_COMPLETE] = False
    logger.info("Session: analysis, checker, and self-check results cleared.")
