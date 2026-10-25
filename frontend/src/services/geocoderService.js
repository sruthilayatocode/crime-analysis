/**
 * geocoderService.js
 * ===================
 * Swappable geocoder service supporting Nominatim (OpenStreetMap),
 * Google, or Mapbox via VITE_GEOCODER_PROVIDER.
 *
 * Biased to Vellore / Tamil Nadu with countrycodes=in, street-level detail,
 * 400ms debounce, and recent searches management.
 */

import { parseCoordinates } from '../utils/coordinateParser';
import { VELLORE_LOCALITY_PRESETS } from './zoneService';

const GEOCODER_PROVIDER = import.meta.env.VITE_GEOCODER_PROVIDER || 'nominatim';
const RECENT_SEARCHES_KEY = 'crimesense_recent_searches';

// Vellore region viewbox (min_lon, max_lat, max_lon, min_lat)
const VELLORE_VIEWBOX = '78.5,13.3,79.6,12.5';

/**
 * Geocode user query with fallback to coordinate parsing and local presets.
 */
export async function geocodeAddress(query) {
  if (!query || typeof query !== 'string') return [];
  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  // 1. Check if the query is an exact coordinate or Plus Code
  const parsedCoord = parseCoordinates(trimmed);
  if (parsedCoord) {
    return [
      {
        id: `coord-${parsedCoord.lat}-${parsedCoord.lng}`,
        title: parsedCoord.formatted,
        subtitle: `Direct Coordinates (${parsedCoord.lat}, ${parsedCoord.lng})`,
        lat: parsedCoord.lat,
        lng: parsedCoord.lng,
        isCoordinate: true,
        type: parsedCoord.type,
      },
    ];
  }

  // 2. Execute provider geocoding
  try {
    if (GEOCODER_PROVIDER === 'google') {
      return await geocodeGoogle(trimmed);
    } else if (GEOCODER_PROVIDER === 'mapbox') {
      return await geocodeMapbox(trimmed);
    } else {
      return await geocodeNominatim(trimmed);
    }
  } catch (err) {
    console.warn(`[Geocoder] Provider (${GEOCODER_PROVIDER}) error:`, err);
    return [];
  }
}

/**
 * OpenStreetMap Nominatim Provider
 */
async function geocodeNominatim(query, isRetry = false) {
  const url = new URL('https://nominatim.openstreetmap.org/search');
  url.searchParams.set('q', query);
  url.searchParams.set('format', 'json');
  url.searchParams.set('countrycodes', 'in');
  url.searchParams.set('viewbox', VELLORE_VIEWBOX);
  url.searchParams.set('bounded', '0'); // Biased towards viewbox without strictly excluding
  url.searchParams.set('addressdetails', '1');
  url.searchParams.set('limit', '7');

  const response = await fetch(url.toString(), {
    headers: {
      'Accept': 'application/json',
      'Accept-Language': 'en',
      'User-Agent': 'CrimeSense-SafetyApp/1.0 (crimesense@safety.org)',
    },
  });

  if (response.status === 429) {
    if (!isRetry) {
      // Single retry after 1 s for transient rate-limit bursts
      await new Promise((r) => setTimeout(r, 1000));
      return geocodeNominatim(query, true);
    }
    console.warn('[Geocoder] Nominatim rate limit (429) hit.');
    return [];
  }

  if (!response.ok) {
    throw new Error(`Nominatim returned status ${response.status}`);
  }

  const data = await response.json();
  if (!Array.isArray(data) || data.length === 0) {
    return [];
  }

  return data.map((item) => formatNominatimResult(item));
}


/**
 * Extract clean street-level title and contextual subtitle from Nominatim result
 */
function formatNominatimResult(item) {
  const addr = item.address || {};

  // Build primary title: landmark / amenity / road / suburb
  const titleParts = [
    item.namedetails?.name ||
      addr.amenity ||
      addr.building ||
      addr.road ||
      addr.suburb ||
      addr.neighbourhood ||
      item.display_name.split(',')[0],
  ].filter(Boolean);

  const title = titleParts[0] || 'Location';

  // Build street-level contextual subtitle
  const subtitleParts = [
    addr.road && addr.road !== title ? addr.road : null,
    addr.suburb && addr.suburb !== title ? addr.suburb : null,
    addr.city || addr.town || addr.village || addr.county || 'Vellore',
    addr.postcode,
    addr.state || 'Tamil Nadu',
  ].filter(Boolean);

  const subtitle = subtitleParts.join(', ') || item.display_name;

  return {
    id: `osm-${item.place_id || item.osm_id}`,
    title,
    subtitle,
    lat: parseFloat(item.lat),
    lng: parseFloat(item.lon),
    raw: item,
  };
}

/**
 * Google Geocoding Provider placeholder (activated via VITE_GEOCODER_PROVIDER=google)
 */
async function geocodeGoogle(query) {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_KEY;
  if (!apiKey) return geocodeNominatim(query);

  const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(
    query
  )}&components=country:IN&key=${apiKey}`;
  const res = await fetch(url);
  const data = await res.json();

  if (!data.results || data.results.length === 0) return filterPresets(query);

  return data.results.map((item, idx) => ({
    id: `google-${idx}`,
    title: item.address_components[0]?.long_name || item.formatted_address.split(',')[0],
    subtitle: item.formatted_address,
    lat: item.geometry.location.lat,
    lng: item.geometry.location.lng,
  }));
}

/**
 * Mapbox Geocoding Provider placeholder (activated via VITE_GEOCODER_PROVIDER=mapbox)
 */
async function geocodeMapbox(query) {
  const token = import.meta.env.VITE_MAPBOX_TOKEN;
  if (!token) return geocodeNominatim(query);

  const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
    query
  )}.json?country=in&proximity=79.1325,12.9165&access_token=${token}`;
  const res = await fetch(url);
  const data = await res.json();

  if (!data.features || data.features.length === 0) return filterPresets(query);

  return data.features.map((item) => ({
    id: `mapbox-${item.id}`,
    title: item.text,
    subtitle: item.place_name,
    lat: item.center[1],
    lng: item.center[0],
  }));
}

/**
 * Filter local Vellore locality presets
 */
function filterPresets(query) {
  const q = query.toLowerCase();
  return VELLORE_LOCALITY_PRESETS.filter(
    (p) => p.name.toLowerCase().includes(q) || p.desc.toLowerCase().includes(q)
  ).map((p, idx) => ({
    id: `preset-${idx}`,
    title: p.name,
    subtitle: `${p.desc}, Vellore`,
    lat: p.lat,
    lng: p.lng,
  }));
}

// --------------------------------------------------------------------------- //
// Recent Searches (keep last 10 locally)
// --------------------------------------------------------------------------- //

export function getRecentSearches() {
  try {
    const raw = localStorage.getItem(RECENT_SEARCHES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.slice(0, 10) : [];
  } catch {
    return [];
  }
}

export function saveRecentSearch(item) {
  if (!item || !item.title || !item.lat || !item.lng) return;
  try {
    const current = getRecentSearches();
    const cleanItem = {
      id: item.id || `search-${Date.now()}`,
      title: item.title,
      subtitle: item.subtitle || '',
      lat: item.lat,
      lng: item.lng,
      timestamp: Date.now(),
    };
    // De-duplicate by title / coords
    const filtered = current.filter(
      (c) =>
        c.title.toLowerCase() !== cleanItem.title.toLowerCase() &&
        (Math.abs(c.lat - cleanItem.lat) > 0.0001 || Math.abs(c.lng - cleanItem.lng) > 0.0001)
    );
    const updated = [cleanItem, ...filtered].slice(0, 10);
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
    return updated;
  } catch {
    return [];
  }
}

export function removeRecentSearch(id) {
  try {
    const current = getRecentSearches();
    const updated = current.filter((item) => item.id !== id);
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
    return updated;
  } catch {
    return [];
  }
}

export function clearRecentSearches() {
  try {
    localStorage.removeItem(RECENT_SEARCHES_KEY);
    return [];
  } catch {
    return [];
  }
}
