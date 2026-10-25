import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search,
  X,
  Navigation,
  MapPin,
  Clock,
  Trash2,
  Loader2,
  Compass,
  AlertCircle,
  Crosshair,
  Hash,
} from 'lucide-react';
import {
  geocodeAddress,
  getRecentSearches,
  saveRecentSearch,
  removeRecentSearch,
  clearRecentSearches,
} from '../../services/geocoderService';

export default function PreciseSearchBar({
  onSelectLocation,
  onUseCurrentLocation,
  onPickOnMap,
  isPickingOnMap,
  initialValue = '',
}) {
  const [query, setQuery] = useState(initialValue);
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const [errorMessage, setErrorMessage] = useState(null);
  const [activeIndex, setActiveIndex] = useState(-1); // keyboard nav

  const containerRef = useRef(null);
  const inputRef = useRef(null);
  const debounceTimerRef = useRef(null);

  // Load recent searches whenever the dropdown opens
  useEffect(() => {
    if (isOpen) setRecentSearches(getRecentSearches());
  }, [isOpen]);

  // Click / touch outside → close dropdown
  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, []);

  // ---------------------------------------------------------------------- //
  // 400 ms debounced geocode
  // ---------------------------------------------------------------------- //
  const triggerGeocode = useCallback(async (text) => {
    if (!text || text.trim().length < 2) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setActiveIndex(-1);

    try {
      const results = await geocodeAddress(text);
      setSuggestions(results);
      if (results.length === 0) {
        setErrorMessage(
          'No places found. Try a street name, landmark, "lat, lng" pair, or a Plus Code.'
        );
      }
    } catch {
      setSuggestions([]);
      setErrorMessage(
        'Search provider unavailable. Showing local area presets as fallback.'
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    setIsOpen(true);
    setErrorMessage(null);
    setActiveIndex(-1);

    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    if (val.trim().length >= 2) {
      setIsLoading(true);
      debounceTimerRef.current = setTimeout(() => triggerGeocode(val), 400);
    } else {
      setSuggestions([]);
      setIsLoading(false);
    }
  };

  // ---------------------------------------------------------------------- //
  // Keyboard navigation
  // ---------------------------------------------------------------------- //
  const allItems = [
    { type: 'action', id: 'current-location' },
    { type: 'action', id: 'pick-on-map' },
    ...suggestions.map((s) => ({ type: 'suggestion', ...s })),
    ...(suggestions.length === 0 && !query
      ? recentSearches.map((r) => ({ type: 'recent', ...r }))
      : []),
  ];

  const handleKeyDown = (e) => {
    if (!isOpen) return;
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, allItems.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < allItems.length) {
          const item = allItems[activeIndex];
          if (item.type === 'action' && item.id === 'current-location') {
            onUseCurrentLocation();
            setIsOpen(false);
          } else if (item.type === 'action' && item.id === 'pick-on-map') {
            onPickOnMap();
            setIsOpen(false);
          } else {
            handleSelect(item);
          }
        } else if (query.trim().length >= 2) {
          triggerGeocode(query);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setActiveIndex(-1);
        inputRef.current?.blur();
        break;
      default:
        break;
    }
  };

  // ---------------------------------------------------------------------- //
  // Selection handlers
  // ---------------------------------------------------------------------- //
  const handleSelect = (item) => {
    saveRecentSearch(item);
    setRecentSearches(getRecentSearches());
    setQuery(item.title);
    setIsOpen(false);
    setActiveIndex(-1);
    onSelectLocation({
      name: item.title,
      address: item.subtitle,
      lat: item.lat,
      lng: item.lng,
    });
  };

  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    setErrorMessage(null);
    setIsOpen(false);
    setActiveIndex(-1);
    inputRef.current?.focus();
  };

  const handleRemoveRecent = (e, id) => {
    e.stopPropagation();
    const updated = removeRecentSearch(id);
    setRecentSearches(updated);
  };

  const handleClearAllRecents = (e) => {
    e.stopPropagation();
    const updated = clearRecentSearches();
    setRecentSearches(updated);
  };

  // Highlight rows that are keyboard-focused
  const rowClass = (idx) =>
    `w-full flex items-start gap-3 px-4 py-2.5 transition-colors text-left min-h-[48px] cursor-pointer ${
      activeIndex === idx ? 'bg-blue-50' : 'hover:bg-slate-50'
    }`;

  // Offset into allItems: first 2 are always the action buttons
  const ACTION_OFFSET = 2;

  return (
    <div ref={containerRef} className="relative w-full z-[1200]">
      {/* ------------------------------------------------------------------ */}
      {/* Search Input Row                                                    */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 bg-white/95 backdrop-blur-md rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.08)] border border-slate-200/90 flex items-center px-3.5 py-1 min-h-[48px] focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all">
          <Search className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />

          <input
            ref={inputRef}
            id="precise-search-input"
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            placeholder="Place, landmark, street, 12.9165N 79.1325E…"
            className="w-full bg-transparent px-2.5 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
            aria-label="Search area, landmark, address, or coordinates"
            aria-autocomplete="list"
            aria-haspopup="listbox"
            aria-expanded={isOpen}
            autoComplete="off"
          />

          {isLoading ? (
            <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
          ) : query ? (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 text-slate-400 hover:text-slate-600 min-h-[36px] min-w-[36px] flex items-center justify-center rounded-full"
              aria-label="Clear search input"
            >
              <X className="w-4 h-4" />
            </button>
          ) : null}
        </div>

        {/* GPS Quick-Action Button */}
        <button
          type="button"
          id="use-current-location-btn"
          onClick={() => {
            onUseCurrentLocation();
            setIsOpen(false);
          }}
          className="flex items-center justify-center w-12 h-12 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-[0_4px_20px_rgba(0,0,0,0.08)] text-blue-600 hover:bg-blue-50 active:scale-95 transition-all shrink-0 min-h-[48px] min-w-[48px]"
          aria-label="Center on my current GPS location"
          title="Use my current location"
        >
          <Navigation className="w-5 h-5" />
        </button>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Dropdown                                                            */}
      {/* ------------------------------------------------------------------ */}
      {isOpen && (
        <div
          role="listbox"
          aria-label="Location suggestions"
          className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-2xl border border-slate-200/90 overflow-hidden divide-y divide-slate-100 max-h-[72vh] overflow-y-auto"
          style={{ scrollbarWidth: 'none' }}
        >
          {/* ── Quick Action: Use Current Location ── */}
          <button
            type="button"
            role="option"
            aria-selected={activeIndex === 0}
            onClick={() => {
              onUseCurrentLocation();
              setIsOpen(false);
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 transition-colors text-left min-h-[48px] group ${
              activeIndex === 0 ? 'bg-blue-50' : 'hover:bg-blue-50/60'
            }`}
          >
            <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <Crosshair className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-blue-700 block">Use My Current Location</span>
              <span className="text-[11px] text-slate-500">Center on GPS coordinates with high accuracy</span>
            </div>
          </button>

          {/* ── Quick Action: Pick on Map ── */}
          <button
            type="button"
            role="option"
            aria-selected={activeIndex === 1}
            onClick={() => {
              onPickOnMap();
              setIsOpen(false);
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 transition-colors text-left min-h-[48px] group ${
              isPickingOnMap
                ? 'bg-emerald-50'
                : activeIndex === 1
                ? 'bg-emerald-50'
                : 'hover:bg-emerald-50/60'
            }`}
          >
            <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <MapPin className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-emerald-800 block">
                {isPickingOnMap ? '📍 Currently Picking…' : 'Pick on Map'}
              </span>
              <span className="text-[11px] text-slate-500">Drop a pin and drag anywhere to inspect risk</span>
            </div>
          </button>

          {/* ── Geocode Suggestions ── */}
          {suggestions.length > 0 && (
            <div className="py-1">
              <div className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Matching Places &amp; Coordinates
              </div>
              {suggestions.map((item, idx) => {
                const listIdx = ACTION_OFFSET + idx;
                return (
                  <button
                    key={item.id}
                    type="button"
                    role="option"
                    aria-selected={activeIndex === listIdx}
                    onClick={() => handleSelect(item)}
                    className={rowClass(listIdx)}
                  >
                    <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center shrink-0 mt-0.5">
                      {item.isCoordinate ? (
                        <Compass className="w-3.5 h-3.5 text-blue-600" />
                      ) : item.type === 'plus_code' ? (
                        <Hash className="w-3.5 h-3.5 text-purple-600" />
                      ) : (
                        <MapPin className="w-3.5 h-3.5 text-slate-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-bold text-slate-800 block truncate">
                        {item.title}
                      </span>
                      <span className="text-[11px] text-slate-500 line-clamp-1">
                        {item.subtitle}
                      </span>
                    </div>
                    {/* Coordinate chip */}
                    <span className="text-[10px] text-slate-400 font-mono shrink-0 hidden sm:block">
                      {item.lat?.toFixed(4)}, {item.lng?.toFixed(4)}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {/* ── Error / Empty notification ── */}
          {errorMessage && (
            <div className="p-3 bg-amber-50/80 text-amber-900 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* ── No query, no recents → prompt ── */}
          {!query && suggestions.length === 0 && recentSearches.length === 0 && !isLoading && (
            <div className="p-4 text-center">
              <Search className="w-5 h-5 text-slate-300 mx-auto mb-1.5" />
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Type a place, landmark, street address,
                <br />
                coordinates (12.9165, 79.1325) or a Plus Code.
              </p>
            </div>
          )}

          {/* ── Recent Searches ── */}
          {suggestions.length === 0 && recentSearches.length > 0 && !query && (
            <div className="py-1">
              <div className="flex items-center justify-between px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <span>Recent Searches</span>
                <button
                  type="button"
                  onClick={handleClearAllRecents}
                  className="text-slate-400 hover:text-red-600 lowercase tracking-normal font-semibold min-h-[24px]"
                >
                  clear all
                </button>
              </div>

              {recentSearches.map((rec, idx) => {
                const listIdx = ACTION_OFFSET + idx;
                return (
                  <div
                    key={rec.id}
                    onClick={() => handleSelect(rec)}
                    role="option"
                    aria-selected={activeIndex === listIdx}
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSelect(rec); }}
                    className={`w-full flex items-center justify-between px-4 py-2 cursor-pointer min-h-[44px] ${
                      activeIndex === listIdx ? 'bg-blue-50' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <div className="min-w-0">
                        <span className="text-xs font-medium text-slate-700 block truncate">
                          {rec.title}
                        </span>
                        {rec.subtitle && (
                          <span className="text-[10px] text-slate-400 block truncate">
                            {rec.subtitle}
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => handleRemoveRecent(e, rec.id)}
                      className="p-1.5 text-slate-300 hover:text-red-500 rounded-md min-h-[32px] min-w-[32px] flex items-center justify-center"
                      aria-label={`Remove ${rec.title} from history`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
