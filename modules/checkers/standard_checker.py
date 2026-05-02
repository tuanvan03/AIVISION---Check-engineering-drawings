"""
modules/checkers/standard_checker.py — Standard Checker Sub-tool (2c)

Checks compliance with international standards (ISO 128, ISO 1101):
GD&T symbols, surface finish marks, weld symbols, line conventions.
Uses RAG with ISO 1101 + ISO 128 priority.

Requirement: 7.1 – 7.6
"""

import logging
from typing import Any

from modules.rag_engine import RAGEngine
from modules.vlm_client import build_checker_prompt, call_vlm_with_image

logger = logging.getLogger(__name__)


def run_standard_check(
    image_base64: str,
    drawing_type: str,
    dxf_json: dict[str, Any],
    analysis_result: str,
    rag_engine: RAGEngine,
) -> str:
    """
    Run the Standard Checker sub-tool.

    Steps:
    1. Retrieve ISO 128 + ISO 1101 relevant context from RAG engine.
    2. Build system + user prompt with standard criteria for drawing type.
    3. Send image + prompt to VLM.
    4. Return Vietnamese-language standards compliance report.

    Args:
        image_base64: Base64 PNG of the drawing.
        drawing_type: Confirmed drawing type string.
        dxf_json: Full parsed DXF data.
        analysis_result: Output from Analysis Node.
        rag_engine: Initialized RAGEngine instance.

    Returns:
        Vietnamese-language standards compliance report string.
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
        result = call_vlm_with_image(
            system_prompt=system_prompt,
            user_message=user_message,
            image_base64=image_base64,
        )
    except RuntimeError as exc:
        logger.error("Standard checker VLM call failed: %s", exc)
        result = f"❌ Lỗi khi kiểm tra tiêu chuẩn: {exc}"

    logger.info("Standard check completed. Result length: %d chars", len(result))
    return result
