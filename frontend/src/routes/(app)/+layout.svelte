<script lang="ts">
	import { getAuth } from '$lib/stores/auth.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/AppSidebar.svelte';
	import AppHeader from '$lib/components/AppHeader.svelte';
	import AppFooter from '$lib/components/AppFooter.svelte';

	let { children } = $props();
	const auth = getAuth();
</script>

<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset class="bg-muted/40">
		<AppHeader {auth} />
		<div class="flex min-h-[calc(100vh-5.5rem)] flex-1 flex-col p-4 md:p-6">
			{@render children()}
		</div>
		<AppFooter />
	</Sidebar.Inset>
</Sidebar.Provider>
