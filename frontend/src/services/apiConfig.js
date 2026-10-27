/**
 * apiConfig.js
 * Centralized API configuration and resilient HTTP client for CrimeSense frontend.
 *
 * Responsibilities:
 * 1. Resolves backend API base URLs across local dev, custom proxy, and production hosting.
 * 2. Provides robust response parsing (handleApiResponse) that prevents opaque
 *    "Unexpected token '<', '<!doctype '... is not valid JSON" errors by detecting
 *    HTML SPA fallbacks and server outages before JSON parsing.
 * 3. Preserves exact backend JSON error messages and HTTP status codes.
 * 4. Never exposes or logs sensitive credentials, tokens, or personal information.
 */

const rawUrl = (import.meta.env.VITE_API_URL || '').trim();
const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();

// In local browser development/preview, default to http://localhost:5000 if not explicitly configured
const isLocalBrowser =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const localDefaultHost = isLocalBrowser ? 'http://localhost:5000' : '';

// Cleaned base host without trailing slash and without trailing /api
// e.g. "https://crimesense-api.onrender.com" or "http://localhost:5000"
export const API_BASE_URL = rawUrl
  ? rawUrl.replace(/\/+$/, '').replace(/\/api$/, '')
  : rawBaseUrl
    ? rawBaseUrl.replace(/\/+$/, '').replace(/\/api$/, '')
    : localDefaultHost;

// Route prefix including /api
// e.g. "https://crimesense-api.onrender.com/api" or "http://localhost:5000/api"
export const API_BASE = rawBaseUrl
  ? rawBaseUrl.replace(/\/+$/, '')
  : rawUrl
    ? `${rawUrl.replace(/\/+$/, '').replace(/\/api$/, '')}/api`
    : localDefaultHost
      ? `${localDefaultHost}/api`
      : '/api';


/**
 * Check if the frontend is currently running on a known static hosting origin
 * without a configured external backend URL.
 */
export function isStaticHostingWithoutBackend() {
  if (typeof window === 'undefined' || !window.location) return false;
  const host = window.location.hostname.toLowerCase();
  const isStaticHost = host.endsWith('.web.app') || host.endsWith('.firebaseapp.com') || host.endsWith('.github.io');
  const hasExternalBackend = Boolean(rawUrl || rawBaseUrl);
  return isStaticHost && !hasExternalBackend;
}

/**
 * Handle and validate fetch responses safely.
 * Detects HTML error/fallback pages (e.g. Firebase Hosting index.html rewrites, 502 Bad Gateway)
 * and produces clear, actionable error messages instead of letting res.json() throw
 * "Unexpected token '<', '<!doctype '... is not valid JSON".
 *
 * @param {Response} response - Native Fetch API Response object
 * @param {string} [contextMessage] - Optional descriptor for the action (e.g. "Login")
 * @returns {Promise<any>} - Parsed JSON object
 */
export async function handleApiResponse(response, contextMessage = 'API Request') {
  const contentType = (response.headers.get('content-type') || '').toLowerCase();
  const isJson = contentType.includes('application/json');

  // Case 1: Server returned HTML
  if (!isJson && contentType.includes('text/html')) {
    const htmlSnippet = await response.text().catch(() => '');
    const isHtmlDoc = htmlSnippet.trim().toLowerCase().startsWith('<!doctype') || htmlSnippet.trim().toLowerCase().startsWith('<html');

    if (response.status === 200 || response.status === 404 || isHtmlDoc) {
      if (isStaticHostingWithoutBackend()) {
        throw new Error(
          'CrimeSense Backend Unreachable: The application is running on static hosting, but no backend API URL was configured during build (VITE_API_URL is missing). Requests are hitting Firebase index.html instead of the Flask API.'
        );
      }
      throw new Error(
        `${contextMessage} failed: The server returned an HTML page instead of API JSON (HTTP ${response.status}). If deployed, please verify your Flask backend URL (VITE_API_URL) is correct and active.`
      );
    }

    if (response.status === 502 || response.status === 503 || response.status === 504) {
      throw new Error(
        `Backend server unavailable (HTTP ${response.status}). If hosted on a free cloud tier, the server may be sleeping or restarting. Please retry in 30 seconds.`
      );
    }

    throw new Error(
      `${contextMessage} failed: Server returned an HTML error page (HTTP ${response.status}).`
    );
  }

  // Case 2: Response text might not declare application/json but could be JSON
  let data;
  let rawText = '';
  try {
    rawText = await response.text();
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    // If text starts with HTML tag despite no text/html header
    if (rawText.trim().startsWith('<')) {
      throw new Error(
        `${contextMessage} failed: Server returned an HTML response instead of JSON (HTTP ${response.status}). Verify backend route exists.`
      );
    }
    throw new Error(
      `${contextMessage} failed: Received malformed response from server (HTTP ${response.status}).`
    );
  }

  // Case 3: HTTP status error or explicit backend success: false
  if (!response.ok || (data && data.success === false)) {
    const errorMsg =
      (data && (data.message || data.error || data.detail)) ||
      `${contextMessage} failed with HTTP status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

/**
 * Robust fetch wrapper that applies auth headers, base URL prefixes, and safe response handling.
 *
 * @param {string} endpoint - Path relative to API_BASE (e.g. "/auth/login") or absolute URL
 * @param {RequestInit} [options] - Standard fetch options
 * @param {string} [contextMessage] - Friendly action name for error reporting
 */
export async function apiFetch(endpoint, options = {}, contextMessage = 'API Request') {
  // If static hosting without backend, fail early with clear diagnosis before making broken fetch
  if (isStaticHostingWithoutBackend() && !endpoint.startsWith('http')) {
    throw new Error(
      'CrimeSense Backend Unreachable: The application is running on static hosting without a configured backend API URL (VITE_API_URL is missing). Please set VITE_API_URL to point to your Flask server.'
    );
  }

  const token =
    typeof localStorage !== 'undefined'
      ? localStorage.getItem('crimesense_token') ||
        localStorage.getItem('token') ||
        localStorage.getItem('authToken')
      : null;

  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const url = endpoint.startsWith('http://') || endpoint.startsWith('https://')
    ? endpoint
    : endpoint.startsWith('/api')
      ? `${API_BASE_URL}${endpoint}`
      : `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (netErr) {
    // Network or CORS failure
    const hostHint = API_BASE_URL || API_BASE;
    throw new Error(
      `Cannot connect to CrimeSense backend at ${hostHint}. Please ensure the Flask server is running and accessible. (${netErr.message})`
    );
  }

  return handleApiResponse(response, contextMessage);
}
