const CACHE_NAME = 'hyakumeiten-map-v32';
const APP_SHELL = [
  './',
  './index.html',
  './style.css?v=7.2',
  './search.js?v=1',
  './app.js?v=7.2',
  './manifest.webmanifest',
  './icon.svg',
  './icon.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './privacy.html',
  './data/data-version.json',
  './data/udon.json',
  './data/soba.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  const accept = request.headers.get('accept') || '';
  const isNavigation = request.mode === 'navigate' || accept.includes('text/html');
  if (isNavigation) {
    event.respondWith(
      fetch(request).then(response => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        }
        return response;
      }).catch(() => caches.match(request).then(cached => cached || caches.match('./index.html')))
    );
    return;
  }

  if (url.pathname.endsWith('/data/recommendation_tags.json')) {
    const cachePromise = caches.open(CACHE_NAME);
    const networkUpdate = cachePromise.then(cache =>
      fetch(request).then(response => {
        if (response && response.ok) cache.put(request, response.clone());
        return response;
      })
    );
    event.waitUntil(networkUpdate.catch(() => {}));
    event.respondWith(
      cachePromise.then(cache =>
        cache.match(request).then(cached => cached || networkUpdate)
      )
    );
    return;
  }

  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        }
        return response;
      });
    })
  );
});
