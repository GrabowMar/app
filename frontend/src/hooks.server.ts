import type { Handle, HandleServerError } from '@sveltejs/kit';

const API_TARGET = process.env.API_TARGET ?? 'http://localhost:8001';

const PROXY_PREFIXES = ['/api/', '/_allauth/', '/admin/', '/media/', '/app/'];

// RFC 7230 §6.1 hop-by-hop headers — must not be forwarded. Node's undici
// fetch rejects multi-value `Connection` headers (e.g. "upgrade, close"
// added by nginx) with InvalidArgumentError, so we strip them all.
const HOP_BY_HOP = new Set([
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailer',
    'trailers',
    'transfer-encoding',
    'upgrade',
    // Host header must reflect the upstream target, not the incoming request,
    // or undici may refuse to set it explicitly.
    'host',
    'content-length'
]);

function sanitizeRequestHeaders(headers: Headers): Headers {
    const out = new Headers();
    headers.forEach((value, key) => {
        if (!HOP_BY_HOP.has(key.toLowerCase())) {
            out.set(key, value);
        }
    });
    return out;
}

function sanitizeResponseHeaders(headers: Headers): Headers {
    const out = new Headers();
    headers.forEach((value, key) => {
        const k = key.toLowerCase();
        if (k === 'content-length' || k === 'transfer-encoding' || k === 'connection') {
            return;
        }
        out.append(key, value);
    });
    return out;
}

export const handle: Handle = async ({ event, resolve }) => {
    const path = event.url.pathname;

    if (PROXY_PREFIXES.some((prefix) => path.startsWith(prefix))) {
        const targetUrl = `${API_TARGET}${path}${event.url.search}`;
        const reqBody =
            event.request.method !== 'GET' && event.request.method !== 'HEAD'
                ? await event.request.arrayBuffer()
                : undefined;

        const upstream = await fetch(targetUrl, {
            method: event.request.method,
            headers: sanitizeRequestHeaders(event.request.headers),
            body: reqBody,
            // @ts-expect-error Node 18+ fetch supports duplex
            duplex: reqBody ? 'half' : undefined,
            redirect: 'manual'
        });

        return new Response(upstream.body, {
            status: upstream.status,
            statusText: upstream.statusText,
            headers: sanitizeResponseHeaders(upstream.headers)
        });
    }

    return resolve(event);
};

export const handleError: HandleServerError = async ({ error }) => {
    console.error('Server error:', error);
    return {
        message: 'An unexpected error occurred'
    };
};
