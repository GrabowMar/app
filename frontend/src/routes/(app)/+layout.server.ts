import { redirect } from '@sveltejs/kit';

import type { LayoutServerLoad } from './$types';

import type { AuthUser } from '$lib/stores/auth.svelte';

const API_TARGET = process.env.API_TARGET ?? 'http://localhost:8001';

export const load: LayoutServerLoad = async ({ request, url }) => {
	let res: Response | null = null;
	let user: AuthUser | null = null;

	try {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 5000);
		res = await globalThis.fetch(`${API_TARGET}/_allauth/browser/v1/auth/session`, {
			headers: {
				accept: 'application/json',
				cookie: request.headers.get('cookie') ?? '',
			},
			signal: controller.signal,
		});
		clearTimeout(timeoutId);

		const body = await res.json().catch(() => null);
		user = (body?.data?.user ?? null) as AuthUser | null;
	} catch {
		res = null;
		user = null;
	}

	if (!res?.ok || !user) {
		const next = encodeURIComponent(`${url.pathname}${url.search}`);
		throw redirect(303, `/auth/login?next=${next}`);
	}

	return { authUser: user };
};
