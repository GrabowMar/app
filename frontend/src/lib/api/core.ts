const ALLAUTH_BASE = '/_allauth/browser/v1';
const API_BASE = '/api';

export function getCsrfToken(): string {
	const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
	return match ? decodeURIComponent(match[1]) : '';
}

export async function allauthFetch(path: string, options: RequestInit = {}): Promise<Response> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string>),
	};
	const method = (options.method || 'GET').toUpperCase();
	if (method !== 'GET' && method !== 'HEAD') {
		headers['X-CSRFToken'] = getCsrfToken();
	}
	const res = await fetch(`${ALLAUTH_BASE}${path}`, {
		...options,
		headers,
		credentials: 'include',
	});
	return res;
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string>),
	};
	const method = (options.method || 'GET').toUpperCase();
	if (method !== 'GET' && method !== 'HEAD') {
		headers['X-CSRFToken'] = getCsrfToken();
	}
	const res = await fetch(`${API_BASE}${path}`, {
		...options,
		headers,
		credentials: 'include',
	});
	if (!res.ok) {
		if (res.status === 401) {
			window.location.href = '/auth/login';
			return new Promise<Response>(() => {});
		}
		const body = await res.json().catch(() => ({}));
		throw body;
	}
	return res;
}
