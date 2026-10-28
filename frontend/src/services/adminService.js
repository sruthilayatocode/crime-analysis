import { authService } from './authService';
import { API_BASE, apiFetch } from './apiConfig';
import fallbackOverview from '../data/fallbackOverview.json';
import fallbackCrimes from '../data/fallbackCrimes.json';

export const adminService = {
  /**
   * 1. Overview & KPIs
   */
  async getOverview() {
    try {
      return await apiFetch('/admin/overview', { method: 'GET' }, 'Fetch admin overview');
    } catch (err) {
      console.warn('[adminService] Using fallback overview stats:', err.message);
      return fallbackOverview;
    }
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

    try {
      return await apiFetch(`/admin/crimes?${params.toString()}`, { method: 'GET' }, 'Fetch crime records');
    } catch (err) {
      console.warn('[adminService] Using fallback crime list:', err.message);
      let list = [...fallbackCrimes];
      if (q) {
        const query = q.toLowerCase();
        list = list.filter((c) => (c.crime_type || '').toLowerCase().includes(query) || (c.location_name || '').toLowerCase().includes(query));
      }
      if (crime_type && crime_type !== 'all') {
        list = list.filter((c) => (c.crime_type || '').toLowerCase() === crime_type.toLowerCase());
      }
      const total = list.length;
      const start = (page - 1) * per_page;
      const paged = list.slice(start, start + per_page);
      return {
        success: true,
        data: paged,
        count: total,
        total,
        page,
        per_page,
        total_pages: Math.ceil(total / per_page) || 1,
      };
    }
  },

  async createCrime(crimeData) {
    return apiFetch(
      '/admin/crimes',
      {
        method: 'POST',
        body: JSON.stringify(crimeData),
      },
      'Create crime incident'
    );
  },

  async updateCrime(id, crimeData) {
    return apiFetch(
      `/admin/crimes/${id}`,
      {
        method: 'PUT',
        body: JSON.stringify(crimeData),
      },
      'Update crime incident'
    );
  },

  async deleteCrime(id) {
    return apiFetch(
      `/admin/crimes/${id}`,
      { method: 'DELETE' },
      'Delete crime incident'
    );
  },

  /**
   * Pending Citizen Incident Triage
   */
  async getPendingCrimes() {
    try {
      return await apiFetch('/admin/crimes/pending', { method: 'GET' }, 'Fetch pending reports');
    } catch {
      return { success: true, count: 0, data: [] };
    }
  },

  async approveCrime(id, notes = '') {
    return apiFetch(
      `/admin/crimes/${id}/approve`,
      {
        method: 'PATCH',
        body: JSON.stringify({ admin_notes: notes }),
      },
      'Approve incident report'
    );
  },

  async rejectCrime(id, notes = '') {
    return apiFetch(
      `/admin/crimes/${id}/reject`,
      {
        method: 'PATCH',
        body: JSON.stringify({ admin_notes: notes }),
      },
      'Reject incident report'
    );
  },

  getExportCsvUrl(params = {}) {
    const query = new URLSearchParams(params).toString();
    const token = authService.getToken();
    return `${API_BASE}/admin/crimes/export?${query}&token=${token || ''}`;
  },

  async importCrimesCsv(file) {
    const formData = new FormData();
    formData.append('file', file);

    return apiFetch(
      '/admin/crimes/import',
      {
        method: 'POST',
        body: formData,
      },
      'Import CSV'
    );
  },

  /**
   * 3. History & Trends Analytics
   */
  async getHistoricalTrends(year = 'all') {
    return apiFetch(
      `/admin/analytics/trends?year=${year}`,
      { method: 'GET' },
      'Load historical analytics'
    );
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

    return apiFetch(`/admin/users?${params.toString()}`, { method: 'GET' }, 'Fetch user list');
  },

  async getUserDetail(userId) {
    return apiFetch(`/admin/users/${userId}`, { method: 'GET' }, 'Load user detail');
  },

  async changeUserRole(userId, role) {
    return apiFetch(
      `/admin/users/${userId}/role`,
      {
        method: 'PUT',
        body: JSON.stringify({ role }),
      },
      'Update user role'
    );
  },

  async toggleUserActive(userId, isActive) {
    return apiFetch(
      `/admin/users/${userId}/status`,
      {
        method: 'PUT',
        body: JSON.stringify({ is_active: isActive }),
      },
      'Update user status'
    );
  },

  async deleteUser(userId) {
    return apiFetch(
      `/admin/users/${userId}`,
      { method: 'DELETE' },
      'Delete user'
    );
  },

  /**
   * 5. Live Map (Consent-Guarded)
   */
  async getLiveMapUsers() {
    return apiFetch('/admin/live-map/users', { method: 'GET' }, 'Fetch live location stream');
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

    return apiFetch(`/admin/sos-feed?${params.toString()}`, { method: 'GET' }, 'Fetch SOS alerts');
  },

  async resolveSOSEvent(eventId, notes = '') {
    return apiFetch(
      `/admin/sos-events/${eventId}/resolve`,
      {
        method: 'POST',
        body: JSON.stringify({ notes }),
      },
      'Resolve SOS event'
    );
  },

  async addSOSNotes(eventId, notes) {
    return apiFetch(
      `/admin/sos-events/${eventId}/notes`,
      {
        method: 'PUT',
        body: JSON.stringify({ notes }),
      },
      'Attach notes'
    );
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

    return apiFetch(`/admin/audit-logs?${params.toString()}`, { method: 'GET' }, 'Fetch audit logs');
  },
};
