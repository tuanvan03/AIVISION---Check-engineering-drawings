# Tài Liệu API - Drawing Checker Application

**Base URL:** `http://localhost:8000`

**Tài khoản test:**
- **Admin:** `admin@gmail.com` / `admin@123`
- **User:** Tự tạo tài khoản qua endpoint `/api/v1/auth/register`

---

## Mục Lục

1. [Authentication APIs](#1-authentication-apis)
2. [User APIs](#2-user-apis)
3. [Analysis APIs](#3-analysis-apis)
4. [Admin APIs](#4-admin-apis)
5. [Page Routes](#5-page-routes)

---

## 1. Authentication APIs

**File:** `app/routers/auth.py`

**Services liên quan:** `AuthService`

### 1.1. Đăng ký tài khoản

**Endpoint:** `POST /api/v1/auth/register`

**Mô tả:** Tạo tài khoản người dùng mới

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "confirm_password": "password123",
  "display_name": "Nguyễn Văn A"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "display_name": "Nguyễn Văn A",
  "role": "user"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "Test@123",
    "confirm_password": "Test@123",
    "display_name": "Test User"
  }'
```

**Postman:**
- Method: `POST`
- URL: `http://localhost:8000/api/v1/auth/register`
- Headers: `Content-Type: application/json`
- Body (raw JSON): Như trên

---

### 1.2. Đăng nhập

**Endpoint:** `POST /api/v1/auth/login`

**Mô tả:** Đăng nhập và nhận cookie session

**Request Body:**
```json
{
  "email": "admin@gmail.com",
  "password": "admin@123"
}
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": 1,
    "email": "admin@gmail.com",
    "display_name": "Admin",
    "role": "admin"
  },
  "redirect_url": "/admin"
}
```

**Cookie được set:** `access_token` (HttpOnly, 24h expiry)

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "admin@gmail.com",
    "password": "admin@123"
  }'
```

**Postman:**
- Method: `POST`
- URL: `http://localhost:8000/api/v1/auth/login`
- Headers: `Content-Type: application/json`
- Body (raw JSON): Như trên
- Sau khi login, cookie `access_token` sẽ tự động được lưu

---

### 1.3. Đăng xuất

**Endpoint:** `POST /api/v1/auth/logout`

**Mô tả:** Đăng xuất và xóa cookie session

**Authentication:** Required (Cookie)

**Response:** `200 OK`
```json
{
  "message": "Đăng xuất thành công"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -b cookies.txt
```

---

### 1.4. Quên mật khẩu

**Endpoint:** `POST /api/v1/auth/forgot-password`

**Mô tả:** Gửi yêu cầu reset mật khẩu (chưa implement đầy đủ)

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi."
}
```

---

### 1.5. Lấy WebSocket Token

**Endpoint:** `GET /api/v1/auth/ws-token`

**Mô tả:** Lấy token ngắn hạn (60s) để kết nối WebSocket

**Authentication:** Required (Cookie)

**Response:** `200 OK`
```json
{
  "ws_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/auth/ws-token \
  -b cookies.txt
```

---

## 2. User APIs

**File:** `app/routers/users.py`

**Services liên quan:** `AuthService`, `QuotaService`

### 2.1. Lấy thông tin người dùng hiện tại

**Endpoint:** `GET /api/v1/users/me`

**Mô tả:** Lấy thông tin profile và quota của user đang đăng nhập

**Authentication:** Required (Cookie)

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "display_name": "Nguyễn Văn A",
  "role": "user",
  "avatar_url": null,
  "quota": {
    "used": 5,
    "max": 100,
    "remaining": 95
  }
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -b cookies.txt
```

**Postman:**
- Method: `GET`
- URL: `http://localhost:8000/api/v1/users/me`
- Cookies sẽ tự động gửi sau khi login

---

### 2.2. Cập nhật profile

**Endpoint:** `PUT /api/v1/users/me`

**Mô tả:** Cập nhật tên hiển thị và avatar

**Authentication:** Required (Cookie)

**Request Body:**
```json
{
  "display_name": "Nguyễn Văn B",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**Response:** `200 OK` (Trả về profile đã cập nhật)

**cURL Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/users/me \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "display_name": "Updated Name",
    "avatar_url": null
  }'
```

---

### 2.3. Đổi mật khẩu

**Endpoint:** `POST /api/v1/users/me/change-password`

**Mô tả:** Đổi mật khẩu (yêu cầu mật khẩu cũ)

**Authentication:** Required (Cookie)

**Request Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Đổi mật khẩu thành công"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/users/me/change-password \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "current_password": "Test@123",
    "new_password": "NewPass@456"
  }'
```

---

### 2.4. Thiết lập mật khẩu

**Endpoint:** `POST /api/v1/users/me/set-password`

**Mô tả:** Thiết lập mật khẩu cho tài khoản OAuth chưa có password

**Authentication:** Required (Cookie)

**Request Body:**
```json
{
  "new_password": "newpassword123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Thiết lập mật khẩu thành công"
}
```

---

## 3. Analysis APIs

**File:** `app/routers/analysis.py`

**Services liên quan:** `AnalysisService`, `QuotaService`

### 3.1. Upload file DXF

**Endpoint:** `POST /api/v1/analysis/upload`

**Mô tả:** Upload file DXF để phân tích, hệ thống sẽ dự đoán loại bản vẽ

**Authentication:** Required (Cookie)

**Quota Check:** Required (kiểm tra quota trước khi upload)

**Request:** `multipart/form-data`
- `file`: File DXF (max 50MB)

**Response:** `201 Created`
```json
{
  "task_id": "abc123-def456",
  "message": "Tải lên thành công, vui lòng xác nhận loại bản vẽ",
  "predicted_drawing_type": "mechanical",
  "prediction_confidence": 0.85,
  "prediction_reasoning": "Phát hiện nhiều dimension và tolerance symbols",
  "is_confident": true,
  "dxf_metadata": {
    "version": "AC1027",
    "layers": 5,
    "entities": 150
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/analysis/upload \
  -b cookies.txt \
  -F "file=@/path/to/drawing.dxf"
```

**Postman:**
- Method: `POST`
- URL: `http://localhost:8000/api/v1/analysis/upload`
- Body: `form-data`
  - Key: `file`, Type: `File`, Value: Chọn file DXF

---

### 3.2. Xác nhận loại bản vẽ và bắt đầu phân tích

**Endpoint:** `POST /api/v1/analysis/{task_id}/confirm-type`

**Mô tả:** Xác nhận loại bản vẽ và bắt đầu quá trình phân tích chi tiết

**Authentication:** Required (Cookie)

**Path Parameters:**
- `task_id`: ID của task từ bước upload

**Request Body:**
```json
{
  "drawing_type": "mechanical"
}
```

**Giá trị hợp lệ cho `drawing_type`:**
- `mechanical`: Bản vẽ cơ khí
- `architectural`: Bản vẽ kiến trúc
- `electrical`: Bản vẽ điện

**Response:** `200 OK`
```json
{
  "message": "Đã bắt đầu phân tích",
  "task_id": "abc123-def456"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/analysis/abc123-def456/confirm-type \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "drawing_type": "mechanical"
  }'
```

---

### 3.3. Kiểm tra trạng thái phân tích

**Endpoint:** `GET /api/v1/analysis/{task_id}/status`

**Mô tả:** Lấy trạng thái hiện tại của task phân tích

**Authentication:** Required (Cookie)

**Response:** `200 OK`
```json
{
  "task_id": "abc123-def456",
  "status": "completed",
  "progress_step": "Hoàn thành phân tích",
  "result": {
    "high_errors": 2,
    "medium_errors": 5,
    "low_errors": 3,
    "details": [
      {
        "severity": "high",
        "category": "dimension",
        "message": "Thiếu dimension cho đường kính lỗ",
        "location": "Layer: DIMENSIONS"
      }
    ]
  },
  "error_message": null
}
```

**Các trạng thái:**
- `pending`: Đang chờ
- `parsing`: Đang parse DXF
- `analyzing`: Đang phân tích
- `completed`: Hoàn thành
- `failed`: Thất bại

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/analysis/abc123-def456/status \
  -b cookies.txt
```

---

### 3.4. Lấy file SVG preview

**Endpoint:** `GET /api/v1/analysis/{task_id}/svg`

**Mô tả:** Lấy file SVG render của bản vẽ DXF

**Authentication:** Required (Cookie)

**Response:** `200 OK` (Content-Type: `image/svg+xml`)

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/analysis/abc123-def456/svg \
  -b cookies.txt \
  -o drawing.svg
```

---

### 3.5. Chat với AI về bản vẽ

**Endpoint:** `POST /api/v1/analysis/{task_id}/chat`

**Mô tả:** Hỏi AI về kết quả phân tích hoặc bản vẽ

**Authentication:** Required (Cookie)

**Request Body:**
```json
{
  "message": "Giải thích lỗi dimension này cho tôi"
}
```

**Response:** `200 OK`
```json
{
  "reply": "Lỗi dimension này xảy ra vì...",
  "task_id": "abc123-def456"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/analysis/abc123-def456/chat \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "message": "Tại sao có lỗi high severity?"
  }'
```

---

### 3.6. Lấy lịch sử phân tích

**Endpoint:** `GET /api/v1/analysis/history`

**Mô tả:** Lấy danh sách các bản vẽ đã phân tích của user

**Authentication:** Required (Cookie)

**Query Parameters:**
- `page`: Số trang (default: 1)
- `page_size`: Số item mỗi trang (default: 20, max: 100)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "task_id": "abc123-def456",
      "filename": "drawing.dxf",
      "status": "completed",
      "high_errors": 2,
      "medium_errors": 5,
      "low_errors": 3,
      "created_at": "2026-05-04T10:30:00Z",
      "error_message": null
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/history?page=1&page_size=20" \
  -b cookies.txt
```

---

### 3.7. Xóa lịch sử phân tích

**Endpoint:** `DELETE /api/v1/analysis/history/{history_id}`

**Mô tả:** Xóa một bản ghi lịch sử phân tích

**Authentication:** Required (Cookie)

**Response:** `204 No Content`

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/analysis/history/1 \
  -b cookies.txt
```

---

## 4. Admin APIs

**File:** `app/routers/admin.py`

**Services liên quan:** `AuthService`, `QuotaService`, `LogService`

**Authentication:** Tất cả endpoints yêu cầu role `admin`

### 4.1. Lấy thống kê tổng quan

**Endpoint:** `GET /api/v1/admin/stats`

**Mô tả:** Lấy thống kê tổng quan hệ thống

**Authentication:** Admin only

**Response:** `200 OK`
```json
{
  "total_users": 150,
  "active_users_7d": 45,
  "analyses_today": 23,
  "analyses_this_month": 456
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/admin/stats \
  -b cookies.txt
```

---

### 4.2. Lấy dữ liệu biểu đồ

**Endpoint:** `GET /api/v1/admin/stats/chart`

**Mô tả:** Lấy dữ liệu số lượng phân tích 31 ngày gần nhất

**Authentication:** Admin only

**Response:** `200 OK`
```json
{
  "labels": ["2026-04-04", "2026-04-05", ..., "2026-05-04"],
  "data": [12, 15, 8, 20, ..., 23]
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/admin/stats/chart \
  -b cookies.txt
```

---

### 4.3. Danh sách người dùng

**Endpoint:** `GET /api/v1/admin/users`

**Mô tả:** Lấy danh sách người dùng với phân trang và tìm kiếm

**Authentication:** Admin only

**Query Parameters:**
- `search`: Tìm kiếm theo email hoặc tên (optional)
- `page`: Số trang (default: 1)
- `page_size`: Số item mỗi trang (default: 20)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "display_name": "Nguyễn Văn A",
    "role": "user",
    "is_active": true,
    "created_at": "2026-01-15T08:00:00Z"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/users?search=nguyen&page=1&page_size=20" \
  -b cookies.txt
```

---

### 4.4. Khóa tài khoản

**Endpoint:** `POST /api/v1/admin/users/{user_id}/lock`

**Mô tả:** Khóa tài khoản người dùng

**Authentication:** Admin only

**Response:** `200 OK`
```json
{
  "message": "Đã khoá tài khoản"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/users/5/lock \
  -b cookies.txt
```

---

### 4.5. Mở khóa tài khoản

**Endpoint:** `POST /api/v1/admin/users/{user_id}/unlock`

**Mô tả:** Mở khóa tài khoản người dùng

**Authentication:** Admin only

**Response:** `200 OK`
```json
{
  "message": "Đã mở khoá tài khoản"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/users/5/unlock \
  -b cookies.txt
```

---

### 4.6. Thay đổi quyền người dùng

**Endpoint:** `PUT /api/v1/admin/users/{user_id}/role`

**Mô tả:** Thay đổi role của người dùng

**Authentication:** Admin only

**Request Body:**
```json
{
  "role": "admin"
}
```

**Giá trị hợp lệ:** `user`, `admin`

**Response:** `200 OK`
```json
{
  "message": "Đã đổi quyền"
}
```

**cURL Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/admin/users/5/role \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "role": "admin"
  }'
```

---

### 4.7. Cập nhật quota người dùng

**Endpoint:** `PUT /api/v1/admin/users/{user_id}/quota`

**Mô tả:** Cập nhật số lượng request tối đa mỗi ngày

**Authentication:** Admin only

**Request Body:**
```json
{
  "max_requests": 200
}
```

**Response:** `200 OK`
```json
{
  "message": "Đã cập nhật quota"
}
```

**cURL Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/admin/users/5/quota \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "max_requests": 200
  }'
```

---

### 4.8. Xem logs hệ thống

**Endpoint:** `GET /api/v1/admin/logs`

**Mô tả:** Lấy danh sách logs với filter

**Authentication:** Admin only

**Query Parameters:**
- `user_id`: Filter theo user ID (optional)
- `event_type`: Filter theo loại event (optional)
- `severity`: Filter theo mức độ (optional)
- `page`: Số trang (default: 1)
- `page_size`: Số item mỗi trang (default: 50)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 5,
    "event_type": "login",
    "severity": "info",
    "ip_address": "192.168.1.100",
    "created_at": "2026-05-04T10:30:00Z",
    "details": {
      "user_agent": "Mozilla/5.0..."
    }
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/logs?event_type=login&page=1" \
  -b cookies.txt
```

---

### 4.9. Export logs ra CSV

**Endpoint:** `GET /api/v1/admin/logs/export`

**Mô tả:** Export logs trong khoảng thời gian ra file CSV

**Authentication:** Admin only

**Query Parameters:**
- `date_from`: Ngày bắt đầu (ISO 8601 format, required)
- `date_to`: Ngày kết thúc (ISO 8601 format, required)

**Response:** `200 OK` (Content-Type: `text/csv`)

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/logs/export?date_from=2026-05-01T00:00:00Z&date_to=2026-05-04T23:59:59Z" \
  -b cookies.txt \
  -o logs.csv
```

---

## 5. Page Routes

**File:** `app/routers/pages.py`

**Mô tả:** Các route render HTML pages (không phải API)

### Danh sách Pages:

| Route | Mô tả | Authentication |
|-------|-------|----------------|
| `GET /` | Trang chủ (redirect đến /login nếu chưa đăng nhập) | Optional |
| `GET /login` | Trang đăng nhập | Public |
| `GET /register` | Trang đăng ký | Public |
| `GET /history` | Trang lịch sử phân tích | Required |
| `GET /profile` | Trang profile người dùng | Required |
| `GET /admin` | Dashboard admin | Admin only |
| `GET /admin/users` | Quản lý người dùng | Admin only |
| `GET /admin/logs` | Xem logs hệ thống | Admin only |

---

## Tổng Kết Thống Kê API

### Theo File Router:

| File | Số lượng API | Loại |
|------|--------------|------|
| `auth.py` | 5 | Authentication |
| `users.py` | 4 | User Management |
| `analysis.py` | 7 | Analysis & Drawing |
| `admin.py` | 9 | Admin Management |
| `pages.py` | 8 | HTML Pages |
| **Tổng** | **33** | |

### Theo Chức Năng:

- **Authentication:** 5 APIs
- **User Profile & Settings:** 4 APIs
- **Drawing Analysis:** 7 APIs
- **Admin Management:** 9 APIs
- **Page Rendering:** 8 routes

---

## Workflow Sử Dụng Thông Thường

### 1. Đăng ký và đăng nhập:
```bash
# Đăng ký
POST /api/v1/auth/register

# Đăng nhập
POST /api/v1/auth/login
```

### 2. Upload và phân tích bản vẽ:
```bash
# Upload file DXF
POST /api/v1/analysis/upload

# Xác nhận loại bản vẽ
POST /api/v1/analysis/{task_id}/confirm-type

# Kiểm tra trạng thái
GET /api/v1/analysis/{task_id}/status

# Xem SVG preview
GET /api/v1/analysis/{task_id}/svg

# Chat với AI
POST /api/v1/analysis/{task_id}/chat
```

### 3. Quản lý profile:
```bash
# Xem thông tin
GET /api/v1/users/me

# Cập nhật profile
PUT /api/v1/users/me

# Đổi mật khẩu
POST /api/v1/users/me/change-password
```

### 4. Admin quản lý (chỉ admin):
```bash
# Xem thống kê
GET /api/v1/admin/stats

# Quản lý users
GET /api/v1/admin/users
POST /api/v1/admin/users/{user_id}/lock
PUT /api/v1/admin/users/{user_id}/role

# Xem logs
GET /api/v1/admin/logs
GET /api/v1/admin/logs/export
```

---

## Notes

- Tất cả API đều sử dụng **Cookie-based authentication** (trừ login/register)
- Cookie `access_token` có thời hạn 24 giờ
- Quota mặc định cho user thường: 100 requests/ngày
- Admin không bị giới hạn quota
- File DXF tối đa: 50MB
- WebSocket endpoint: `ws://localhost:8000/ws?token={ws_token}`

---

**Ngày tạo:** 04/05/2026  
**Version:** 1.0
