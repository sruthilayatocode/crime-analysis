/**
 * frontend/public/firebase-messaging-sw.js
 * ========================================
 * Firebase Cloud Messaging Service Worker for background SOS alerts.
 */

// Give the service worker access to Firebase Messaging.
importScripts('https://www.gstatic.com/firebasejs/10.9.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.9.0/firebase-messaging-compat.js');

// Initialize the Firebase app in the service worker by passing in the messagingSenderId.
firebase.initializeApp({
  apiKey: 'AIzaSyA_CrimeSenseDemoKey1234567890',
  authDomain: 'crimesense-alerts.firebaseapp.com',
  projectId: 'crimesense-alerts',
  storageBucket: 'crimesense-alerts.appspot.com',
  messagingSenderId: '1029384756',
  appId: '1:1029384756:web:abcdef1234567890',
});

const messaging = firebase.messaging();

// Background message handler
messaging.onBackgroundMessage(function (payload) {
  console.log('[firebase-messaging-sw.js] Received background message: ', payload);
  const title = payload.notification?.title || payload.data?.title || '🚨 CRIMESENSE SOS DISTRESS ALERT';
  const notificationOptions = {
    body: payload.notification?.body || payload.data?.body || 'Emergency SOS distress triggered. Tap to open live tracking.',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    tag: 'crimesense-sos-alert',
    renotify: true,
    requireInteraction: true,
    vibrate: [500, 250, 500, 250, 500],
    data: {
      url: '/sos',
      ...payload.data,
    },
  };

  self.registration.showNotification(title, notificationOptions);
});

// Handle notification click to focus or open CrimeSense window
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url.includes('/sos') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/sos');
      }
    })
  );
});

// Message listener from foreground window
self.addEventListener('message', function (event) {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    self.registration.showNotification(event.data.title, event.data.options);
  }
});
