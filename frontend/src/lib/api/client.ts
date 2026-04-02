const ALLAUTH_BASE = '/_allauth/browser/v1';
const API_BASE = '/api';

export interface ApiUser {
	email: string;
	name: string;
	url: string;
}

async function allauthFetch(path: string, options: RequestInit = {}): Promise<Response> {
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

function getCsrfToken(): string {
	const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
	return match ? decodeURIComponent(match[1]) : '';
}

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
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

export async function authenticate2FA(code: string): Promise<void> {
	const res = await allauthFetch('/auth/2fa/authenticate', {
		method: 'POST',
		body: JSON.stringify({ code }),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function verifyEmail(key: string): Promise<void> {
	const res = await allauthFetch('/auth/email/verify', {
		method: 'POST',
		body: JSON.stringify({ key }),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function requestPasswordReset(email: string): Promise<void> {
	const res = await allauthFetch('/auth/password/request', {
		method: 'POST',
		body: JSON.stringify({ email }),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function resetPassword(key: string, password: string): Promise<void> {
	const res = await allauthFetch('/auth/password/reset', {
		method: 'POST',
		body: JSON.stringify({ key, password }),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function getMe(): Promise<ApiUser> {
	const res = await apiFetch('/users/me/');
	return res.json();
}

export async function getUser(pk: number): Promise<ApiUser> {
	const res = await apiFetch(`/users/${pk}/`);
	return res.json();
}

export async function updateMe(data: { name: string }): Promise<ApiUser> {
	const res = await apiFetch('/users/me/', {
		method: 'PATCH',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function changePassword(data: {
	current_password: string;
	new_password: string;
}): Promise<void> {
	const res = await allauthFetch('/account/password/change', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function logout(): Promise<void> {
	const res = await allauthFetch('/auth/session', {
		method: 'DELETE',
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

// ---------------------------------------------------------------------------
// API Token Management
// ---------------------------------------------------------------------------

export interface ApiTokenInfo {
	key_preview: string;
	created_at: string;
}

export interface ApiTokenCreated {
	key: string;
	created_at: string;
}

export async function getApiToken(): Promise<ApiTokenInfo | null> {
	const res = await apiFetch('/users/me/token/');
	return res.json();
}

export async function getApiTokenSafe(): Promise<ApiTokenInfo | null> {
	try {
		const headers: Record<string, string> = { 'Content-Type': 'application/json' };
		const res = await fetch(`${API_BASE}/users/me/token/`, {
			headers,
			credentials: 'include',
		});
		if (res.status === 404) return null;
		if (res.status === 401) {
			window.location.href = '/auth/login';
			return new Promise<null>(() => {});
		}
		if (!res.ok) throw new Error('Failed to check token');
		return res.json();
	} catch {
		return null;
	}
}

export async function generateApiToken(): Promise<ApiTokenCreated> {
	const res = await apiFetch('/users/me/token/', { method: 'POST' });
	return res.json();
}

export async function revokeApiToken(): Promise<void> {
	await apiFetch('/users/me/token/', { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// LLM Models
// ---------------------------------------------------------------------------

export interface LLMModelSummary {
	id: number;
	model_id: string;
	canonical_slug: string;
	provider: string;
	model_name: string;
	description: string;
	is_free: boolean;
	context_window: number;
	max_output_tokens: number;
	context_window_display: string;
	input_price_per_million: number;
	output_price_per_million: number;
	capabilities: string[];
	cost_efficiency: number;
	supports_vision: boolean;
	supports_function_calling: boolean;
	supports_streaming: boolean;
	supports_json_mode: boolean;
}

export interface LLMModelDetail extends LLMModelSummary {
	description: string;
	max_output_tokens: number;
	input_price_per_token: number;
	output_price_per_token: number;
	metadata: Record<string, unknown>;
	capabilities_json: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

export interface PaginatedModels {
	items: LLMModelSummary[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface ModelsStats {
	total: number;
	providers: number;
	free: number;
	avg_input_price: number;
	avg_output_price: number;
}

export interface SyncResult {
	fetched: number;
	upserted: number;
}

export async function getModels(params: {
	page?: number;
	per_page?: number;
	search?: string;
	provider?: string;
	capability?: string;
	free_only?: boolean;
	sort_by?: string;
	sort_dir?: 'asc' | 'desc';
	price_range?: string;
	context_range?: string;
} = {}): Promise<PaginatedModels> {
	const q = new URLSearchParams();
	if (params.page) q.set('page', String(params.page));
	if (params.per_page) q.set('per_page', String(params.per_page));
	if (params.search) q.set('search', params.search);
	if (params.provider) q.set('provider', params.provider);
	if (params.capability) q.set('capability', params.capability);
	if (params.free_only) q.set('free_only', 'true');
	if (params.sort_by) q.set('sort_by', params.sort_by);
	if (params.sort_dir) q.set('sort_dir', params.sort_dir);
	if (params.price_range) q.set('price_range', params.price_range);
	if (params.context_range) q.set('context_range', params.context_range);
	const qs = q.toString();
	const res = await apiFetch(`/models/${qs ? '?' + qs : ''}`);
	return res.json();
}

export async function getModel(slug: string): Promise<LLMModelDetail> {
	const res = await apiFetch(`/models/detail/${slug}/`);
	return res.json();
}

export async function getModelsStats(): Promise<ModelsStats> {
	const res = await apiFetch('/models/stats/');
	return res.json();
}

export async function getProviders(): Promise<string[]> {
	const res = await apiFetch('/models/providers/');
	return res.json();
}

export async function syncModelsFromOpenRouter(): Promise<SyncResult> {
	const res = await apiFetch('/models/sync/', { method: 'POST' });
	return res.json();
}

export async function deleteModel(slug: string): Promise<void> {
	await apiFetch(`/models/detail/${slug}/`, { method: 'DELETE' });
}

export async function getRelatedModels(slug: string, limit = 10): Promise<LLMModelSummary[]> {
	const res = await apiFetch(`/models/detail/${slug}/related/?limit=${limit}`);
	return res.json();
}
