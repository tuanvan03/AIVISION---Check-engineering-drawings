"""
config.py — Central configuration, prompts, and constants for AI Vision Drawing Checker.

All model names, thresholds, prompt templates, and citation formats are
defined here to keep them easy to update without touching business logic.
"""

import os
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# Model Configuration
# ---------------------------------------------------------------------------

# Vision Language Model used for all image-based analysis
VLM_MODEL: str = "gpt-4o"

# Text-only LLM for RAG Q&A and lightweight classification
TEXT_MODEL: str = "gpt-4o-mini"

# Embedding model for ChromaDB vector store
EMBEDDING_MODEL: str = "text-embedding-3-small"

# Maximum tokens for VLM responses
VLM_MAX_TOKENS: int = 4096

# Temperature — 0 for deterministic, consistent results
VLM_TEMPERATURE: float = 0.0

# ---------------------------------------------------------------------------
# Drawing Types
# ---------------------------------------------------------------------------
DRAWING_TYPES: list[str] = [
    "Cơ khí (Mechanical)",
    "Nội thất (Interior)",
    "Kiến trúc (Architectural)",
    "Điện (Electrical)",
    "Ống & Đường ống (Piping & Plumbing)",
    "Kết cấu thép (Structural)",
    "Khác (Other)",
]

# Minimum confidence score (0–1) for Drawing_Type_Predictor to make a suggestion
# Below this threshold the system will ask the user directly
DRAWING_TYPE_CONFIDENCE_THRESHOLD: float = 0.6

# ---------------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------------

# Path to ISO PDF documents
DOCUMENTS_DIR: str = "documents"

# ChromaDB persistence directory
CHROMA_PERSIST_DIR: str = ".chroma_db"

# Collection name in ChromaDB
CHROMA_COLLECTION_NAME: str = "iso_standards"

# Number of top-k chunks to retrieve per RAG query
RAG_TOP_K: int = 5

# Chunk size for splitting PDF pages
RAG_CHUNK_SIZE: int = 1000
RAG_CHUNK_OVERLAP: int = 200

# Priority document mapping for each checker
RAG_CHECKER_PRIORITY: dict[str, list[str]] = {
    "dimension": ["ISO-129-1-2018.pdf", "ISO-DIS-129-2.pdf", "ISO-128-1-2020.pdf"],
    "annotation": ["ISO-7200-2004.pdf", "ISO-128-1-2020.pdf"],
    "standard": ["ISO-1101-2017.pdf", "ISO-128-1-2020.pdf", "ISO-128-2-2020.pdf", "ISO-128-3-2020.pdf"],
}

# ---------------------------------------------------------------------------
# Region Cropper
# ---------------------------------------------------------------------------

# When entity count is below this threshold, skip cropping and send full SVG
COMPLEXITY_THRESHOLD: int = 200

# Default padding (in DXF units) added around cropped regions
CROP_PADDING_DXF_UNITS: float = 10.0

# Target pixel dimensions for cropped high-res images
CROP_TARGET_WIDTH_PX: int = 1024
CROP_TARGET_HEIGHT_PX: int = 1024

# Default SVG export resolution for full drawing
SVG_DEFAULT_DPI: int = 150

# High-resolution DPI for cropped regions
SVG_CROP_DPI: int = 300

# ---------------------------------------------------------------------------
# Self-Check Configuration (Req 5.1 – 5.5)
# ---------------------------------------------------------------------------

# Maximum number of errors to verify via self-check in a single run.
# Prevents excessive VLM calls; high-severity errors are prioritized.
SELF_CHECK_MAX_ERRORS: int = 10

# System prompt template for Self-Check VLM calls.
# Placeholders: {error_description}, {iso_reference}, {checker_type}
SYSTEM_PROMPT_SELF_CHECK: str = """Bạn là chuyên gia kiểm tra bản vẽ kỹ thuật với nhiều năm kinh nghiệm.
Bạn đang xem xét một VÙNG CỤ THỂ trong bản vẽ kỹ thuật (ảnh đã được crop và phóng to).

Người dùng cần xác nhận xem lỗi sau đây có THỰC SỰ TỒN TẠI trong vùng ảnh này không:

Loại lỗi: {checker_type}
Mô tả lỗi: {error_description}
Tiêu chuẩn liên quan: {iso_reference}

Hãy quan sát KỸ LƯỠNG vùng ảnh và trả lời bằng JSON theo định dạng sau:
{{
  "confirmed": true/false,
  "reasoning": "Giải thích ngắn gọn tại sao lỗi tồn tại hoặc không tồn tại trong vùng này (tiếng Việt)"
}}

Quy tắc:
- Chỉ trả về JSON, không thêm nội dung khác
- confirmed: true nếu lỗi CÓ tồn tại, false nếu KHÔNG tồn tại (false positive)
- Nếu không chắc chắn, hãy trả về confirmed: true để tránh bỏ sót lỗi thực
"""

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_ANALYSIS: str = """Bạn là một chuyên gia kiểm tra bản vẽ kỹ thuật CAD với nhiều năm kinh nghiệm.
Bạn nhận được:
1. Ảnh bản vẽ kỹ thuật (SVG/PNG)
2. Dữ liệu JSON từ parser ezdxf chứa toàn bộ thông tin entities, layers, dimensions, annotations

Nhiệm vụ của bạn (Tool 1 — Analysis Node):
- Mô tả chi tiết từng thành phần của bản vẽ: đường nét, kích thước, chú thích, khung tên, tỷ lệ, ký hiệu kỹ thuật
- Liệt kê TẤT CẢ các giá trị số liệu kích thước có trong bản vẽ
- Xác định loại bản vẽ: {drawing_type}
- Trả lời HOÀN TOÀN bằng tiếng Việt
"""

SYSTEM_PROMPT_DIMENSION_CHECKER: str = """Bạn là chuyên gia kiểm tra kích thước bản vẽ kỹ thuật theo tiêu chuẩn ISO.
Loại bản vẽ: {drawing_type}

Tiêu chí áp dụng cho loại bản vẽ này:
{drawing_type_criteria}

Tài liệu tiêu chuẩn tham chiếu (từ RAG):
{rag_context}

Nhiệm vụ (Sub-tool 2a — Dimension Checker):
1. Kiểm tra TÍNH ĐẦY ĐỦ: mọi thành phần hình học phải có kích thước tương ứng
2. Kiểm tra TÍNH NHẤT QUÁN: các kích thước không được mâu thuẫn nhau
3. Kiểm tra ĐỊNH DẠNG ghi kích thước theo tiêu chuẩn áp dụng
4. Với mỗi lỗi, trích dẫn chính xác điều khoản ISO liên quan

Định dạng trích dẫn: [Tên tiêu chuẩn] [Số hiệu] - [Điều khoản]: [Nội dung quy định]
Trả lời HOÀN TOÀN bằng tiếng Việt.
"""

SYSTEM_PROMPT_ANNOTATION_CHECKER: str = """Bạn là chuyên gia kiểm tra chú thích bản vẽ kỹ thuật theo tiêu chuẩn ISO 7200.
Loại bản vẽ: {drawing_type}

Tiêu chí áp dụng cho loại bản vẽ này:
{drawing_type_criteria}

Tài liệu tiêu chuẩn tham chiếu (từ RAG):
{rag_context}

Nhiệm vụ (Sub-tool 2b — Annotation Checker):
1. Kiểm tra SỰ HIỆN DIỆN của các chú thích bắt buộc:
   - Khung tên (title block): tên bản vẽ, số hiệu, ngày, tên người vẽ, tỷ lệ
   - Tỷ lệ bản vẽ
   - Vật liệu
   - Dung sai chung (general tolerance)
   - Ký hiệu chiếu góc (1st/3rd angle projection)
2. Kiểm tra TÍNH RÕ RÀNG và ĐẦY ĐỦ của các ghi chú kỹ thuật
3. Kiểm tra ĐỊNH DẠNG và VỊ TRÍ của chú thích

Định dạng trích dẫn: [Tên tiêu chuẩn] [Số hiệu] - [Điều khoản]: [Nội dung quy định]
Trả lời HOÀN TOÀN bằng tiếng Việt.
"""

SYSTEM_PROMPT_STANDARD_CHECKER: str = """Bạn là chuyên gia kiểm tra tuân thủ tiêu chuẩn quốc tế ISO/ASME cho bản vẽ kỹ thuật.
Loại bản vẽ: {drawing_type}

Tiêu chí áp dụng cho loại bản vẽ này:
{drawing_type_criteria}

Tài liệu tiêu chuẩn tham chiếu (từ RAG):
{rag_context}

Nhiệm vụ (Sub-tool 2c — Standard Checker):
1. Kiểm tra KÝ HIỆU DUNG SAI HÌNH HỌC (GD&T) theo ISO 1101
2. Kiểm tra KÝ HIỆU HOÀN THIỆN BỀ MẶT theo ISO 1302
3. Kiểm tra KÝ HIỆU HÀN (nếu có)
4. Kiểm tra QUY ƯỚC VẼ KỸ THUẬT theo ISO 128 (loại đường nét, chiều dày, v.v.)
5. Với mỗi vi phạm, trích dẫn chính xác điều khoản tiêu chuẩn

Định dạng trích dẫn: [Tên tiêu chuẩn] [Số hiệu] - [Điều khoản]: [Nội dung quy định]
Trả lời HOÀN TOÀN bằng tiếng Việt.
"""

SYSTEM_PROMPT_RAG_CHAT: str = """Bạn là trợ lý kỹ thuật chuyên về các tiêu chuẩn ISO cho bản vẽ kỹ thuật.

Tài liệu tiêu chuẩn tham chiếu:
{rag_context}

Hãy trả lời câu hỏi của kỹ sư dựa trên các tài liệu tiêu chuẩn được cung cấp.
Luôn trích dẫn nguồn theo định dạng: [Tên tiêu chuẩn] [Số hiệu] - [Điều khoản]: [Nội dung]
Nếu không tìm thấy thông tin liên quan, hãy nói rõ và đề xuất tham khảo trực tiếp tài liệu gốc.
Trả lời HOÀN TOÀN bằng tiếng Việt.
"""

# Drawing-type-specific dimension criteria injected into checker prompts
DRAWING_TYPE_DIMENSION_CRITERIA: dict[str, str] = {
    "Cơ khí (Mechanical)": (
        "- Tất cả kích thước phải được ghi theo ISO 129-1\n"
        "- Dung sai kích thước phải được chỉ định hoặc tham chiếu dung sai chung\n"
        "- Kích thước lỗ, trục phải có ký hiệu ⌀ hoặc R\n"
        "- Chiều dày vật liệu phải được ghi rõ\n"
        "- Kích thước ren phải theo ISO 724"
    ),
    "Kiến trúc (Architectural)": (
        "- Kích thước phòng, tường phải được ghi đầy đủ\n"
        "- Cao độ nền, trần phải được chỉ định\n"
        "- Kích thước cửa, cửa sổ phải có đầy đủ\n"
        "- Tỷ lệ phổ biến: 1:50, 1:100, 1:200"
    ),
    "default": (
        "- Mọi thành phần hình học phải có kích thước tương ứng\n"
        "- Kích thước không được mâu thuẫn nhau\n"
        "- Định dạng kích thước phải theo tiêu chuẩn áp dụng"
    ),
}

DRAWING_TYPE_ANNOTATION_CRITERIA: dict[str, str] = {
    "Cơ khí (Mechanical)": (
        "- Khung tên bắt buộc: tên chi tiết, số hiệu, vật liệu, tỷ lệ, đơn vị, dung sai chung\n"
        "- Ký hiệu chiếu góc (1st hoặc 3rd angle) bắt buộc\n"
        "- Ghi chú xử lý bề mặt (nếu có yêu cầu)\n"
        "- Số phiên bản và lịch sử sửa đổi"
    ),
    "Kiến trúc (Architectural)": (
        "- Khung tên: tên dự án, số bản vẽ, ngày, tỷ lệ\n"
        "- Hướng bắc (North arrow) trên mặt bằng\n"
        "- Ghi chú vật liệu và hoàn thiện\n"
        "- Chú thích các ký hiệu sử dụng"
    ),
    "default": (
        "- Khung tên phải có: tên bản vẽ, số hiệu, tỷ lệ, ngày\n"
        "- Tỷ lệ bản vẽ phải được ghi rõ\n"
        "- Chú thích phải rõ ràng và đầy đủ"
    ),
}

DRAWING_TYPE_STANDARD_CRITERIA: dict[str, str] = {
    "Cơ khí (Mechanical)": (
        "- Ký hiệu GD&T theo ISO 1101 (độ thẳng, phẳng, tròn, trụ, vuông góc, v.v.)\n"
        "- Ký hiệu hoàn thiện bề mặt theo ISO 1302\n"
        "- Loại đường nét theo ISO 128-2 (đường liền, đứt, tâm, kích thước)\n"
        "- Chiều dày đường theo quy chuẩn ISO 128"
    ),
    "default": (
        "- Loại đường nét theo ISO 128-2\n"
        "- Ký hiệu kỹ thuật phải theo tiêu chuẩn ISO/ASME tương ứng\n"
        "- Quy ước trình bày theo ISO 128-1"
    ),
}

# ---------------------------------------------------------------------------
# UI Text (Vietnamese)
# ---------------------------------------------------------------------------

UI_TITLE: str = "AI Vision Drawing Checker"
UI_SUBTITLE: str = "Kiểm tra bản vẽ kỹ thuật tự động bằng AI"

UI_UPLOAD_LABEL: str = "Tải lên file bản vẽ DXF"
UI_UPLOAD_HELP: str = "Chỉ chấp nhận file định dạng .dxf"
UI_UPLOAD_ERROR_FORMAT: str = "❌ File không đúng định dạng. Vui lòng tải lên file .dxf"
UI_UPLOAD_ERROR_PARSE: str = "❌ Không thể đọc file DXF: {error}"
UI_UPLOAD_SUCCESS: str = "✅ Đã tải lên file: {filename}"

UI_CHAT_PLACEHOLDER: str = "Nhập câu hỏi hoặc yêu cầu kiểm tra..."
UI_CHAT_WAITING: str = "⏳ Hãy tải lên file DXF trước để bắt đầu kiểm tra."
UI_CHAT_ANALYZING: str = "🔍 Đang phân tích bản vẽ..."
UI_CHAT_ERROR: str = "❌ Đã xảy ra lỗi: {error}. Vui lòng thử lại."

UI_DRAWING_TYPE_ASK: str = (
    "🤔 Tôi chưa xác định được loại bản vẽ. "
    "Bạn vui lòng cho biết đây là loại bản vẽ gì?\n"
    "(Ví dụ: Cơ khí, Kiến trúc, Điện, Nội thất, ...)"
)

UI_ANALYSIS_HEADER: str = "📋 Phân Tích Chi Tiết Bản Vẽ"
UI_REVIEW_HEADER: str = "🔍 Báo Cáo Kiểm Tra"
UI_DIMENSION_HEADER: str = "📐 Kiểm Tra Kích Thước"
UI_ANNOTATION_HEADER: str = "📝 Kiểm Tra Chú Thích"
UI_STANDARD_HEADER: str = "📜 Kiểm Tra Tiêu Chuẩn Quốc Tế"

# Self-Check section header in the final report (Req 5.3)
UI_SELF_CHECK_HEADER: str = "🔎 Xác Minh Tự Động (Self-Check)"

# Conclusion section constants (Req 10.5 – 10.6)
UI_CONCLUSION_HEADER: str = "📊 Kết Luận & Gợi Ý"

# Quality verdict templates — used in the conclusion section
UI_CONCLUSION_GOOD: str = (
    "✅ **Bản vẽ đạt yêu cầu cơ bản.** "
    "Không phát hiện lỗi nghiêm trọng. Kiểm tra lại các lỗi mức trung bình (nếu có) trước khi phát hành."
)
UI_CONCLUSION_NEEDS_FIX: str = (
    "⚠️ **Bản vẽ cần chỉnh sửa trước khi sử dụng.** "
    "Có {high_count} lỗi nghiêm trọng cần được giải quyết ngay. "
    "Xem xét kỹ từng lỗi và tham chiếu tiêu chuẩn ISO được trích dẫn."
)
UI_CONCLUSION_CRITICAL: str = (
    "🔴 **Bản vẽ cần xem xét lại toàn bộ.** "
    "Phát hiện {high_count} lỗi nghiêm trọng — bản vẽ chưa đáp ứng tiêu chuẩn. "
    "Cần chỉnh sửa đáng kể trước khi sử dụng hoặc phát hành."
)
