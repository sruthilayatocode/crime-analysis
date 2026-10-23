import { authService } from './authService';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

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
    const res = await fetch(`${API_BASE}/user/onboarding-status`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error('Failed to load onboarding status');
    }
    return res.json();
  },

  /**
   * Fetch all emergency contacts for current user.
   */
  async getContacts() {
    const res = await fetch(`${API_BASE}/user/sos-contacts`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to fetch SOS contacts');
    }
    return data.contacts || [];
  },

  /**
   * Add a single SOS contact.
   */
  async addContact({ name, phone, relationship, is_primary = false }) {
    const res = await fetch(`${API_BASE}/user/sos-contacts`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ name, phone, relationship, is_primary }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to add contact');
    }
    return data;
  },

  /**
   * Bulk save contacts during mandatory onboarding (1-5 contacts).
   */
  async bulkSaveContacts(contacts) {
    const res = await fetch(`${API_BASE}/user/sos-contacts/bulk`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ contacts }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to save contacts');
    }
    return data;
  },

  /**
   * Update an existing contact.
   */
  async updateContact(id, contactData) {
    const res = await fetch(`${API_BASE}/user/sos-contacts/${id}`, {
      method: 'PUT',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify(contactData),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to update contact');
    }
    return data;
  },

  /**
   * Delete an SOS contact.
   */
  async deleteContact(id) {
    const res = await fetch(`${API_BASE}/user/sos-contacts/${id}`, {
      method: 'DELETE',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to delete contact');
    }
    return data;
  },

  /**
   * Send test verification notification to a specific contact.
   */
  async sendTestMessage(id) {
    const res = await fetch(`${API_BASE}/user/sos-contacts/${id}/test`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to send test message');
    }
    return data;
  },

  /**
   * Trigger emergency SOS distress event.
   */
  async triggerSOS({ latitude, longitude, accuracy, zone, type = 'manual' }) {
    const res = await fetch(`${API_BASE}/user/sos-events/trigger`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ latitude, longitude, accuracy, zone, type }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to trigger SOS alert');
    }
    return data;
  },

  /**
   * Check for currently active SOS event for logged-in user.
   */
  async getActiveSOSEvent() {
    const res = await fetch(`${API_BASE}/user/sos-events/active`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to check active SOS status');
    }
    return data;
  },

  /**
   * Resolve active SOS event ("I'm Safe").
   */
  async resolveSOSEvent(eventId) {
    const res = await fetch(`${API_BASE}/user/sos-events/${eventId}/resolve`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to resolve SOS event');
    }
    return data;
  },

  /**
   * Send live GPS coordinates update for active SOS event.
   */
  async updateLiveSOSLocation(eventId, { latitude, longitude, accuracy, zone }) {
    const res = await fetch(`${API_BASE}/user/sos-events/${eventId}/live-location`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ latitude, longitude, accuracy, zone }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to update live coordinates');
    }
    return data;
  },

  /**
   * Extend 1-hour live location sharing.
   */
  async extendLiveTracking(eventId) {
    const res = await fetch(`${API_BASE}/user/sos-events/${eventId}/extend-tracking`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to extend live tracking');
    }
    return data;
  },

  /**
   * Admin: Fetch SOS events for real-time monitoring.
   */
  async getAdminSOSEvents(status = 'all', limit = 50) {
    const res = await fetch(`${API_BASE}/admin/sos-events?status=${status}&limit=${limit}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to fetch admin SOS events');
    }
    return data;
  },

  /**
   * Send 30s client heartbeat with interaction flag and coordinates.
   */
  async sendHeartbeat({ latitude, longitude, accuracy, zone, has_interaction = false }) {
    const res = await fetch(`${API_BASE}/user/heartbeat`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({
        latitude,
        longitude,
        accuracy,
        zone,
        has_interaction,
        timestamp: new Date().toISOString(),
      }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Heartbeat sync failed');
    }
    return data;
  },

  /**
   * Check current user's Red Zone safety state & warning countdown.
   */
  async getSafetyStatus() {
    const res = await fetch(`${API_BASE}/user/safety-status`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to fetch safety status');
    }
    return data;
  },

  /**
   * Respond "I'm Safe" to the inactivity warning prompt.
   */
  async safetyCheckin() {
    const res = await fetch(`${API_BASE}/user/safety-checkin`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Safety check-in failed');
    }
    return data;
  },

  /**
   * Save Web Push (VAPID) notification subscription.
   */
  async savePushSubscription(subscription) {
    const res = await fetch(`${API_BASE}/user/push-subscription`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ subscription }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to save push subscription');
    }
    return data;
  },

  /**
   * Dev Mode: Simulate Red Zone states, 1-minute threshold, and auto SOS timeout.
   */
  async simulateRedZone(action = 'enter_red', thresholdMinutes = 1) {
    const res = await fetch(`${API_dev_base()}/simulate-red-zone`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ action, threshold_minutes: thresholdMinutes }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Simulation command failed');
    }
    return data;
  },
};

function API_dev_base() {
  return `${API_BASE}/dev`;
}

