"""
modules/orchestrator.py — LangGraph Orchestrator Module

Defines the full LangGraph state machine that coordinates the drawing analysis
pipeline:
  collect_info → analysis_node → review_node (dim → ann → std) → respond

Also handles:
  - User feedback triggering re-evaluation
  - RAG-based Q&A chat responses

Requirement: 11.1 – 11.5, 9.1 – 9.5
"""

import logging
from typing import Any, Literal, TypedDict

from langgraph.graph import StateGraph, END

from modules import session_db
from modules.rag_engine import RAGEngine
from modules.vlm_client import (
    build_analysis_prompt,
    build_checker_prompt,
    call_vlm_with_image,
    call_text_llm,
)
from modules.checkers.dimension_checker import run_dimension_check
from modules.checkers.annotation_checker import run_annotation_check
from modules.checkers.standard_checker import run_standard_check
import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph State Schema
# ---------------------------------------------------------------------------

class GraphState(TypedDict):
    """
    Shared state passed between all LangGraph nodes.
    All fields are optional; nodes update only what they produce.
    """
    # Input data
    user_message: str           # Latest user message
    drawing_type: str           # Confirmed drawing type
    image_base64: str           # PNG base64 of drawing
    dxf_json: dict[str, Any]   # Parsed DXF data

    # Node outputs
    analysis_result: str
    dimension_result: str
    annotation_result: str
    standard_result: str

    # Control flow
    needs_drawing_type: bool    # True → route to collect_info node
    is_feedback: bool           # True → re-run review with user feedback
    final_response: str         # Assembled response sent to chat


# ---------------------------------------------------------------------------
# Node: Collect Drawing Type Info
# ---------------------------------------------------------------------------

def node_collect_info(state: GraphState) -> dict[str, Any]:
    """
    Node triggered when drawing type is not yet confirmed.
    Returns a prompt asking the user for the drawing type.
    """
    logger.info("Node: collect_info — drawing type not confirmed yet.")
    response = config.UI_DRAWING_TYPE_ASK
    return {
        "final_response": response,
        "needs_drawing_type": True,
    }


# ---------------------------------------------------------------------------
# Node: Analysis (Tool 1)
# ---------------------------------------------------------------------------

def node_analysis(state: GraphState) -> dict[str, Any]:
    """
    Analysis Node (Tool 1): Sends the drawing image + DXF JSON to VLM
    for detailed description of all drawing components.
    """
    logger.info("Node: analysis — starting VLM analysis.")
    drawing_type = state.get("drawing_type", "Không xác định")
    dxf_json = state.get("dxf_json", {})
    image_base64 = state.get("image_base64", "")

    system_prompt, user_message = build_analysis_prompt(
        drawing_type=drawing_type,
        dxf_json_summary=dxf_json,
    )

    try:
        result = call_vlm_with_image(
            system_prompt=system_prompt,
            user_message=user_message,
            image_base64=image_base64,
        )
    except RuntimeError as exc:
        result = f"❌ Lỗi phân tích bản vẽ: {exc}"
        logger.error("Analysis node failed: %s", exc)

    # Persist to session
    session_db.save_analysis_result(result)

    return {"analysis_result": result}


# ---------------------------------------------------------------------------
# Node: Review (Tool 2) — runs 3 sub-tools sequentially
# ---------------------------------------------------------------------------

def node_review(state: GraphState, rag_engine: RAGEngine) -> dict[str, Any]:
    """
    Review Node (Tool 2): Runs Dimension → Annotation → Standard checkers
    sequentially and assembles a structured Vietnamese report.
    """
    logger.info("Node: review — starting sequential checker run.")
    drawing_type = state.get("drawing_type", "Không xác định")
    dxf_json = state.get("dxf_json", {})
    image_base64 = state.get("image_base64", "")
    analysis_result = state.get("analysis_result") or session_db.get_analysis_result() or ""

    # Sub-tool 2a: Dimension Checker
    logger.info("Review → running Dimension Checker")
    dim_result = run_dimension_check(
        image_base64=image_base64,
        drawing_type=drawing_type,
        dxf_json=dxf_json,
        analysis_result=analysis_result,
        rag_engine=rag_engine,
    )
    session_db.save_dimension_result(dim_result)

    # Sub-tool 2b: Annotation Checker
    logger.info("Review → running Annotation Checker")
    ann_result = run_annotation_check(
        image_base64=image_base64,
        drawing_type=drawing_type,
        dxf_json=dxf_json,
        analysis_result=analysis_result,
        rag_engine=rag_engine,
    )
    session_db.save_annotation_result(ann_result)

    # Sub-tool 2c: Standard Checker
    logger.info("Review → running Standard Checker")
    std_result = run_standard_check(
        image_base64=image_base64,
        drawing_type=drawing_type,
        dxf_json=dxf_json,
        analysis_result=analysis_result,
        rag_engine=rag_engine,
    )
    session_db.save_standard_result(std_result)
    session_db.save_review_complete(True)

    # Assemble structured report
    report = _assemble_report(dim_result, ann_result, std_result)

    return {
        "dimension_result": dim_result,
        "annotation_result": ann_result,
        "standard_result": std_result,
        "final_response": report,
    }


# ---------------------------------------------------------------------------
# Node: RAG Chat (for post-review Q&A)
# ---------------------------------------------------------------------------

def node_rag_chat(state: GraphState, rag_engine: RAGEngine) -> dict[str, Any]:
    """
    Handles free-form user questions about standards after the review is complete.
    Retrieves relevant RAG chunks and generates a grounded Vietnamese response.
    """
    user_message = state.get("user_message", "")
    logger.info("Node: rag_chat — answering question: %.80s", user_message)

    # Retrieve general standard context
    chunks = rag_engine.retrieve(query=user_message, checker_type=None)
    rag_context = rag_engine.format_context(chunks)

    system_prompt = config.SYSTEM_PROMPT_RAG_CHAT.format(rag_context=rag_context)

    # Include recent session context as additional context
    dim = session_db.get_dimension_result() or ""
    ann = session_db.get_annotation_result() or ""
    std = session_db.get_standard_result() or ""

    context_summary = ""
    if dim or ann or std:
        context_summary = (
            "\n\n**Kết quả kiểm tra đã có:**\n"
            f"- Kích thước: {dim[:300]}...\n"
            f"- Chú thích: {ann[:300]}...\n"
            f"- Tiêu chuẩn: {std[:300]}..."
        )

    enriched_message = user_message + context_summary

    try:
        response = call_text_llm(
            system_prompt=system_prompt,
            user_message=enriched_message,
        )
    except RuntimeError as exc:
        response = f"❌ Lỗi trả lời câu hỏi: {exc}"

    return {"final_response": response}


# ---------------------------------------------------------------------------
# Router function
# ---------------------------------------------------------------------------

def route_after_input(state: GraphState) -> Literal["collect_info", "analysis", "rag_chat"]:
    """
    Route the graph after receiving user input.
    - If no drawing type → collect_info
    - If review is complete and user is asking a question → rag_chat
    - Otherwise → analysis (which flows into review)
    """
    needs_type = state.get("needs_drawing_type", False)
    is_feedback = state.get("is_feedback", False)

    if needs_type:
        return "collect_info"

    # If review already complete and user is just asking, go to RAG chat
    if session_db.is_review_complete() and not is_feedback:
        return "rag_chat"

    return "analysis"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(rag_engine: RAGEngine) -> Any:
    """
    Build and compile the LangGraph state machine.

    The graph topology:
        START → router → collect_info → END
                       → analysis → review → END
                       → rag_chat → END

    Args:
        rag_engine: Initialized RAGEngine passed to nodes that need it.

    Returns:
        Compiled LangGraph CompiledGraph.
    """

    # Bind rag_engine into the closure for nodes that need it
    def _node_review(state: GraphState) -> dict[str, Any]:
        return node_review(state, rag_engine)

    def _node_rag_chat(state: GraphState) -> dict[str, Any]:
        return node_rag_chat(state, rag_engine)

    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("collect_info", node_collect_info)
    workflow.add_node("analysis", node_analysis)
    workflow.add_node("review", _node_review)
    workflow.add_node("rag_chat", _node_rag_chat)

    # Set entry point with conditional routing
    workflow.set_conditional_entry_point(
        route_after_input,
        {
            "collect_info": "collect_info",
            "analysis": "analysis",
            "rag_chat": "rag_chat",
        },
    )

    # Edges
    workflow.add_edge("collect_info", END)
    workflow.add_edge("analysis", "review")
    workflow.add_edge("review", END)
    workflow.add_edge("rag_chat", END)

    return workflow.compile()


# ---------------------------------------------------------------------------
# High-level run function (called from Streamlit UI)
# ---------------------------------------------------------------------------

def run_pipeline(
    user_message: str,
    rag_engine: RAGEngine,
    graph: Any | None = None,
) -> str:
    """
    Run the full LangGraph pipeline for a user message.

    Reads current session state to assemble the GraphState, runs the graph,
    and returns the final response string.

    Args:
        user_message: The user's latest message.
        rag_engine: Initialized RAGEngine.
        graph: Pre-compiled graph (optional; built fresh if None).

    Returns:
        Final response string to display in chat.
    """
    if graph is None:
        graph = build_graph(rag_engine)

    # Determine drawing type from session
    drawing_type = session_db.get_drawing_type_confirmed() or ""
    needs_drawing_type = not bool(drawing_type)

    # Check if this is a feedback / re-evaluation request
    is_feedback = (
        session_db.is_review_complete()
        and any(kw in user_message.lower() for kw in
                ["xem lại", "kiểm tra lại", "sai", "nhầm", "chỉnh", "điều chỉnh", "đánh giá lại"])
    )

    if is_feedback:
        # On feedback, clear previous results and re-run
        session_db.clear_results()

    # Assemble state
    initial_state: GraphState = {
        "user_message": user_message,
        "drawing_type": drawing_type,
        "image_base64": "",
        "dxf_json": session_db.get_dxf_json() or {},
        "analysis_result": session_db.get_analysis_result() or "",
        "dimension_result": session_db.get_dimension_result() or "",
        "annotation_result": session_db.get_annotation_result() or "",
        "standard_result": session_db.get_standard_result() or "",
        "needs_drawing_type": needs_drawing_type,
        "is_feedback": is_feedback,
        "final_response": "",
    }

    # Attach image (PNG bytes → base64)
    png_bytes = session_db.get_dxf_png_bytes()
    if png_bytes:
        import base64
        initial_state["image_base64"] = base64.b64encode(png_bytes).decode("utf-8")

    try:
        result_state = graph.invoke(initial_state)
        response = result_state.get("final_response", "")
        if not response:
            response = "⚠️ Không có phản hồi từ hệ thống. Vui lòng thử lại."
    except Exception as exc:
        logger.error("Graph execution failed: %s", exc)
        response = f"❌ Lỗi hệ thống: {exc}"

    return response


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _assemble_report(
    dim_result: str,
    ann_result: str,
    std_result: str,
) -> str:
    """Combine checker results into a structured Vietnamese report."""
    return (
        f"## {config.UI_REVIEW_HEADER}\n\n"
        f"---\n\n"
        f"### {config.UI_DIMENSION_HEADER}\n\n"
        f"{dim_result}\n\n"
        f"---\n\n"
        f"### {config.UI_ANNOTATION_HEADER}\n\n"
        f"{ann_result}\n\n"
        f"---\n\n"
        f"### {config.UI_STANDARD_HEADER}\n\n"
        f"{std_result}\n\n"
        f"---\n\n"
        "*Báo cáo được tạo tự động bởi AI Vision Drawing Checker. "
        "Kết quả mang tính tham khảo — vui lòng xác minh với tài liệu tiêu chuẩn gốc.*"
    )
