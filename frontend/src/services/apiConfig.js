/**
 * apiConfig.js
 * Centralized API configuration for CrimeSense frontend.
 * Seamlessly resolves backend URLs in local dev and production on Firebase Hosting.
 */

const rawUrl = (import.meta.env.VITE_API_URL || '').trim();
const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();

// Base host without trailing slash and without trailing /api (e.g., "https://my-backend.onrender.com")
export const API_BASE_URL = rawUrl
  ? rawUrl.replace(/\/+$/, '').replace(/\/api$/, '')
  : rawBaseUrl
    ? rawBaseUrl.replace(/\/+$/, '').replace(/\/api$/, '')
    : '';

// API route base with /api (e.g., "https://my-backend.onrender.com/api" or "/api")
export const API_BASE = rawBaseUrl
  ? rawBaseUrl.replace(/\/+$/, '')
  : rawUrl
    ? `${rawUrl.replace(/\/+$/, '')}/api`
    : '/api';
