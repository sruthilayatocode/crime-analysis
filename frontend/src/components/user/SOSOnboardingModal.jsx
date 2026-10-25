import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  UserPlus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  PhoneCall,
  Star,
  Users,
  Smartphone,
  Lock,
  LogIn,
} from 'lucide-react';
import { useSOS } from '../../context/SOSContext';
import { sosService, validateAndFormatPhone, pickContactFromDevice } from '../../services/sosService';
import { sosContactsStore } from '../../services/firebase';

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

export default function SOSOnboardingModal() {
  const { onboardingRequired, setOnboardingRequired, refreshContacts } = useSOS();
  const navigate = useNavigate();

  const [contactList, setContactList] = useState([
    { id: 1, name: '', phone: '', relationship: 'Family', is_primary: true },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isAuthError, setIsAuthError] = useState(false);
  const [hasContactPicker] = useState(
    typeof window !== 'undefined' && 'contacts' in navigator && 'ContactsManager' in window
  );

  if (!onboardingRequired) return null;

  const handleFieldChange = (id, field, value) => {
    setContactList((prev) =>
      prev.map((c) => {
        if (c.id === id) {
          return { ...c, [field]: value };
        }
        return c;
      })
    );
  };

  const handleSetPrimary = (id) => {
    setContactList((prev) =>
      prev.map((c) => ({
        ...c,
        is_primary: c.id === id,
      }))
    );
  };

  const handleAddRow = () => {
    if (contactList.length >= 5) return;
    const newId = Date.now();
    setContactList((prev) => [
      ...prev,
      {
        id: newId,
        name: '',
        phone: '',
        relationship: 'Friend',
        is_primary: false,
      },
    ]);
  };

  const handleRemoveRow = (id) => {
    if (contactList.length <= 1) return;
    setContactList((prev) => {
      const filtered = prev.filter((c) => c.id !== id);
      // Ensure at least one is primary
      if (!filtered.some((c) => c.is_primary) && filtered.length > 0) {
        filtered[0].is_primary = true;
      }
      return filtered;
    });
  };

  const handlePickContact = async (id) => {
    try {
      const picked = await pickContactFromDevice();
      if (picked) {
        setContactList((prev) =>
          prev.map((c) => {
            if (c.id === id) {
              return {
                ...c,
                name: picked.name || c.name,
                phone: picked.phone || c.phone,
              };
            }
            return c;
          })
        );
      }
    } catch (err) {
      alert('Could not access device contacts. Please type the number manually.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setIsAuthError(false);

    // Validate contacts
    const validPayload = [];
    for (let i = 0; i < contactList.length; i++) {
      const c = contactList[i];
      const trimmedName = c.name.trim();
      const trimmedPhone = c.phone.trim();

      if (!trimmedName) {
        setErrorMsg(`Please provide a name for Contact #${i + 1}.`);
        return;
      }

      const val = validateAndFormatPhone(trimmedPhone);
      if (!val.isValid) {
        setErrorMsg(`Contact #${i + 1} (${trimmedName}): ${val.error}`);
        return;
      }

      validPayload.push({
        name: trimmedName,
        phone: val.formatted,
        relationship: c.relationship,
        is_primary: Boolean(c.is_primary),
      });
    }

    if (validPayload.length < 1) {
      setErrorMsg('At least 1 emergency contact is required.');
      return;
    }

    // Ensure at least one is primary
    if (!validPayload.some((c) => c.is_primary)) {
      validPayload[0].is_primary = true;
    }

    setSubmitting(true);
    // Immediately persist to local storage so even if page reloads right now, contacts remain!
    sosContactsStore.persistContacts(validPayload);
    try {
      await sosService.bulkSaveContacts(validPayload);
      await refreshContacts();
      setOnboardingRequired(false);
    } catch (err) {
      const msg = err.message || '';
      // Detect authentication / session errors
      if (
        msg.toLowerCase().includes('authentication') ||
        msg.toLowerCase().includes('unauthorized') ||
        msg.toLowerCase().includes('token') ||
        msg.toLowerCase().includes('login')
      ) {
        setIsAuthError(true);
      } else {
        setErrorMsg(msg || 'Failed to save emergency contacts.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-white text-slate-900 rounded-3xl max-w-md w-full max-h-[92vh] flex flex-col shadow-2xl border border-slate-200/80 overflow-hidden">
        {/* Header with emergency shield badge */}
        <div className="bg-gradient-to-r from-red-600 to-rose-600 text-white p-5 sm:p-6 relative">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-sm border border-white/25 flex items-center justify-center shrink-0 shadow-inner">
              <ShieldAlert className="w-6 h-6 text-white stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5 text-red-200 text-xs font-bold uppercase tracking-wider">
                <Lock className="w-3.5 h-3.5" />
                <span>Mandatory Safety Setup</span>
              </div>
              <h2 className="text-lg sm:text-xl font-black text-white tracking-tight">
                Add SOS Contacts
              </h2>
            </div>
          </div>
          <p className="text-xs text-red-100 mt-2.5 leading-relaxed">
            In an emergency, your live GPS location & safety zone will be instantly sent via SMS/WhatsApp to these contacts.
          </p>
        </div>

        {/* Form area */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1">
              <Users className="w-3.5 h-3.5 text-slate-400" />
              <span>Contacts ({contactList.length} / 5)</span>
            </span>
            <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
              Min 1, Max 5
            </span>
          </div>

          {isAuthError && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex flex-col gap-3">
              <div className="flex items-start gap-2 text-xs text-amber-800 font-medium">
                <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-amber-900">Session Expired</p>
                  <p className="text-amber-700 mt-0.5">Please log in again to save your emergency contacts.</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="w-full py-2.5 px-4 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all"
              >
                <LogIn className="w-4 h-4" />
                <span>Log In Again</span>
              </button>
            </div>
          )}

          {errorMsg && !isAuthError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-2xl flex items-start gap-2 text-xs text-red-700 font-medium">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* List of Contact Cards */}
          <div className="space-y-3">
            {contactList.map((contact, idx) => {
              const phoneVal = validateAndFormatPhone(contact.phone);

              return (
                <div
                  key={contact.id}
                  className={`p-3.5 rounded-2xl border transition-all ${
                    contact.is_primary
                      ? 'border-red-300 bg-red-50/40 shadow-xs'
                      : 'border-slate-200 bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60">
                    <span className="text-xs font-black text-slate-800 flex items-center gap-1.5">
                      <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 text-[10px] font-bold flex items-center justify-center">
                        {idx + 1}
                      </span>
                      <span>Contact #{idx + 1}</span>
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleSetPrimary(contact.id)}
                        className={`text-[11px] font-bold px-2 py-1 rounded-lg flex items-center gap-1 transition-all ${
                          contact.is_primary
                            ? 'bg-red-600 text-white shadow-xs'
                            : 'bg-slate-200/70 text-slate-600 hover:bg-slate-300'
                        }`}
                      >
                        <Star className="w-3 h-3 fill-current" />
                        <span>{contact.is_primary ? 'Primary' : 'Make Primary'}</span>
                      </button>

                      {contactList.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveRow(contact.id)}
                          className="p-1 text-slate-400 hover:text-red-600 transition-colors"
                          title="Remove Contact"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2.5">
                    {/* Name Field */}
                    <div>
                      <label className="block text-[11px] font-bold text-slate-600 mb-1">
                        Full Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Ramesh Kumar"
                        value={contact.name}
                        onChange={(e) => handleFieldChange(contact.id, 'name', e.target.value)}
                        className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
                      />
                    </div>

                    {/* Phone Field */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-[11px] font-bold text-slate-600">
                          Mobile Number <span className="text-red-500">*</span>
                        </label>
                        {hasContactPicker && (
                          <button
                            type="button"
                            onClick={() => handlePickContact(contact.id)}
                            className="text-[10px] font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                          >
                            <Smartphone className="w-3 h-3" />
                            <span>Pick from Contacts</span>
                          </button>
                        )}
                      </div>
                      <div className="relative">
                        <input
                          type="tel"
                          required
                          placeholder="e.g. 9876543210 or +91 98765 43210"
                          value={contact.phone}
                          onChange={(e) => handleFieldChange(contact.id, 'phone', e.target.value)}
                          className={`w-full px-3 py-2 rounded-xl bg-white border text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${
                            contact.phone && phoneVal.isValid
                              ? 'border-emerald-500 focus:ring-emerald-500/20 focus:border-emerald-500'
                              : contact.phone
                              ? 'border-amber-400 focus:ring-amber-500/20 focus:border-amber-400'
                              : 'border-slate-300 focus:ring-red-500/20 focus:border-red-500'
                          }`}
                        />
                        {contact.phone && (
                          <div className="absolute right-2.5 top-2.5">
                            {phoneVal.isValid ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            ) : (
                              <AlertCircle className="w-4 h-4 text-amber-500" />
                            )}
                          </div>
                        )}
                      </div>
                      {contact.phone && phoneVal.isValid && (
                        <p className="text-[10px] text-emerald-700 font-mono mt-0.5">
                          Standard E.164: {phoneVal.formatted}
                        </p>
                      )}
                    </div>

                    {/* Relationship Dropdown */}
                    <div>
                      <label className="block text-[11px] font-bold text-slate-600 mb-1">
                        Relationship
                      </label>
                      <select
                        value={contact.relationship}
                        onChange={(e) =>
                          handleFieldChange(contact.id, 'relationship', e.target.value)
                        }
                        className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
                      >
                        {RELATIONSHIP_OPTIONS.map((rel) => (
                          <option key={rel} value={rel}>
                            {rel}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Add Another Contact Button */}
          {contactList.length < 5 && (
            <button
              type="button"
              onClick={handleAddRow}
              className="w-full py-2.5 px-3 border-2 border-dashed border-slate-300 hover:border-slate-400 text-slate-700 rounded-2xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all bg-slate-50 hover:bg-slate-100 min-h-[44px]"
            >
              <UserPlus className="w-4 h-4 text-slate-500" />
              <span>Add Another Contact ({contactList.length}/5)</span>
            </button>
          )}

          {/* Save & Confirm Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-red-600 to-red-500 text-white font-bold text-sm shadow-[0_4px_15px_rgba(239,68,68,0.4)] hover:shadow-[0_6px_20px_rgba(239,68,68,0.5)] active:scale-98 transition-all disabled:opacity-50 min-h-[48px] flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Configuring SOS Contacts...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 stroke-[2.5]" />
                  <span>Save Emergency Contacts & Enter App</span>
                </>
              )}
            </button>
            <p className="text-[10px] text-center text-slate-400 mt-2">
              You can edit or update these contacts anytime in Settings.
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
