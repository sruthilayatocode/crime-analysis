import { apiFetch, API_BASE } from './apiConfig';

export const savedPlacesService = {
  /**
   * Fetch user's saved locations, re-evaluating risk zones live on load.
   */
  async getSavedPlaces(reEvaluate = true) {
    const data = await apiFetch(
      `/user/saved-locations?re_evaluate=${reEvaluate}`,
      { method: 'GET' },
      'Fetch saved places'
    );
    return data.locations || [];
  },

  /**
   * Save a new destination with label, address, coordinates, and optional pin.
   */
  async addSavedPlace({ label, address, latitude, longitude, is_pinned = false }) {
    return apiFetch(
      '/user/saved-locations',
      {
        method: 'POST',
        body: JSON.stringify({ label, address, latitude, longitude, is_pinned }),
      },
      'Save place'
    );
  },

  /**
   * Rename or update saved place.
   */
  async updateSavedPlace(id, { label, address, is_pinned }) {
    return apiFetch(
      `/user/saved-locations/${id}`,
      {
        method: 'PUT',
        body: JSON.stringify({ label, address, is_pinned }),
      },
      'Update place'
    );
  },

  /**
   * Delete a saved place.
   */
  async deleteSavedPlace(id) {
    return apiFetch(
      `/user/saved-locations/${id}`,
      { method: 'DELETE' },
      'Delete place'
    );
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
    return apiFetch(
      '/share',
      {
        method: 'POST',
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
      },
      'Generate share link'
    );
  },

  /**
   * Public: Fetch shared location data without authentication.
   */
  async getPublicShareLocation(token) {
    return apiFetch(
      `/share/${token}`,
      { method: 'GET' },
      'Load shared location'
    );
  },

  /**
   * Revoke a shared link ("Stop Sharing").
   */
  async revokeShareLink(token) {
    return apiFetch(
      `/share/${token}/revoke`,
      { method: 'POST' },
      'Revoke share link'
    );
  },
};
export { API_BASE };
