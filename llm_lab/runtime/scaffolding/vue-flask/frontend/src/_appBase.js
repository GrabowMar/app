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
if (axios) { axios.defaults = axios.defaults || {}; axios.defaults.baseURL = APP_BASE; }

if (APP_BASE && axios && axios.create && !axios.__APP_BASE_PATCHED__) {
  const origCreate = axios.create.bind(axios);
  axios.create = (config = {}) => {
    const cfg = { ...(config || {}) };
    const bu = cfg.baseURL || '';
    if (bu === '' || bu.startsWith('/')) cfg.baseURL = APP_BASE + bu;
    return origCreate(cfg);
  };
  axios.__APP_BASE_PATCHED__ = true;
}
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
if (APP_BASE && typeof window !== 'undefined' && window.fetch && !window.__APP_FETCH_PATCHED__) {
  const origFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {
    try {
      if (typeof input === 'string' && input.startsWith('/') && !input.startsWith(APP_BASE + '/')) {
        return origFetch(APP_BASE + input, init);
      }
    } catch (e) { /* fall through */ }
    return origFetch(input, init);
  };
  window.__APP_FETCH_PATCHED__ = true;
}
