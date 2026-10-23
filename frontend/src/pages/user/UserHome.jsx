import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  MapContainer,
  TileLayer,
  Circle,
  Marker,
  Popup,
  useMap,
  useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MapPin,
  X,
  AlertCircle,
  Check,
  Compass,
} from 'lucide-react';

import PreciseSearchBar from '../../components/user/PreciseSearchBar';
import ZoneStatusCard from '../../components/user/ZoneStatusCard';
import LocationPermissionExplainer from '../../components/user/LocationPermissionExplainer';
import { useUserLocation } from '../../hooks/useUserLocation';
import { fetchZoneRisk, saveLocation, VELLORE_LOCALITY_PRESETS } from '../../services/zoneService';

// Crisp SVG-based div icons for Leaflet (avoids broken image 404s in Vite)
const userLocationIcon = L.divIcon({
  className: 'user-loc-marker',
  html: `
    <div style="position: relative; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;">
      <div style="position: absolute; width: 22px; height: 22px; border-radius: 9999px; background-color: rgba(37, 99, 235, 0.25); animation: pulse 2s infinite;"></div>
      <div style="width: 14px; height: 14px; border-radius: 9999px; background-color: #2563eb; border: 2.5px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>
    </div>
  `,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

const pickedPinIcon = L.divIcon({
  className: 'picked-pin-marker',
  html: `
    <div style="position: relative; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: grab;">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="#2563eb" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/>
        <circle cx="12" cy="10" r="3" fill="#ffffff"/>
      </svg>
    </div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 32],
});

const simplifiedIncidentIcon = (color = '#ef4444') =>
  L.divIcon({
    className: 'incident-loc-marker',
    html: `
      <div style="width: 12px; height: 12px; border-radius: 9999px; background-color: ${color}; border: 1.5px solid #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.25);"></div>
    `,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });

// Map controller to center view dynamically
function MapCenterController({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && center.lat && center.lng) {
      map.setView([center.lat, center.lng], 14, { animate: true });
    }
  }, [center, map]);
  return null;
}

// Map event listener for clicking when in "Pick on Map" mode
function MapClickHandler({ isPicking, onMapClick }) {
  useMapEvents({
    click(e) {
      if (isPicking) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
}

export default function UserHome() {
  const [searchParams] = useSearchParams();
  const [currentLocality, setCurrentLocality] = useState('Katpadi, Vellore');
  const [activeCoords, setActiveCoords] = useState({ lat: 12.9806, lng: 79.1368 });
  const [zoneData, setZoneData] = useState(null);
  const [loadingZone, setLoadingZone] = useState(true);
  const [zoneError, setZoneError] = useState(null);
  // Track whether the user has manually selected a location so GPS won't override it
  const [userPickedLocation, setUserPickedLocation] = useState(false);

  // Pick on Map mode
  const [isPickingOnMap, setIsPickingOnMap] = useState(false);
  const [pickedCoords, setPickedCoords] = useState(null);

  // Handle URL query parameters (e.g. from Saved Places 'View on Map')
  useEffect(() => {
    const pLat = searchParams.get('lat');
    const pLng = searchParams.get('lng');
    const pLabel = searchParams.get('label');
    if (pLat && pLng) {
      const latF = parseFloat(pLat);
      const lngF = parseFloat(pLng);
      if (!isNaN(latF) && !isNaN(lngF)) {
        setUserPickedLocation(true);
        setActiveCoords({ lat: latF, lng: lngF });
        if (pLabel) setCurrentLocality(pLabel);
      }
    }
  }, [searchParams]);

  // User location hook with watchPosition and throttled backend reporting
  const {
    coords: gpsCoords,
    showExplainer,
    isRequesting,
    statusMessage,
    clearStatusMessage,
    requestLocation,
    skipExplainer,
    recheckGPS,
  } = useUserLocation(zoneData?.zone || 'GREEN');

  // On first GPS fix (and only if the user hasn't manually chosen a location),
  // center the map on the user's real position.
  useEffect(() => {
    if (!userPickedLocation && gpsCoords && gpsCoords.lat && gpsCoords.lng) {
      setActiveCoords({ lat: gpsCoords.lat, lng: gpsCoords.lng });
    }
  }, [gpsCoords, userPickedLocation]);

  // Fetch zone risk evaluation
  const loadZoneData = async (lat, lng, radius = 1000) => {
    setLoadingZone(true);
    setZoneError(null);
    try {
      const data = await fetchZoneRisk(lat, lng, radius);
      setZoneData(data);
    } catch (err) {
      setZoneData(null);
      setZoneError('Unable to load crime risk data from server.');
    } finally {
      setLoadingZone(false);
    }
  };

  useEffect(() => {
    loadZoneData(activeCoords.lat, activeCoords.lng);
  }, [activeCoords.lat, activeCoords.lng]);

  // Handle selection from search bar
  const handleSelectLocation = (loc) => {
    if (showExplainer) skipExplainer();
    setIsPickingOnMap(false);
    setUserPickedLocation(true); // prevent GPS from re-centering
    setCurrentLocality(loc.name || loc.address || 'Selected Location');
    setActiveCoords({ lat: loc.lat, lng: loc.lng });
  };

  // Handle "Use my current location"
  const handleUseCurrentLocation = () => {
    if (showExplainer) skipExplainer();
    setIsPickingOnMap(false);
    setUserPickedLocation(false); // re-enable GPS auto-center
    if (gpsCoords) {
      setActiveCoords({ lat: gpsCoords.lat, lng: gpsCoords.lng });
      setCurrentLocality('My Current GPS Location');
    }
    recheckGPS();
  };

  // Start "Pick on map" mode
  const handleStartPickOnMap = () => {
    setIsPickingOnMap(true);
    setPickedCoords({ lat: activeCoords.lat, lng: activeCoords.lng });
  };

  // Dragging or clicking to update picked pin
  const handleMapClickOrDrag = (lat, lng) => {
    setPickedCoords({ lat, lng });
  };

  // Confirm picked pin
  const handleConfirmPickedLocation = () => {
    if (pickedCoords) {
      setUserPickedLocation(true);
      setActiveCoords({ lat: pickedCoords.lat, lng: pickedCoords.lng });
      setCurrentLocality(`Dropped Pin (${pickedCoords.lat.toFixed(4)}, ${pickedCoords.lng.toFixed(4)})`);
      setIsPickingOnMap(false);
    }
  };

  const handleCancelPick = () => {
    setIsPickingOnMap(false);
    setPickedCoords(null);
  };

  // Save location callback
  const handleSaveLocation = (name) => {
    saveLocation({
      label: name,
      address: currentLocality,
      lat: activeCoords.lat,
      lng: activeCoords.lng,
      zone: zoneData?.zone || 'GREEN',
    });
  };

  // Determine circle style according to current zone
  const getZoneCircleStyle = (zone = 'GREEN') => {
    switch ((zone || 'GREEN').toUpperCase()) {
      case 'RED':
        return { color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.16 };
      case 'YELLOW':
        return { color: '#f59e0b', fillColor: '#f59e0b', fillOpacity: 0.16 };
      default:
        return { color: '#10b981', fillColor: '#10b981', fillOpacity: 0.14 };
    }
  };

  const currentZone = zoneData?.zone || 'GREEN';
  const circleStyle = getZoneCircleStyle(currentZone);

  // Simplified nearby marker if severe incident exists
  const nearbyIncidents = useMemo(() => {
    if (zoneData?.most_severe_recent_incident?.title) {
      return [
        {
          lat: activeCoords.lat + 0.0012,
          lng: activeCoords.lng + 0.0015,
          title: zoneData.most_severe_recent_incident.title,
          crime_type: zoneData.most_severe_recent_incident.crime_type,
          date: zoneData.most_severe_recent_incident.date,
        },
      ];
    }
    return [];
  }, [zoneData, activeCoords]);

  return (
    <div className="relative flex-1 flex flex-col h-[calc(100vh-64px)] overflow-hidden">
      {/* 1. Full-screen Location Permission Explainer on first entry */}
      {showExplainer && (
        <LocationPermissionExplainer
          onEnable={requestLocation}
          onSkip={skipExplainer}
          isRequesting={isRequesting}
        />
      )}

      {/* 2. Top Search Bar & Controls */}
      <div className="absolute top-0 left-0 right-0 z-[1100] p-3 space-y-2 pointer-events-none">
        <div className="pointer-events-auto">
          <PreciseSearchBar
            onSelectLocation={handleSelectLocation}
            onUseCurrentLocation={handleUseCurrentLocation}
            onPickOnMap={handleStartPickOnMap}
            isPickingOnMap={isPickingOnMap}
            initialValue={currentLocality}
          />
        </div>

        {/* Fallback status toast (e.g. if GPS denied or unavailable) */}
        {statusMessage && (
          <div className="pointer-events-auto flex items-center justify-between gap-2 p-2.5 rounded-xl bg-slate-900/90 text-white text-xs shadow-lg backdrop-blur-md animate-in fade-in-50">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>{statusMessage}</span>
            </div>
            <button
              type="button"
              onClick={clearStatusMessage}
              className="p-1 hover:text-slate-300 min-h-[28px] min-w-[28px] flex items-center justify-center"
              aria-label="Dismiss message"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Locality chips when not in pick mode */}
        {!isPickingOnMap && (
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pointer-events-auto py-1 pb-1.5 px-0.5">
            {VELLORE_LOCALITY_PRESETS.slice(0, 4).map((preset) => (
              <button
                key={preset.name}
                type="button"
                onClick={() =>
                  handleSelectLocation({
                    name: preset.name,
                    lat: preset.lat,
                    lng: preset.lng,
                  })
                }
                className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap shadow-xs backdrop-blur-md transition-all min-h-[32px] ${
                  activeCoords.lat === preset.lat
                    ? 'bg-blue-600 text-white shadow-blue-200'
                    : 'bg-white/90 text-slate-700 hover:bg-white border border-slate-200/80'
                }`}
              >
                {preset.name}
              </button>
            ))}
          </div>
        )}

        {/* "Pick on Map" Active Instruction Bar */}
        {isPickingOnMap && (
          <div className="pointer-events-auto flex items-center justify-between gap-2 p-3 rounded-2xl bg-white border border-slate-200 shadow-xl animate-in slide-in-from-top-3">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-600 shrink-0 animate-bounce" />
              <div className="text-xs">
                <span className="font-bold text-slate-800 block">Tap map or drag pin</span>
                <span className="text-[10px] text-slate-500">Position pin at your target area</span>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleConfirmPickedLocation}
                className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-blue-600 text-white text-xs font-bold shadow-xs hover:bg-blue-700 active:scale-95 transition-all min-h-[36px]"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Done</span>
              </button>
              <button
                type="button"
                onClick={handleCancelPick}
                className="p-1.5 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 min-h-[36px] min-w-[36px] flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 3. Full-width Leaflet Map */}
      <div className="flex-1 w-full relative z-0">
        <MapContainer
          center={[activeCoords.lat, activeCoords.lng]}
          zoom={14}
          zoomControl={false}
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          {/* Clean CartoDB Voyager light tiles */}
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />

          <MapCenterController center={isPickingOnMap ? pickedCoords : activeCoords} />
          <MapClickHandler isPicking={isPickingOnMap} onMapClick={handleMapClickOrDrag} />

          {/* User's GPS Location Marker */}
          {gpsCoords && (
            <Marker position={[gpsCoords.lat, gpsCoords.lng]} icon={userLocationIcon}>
              <Popup>
                <div className="text-xs p-1">
                  <p className="font-bold text-slate-800">Your Current Position</p>
                  <p className="text-[10px] text-slate-500">Live GPS tracking active</p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Draggable Picked Pin in Pick Mode */}
          {isPickingOnMap && pickedCoords && (
            <Marker
              position={[pickedCoords.lat, pickedCoords.lng]}
              icon={pickedPinIcon}
              draggable={true}
              eventHandlers={{
                dragend: (e) => {
                  const latlng = e.target.getLatLng();
                  handleMapClickOrDrag(latlng.lat, latlng.lng);
                },
              }}
            >
              <Popup autoPan={false}>
                <div className="text-xs p-1">
                  <p className="font-bold text-blue-600">Selected Point</p>
                  <p className="text-[10px] text-slate-500">
                    {pickedCoords.lat.toFixed(4)}, {pickedCoords.lng.toFixed(4)}
                  </p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Colored Zone Circle (1,000m radius around active evaluated location) */}
          {!isPickingOnMap && (
            <Circle
              center={[activeCoords.lat, activeCoords.lng]}
              radius={1000}
              pathOptions={{
                color: circleStyle.color,
                weight: 2,
                fillColor: circleStyle.fillColor,
                fillOpacity: circleStyle.fillOpacity,
              }}
            />
          )}

          {/* Simplified Nearby Incident Markers */}
          {!isPickingOnMap &&
            nearbyIncidents.map((inc, i) => (
              <Marker
                key={i}
                position={[inc.lat, inc.lng]}
                icon={simplifiedIncidentIcon(circleStyle.color)}
              >
                <Popup>
                  <div className="text-xs p-1 max-w-[180px]">
                    <p className="font-semibold text-slate-800">{inc.crime_type}</p>
                    <p className="text-[10px] text-slate-500">{inc.title}</p>
                  </div>
                </Popup>
              </Marker>
            ))}
        </MapContainer>
      </div>

      {/* 4. Bottom Zone Status Card or Error State */}
      {!showExplainer && !isPickingOnMap && zoneError && (
        <div className="absolute bottom-2 left-0 right-0 z-20 pointer-events-auto px-3 animate-in slide-in-from-bottom-3 duration-200">
          <div className="bg-white/95 backdrop-blur-md border border-red-200 rounded-2xl p-4 shadow-xl flex items-center justify-between gap-3 text-slate-800 text-xs">
            <div className="flex items-center gap-2.5 min-w-0">
              <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
              <div className="min-w-0">
                <span className="font-bold text-slate-900 block truncate">Zone Evaluation Offline</span>
                <span className="text-[11px] text-slate-500 truncate block">{zoneError}</span>
              </div>
            </div>
            <button
              type="button"
              onClick={() => loadZoneData(activeCoords.lat, activeCoords.lng)}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-xl text-xs font-bold shrink-0 transition-all shadow-sm shadow-blue-500/20 min-h-[38px]"
            >
              Retry
            </button>
          </div>
        </div>
      )}
      {!showExplainer && !isPickingOnMap && !zoneError && (
        <div className="absolute bottom-2 left-0 right-0 z-20 pointer-events-auto animate-in slide-in-from-bottom-4 duration-300">
          <ZoneStatusCard
            zoneData={zoneData}
            loading={loadingZone}
            currentLocality={currentLocality}
            coords={activeCoords}
            onSaveLocation={handleSaveLocation}
          />
        </div>
      )}
    </div>
  );
}
