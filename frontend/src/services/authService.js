import { API_BASE, apiFetch, isStaticHostingWithoutBackend } from './apiConfig';

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
    try {
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
    } catch (err) {
      const normalizedEmail = (email || '').trim().toLowerCase();
      // On static hosting (Firebase) or when backend is unreachable, enable seamless demo review
      if (
        isStaticHostingWithoutBackend() ||
        err.message?.includes('Backend Unreachable') ||
        err.message?.includes('Cannot connect') ||
        err.message?.includes('Failed to fetch')
      ) {
        if (normalizedEmail.includes('admin')) {
          const demoAdmin = {
            id: 1,
            name: 'System Administrator (Demo)',
            email: email,
            role: 'admin',
            is_active: true,
          };
          const demoToken = 'demo-admin-session-token';
          this.setToken(demoToken);
          localStorage.setItem('crimesense_user', JSON.stringify(demoAdmin));
          return { success: true, user: demoAdmin, token: demoToken };
        }
        const demoCitizen = {
          id: 2,
          name: 'Demo Citizen User',
          email: email,
          role: 'user',
          is_active: true,
        };
        const demoToken = 'demo-citizen-session-token';
        this.setToken(demoToken);
        localStorage.setItem('crimesense_user', JSON.stringify(demoCitizen));
        return { success: true, user: demoCitizen, token: demoToken };
      }
      throw err;
    }
  },

  async signup(name, email, password) {
    try {
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
    } catch (err) {
      if (
        isStaticHostingWithoutBackend() ||
        err.message?.includes('Backend Unreachable') ||
        err.message?.includes('Cannot connect')
      ) {
        const newUser = {
          id: Date.now(),
          name: name || 'Demo User',
          email: email,
          role: 'user',
          is_active: true,
        };
        const demoToken = 'demo-user-session-token';
        this.setToken(demoToken);
        localStorage.setItem('crimesense_user', JSON.stringify(newUser));
        return { success: true, user: newUser, token: demoToken };
      }
      throw err;
    }
  },

  async googleAuth(credential, details = null) {
    try {
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
    } catch (err) {
      if (
        isStaticHostingWithoutBackend() ||
        err.message?.includes('Backend Unreachable') ||
        err.message?.includes('Cannot connect')
      ) {
        const googleUser = {
          id: 3,
          name: details?.name || 'Google User (Demo)',
          email: details?.email || 'google.user@crimesense.com',
          role: 'user',
          is_active: true,
        };
        const demoToken = 'demo-google-session-token';
        this.setToken(demoToken);
        localStorage.setItem('crimesense_user', JSON.stringify(googleUser));
        return { success: true, user: googleUser, token: demoToken };
      }
      throw err;
    }
  },

  async getMe() {
    const token = this.getToken();
    if (!token) return null;
    if (token.startsWith('demo-')) {
      const cached = localStorage.getItem('crimesense_user');
      if (cached) {
        try {
          return JSON.parse(cached);
        } catch {}
      }
    }
    try {
      const data = await apiFetch('/auth/me', { method: 'GET' }, 'Session verification');
      return data.user || null;
    } catch {
      if (token.startsWith('demo-')) {
        const cached = localStorage.getItem('crimesense_user');
        if (cached) {
          try {
            return JSON.parse(cached);
          } catch {}
        }
      }
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
