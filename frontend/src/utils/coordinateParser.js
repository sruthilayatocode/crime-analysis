/**
 * coordinateParser.js
 * ===================
 * Helper functions to parse various location input formats:
 * - Decimal: "12.9165, 79.1325" or "12.9165 79.1325"
 * - Directional: "12.9165N 79.1325E" or "12.9165 N, 79.1325 E"
 * - Plus Codes: "7M24WX88+22" or "WX88+22 Vellore"
 */

const OLC_ALPHABET = '23456789CFGHJMPQRVWX';

/**
 * Decode a full or recovery-based Open Location Code (Plus Code)
 */
export function decodePlusCode(rawCode, refLat = 12.9165, refLng = 79.1325) {
  if (!rawCode || typeof rawCode !== 'string') return null;

  // Extract the plus code part (e.g. from "7M24WX88+22" or "WX88+22, Vellore")
  const plusMatch = rawCode.match(/([23456789CFGHJMPQRVWX]{4,8}\+[23456789CFGHJMPQRVWX]{2,3})/i);
  if (!plusMatch) return null;

  let code = plusMatch[1].toUpperCase();

  // If short code (e.g. 4 or 6 chars before +), pad using reference coordinate prefix
  if (code.indexOf('+') < 8) {
    const missingChars = 8 - code.indexOf('+');
    // Approximate reference prefix for Vellore/Tamil Nadu area is '7M24' or similar
    const fullRefPrefix = encodeRefPrefix(refLat, refLng, missingChars);
    code = fullRefPrefix + code;
  }

  const clean = code.replace('+', '').trim();
  if (clean.length < 8) return null;

  let lat = -90.0;
  let lng = -180.0;
  let latVal = 20.0;
  let lngVal = 20.0;

  for (let i = 0; i < Math.min(clean.length, 10); i += 2) {
    const latChar = clean[i];
    const lngChar = clean[i + 1];
    const latIdx = OLC_ALPHABET.indexOf(latChar);
    const lngIdx = OLC_ALPHABET.indexOf(lngChar);
    if (latIdx === -1 || lngIdx === -1) return null;

    lat += latIdx * latVal;
    lng += lngIdx * lngVal;
    latVal /= 20.0;
    lngVal /= 20.0;
  }

  // Center coordinate
  lat += (latVal * 20.0) / 2.0;
  lng += (lngVal * 20.0) / 2.0;

  return {
    lat: Number(lat.toFixed(6)),
    lng: Number(lng.toFixed(6)),
    type: 'plus_code',
    formatted: `Plus Code (${code})`,
  };
}

function encodeRefPrefix(lat, lng, numChars) {
  let l = lat + 90.0;
  let n = lng + 180.0;
  let res = '';
  let step = 20.0;

  for (let i = 0; i < numChars; i += 2) {
    const latIdx = Math.floor(l / step);
    const lngIdx = Math.floor(n / step);
    l -= latIdx * step;
    n -= lngIdx * step;
    step /= 20.0;
    res += OLC_ALPHABET[latIdx] + OLC_ALPHABET[lngIdx];
  }
  return res.slice(0, numChars);
}

/**
 * Parse any coordinate string:
 * - 12.9165, 79.1325
 * - 12.9165 79.1325
 * - 12.9165N 79.1325E
 * - 12.9165 N, 79.1325 E
 * - 12.9165S 79.1325W
 */
export function parseCoordinates(query) {
  if (!query || typeof query !== 'string') return null;
  const text = query.trim();

  // Try Plus Code first if '+' is present
  if (text.includes('+')) {
    const plusRes = decodePlusCode(text);
    if (plusRes) return plusRes;
  }

  // 1. Directional coordinates regex: e.g. 12.9165N, 79.1325E or 12.9165 N 79.1325 E
  const dirMatch = text.match(
    /^([0-9.]+)\s*([NSns])\s*[, ]\s*([0-9.]+)\s*([EWew])$/
  );
  if (dirMatch) {
    let lat = parseFloat(dirMatch[1]);
    const latDir = dirMatch[2].toUpperCase();
    let lng = parseFloat(dirMatch[3]);
    const lngDir = dirMatch[4].toUpperCase();

    if (latDir === 'S') lat = -lat;
    if (lngDir === 'W') lng = -lng;

    if (isValidLatLng(lat, lng)) {
      return {
        lat: Number(lat.toFixed(6)),
        lng: Number(lng.toFixed(6)),
        type: 'coordinate',
        formatted: `${Math.abs(lat).toFixed(4)}°${latDir}, ${Math.abs(lng).toFixed(4)}°${lngDir}`,
      };
    }
  }

  // 2. Decimal coordinates: e.g. 12.9165, 79.1325 or -12.9165 79.1325
  const decMatch = text.match(
    /^([-+]?[0-9]*\.?[0-9]+)\s*[, ]\s*([-+]?[0-9]*\.?[0-9]+)$/
  );
  if (decMatch) {
    const lat = parseFloat(decMatch[1]);
    const lng = parseFloat(decMatch[2]);
    if (isValidLatLng(lat, lng)) {
      return {
        lat: Number(lat.toFixed(6)),
        lng: Number(lng.toFixed(6)),
        type: 'coordinate',
        formatted: `${lat.toFixed(4)}, ${lng.toFixed(4)}`,
      };
    }
  }

  return null;
}

export function isValidLatLng(lat, lng) {
  return (
    !isNaN(lat) &&
    !isNaN(lng) &&
    lat >= -90.0 &&
    lat <= 90.0 &&
    lng >= -180.0 &&
    lng <= 180.0
  );
}

/**
 * Calculate distance in meters between two lat/lng coordinates (Haversine)
 */
export function haversineDistanceMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000.0;
  const toRad = (deg) => (deg * Math.PI) / 180.0;

  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}
