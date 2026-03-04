// LyricFlow Service Worker
// Network-first for everything: always fetch fresh from server,
// fall back to cache only when offline.

const CACHE_NAME = 'lyricflow-v14';

// Install: skip waiting so new SW activates immediately
self.addEventListener('install', () => self.skipWaiting());

// Activate: delete ALL old caches, then claim clients
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch: network-first for static assets and pages.
// API calls and audio are not intercepted at all.
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  if (event.request.method !== 'GET') return;
  if (url.pathname.startsWith('/api/')) return;
  if (url.pathname.endsWith('.mp3')) return;

  // Network-first: try server, cache the response, fall back to cache
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
