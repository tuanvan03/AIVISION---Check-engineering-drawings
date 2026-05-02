"""
modules/vlm_client.py — VLM Client Module

Provides a thin wrapper around the OpenAI API for Vision Language Model calls.
Handles image encoding (base64), prompt assembly, and response parsing.

Requirement: 3.5, 3.6
"""

import base64
import io
import json
import logging
from typing import Any

from openai import OpenAI

import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Client initialization
# ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    """Return a configured OpenAI client. Uses API key from config."""
    return OpenAI(api_key=config.OPENAI_API_KEY)


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def encode_svg_to_png_base64(svg_content: str, dpi: int = 150) -> str:
    """
    Convert an SVG string to a base64-encoded PNG string.

    Uses cairosvg for high-quality vector-to-raster conversion.

    Args:
        svg_content: SVG markup as a string.
        dpi: Resolution for rasterization.

    Returns:
        Base64-encoded PNG string.
    """
    try:
        import cairosvg
        png_bytes = cairosvg.svg2png(
            bytestring=svg_content.encode("utf-8"),
            dpi=dpi,
        )
        return base64.b64encode(png_bytes).decode("utf-8")
    except ImportError:
        logger.warning("cairosvg not available; falling back to SVG inline data URL")
        # Fallback: inline SVG as base64 (browsers and some VLMs accept this)
        svg_b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        return svg_b64


def encode_png_bytes_to_base64(png_bytes: bytes) -> str:
    """Encode raw PNG bytes to a base64 string."""
    return base64.b64encode(png_bytes).decode("utf-8")


# ---------------------------------------------------------------------------
# Core VLM call
# ---------------------------------------------------------------------------

def call_vlm_with_image(
    system_prompt: str,
    user_message: str,
    image_base64: str,
    image_media_type: str = "image/png",
    max_tokens: int = config.VLM_MAX_TOKENS,
    temperature: float = config.VLM_TEMPERATURE,
    model: str = config.VLM_MODEL,
) -> str:
    """
    Send a vision request to OpenAI VLM with a base64-encoded image.

    Args:
        system_prompt: System-level instruction for the model.
        user_message: User-turn message (can include JSON data as text).
        image_base64: Base64-encoded image (PNG or JPEG).
        image_media_type: MIME type of the image.
        max_tokens: Maximum response length in tokens.
        temperature: Sampling temperature (0 = deterministic).
        model: OpenAI model identifier.

    Returns:
        Model response text.

    Raises:
        RuntimeError: On API failure.
    """
    client = _get_client()

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_media_type};base64,{image_base64}",
                        "detail": "high",
                    },
                },
                {"type": "text", "text": user_message},
            ],
        },
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content or ""
            
            # Catch AI safety refusal
            refusal_signatures = [
                "I'm sorry, I can't assist with that",
                "I am sorry, I can't assist with that",
                "I cannot assist with that"
            ]
            if any(sig in content for sig in refusal_signatures):
                logger.warning("VLM refusal detected (attempt %d/%d). Retrying...", attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    continue
                else:
                    raise RuntimeError("VLM liên tục từ chối xử lý yêu cầu (Safety filter block).")

            logger.info(
                "VLM response: %d chars, model=%s, tokens=%d",
                len(content),
                model,
                response.usage.total_tokens if response.usage else 0,
            )
            return content
        except Exception as exc:
            if attempt < max_retries - 1:
                logger.warning("VLM API error (attempt %d/%d): %s. Retrying...", attempt + 1, max_retries, exc)
                continue
            logger.error("VLM API call failed: %s", exc)
            raise RuntimeError(f"Lỗi gọi VLM API: {exc}") from exc
    
    return ""


def call_text_llm(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2048,
    temperature: float = config.VLM_TEMPERATURE,
    model: str = config.TEXT_MODEL,
) -> str:
    """
    Send a text-only request to the LLM (no image).

    Used for tasks like RAG Q&A, drawing type prediction fallback, etc.

    Args:
        system_prompt: System instruction.
        user_message: User message.
        max_tokens: Maximum response tokens.
        temperature: Sampling temperature.
        model: Model to use.

    Returns:
        Model response text.
    """
    client = _get_client()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content or ""
            
            # Catch AI safety refusal
            refusal_signatures = [
                "I'm sorry, I can't assist with that",
                "I am sorry, I can't assist with that",
                "I cannot assist with that"
            ]
            if any(sig in content for sig in refusal_signatures):
                logger.warning("Text LLM refusal detected (attempt %d/%d). Retrying...", attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    continue
                else:
                    raise RuntimeError("LLM liên tục từ chối xử lý yêu cầu (Safety filter block).")

            logger.info("Text LLM response: %d chars, model=%s", len(content), model)
            return content
        except Exception as exc:
            if attempt < max_retries - 1:
                logger.warning("Text LLM API error (attempt %d/%d): %s. Retrying...", attempt + 1, max_retries, exc)
                continue
            logger.error("Text LLM API call failed: %s", exc)
            raise RuntimeError(f"Lỗi gọi LLM API: {exc}") from exc
            
    return ""


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_analysis_prompt(
    drawing_type: str,
    dxf_json_summary: dict[str, Any],
) -> tuple[str, str]:
    """
    Build (system_prompt, user_message) for the Analysis Node.

    Returns:
        Tuple of (system_prompt, user_message).
    """
    system_prompt = config.SYSTEM_PROMPT_ANALYSIS.format(drawing_type=drawing_type)

    # Summarize key DXF data to include in the user message (avoid too-large JSON)
    summary = {
        "entity_count": len(dxf_json_summary.get("entities", [])),
        "dimension_count": len(dxf_json_summary.get("dimensions", [])),
        "text_count": len(dxf_json_summary.get("texts", [])),
        "layer_names": [l["name"] for l in dxf_json_summary.get("layers", [])],
        "block_names": [b["name"] for b in dxf_json_summary.get("blocks", [])],
        "dimensions_sample": dxf_json_summary.get("dimensions", [])[:20],
        "texts_sample": dxf_json_summary.get("texts", [])[:30],
        "metadata": dxf_json_summary.get("metadata", {}),
        "extents": dxf_json_summary.get("extents", {}),
        "title_block": dxf_json_summary.get("title_block", {}),
    }

    user_message = (
        f"Loại bản vẽ: {drawing_type}\n\n"
        f"Dữ liệu JSON từ ezdxf:\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```\n\n"
        "Hãy phân tích chi tiết bản vẽ kỹ thuật trong ảnh trên và mô tả tất cả các thành phần."
    )

    return system_prompt, user_message


def build_checker_prompt(
    checker_type: str,
    drawing_type: str,
    rag_context: str,
    dxf_json: dict[str, Any],
    analysis_result: str,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_message) for a checker node.

    Args:
        checker_type: "dimension", "annotation", or "standard".
        drawing_type: Confirmed drawing type string.
        rag_context: Formatted RAG context string.
        dxf_json: Full DXF JSON.
        analysis_result: Output from Analysis Node.

    Returns:
        Tuple of (system_prompt, user_message).
    """
    # Select the right prompt template and criteria
    if checker_type == "dimension":
        criteria = config.DRAWING_TYPE_DIMENSION_CRITERIA.get(
            drawing_type, config.DRAWING_TYPE_DIMENSION_CRITERIA["default"]
        )
        system_prompt = config.SYSTEM_PROMPT_DIMENSION_CHECKER.format(
            drawing_type=drawing_type,
            drawing_type_criteria=criteria,
            rag_context=rag_context,
        )
    elif checker_type == "annotation":
        criteria = config.DRAWING_TYPE_ANNOTATION_CRITERIA.get(
            drawing_type, config.DRAWING_TYPE_ANNOTATION_CRITERIA["default"]
        )
        system_prompt = config.SYSTEM_PROMPT_ANNOTATION_CHECKER.format(
            drawing_type=drawing_type,
            drawing_type_criteria=criteria,
            rag_context=rag_context,
        )
    else:  # "standard"
        criteria = config.DRAWING_TYPE_STANDARD_CRITERIA.get(
            drawing_type, config.DRAWING_TYPE_STANDARD_CRITERIA["default"]
        )
        system_prompt = config.SYSTEM_PROMPT_STANDARD_CHECKER.format(
            drawing_type=drawing_type,
            drawing_type_criteria=criteria,
            rag_context=rag_context,
        )

    # Build user message with context
    user_message = (
        f"**Kết quả phân tích bản vẽ (Analysis Node):**\n{analysis_result}\n\n"
        f"**Dữ liệu kích thước từ DXF:**\n"
        f"```json\n{json.dumps(dxf_json.get('dimensions', [])[:30], ensure_ascii=False, indent=2)}\n```\n\n"
        f"**Dữ liệu chú thích từ DXF:**\n"
        f"```json\n{json.dumps(dxf_json.get('texts', [])[:30], ensure_ascii=False, indent=2)}\n```\n\n"
        "Dựa trên ảnh bản vẽ và dữ liệu trên, hãy thực hiện kiểm tra chi tiết.\n\n"
        "QUAN TRỌNG: Trả về kết quả theo định dạng JSON có cấu trúc sau:\n"
        "```json\n"
        "{\n"
        '  "detailed_analysis": [\n'
        "    {\n"
        '      "step": "Tên mục kiểm tra (ví dụ: Kiểm tra tính đầy đủ của kích thước)",\n'
        '      "result": "pass" hoặc "fail" hoặc "warning",\n'
        '      "detail": "Mô tả chi tiết kết quả kiểm tra bước này bằng tiếng Việt"\n'
        "    }\n"
        "  ],\n"
        '  "errors": [\n'
        "    {\n"
        '      "error_id": "dim_001",\n'
        '      "severity": "high",\n'
        '      "description": "Mô tả lỗi bằng tiếng Việt",\n'
        '      "entity_handles": ["A1F", "B3C"],\n'
        '      "iso_reference": "[ISO 129-1:2018] - Điều 6.2: Nội dung quy định"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n"
        "Nếu không có lỗi, trả về {\"detailed_analysis\": [...], \"errors\": []}.\n"
        "detailed_analysis là bắt buộc — liệt kê MỀI bước kiểm tra với result (pass/fail/warning) và giải thích.\n"
        "severity phải là một trong: \"high\", \"medium\", \"low\".\n"
        "entity_handles là danh sách handle DXF của các entity liên quan (có thể rỗng [])."
    )


    return system_prompt, user_message


# ---------------------------------------------------------------------------
# Self-Check prompt and call (Req 4.1 – 4.6)
# ---------------------------------------------------------------------------

def build_self_check_prompt(
    error_description: str,
    iso_reference: str,
    checker_type: str,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_message) for a Self-Check VLM call.

    The prompt instructs the VLM to focus exclusively on the cropped region
    and confirm whether the described error is actually present.

    Args:
        error_description: Vietnamese description of the error to verify.
        iso_reference: ISO standard clause citation string.
        checker_type: Checker label ("dimension", "annotation", or "standard").

    Returns:
        Tuple of (system_prompt, user_message).

    Requirement: 4.1, 4.5, 4.6
    """
    # Use the centralized template from config (Req 4.6)
    system_prompt = config.SYSTEM_PROMPT_SELF_CHECK.format(
        error_description=error_description,
        iso_reference=iso_reference,
        checker_type=checker_type,
    )

    user_message = (
        "Hãy quan sát ảnh bản vẽ được crop (vùng có thể chứa lỗi) và xác nhận:\n"
        f"- Lỗi cần xác nhận: {error_description}\n"
        f"- Tiêu chuẩn liên quan: {iso_reference}\n\n"
        "Trả về JSON theo định dạng yêu cầu. Chỉ JSON, không thêm nội dung khác."
    )

    return system_prompt, user_message


def call_vlm_for_self_check(
    image_base64: str,
    error_description: str,
    iso_reference: str,
    checker_type: str,
) -> bool:
    """
    Call VLM with a cropped image to verify whether an error actually exists.

    Sends the cropped region image + self-check prompt to GPT-4o and parses
    the JSON response for the "confirmed" field.

    Args:
        image_base64: Base64-encoded PNG of the cropped region.
        error_description: Vietnamese description of the error.
        iso_reference: ISO standard citation.
        checker_type: Checker label.

    Returns:
        True if VLM confirms the error exists (keep in report).
        False if VLM says the error is a false positive (remove from report).
        Defaults to True on any JSON parse failure (Req 4.4).

    Requirement: 4.2, 4.3, 4.4
    """
    system_prompt, user_message = build_self_check_prompt(
        error_description=error_description,
        iso_reference=iso_reference,
        checker_type=checker_type,
    )

    try:
        raw_response = call_vlm_with_image(
            system_prompt=system_prompt,
            user_message=user_message,
            image_base64=image_base64,
            max_tokens=512,        # Self-check only needs a short JSON reply
            temperature=0.0,
        )
    except RuntimeError as exc:
        logger.warning("Self-check VLM call failed: %s — defaulting to confirmed=True", exc)
        return True  # Req 4.4: keep error on failure

    # Parse JSON response (Req 4.3)
    try:
        # Strip markdown code fences if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        data = json.loads(cleaned)
        confirmed = bool(data.get("confirmed", True))
        reasoning = data.get("reasoning", "")
        logger.info(
            "Self-check result: confirmed=%s, reasoning=%.100s", confirmed, reasoning
        )
        return confirmed
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(
            "Self-check JSON parse failed (%s); raw='%.200s' — defaulting to confirmed=True",
            exc, raw_response,
        )
        return True  # Req 4.4: safe fallback

