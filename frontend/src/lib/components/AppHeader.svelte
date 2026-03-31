<script lang="ts">
	import PanelLeft from '@lucide/svelte/icons/panel-left';
	import FlaskConical from '@lucide/svelte/icons/flask-conical';
	import User from '@lucide/svelte/icons/user';
	import Settings from '@lucide/svelte/icons/settings';
	import LogOut from '@lucide/svelte/icons/log-out';
	import { Separator } from '$lib/components/ui/separator';
	import { Button } from '$lib/components/ui/button';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	interface AuthState {
		isAuthenticated: boolean;
		user: { id: number; email: string; display?: string; name?: string } | null;
	}

	let { auth }: { auth: AuthState } = $props();
	let mobileMenuOpen = $state(false);
</script>

<header class="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:px-6">
	<button
		class="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground md:hidden"
		onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
	>
		<PanelLeft class="h-5 w-5" />
		<span class="sr-only">Toggle menu</span>
	</button>

	<a href="/" class="flex items-center gap-2 font-semibold">
		<FlaskConical class="h-5 w-5 text-primary" />
		<span class="hidden md:inline">LLM Lab</span>
	</a>

	<div class="flex-1"></div>

	<div class="flex items-center gap-2">
		<ThemeToggle />

		{#if auth.isAuthenticated && auth.user}
			<Separator orientation="vertical" class="mx-1 h-6" />
			<Button variant="ghost" size="sm" href="/users/settings" class="gap-2">
				<User class="h-4 w-4" />
				<span class="hidden md:inline">{auth.user.display || auth.user.name || auth.user.email}</span>
			</Button>
		{/if}
	</div>
</header>
