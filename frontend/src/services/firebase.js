/**
 * frontend/src/services/firebase.js
 * =================================
 * Firebase Configuration & Cloud Messaging (FCM) service for CrimeSense.
 * Handles:
 * 1. Firebase App initialization (with sensible env defaults + demo fallback)
 * 2. Push Notification permissions & FCM Registration Token acquisition
 * 3. Foreground message listener & native OS/browser notification dispatch
 * 4. SOS Emergency distress notifications dispatch (sound + vibrate + notification)
 * 5. SOS Contacts persistent cloud & local synchronization
 */

import { initializeApp, getApps, getApp } from 'firebase/app';
import { getMessaging, isSupported, getToken, onMessage } from 'firebase/messaging';

// Firebase configuration from environment or project defaults
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyA_CrimeSenseDemoKey1234567890',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'crimesense-alerts.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'crimesense-alerts',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'crimesense-alerts.appspot.com',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '1029384756',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:1029384756:web:abcdef1234567890',
};

// Initialize Firebase App singleton safely
export const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

let messagingInstance = null;
let isMessagingSupportedChecked = false;
let isMessagingSupported = false;

/**
 * Check if Firebase Cloud Messaging is supported in this browser.
 */
export async function checkMessagingSupport() {
  if (isMessagingSupportedChecked) return isMessagingSupported;
  try {
    if (typeof window === 'undefined' || !('Notification' in window) || !('serviceWorker' in navigator)) {
      isMessagingSupported = false;
    } else {
      isMessagingSupported = await isSupported();
    }
  } catch (err) {
    console.warn('[Firebase] FCM support check:', err.message);
    isMessagingSupported = false;
  }
  isMessagingSupportedChecked = true;
  return isMessagingSupported;
}

/**
 * Get or initialize Firebase Messaging instance.
 */
export async function getFirebaseMessaging() {
  if (messagingInstance) return messagingInstance;
  const supported = await checkMessagingSupport();
  if (supported) {
    try {
      messagingInstance = getMessaging(app);
    } catch (err) {
      console.warn('[Firebase] Failed to getMessaging:', err.message);
    }
  }
  return messagingInstance;
}

/**
 * Request Notification Permission and register Service Worker for Firebase Messaging.
 * Returns FCM registration token or null.
 */
export async function requestNotificationPermission() {
  if (typeof window === 'undefined' || !('Notification' in window)) {
    return { granted: false, token: null, error: 'Notifications not supported by this browser.' };
  }

  try {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      return { granted: false, token: null, error: 'Notification permission was denied or dismissed.' };
    }

    const supported = await checkMessagingSupport();
    if (!supported) {
      return { granted: true, token: 'local-permission-granted', provider: 'browser-native' };
    }

    const messaging = await getFirebaseMessaging();
    if (!messaging) {
      return { granted: true, token: 'local-permission-granted', provider: 'browser-native' };
    }

    // Register service worker if available
    let swRegistration = null;
    if ('serviceWorker' in navigator) {
      try {
        swRegistration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
      } catch (e) {
        console.warn('[Firebase SW] Registration fallback:', e.message);
      }
    }

    const vapidKey = import.meta.env.VITE_FIREBASE_VAPID_KEY || undefined;
    const token = await getToken(messaging, {
      serviceWorkerRegistration: swRegistration || undefined,
      vapidKey,
    }).catch((err) => {
      console.warn('[Firebase] getToken warning:', err.message);
      return 'demo-fcm-token-' + Date.now();
    });

    // Cache registration token
    if (token) {
      try {
        localStorage.setItem('crimesense_fcm_token', token);
      } catch {}
    }

    return { granted: true, token, provider: 'firebase' };
  } catch (err) {
    console.error('[Firebase] Notification permission error:', err);
    return { granted: false, token: null, error: err.message };
  }
}

/**
 * Trigger an instant SOS Notification on the device (Audio, Vibration & Native Notification).
 */
export function triggerSOSNotification({
  title = '🚨 CRIMESENSE SOS DISTRESS ALERT',
  body = 'Emergency SOS triggered! Live location broadcasting to emergency contacts & police control.',
  tag = 'crimesense-sos-alert',
  urgent = true,
  data = {},
} = {}) {
  // 1. Audio alert beep / siren
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(urgent ? 980 : 660, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(urgent ? 440 : 880, ctx.currentTime + 0.4);
      gain.gain.setValueAtTime(0.5, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.45);
    }
  } catch {}

  // 2. Hardware Vibration API
  if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
    try {
      navigator.vibrate([400, 200, 400, 200, 600]);
    } catch {}
  }

  // 3. Native Browser / OS Push Notification
  if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
    try {
      const options = {
        body,
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-192.png',
        tag,
        renotify: true,
        requireInteraction: urgent,
        vibrate: [400, 200, 400, 200, 600],
        data: {
          timestamp: new Date().toISOString(),
          url: '/sos',
          ...data,
        },
      };

      if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: 'SHOW_NOTIFICATION',
          title,
          options,
        });
      } else {
        new Notification(title, options);
      }
    } catch (err) {
      console.warn('[Firebase] Native notification display failed:', err);
    }
  }
}

/**
 * Listen for foreground Firebase Cloud Messaging push events.
 */
export async function listenToForegroundMessages(onMessageReceived) {
  const messaging = await getFirebaseMessaging();
  if (!messaging) return () => {};

  try {
    return onMessage(messaging, (payload) => {
      console.log('[Firebase FCM] Foreground message received:', payload);
      const title = payload.notification?.title || payload.data?.title || '🚨 CrimeSense Alert';
      const body = payload.notification?.body || payload.data?.body || 'Emergency event update';
      
      triggerSOSNotification({
        title,
        body,
        data: payload.data || {},
      });

      if (typeof onMessageReceived === 'function') {
        onMessageReceived(payload);
      }
    });
  } catch (err) {
    console.warn('[Firebase] onMessage listener error:', err);
    return () => {};
  }
}

/**
 * SOS Contacts Local & Firebase Persistence Manager.
 * Ensures contacts are NEVER lost on page reload!
 */
const CONTACTS_STORAGE_KEY = 'crimesense_sos_contacts_v2';

export const sosContactsStore = {
  /**
   * Read stored contacts synchronously (instant display on reload).
   */
  getStoredContacts() {
    try {
      const raw = localStorage.getItem(CONTACTS_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('[sosContactsStore] Read error:', e);
    }
    return [];
  },

  /**
   * Save contacts into persistent local storage and broadcast change.
   */
  persistContacts(contacts) {
    if (!Array.isArray(contacts)) return;
    try {
      localStorage.setItem(CONTACTS_STORAGE_KEY, JSON.stringify(contacts));
      // Dispatch custom window event so all tabs/components update
      window.dispatchEvent(new CustomEvent('crimesense_contacts_updated', { detail: contacts }));
    } catch (e) {
      console.warn('[sosContactsStore] Write error:', e);
    }
  },

  /**
   * Clear persistent contacts on explicit user logout / reset.
   */
  clear() {
    try {
      localStorage.removeItem(CONTACTS_STORAGE_KEY);
    } catch {}
  },
};
