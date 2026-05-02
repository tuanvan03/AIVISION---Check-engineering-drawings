"""
modules/checkers/dimension_checker.py — Dimension Checker Sub-tool (2a)

Checks the completeness, consistency, and formatting of dimensions in the drawing
using the VLM + RAG retrieved ISO 129 context.

Returns a Structured_Checker_Result dict (with analysis_summary + error list)
alongside a plain-text Vietnamese report for backward compatibility.

Requirement: 5.1 – 5.6, Self-Check Req 1.1 – 1.7, 9.1 – 9.7
"""

import json
import logging
from typing import Any

from modules.rag_engine import RAGEngine
from modules.vlm_client import build_checker_prompt, call_vlm_with_image

logger = logging.getLogger(__name__)


def run_dimension_check(
    image_base64: str,
    drawing_type: str,
    dxf_json: dict[str, Any],
    analysis_result: str,
    rag_engine: RAGEngine,
) -> tuple[dict[str, Any], str]:
    """
    Run the Dimension Checker sub-tool.

    Steps:
    1. Retrieve ISO 129 relevant context from RAG engine.
    2. Build system + user prompt with drawing type criteria.
    3. Send image + prompt to VLM requesting structured JSON output.
    4. Parse response into Structured_Checker_Result (with analysis_summary);
       fallback to plain text if VLM returns non-JSON (Req 1.4).
    5. Return (structured_result, plain_text_report).

    Args:
        image_base64: Base64 PNG of the full drawing (or cropped region).
        drawing_type: Confirmed drawing type string.
        dxf_json: Full parsed DXF data.
        analysis_result: Output from Analysis Node for context.
        rag_engine: Initialized RAGEngine instance.

    Returns:
        Tuple of:
          - structured_result: dict with keys "analysis_summary" and "errors"
          - plain_text: Vietnamese error report string
    """
    logger.info("Running Dimension Checker for drawing type: %s", drawing_type)

    # --- Step 1: Retrieve RAG context (ISO 129 priority) ---
    rag_query = (
        f"Quy tắc ghi kích thước bản vẽ kỹ thuật {drawing_type} "
        "theo ISO 129, yêu cầu đầy đủ kích thước, nhất quán và định dạng"
    )
    chunks = rag_engine.retrieve(query=rag_query, checker_type="dimension")
    rag_context = rag_engine.format_context(chunks)

    # --- Step 2: Build prompt ---
    system_prompt, user_message = build_checker_prompt(
        checker_type="dimension",
        drawing_type=drawing_type,
        rag_context=rag_context,
        dxf_json=dxf_json,
        analysis_result=analysis_result,
    )

    # --- Step 3: Call VLM ---
    try:
        raw_result = call_vlm_with_image(
            system_prompt=system_prompt,
            user_message=user_message,
            image_base64=image_base64,
        )
    except RuntimeError as exc:
        logger.error("Dimension checker VLM call failed: %s", exc)
        error_msg = f"❌ Lỗi khi kiểm tra kích thước: {exc}"
        return {"detailed_analysis": [], "errors": []}, error_msg

    # --- Step 4: Parse structured JSON or fallback ---
    structured, plain_text = _parse_checker_response(raw_result, checker_prefix="dim")

    logger.info(
        "Dimension check completed. Errors: %d, steps: %d, text length: %d chars",
        len(structured.get("errors", [])),
        len(structured.get("detailed_analysis", [])),
        len(plain_text),
    )
    return structured, plain_text


# ---------------------------------------------------------------------------
# Shared JSON parser — used by all three checkers
# ---------------------------------------------------------------------------

def _parse_checker_response(
    raw: str,
    checker_prefix: str = "err",
) -> tuple[dict[str, Any], str]:
    """
    Parse a VLM checker response into (structured_result, plain_text).

    Tries to extract a JSON object with keys "analysis_summary" and "errors".
    If that fails, wraps the plain text in a fallback structure (Req 1.4 – 1.6, 9.4).

    The structured_result has the shape:
        {
            "analysis_summary": str,   # Req 9.1: VLM narrative of what was checked
            "errors": [
                {
                    "error_id": str,
                    "severity": "high" | "medium" | "low",
                    "description": str,
                    "entity_handles": list[str],
                    "iso_reference": str,
                    "confirmed": bool   # True by default; self-check may flip to False
                },
                ...
            ]
        }

    Args:
        raw: Raw VLM response string.
        checker_prefix: Short prefix for auto-generated error_ids.

    Returns:
        Tuple of (structured_result dict, plain_text str).
    """
    # Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(cleaned)
        errors = data.get("errors", [])
        detailed_analysis = data.get("detailed_analysis", [])  # list of {step, result, detail}

        # Normalize each error entry to ensure required fields
        normalized = []
        for idx, err in enumerate(errors):
            normalized.append({
                "error_id": err.get("error_id", f"{checker_prefix}_{idx + 1:03d}"),
                "severity": err.get("severity", "medium"),
                "description": err.get("description", str(err)),
                "entity_handles": err.get("entity_handles", []),
                "iso_reference": err.get("iso_reference", ""),
                "confirmed": True,  # Initial state; self-check may set to False
            })

        structured = {
            "detailed_analysis": detailed_analysis,
            "errors": normalized,
        }
        plain_text = _structured_to_plain_text(detailed_analysis, normalized)
        return structured, plain_text

    except (json.JSONDecodeError, KeyError, TypeError):
        # Req 9.4: fallback — use full plain text as detailed_analysis summary step, errors empty
        logger.debug(
            "Checker response is not structured JSON (prefix=%s); using fallback.", checker_prefix
        )
        # Wrap the raw response as a single step so _section_text can render it
        fallback_step = {
            "step": "Kết quả kiểm tra",
            "result": "warning",
            "detail": raw,
        }
        structured = {
            "detailed_analysis": [fallback_step],
            "errors": [],
        }
        return structured, raw


def _errors_to_plain_text(errors: list[dict[str, Any]]) -> str:
    """
    Convert a list of structured error dicts to a formatted Vietnamese error list.
    Used when regenerating the error section after self-check filtering (Req 9.7).
    """
    if not errors:
        return "✅ Không phát hiện lỗi."

    lines = []
    severity_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    for err in errors:
        icon = severity_icons.get(err.get("severity", "medium"), "⚪")
        lines.append(
            f"{icon} **[{err.get('error_id', '?')}]** "
            f"({err.get('severity', 'medium').upper()}) — "
            f"{err.get('description', '')}"
        )
        if err.get("iso_reference"):
            lines.append(f"   📌 *{err['iso_reference']}*")
        if err.get("entity_handles"):
            handles_str = ", ".join(err["entity_handles"])
            lines.append(f"   🔧 Entities: `{handles_str}`")
        lines.append("")  # Blank line between errors

    return "\n".join(lines)


def _structured_to_plain_text(
    detailed_analysis: list[dict],
    errors: list[dict[str, Any]],
) -> str:
    """
    Combine detailed_analysis steps and error list into a full plain-text section.

    Format (Req 9.5):
        **Phân Tích Chi Tiết:**
        ✔️ Bước 1: ...
        ❌ Bước 2: ...

        **Các lỗi phát hiện:**
        ...

    Args:
        detailed_analysis: List of {step, result, detail} dicts from VLM.
        errors: List of normalized error dicts.

    Returns:
        Formatted plain-text string for display in the report section.
    """
    parts = []

    # Render step-by-step analysis (Req 9.5)
    if detailed_analysis:
        parts.append("**Phân Tích Chi Tiết:**\n")
        result_icons = {"pass": "✅", "fail": "❌", "warning": "⚠️"}
        for step_item in detailed_analysis:
            icon = result_icons.get(step_item.get("result", ""), "⚪")
            step_name = step_item.get("step", "")
            detail = step_item.get("detail", "")
            parts.append(f"{icon} **{step_name}**")
            if detail:
                parts.append(f"   {detail}")
            parts.append("")  # Blank line between steps for readability


    # Then show errors (Req 9.5)
    if errors:
        parts.append("**Các lỗi phát hiện:**\n")
        parts.append(_errors_to_plain_text(errors))
    elif detailed_analysis:
        parts.append("✅ Không phát hiện lỗi trong phần này.")

    return "\n".join(parts) if parts else "✅ Không phát hiện lỗi."


def _filter_confirmed_structured(struct: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy of a structured result with only confirmed=True errors.
    Preserves detailed_analysis unchanged (Req 6.3).
    """
    return {
        "detailed_analysis": struct.get("detailed_analysis", []),
        "errors": [e for e in struct.get("errors", []) if e.get("confirmed", True)],
    }


def _section_text(struct: dict[str, Any], plain_fallback: str = "") -> str:
    """
    Build the display text for a single checker section (Sections 1–3) in the final report.

    Shows:
    1. Step-by-step detailed_analysis (if available).
    2. ALL errors from the first check pass (Req 6.2, 6.3) — NOT filtered by confirmed.
       False positives removed by self-check are only hidden in Section 4.
    3. Falls back to plain_fallback if struct has no structured data (Req 9.6).

    Args:
        struct: Structured checker result dict (with detailed_analysis + errors).
        plain_fallback: Original plain-text output from the checker (used if struct empty).

    Returns:
        Formatted section string for embedding in the report.
    """
    detailed_analysis = struct.get("detailed_analysis", [])
    # Req 6.2 / 6.3: show ALL errors from first pass in sections 1–3
    all_errors = struct.get("errors", [])

    # Req 9.6: fall back to plain text if no structured data available
    if not detailed_analysis and not all_errors:
        return plain_fallback or "✅ Không phát hiện lỗi."

    return _structured_to_plain_text(detailed_analysis, all_errors)


def _section_text_confirmed(struct: dict[str, Any], plain_fallback: str = "") -> str:
    """
    Like _section_text but shows ONLY confirmed=True errors.
    Used in Section 4 (self-check) to display the remaining errors after filtering.

    Args:
        struct: Structured checker result dict.
        plain_fallback: Fallback text when struct is empty.

    Returns:
        Formatted section string with only confirmed errors.
    """
    detailed_analysis = struct.get("detailed_analysis", [])
    confirmed_errors = [e for e in struct.get("errors", []) if e.get("confirmed", True)]

    if not detailed_analysis and not struct.get("errors"):
        return plain_fallback or "✅ Không phát hiện lỗi."

    # For section 4 we only show the error list (no step analysis repeated)
    if not confirmed_errors:
        return "✅ Không còn lỗi nào sau khi xác minh."
    return "**Các lỗi còn lại sau self-check:**\n\n" + _errors_to_plain_text(confirmed_errors)

