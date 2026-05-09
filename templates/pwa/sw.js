{% load static %}
const CACHE = 'liveboutique-v3';
const PRECACHE = [
  '/',
  '/offline/',
  '{% static "css/styles.css" %}',
  '{% static "js/app.js" %}',
  '{% static "js/pwa.js" %}',
  '{% static "icons/icon.svg" %}',
  '{% static "icons/icon-192.png" %}',
  '{% static "icons/icon-512.png" %}',
  '{% static "icons/apple-touch-icon.png" %}',
  {% for image in featured_image_urls %}'{{ image|escapejs }}',
  {% endfor %}
];

const QUEUE_DB = 'liveboutique-queue';
const QUEUE_STORE = 'pending-cart-adds';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.all(PRECACHE.map((url) =>
        c.add(url).catch((err) => console.warn('[sw] precache miss', url, err))
      )))
  );
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

  // Background-sync friendly path: cart adds get queued if offline.
  if (req.method === 'POST' && /\/cart\/add\//.test(req.url)) {
    event.respondWith(handleCartAdd(req));
    return;
  }
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

// --- Background Sync: queue cart-add POSTs while offline -------------

async function handleCartAdd(req) {
  try {
    return await fetch(req.clone());
  } catch (err) {
    // Offline: clone the body, store it, register a sync.
    const cloned = req.clone();
    const blob = await cloned.blob();
    const headers = {};
    cloned.headers.forEach((v, k) => { headers[k] = v; });
    await enqueueRequest({
      url: cloned.url,
      method: cloned.method,
      headers,
      body: await blobToBase64(blob),
      ts: Date.now(),
    });
    if ('sync' in self.registration) {
      try { await self.registration.sync.register('sync-cart-adds'); } catch (e) {}
    }
    // Fake an "accepted" response so the caller's redirect chain doesn't break.
    return new Response(JSON.stringify({queued: true}), {
      status: 202,
      headers: {'Content-Type': 'application/json'}
    });
  }
}

self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-cart-adds') {
    event.waitUntil(flushQueue());
  }
});

async function flushQueue() {
  const items = await readQueue();
  for (const item of items) {
    try {
      await fetch(item.url, {
        method: item.method,
        headers: item.headers,
        body: base64ToBlob(item.body),
        credentials: 'include',
      });
      await deleteFromQueue(item.id);
    } catch (e) {
      // Leave it in the queue — sync will retry.
      console.warn('[sw] sync retry will continue', e);
    }
  }
}

// --- IndexedDB queue helpers (no external deps) ----------------------

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(QUEUE_DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(QUEUE_STORE, {keyPath: 'id', autoIncrement: true});
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
async function enqueueRequest(item) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(QUEUE_STORE, 'readwrite');
    tx.objectStore(QUEUE_STORE).add(item);
    tx.oncomplete = () => res();
    tx.onerror = () => rej(tx.error);
  });
}
async function readQueue() {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(QUEUE_STORE, 'readonly');
    const req = tx.objectStore(QUEUE_STORE).getAll();
    req.onsuccess = () => res(req.result || []);
    req.onerror = () => rej(req.error);
  });
}
async function deleteFromQueue(id) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(QUEUE_STORE, 'readwrite');
    tx.objectStore(QUEUE_STORE).delete(id);
    tx.oncomplete = () => res();
    tx.onerror = () => rej(tx.error);
  });
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onloadend = () => resolve(r.result);
    r.onerror = () => reject(r.error);
    r.readAsDataURL(blob);
  });
}
function base64ToBlob(dataUrl) {
  const [meta, b64] = String(dataUrl).split(',');
  const mime = (meta.match(/:(.*);base64/) || [])[1] || 'application/x-www-form-urlencoded';
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return new Blob([arr], {type: mime});
}
