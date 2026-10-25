import { API_BASE } from './apiConfig';

export const authService = {
  getToken() {
    return localStorage.getItem('crimesense_token') || localStorage.getItem('token') || localStorage.getItem('authToken');
  },

  setToken(token) {
    if (token) {
      localStorage.setItem('crimesense_token', token);
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('crimesense_token');
      localStorage.removeItem('token');
      localStorage.removeItem('authToken');
    }
  },

  getAuthHeaders() {
    const token = this.getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  },

  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || 'Login failed');
    }
    if (data.token) this.setToken(data.token);
    return data;
  },

  async signup(name, email, password) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || 'Signup failed');
    }
    if (data.token) this.setToken(data.token);
    return data;
  },

  async googleAuth(credential, details = null) {
    const body = credential ? { credential } : details;
    const res = await fetch(`${API_BASE}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || 'Google authentication failed');
    }
    if (data.token) this.setToken(data.token);
    return data;
  },

  async getMe() {
    const token = this.getToken();
    if (!token) return null;
    const res = await fetch(`${API_BASE}/auth/me`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    if (!res.ok) {
      this.setToken(null);
      return null;
    }
    const data = await res.json();
    return data.user || null;
  },

  async logout() {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });
    } catch {
      // Ignore errors on logout
    } finally {
      this.setToken(null);
    }
  },

  async updateProfile({ name, avatar_url }) {
    const res = await fetch(`${API_BASE}/user/profile`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ name, avatar_url }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to update profile');
    }
    return data;
  },

  async deleteLocationHistory() {
    const res = await fetch(`${API_BASE}/user/locations`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to delete location history');
    }
    return data;
  },

  async deleteAccount() {
    const res = await fetch(`${API_BASE}/user/account`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to delete account');
    }
    this.setToken(null);
    return data;
  },

  async getSettings() {
    const res = await fetch(`${API_BASE}/user/settings`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to fetch settings');
    }
    return data.settings;
  },

  async updateSettings(settings) {
    const res = await fetch(`${API_BASE}/user/settings`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(settings),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to update settings');
    }
    return data.settings;
  },

  async verifyEmail(token) {
    const res = await fetch(`${API_BASE}/auth/verify-email?token=${encodeURIComponent(token)}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || 'Email verification failed');
    }
    return data;
  },

  async resendVerification(email) {
    const res = await fetch(`${API_BASE}/auth/resend-verification`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || 'Failed to resend verification email');
    }
    return data;
  },

  async forgotPassword(email) {
    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || 'Failed to request password reset');
    }
    return data;
  },

  async resetPassword(token, password) {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, password }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || 'Failed to reset password');
    }
    return data;
  },
};
