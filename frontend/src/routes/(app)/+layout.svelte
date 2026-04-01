<script lang="ts">
	import { goto } from '$app/navigation';
	import { getAuth } from '$lib/stores/auth.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/AppSidebar.svelte';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import AppFooter from '$lib/components/AppFooter.svelte';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';

	let { children } = $props();
	const auth = getAuth();

	$effect(() => {
		if (!auth.isLoading && !auth.isAuthenticated) {
			goto('/auth/login');
		}
	});
</script>

{#if auth.isLoading}
	<div class="flex min-h-screen items-center justify-center">
		<LoaderCircle class="size-8 animate-spin text-muted-foreground" />
	</div>
{:else if auth.isAuthenticated}
	<Sidebar.Provider>
		<AppSidebar />
		<Sidebar.Inset class="bg-muted/40 min-w-0">
			<AppHeader {auth} />
			<div class="flex min-h-[calc(100vh-5.5rem)] flex-1 flex-col p-4 md:p-6 min-w-0 overflow-x-hidden">
				{@render children()}
			</div>
			<AppFooter />
		</Sidebar.Inset>
	</Sidebar.Provider>
{/if}
