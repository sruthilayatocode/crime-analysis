import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  PhoneCall,
  UserPlus,
  Trash2,
  Radio,
  CheckCircle2,
  X,
  Star,
  Smartphone,
  AlertCircle,
  MapPin,
  ExternalLink,
  Bell,
  BellRing,
  ArrowLeft,
} from 'lucide-react';
import { useSOS } from '../../context/SOSContext';
import {
  sosService,
  validateAndFormatPhone,
  pickContactFromDevice,
} from '../../services/sosService';
import { sosContactsStore, triggerSOSNotification } from '../../services/firebase';

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

export default function UserSOS() {
  const navigate = useNavigate();
  const {
    contacts,
    refreshContacts,
    startSOSCountdown,
    isCountingDown,
    countdown,
    cancelCountdown,
    activeSosEvent,
    resolveSOS,
    isLiveTracking,
    extendLiveLocationSharing,
    requestPushPermission,
    notificationPermissionGranted,
  } = useSOS();

  const [isAddingContact, setIsAddingContact] = useState(false);
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [contactRelation, setContactRelation] = useState('Family');
  const [isPrimary, setIsPrimary] = useState(false);
  const [savingContact, setSavingContact] = useState(false);
  const [contactError, setContactError] = useState('');

  // Press & Hold State for the Main Center Button
  const [isHolding, setIsHolding] = useState(false);
  const [holdProgress, setHoldProgress] = useState(0);
  const holdTimerRef = useRef(null);
  const holdIntervalRef = useRef(null);
  const [hasContactPicker] = useState(
    typeof window !== 'undefined' && 'contacts' in navigator && 'ContactsManager' in window
  );

  const startHold = () => {
    if (activeSosEvent || isCountingDown) return;
    setIsHolding(true);
    setHoldProgress(0);
    const startTime = Date.now();
    const duration = 2000;

    holdIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const pct = Math.min(100, (elapsed / duration) * 100);
      setHoldProgress(pct);
    }, 40);

    holdTimerRef.current = setTimeout(() => {
      clearHold();
      startSOSCountdown();
    }, duration);
  };

  const clearHold = () => {
    setIsHolding(false);
    setHoldProgress(0);
    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
    if (holdIntervalRef.current) {
      clearInterval(holdIntervalRef.current);
      holdIntervalRef.current = null;
    }
  };

  const handlePickDeviceContact = async () => {
    try {
      const picked = await pickContactFromDevice();
      if (picked) {
        if (picked.name) setContactName(picked.name);
        if (picked.phone) setContactPhone(picked.phone);
      }
    } catch {
      // Fallback
    }
  };

  const handleAddContact = async (e) => {
    e.preventDefault();
    setContactError('');

    if (!contactName.trim() || !contactPhone.trim()) {
      setContactError('Please fill in both name and phone number.');
      return;
    }

    const val = validateAndFormatPhone(contactPhone.trim());
    if (!val.isValid) {
      setContactError(val.error);
      return;
    }

    if (contacts.length >= 5) {
      setContactError('Maximum 5 emergency contacts allowed.');
      return;
    }

    setSavingContact(true);
    const newEntry = {
      id: Date.now(),
      name: contactName.trim(),
      phone: val.formatted,
      relationship: contactRelation,
      is_primary: isPrimary || contacts.length === 0,
    };
    // Immediately persist locally so reload retains it even if network stalls
    sosContactsStore.persistContacts([...contacts, newEntry]);

    try {
      await sosService.addContact({
        name: contactName.trim(),
        phone: val.formatted,
        relationship: contactRelation,
        is_primary: isPrimary || contacts.length === 0,
      });
      await refreshContacts();
      setContactName('');
      setContactPhone('');
      setIsPrimary(false);
      setIsAddingContact(false);
    } catch (err) {
      setContactError(err.message || 'Failed to add contact');
    } finally {
      setSavingContact(false);
    }
  };

  const handleDeleteContact = async (id, name) => {
    if (contacts.length <= 1) {
      alert('You must maintain at least 1 emergency contact for safety.');
      return;
    }
    if (window.confirm(`Remove '${name}' from emergency contacts?`)) {
      const remaining = contacts.filter((c) => c.id !== id);
      sosContactsStore.persistContacts(remaining);
      try {
        await sosService.deleteContact(id);
        await refreshContacts();
      } catch (err) {
        alert(err.message || 'Failed to delete contact');
      }
    }
  };

  const handleMakePrimary = async (c) => {
    try {
      await sosService.updateContact(c.id, { is_primary: true });
      await refreshContacts();
    } catch (err) {
      alert(err.message || 'Failed to update primary contact');
    }
  };

  const emergencyServices = [
    { label: 'Police / National Emergency', number: '112', desc: 'Immediate Police & Emergency Response' },
    { label: 'Women Safety Helpline', number: '1091', desc: '24/7 Women Protection & Support' },
    { label: 'Ambulance & Medical', number: '108', desc: 'Emergency Medical & Paramedic' },
  ];

  const phoneVal = validateAndFormatPhone(contactPhone);

  return (
    <div className="flex-1 p-4 pb-24 space-y-5 max-w-md mx-auto w-full">
      {/* Top Header */}
      <div className="relative flex items-center justify-center pt-2">
        <button
          type="button"
          onClick={() => navigate('/user')}
          className="absolute left-0 p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-200/60 active:scale-95 transition-all flex items-center justify-center"
          title="Back to Home"
          aria-label="Back to Home"
        >
          <ArrowLeft className="w-5 h-5 stroke-[2.5]" />
        </button>
        <div className="text-center">
          <h1 className="text-xl font-black text-slate-900 tracking-tight flex items-center justify-center gap-2">
            <ShieldAlert className="w-6 h-6 text-red-600 stroke-[2.5]" />
            <span>Emergency Assistance</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Press & hold 2 seconds to dispatch instant distress alerts
          </p>
        </div>
      </div>

      {/* Main SOS Trigger Widget */}
      <div className="flex flex-col items-center justify-center py-2">
        {activeSosEvent ? (
          <div className="w-full bg-gradient-to-br from-red-600 to-rose-700 text-white rounded-3xl p-5 text-center space-y-3.5 shadow-xl animate-pulse border-2 border-red-400">
            <div className="inline-flex p-3 rounded-full bg-white/20">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <div>
              <span className="text-[10px] font-black uppercase tracking-wider bg-black/25 px-2.5 py-0.5 rounded-full">
                Broadcast Active
              </span>
              <h2 className="text-lg font-black uppercase tracking-wider mt-1">
                Distress Signal Active!
              </h2>
              <p className="text-xs text-red-100 mt-0.5">
                Live GPS coordinates sent to your {contacts.length} emergency contact(s).
              </p>
            </div>

            <div className="flex flex-col gap-2 pt-1">
              <button
                type="button"
                onClick={resolveSOS}
                className="w-full py-3 rounded-2xl bg-white text-emerald-800 font-black text-xs shadow-md active:scale-95 transition-all flex items-center justify-center gap-1.5 min-h-[44px]"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>I'm Safe &ndash; Resolve Alert</span>
              </button>

              <button
                type="button"
                onClick={extendLiveLocationSharing}
                className="w-full py-2.5 rounded-2xl bg-red-800/60 hover:bg-red-800 text-white font-bold text-xs transition-all flex items-center justify-center gap-1 min-h-[40px]"
              >
                <Radio className="w-3.5 h-3.5" />
                <span>Extend Live Location (1 Hour)</span>
              </button>
            </div>
          </div>
        ) : isCountingDown ? (
          <div className="flex flex-col items-center space-y-3 p-4 bg-red-50 border border-red-200 rounded-3xl w-full">
            <div className="relative flex items-center justify-center w-28 h-28 rounded-full bg-red-600 text-white shadow-xl animate-pulse">
              <span className="text-4xl font-black">{countdown}</span>
            </div>
            <p className="text-xs font-bold text-red-700">
              Dispatching SOS alert in {countdown}s...
            </p>
            <button
              type="button"
              onClick={cancelCountdown}
              className="w-full py-2.5 rounded-xl bg-slate-800 text-white text-xs font-bold transition-all min-h-[40px]"
            >
              Cancel / Abort Alert
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-2 select-none">
            <div className="relative flex items-center justify-center">
              {/* Outer pulsing ring */}
              <span className="absolute -inset-2 rounded-full bg-red-500/20 animate-ping pointer-events-none" />

              <button
                type="button"
                aria-label="Activate Emergency SOS Signal - Press and hold 2 seconds"
                onMouseDown={startHold}
                onMouseUp={clearHold}
                onMouseLeave={clearHold}
                onTouchStart={startHold}
                onTouchEnd={clearHold}
                onDoubleClick={startSOSCountdown}
                className="group relative flex flex-col items-center justify-center w-40 h-40 rounded-full bg-gradient-to-tr from-red-600 via-red-500 to-rose-600 text-white shadow-[0_12px_40px_rgba(239,68,68,0.45)] hover:scale-102 active:scale-95 transition-all duration-200 border-4 border-white"
              >
                {/* Hold SVG Progress Ring */}
                {isHolding && (
                  <svg className="absolute -inset-1 w-[170px] h-[170px] transform -rotate-90 pointer-events-none" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="46"
                      className="stroke-white"
                      strokeWidth="6"
                      fill="transparent"
                      strokeDasharray="289"
                      strokeDashoffset={289 - (289 * holdProgress) / 100}
                      strokeLinecap="round"
                    />
                  </svg>
                )}

                <ShieldAlert className="w-12 h-12 stroke-[2.2]" />
                <span className="text-2xl font-black tracking-widest mt-1">SOS</span>
                <span className="text-[10px] font-bold text-red-100 uppercase tracking-wider">
                  {isHolding ? `Holding ${Math.round(holdProgress)}%` : 'Hold 2 Seconds'}
                </span>
              </button>
            </div>

            <p className="text-[11px] text-slate-400 text-center max-w-xs pt-1">
              Press and hold for 2s (or double-tap) &bull; 5-second countdown follows
            </p>
          </div>
        )}
      </div>

      {/* Official Helplines */}
      <div className="space-y-2">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 px-1">
          Official Emergency Helplines
        </h2>
        <div className="grid grid-cols-1 gap-2">
          {emergencyServices.map((svc) => (
            <a
              key={svc.number}
              href={`tel:${svc.number}`}
              className="bg-white rounded-2xl p-3 border border-slate-200/80 shadow-2xs hover:border-red-300 transition-all flex items-center justify-between min-h-[52px]"
            >
              <div>
                <span className="text-xs sm:text-sm font-bold text-slate-800">{svc.label}</span>
                <p className="text-[11px] text-slate-500">{svc.desc}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs font-black text-red-600 bg-red-50 px-2.5 py-1 rounded-lg border border-red-100">
                  {svc.number}
                </span>
                <div className="w-9 h-9 rounded-xl bg-red-600 text-white flex items-center justify-center shadow-xs">
                  <PhoneCall className="w-4 h-4" />
                </div>
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* Firebase Push Notifications Status Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-2xl p-3.5 border border-indigo-800/40 shadow-sm flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/30">
            <BellRing className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-black text-white">Firebase SOS Alerts</span>
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                ACTIVE
              </span>
            </div>
            <p className="text-[10px] text-slate-300">Push notifications & alarm sirens enabled</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => {
            triggerSOSNotification({
              title: '🚨 CRIMESENSE SOS TEST ALERT',
              body: 'Firebase Push Notification is working perfectly! Siren & alerts are enabled.',
              urgent: false,
            });
          }}
          className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold rounded-xl shadow-xs transition-colors shrink-0"
        >
          Test Alert
        </button>
      </div>

      {/* Emergency Contacts Section */}
      <div className="space-y-2.5 pt-1">
        <div className="flex items-center justify-between px-1">
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Emergency SOS Contacts ({contacts.length}/5)
            </h2>
            <p className="text-[10px] text-slate-400">Notified instantly during SOS trigger</p>
          </div>

          {contacts.length < 5 && (
            <button
              type="button"
              onClick={() => setIsAddingContact(!isAddingContact)}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 min-h-[36px]"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          )}
        </div>

        {/* Add Contact Inline Form */}
        {isAddingContact && (
          <form
            onSubmit={handleAddContact}
            className="bg-white rounded-2xl p-4 border border-blue-200 shadow-sm space-y-3 animate-in fade-in-50"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800">Add New SOS Contact</h3>
              {hasContactPicker && (
                <button
                  type="button"
                  onClick={handlePickDeviceContact}
                  className="text-[11px] font-bold text-blue-600 flex items-center gap-1"
                >
                  <Smartphone className="w-3.5 h-3.5" />
                  <span>From Device</span>
                </button>
              )}
            </div>

            {contactError && (
              <div className="p-2.5 bg-red-50 text-red-700 text-xs rounded-xl flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{contactError}</span>
              </div>
            )}

            <div>
              <label className="block text-[11px] font-bold text-slate-600 mb-1">Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Ananya Sharma"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-600 mb-1">
                Mobile Number (Indian / E.164)
              </label>
              <input
                type="tel"
                required
                placeholder="e.g. 9876543210 or +91 98765 43210"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {contactPhone && phoneVal.isValid && (
                <p className="text-[10px] text-emerald-600 font-mono mt-0.5">
                  Valid: {phoneVal.formatted}
                </p>
              )}
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-600 mb-1">
                Relationship
              </label>
              <select
                value={contactRelation}
                onChange={(e) => setContactRelation(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs focus:outline-none"
              >
                {RELATIONSHIP_OPTIONS.map((rel) => (
                  <option key={rel} value={rel}>
                    {rel}
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={isPrimary}
                onChange={(e) => setIsPrimary(e.target.checked)}
                className="rounded border-slate-300 text-red-600 focus:ring-red-500"
              />
              <span>Set as Primary Contact</span>
            </label>

            <div className="flex gap-2 pt-1">
              <button
                type="submit"
                disabled={savingContact}
                className="flex-1 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold min-h-[40px]"
              >
                {savingContact ? 'Saving...' : 'Save Contact'}
              </button>
              <button
                type="button"
                onClick={() => setIsAddingContact(false)}
                className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold min-h-[40px]"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Contacts List */}
        <div className="space-y-2">
          {contacts.map((c) => (
            <div
              key={c.id}
              className={`bg-white rounded-2xl p-3 border shadow-2xs flex items-center justify-between ${
                c.is_primary ? 'border-red-300 bg-red-50/20' : 'border-slate-200/80'
              }`}
            >
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-slate-800">{c.name}</span>
                  <span className="text-[10px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded">
                    {c.relationship}
                  </span>
                  {c.is_primary && (
                    <span className="text-[9px] font-black text-red-700 bg-red-100 px-1.5 py-0.2 rounded-full flex items-center gap-0.5">
                      <Star className="w-2.5 h-2.5 fill-current" />
                      <span>Primary</span>
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 font-mono mt-0.5">{c.phone}</p>
              </div>

              <div className="flex items-center gap-1.5">
                {!c.is_primary && (
                  <button
                    type="button"
                    onClick={() => handleMakePrimary(c)}
                    className="p-1.5 text-slate-400 hover:text-amber-500 rounded-lg"
                    title="Set as primary"
                  >
                    <Star className="w-4 h-4" />
                  </button>
                )}
                <a
                  href={`tel:${c.phone}`}
                  className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 flex items-center justify-center min-h-[32px] min-w-[32px]"
                  aria-label={`Call ${c.name}`}
                >
                  <PhoneCall className="w-3.5 h-3.5" />
                </a>
                <button
                  type="button"
                  onClick={() => handleDeleteContact(c.id, c.name)}
                  className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg min-h-[32px] min-w-[32px] flex items-center justify-center"
                  aria-label={`Delete ${c.name}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
