import { API_BASE, apiFetch } from './apiConfig';

export const authService = {
  getToken() {
    return (
      localStorage.getItem('crimesense_token') ||
      localStorage.getItem('token') ||
      localStorage.getItem('authToken')
    );
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
    const data = await apiFetch(
      '/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      },
      'Login'
    );
    if (data.token) this.setToken(data.token);
    return data;
  },

  async signup(name, email, password) {
    const data = await apiFetch(
      '/auth/signup',
      {
        method: 'POST',
        body: JSON.stringify({ name, email, password }),
      },
      'Signup'
    );
    if (data.token) this.setToken(data.token);
    return data;
  },

  async googleAuth(credential, details = null) {
    const body = credential ? { credential } : details;
    const data = await apiFetch(
      '/auth/google',
      {
        method: 'POST',
        body: JSON.stringify(body),
      },
      'Google authentication'
    );
    if (data.token) this.setToken(data.token);
    return data;
  },

  async getMe() {
    const token = this.getToken();
    if (!token) return null;
    try {
      const data = await apiFetch('/auth/me', { method: 'GET' }, 'Session verification');
      return data.user || null;
    } catch {
      // Clear expired or invalid token
      this.setToken(null);
      return null;
    }
  },

  async logout() {
    try {
      await apiFetch('/auth/logout', { method: 'POST' }, 'Logout');
    } catch {
      // Ignore errors on logout
    } finally {
      this.setToken(null);
    }
  },

  async updateProfile({ name, avatar_url }) {
    return apiFetch(
      '/user/profile',
      {
        method: 'PUT',
        body: JSON.stringify({ name, avatar_url }),
      },
      'Profile update'
    );
  },

  async deleteLocationHistory() {
    return apiFetch(
      '/user/locations',
      { method: 'DELETE' },
      'Delete location history'
    );
  },

  async deleteAccount() {
    const data = await apiFetch(
      '/user/account',
      { method: 'DELETE' },
      'Delete account'
    );
    this.setToken(null);
    return data;
  },

  async getSettings() {
    const data = await apiFetch(
      '/user/settings',
      { method: 'GET' },
      'Fetch settings'
    );
    return data.settings;
  },

  async updateSettings(settings) {
    const data = await apiFetch(
      '/user/settings',
      {
        method: 'POST',
        body: JSON.stringify(settings),
      },
      'Update settings'
    );
    return data.settings;
  },

  async verifyEmail(token) {
    return apiFetch(
      `/auth/verify-email?token=${encodeURIComponent(token)}`,
      { method: 'GET' },
      'Email verification'
    );
  },

  async resendVerification(email) {
    return apiFetch(
      '/auth/resend-verification',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
      },
      'Resend verification'
    );
  },

  async forgotPassword(email) {
    return apiFetch(
      '/auth/forgot-password',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
      },
      'Password reset request'
    );
  },

  async resetPassword(token, password) {
    return apiFetch(
      '/auth/reset-password',
      {
        method: 'POST',
        body: JSON.stringify({ token, password }),
      },
      'Reset password'
    );
  },
};
export { API_BASE };
