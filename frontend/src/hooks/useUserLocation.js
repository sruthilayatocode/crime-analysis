/**
 * useUserLocation.js
 * ==================
 * Hook to manage location permission, watchPosition tracking, and throttled
 * backend reporting (every 30 seconds or 50 meters moved).
 *
 * Fixes:
 * - Uses a ref for currentZone so the watchPosition callback always sees the
 *   latest value without restarting the watch on every zone change.
 * - watchPosition is started once and restarted only if the user explicitly
 *   grants permission again.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { haversineDistanceMeters } from '../utils/coordinateParser';

const PERMISSION_DECIDED_KEY = 'crimesense_location_permission_decided';
const DEFAULT_FALLBACK_COORDS = { lat: 12.9806, lng: 79.1368, accuracy: 25 }; // Katpadi, Vellore

export function useUserLocation(currentZone = 'GREEN') {
  const [coords, setCoords] = useState(() => {
    // Re-use previously cached coords (persisted to localStorage)
    const cached = localStorage.getItem('crimesense_cached_coords');
    if (cached) {
      try {
        return JSON.parse(cached);
      } catch { /* ignore */ }
    }
    return DEFAULT_FALLBACK_COORDS;
  });

  const [permissionState, setPermissionState] = useState(() => {
    return localStorage.getItem('crimesense_location_perm_state') || 'prompt';
  });

  const [showExplainer, setShowExplainer] = useState(() => {
    return !localStorage.getItem(PERMISSION_DECIDED_KEY);
  });

  const [isRequesting, setIsRequesting] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  // Throttling references
  const lastSentTimeRef = useRef(0);
  const lastSentCoordsRef = useRef(null);
  const watchIdRef = useRef(null);

  // Keep currentZone accessible inside the watchPosition callback without
  // requiring the watch to be restarted every time the zone changes.
  const currentZoneRef = useRef(currentZone);
  useEffect(() => {
    currentZoneRef.current = currentZone;
  }, [currentZone]);

  // ---------------------------------------------------------------------- //
  // Throttled location sender — silently fails if backend is unreachable
  // ---------------------------------------------------------------------- //
  const sendLocationToBackend = useCallback(async (lat, lng, accuracy) => {
    // Check if location access is turned off by user
    if (localStorage.getItem('crimesense_setting_location_access') === 'false') {
      return;
    }

    const now = Date.now();
    const timeSinceLast = (now - lastSentTimeRef.current) / 1000; // seconds

    let distanceMoved = 99_999;
    if (lastSentCoordsRef.current) {
      distanceMoved = haversineDistanceMeters(
        lastSentCoordsRef.current.lat,
        lastSentCoordsRef.current.lng,
        lat,
        lng
      );
    }

    // Throttle: at least 30 s elapsed OR moved ≥ 50 m
    if (timeSinceLast < 30 && distanceMoved < 50) return;

    lastSentTimeRef.current = now;
    lastSentCoordsRef.current = { lat, lng };

    try {
      const token = localStorage.getItem('crimesense_token');
      await fetch('/api/user/location', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          latitude: lat,
          longitude: lng,
          accuracy,
          zone: (currentZoneRef.current || 'green').toLowerCase(),
        }),
      });
    } catch {
      // Intentional silent failure — background GPS sync is best-effort
    }
  }, []); // stable — depends only on refs

  // ---------------------------------------------------------------------- //
  // Start watchPosition (high accuracy, persistent while page is open)
  // ---------------------------------------------------------------------- //
  const startWatching = useCallback(() => {
    // Check master toggle
    if (localStorage.getItem('crimesense_setting_location_access') === 'false') {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      return;
    }

    if (!navigator.geolocation) {
      setPermissionState('unavailable');
      setStatusMessage('Geolocation is not supported by your browser.');
      return;
    }

    // Clear any existing watch before starting a new one
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }

    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        const newCoords = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: Math.round(pos.coords.accuracy),
        };
        setCoords(newCoords);
        localStorage.setItem('crimesense_cached_coords', JSON.stringify(newCoords));
        setPermissionState('granted');
        localStorage.setItem('crimesense_location_perm_state', 'granted');
        setStatusMessage(null);

        // Throttled sync to backend
        sendLocationToBackend(newCoords.lat, newCoords.lng, newCoords.accuracy);
      },
      (err) => {
        if (err.code === 1) {
          // PERMISSION_DENIED
          setPermissionState('denied');
          localStorage.setItem('crimesense_location_perm_state', 'denied');
          setStatusMessage(
            'Location permission denied. You can search for any area manually.'
          );
        } else {
          // POSITION_UNAVAILABLE (2) or TIMEOUT (3)
          setPermissionState('unavailable');
          localStorage.setItem('crimesense_location_perm_state', 'unavailable');
          setStatusMessage('Unable to acquire GPS signal. Using manual search.');
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 15_000,
        maximumAge: 10_000,
      }
    );
  }, [sendLocationToBackend]); // stable

  const stopWatching = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
  }, []);

  // ---------------------------------------------------------------------- //
  // Request location when the explainer "Enable" button is clicked
  // ---------------------------------------------------------------------- //
  const requestLocation = useCallback(() => {
    setIsRequesting(true);
    localStorage.setItem(PERMISSION_DECIDED_KEY, 'true');

    if (!navigator.geolocation) {
      setIsRequesting(false);
      setShowExplainer(false);
      setPermissionState('unavailable');
      setStatusMessage('Geolocation is not supported by your browser.');
      return;
    }

    // Attempt a fast one-shot read first so the UI updates immediately
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsRequesting(false);
        setShowExplainer(false);
        const newCoords = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: Math.round(pos.coords.accuracy),
        };
        setCoords(newCoords);
        localStorage.setItem('crimesense_cached_coords', JSON.stringify(newCoords));
        setPermissionState('granted');
        localStorage.setItem('crimesense_location_perm_state', 'granted');
        // Now also start the continuous watch if master toggle allows
        if (localStorage.getItem('crimesense_setting_location_access') !== 'false') {
          startWatching();
        }
      },
      (err) => {
        setIsRequesting(false);
        setShowExplainer(false);
        if (err.code === 1) {
          setPermissionState('denied');
          localStorage.setItem('crimesense_location_perm_state', 'denied');
          setStatusMessage(
            'Location permission denied. Please enter addresses or areas manually.'
          );
        } else {
          setPermissionState('unavailable');
          localStorage.setItem('crimesense_location_perm_state', 'unavailable');
          setStatusMessage('GPS signal unavailable. You can search manually.');
        }
      },
      { enableHighAccuracy: true, timeout: 12_000 }
    );
  }, [startWatching]);

  // ---------------------------------------------------------------------- //
  // Skip the explainer (user prefers manual search)
  // ---------------------------------------------------------------------- //
  const skipExplainer = useCallback(() => {
    localStorage.setItem(PERMISSION_DECIDED_KEY, 'true');
    setShowExplainer(false);
    setStatusMessage(
      'Showing default Vellore area. Use the search bar to find any location.'
    );
  }, []);

  // ---------------------------------------------------------------------- //
  // On mount & toggle changes: resume or pause watching
  // ---------------------------------------------------------------------- //
  useEffect(() => {
    const handleToggle = (e) => {
      const enabled = e?.detail?.enabled ?? (localStorage.getItem('crimesense_setting_location_access') !== 'false');
      if (enabled) {
        if (localStorage.getItem('crimesense_location_perm_state') === 'granted') {
          startWatching();
        }
      } else {
        stopWatching();
      }
    };

    window.addEventListener('crimesense_location_access_changed', handleToggle);

    if (
      localStorage.getItem('crimesense_location_perm_state') === 'granted' &&
      localStorage.getItem('crimesense_setting_location_access') !== 'false'
    ) {
      startWatching();
    }

    return () => {
      window.removeEventListener('crimesense_location_access_changed', handleToggle);
      stopWatching();
    };
  }, [startWatching, stopWatching]);

  return {
    coords,
    setCoords,
    permissionState,
    showExplainer,
    isRequesting,
    statusMessage,
    clearStatusMessage: () => setStatusMessage(null),
    requestLocation,
    skipExplainer,
    recheckGPS: requestLocation,
  };
}
