// Runtime adapter that detects the reverse-proxy mount prefix and patches
// global axios + window.fetch so generated SPAs don't need build-time
// knowledge of their URL. Must be imported BEFORE any module that itself
// calls `axios.create(...)` at top level.

import axios from 'axios';

function detectBase() {
  if (typeof window === 'undefined') return '';
  const baseEl = document.querySelector('base[href]');
  if (baseEl) {
    try {
      const u = new URL(baseEl.getAttribute('href'), window.location.origin);
      const path = u.pathname.replace(/\/$/, '');
      if (path) return path;
    } catch (e) { /* fall through */ }
  }
  const m = window.location.pathname.match(/^\/app\/[^/]+/);
  return m ? m[0] : '';
}

export const APP_BASE = detectBase();

if (axios) {
  axios.defaults = axios.defaults || {};
  axios.defaults.baseURL = APP_BASE;
}

// Patch axios.create so per-instance baseURLs inherit APP_BASE.
if (APP_BASE && axios && axios.create && !axios.__APP_BASE_PATCHED__) {
  const origCreate = axios.create.bind(axios);
  axios.create = (config = {}) => {
    const cfg = { ...(config || {}) };
    const bu = cfg.baseURL || '';
    if (bu === '' || bu.startsWith('/')) {
      cfg.baseURL = APP_BASE + bu;
    }
    return origCreate(cfg);
  };
  axios.__APP_BASE_PATCHED__ = true;
}

// Belt-and-braces: global interceptor on the default axios instance.
if (APP_BASE && axios && axios.interceptors && !axios.__APP_BASE_INTERCEPTOR__) {
  axios.interceptors.request.use((config) => {
    const url = config.url || '';
    if (typeof url === 'string' && url.startsWith('/') && !url.startsWith(APP_BASE + '/')) {
      config.url = APP_BASE + url;
    }
    return config;
  });
  axios.__APP_BASE_INTERCEPTOR__ = true;
}

// Patch window.fetch so generated code calling fetch('/api/foo') is also
// re-prefixed. Skips absolute URLs and paths already under APP_BASE.
if (APP_BASE && typeof window !== 'undefined' && window.fetch && !window.__APP_FETCH_PATCHED__) {
  const origFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {
    try {
      if (typeof input === 'string' && input.startsWith('/') && !input.startsWith(APP_BASE + '/')) {
        return origFetch(APP_BASE + input, init);
      }
      if (input instanceof Request && input.url) {
        const u = new URL(input.url, window.location.origin);
        if (u.origin === window.location.origin && u.pathname.startsWith('/') && !u.pathname.startsWith(APP_BASE + '/')) {
          const rewritten = APP_BASE + u.pathname + u.search + u.hash;
          return origFetch(new Request(rewritten, input), init);
        }
      }
    } catch (e) { /* fall through */ }
    return origFetch(input, init);
  };
  window.__APP_FETCH_PATCHED__ = true;
}
