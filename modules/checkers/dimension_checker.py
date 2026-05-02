"""
modules/checkers/dimension_checker.py — Dimension Checker Sub-tool (2a)

Checks the completeness, consistency, and formatting of dimensions in the drawing
using the VLM + RAG retrieved ISO 129 context.

Requirement: 5.1 – 5.6
"""

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
) -> str:
    """
    Run the Dimension Checker sub-tool.

    Steps:
    1. Retrieve ISO 129 relevant context from RAG engine.
    2. Build system + user prompt with drawing type criteria.
    3. Send image + prompt to VLM.
    4. Return Vietnamese-language error report.

    Args:
        image_base64: Base64 PNG of the full drawing (or cropped region).
        drawing_type: Confirmed drawing type string.
        dxf_json: Full parsed DXF data.
        analysis_result: Output from Analysis Node for context.
        rag_engine: Initialized RAGEngine instance.

    Returns:
        Vietnamese-language dimension check report string.
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
        result = call_vlm_with_image(
            system_prompt=system_prompt,
            user_message=user_message,
            image_base64=image_base64,
        )
    except RuntimeError as exc:
        logger.error("Dimension checker VLM call failed: %s", exc)
        result = f"❌ Lỗi khi kiểm tra kích thước: {exc}"

    logger.info("Dimension check completed. Result length: %d chars", len(result))
    return result
