-- Database Schema cho AI Vision Drawing Checker
-- Bảng Thuật Ngữ và Database Schema được định nghĩa trong L0-foundation.md

CREATE DATABASE IF NOT EXISTS drawing_checker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE drawing_checker;

-- Bảng users
CREATE TABLE IF NOT EXISTS users (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NULL,          -- NULL nếu đăng ký qua OAuth
    display_name    VARCHAR(100) NOT NULL,
    role            ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    avatar_url      VARCHAR(500) NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    oauth_provider  ENUM('google', 'github') NULL,
    oauth_id        VARCHAR(255) NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_oauth (oauth_provider, oauth_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bảng quota_usage
CREATE TABLE IF NOT EXISTS quota_usage (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL,
    usage_date      DATE NOT NULL,              -- Ngày theo UTC+7
    request_count   INT UNSIGNED NOT NULL DEFAULT 0,
    max_requests    INT UNSIGNED NOT NULL DEFAULT 10,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_date (user_id, usage_date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bảng analysis_history
CREATE TABLE IF NOT EXISTS analysis_history (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL,
    task_id         VARCHAR(36) NOT NULL UNIQUE, -- UUID v4
    filename        VARCHAR(255) NOT NULL,
    drawing_type    VARCHAR(100) NULL,
    status          ENUM('pending','running','completed','failed') NOT NULL DEFAULT 'pending',
    high_errors     INT UNSIGNED NOT NULL DEFAULT 0,
    medium_errors   INT UNSIGNED NOT NULL DEFAULT 0,
    low_errors      INT UNSIGNED NOT NULL DEFAULT 0,
    report_content  LONGTEXT NULL,              -- JSON hoặc Markdown
    error_message   TEXT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bảng activity_logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NULL,       -- NULL cho system events
    event_type      VARCHAR(50) NOT NULL,       -- login_success, login_fail, analysis_start, etc.
    ip_address      VARCHAR(45) NULL,           -- IPv4 hoặc IPv6
    details         JSON NULL,                  -- Thông tin chi tiết dạng JSON
    severity        ENUM('INFO', 'WARNING', 'ERROR') NOT NULL DEFAULT 'INFO',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_severity (severity),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bảng sessions
CREATE TABLE IF NOT EXISTS sessions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL,
    jwt_token_hash  VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash của JWT
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
