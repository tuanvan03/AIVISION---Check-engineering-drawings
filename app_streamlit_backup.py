"""
app.py — Streamlit Entry Point for AI Vision Drawing Checker

Layout: 3/4 Drawing Viewer | 1/4 Chat Interface

Flow:
1. Initialize session state and RAG engine on startup
2. User uploads DXF → parse → render → predict drawing type
3. Chat interface collects drawing type confirmation
4. LangGraph pipeline runs Analysis → Review (3 checkers) → Report
5. User can ask follow-up questions answered via RAG

Requirement: 1.1 – 12.4
"""

import logging
import tempfile
from pathlib import Path

import streamlit as st

# Configure logging before importing project modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Project modules
import config
from modules import session_db
from modules.dxf_parser import parse_dxf
from modules.svg_renderer import dxf_to_svg, dxf_to_png_bytes, get_drawing_bounds
from modules.drawing_type_predictor import predict_drawing_type, format_suggestion_message
from modules.rag_engine import get_rag_engine
from modules.orchestrator import build_graph, run_pipeline
from ui.drawing_viewer import render_drawing_viewer
from ui.chat_interface import render_chat_interface


# ---------------------------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=config.UI_TITLE,
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": (
            "**AI Vision Drawing Checker** — Kiểm tra bản vẽ kỹ thuật tự động "
            "bằng AI theo tiêu chuẩn ISO/ASME."
        ),
    },
)

# ---------------------------------------------------------------------------
# Custom CSS for premium look
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* App header */
    .app-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.2rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .app-header h1 {
        color: white;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
    }
    .app-header p {
        color: #90caf9;
        font-size: 0.9rem;
        margin: 0;
    }

    /* Panel styling */
    .drawing-panel {
        background: #fafafa;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        min-height: 80vh;
    }
    .chat-panel {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        min-height: 80vh;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .status-ready { background: #e8f5e9; color: #2e7d32; }
    .status-pending { background: #fff8e1; color: #f57f17; }
    .status-error { background: #ffebee; color: #c62828; }

    /* Hide default Streamlit elements */
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Startup: initialize session and RAG engine
# ---------------------------------------------------------------------------

def _init_rag_engine():
    """
    Initialize (or return cached) RAG engine.
    Stored in st.session_state to avoid re-indexing on every rerun.
    """
    if "rag_engine" not in st.session_state:
        with st.spinner("⏳ Đang khởi tạo cơ sở tri thức tiêu chuẩn ISO..."):
            engine = get_rag_engine()
            st.session_state["rag_engine"] = engine
            logger.info("RAG engine initialized and cached in session.")
    return st.session_state["rag_engine"]


def _init_graph(rag_engine):
    """Build (or return cached) LangGraph compiled graph."""
    if "langgraph" not in st.session_state:
        st.session_state["langgraph"] = build_graph(rag_engine)
    return st.session_state["langgraph"]


# ---------------------------------------------------------------------------
# File upload handler
# ---------------------------------------------------------------------------

def handle_file_uploaded(file_bytes: bytes, filename: str) -> None:
    """
    Process an uploaded DXF file:
    1. Write to a temp file
    2. Parse with dxf_parser
    3. Render SVG and PNG
    4. Extract drawing bounds
    5. Run drawing type predictor
    6. Store everything in session_db
    7. Trigger drawing type suggestion in chat
    """
    # Write to temporary file (ezdxf needs a real file path)
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        # --- Parse DXF ---
        with st.spinner("🔍 Đang đọc file DXF..."):
            try:
                dxf_json = parse_dxf(tmp_path)
            except (ValueError, FileNotFoundError) as exc:
                st.error(config.UI_UPLOAD_ERROR_PARSE.format(error=str(exc)))
                logger.error("DXF parse failed: %s", exc)
                return

        # --- Render SVG ---
        with st.spinner("🖼️ Đang render bản vẽ..."):
            try:
                svg_content = dxf_to_svg(tmp_path)
                png_bytes = dxf_to_png_bytes(tmp_path, dpi=config.SVG_DEFAULT_DPI)
                bounds = get_drawing_bounds(tmp_path)
            except ValueError as exc:
                st.error(config.UI_UPLOAD_ERROR_PARSE.format(error=str(exc)))
                logger.error("SVG render failed: %s", exc)
                return

        # --- Save to session ---
        session_db.save_dxf_data(
            filename=filename,
            dxf_json=dxf_json,
            png_bytes=png_bytes,
            svg_content=svg_content,
        )
        if bounds:
            session_db.save_drawing_bounds(bounds)

        # --- Clear previous results ---
        session_db.clear_results()

        # --- Predict drawing type ---
        with st.spinner("🧠 Đang nhận dạng loại bản vẽ..."):
            prediction = predict_drawing_type(dxf_json)
            session_db.save_drawing_type_predicted(
                drawing_type=prediction.drawing_type,
                reasoning=prediction.reasoning,
                confidence=prediction.confidence,
            )

        # --- Post system message to chat ---
        welcome = (
            f"✅ {config.UI_UPLOAD_SUCCESS.format(filename=filename)}\n\n"
            f"Đã nhận: **{len(dxf_json.get('entities', []))}** entities, "
            f"**{len(dxf_json.get('dimensions', []))}** kích thước, "
            f"**{len(dxf_json.get('layers', []))}** layers.\n\n"
        )
        suggestion = format_suggestion_message(prediction)
        session_db.add_message("assistant", welcome + suggestion)

        # Set awaiting confirmation flag
        session_db.set_awaiting_type_confirmation(True)

        logger.info("File uploaded and processed: %s", filename)

    finally:
        # Clean up temp file
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Chat message handler
# ---------------------------------------------------------------------------

def handle_user_message(user_message: str) -> str:
    """
    Route a user chat message through the LangGraph pipeline.
    Returns the assistant's response.
    """
    rag_engine = st.session_state.get("rag_engine")
    graph = st.session_state.get("langgraph")

    if rag_engine is None or graph is None:
        return "❌ Hệ thống chưa sẵn sàng. Vui lòng tải lại trang."

    return run_pipeline(
        user_message=user_message,
        rag_engine=rag_engine,
        graph=graph,
    )


# ---------------------------------------------------------------------------
# Main application layout
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Main Streamlit app entry point.
    Initializes state, renders the header, then splits into 2 columns:
      - col_drawing (3/4): Drawing Viewer
      - col_chat (1/4): Chat Interface
    """
    # Initialize session state
    session_db.init_session()

    # Initialize RAG engine and LangGraph (cached between reruns)
    rag_engine = _init_rag_engine()
    _init_graph(rag_engine)

    # --- App Header ---
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <h1>📐 {config.UI_TITLE}</h1>
                <p>{config.UI_SUBTITLE} · Tiêu chuẩn ISO 128 · ISO 129 · ISO 1101 · ISO 7200</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Two-column layout: 3/4 drawing | 1/4 chat ---
    col_drawing, col_chat = st.columns([3, 1], gap="medium")

    with col_drawing:
        with st.container():
            render_drawing_viewer(
                svg_content=session_db.get_dxf_svg(),
                dxf_json=session_db.get_dxf_json(),
                filename=session_db.get_dxf_filename(),
            )

    with col_chat:
        with st.container():
            render_chat_interface(
                on_user_message=handle_user_message,
                on_file_uploaded=handle_file_uploaded,
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
