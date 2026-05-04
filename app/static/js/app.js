/* ============================================================
   AI Vision Drawing Checker — Core Application JS
   Vanilla JS (no framework), handles theme, auth, toasts,
   API helpers, and global UI state.
   ============================================================ */

// ===================== Theme Toggle =====================
(function() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcons(savedTheme);

  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      updateThemeIcons(next);
    });
  }

  function updateThemeIcons(theme) {
    const darkIcon = document.getElementById('themeIconDark');
    const lightIcon = document.getElementById('themeIconLight');
    if (darkIcon && lightIcon) {
      darkIcon.style.display = theme === 'dark' ? 'none' : '';
      lightIcon.style.display = theme === 'dark' ? '' : 'none';
    }
  }
})();

// ===================== Logout =====================
(function() {
  const btn = document.getElementById('logoutBtn');
  if (btn) {
    btn.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/v1/auth/logout', { method: 'POST' });
        if (res.ok) {
          window.location.href = '/login';
        }
      } catch (e) {
        window.location.href = '/login';
      }
    });
  }
})();

// ===================== Toast System =====================
window.showToast = function(message, type = 'error', duration = 5000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
};

// ===================== API Helpers =====================
window.api = {
  async request(url, options = {}) {
    const config = {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    };
    // Don't set Content-Type for FormData
    if (config.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    const res = await fetch(url, config);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.error?.message || data?.detail || `Lỗi HTTP ${res.status}`;
      throw new Error(msg);
    }
    return data;
  },

  post(url, body) {
    return this.request(url, { method: 'POST', body: JSON.stringify(body) });
  },

  get(url) {
    return this.request(url, { method: 'GET' });
  },

  postForm(url, formData) {
    return this.request(url, { method: 'POST', body: formData });
  },

  delete(url) {
    return this.request(url, { method: 'DELETE' });
  },

  put(url, body) {
    return this.request(url, { method: 'PUT', body: JSON.stringify(body) });
  }
};

// ===================== Form Validation =====================
window.validateEmail = function(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

window.showFieldError = function(el, message) {
  let errEl = el.parentElement.querySelector('.form-error');
  if (!errEl) {
    errEl = document.createElement('div');
    errEl.className = 'form-error';
    el.parentElement.appendChild(errEl);
  }
  errEl.textContent = message;
};

window.clearFieldErrors = function(form) {
  form.querySelectorAll('.form-error').forEach(el => el.remove());
  form.querySelectorAll('.form-input.input-error').forEach(el => el.classList.remove('input-error'));
};

// ===================== Markdown Renderer (lightweight) =====================
window.renderMarkdown = function(text) {
  if (!text) return '';
  let html = text;
  // Escape HTML
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  // Code blocks (``` ... ```)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  // Inline code (`...`)
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Bold (**...**)
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // Italic (*...*)
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  // Headers (### ...)
  html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr>');
  // Tables (basic support: | col | col |)
  html = html.replace(/^\|(.+)\|$/gm, (match) => {
    const cells = match.split('|').filter(c => c.trim());
    if (cells.every(c => /^[-:\s]+$/.test(c))) return ''; // separator row
    const tag = match.includes('---') ? 'th' : 'td';
    return '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
  });
  // Wrap adjacent <tr> in <table>
  html = html.replace(/(<tr>.*?<\/tr>)+/gs, '<table>$&</table>');
  // Line breaks
  html = html.replace(/\n\n/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');
  html = '<p>' + html + '</p>';
  // Clean empty <p></p>
  html = html.replace(/<p><\/p>/g, '');
  return html;
};
