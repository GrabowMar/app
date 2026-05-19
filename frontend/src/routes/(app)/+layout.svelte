<script lang="ts">
	import { goto } from '$app/navigation';
	import { getAuth } from '$lib/stores/auth.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/AppSidebar.svelte';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import AppFooter from '$lib/components/AppFooter.svelte';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import { onMount } from 'svelte';

	let { children } = $props();
	const auth = getAuth();
	let loadingTooLong = $state(false);

	onMount(() => {
		const timer = setTimeout(() => {
			if (auth.isLoading) {
				loadingTooLong = true;
			}
		}, 5000);
		return () => clearTimeout(timer);
	});

	function forceReload() {
		// Navigate to clean URL (strips _r params) for a fresh start
		window.location.href = window.location.pathname;
	}

	$effect(() => {
		if (!auth.isLoading && !auth.isAuthenticated) {
			goto('/auth/login');
		}
	});
</script>

{#if auth.isLoading}
	<div class="flex min-h-dvh items-center justify-center bg-background">
		{#if loadingTooLong}
			<div class="flex flex-col items-center gap-4 text-center">
				<p class="text-muted-foreground">Loading is taking longer than expected.</p>
				<button
					onclick={forceReload}
					class="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 cursor-pointer transition-colors"
				>
					Reload Page
				</button>
			</div>
		{:else}
			<LoaderCircle class="size-7 animate-spin text-primary" />
		{/if}
	</div>
{:else if auth.isAuthenticated}
	<Sidebar.Provider>
		<AppSidebar />
		<Sidebar.Inset class="bg-background min-w-0">
			<AppHeader {auth} />
			<div class="flex min-h-[calc(100dvh-3rem)] flex-1 flex-col p-3 sm:p-4 md:p-5 min-w-0 overflow-x-clip">
				{@render children()}
			</div>
			<AppFooter />
		</Sidebar.Inset>
	</Sidebar.Provider>
{/if}
