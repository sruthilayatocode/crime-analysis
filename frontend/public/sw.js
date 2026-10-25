/**
 * Service Worker for CrimeSense PWA
 * Caches application shell for offline capability.
 */

const CACHE_NAME = 'crimesense-shell-v1';
const PRECACHE_ASSETS = [
  '/',
  '/app',
  '/app/saved',
  '/app/sos',
  '/app/settings',
  '/manifest.json',
  '/favicon.svg',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// Install: pre-cache application shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
      .catch((err) => {
        console.warn('[SW] Pre-caching error:', err);
      })
  );
});

// Activate: clean up older caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames.map((name) => {
            if (name !== CACHE_NAME) {
              return caches.delete(name);
            }
          })
        )
      )
      .then(() => self.clients.claim())
  );
});

// Fetch: Network First for API, Stale-While-Revalidate for static assets / shell
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Ignore non-GET requests and external chrome-extensions
  if (event.request.method !== 'GET' || !url.protocol.startsWith('http')) {
    return;
  }

  // API calls: Network first with graceful offline response
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(async () => {
        const cached = await caches.match(event.request);
        if (cached) return cached;
        return new Response(
          JSON.stringify({
            offline: true,
            error: 'You are currently offline. Showing cached or local data.',
          }),
          {
            headers: { 'Content-Type': 'application/json' },
            status: 503,
          }
        );
      })
    );
    return;
  }

  // Shell & Navigation requests: Network first with cache fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(async () => {
        const cached = await caches.match(event.request);
        if (cached) return cached;
        return caches.match('/app') || caches.match('/');
      })
    );
    return;
  }

  // Static assets: Cache first / Stale-while-revalidate
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // Fetch background update
        fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, networkResponse.clone());
              });
            }
          })
          .catch(() => {});
        return cachedResponse;
      }

      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }
        const toCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, toCache);
        });
        return networkResponse;
      });
    })
  );
});
