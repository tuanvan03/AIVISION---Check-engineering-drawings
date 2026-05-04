/* ============================================================
   AI Vision Drawing Checker — WebSocket Client
   Handles real-time progress updates, result streaming,
   SVG rendering, and fallback to polling.
   ============================================================ */

class AnalysisWebSocket {
  constructor() {
    this.ws = null;
    this.taskId = null;
    this.callbacks = {};
    this.reconnectAttempts = 0;
    this.maxReconnects = 5;
    this.reconnectDelay = 3000;
    this.intentionalClose = false;
  }

  /**
   * Connect to the analysis WebSocket endpoint.
   * @param {string} taskId - Analysis task UUID
   * @param {string} wsToken - Short-lived JWT from GET /api/v1/auth/ws-token
   * @param {object} callbacks - { onProgress, onSvgReady, onResult, onError, onClose }
   */
  connect(taskId, wsToken, callbacks = {}) {
    this.taskId = taskId;
    this.callbacks = callbacks;
    this.intentionalClose = false;
    this.reconnectAttempts = 0;

    // Determine protocol (wss:// for HTTPS, ws:// for HTTP)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/analysis/${taskId}?token=${encodeURIComponent(wsToken)}`;

    this._open(url);
  }

  _open(url) {
    try {
      this.ws = new WebSocket(url);
    } catch (e) {
      console.error('[WS] Failed to create WebSocket:', e);
      this._handleClose();
      return;
    }

    this.ws.onopen = () => {
      console.log('[WS] Connected for task', this.taskId);
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        this._handleMessage(payload);
      } catch (e) {
        console.error('[WS] Failed to parse message:', e);
      }
    };

    this.ws.onerror = (err) => {
      console.error('[WS] Error:', err);
    };

    this.ws.onclose = (event) => {
      console.log('[WS] Closed:', event.code, event.reason);
      if (!this.intentionalClose) {
        this._handleClose();
      }
    };
  }

  _handleMessage(payload) {
    switch (payload.event) {
      case 'connected':
        console.log('[WS] Handshake complete for task', payload.data?.task_id);
        break;

      case 'progress':
        if (this.callbacks.onProgress) {
          this.callbacks.onProgress(payload.data || {});
        }
        // Also check for SVG inside progress (some implementations include it)
        if (payload.data?.svg_content) {
          if (this.callbacks.onSvgReady) {
            this.callbacks.onSvgReady(payload.data);
          }
        }
        break;

      case 'svg_ready':
        if (this.callbacks.onSvgReady) {
          this.callbacks.onSvgReady(payload.data || {});
        }
        break;

      case 'result':
        if (this.callbacks.onResult) {
          this.callbacks.onResult(payload.data || {});
        }
        this.disconnect();
        break;

      case 'error':
        if (this.callbacks.onError) {
          this.callbacks.onError(payload.data || {});
        }
        this.disconnect();
        break;

      default:
        console.log('[WS] Unknown event:', payload.event);
    }
  }

  _handleClose() {
    if (this.callbacks.onClose) {
      this.callbacks.onClose();
    }

    // Auto-reconnect if not intentional
    if (!this.intentionalClose && this.reconnectAttempts < this.maxReconnects) {
      this.reconnectAttempts++;
      console.log(`[WS] Reconnecting (${this.reconnectAttempts}/${this.maxReconnects})...`);
      setTimeout(() => {
        if (!this.intentionalClose && this.taskId) {
          // Re-fetch WS token and reconnect
          this._reconnect();
        }
      }, this.reconnectDelay);
    }
  }

  async _reconnect() {
    try {
      const res = await fetch('/api/v1/auth/ws-token');
      if (!res.ok) throw new Error('Failed to refresh WS token');
      const data = await res.json();
      if (data.ws_token) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const url = `${protocol}//${host}/ws/analysis/${this.taskId}?token=${encodeURIComponent(data.ws_token)}`;
        this._open(url);
      }
    } catch (e) {
      console.error('[WS] Reconnect failed:', e);
      if (this.callbacks.onError) {
        this.callbacks.onError({ message: 'Mất kết nối. Đang thử lại...' });
      }
    }
  }

  disconnect() {
    this.intentionalClose = true;
    if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
      this.ws.close();
    }
    this.ws = null;
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}
