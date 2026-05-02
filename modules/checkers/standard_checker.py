"""
modules/checkers/standard_checker.py — Standard Checker Sub-tool (2c)

Checks compliance with international standards (ISO 128, ISO 1101):
GD&T symbols, surface finish marks, weld symbols, line conventions.
Uses RAG with ISO 1101 + ISO 128 priority.

Returns a Structured_Checker_Result dict with keys:
  - "detailed_analysis": list of {step, result, detail} dicts (step-by-step check results)
  - "errors": list of confirmed error dicts with entity_handles, severity, iso_reference

Requirement: 7.1 – 7.6, Self-Check Req 1.3, 1.6, 9.1 – 9.7
"""

import logging
from typing import Any

from modules.rag_engine import RAGEngine
from modules.vlm_client import build_checker_prompt, call_vlm_with_image
from modules.checkers.dimension_checker import _parse_checker_response

logger = logging.getLogger(__name__)


def run_standard_check(
    image_base64: str,
    drawing_type: str,
    dxf_json: dict[str, Any],
    analysis_result: str,
    rag_engine: RAGEngine,
) -> tuple[dict[str, Any], str]:
    """
    Run the Standard Checker sub-tool.

    Steps:
    1. Retrieve ISO 128 + ISO 1101 relevant context from RAG engine.
    2. Build system + user prompt with standard criteria for drawing type.
    3. Send image + prompt to VLM requesting structured JSON output with
       detailed_analysis (step-by-step) + errors list.
    4. Parse response into Structured_Checker_Result; fallback to a single
       warning step if VLM returns non-JSON (Req 1.6).

    Args:
        image_base64: Base64 PNG of the drawing.
        drawing_type: Confirmed drawing type string.
        dxf_json: Full parsed DXF data.
        analysis_result: Output from Analysis Node.
        rag_engine: Initialized RAGEngine instance.

    Returns:
        Tuple of:
          - structured_result: dict with keys "detailed_analysis" and "errors"
          - plain_text: Vietnamese standards compliance report string
    """
    logger.info("Running Standard Checker for drawing type: %s", drawing_type)

    # --- Step 1: RAG context (ISO 1101 + ISO 128 priority) ---
    rag_query = (
        f"Tiêu chuẩn ISO cho bản vẽ kỹ thuật {drawing_type}: "
        "ký hiệu GD&T, dung sai hình học ISO 1101, "
        "quy ước loại đường nét ISO 128, ký hiệu hoàn thiện bề mặt"
    )
    chunks = rag_engine.retrieve(query=rag_query, checker_type="standard")
    rag_context = rag_engine.format_context(chunks)

    # --- Step 2: Build prompt ---
    system_prompt, user_message = build_checker_prompt(
        checker_type="standard",
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
        logger.error("Standard checker VLM call failed: %s", exc)
        error_msg = f"❌ Lỗi khi kiểm tra tiêu chuẩn: {exc}"
        return {"detailed_analysis": [], "errors": []}, error_msg

    # --- Step 4: Parse structured JSON or fallback (Req 1.6) ---
    structured, plain_text = _parse_checker_response(raw_result, checker_prefix="std")

    logger.info(
        "Standard check completed. Errors: %d, steps: %d, text length: %d chars",
        len(structured.get("errors", [])),
        len(structured.get("detailed_analysis", [])),
        len(plain_text),
    )
    return structured, plain_text
