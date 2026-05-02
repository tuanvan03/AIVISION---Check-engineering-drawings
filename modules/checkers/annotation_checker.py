"""
modules/checkers/annotation_checker.py — Annotation Checker Sub-tool (2b)

Checks the presence and correctness of mandatory annotations:
title block, scale, material, general tolerance, projection symbol.
Uses RAG with ISO 7200 priority.

Requirement: 6.1 – 6.6
"""

import logging
from typing import Any

from modules.rag_engine import RAGEngine
from modules.vlm_client import build_checker_prompt, call_vlm_with_image

logger = logging.getLogger(__name__)


def run_annotation_check(
    image_base64: str,
    drawing_type: str,
    dxf_json: dict[str, Any],
    analysis_result: str,
    rag_engine: RAGEngine,
) -> str:
    """
    Run the Annotation Checker sub-tool.

    Steps:
    1. Retrieve ISO 7200 relevant context from RAG engine.
    2. Build system + user prompt with annotation criteria for drawing type.
    3. Send image + prompt to VLM.
    4. Return Vietnamese-language annotation check report.

    Args:
        image_base64: Base64 PNG of the drawing.
        drawing_type: Confirmed drawing type string.
        dxf_json: Full parsed DXF data.
        analysis_result: Output from Analysis Node.
        rag_engine: Initialized RAGEngine instance.

    Returns:
        Vietnamese-language annotation check report string.
    """
    logger.info("Running Annotation Checker for drawing type: %s", drawing_type)

    # --- Step 1: RAG context (ISO 7200 priority) ---
    rag_query = (
        f"Yêu cầu khung tên bản vẽ kỹ thuật {drawing_type}: "
        "tên bản vẽ, số hiệu, tỷ lệ, vật liệu, dung sai chung, "
        "ký hiệu chiếu góc theo ISO 7200"
    )
    chunks = rag_engine.retrieve(query=rag_query, checker_type="annotation")
    rag_context = rag_engine.format_context(chunks)

    # --- Step 2: Build prompt ---
    system_prompt, user_message = build_checker_prompt(
        checker_type="annotation",
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
        logger.error("Annotation checker VLM call failed: %s", exc)
        result = f"❌ Lỗi khi kiểm tra chú thích: {exc}"

    logger.info("Annotation check completed. Result length: %d chars", len(result))
    return result
