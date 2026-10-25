import { authService } from './authService';

import { API_BASE } from './apiConfig';

export const savedPlacesService = {
  /**
   * Fetch user's saved locations, re-evaluating risk zones live on load.
   */
  async getSavedPlaces(reEvaluate = true) {
    const res = await fetch(`${API_BASE}/user/saved-locations?re_evaluate=${reEvaluate}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to fetch saved places');
    }
    return data.locations || [];
  },

  /**
   * Save a new destination with label, address, coordinates, and optional pin.
   */
  async addSavedPlace({ label, address, latitude, longitude, is_pinned = false }) {
    const res = await fetch(`${API_BASE}/user/saved-locations`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ label, address, latitude, longitude, is_pinned }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to save place');
    }
    return data;
  },

  /**
   * Rename or update saved place.
   */
  async updateSavedPlace(id, { label, address, is_pinned }) {
    const res = await fetch(`${API_BASE}/user/saved-locations/${id}`, {
      method: 'PUT',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ label, address, is_pinned }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to update place');
    }
    return data;
  },

  /**
   * Delete a saved place.
   */
  async deleteSavedPlace(id) {
    const res = await fetch(`${API_BASE}/user/saved-locations/${id}`, {
      method: 'DELETE',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to delete place');
    }
    return data;
  },

  /**
   * Create a CrimeSense shareable link (/s/<token>).
   */
  async createShareLink({
    latitude,
    longitude,
    accuracy,
    label,
    address,
    zone,
    is_live = false,
    expiry_hours = 1,
  }) {
    const res = await fetch(`${API_BASE}/share`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({
        latitude,
        longitude,
        accuracy,
        label,
        address,
        zone,
        is_live,
        expiry_hours,
      }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to generate share link');
    }
    return data;
  },

  /**
   * Public: Fetch shared location data without authentication.
   */
  async getPublicShareLocation(token) {
    const res = await fetch(`${API_BASE}/share/${token}`, {
      method: 'GET',
    });
    const data = await res.json();
    if (!res.ok && res.status !== 200) {
      throw new Error(data.error || 'Failed to load shared location');
    }
    return data;
  },

  /**
   * Revoke a shared link ("Stop Sharing").
   */
  async revokeShareLink(token) {
    const res = await fetch(`${API_BASE}/share/${token}/revoke`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to revoke link');
    }
    return data;
  },
};
