import { authService } from './authService';
import { API_BASE, apiFetch } from './apiConfig';

/**
 * Validate and format an Indian or international phone number into E.164 standard.
 * Returns { isValid, formatted, error }
 */
export function validateAndFormatPhone(phoneStr) {
  if (!phoneStr || typeof phoneStr !== 'string') {
    return { isValid: false, formatted: '', error: 'Phone number is required.' };
  }

  const cleaned = phoneStr.replace(/[\s\-\(\)\.]+/g, '').trim();

  // Case 1: International with +
  if (cleaned.startsWith('+')) {
    const digits = cleaned.slice(1);
    if (!/^\d{8,15}$/.test(digits)) {
      return { isValid: false, formatted: '', error: 'Must contain 8-15 digits after +' };
    }
    return { isValid: true, formatted: cleaned, error: null };
  }

  // Case 2: Starts with 00 (international format)
  if (cleaned.startsWith('00')) {
    const digits = cleaned.slice(2);
    if (!/^\d{8,15}$/.test(digits)) {
      return { isValid: false, formatted: '', error: 'Invalid international number' };
    }
    return { isValid: true, formatted: `+${digits}`, error: null };
  }

  // Case 3: 11 digits starting with 0 (Indian trunk)
  if (cleaned.startsWith('0') && cleaned.length === 11 && /^\d+$/.test(cleaned)) {
    return { isValid: true, formatted: `+91${cleaned.slice(1)}`, error: null };
  }

  // Case 4: 10 digit Indian number
  if (cleaned.length === 10 && /^[6-9]\d{9}$/.test(cleaned)) {
    return { isValid: true, formatted: `+91${cleaned}`, error: null };
  }

  // Case 5: 12 digit with 91 country code without +
  if (cleaned.length === 12 && cleaned.startsWith('91') && /^\d+$/.test(cleaned)) {
    return { isValid: true, formatted: `+${cleaned}`, error: null };
  }

  // Generic 10 digit fallback
  if (cleaned.length === 10 && /^\d{10}$/.test(cleaned)) {
    return { isValid: true, formatted: `+91${cleaned}`, error: null };
  }

  return {
    isValid: false,
    formatted: '',
    error: 'Enter a valid 10-digit mobile number or international +country format',
  };
}

/**
 * Web Contact Picker API helper.
 * Allows picking contacts directly from mobile/tablet phonebook where supported.
 */
export async function pickContactFromDevice() {
  if (!('contacts' in navigator && 'ContactsManager' in window)) {
    throw new Error('Contact Picker API is not supported on this device/browser.');
  }

  try {
    const props = ['name', 'tel'];
    const opts = { multiple: false };
    const contacts = await navigator.contacts.select(props, opts);

    if (!contacts || contacts.length === 0) {
      return null;
    }

    const picked = contacts[0];
    const name = picked.name?.[0] || '';
    const phone = picked.tel?.[0] || '';

    return { name, phone };
  } catch (err) {
    if (err.name === 'AbortError') return null;
    throw err;
  }
}

/**
 * Play a synthesizer warning beep using Web Audio API for SOS countdown.
 */
export function playAlertBeep(frequency = 880, duration = 0.15) {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(frequency, ctx.currentTime);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch {
    // Audio context may be restricted before user gesture
  }
}

export const sosService = {
  /**
   * Check whether user has completed mandatory SOS onboarding.
   */
  async getOnboardingStatus() {
    return apiFetch('/user/onboarding-status', { method: 'GET' }, 'Load onboarding status');
  },

  /**
   * Fetch all emergency contacts for current user.
   */
  async getContacts() {
    const data = await apiFetch('/user/sos-contacts', { method: 'GET' }, 'Fetch SOS contacts');
    return data.contacts || [];
  },

  /**
   * Add a single SOS contact.
   */
  async addContact({ name, phone, relationship, is_primary = false }) {
    return apiFetch(
      '/user/sos-contacts',
      {
        method: 'POST',
        body: JSON.stringify({ name, phone, relationship, is_primary }),
      },
      'Add SOS contact'
    );
  },

  /**
   * Bulk save contacts during mandatory onboarding (1-5 contacts).
   */
  async bulkSaveContacts(contacts) {
    return apiFetch(
      '/user/sos-contacts/bulk',
      {
        method: 'POST',
        body: JSON.stringify({ contacts }),
      },
      'Save SOS contacts'
    );
  },

  /**
   * Update an existing contact.
   */
  async updateContact(id, contactData) {
    return apiFetch(
      `/user/sos-contacts/${id}`,
      {
        method: 'PUT',
        body: JSON.stringify(contactData),
      },
      'Update SOS contact'
    );
  },

  /**
   * Delete an SOS contact.
   */
  async deleteContact(id) {
    return apiFetch(
      `/user/sos-contacts/${id}`,
      { method: 'DELETE' },
      'Delete SOS contact'
    );
  },

  /**
   * Send test verification notification to a specific contact.
   */
  async sendTestMessage(id) {
    return apiFetch(
      `/user/sos-contacts/${id}/test`,
      { method: 'POST' },
      'Send test message'
    );
  },

  /**
   * Trigger emergency SOS distress event.
   */
  async triggerSOS({ latitude, longitude, accuracy, zone, type = 'manual' }) {
    return apiFetch(
      '/user/sos-events/trigger',
      {
        method: 'POST',
        body: JSON.stringify({ latitude, longitude, accuracy, zone, type }),
      },
      'Trigger SOS alert'
    );
  },

  /**
   * Check for currently active SOS event for logged-in user.
   */
  async getActiveSOSEvent() {
    return apiFetch(
      '/user/sos-events/active',
      { method: 'GET' },
      'Check active SOS status'
    );
  },

  /**
   * Resolve active SOS event ("I'm Safe").
   */
  async resolveSOSEvent(eventId) {
    return apiFetch(
      `/user/sos-events/${eventId}/resolve`,
      { method: 'POST' },
      'Resolve SOS event'
    );
  },

  /**
   * Send live GPS coordinates update for active SOS event.
   */
  async updateLiveSOSLocation(eventId, { latitude, longitude, accuracy, zone }) {
    return apiFetch(
      `/user/sos-events/${eventId}/live-location`,
      {
        method: 'POST',
        body: JSON.stringify({ latitude, longitude, accuracy, zone }),
      },
      'Update live coordinates'
    );
  },

  /**
   * Extend 1-hour live location sharing.
   */
  async extendLiveTracking(eventId) {
    return apiFetch(
      `/user/sos-events/${eventId}/extend-tracking`,
      { method: 'POST' },
      'Extend live tracking'
    );
  },

  /**
   * Admin: Fetch SOS events for real-time monitoring.
   */
  async getAdminSOSEvents(status = 'all', limit = 50) {
    return apiFetch(
      `/admin/sos-events?status=${status}&limit=${limit}`,
      { method: 'GET' },
      'Fetch admin SOS events'
    );
  },

  /**
   * Send 30s client heartbeat with interaction flag and coordinates.
   */
  async sendHeartbeat({ latitude, longitude, accuracy, zone, has_interaction = false }) {
    return apiFetch(
      '/user/heartbeat',
      {
        method: 'POST',
        body: JSON.stringify({
          latitude,
          longitude,
          accuracy,
          zone,
          has_interaction,
          timestamp: new Date().toISOString(),
        }),
      },
      'Heartbeat sync'
    );
  },

  /**
   * Check current user's Red Zone safety state & warning countdown.
   */
  async getSafetyStatus() {
    return apiFetch(
      '/user/safety-status',
      { method: 'GET' },
      'Fetch safety status'
    );
  },

  /**
   * Respond "I'm Safe" to the inactivity warning prompt.
   */
  async safetyCheckin() {
    return apiFetch(
      '/user/safety-checkin',
      { method: 'POST' },
      'Safety check-in'
    );
  },

  /**
   * Save Web Push (VAPID) notification subscription.
   */
  async savePushSubscription(subscription) {
    return apiFetch(
      '/user/push-subscription',
      {
        method: 'POST',
        body: JSON.stringify({ subscription }),
      },
      'Save push subscription'
    );
  },

  /**
   * Dev Mode: Simulate Red Zone states, 1-minute threshold, and auto SOS timeout.
   */
  async simulateRedZone(action = 'enter_red', thresholdMinutes = 1) {
    return apiFetch(
      '/dev/simulate-red-zone',
      {
        method: 'POST',
        body: JSON.stringify({ action, threshold_minutes: thresholdMinutes }),
      },
      'Simulation command'
    );
  },
};

export { API_BASE };
