<script lang="ts">
	import '../app.css';
	import { getAuth } from '$lib/stores/auth.svelte';
	import { Toaster } from '$lib/components/ui/sonner';
	import { ModeWatcher } from 'mode-watcher';
	import CookieBanner from '$lib/components/CookieBanner.svelte';
	import { onMount } from 'svelte';

	let { children } = $props();
	const auth = getAuth();

	onMount(() => {
		auth.checkSession();
	});
</script>

<svelte:head>
	<title>LLM Lab</title>
</svelte:head>

<ModeWatcher />

<div class="min-h-screen">
	{@render children()}
</div>

<Toaster />
<CookieBanner />
