"""
ui/chat_interface.py — Chat Interface UI Component

Renders the right-side chat panel (1/4 width) with:
  - Chat history display
  - User input box
  - File uploader
  - Drawing type confirmation UI

Requirement: 2.1, 2.3, 2.7, 2.8, 2.9, 8.2
"""

import logging
from typing import Callable

import streamlit as st

import config
from modules import session_db

logger = logging.getLogger(__name__)


def render_chat_interface(
    on_user_message: Callable[[str], str],
    on_file_uploaded: Callable[[bytes, str], None],
) -> None:
    """
    Render the full chat interface panel.

    Args:
        on_user_message: Callback that takes (user_message: str) → (assistant_reply: str).
                         Called when user submits a message.
        on_file_uploaded: Callback that takes (file_bytes: bytes, filename: str).
                          Called when user uploads a DXF file.
    """
    # --- File uploader at top of chat panel ---
    _render_file_uploader(on_file_uploaded)

    st.markdown("---")

    # --- Chat history ---
    _render_chat_history()

    # --- User input ---
    _render_input_box(on_user_message)


def _render_file_uploader(on_file_uploaded: Callable) -> None:
    """File upload widget with format validation."""
    uploaded_file = st.file_uploader(
        config.UI_UPLOAD_LABEL,
        type=["dxf"],
        help=config.UI_UPLOAD_HELP,
        key="dxf_file_uploader",
    )

    if uploaded_file is not None:
        filename = uploaded_file.name

        # Only process if this is a new file (avoid re-processing on every rerun)
        if filename != session_db.get_dxf_filename():
            if not filename.lower().endswith(".dxf"):
                st.error(config.UI_UPLOAD_ERROR_FORMAT)
                return

            with st.spinner("⏳ Đang đọc và render bản vẽ..."):
                file_bytes = uploaded_file.read()
                on_file_uploaded(file_bytes, filename)


def _render_chat_history() -> None:
    """Render all chat messages in the history."""
    history = session_db.get_chat_history()

    # Chat container with max height and scroll
    chat_container = st.container(height=500)
    with chat_container:
        if not history:
            st.markdown(
                "<div style='color: #888; text-align: center; margin-top: 40px;'>"
                "💬 Bắt đầu hội thoại bên dưới"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            for msg in history:
                role = msg["role"]
                content = msg["content"]

                if role == "user":
                    with st.chat_message("user"):
                        st.markdown(content)
                elif role == "assistant":
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(content)
                # Skip "system" messages — they are internal


def _render_input_box(on_user_message: Callable) -> None:
    """Render the chat input box and handle submission."""
    has_dxf = session_db.has_dxf_loaded()

    # Show placeholder hint if no DXF loaded
    placeholder = config.UI_CHAT_PLACEHOLDER if has_dxf else "Tải lên file DXF trước..."
    disabled = not has_dxf

    # Drawing type quick-confirm buttons (shown when awaiting confirmation)
    if session_db.is_awaiting_type_confirmation():
        _render_type_confirmation_buttons()
        st.markdown("---")

    user_input = st.chat_input(
        placeholder=placeholder,
        disabled=disabled,
        key="chat_input",
    )

    if user_input:
        # Check if no DXF is loaded — guard
        if not has_dxf:
            st.warning(config.UI_CHAT_WAITING)
            return

        # Record user message
        session_db.add_message("user", user_input)

        # Handle drawing type response if awaiting confirmation
        if session_db.is_awaiting_type_confirmation():
            _handle_drawing_type_input(user_input)

        # Call orchestrator and display response
        with st.spinner(config.UI_CHAT_ANALYZING):
            try:
                reply = on_user_message(user_input)
            except Exception as exc:  # noqa: BLE001
                reply = config.UI_CHAT_ERROR.format(error=str(exc))
                logger.error("Chat callback error: %s", exc)

        session_db.add_message("assistant", reply)
        st.rerun()


def _render_type_confirmation_buttons() -> None:
    """
    Show clickable buttons for common drawing types for quick confirmation.
    Displayed when the system has made a prediction and is awaiting user response.
    """
    st.markdown("**📌 Xác nhận loại bản vẽ:**")
    predicted = session_db.get_drawing_type_predicted()
    predicted_type = predicted["type"] if predicted else None

    # Show predicted type highlighted, others as secondary buttons
    cols = st.columns(2)
    for idx, dt in enumerate(config.DRAWING_TYPES):
        col = cols[idx % 2]
        is_predicted = (dt == predicted_type)
        label = f"✅ {dt}" if is_predicted else dt
        if col.button(label, key=f"type_btn_{idx}", use_container_width=True):
            session_db.save_drawing_type_confirmed(dt)
            session_db.add_message(
                "user",
                f"Xác nhận: loại bản vẽ là **{dt}**",
            )
            st.rerun()


def _handle_drawing_type_input(user_input: str) -> None:
    """
    Parse free-text user input to extract a drawing type confirmation.
    If a known drawing type keyword is found, auto-confirm it.
    """
    user_lower = user_input.lower()
    for dt in config.DRAWING_TYPES:
        dt_lower = dt.lower()
        # Check both the English and Vietnamese parts
        parts = dt.replace("(", "").replace(")", "").split()
        if any(p.lower() in user_lower for p in parts if len(p) > 3):
            session_db.save_drawing_type_confirmed(dt)
            logger.info("Drawing type auto-confirmed from text: %s", dt)
            return

    # If user says "đúng", "phải", "yes", "ok", "correct" → confirm predicted type
    confirm_keywords = ["đúng", "phải", "yes", "ok", "correct", "ừ", "vâng", "ok rồi"]
    if any(kw in user_lower for kw in confirm_keywords):
        predicted = session_db.get_drawing_type_predicted()
        if predicted:
            session_db.save_drawing_type_confirmed(predicted["type"])
            logger.info("Predicted drawing type confirmed by user: %s", predicted["type"])
