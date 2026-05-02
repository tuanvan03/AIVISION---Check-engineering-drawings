"""
modules/orchestrator.py — LangGraph Orchestrator Module

Defines the full LangGraph state machine that coordinates the drawing analysis
pipeline:
  collect_info → analysis → review → self_check → END

Also handles:
  - User feedback triggering re-evaluation
  - RAG-based Q&A chat responses

Requirement: 11.1 – 11.5, 9.1 – 9.5
Self-Check Req: 3.1 – 3.11, 6.1 – 6.6, 8.1 – 8.6
"""

import base64
import logging
import time
from typing import Any, Literal, TypedDict

from langgraph.graph import StateGraph, END

from modules import session_db
from modules.rag_engine import RAGEngine
from modules.region_cropper import (
    DXFRegion,
    get_union_bbox,
    crop_region,
    make_drawing_bounds,
    png_bytes_to_base64,
)
from modules.vlm_client import (
    build_analysis_prompt,
    call_vlm_with_image,
    call_text_llm,
    call_vlm_for_self_check,
)
from modules.checkers.dimension_checker import run_dimension_check
from modules.checkers.annotation_checker import run_annotation_check
from modules.checkers.standard_checker import run_standard_check
import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph State Schema  (Req 8.1 – 8.5)
# ---------------------------------------------------------------------------

class GraphState(TypedDict):
    """
    Shared state passed between all LangGraph nodes.
    All fields are optional; nodes update only what they produce.
    """
    # Input data
    user_message: str               # Latest user message
    drawing_type: str               # Confirmed drawing type
    image_base64: str               # PNG base64 of drawing
    dxf_json: dict[str, Any]        # Parsed DXF data

    # Node outputs — plain text (Req 8.5: backward-compatible)
    analysis_result: str
    dimension_result: str
    annotation_result: str
    standard_result: str

    # Structured checker results (Req 8.2 – 8.4)
    structured_dim_result: dict[str, Any]
    structured_ann_result: dict[str, Any]
    structured_std_result: dict[str, Any]

    # Self-check output (Req 8.1)
    self_check_result: dict[str, Any]

    # Control flow
    needs_drawing_type: bool        # True → route to collect_info node
    is_feedback: bool               # True → re-run review with user feedback
    final_response: str             # Assembled response sent to chat


# ---------------------------------------------------------------------------
# Node: Collect Drawing Type Info
# ---------------------------------------------------------------------------

def node_collect_info(state: GraphState) -> dict[str, Any]:
    """
    Node triggered when drawing type is not yet confirmed.
    Returns a prompt asking the user for the drawing type.
    """
    logger.info("Node: collect_info — drawing type not confirmed yet.")
    return {
        "final_response": config.UI_DRAWING_TYPE_ASK,
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
    sequentially.

    Each checker now returns (structured_result, plain_text).
    Both are stored in the graph state (Req 8.5).
    """
    logger.info("Node: review — starting sequential checker run.")
    drawing_type = state.get("drawing_type", "Không xác định")
    dxf_json = state.get("dxf_json", {})
    image_base64 = state.get("image_base64", "")
    analysis_result = state.get("analysis_result") or session_db.get_analysis_result() or ""

    # Sub-tool 2a: Dimension Checker
    logger.info("Review → running Dimension Checker")
    struct_dim, dim_plain = run_dimension_check(
        image_base64=image_base64,
        drawing_type=drawing_type,
        dxf_json=dxf_json,
        analysis_result=analysis_result,
        rag_engine=rag_engine,
    )
    session_db.save_dimension_result(dim_plain)

    # Sub-tool 2b: Annotation Checker
    logger.info("Review → running Annotation Checker")
    struct_ann, ann_plain = run_annotation_check(
        image_base64=image_base64,
        drawing_type=drawing_type,
        dxf_json=dxf_json,
        analysis_result=analysis_result,
        rag_engine=rag_engine,
    )
    session_db.save_annotation_result(ann_plain)

    # Sub-tool 2c: Standard Checker
    logger.info("Review → running Standard Checker")
    struct_std, std_plain = run_standard_check(
        image_base64=image_base64,
        drawing_type=drawing_type,
        dxf_json=dxf_json,
        analysis_result=analysis_result,
        rag_engine=rag_engine,
    )
    session_db.save_standard_result(std_plain)
    session_db.save_review_complete(True)

    return {
        "dimension_result": dim_plain,
        "annotation_result": ann_plain,
        "standard_result": std_plain,
        "structured_dim_result": struct_dim,
        "structured_ann_result": struct_ann,
        "structured_std_result": struct_std,
        # final_response is assembled by node_self_check (always runs after review)
    }


# ---------------------------------------------------------------------------
# Node: Self-Check (Req 3.1 – 3.11)
# ---------------------------------------------------------------------------

def node_self_check(state: GraphState) -> dict[str, Any]:
    """
    Self-Check Node: Verifies each high/medium severity error by cropping the
    drawing image to the error's bounding box and asking VLM to confirm.

    Pipeline:
    1. Skip if drawing is simple (entity count < COMPLEXITY_THRESHOLD).  (Req 3.3)
    2. Skip if PNG bytes are unavailable.                                 (Req 7.3)
    3. For each high/medium error (up to SELF_CHECK_MAX_ERRORS):         (Req 3.4, 5.1)
       a. Resolve entity_handles → union BBox.                           (Req 3.5)
       b. Crop image at BBox.                                            (Req 3.7)
       c. Call VLM to confirm.                                           (Req 3.8)
       d. Mark confirmed/false-positive.                                 (Req 3.9, 3.10)
    4. Assemble final report with self-check summary.                    (Req 6.1 – 6.6)
    5. Persist results to session.                                       (Req 3.11)
    """
    logger.info("Node: self_check — starting self-check verification.")
    start_ts = time.time()

    dxf_json = state.get("dxf_json", {})
    entity_count = len(dxf_json.get("entities", []))

    struct_dim = state.get("structured_dim_result") or {"errors": []}
    struct_ann = state.get("structured_ann_result") or {"errors": []}
    struct_std = state.get("structured_std_result") or {"errors": []}

    dim_plain = state.get("dimension_result", "")
    ann_plain = state.get("annotation_result", "")
    std_plain = state.get("standard_result", "")

    # Req 3.3 / 6.4: Skip self-check for simple drawings
    if entity_count < config.COMPLEXITY_THRESHOLD:
        logger.info(
            "Skipping self-check: entity count %d < COMPLEXITY_THRESHOLD %d",
            entity_count, config.COMPLEXITY_THRESHOLD,
        )
        report = _assemble_report(
            struct_dim=struct_dim,
            struct_ann=struct_ann,
            struct_std=struct_std,
            dim_plain=dim_plain,
            ann_plain=ann_plain,
            std_plain=std_plain,
            self_check_skipped=True,
        )
        return {"final_response": report, "self_check_result": {"skipped": True}}

    # Req 7.3: Need PNG bytes (Issue #3 fix: render report instead of returning "")
    png_bytes = session_db.get_dxf_png_bytes()
    if not png_bytes:
        logger.warning("Self-check skipped: PNG bytes not in session.")
        report = _assemble_report(
            struct_dim=struct_dim, struct_ann=struct_ann, struct_std=struct_std,
            dim_plain=dim_plain, ann_plain=ann_plain, std_plain=std_plain,
            self_check_skipped=True,
        )
        return {"final_response": report, "self_check_result": {"skipped": True, "reason": "no_png"}}

    # Req 7.4: Build DrawingBounds
    try:
        bounds_dict = session_db.get_drawing_bounds()
        if not bounds_dict:
            raise ValueError("Drawing bounds not in session.")
        drawing_bounds = make_drawing_bounds(png_bytes, bounds_dict)
    except Exception as exc:
        logger.warning("Self-check skipped: cannot build DrawingBounds: %s", exc)
        report = _assemble_report(
            struct_dim=struct_dim, struct_ann=struct_ann, struct_std=struct_std,
            dim_plain=dim_plain, ann_plain=ann_plain, std_plain=std_plain,
            self_check_skipped=True,
        )
        return {"final_response": report, "self_check_result": {"skipped": True, "reason": "no_bounds"}}

    # Collect all errors from all three checkers with their checker type labels
    all_errors: list[tuple[str, dict[str, Any]]] = [
        ("dimension", err) for err in struct_dim.get("errors", [])
    ] + [
        ("annotation", err) for err in struct_ann.get("errors", [])
    ] + [
        ("standard", err) for err in struct_std.get("errors", [])
    ]

    total_errors = len(all_errors)

    # Req 3.4: Only self-check high/medium severity
    eligible = [
        (ctype, err) for ctype, err in all_errors
        if err.get("severity") in ("high", "medium")
    ]

    # Req 5.4: Prioritize high then medium, cap at SELF_CHECK_MAX_ERRORS
    eligible_sorted = sorted(
        eligible,
        key=lambda x: (0 if x[1].get("severity") == "high" else 1),
    )[:config.SELF_CHECK_MAX_ERRORS]

    # Track verified_count: errors actually sent to VLM (had valid bbox + crop) (Req 6.6)
    checked_count = 0    # verified_count — actual VLM calls made
    eligible_count = len(eligible_sorted)  # eligible_count — passed severity filter
    filtered_count = 0

    for checker_type, err in eligible_sorted:
        handles = err.get("entity_handles", [])

        # Req 3.6: Skip if all handles are missing — count as eligible but not verified
        bbox = get_union_bbox(handles, dxf_json) if handles else None
        if bbox is None:
            logger.debug(
                "Self-check skipping error %s: no valid bbox from handles %s",
                err.get("error_id"), handles,
            )
            continue  # Keep original result

        # Req 3.7: Crop region
        try:
            cropped_bytes = crop_region(png_bytes, bbox, drawing_bounds)
        except Exception as exc:
            logger.warning(
                "Self-check crop failed for error %s: %s — keeping error.",
                err.get("error_id"), exc,
            )
            continue  # Req 7.1: keep error on crop failure

        # Req 3.8: Call VLM for self-check
        try:
            crop_b64 = png_bytes_to_base64(cropped_bytes)
            confirmed = call_vlm_for_self_check(
                image_base64=crop_b64,
                error_description=err.get("description", ""),
                iso_reference=err.get("iso_reference", ""),
                checker_type=checker_type,
            )
        except RuntimeError as exc:
            logger.warning(
                "Self-check VLM error for %s: %s — keeping error.", err.get("error_id"), exc
            )
            confirmed = True  # Req 7.2: keep on VLM failure

        checked_count += 1  # Only count errors that reached VLM (Req 6.6)

        # Req 3.9, 3.10: Mark error
        err["confirmed"] = confirmed
        if not confirmed:
            filtered_count += 1
            logger.debug(  # Req 6.10
                "Self-check filtered false positive: id=%s type=%s desc=%.80s",
                err.get("error_id"), checker_type, err.get("description", ""),
            )

    elapsed = time.time() - start_ts

    # Req 7.6: Log summary
    logger.info(
        "Self-check complete: total=%d, eligible=%d, verified=%d, filtered=%d, time=%.1fs",
        total_errors, eligible_count, checked_count, filtered_count, elapsed,
    )

    self_check_stats = {
        "skipped": False,
        "total_errors": total_errors,
        "eligible_count": eligible_count,
        "verified_count": checked_count,   # Req 6.6: actual VLM calls
        "filtered_count": filtered_count,
        "elapsed_seconds": round(elapsed, 1),
    }

    # Req 3.11: Persist to session
    session_db.save_self_check_result(self_check_stats)

    # Req 6.1 – 6.4: Pass structured results (with confirmed flags) to report assembler
    # Each section shows analysis_summary + only confirmed errors (Req 6.2, 6.3, 6.4)
    report = _assemble_report(
        struct_dim=struct_dim,
        struct_ann=struct_ann,
        struct_std=struct_std,
        dim_plain=dim_plain,
        ann_plain=ann_plain,
        std_plain=std_plain,
        self_check_stats=self_check_stats,
    )

    return {
        "final_response": report,
        "self_check_result": self_check_stats,
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

    chunks = rag_engine.retrieve(query=user_message, checker_type=None)
    rag_context = rag_engine.format_context(chunks)
    system_prompt = config.SYSTEM_PROMPT_RAG_CHAT.format(rag_context=rag_context)

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

    try:
        response = call_text_llm(
            system_prompt=system_prompt,
            user_message=user_message + context_summary,
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
    - Otherwise → analysis (which flows into review → self_check)
    """
    if state.get("needs_drawing_type", False):
        return "collect_info"

    if session_db.is_review_complete() and not state.get("is_feedback", False):
        return "rag_chat"

    return "analysis"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(rag_engine: RAGEngine) -> Any:
    """
    Build and compile the LangGraph state machine.

    Graph topology:
        START → router → collect_info → END
                       → analysis → review → self_check → END
                       → rag_chat → END

    Args:
        rag_engine: Initialized RAGEngine passed to nodes that need it.

    Returns:
        Compiled LangGraph CompiledGraph.
    """

    def _node_review(state: GraphState) -> dict[str, Any]:
        return node_review(state, rag_engine)

    def _node_rag_chat(state: GraphState) -> dict[str, Any]:
        return node_rag_chat(state, rag_engine)

    workflow = StateGraph(GraphState)

    # Register nodes
    workflow.add_node("collect_info", node_collect_info)
    workflow.add_node("analysis", node_analysis)
    workflow.add_node("review", _node_review)
    workflow.add_node("self_check", node_self_check)   # NEW
    workflow.add_node("rag_chat", _node_rag_chat)

    # Conditional entry point
    workflow.set_conditional_entry_point(
        route_after_input,
        {
            "collect_info": "collect_info",
            "analysis": "analysis",
            "rag_chat": "rag_chat",
        },
    )

    # Edges — review now flows into self_check before END (Req 3.1)
    workflow.add_edge("collect_info", END)
    workflow.add_edge("analysis", "review")
    workflow.add_edge("review", "self_check")    # CHANGED
    workflow.add_edge("self_check", END)         # NEW
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

    drawing_type = session_db.get_drawing_type_confirmed() or ""
    needs_drawing_type = not bool(drawing_type)

    # Detect feedback / re-evaluation requests
    is_feedback = (
        session_db.is_review_complete()
        and any(kw in user_message.lower() for kw in
                ["xem lại", "kiểm tra lại", "sai", "nhầm", "chỉnh", "điều chỉnh", "đánh giá lại"])
    )

    if is_feedback:
        session_db.clear_results()

    # Assemble initial state
    initial_state: GraphState = {
        "user_message": user_message,
        "drawing_type": drawing_type,
        "image_base64": "",
        "dxf_json": session_db.get_dxf_json() or {},
        "analysis_result": session_db.get_analysis_result() or "",
        "dimension_result": session_db.get_dimension_result() or "",
        "annotation_result": session_db.get_annotation_result() or "",
        "standard_result": session_db.get_standard_result() or "",
        "structured_dim_result": {},
        "structured_ann_result": {},
        "structured_std_result": {},
        "self_check_result": {},
        "needs_drawing_type": needs_drawing_type,
        "is_feedback": is_feedback,
        "final_response": "",
    }

    # Attach image
    png_bytes = session_db.get_dxf_png_bytes()
    if png_bytes:
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

def _filter_confirmed(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return only errors where confirmed is True (or not set — treated as True).
    Used by self-check to remove false positives from the report.
    """
    return [e for e in errors if e.get("confirmed", True)]


def _assemble_report(
    struct_dim: dict[str, Any],
    struct_ann: dict[str, Any],
    struct_std: dict[str, Any],
    dim_plain: str = "",
    ann_plain: str = "",
    std_plain: str = "",
    self_check_stats: dict[str, Any] | None = None,
    self_check_skipped: bool = False,
) -> str:
    """
    Assemble the final Vietnamese report in 5 sections (Req 6.1):

    Section 1–3: Checker results — detailed_analysis steps + ALL errors from first pass.
    Section 4: Self-check summary table + confirmed errors only (Issue #2 fix).
    Section 5: Conclusion & suggestions.

    Req 6.2–6.3: Sections 1–3 show VLM detailed_analysis + ALL first-pass errors.
    Req 6.4: Section 4 shows only confirmed=True errors after self-check filtering.
    Req 6.7: Sections 1–3 + 5 only (no Section 4) when self-check is skipped.
    """
    # Import section helpers from dimension_checker (shared by all 3 checkers)
    from modules.checkers.dimension_checker import _section_text, _section_text_confirmed

    # --- Sections 1–3: ALL errors from first pass (Req 6.2, 6.3) ---
    dim_section = _section_text(struct_dim, dim_plain)
    ann_section = _section_text(struct_ann, ann_plain)
    std_section = _section_text(struct_std, std_plain)

    # --- Collect confirmed errors for conclusion stats and section 4 ---
    all_confirmed = (
        _filter_confirmed(struct_dim.get("errors", []))
        + _filter_confirmed(struct_ann.get("errors", []))
        + _filter_confirmed(struct_std.get("errors", []))
    )

    # --- Section 4: Self-Check summary + confirmed errors list (Req 6.2, 6.5) ---
    self_check_section = ""
    if self_check_stats and not self_check_stats.get("skipped") and not self_check_skipped:
        total = self_check_stats.get("total_errors", 0)
        eligible = self_check_stats.get("eligible_count", 0)
        verified = self_check_stats.get("verified_count", 0)  # Req 6.6
        filtered = self_check_stats.get("filtered_count", 0)
        remaining = total - filtered
        elapsed = self_check_stats.get("elapsed_seconds", 0)

        # Issue #5 fix: add note when verified < eligible (some errors had no valid bbox)
        skip_note = ""
        if verified < eligible:
            skip_note = (
                f"\n> ⚠️ *{eligible - verified} lỗi đủ điều kiện nhưng không thể xác minh "
                "(không tìm thấy entity handle trong DXF — giữ nguyên kết quả lần 1).*\n"
            )

        # Issue #2 fix: render confirmed error list per checker
        confirmed_errors_text = ""
        for label, struct in [
            (config.UI_DIMENSION_HEADER, struct_dim),
            (config.UI_ANNOTATION_HEADER, struct_ann),
            (config.UI_STANDARD_HEADER, struct_std),
        ]:
            section_confirmed = _section_text_confirmed(struct)
            confirmed_errors_text += f"**{label}:**\n{section_confirmed}\n\n"

        self_check_section = (
            f"### {config.UI_SELF_CHECK_HEADER}\n\n"
            f"| Tổng lỗi | Đủ điều kiện | Đã xác minh (có bbox) | Loại bỏ | Còn lại | Thời gian |\n"
            f"|:-:|:-:|:-:|:-:|:-:|:-:|\n"
            f"| {total} | {eligible} | {verified} | {filtered} | {remaining} | {elapsed}s |\n"
            f"{skip_note}\n"
            f"{confirmed_errors_text}"
            "---\n\n"
        )

    # --- Section 5: Conclusion & Suggestions (Req 6.8, 10.1–10.4) ---
    conclusion_section = _build_conclusion(all_confirmed, struct_dim, struct_ann, struct_std)

    # --- Assemble final report ---
    parts = [
        f"## {config.UI_REVIEW_HEADER}\n",
        f"### {config.UI_DIMENSION_HEADER}\n\n{dim_section}\n\n---\n",
        f"### {config.UI_ANNOTATION_HEADER}\n\n{ann_section}\n\n---\n",
        f"### {config.UI_STANDARD_HEADER}\n\n{std_section}\n\n---\n",
    ]
    if self_check_section:
        parts.append(self_check_section)
    parts.append(conclusion_section)

    return "\n".join(parts)


def _build_conclusion(
    all_confirmed: list[dict[str, Any]],
    struct_dim: dict[str, Any],
    struct_ann: dict[str, Any],
    struct_std: dict[str, Any],
) -> str:
    """
    Build Section 5: Kết Luận & Gợi Ý (Req 10.1–10.4).

    Counts errors by severity, picks a quality verdict, and suggests
    follow-up questions based on the ISO standards referenced in the errors.
    """
    # Severity counts (Req 10.2)
    high = sum(1 for e in all_confirmed if e.get("severity") == "high")
    medium = sum(1 for e in all_confirmed if e.get("severity") == "medium")
    low = sum(1 for e in all_confirmed if e.get("severity") == "low")
    total = len(all_confirmed)

    # Quality verdict (Req 10.3)
    if high == 0:
        verdict = config.UI_CONCLUSION_GOOD
    elif high <= 2:
        verdict = config.UI_CONCLUSION_NEEDS_FIX.format(high_count=high)
    else:
        verdict = config.UI_CONCLUSION_CRITICAL.format(high_count=high)

    # Severity table
    severity_table = (
        f"| Mức độ | Số lỗi |\n"
        f"|--------|--------|\n"
        f"| 🔴 Nghiêm trọng (High) | {high} |\n"
        f"| 🟡 Trung bình (Medium) | {medium} |\n"
        f"| 🟢 Nhẹ (Low) | {low} |\n"
        f"| **Tổng cộng** | **{total}** |\n"
    )

    # Suggested follow-up questions based on ISO standards found in errors (Req 10.4)
    iso_refs: set[str] = set()
    for e in all_confirmed:
        ref = e.get("iso_reference", "")
        # Extract the standard name (e.g. "ISO 129-1:2018")
        if "ISO" in ref:
            parts = ref.split("]")[0].lstrip("[")
            iso_refs.add(parts.strip())

    suggestions = []
    if any("129" in r for r in iso_refs):
        suggestions.append("> 💬 *ISO 129-1 quy định chi tiết cách ghi dung sai kích thước như thế nào?*")
    if any("7200" in r for r in iso_refs):
        suggestions.append("> 💬 *Theo ISO 7200, những trường nào bắt buộc phải có trong khung tên?*")
    if any("1101" in r for r in iso_refs):
        suggestions.append("> 💬 *ISO 1101 quy định ký hiệu độ phẳng và độ thẳng như thế nào?*")
    if any("128" in r for r in iso_refs):
        suggestions.append("> 💬 *Chiều dày đường nét theo ISO 128-2 được quy định ra sao?*")
    if not suggestions:
        suggestions = [
            "> 💬 *Các tiêu chuẩn ISO nào áp dụng cho loại bản vẽ này?*",
            "> 💬 *Làm thế nào để ghi dung sai chung đúng theo ISO?*",
        ]

    suggestion_text = "\n".join(suggestions[:3])  # max 3 suggestions

    return (
        f"### {config.UI_CONCLUSION_HEADER}\n\n"
        f"{verdict}\n\n"
        f"{severity_table}\n"
        f"**Gợi ý câu hỏi tiếp theo:**\n\n"
        f"{suggestion_text}\n\n"
        "---\n\n"
        "*Báo cáo được tạo tự động bởi AI Vision Drawing Checker. "
        "Kết quả mang tính tham khảo — vui lòng xác minh với tài liệu tiêu chuẩn gốc.*"
    )
