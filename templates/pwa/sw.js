{% load static %}
const CACHE = 'maison-aleta-v1';
const PRECACHE = [
  '/',
  '/offline/',
  '{% static "css/styles.css" %}',
  '{% static "js/app.js" %}',
  '{% static "js/pwa.js" %}',
  '{% static "icons/icon.svg" %}',
  '{% static "icons/icon-192.png" %}',
  '{% static "icons/icon-512.png" %}',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).catch(() => null));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

// Network-first for HTML, cache-first for static assets, offline fallback to /offline/.
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const accept = req.headers.get('accept') || '';
  if (accept.includes('text/html')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match('/offline/')))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      return (
        cached ||
        fetch(req).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => null);
          return res;
        }).catch(() => cached)
      );
    })
  );
});
