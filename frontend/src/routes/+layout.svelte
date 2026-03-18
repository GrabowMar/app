<script lang="ts">
	import '../app.css';
	import { getAuth } from '$lib/stores/auth.svelte';
	import Navbar from '$lib/components/Navbar.svelte';
	import { Toaster } from '$lib/components/ui/sonner';
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

<div class="min-h-screen bg-background text-foreground">
	<Navbar {auth} />
	<main class="container mx-auto px-4 py-8">
		{@render children()}
	</main>
</div>

<Toaster />
