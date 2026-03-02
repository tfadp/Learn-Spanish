// LyricFlow Service Worker
// Caches static assets (CSS, JS, fonts) for fast repeat loads.
// API calls and audio files are always fetched live.

const CACHE_NAME = 'lyricflow-v1';

// Assets to pre-cache on install
const PRECACHE_URLS = [
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/icons/icon-512.svg',
];

// Install: pre-cache core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// Activate: clean up old caches
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

// Fetch: stale-while-revalidate for static assets, network-only for API/audio
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // API calls — always go to network
  if (url.pathname.startsWith('/api/')) return;

  // Audio files — always go to network (too large to cache)
  if (url.pathname.endsWith('.mp3')) return;

  // Everything else: stale-while-revalidate
  event.respondWith(
    caches.open(CACHE_NAME).then((cache) =>
      cache.match(event.request).then((cached) => {
        const fetched = fetch(event.request).then((response) => {
          // Only cache successful responses
          if (response.ok) {
            cache.put(event.request, response.clone());
          }
          return response;
        }).catch(() => cached); // If network fails, fall back to cache

        // Return cached version immediately, or wait for network
        return cached || fetched;
      })
    )
  );
});
