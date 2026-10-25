/**
 * zoneService.js
 * ==============
 * Client service for calling CrimeSense Zone Risk Analysis API (/api/zone),
 * resolving search queries, and managing local saved locations & emergency contacts.
 */

export { API_BASE_URL } from './apiConfig';

// Pre-configured Vellore localities for instant search suggestions
export const VELLORE_LOCALITY_PRESETS = [
  { name: 'Katpadi', lat: 12.9806, lng: 79.1368, desc: 'Katpadi Junction & Area' },
  { name: 'Vellore Fort', lat: 12.9227, lng: 79.132, desc: 'Historic Fort & Central Vellore' },
  { name: 'Sathuvachari', lat: 12.926, lng: 79.168, desc: 'Sathuvachari Collectorate Area' },
  { name: 'Bagayam', lat: 12.879, lng: 79.132, desc: 'Bagayam & CMC Hospital' },
  { name: 'Thorapadi', lat: 12.898, lng: 79.124, desc: 'Thorapadi Area' },
  { name: 'Gudiyattam', lat: 12.9461, lng: 78.8686, desc: 'Gudiyattam Town' },
  { name: 'Ranipet', lat: 12.9284, lng: 79.333, desc: 'Ranipet Industrial Hub' },
  { name: 'Arcot', lat: 12.9048, lng: 79.3339, desc: 'Arcot Town' },
  { name: 'Ambur', lat: 12.7906, lng: 78.7166, desc: 'Ambur Area' },
  { name: 'Pallikonda', lat: 12.9055, lng: 78.9409, desc: 'Pallikonda Toll & Highway' },
];

/**
 * Fetch zone risk evaluation from backend /api/zone.
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @param {number} radius - Search radius in meters (default 1000)
 */
export async function fetchZoneRisk(lat, lng, radius = 1000) {
  const params = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    radius: String(radius),
  });

  const response = await fetch(`${API_BASE_URL}/api/zone?${params.toString()}`);
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.error || `Failed to fetch zone data: ${response.status}`);
  }

  return response.json();
}

/**
 * Search localities either via local presets or OpenStreetMap Nominatim.
 * @param {string} query
 */
export async function searchLocalities(query) {
  if (!query || query.trim().length < 2) return [];
  const q = query.trim().toLowerCase();

  // Match presets first
  const presetMatches = VELLORE_LOCALITY_PRESETS.filter(
    (item) => item.name.toLowerCase().includes(q) || item.desc.toLowerCase().includes(q)
  );

  if (presetMatches.length > 0) {
    return presetMatches;
  }

  // Fallback to OpenStreetMap Nominatim for general places
  try {
    const nominatimUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
      query + ', Tamil Nadu'
    )}&limit=5`;
    const res = await fetch(nominatimUrl, {
      headers: {
        'Accept-Language': 'en',
      },
    });
    if (!res.ok) return presetMatches;
    const data = await res.json();
    return data.map((item) => ({
      name: item.display_name.split(',')[0],
      desc: item.display_name,
      lat: parseFloat(item.lat),
      lng: parseFloat(item.lon),
    }));
  } catch (err) {
    return presetMatches;
  }
}

/**
 * Saved locations stored in localStorage
 */
const SAVED_LOCATIONS_KEY = 'crimesense_user_saved_locations';

export function getSavedLocations() {
  try {
    const raw = localStorage.getItem(SAVED_LOCATIONS_KEY);
    if (!raw) {
      return [];
    }
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveLocation(location) {
  const existing = getSavedLocations();
  const newItem = {
    id: 'loc-' + Date.now(),
    createdAt: new Date().toISOString(),
    ...location,
  };
  const updated = [newItem, ...existing.filter((item) => item.id !== newItem.id)];
  localStorage.setItem(SAVED_LOCATIONS_KEY, JSON.stringify(updated));
  return updated;
}

export function deleteSavedLocation(id) {
  const existing = getSavedLocations();
  const updated = existing.filter((item) => item.id !== id);
  localStorage.setItem(SAVED_LOCATIONS_KEY, JSON.stringify(updated));
  return updated;
}

/**
 * Emergency contacts in localStorage
 */
const EMERGENCY_CONTACTS_KEY = 'crimesense_emergency_contacts';

export function getEmergencyContacts() {
  try {
    const raw = localStorage.getItem(EMERGENCY_CONTACTS_KEY);
    if (!raw) {
      const defaults = [
        { id: 'ec-1', name: 'Primary Contact (Mom / Dad)', phone: '+91 98765 43210', relation: 'Family' },
        { id: 'ec-2', name: 'Emergency Buddy', phone: '+91 91234 56789', relation: 'Friend' },
      ];
      localStorage.setItem(EMERGENCY_CONTACTS_KEY, JSON.stringify(defaults));
      return defaults;
    }
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveEmergencyContact(contact) {
  const existing = getEmergencyContacts();
  const newItem = {
    id: 'ec-' + Date.now(),
    ...contact,
  };
  const updated = [newItem, ...existing];
  localStorage.setItem(EMERGENCY_CONTACTS_KEY, JSON.stringify(updated));
  return updated;
}

export function deleteEmergencyContact(id) {
  const existing = getEmergencyContacts();
  const updated = existing.filter((item) => item.id !== id);
  localStorage.setItem(EMERGENCY_CONTACTS_KEY, JSON.stringify(updated));
  return updated;
}
