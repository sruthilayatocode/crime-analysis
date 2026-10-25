import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Bell,
  MapPin,
  Shield,
  Download,
  LogOut,
  ChevronRight,
  Info,
  CheckCircle2,
  Lock,
  Users,
  UserPlus,
  Trash2,
  Star,
  Smartphone,
  AlertCircle,
  PhoneCall,
  Send,
  RefreshCw,
  AlertTriangle,
  Edit3,
  X,
  HelpCircle,
  FileText,
  ChevronDown,
  Check,
  Globe,
  Radio,
  Compass,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useSOS } from '../../context/SOSContext';
import { authService } from '../../services/authService';
import {
  sosService,
  validateAndFormatPhone,
  pickContactFromDevice,
} from '../../services/sosService';

const RELATIONSHIP_OPTIONS = [
  'Family',
  'Parent',
  'Spouse / Partner',
  'Sibling',
  'Friend',
  'Colleague',
  'Neighbor',
  'Other',
];

const AVATAR_PRESETS = [
  '🛡️', '⚡', '🌟', '🚀', '🦅', '🦁', '🧭', '⭐', '🔒', '🔥'
];

export default function UserSettings() {
  const { user, logout, refreshUser } = useAuth();
  const { contacts, refreshContacts } = useSOS();
  const navigate = useNavigate();

  // ------------------------------------------------------------------------- //
  // SECTION 1: PROFILE STATES
  // ------------------------------------------------------------------------- //
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileName, setProfileName] = useState(user?.name || '');
  const [profileAvatar, setProfileAvatar] = useState(user?.avatar_url || '🛡️');
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState('');
  const [showDeleteAccountModal, setShowDeleteAccountModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deletingAccount, setDeletingAccount] = useState(false);

  // ------------------------------------------------------------------------- //
  // SECTION 2: SOS CONTACTS STATES
  // ------------------------------------------------------------------------- //
  const [isAddingContact, setIsAddingContact] = useState(false);
  const [editingContact, setEditingContact] = useState(null);
  const [cName, setCName] = useState('');
  const [cPhone, setCPhone] = useState('');
  const [cRel, setCRel] = useState('Family');
  const [cPrimary, setCPrimary] = useState(false);
  const [savingContact, setSavingContact] = useState(false);
  const [contactError, setContactError] = useState('');
  const [testingContactId, setTestingContactId] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [hasContactPicker] = useState(
    typeof window !== 'undefined' && 'contacts' in navigator && 'ContactsManager' in window
  );

  // ------------------------------------------------------------------------- //
  // SECTION 3: LOCATION & PRIVACY STATES
  // ------------------------------------------------------------------------- //
  const [locationAccess, setLocationAccess] = useState(() => {
    return localStorage.getItem('crimesense_setting_location_access') !== 'false';
  });
  const [allowAdminLiveLocation, setAllowAdminLiveLocation] = useState(() => {
    return localStorage.getItem('crimesense_setting_admin_live') === 'true';
  });
  const [showRevokeGuide, setShowRevokeGuide] = useState(false);
  const [selectedBrowserTab, setSelectedBrowserTab] = useState('chrome');
  const [deletingLocations, setDeletingLocations] = useState(false);
  const [locationDeletedMsg, setLocationDeletedMsg] = useState('');

  // ------------------------------------------------------------------------- //
  // SECTION 4: ALERTS STATES
  // ------------------------------------------------------------------------- //
  const [redZoneAlert, setRedZoneAlert] = useState(() => {
    return localStorage.getItem('crimesense_setting_notify_red') !== 'false';
  });
  const [inactivityMinutes, setInactivityMinutes] = useState(() => {
    return parseInt(localStorage.getItem('crimesense_setting_inactivity_mins') || '10', 10);
  });
  const [alertRadius, setAlertRadius] = useState(() => {
    return localStorage.getItem('crimesense_setting_radius') || '1000';
  });

  // ------------------------------------------------------------------------- //
  // SECTION 5: ABOUT & PRIVACY POLICY STATES
  // ------------------------------------------------------------------------- //
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);
  const [showDataSources, setShowDataSources] = useState(false);

  // PWA install state
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [installed, setInstalled] = useState(false);

  // Keep profile inputs in sync with authenticated user
  useEffect(() => {
    if (user) {
      setProfileName(user.name || '');
      setProfileAvatar(user.avatar_url || '🛡️');
    }
  }, [user]);

  // ------------------------------------------------------------------------- //
  // SYNC SETTINGS FROM SERVER ON MOUNT
  // ------------------------------------------------------------------------- //
  useEffect(() => {
    async function loadServerSettings() {
      try {
        const s = await authService.getSettings();
        if (s) {
          if (typeof s.location_sharing_enabled === 'boolean') {
            setLocationAccess(s.location_sharing_enabled);
            localStorage.setItem('crimesense_setting_location_access', String(s.location_sharing_enabled));
          }
          if (typeof s.red_zone_alert_enabled === 'boolean') {
            setRedZoneAlert(s.red_zone_alert_enabled);
            localStorage.setItem('crimesense_setting_notify_red', String(s.red_zone_alert_enabled));
          }
          if (s.inactivity_minutes) {
            setInactivityMinutes(s.inactivity_minutes);
            localStorage.setItem('crimesense_setting_inactivity_mins', String(s.inactivity_minutes));
          }
          if (s.alert_radius_m) {
            setAlertRadius(String(s.alert_radius_m));
            localStorage.setItem('crimesense_setting_radius', String(s.alert_radius_m));
          }
          if (typeof s.share_live_location_with_admin === 'boolean') {
            setAllowAdminLiveLocation(s.share_live_location_with_admin);
            localStorage.setItem('crimesense_setting_admin_live', String(s.share_live_location_with_admin));
          }
        }
      } catch (err) {
        console.warn('[UserSettings] Using cached local settings:', err);
      }
    }
    loadServerSettings();
  }, []);

  // Sync settings helper
  const persistSettingsToServer = async (patch) => {
    try {
      await authService.updateSettings(patch);
    } catch (err) {
      console.error('[UserSettings] Failed to persist settings to server:', err);
    }
  };

  // PWA detection
  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setIsInstallable(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setInstalled(true);
    }
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstallApp = async () => {
    if (!deferredPrompt) {
      alert('To install, tap your browser menu and choose "Add to Home Screen".');
      return;
    }
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setIsInstallable(false);
      setInstalled(true);
    }
    setDeferredPrompt(null);
  };

  // ------------------------------------------------------------------------- //
  // SECTION 1 HANDLERS: PROFILE
  // ------------------------------------------------------------------------- //
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (!profileName.trim()) return;
    setSavingProfile(true);
    try {
      await authService.updateProfile({
        name: profileName.trim(),
        avatar_url: profileAvatar,
      });
      if (refreshUser) await refreshUser();
      setProfileSuccessMsg('Profile updated successfully!');
      setIsEditingProfile(false);
      setTimeout(() => setProfileSuccessMsg(''), 3500);
    } catch (err) {
      alert(err.message || 'Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText.trim().toUpperCase() !== 'DELETE') {
      alert('Please type "DELETE" to confirm permanent account removal.');
      return;
    }
    setDeletingAccount(true);
    try {
      await authService.deleteAccount();
      if (logout) await logout();
      alert('Your account and all associated personal data have been permanently deleted.');
      navigate('/login');
    } catch (err) {
      alert(err.message || 'Failed to delete account');
      setDeletingAccount(false);
    }
  };

  // ------------------------------------------------------------------------- //
  // SECTION 2 HANDLERS: SOS CONTACTS & TEST MESSAGE
  // ------------------------------------------------------------------------- //
  const openAddContactForm = () => {
    setEditingContact(null);
    setCName('');
    setCPhone('');
    setCRel('Family');
    setCPrimary(contacts.length === 0);
    setContactError('');
    setIsAddingContact(true);
  };

  const openEditContactForm = (c) => {
    setEditingContact(c);
    setCName(c.name);
    setCPhone(c.phone);
    setCRel(c.relationship || 'Family');
    setCPrimary(c.is_primary);
    setContactError('');
    setIsAddingContact(true);
  };

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    setContactError('');

    if (!cName.trim() || !cPhone.trim()) {
      setContactError('Please provide name and phone number.');
      return;
    }

    const val = validateAndFormatPhone(cPhone.trim());
    if (!val.isValid) {
      setContactError(val.error);
      return;
    }

    if (!editingContact && contacts.length >= 5) {
      setContactError('Maximum 5 emergency contacts allowed.');
      return;
    }

    setSavingContact(true);
    try {
      if (editingContact) {
        await sosService.updateContact(editingContact.id, {
          name: cName.trim(),
          phone: val.formatted,
          relationship: cRel,
          is_primary: cPrimary,
        });
      } else {
        await sosService.addContact({
          name: cName.trim(),
          phone: val.formatted,
          relationship: cRel,
          is_primary: cPrimary || contacts.length === 0,
        });
      }
      await refreshContacts();
      setIsAddingContact(false);
      setEditingContact(null);
    } catch (err) {
      setContactError(err.message || 'Failed to save contact');
    } finally {
      setSavingContact(false);
    }
  };

  const handleDeleteContact = async (id, name) => {
    if (contacts.length <= 1) {
      alert('You must maintain at least 1 emergency contact for personal safety.');
      return;
    }
    if (window.confirm(`Remove '${name}' from SOS emergency contacts?`)) {
      try {
        await sosService.deleteContact(id);
        await refreshContacts();
      } catch (err) {
        alert(err.message || 'Failed to delete contact');
      }
    }
  };

  const handleSetPrimary = async (c) => {
    try {
      await sosService.updateContact(c.id, { is_primary: true });
      await refreshContacts();
    } catch (err) {
      alert(err.message || 'Failed to update primary contact');
    }
  };

  const handleSendTestMessage = async (c) => {
    setTestingContactId(c.id);
    setTestResult(null);
    try {
      const res = await sosService.sendTestMessage(c.id);
      setTestResult({
        contactId: c.id,
        contactName: c.name,
        success: true,
        message: res.message || `Test verification notification sent to ${c.name}.`,
        preview: res?.result?.message_preview || '',
      });
    } catch (err) {
      setTestResult({
        contactId: c.id,
        contactName: c.name,
        success: false,
        message: err.message || 'Failed to dispatch test notification.',
      });
    } finally {
      setTestingContactId(null);
    }
  };

  const handlePickDevice = async () => {
    try {
      const picked = await pickContactFromDevice();
      if (picked) {
        if (picked.name) setCName(picked.name);
        if (picked.phone) setCPhone(picked.phone);
      }
    } catch {}
  };

  // ------------------------------------------------------------------------- //
  // SECTION 3 HANDLERS: LOCATION & PRIVACY
  // ------------------------------------------------------------------------- //
  const handleToggleLocationAccess = () => {
    const updated = !locationAccess;
    setLocationAccess(updated);
    localStorage.setItem('crimesense_setting_location_access', String(updated));

    // Dispatch global event for useUserLocation and context
    window.dispatchEvent(
      new CustomEvent('crimesense_location_access_changed', {
        detail: { enabled: updated },
      })
    );

    // Persist to server
    persistSettingsToServer({ location_sharing_enabled: updated });
  };

  const handleToggleAdminLiveLocation = () => {
    const updated = !allowAdminLiveLocation;
    setAllowAdminLiveLocation(updated);
    localStorage.setItem('crimesense_setting_admin_live', String(updated));
    persistSettingsToServer({ share_live_location_with_admin: updated });
  };

  const handleDeleteLocationHistory = async () => {
    if (!window.confirm('Delete all stored GPS tracking entries? This cannot be undone.')) {
      return;
    }
    setDeletingLocations(true);
    try {
      const res = await authService.deleteLocationHistory();
      setLocationDeletedMsg(res.message || 'Location history deleted successfully.');
      setTimeout(() => setLocationDeletedMsg(''), 4000);
    } catch (err) {
      alert(err.message || 'Failed to delete location history');
    } finally {
      setDeletingLocations(false);
    }
  };

  // ------------------------------------------------------------------------- //
  // SECTION 4 HANDLERS: ALERTS
  // ------------------------------------------------------------------------- //
  const handleToggleRedZoneAlert = () => {
    const updated = !redZoneAlert;
    setRedZoneAlert(updated);
    localStorage.setItem('crimesense_setting_notify_red', String(updated));
    persistSettingsToServer({ red_zone_alert_enabled: updated });
  };

  const handleInactivityMinutesChange = (mins) => {
    setInactivityMinutes(mins);
    localStorage.setItem('crimesense_setting_inactivity_mins', String(mins));
    persistSettingsToServer({ inactivity_minutes: mins });
  };

  const handleRadiusChange = (val) => {
    setAlertRadius(val);
    localStorage.setItem('crimesense_setting_radius', val);
    persistSettingsToServer({ alert_radius_m: parseInt(val, 10) });
  };

  const handleLogout = async () => {
    if (logout) await logout();
    navigate('/login');
  };

  const phoneVal = validateAndFormatPhone(cPhone);

  return (
    <div className="flex-1 p-4 pb-28 space-y-5 max-w-md mx-auto w-full text-slate-900">
      {/* Header */}
      <div className="pt-2">
        <h1 className="text-xl font-extrabold tracking-tight text-slate-900">Settings & Safety</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Manage your profile, emergency contacts, privacy, and safety alert rules
        </p>
      </div>

      {profileSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{profileSuccessMsg}</span>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SECTION 1: PROFILE                                                    */}
      {/* ===================================================================== */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-red-600" />
            <h2 className="text-sm font-bold text-slate-800">1. User Profile</h2>
          </div>
          <button
            type="button"
            onClick={() => setIsEditingProfile(!isEditingProfile)}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 min-h-[36px]"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>{isEditingProfile ? 'Close' : 'Edit Profile'}</span>
          </button>
        </div>

        {/* User Card */}
        <div className="flex items-center gap-3.5 bg-slate-50/80 p-3.5 rounded-xl border border-slate-200/60">
          <div className="w-13 h-13 rounded-2xl bg-gradient-to-tr from-red-600 to-rose-500 text-white flex items-center justify-center font-bold text-2xl shadow-sm shrink-0">
            {profileAvatar.length <= 2 ? profileAvatar : (user?.name ? user.name[0].toUpperCase() : '🛡️')}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-bold text-slate-900 truncate">{user?.name || 'CrimeSense User'}</h3>
            <p className="text-xs text-slate-500 truncate">{user?.email || 'user@crimesense.com'}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                Active Account
              </span>
              {user?.role === 'admin' && (
                <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                  Admin Role
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Edit Profile Form */}
        {isEditingProfile && (
          <form onSubmit={handleSaveProfile} className="p-3.5 bg-slate-100/70 rounded-xl border border-slate-200 space-y-3">
            <span className="text-xs font-bold text-slate-800 block">Edit Profile Information</span>
            <div>
              <label className="text-[11px] font-medium text-slate-600 block mb-1">Full Name</label>
              <input
                type="text"
                required
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-xs focus:outline-none focus:ring-1 focus:ring-red-500"
                placeholder="Enter your name"
              />
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-600 block mb-1">Avatar Icon Preset</label>
              <div className="flex flex-wrap gap-1.5">
                {AVATAR_PRESETS.map((icon) => (
                  <button
                    key={icon}
                    type="button"
                    onClick={() => setProfileAvatar(icon)}
                    className={`w-9 h-9 rounded-lg text-lg flex items-center justify-center transition-all ${
                      profileAvatar === icon
                        ? 'bg-red-600 text-white ring-2 ring-red-400 scale-105'
                        : 'bg-white hover:bg-slate-200 border border-slate-200'
                    }`}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2 pt-1">
              <button
                type="submit"
                disabled={savingProfile}
                className="flex-1 py-2 rounded-lg bg-red-600 text-white text-xs font-bold min-h-[38px] hover:bg-red-700 transition-colors"
              >
                {savingProfile ? 'Saving...' : 'Save Profile'}
              </button>
              <button
                type="button"
                onClick={() => setIsEditingProfile(false)}
                className="px-3 py-2 rounded-lg bg-slate-200 text-slate-700 text-xs font-bold min-h-[38px]"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Profile Actions: Admin link, Logout, Delete Account */}
        <div className="pt-1 flex flex-col gap-2">
          {user?.role === 'admin' && (
            <button
              type="button"
              onClick={() => navigate('/admin')}
              className="w-full py-2.5 px-3 rounded-xl bg-blue-50 text-blue-700 border border-blue-200 text-xs font-bold flex items-center justify-between hover:bg-blue-100 transition-colors min-h-[44px]"
            >
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-600" />
                <span>Go to Admin Intelligence Portal</span>
              </div>
              <ChevronRight className="w-4 h-4" />
            </button>
          )}

          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={handleLogout}
              className="py-2.5 px-3 rounded-xl bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold flex items-center justify-center gap-1.5 hover:bg-slate-200 transition-colors min-h-[44px]"
            >
              <LogOut className="w-4 h-4 text-slate-600" />
              <span>Log Out</span>
            </button>

            <button
              type="button"
              onClick={() => setShowDeleteAccountModal(true)}
              className="py-2.5 px-3 rounded-xl bg-red-50 text-red-700 border border-red-200 text-xs font-bold flex items-center justify-center gap-1.5 hover:bg-red-100 transition-colors min-h-[44px]"
            >
              <Trash2 className="w-4 h-4 text-red-600" />
              <span>Delete Account</span>
            </button>
          </div>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* SECTION 2: SOS EMERGENCY CONTACTS                                     */}
      {/* ===================================================================== */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-red-600" />
            <h2 className="text-sm font-bold text-slate-800">2. SOS Emergency Contacts</h2>
          </div>
          <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
            {contacts.length}/5 configured
          </span>
        </div>
        <p className="text-xs text-slate-500">
          Emergency contacts receive instant automated SMS/WhatsApp alerts with your live coordinates during manual SOS or inactive Red-Zone situations.
        </p>

        {/* Test message result notification banner */}
        {testResult && (
          <div
            className={`p-3 rounded-xl border text-xs space-y-1.5 ${
              testResult.success
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : 'bg-red-50 border-red-200 text-red-900'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-bold flex items-center gap-1.5">
                {testResult.success ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertCircle className="w-4 h-4 text-red-600" />}
                {testResult.success ? `Test Message Dispatched to ${testResult.contactName}` : 'Test Message Failed'}
              </span>
              <button
                type="button"
                onClick={() => setTestResult(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[11px] opacity-90">{testResult.message}</p>
            {testResult.preview && (
              <pre className="p-2 bg-white/70 rounded-lg text-[10px] text-slate-700 whitespace-pre-wrap font-mono border border-emerald-200/60">
                {testResult.preview}
              </pre>
            )}
          </div>
        )}

        {/* Contact List */}
        <div className="space-y-2">
          {contacts.map((c) => (
            <div
              key={c.id}
              className={`p-3 rounded-xl border transition-all ${
                c.is_primary ? 'border-red-300 bg-red-50/40' : 'border-slate-200 bg-slate-50/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-xs text-slate-900">{c.name}</span>
                    <span className="text-[10px] text-slate-500 bg-slate-200/70 px-1.5 py-0.2 rounded font-medium">
                      {c.relationship}
                    </span>
                    {c.is_primary && (
                      <span className="text-[9px] font-black text-red-700 bg-red-100 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                        <Star className="w-2.5 h-2.5 fill-current" />
                        <span>Primary</span>
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-600 font-mono block mt-0.5">{c.phone}</span>
                </div>

                <div className="flex items-center gap-1">
                  {!c.is_primary && (
                    <button
                      type="button"
                      onClick={() => handleSetPrimary(c)}
                      className="p-1.5 text-slate-400 hover:text-amber-500 rounded-lg min-h-[36px] min-w-[36px] flex items-center justify-center"
                      title="Set as Primary SOS Contact"
                      aria-label="Set as Primary"
                    >
                      <Star className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => openEditContactForm(c)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg min-h-[36px] min-w-[36px] flex items-center justify-center"
                    title="Edit Contact"
                    aria-label="Edit Contact"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDeleteContact(c.id, c.name)}
                    className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg min-h-[36px] min-w-[36px] flex items-center justify-center"
                    title="Remove Contact"
                    aria-label="Remove Contact"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Send Test Message Action Button */}
              <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between">
                <span className="text-[10px] text-slate-400">Verify contact reception:</span>
                <button
                  type="button"
                  onClick={() => handleSendTestMessage(c)}
                  disabled={testingContactId === c.id}
                  className="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-300 rounded-lg text-[11px] font-semibold text-slate-700 flex items-center gap-1.5 transition-colors disabled:opacity-50 min-h-[32px]"
                >
                  {testingContactId === c.id ? (
                    <>
                      <RefreshCw className="w-3 h-3 animate-spin text-blue-600" />
                      <span>Sending Test...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3 h-3 text-red-600" />
                      <span>Send Test Message</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Add / Edit Contact Form */}
        {isAddingContact ? (
          <form onSubmit={handleContactSubmit} className="p-3.5 bg-slate-100/80 rounded-xl border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800">
                {editingContact ? `Edit '${editingContact.name}'` : 'Add New SOS Emergency Contact'}
              </span>
              {hasContactPicker && !editingContact && (
                <button
                  type="button"
                  onClick={handlePickDevice}
                  className="text-[11px] font-bold text-blue-600 flex items-center gap-1"
                >
                  <Smartphone className="w-3 h-3" />
                  <span>Pick from Device</span>
                </button>
              )}
            </div>

            {contactError && (
              <p className="text-xs text-red-600 font-medium bg-red-50 p-2 rounded-lg border border-red-200">
                {contactError}
              </p>
            )}

            <input
              type="text"
              required
              placeholder="Contact Full Name"
              value={cName}
              onChange={(e) => setCName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-xs focus:outline-none focus:ring-1 focus:ring-red-500"
            />

            <input
              type="tel"
              required
              placeholder="Mobile Number (e.g. 9876543210 or +91...)"
              value={cPhone}
              onChange={(e) => setCPhone(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-xs focus:outline-none focus:ring-1 focus:ring-red-500"
            />
            {cPhone && phoneVal.isValid && (
              <p className="text-[10px] text-emerald-600 font-mono">
                Validated E.164: {phoneVal.formatted}
              </p>
            )}

            <select
              value={cRel}
              onChange={(e) => setCRel(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-xs focus:outline-none"
            >
              {RELATIONSHIP_OPTIONS.map((rel) => (
                <option key={rel} value={rel}>
                  {rel}
                </option>
              ))}
            </select>

            <label className="flex items-center gap-2 pt-1 cursor-pointer">
              <input
                type="checkbox"
                checked={cPrimary}
                onChange={(e) => setCPrimary(e.target.checked)}
                className="w-4 h-4 rounded text-red-600 accent-red-600 cursor-pointer"
              />
              <span className="text-xs text-slate-700 font-medium">Set as Primary Emergency Contact</span>
            </label>

            <div className="flex gap-2 pt-1">
              <button
                type="submit"
                disabled={savingContact}
                className="flex-1 py-2 rounded-lg bg-red-600 text-white text-xs font-bold min-h-[38px] hover:bg-red-700 transition-colors"
              >
                {savingContact ? 'Saving...' : editingContact ? 'Update Contact' : 'Save Contact'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsAddingContact(false);
                  setEditingContact(null);
                }}
                className="px-3 py-2 rounded-lg bg-slate-200 text-slate-700 text-xs font-bold min-h-[38px]"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          contacts.length < 5 && (
            <button
              type="button"
              onClick={openAddContactForm}
              className="w-full py-2.5 px-3 border border-dashed border-red-300 text-red-600 hover:bg-red-50 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all min-h-[42px]"
            >
              <UserPlus className="w-4 h-4" />
              <span>Add Emergency Contact ({5 - contacts.length} remaining)</span>
            </button>
          )
        )}
      </div>

      {/* ===================================================================== */}
      {/* SECTION 3: LOCATION & PRIVACY                                         */}
      {/* ===================================================================== */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-bold text-slate-800">3. Location & Privacy</h2>
          </div>
          <button
            type="button"
            onClick={() => setShowRevokeGuide(!showRevokeGuide)}
            className="text-[11px] font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>How to revoke</span>
          </button>
        </div>

        {/* Master Location Access Toggle */}
        <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
          <div className="space-y-0.5 pr-2">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-bold text-slate-800">Location Access (Master Switch)</span>
            </div>
            <p className="text-[11px] text-slate-500">
              When ON: enables live GPS tracking, 30s safety heartbeats, and automated Red-Zone alarms.
            </p>
          </div>

          <label className="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={locationAccess}
              onChange={handleToggleLocationAccess}
              className="sr-only peer"
              aria-label="Toggle location access"
            />
            <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Clear warning banner when location access is turned OFF */}
        {!locationAccess && (
          <div className="p-3 bg-amber-50 border border-amber-300 text-amber-900 rounded-xl text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-amber-800">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Location Access Disabled — Safety Warning</span>
            </div>
            <p className="text-[11px] text-amber-700 leading-relaxed">
              Automated Red-Zone entry detection, 30-second heartbeats, and inactivity distress alerts are currently <strong>DISABLED</strong>.
              Manual location search and map navigation will continue to work normally.
            </p>
          </div>
        )}

        {/* Allow Admins to see live location toggle */}
        <div className="p-3 bg-slate-50/70 rounded-xl border border-slate-200 flex items-center justify-between">
          <div className="space-y-0.5 pr-2">
            <span className="text-xs font-bold text-slate-800 block">Allow admins to see my live location</span>
            <p className="text-[11px] text-slate-500">
              Permits authorized police and safety administrators to view your live GPS position on the monitoring map.
            </p>
          </div>
          <input
            type="checkbox"
            checked={allowAdminLiveLocation}
            onChange={handleToggleAdminLiveLocation}
            className="w-5 h-5 rounded text-blue-600 accent-blue-600 cursor-pointer shrink-0 min-h-[44px] min-w-[24px]"
            aria-label="Allow admins to see my live location"
          />
        </div>

        {/* Delete Location History Action */}
        <div className="pt-1 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-800 block">Location History Retention</span>
            <p className="text-[11px] text-slate-500">Purged automatically after 30 days or delete on demand</p>
          </div>
          <button
            type="button"
            onClick={handleDeleteLocationHistory}
            disabled={deletingLocations}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 rounded-xl text-xs font-bold transition-colors disabled:opacity-50 min-h-[40px]"
          >
            {deletingLocations ? 'Deleting...' : 'Delete My Location History'}
          </button>
        </div>

        {locationDeletedMsg && (
          <p className="text-xs font-semibold text-emerald-700 bg-emerald-50 p-2.5 rounded-lg border border-emerald-200">
            {locationDeletedMsg}
          </p>
        )}

        {/* Interactive In-App Explainer: How to Revoke Browser Permissions */}
        {showRevokeGuide && (
          <div className="p-3.5 bg-slate-100 rounded-xl border border-slate-300 text-xs space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800 flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-blue-600" />
                <span>How to Revoke Browser Location Permissions</span>
              </span>
              <button
                type="button"
                onClick={() => setShowRevokeGuide(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex gap-1 border-b border-slate-200 pb-1.5 overflow-x-auto">
              {[
                { id: 'chrome', label: 'Google Chrome' },
                { id: 'safari', label: 'Apple Safari' },
                { id: 'ios', label: 'iOS / iPhone' },
                { id: 'android', label: 'Android' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedBrowserTab(tab.id)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-bold whitespace-nowrap transition-all ${
                    selectedBrowserTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {selectedBrowserTab === 'chrome' && (
              <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-600 leading-relaxed">
                <li>Click the <strong>Tune / Padlock icon</strong> on the left side of the address bar.</li>
                <li>Toggle <strong>Location</strong> switch to <strong>Blocked / Off</strong>.</li>
                <li>Reload the page to apply the updated permission immediately.</li>
              </ol>
            )}

            {selectedBrowserTab === 'safari' && (
              <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-600 leading-relaxed">
                <li>Click <strong>Safari</strong> in the top menu bar &gt; <strong>Settings...</strong></li>
                <li>Click the <strong>Websites</strong> tab, then select <strong>Location</strong> in the left pane.</li>
                <li>Find <strong>CrimeSense</strong> and set permission to <strong>Deny</strong>.</li>
              </ol>
            )}

            {selectedBrowserTab === 'ios' && (
              <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-600 leading-relaxed">
                <li>Open iPhone <strong>Settings</strong> &gt; <strong>Privacy & Security</strong> &gt; <strong>Location Services</strong>.</li>
                <li>Tap <strong>Safari Websites</strong> (or CrimeSense).</li>
                <li>Select <strong>Never</strong> or toggle <strong>Precise Location OFF</strong>.</li>
              </ol>
            )}

            {selectedBrowserTab === 'android' && (
              <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-600 leading-relaxed">
                <li>Open Chrome, tap the <strong>3 dots (⋮)</strong> &gt; <strong>Settings</strong>.</li>
                <li>Tap <strong>Site Settings</strong> &gt; <strong>Location</strong>.</li>
                <li>Locate CrimeSense under 'Allowed' and tap <strong>Block / Clear & Reset</strong>.</li>
              </ol>
            )}
          </div>
        )}
      </div>

      {/* ===================================================================== */}
      {/* SECTION 4: ALERTS CONFIGURATION                                       */}
      {/* ===================================================================== */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-red-600" />
          <h2 className="text-sm font-bold text-slate-800">4. Safety Alerts & Automation</h2>
        </div>

        {/* Red-Zone Auto Alert Toggle */}
        <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
          <div className="space-y-0.5 pr-2">
            <span className="text-xs font-bold text-slate-800 block">Red-Zone Proximity & Auto Alert</span>
            <p className="text-[11px] text-slate-500">
              Vibrate, trigger push warnings, and initiate inactivity monitoring when inside high-risk RED zones.
            </p>
          </div>
          <input
            type="checkbox"
            checked={redZoneAlert}
            onChange={handleToggleRedZoneAlert}
            className="w-5 h-5 rounded text-blue-600 accent-blue-600 cursor-pointer shrink-0 min-h-[44px] min-w-[24px]"
            aria-label="Toggle red zone auto alert"
          />
        </div>

        {/* Inactivity Duration Selector (5 / 10 / 15 / 30 min) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">Inactivity Warning Trigger Threshold</span>
            <span className="text-xs font-extrabold text-red-600 bg-red-50 px-2.5 py-0.5 rounded-full">
              {inactivityMinutes} minutes
            </span>
          </div>
          <p className="text-[11px] text-slate-500">
            If stationary without movement (&gt;30m) or screen touch in a RED zone for this duration, a 60-second safety check-in prompt fires.
          </p>

          <div className="grid grid-cols-4 gap-2 pt-1">
            {[5, 10, 15, 30].map((mins) => (
              <button
                key={mins}
                type="button"
                onClick={() => handleInactivityMinutesChange(mins)}
                className={`py-2 rounded-xl text-xs font-bold transition-all min-h-[44px] ${
                  inactivityMinutes === mins
                    ? 'bg-red-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {mins} min
              </button>
            ))}
          </div>
        </div>

        {/* Alert Radius Selector (500m / 1000m / 2000m) */}
        <div className="space-y-2 pt-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">Zone Warning Perimeter Radius</span>
            <span className="text-xs font-extrabold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full">
              {alertRadius} meters
            </span>
          </div>
          <p className="text-[11px] text-slate-500">
            Geographic search perimeter evaluated for crime hot-spot clusters and risk rating.
          </p>

          <div className="grid grid-cols-3 gap-2 pt-1">
            {[
              { val: '500', label: '500m (0.5 km)' },
              { val: '1000', label: '1000m (1.0 km)' },
              { val: '2000', label: '2000m (2.0 km)' },
            ].map((item) => (
              <button
                key={item.val}
                type="button"
                onClick={() => handleRadiusChange(item.val)}
                className={`py-2 px-1 rounded-xl text-xs font-bold transition-all min-h-[44px] ${
                  alertRadius === item.val
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* SECTION 5: ABOUT & PRIVACY                                            */}
      {/* ===================================================================== */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-3">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-slate-700" />
          <h2 className="text-sm font-bold text-slate-800">5. About CrimeSense</h2>
        </div>

        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
          <div>
            <span className="font-bold text-slate-800 block">CrimeSense SafeCity Engine</span>
            <span className="text-[11px] text-slate-500">Production Build</span>
          </div>
          <span className="font-mono text-xs font-bold text-slate-700 bg-white px-2.5 py-1 rounded-lg border border-slate-300">
            v2.4.0
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            type="button"
            onClick={() => setShowDataSources(true)}
            className="p-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl text-left text-xs space-y-1 transition-colors min-h-[48px]"
          >
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-blue-600" />
              <span>Data Sources</span>
            </span>
            <span className="text-[10px] text-slate-500 block">Verified Open & Police Portals</span>
          </button>

          <button
            type="button"
            onClick={() => setShowPrivacyPolicy(true)}
            className="p-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl text-left text-xs space-y-1 transition-colors min-h-[48px]"
          >
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-emerald-600" />
              <span>Privacy Policy</span>
            </span>
            <span className="text-[10px] text-slate-500 block">30-day purge & encryption</span>
          </button>
        </div>

        {/* PWA Install Button */}
        {!installed && (
          <div className="pt-2">
            <button
              type="button"
              onClick={handleInstallApp}
              className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs font-bold shadow-xs hover:opacity-95 transition-all flex items-center justify-center gap-2 min-h-[44px]"
            >
              <Download className="w-4 h-4" />
              <span>Install CrimeSense Mobile App</span>
            </button>
          </div>
        )}
      </div>

      {/* ===================================================================== */}
      {/* MODAL: DATA SOURCES                                                   */}
      {/* ===================================================================== */}
      {showDataSources && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-sm w-full p-5 space-y-4 shadow-2xl border border-slate-100">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Globe className="w-4 h-4 text-blue-600" />
                <span>Verified Data Sources</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowDataSources(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2.5 text-xs text-slate-600 leading-relaxed max-h-72 overflow-y-auto pr-1">
              <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-bold text-slate-800 block">1. Tamil Nadu State Police Open Data Portal</span>
                <span className="text-[11px] text-slate-500">Official FIR public crime registry and station incident indices.</span>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-bold text-slate-800 block">2. National Crime Records Bureau (NCRB)</span>
                <span className="text-[11px] text-slate-500">Historical violent crime statistics and trend analysis models.</span>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-bold text-slate-800 block">3. OpenStreetMap & Nominatim Geocoding</span>
                <span className="text-[11px] text-slate-500">High-precision road network geometry and landmark coordinates.</span>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-bold text-slate-800 block">4. CrimeSense Crowd-Verified Safety Feed</span>
                <span className="text-[11px] text-slate-500">Community safety reports audited for spam and veracity.</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowDataSources(false)}
              className="w-full py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs"
            >
              Got it
            </button>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: PRIVACY POLICY                                                 */}
      {/* ===================================================================== */}
      {showPrivacyPolicy && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-5 space-y-4 shadow-2xl border border-slate-100 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between shrink-0">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-600" />
                <span>CrimeSense Privacy Policy</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowPrivacyPolicy(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 text-xs text-slate-600 leading-relaxed pr-1">
              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-900">
                <span className="font-bold block">Zero Data Commercialization</span>
                <p className="text-[11px] mt-0.5">We do not sell, rent, or monetize your location data or personal contact lists with advertisers.</p>
              </div>

              <div>
                <h4 className="font-bold text-slate-800 mb-1">1. Automatic 30-Day Purge</h4>
                <p className="text-[11px] text-slate-500">
                  All GPS location history records are automatically purged from the server after 30 days. You can also click "Delete My Location History" at any time.
                </p>
              </div>

              <div>
                <h4 className="font-bold text-slate-800 mb-1">2. Emergency Distress Protocol</h4>
                <p className="text-[11px] text-slate-500">
                  When an SOS distress signal is triggered, your coordinates are transmitted over TLS encryption to Twilio telecommunication relays and designated emergency contacts.
                </p>
              </div>

              <div>
                <h4 className="font-bold text-slate-800 mb-1">3. Complete Account Erasure</h4>
                <p className="text-[11px] text-slate-500">
                  Deleting your account removes all authentication credentials, emergency contacts, saved places, shareable links, and location history immediately.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowPrivacyPolicy(false)}
              className="w-full py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs shrink-0"
            >
              Close Policy
            </button>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: DELETE ACCOUNT CONFIRMATION                                    */}
      {/* ===================================================================== */}
      {showDeleteAccountModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-sm w-full p-5 space-y-4 shadow-2xl border border-red-200">
            <div className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <h3 className="text-sm font-bold text-slate-900">Delete CrimeSense Account?</h3>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              This action is <strong>permanent and irreversible</strong>. It will delete all your personal data, including:
            </p>

            <ul className="text-[11px] text-slate-500 list-disc list-inside space-y-1 bg-red-50/60 p-3 rounded-xl border border-red-200/60">
              <li>User account and login credentials</li>
              <li>All registered SOS emergency contacts</li>
              <li>Saved destination places & custom pins</li>
              <li>Complete location history tracking logs</li>
              <li>Active shareable link tokens</li>
            </ul>

            <div className="space-y-1.5 pt-1">
              <label className="text-[11px] font-bold text-slate-700 block">
                Type <span className="text-red-600 font-mono">DELETE</span> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="Type DELETE"
                className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-300 text-xs font-mono uppercase focus:outline-none focus:ring-1 focus:ring-red-500"
              />
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={deletingAccount || deleteConfirmText.trim().toUpperCase() !== 'DELETE'}
                className="flex-1 py-2.5 rounded-xl bg-red-600 text-white font-bold text-xs disabled:opacity-40 min-h-[44px] hover:bg-red-700 transition-colors"
              >
                {deletingAccount ? 'Deleting...' : 'Permanently Delete'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowDeleteAccountModal(false);
                  setDeleteConfirmText('');
                }}
                className="px-4 py-2.5 rounded-xl bg-slate-200 text-slate-700 font-bold text-xs min-h-[44px]"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
