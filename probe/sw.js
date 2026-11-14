/* Guya storage/offline PROBE service worker (P0). Diagnostic only - not part of the app.
   Lives at probe/sw.js, so the widest scope a browser will grant it is .../probe/ (the script's own
   directory; GitHub Pages sends no Service-Worker-Allowed header). It can never control index.html or
   storage_check.html. As a second guard it answers ONLY two URLs inside that scope and ignores the rest.
   Storage used: Cache "guya-probe-v1" only. */
var PROBE_CACHE = 'guya-probe-v1';
var PROBE_VERSION = 'p0-2026.11.15a';
var SCOPE_PATH = new URL('./', self.location.href).pathname;      /* .../probe/ */
var PAGE_PATH = SCOPE_PATH + 'page.html';
var PING_PATH = SCOPE_PATH + '__ping';
var lastNav = { source: 'none', at: null };

self.addEventListener('install', function (e) {
  /* cache the probe page so it can be served with the network off */
  e.waitUntil(caches.open(PROBE_CACHE).then(function (c) { return c.add(new Request('page.html', { cache: 'reload' })); }));
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  /* deliberately NO clients.claim(): the probe reports whether the page is controlled on the SECOND load */
  e.waitUntil(Promise.resolve());
});

function timeout(ms) { return new Promise(function (_, rej) { setTimeout(function () { rej(new Error('timeout')); }, ms); }); }

self.addEventListener('fetch', function (e) {
  var url = new URL(e.request.url);
  if (url.origin !== self.location.origin) return;                  /* never touch other origins */
  if (url.pathname.indexOf(SCOPE_PATH) !== 0) return;               /* never touch anything outside .../probe/ */
  if (url.pathname === PING_PATH) {
    e.respondWith(caches.open(PROBE_CACHE).then(function (c) { return c.match('page.html'); }).then(function (hit) {
      return new Response(JSON.stringify({ sw: true, version: PROBE_VERSION, scope: self.registration.scope, pageCached: !!hit, lastNav: lastNav }),
        { headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
    }));
    return;
  }
  if (url.pathname === PAGE_PATH && e.request.method === 'GET') {
    /* network first (4 s), then the cached copy */
    e.respondWith(Promise.race([fetch(e.request), timeout(4000)]).then(function (r) {
      if (!r || !r.ok) throw new Error('bad response');
      lastNav = { source: 'network', at: Date.now() };
      var copy = r.clone();
      caches.open(PROBE_CACHE).then(function (c) { return c.put('page.html', copy); });
      return r;
    }).catch(function () {
      return caches.open(PROBE_CACHE).then(function (c) { return c.match('page.html'); }).then(function (hit) {
        if (hit) { lastNav = { source: 'cache', at: Date.now() }; return hit; }
        lastNav = { source: 'failed', at: Date.now() };
        return new Response('Guya probe: offline and no cached copy.', { status: 503, headers: { 'Content-Type': 'text/plain' } });
      });
    }));
    return;
  }
  /* everything else inside the scope: not handled - the browser fetches it normally */
});
