const CACHE = 'video-enhancer-v1';
const STATIC = [
  '/static/style.css',
  '/static/icons.svg',
  '/static/logo.svg',
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/static/manifest.json',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  // Cache-first for static assets, network-first for everything else
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.match(e.request).then(cached => cached || fetch(e.request))
    );
  }
});
