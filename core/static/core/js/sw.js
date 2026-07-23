/**
 * sw.js - minimal service worker for "Add to Home Screen" (v2.4).
 *
 * Caches the app shell (CSS + cart JS) so repeat visits load instantly
 * even on slow 2G/3G connections, and the menu still renders offline
 * (product images not in the pre-cache list will still try the network).
 *
 * Bump CACHE_NAME whenever style.css/cart.js change so old caches are
 * discarded instead of serving stale assets forever.
 */
const CACHE_NAME = "samwa-shell-v1";
const APP_SHELL = [
  "/",
  "/static/core/css/style.css",
  "/static/core/js/cart.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
