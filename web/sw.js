const CACHE = 'centinel-v1';
const STATIC = ['/monitor/', '/monitor/index.html'];

self.addEventListener('install', e =>
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC)).then(() => self.skipWaiting())
  )
);

self.addEventListener('activate', e =>
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
);

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  if (url.pathname.endsWith('snapshot.json')) {
    // Network-first: always try to get fresh data.
    // On failure (CDN down, offline) serve last cached copy.
    e.respondWith(
      fetch(e.request)
        .then(r => {
          const clone = r.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
          return r;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Cache-first for everything else (panel assets)
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
