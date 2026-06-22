const CACHE = 'vigil-v2';

self.addEventListener('install', e =>
  e.waitUntil(self.skipWaiting())
);

self.addEventListener('activate', e =>
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
);

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  if (url.pathname.endsWith('snapshot.json')) {
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

  // Network-first for HTML pages; cache-first for static assets
  if (e.request.mode === 'navigate' || url.pathname.endsWith('.html')) {
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

  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
