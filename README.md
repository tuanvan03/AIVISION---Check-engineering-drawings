# 📐 AI Vision Drawing Checker

> Công cụ kiểm tra bản vẽ kỹ thuật CAD tự động sử dụng trí tuệ nhân tạo, tích hợp chuẩn ISO/ASME và hệ thống RAG tra cứu tiêu chuẩn.

---

## 📋 Mô Tả Bài Toán

### Vấn Đề
Kỹ sư thiết kế bản vẽ kỹ thuật (DXF) phải đối chiếu thủ công với hàng chục trang tiêu chuẩn ISO/ASME để kiểm tra:
- **Kích thước** có đủ và nhất quán không?
- **Chú thích** (khung tên, tỷ lệ, vật liệu, dung sai chung) có đầy đủ không?
- **Ký hiệu kỹ thuật** (GD&T, hoàn thiện bề mặt, đường nét) có đúng chuẩn quốc tế không?

Quá trình này tốn thời gian, phụ thuộc vào kinh nghiệm cá nhân và dễ bỏ sót lỗi.

### Giải Pháp
**AI Vision Drawing Checker** tự động hóa toàn bộ quy trình kiểm tra bằng cách:
1. Đọc và phân tích file DXF bằng `ezdxf`
2. Render bản vẽ thành ảnh SVG/PNG để AI "nhìn thấy"
3. Sử dụng **Vision Language Model (GPT-4o)** để phân tích bản vẽ như một chuyên gia
4. Truy xuất điều khoản tiêu chuẩn từ **7 tài liệu ISO gốc** (PDF) qua hệ thống **RAG + ChromaDB**
5. Tổng hợp báo cáo lỗi chi tiết bằng **tiếng Việt** kèm trích dẫn nguồn chuẩn xác

---

## 🗂️ Cơ Sở Tri Thức Tiêu Chuẩn (RAG)

Hệ thống được nạp từ 7 tài liệu ISO gốc trong thư mục `documents/`:

| File | Tiêu Chuẩn | Phục Vụ |
|------|-----------|---------|
| `ISO-128-1-2020.pdf` | ISO 128-1:2020 — Nguyên tắc trình bày chung | Tất cả checker |
| `ISO-128-2-2020.pdf` | ISO 128-2:2020 — Quy ước đường nét | Dimension, Standard Checker |
| `ISO-128-3-2020.pdf` | ISO 128-3:2020 — Hướng nhìn, mặt cắt | Standard Checker |
| `ISO-129-1-2018.pdf` | ISO 129-1:2018 — Ghi kích thước và dung sai | Dimension Checker |
| `ISO-DIS-129-2.pdf` | ISO/DIS 129-2 — Dung sai hình dạng và vị trí | Dimension Checker |
| `ISO-1101-2017.pdf` | ISO 1101:2017 — Dung sai hình học (GD&T) | Standard Checker |
| `ISO-7200-2004.pdf` | ISO 7200:2004 — Khung tên bản vẽ kỹ thuật | Annotation Checker |

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                       Streamlit UI                               │
│  ┌──────────────────────────────────┐  ┌──────────────────────┐ │
│  │   Drawing Viewer  (3/4 màn hình) │  │  Chat Interface      │ │
│  │   - Hiển thị SVG bản vẽ          │  │  (1/4 màn hình)     │ │
│  │   - Metadata badges               │  │  - Lịch sử hội thoại│ │
│  │   - Click để zoom                 │  │  - File uploader    │ │
│  └──────────────────────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────▼───────────────┐
              │      LangGraph Orchestrator    │
              │                               │
              │  ┌──────────────────────────┐ │
              │  │  Collect Info Node        │ │  ← Xác nhận loại bản vẽ
              │  └────────────┬─────────────┘ │
              │               ▼               │
              │  ┌──────────────────────────┐ │
              │  │  Analysis Node (Tool 1)   │ │  ← GPT-4o phân tích tổng thể
              │  └────────────┬─────────────┘ │
              │               ▼               │
              │  ┌──────────────────────────┐ │
              │  │  Review Node (Tool 2)     │ │
              │  │  ┌──────────────────────┐│ │
              │  │  │ Dimension Checker (2a)││ │  ← ISO 129  → Structured JSON
              │  │  │ Annotation Checker(2b)││ │  ← ISO 7200 → Structured JSON
              │  │  │ Standard Checker  (2c)││ │  ← ISO 1101 → Structured JSON
              │  │  └──────────────────────┘│ │
              │  └────────────┬─────────────┘ │
              │               ▼               │
              │  ┌──────────────────────────┐ │
              │  │  Self-Check Node         │ │
              │  │  - Lookup entity handles  │ │  ← get_entity_bbox()
              │  │  - Crop vùng lỗi (PNG)    │ │  ← crop_region()
              │  │  - GPT-4o xác nhận lỗi   │ │  ← call_vlm_for_self_check()
              │  │  - Lọc false positives    │ │
              │  └────────────┬─────────────┘ │
              │               ▼               │
              │  ┌──────────────────────────┐ │
              │  │  RAG Chat Node            │ │  ← Hỏi đáp sau khi có kết quả
              │  └──────────────────────────┘ │
              └───────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
 ┌───────────────┐  ┌─────────────────┐  ┌────────────────┐
 │  DXF Parser   │  │  SVG Renderer   │  │   RAG Engine   │
 │  (ezdxf)      │  │  + Region       │  │  (ChromaDB +   │
 │               │  │  Cropper        │  │   OpenAI Embed)│
 └───────────────┘  └─────────────────┘  └────────────────┘
```

---

## 🔄 Luồng Hoạt Động

```
1. UPLOAD FILE DXF
   └─► DXF Parser (ezdxf) → JSON (entities, dims, layers, texts, title block)
       └─► SVG Renderer → SVG string + PNG bytes
           └─► Drawing Type Predictor → đề xuất loại bản vẽ

2. XÁC NHẬN LOẠI BẢN VẼ (qua Chat)
   └─► Người dùng xác nhận: "Cơ khí" / "Kiến trúc" / ...
       └─► Session DB lưu drawing_type → dùng cho tất cả bước sau

3. PHÂN TÍCH (Analysis Node — Tool 1)
   └─► Gửi: ảnh PNG (base64) + DXF JSON summary → GPT-4o
       └─► Nhận: mô tả chi tiết tất cả thành phần bản vẽ (tiếng Việt)

4. KIỂM TRA (Review Node — Tool 2, tuần tự)
   ├─► Dimension Checker (2a)
   │   └─► RAG query ISO 129 → ChromaDB → top-5 chunks
   │       └─► GPT-4o: kiểm tra → Structured JSON {errors: [{error_id, severity,
   │                                description, entity_handles, iso_reference}]}
   │
   ├─► Annotation Checker (2b)
   │   └─► RAG query ISO 7200 → ChromaDB → top-5 chunks
   │       └─► GPT-4o: kiểm tra → Structured JSON (cùng schema)
   │
   └─► Standard Checker (2c)
       └─► RAG query ISO 1101 + ISO 128 → ChromaDB → top-5 chunks
           └─► GPT-4o: kiểm tra → Structured JSON (cùng schema)

5. XÁC MINH TỰ ĐỘNG (Self-Check Node) ← MỚI
   Chỉ chạy khi entity count ≥ 200 (COMPLEXITY_THRESHOLD)
   └─► Với mỗi lỗi severity "high" hoặc "medium" (tối đa 10 lỗi):
       ├─► Tra entity_handles → tính union BBox trong tọa độ DXF
       ├─► Region Cropper → crop PNG tại BBox với padding
       ├─► GPT-4o với ảnh crop: "Lỗi X có thực sự tồn tại không?"
       │   └─► Nhận: {confirmed: true/false, reasoning: "..."}
       └─► False positive → loại khỏi báo cáo cuối

6. BÁO CÁO
   └─► Tổng hợp: bảng tóm tắt self-check + 3 phần lỗi đã xác minh
       └─► Hiển thị trong Chat Interface

7. HỎI ĐÁP SAU ĐÁNH GIÁ
   └─► Người dùng đặt câu hỏi về tiêu chuẩn
       └─► RAG Chat Node: truy xuất ChromaDB → trả lời có trích dẫn

8. ĐÁNH GIÁ LẠI (nếu người dùng phản hồi)
   └─► Phát hiện từ khóa: "xem lại", "sai", "chỉnh", ...
       └─► Xóa kết quả cũ → chạy lại từ bước 3
```

---

## 📦 Công Cụ và Thư Viện

### AI & LLM
| Công cụ | Phiên bản | Mục đích |
|---------|-----------|---------|
| `openai` | ≥ 2.0 | GPT-4o cho vision analysis, GPT-4o-mini cho text |
| `langchain` / `langchain-openai` | ≥ 0.2 | LLM abstractions, prompt management |
| `langgraph` | ≥ 0.1 | Điều phối pipeline dạng đồ thị trạng thái |
| `chromadb` | ≥ 0.5 | Vector store lưu 268 chunks từ 7 tài liệu ISO |
| `langchain-chroma` | ≥ 0.1 | Kết nối LangChain ↔ ChromaDB |

### CAD & Đồ Họa
| Công cụ | Phiên bản | Mục đích |
|---------|-----------|---------|
| `ezdxf` | ≥ 1.3 | Đọc và parse file DXF |
| `matplotlib` | ≥ 3.8 | Render DXF → SVG/PNG qua ezdxf drawing add-on |
| `cairosvg` | ≥ 2.7 | Chuyển SVG → PNG chất lượng cao cho VLM |
| `Pillow` | ≥ 10.0 | Crop, resize ảnh (Region Cropper) |

### RAG & Xử Lý Tài Liệu
| Công cụ | Phiên bản | Mục đích |
|---------|-----------|---------|
| `pdfplumber` | ≥ 0.11 | Trích xuất text từ PDF tiêu chuẩn ISO |
| `pypdf` | ≥ 4.0 | Parse metadata PDF |
| `langchain-text-splitters` | ≥ 0.1 | Chia văn bản thành chunks (1000 ký tự, overlap 200) |

### Giao Diện & Tiện Ích
| Công cụ | Phiên bản | Mục đích |
|---------|-----------|---------|
| `streamlit` | ≥ 1.32 | Web UI framework |
| `python-dotenv` | ≥ 1.0 | Quản lý biến môi trường |
| `numpy` | ≥ 1.26 | Tính toán số học |

---

## 📁 Cấu Trúc Dự Án

```
AI-016/
├── app.py                          # Entry point Streamlit
├── config.py                       # Cấu hình, prompts, hằng số
├── requirements.txt                # Danh sách thư viện
├── .env                            # Biến môi trường (API key)
│
├── documents/                      # 7 tài liệu ISO (PDF)
│   ├── ISO-128-1-2020.pdf
│   ├── ISO-128-2-2020.pdf
│   ├── ISO-128-3-2020.pdf
│   ├── ISO-129-1-2018.pdf
│   ├── ISO-DIS-129-2.pdf
│   ├── ISO-1101-2017.pdf
│   └── ISO-7200-2004.pdf
│
├── modules/
│   ├── dxf_parser.py               # DXF → JSON (Module 2)
│   ├── svg_renderer.py             # DXF → SVG/PNG (Module 3)
│   ├── region_cropper.py           # Crop vùng phân tích chi tiết (Module 4)
│   ├── drawing_type_predictor.py   # Nhận diện loại bản vẽ (Module 5)
│   ├── rag_engine.py               # ChromaDB + ISO PDF indexing (Module 6)
│   ├── vlm_client.py               # OpenAI API wrapper (Module 7)
│   ├── session_db.py               # Streamlit session state (Module 8)
│   ├── orchestrator.py             # LangGraph pipeline (Module 12)
│   └── checkers/
│       ├── dimension_checker.py    # Kiểm tra kích thước (Module 9)
│       ├── annotation_checker.py   # Kiểm tra chú thích (Module 10)
│       └── standard_checker.py    # Kiểm tra tiêu chuẩn ISO (Module 11)
│
└── ui/
    ├── drawing_viewer.py           # SVG viewer component (Module 13)
    └── chat_interface.py           # Chat UI component (Module 13)
```

---

## ⚙️ Hướng Dẫn Cài Đặt và Chạy

### Yêu Cầu Hệ Thống
- **Python**: 3.11+
- **OS**: Linux / macOS / Windows
- **RAM**: ≥ 4GB (ChromaDB indexing cần ~1GB lần đầu)
- **OpenAI API Key** có quyền truy cập `gpt-4o` và `text-embedding-3-small`

---

### Bước 1: Clone và Chuẩn Bị Môi Trường

```bash
# Clone repository
git clone <repository-url>
cd AI-016

# Tạo virtual environment (nếu chưa có)
python3.11 -m venv .venv

# Kích hoạt venv
# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

---

### Bước 2: Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

> **Lưu ý:** Lần đầu cài đặt có thể mất 3–5 phút do tải các package ML như `chromadb`, `onnxruntime`, `tokenizers`.

---

### Bước 3: Cấu Hình API Key

Tạo file `.env` trong thư mục gốc (hoặc chỉnh sửa file đã có):

```bash
# .env
OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxx"
```

> ⚠️ **Quan trọng:** Key phải có quyền truy cập model `gpt-4o` và embedding `text-embedding-3-small`.

---

### Bước 4: Kiểm Tra Tài Liệu ISO

Đảm bảo thư mục `documents/` chứa đủ 7 file PDF:

```bash
ls documents/
# ISO-1101-2017.pdf  ISO-128-1-2020.pdf  ISO-128-2-2020.pdf
# ISO-128-3-2020.pdf  ISO-129-1-2018.pdf  ISO-7200-2004.pdf
# ISO-DIS-129-2.pdf
```

---

### Bước 5: Chạy Ứng Dụng

```bash
# Với venv đã kích hoạt:
streamlit run app.py

# Hoặc chạy trực tiếp từ venv:
.venv/bin/streamlit run app.py
```

Truy cập ứng dụng tại: **http://localhost:8501**

---

### Lần Đầu Khởi Động

Lần đầu chạy, hệ thống sẽ tự động:
1. **Index 7 tài liệu ISO** từ thư mục `documents/` vào ChromaDB (~268 chunks)
2. **Gọi OpenAI Embedding API** để tạo vector embeddings (mất ~30–60 giây)
3. **Lưu index** vào thư mục `.chroma_db/` — các lần chạy sau sẽ load ngay, không cần index lại

```
2026-05-01 [INFO] rag_engine: Indexing: ISO-128-1-2020.pdf
2026-05-01 [INFO] rag_engine: Indexing: ISO-128-2-2020.pdf
...
2026-05-01 [INFO] rag_engine: ChromaDB index built with 268 chunks.
```

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Tải Lên Bản Vẽ
- Click **"Upload"** ở góc phải trên
- Chọn file `.dxf` (tối đa 200MB)
- Bản vẽ sẽ hiển thị ở khu vực 3/4 màn hình bên trái

### 2. Xác Nhận Loại Bản Vẽ
- Hệ thống tự phân tích metadata và đề xuất loại bản vẽ trong chat
- Click nút xác nhận hoặc gõ loại bản vẽ bằng text
- Ví dụ: `"Đúng, đây là bản vẽ cơ khí"` hoặc `"Kiến trúc"`

### 3. Yêu Cầu Kiểm Tra
- Gõ vào ô chat: `"Kiểm tra bản vẽ này cho tôi"` hoặc `"Phân tích bản vẽ"`
- Hệ thống sẽ chạy lần lượt: Phân tích → Kiểm tra kích thước → Chú thích → Tiêu chuẩn

### 4. Xem Kết Quả
Báo cáo xuất hiện trong chat gồm 3 phần:
- **📐 Kiểm Tra Kích Thước** — lỗi kích thước, trích dẫn ISO 129
- **📝 Kiểm Tra Chú Thích** — thiếu trường khung tên, trích dẫn ISO 7200
- **📜 Kiểm Tra Tiêu Chuẩn** — vi phạm GD&T/đường nét, trích dẫn ISO 1101/128

### 5. Hỏi Đáp Về Tiêu Chuẩn
Sau khi có kết quả, có thể hỏi thêm:
- `"ISO 1101 quy định ký hiệu độ phẳng như thế nào?"`
- `"Dung sai chung cần ghi ở đâu theo ISO 7200?"`

### 6. Yêu Cầu Đánh Giá Lại
Gõ các từ như: `"xem lại"`, `"kiểm tra lại"`, `"tôi đã sửa bản vẽ"` → hệ thống sẽ chạy lại toàn bộ quy trình.

---

## 🧩 Mô Tả Chi Tiết Các Module

### `modules/dxf_parser.py`
Đọc file DXF bằng `ezdxf`, trích xuất toàn bộ:
- **Entities**: LINE, ARC, CIRCLE, LWPOLYLINE, SPLINE, INSERT, HATCH, ...
- **Dimensions**: loại (linear, angular, radial), giá trị đo, vị trí, style
- **Texts/MTexts**: nội dung, vị trí, chiều cao chữ
- **Layers**: tên, màu, linetype, visibility
- **Blocks**: tên, số lượng entity
- **Title Block**: heuristic scan từ paper space layouts
- **Metadata**: DXF version, đơn vị, tỷ lệ, giới hạn bản vẽ

### `modules/svg_renderer.py`
Sử dụng `ezdxf.addons.drawing` + `MatplotlibBackend`:
- Export SVG string để nhúng vào HTML (Streamlit)
- Export PNG bytes với DPI tùy chỉnh cho VLM analysis

### `modules/region_cropper.py`
- Chuyển đổi tọa độ DXF → tọa độ pixel (có flip Y axis)
- Crop vùng cụ thể với padding tùy chỉnh
- Upscale lên 1024×1024px cho phân tích VLM chi tiết hơn
- Fallback về ảnh toàn bộ nếu vùng crop không hợp lệ

### `modules/drawing_type_predictor.py`
Hệ thống scoring dựa trên keyword:
- **Layer names**: "DIM", "CENTERLINE", "WALL", "ELEC", "PIPE", ...
- **Block names**: "BOLT", "NORTH ARROW", "SWITCH", "BEAM", ...
- **Scale (DIMSCALE)**: 1:1 → cơ khí; 1:100 → kiến trúc
- **Text content**: tìm từ khóa trong nội dung text entities
- Confidence ≥ 0.6 → đề xuất; < 0.6 → hỏi trực tiếp

### `modules/rag_engine.py`
- Index PDF bằng `pdfplumber` → `RecursiveCharacterTextSplitter` (1000 chars, overlap 200)
- Lưu vào ChromaDB với metadata đầy đủ (tên chuẩn, số hiệu, trang, tiêu đề)
- Retrieval có filter theo checker type (ưu tiên tài liệu phù hợp)
- Format citation: `[ISO 129-1:2018] - Trang 12: Indication of dimensions`

### `modules/orchestrator.py`
LangGraph `StateGraph` với 5 nodes:
- `collect_info` → khi chưa có drawing type
- `analysis` → Tool 1, phân tích tổng thể
- `review` → Tool 2, chạy 3 sub-tools tuần tự, trả **Structured JSON**
- `self_check` → **[MỚI]** Xác minh từng lỗi high/medium bằng ảnh crop
- `rag_chat` → hỏi đáp sau khi review xong

**Topology:** `analysis → review → self_check → END`

### `modules/region_cropper.py` *(đã mở rộng)*
- `crop_region()`, `make_drawing_bounds()` — đã có từ trước
- **[MỚI]** `get_entity_bbox(handle, dxf_json)` — tra cứu bounding box của entity theo handle
  - Hỗ trợ: LINE, ARC, CIRCLE, LWPOLYLINE, POLYLINE, ELLIPSE, DIMENSION, TEXT/MTEXT
- **[MỚI]** `get_union_bbox(handles, dxf_json)` — hợp nhất nhiều bbox thành một vùng

### `modules/vlm_client.py` *(đã mở rộng)*
- `call_vlm_with_image()`, `call_text_llm()` — đã có từ trước
- `build_checker_prompt()` — **cập nhật** yêu cầu VLM trả Structured JSON
- **[MỚI]** `build_self_check_prompt(error_description, iso_reference, checker_type)` — prompt xác minh
- **[MỚI]** `call_vlm_for_self_check(image_base64, ...)` — gọi VLM, trả `bool` (confirmed/false positive)

---

## 🔑 Biến Môi Trường

| Biến | Bắt Buộc | Mô Tả |
|------|----------|-------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key với quyền `gpt-4o` + `text-embedding-3-small` |

---

## 📊 Hiệu Suất Ước Tính

| Bước | Thời Gian Ước Tính |
|------|-------------------|
| Parse DXF + Render SVG | 2–5 giây |
| RAG Indexing (lần đầu) | 30–90 giây |
| Analysis Node (Tool 1) | 15–30 giây |
| Dimension Checker | 15–25 giây |
| Annotation Checker | 15–25 giây |
| Standard Checker | 15–25 giây |
| **Self-Check Node** | **0–60 giây** |
| → Bỏ qua (< 200 entities) | 0 giây |
| → Xác minh 10 lỗi high/medium | ~30–60 giây |
| **Tổng kiểm tra đầy đủ** | **~1.5–3 phút** |

---

## 🐛 Xử Lý Lỗi Thường Gặp

### `ModuleNotFoundError: No module named 'matplotlib'`
```bash
pip install matplotlib
```

### ChromaDB không load được
```bash
# Xóa index cũ và rebuild
rm -rf .chroma_db/
streamlit run app.py  # Sẽ tự index lại
```

### Lỗi `DXFStructureError`
File DXF bị hỏng hoặc không tương thích. Thử export lại từ phần mềm CAD với định dạng DXF R2010 (AC1024) hoặc mới hơn.

### API Rate Limit
Nếu gặp lỗi `429 Too Many Requests`, chờ 60 giây và thử lại. Có thể tăng `VLM_MAX_TOKENS` trong `config.py` xuống để giảm tải.

---

## 📄 License

Dự án này được xây dựng cho mục đích nghiên cứu và nội bộ tại **VINAI**.

---

*Được xây dựng với ❤️ — AI Vision Drawing Checker v1.0*
