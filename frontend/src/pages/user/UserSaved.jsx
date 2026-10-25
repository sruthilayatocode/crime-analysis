import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bookmark,
  MapPin,
  Plus,
  Trash2,
  Share2,
  ExternalLink,
  Edit2,
  Star,
  Home,
  Briefcase,
  GraduationCap,
  Dumbbell,
  Building,
  HeartPulse,
  Coffee,
  Navigation,
  RefreshCw,
  Search,
  Check,
  X,
  Compass,
} from 'lucide-react';
import ZoneBadge from '../../components/user/ZoneBadge';
import ShareLocationModal from '../../components/user/ShareLocationModal';
import { savedPlacesService } from '../../services/savedPlacesService';
import { fetchZoneRisk } from '../../services/zoneService';

const PRESET_LABELS = [
  { label: 'Home', icon: Home },
  { label: 'College', icon: GraduationCap },
  { label: 'Office', icon: Briefcase },
  { label: 'Gym', icon: Dumbbell },
  { label: 'Hostel', icon: Building },
  { label: 'Hospital', icon: HeartPulse },
];

export default function UserSaved() {
  const navigate = useNavigate();

  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reEvaluating, setReEvaluating] = useState(false);
  const [userCoords, setUserCoords] = useState(null);

  // Add / Save Modal State
  const [isAdding, setIsAdding] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [newAddress, setNewAddress] = useState('');
  const [newLat, setNewLat] = useState('12.9806');
  const [newLng, setNewLng] = useState('79.1368');
  const [isPinned, setIsPinned] = useState(false);
  const [savingPlace, setSavingPlace] = useState(false);

  // Rename Modal State
  const [editingPlace, setEditingPlace] = useState(null);
  const [renameLabel, setRenameLabel] = useState('');
  const [renaming, setRenaming] = useState(false);

  // Share Modal State
  const [sharingPlace, setSharingPlace] = useState(null);

  // Obtain user's live position for distance calculations
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserCoords({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
          });
        },
        () => {}
      );
    }
  }, []);

  // Fetch saved places (re-evaluates risk zones live on load)
  const loadPlaces = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    else setReEvaluating(true);

    try {
      const data = await savedPlacesService.getSavedPlaces(true);
      setPlaces(data);
    } catch (err) {
      console.error('Error loading saved places:', err);
    } finally {
      setLoading(false);
      setReEvaluating(false);
    }
  };

  useEffect(() => {
    loadPlaces();
  }, []);

  // Calculate distance in meters between user and place
  const calculateDistance = (placeLat, placeLng) => {
    if (!userCoords || !placeLat || !placeLng) return null;
    const R = 6371000;
    const dLat = ((placeLat - userCoords.latitude) * Math.PI) / 180;
    const dLon = ((placeLng - userCoords.longitude) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((userCoords.latitude * Math.PI) / 180) *
        Math.cos((placeLat * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const dist = Math.round(R * c);

    if (dist >= 1000) {
      return `${(dist / 1000).toFixed(1)} km`;
    }
    return `${dist} m`;
  };

  // Preset Label Click
  const handlePresetSelect = (presetName) => {
    setNewLabel(presetName);
  };

  // Use Current Location button in Add form
  const handleUseCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setNewLat(pos.coords.latitude.toFixed(5));
          setNewLng(pos.coords.longitude.toFixed(5));
          setNewAddress(`Current Location (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)})`);
        },
        () => alert('Could not get GPS location. Please check browser permissions.')
      );
    }
  };

  // Add Place Submit
  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!newLabel.trim()) return;

    setSavingPlace(true);
    try {
      await savedPlacesService.addSavedPlace({
        label: newLabel.trim(),
        address: newAddress.trim() || `${parseFloat(newLat).toFixed(4)}, ${parseFloat(newLng).toFixed(4)}`,
        latitude: parseFloat(newLat),
        longitude: parseFloat(newLng),
        is_pinned: isPinned,
      });
      await loadPlaces(false);
      setNewLabel('');
      setNewAddress('');
      setIsPinned(false);
      setIsAdding(false);
    } catch (err) {
      alert(`Error saving place: ${err.message}`);
    } finally {
      setSavingPlace(false);
    }
  };

  // Toggle Pin / Favorite
  const handleTogglePin = async (place) => {
    try {
      await savedPlacesService.updateSavedPlace(place.id, {
        is_pinned: !place.is_pinned,
      });
      await loadPlaces(false);
    } catch (err) {
      alert(err.message);
    }
  };

  // Rename Place Submit
  const handleRenameSubmit = async (e) => {
    e.preventDefault();
    if (!editingPlace || !renameLabel.trim()) return;

    setRenaming(true);
    try {
      await savedPlacesService.updateSavedPlace(editingPlace.id, {
        label: renameLabel.trim(),
      });
      await loadPlaces(false);
      setEditingPlace(null);
      setRenameLabel('');
    } catch (err) {
      alert(`Error renaming place: ${err.message}`);
    } finally {
      setRenaming(false);
    }
  };

  // Delete Place
  const handleDeletePlace = async (id, label) => {
    if (window.confirm(`Remove '${label}' from your saved places?`)) {
      try {
        await savedPlacesService.deleteSavedPlace(id);
        setPlaces((prev) => prev.filter((p) => p.id !== id));
      } catch (err) {
        alert(err.message);
      }
    }
  };

  // View on Map (navigates to Home / Search view centered on place)
  const handleViewOnMap = (place) => {
    navigate(`/app?lat=${place.latitude}&lng=${place.longitude}&label=${encodeURIComponent(place.label)}`);
  };

  const getIconForLabel = (label = '') => {
    const l = label.toLowerCase();
    if (l.includes('home')) return Home;
    if (l.includes('work') || l.includes('office')) return Briefcase;
    if (l.includes('college') || l.includes('vit') || l.includes('school') || l.includes('campus')) return GraduationCap;
    if (l.includes('gym') || l.includes('fitness')) return Dumbbell;
    if (l.includes('hospital') || l.includes('clinic')) return HeartPulse;
    if (l.includes('hostel')) return Building;
    if (l.includes('cafe') || l.includes('coffee')) return Coffee;
    return MapPin;
  };

  return (
    <div className="flex-1 p-4 pb-24 space-y-4 max-w-md mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between pt-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-blue-600 fill-blue-600/20" />
            <span>Saved Places</span>
          </h1>
          <p className="text-xs text-slate-500">Live safety monitoring for your frequent destinations</p>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => loadPlaces(false)}
            disabled={reEvaluating}
            title="Re-evaluate live safety zones"
            className="p-2 text-slate-500 hover:text-blue-600 rounded-xl hover:bg-slate-100 transition-colors min-h-[40px] min-w-[40px] flex items-center justify-center"
          >
            <RefreshCw className={`w-4 h-4 ${reEvaluating ? 'animate-spin text-blue-600' : ''}`} />
          </button>

          <button
            type="button"
            onClick={() => setIsAdding(!isAdding)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-xs active:scale-95 transition-all min-h-[40px]"
          >
            <Plus className="w-4 h-4" />
            <span>Add Place</span>
          </button>
        </div>
      </div>

      {/* Add New Place Modal/Drawer */}
      {isAdding && (
        <form
          onSubmit={handleAddSubmit}
          className="bg-white rounded-2xl p-4 border border-blue-200 shadow-lg space-y-3 animate-in fade-in-50"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Save New Destination
            </h2>
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Preset Quick Chips */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 mb-1.5">Quick Presets</label>
            <div className="flex flex-wrap gap-1.5">
              {PRESET_LABELS.map((p) => {
                const IconComponent = p.icon;
                const active = newLabel.toLowerCase() === p.label.toLowerCase();
                return (
                  <button
                    key={p.label}
                    type="button"
                    onClick={() => handlePresetSelect(p.label)}
                    className={`px-2.5 py-1 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
                      active
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    <IconComponent className="w-3.5 h-3.5" />
                    <span>{p.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-600 mb-1">
              Custom Place Label <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. My Apartment, VIT Main Campus"
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] font-bold text-slate-600">Location Address / Area</label>
              <button
                type="button"
                onClick={handleUseCurrentLocation}
                className="text-[10px] font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <Compass className="w-3 h-3" />
                <span>Use Current GPS</span>
              </button>
            </div>
            <input
              type="text"
              placeholder="e.g. Katpadi, Vellore"
              value={newAddress}
              onChange={(e) => setNewAddress(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[10px] font-bold text-slate-500 mb-0.5">Latitude</label>
              <input
                type="number"
                step="any"
                required
                value={newLat}
                onChange={(e) => setNewLat(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-500 mb-0.5">Longitude</label>
              <input
                type="number"
                step="any"
                required
                value={newLng}
                onChange={(e) => setNewLng(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer pt-1">
            <input
              type="checkbox"
              checked={isPinned}
              onChange={(e) => setIsPinned(e.target.checked)}
              className="rounded border-slate-300 text-amber-500 focus:ring-amber-400"
            />
            <span className="flex items-center gap-1 font-semibold">
              <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
              <span>Pin / Favorite to top</span>
            </span>
          </label>

          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              disabled={savingPlace}
              className="flex-1 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-xs transition-all min-h-[40px]"
            >
              {savingPlace ? 'Saving...' : 'Save Place'}
            </button>
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 min-h-[40px]"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Rename Modal */}
      {editingPlace && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs animate-in fade-in">
          <form
            onSubmit={handleRenameSubmit}
            className="bg-white rounded-3xl p-5 max-w-sm w-full shadow-2xl border border-slate-200 space-y-3"
          >
            <div className="flex items-center justify-between pb-1 border-b border-slate-100">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Rename Place
              </h3>
              <button
                type="button"
                onClick={() => setEditingPlace(null)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-600 mb-1">New Label</label>
              <input
                type="text"
                required
                value={renameLabel}
                onChange={(e) => setRenameLabel(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="submit"
                disabled={renaming}
                className="flex-1 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold min-h-[38px]"
              >
                {renaming ? 'Updating...' : 'Save Changes'}
              </button>
              <button
                type="button"
                onClick={() => setEditingPlace(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold min-h-[38px]"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Share Modal */}
      {sharingPlace && (
        <ShareLocationModal
          location={sharingPlace}
          onClose={() => setSharingPlace(null)}
        />
      )}

      {/* Places List */}
      {loading ? (
        <div className="py-12 text-center text-xs text-slate-400 font-mono">
          Loading saved destinations & re-evaluating risk zones...
        </div>
      ) : places.length === 0 ? (
        <div className="bg-white rounded-3xl p-8 text-center space-y-3 border border-slate-200/80 shadow-2xs">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
            <Bookmark className="w-6 h-6" />
          </div>
          <h2 className="text-sm font-bold text-slate-800">No Saved Places Yet</h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
            Bookmark your home, college, workplace, or transit stops to track live safety zones and share instantly.
          </p>
          <button
            type="button"
            onClick={() => setIsAdding(true)}
            className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold shadow-xs hover:bg-blue-700 transition-all min-h-[40px]"
          >
            Add Your First Place
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {places.map((place) => {
            const IconComponent = getIconForLabel(place.label);
            const distance = calculateDistance(place.latitude, place.longitude);
            const zoneUpper = (place.zone || 'GREEN').toUpperCase();

            return (
              <div
                key={place.id}
                className={`bg-white rounded-2xl p-4 border transition-all shadow-2xs space-y-3 relative ${
                  place.is_pinned
                    ? 'border-amber-300/80 bg-amber-50/20'
                    : 'border-slate-200/90'
                }`}
              >
                {/* Top Row: Icon + Label + Pinned Star + Zone Badge */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-xs ${
                        zoneUpper === 'RED'
                          ? 'bg-red-50 text-red-600 border border-red-200'
                          : zoneUpper === 'YELLOW'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}
                    >
                      <IconComponent className="w-5 h-5 stroke-[2.2]" />
                    </div>

                    <div>
                      <div className="flex items-center gap-1.5">
                        <h2 className="text-sm font-bold text-slate-900 leading-tight">
                          {place.label}
                        </h2>
                        {place.is_pinned && (
                          <span title="Pinned Favorite">
                            <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                        {place.address}
                      </p>
                    </div>
                  </div>

                  {/* Zone Badge re-evaluated live */}
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider shrink-0 ${
                      zoneUpper === 'RED'
                        ? 'bg-red-100 text-red-700 border border-red-200'
                        : zoneUpper === 'YELLOW'
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                    }`}
                  >
                    {zoneUpper}
                  </span>
                </div>

                {/* Sub-row: Distance + Last Checked info */}
                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-0.5 border-t border-slate-100 font-mono">
                  <span>
                    {distance ? `${distance} from current GPS` : `${place.latitude.toFixed(4)}, ${place.longitude.toFixed(4)}`}
                  </span>
                  <span className="text-[10px] text-slate-400 font-sans">
                    Checked live
                  </span>
                </div>

                {/* Action Buttons: View on Map, Rename, Share, Delete */}
                <div className="grid grid-cols-4 gap-1.5 pt-1">
                  {/* View on Map */}
                  <button
                    type="button"
                    onClick={() => handleViewOnMap(place)}
                    className="py-1.5 px-2 rounded-xl bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 text-[11px] font-bold flex items-center justify-center gap-1 transition-colors min-h-[36px]"
                    title="View on Map"
                  >
                    <Navigation className="w-3.5 h-3.5" />
                    <span>Map</span>
                  </button>

                  {/* Share */}
                  <button
                    type="button"
                    onClick={() => setSharingPlace(place)}
                    className="py-1.5 px-2 rounded-xl bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 text-slate-700 text-[11px] font-bold flex items-center justify-center gap-1 transition-colors min-h-[36px]"
                    title="Share via WhatsApp or CrimeSense link"
                  >
                    <Share2 className="w-3.5 h-3.5" />
                    <span>Share</span>
                  </button>

                  {/* Rename */}
                  <button
                    type="button"
                    onClick={() => {
                      setEditingPlace(place);
                      setRenameLabel(place.label);
                    }}
                    className="py-1.5 px-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold flex items-center justify-center gap-1 transition-colors min-h-[36px]"
                    title="Rename place"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                    <span>Edit</span>
                  </button>

                  {/* Pin / Delete Dropdown or Actions */}
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => handleTogglePin(place)}
                      className={`flex-1 py-1.5 rounded-xl text-[11px] font-bold flex items-center justify-center transition-colors min-h-[36px] ${
                        place.is_pinned
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-500 hover:text-amber-600'
                      }`}
                      title={place.is_pinned ? 'Unpin' : 'Pin to top'}
                    >
                      <Star className={`w-3.5 h-3.5 ${place.is_pinned ? 'fill-current' : ''}`} />
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDeletePlace(place.id, place.label)}
                      className="p-1.5 rounded-xl bg-slate-100 hover:bg-red-50 text-slate-400 hover:text-red-600 transition-colors min-h-[36px] min-w-[32px] flex items-center justify-center"
                      title="Delete Place"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
