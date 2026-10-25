import { authService } from './authService';

import { API_BASE } from './apiConfig';

export const adminService = {
  /**
   * 1. Overview & KPIs
   */
  async getOverview() {
    const res = await fetch(`${API_BASE}/admin/overview`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to fetch admin overview');
    }
    return data;
  },

  /**
   * 2. Crime Incidents CRUD, Pagination, Filters & Search
   */
  async getCrimes({
    page = 1,
    per_page = 20,
    q = '',
    crime_type = '',
    severity = '',
    district = '',
    start_date = '',
    end_date = '',
    sort_by = 'published_date',
    order = 'desc',
  } = {}) {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(per_page),
      sort_by,
      order,
    });
    if (q) params.append('q', q);
    if (crime_type && crime_type !== 'all') params.append('crime_type', crime_type);
    if (severity && severity !== 'all') params.append('severity', severity);
    if (district && district !== 'all') params.append('district', district);
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);

    const res = await fetch(`${API_BASE}/admin/crimes?${params.toString()}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to fetch crime records');
    }
    return data;
  },

  async createCrime(crimeData) {
    const res = await fetch(`${API_BASE}/admin/crimes`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify(crimeData),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to create crime incident');
    }
    return data;
  },

  async updateCrime(id, crimeData) {
    const res = await fetch(`${API_BASE}/admin/crimes/${id}`, {
      method: 'PUT',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify(crimeData),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to update crime incident');
    }
    return data;
  },

  async deleteCrime(id) {
    const res = await fetch(`${API_BASE}/admin/crimes/${id}`, {
      method: 'DELETE',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to delete crime incident');
    }
    return data;
  },

  getExportCsvUrl(params = {}) {
    const query = new URLSearchParams(params).toString();
    const token = authService.getToken();
    return `${API_BASE}/admin/crimes/export?${query}&token=${token || ''}`;
  },

  async importCrimesCsv(file) {
    const formData = new FormData();
    formData.append('file', file);

    const token = authService.getToken();
    const res = await fetch(`${API_BASE}/admin/crimes/import`, {
      method: 'POST',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to import CSV');
    }
    return data;
  },

  /**
   * 3. History & Trends Analytics
   */
  async getHistoricalTrends(year = 'all') {
    const res = await fetch(`${API_BASE}/admin/analytics/trends?year=${year}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to load historical analytics');
    }
    return data;
  },

  /**
   * 4. Users Management
   */
  async getUsers({ page = 1, per_page = 20, q = '', role = 'all' } = {}) {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(per_page),
    });
    if (q) params.append('q', q);
    if (role && role !== 'all') params.append('role', role);

    const res = await fetch(`${API_BASE}/admin/users?${params.toString()}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to fetch user list');
    }
    return data;
  },

  async getUserDetail(userId) {
    const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to load user detail');
    }
    return data;
  },

  async changeUserRole(userId, role) {
    const res = await fetch(`${API_BASE}/admin/users/${userId}/role`, {
      method: 'PUT',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ role }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to update user role');
    }
    return data;
  },

  async toggleUserActive(userId, isActive) {
    const res = await fetch(`${API_BASE}/admin/users/${userId}/status`, {
      method: 'PUT',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ is_active: isActive }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to update user status');
    }
    return data;
  },

  async deleteUser(userId) {
    const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
      method: 'DELETE',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to delete user');
    }
    return data;
  },

  /**
   * 5. Live Map (Consent-Guarded)
   */
  async getLiveMapUsers() {
    const res = await fetch(`${API_BASE}/admin/live-map/users`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to fetch live location stream');
    }
    return data;
  },

  /**
   * 6. Alerts & SOS Feed
   */
  async getSOSFeed({ status = 'all', type = 'all', start_date = '', end_date = '' } = {}) {
    const params = new URLSearchParams();
    if (status && status !== 'all') params.append('status', status);
    if (type && type !== 'all') params.append('type', type);
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);

    const res = await fetch(`${API_BASE}/admin/sos-feed?${params.toString()}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to fetch SOS alerts');
    }
    return data;
  },

  async resolveSOSEvent(eventId, notes = '') {
    const res = await fetch(`${API_BASE}/admin/sos-events/${eventId}/resolve`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ notes }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to resolve SOS event');
    }
    return data;
  },

  async addSOSNotes(eventId, notes) {
    const res = await fetch(`${API_BASE}/admin/sos-events/${eventId}/notes`, {
      method: 'PUT',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ notes }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to attach notes');
    }
    return data;
  },

  /**
   * 7. Audit Logs
   */
  async getAuditLogs({ page = 1, per_page = 30, action = '', admin = '' } = {}) {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(per_page),
    });
    if (action && action !== 'all') params.append('action', action);
    if (admin) params.append('admin', admin);

    const res = await fetch(`${API_BASE}/admin/audit-logs?${params.toString()}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || data.error || 'Failed to fetch audit logs');
    }
    return data;
  },
};
