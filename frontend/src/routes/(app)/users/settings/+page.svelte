<script lang="ts">
	import { getMe } from '$lib/api/client';
	import type { ApiUser } from '$lib/api/client';
	import { getPreferences, VALID_COLORS } from '$lib/stores/preferences.svelte';
	import * as Card from '$lib/components/ui/card';
	import { Separator } from '$lib/components/ui/separator';
	import { onMount } from 'svelte';
	import Shield from '@lucide/svelte/icons/shield';
	import Cookie from '@lucide/svelte/icons/cookie';
	import ProfileSection from '$lib/components/users-settings/ProfileSection.svelte';
	import SecuritySection from '$lib/components/users-settings/SecuritySection.svelte';
	import TokenSection from '$lib/components/users-settings/TokenSection.svelte';
	import PreferencesSection from '$lib/components/users-settings/PreferencesSection.svelte';

	const prefs = getPreferences();

	type TabId = 'general' | 'profile' | 'api';
	const TABS: { id: TabId; label: string }[] = [
		{ id: 'general', label: 'General' },
		{ id: 'profile', label: 'Profile' },
		{ id: 'api', label: 'API Access' },
	];

	let activeTab = $state<TabId>('general');

	let profile = $state<ApiUser | null>(null);
	let loading = $state(true);

	const avatarColorMap: Record<string, string> = {
		blue: 'bg-blue-500',
		indigo: 'bg-indigo-500',
		purple: 'bg-purple-500',
		pink: 'bg-pink-500',
		red: 'bg-red-500',
		orange: 'bg-orange-500',
		amber: 'bg-amber-500',
		green: 'bg-green-500',
		teal: 'bg-teal-500',
		cyan: 'bg-cyan-500',
	};

	const accentRingMap: Record<string, string> = {
		blue: 'ring-blue-500',
		indigo: 'ring-indigo-500',
		purple: 'ring-purple-500',
		pink: 'ring-pink-500',
		red: 'ring-red-500',
		orange: 'ring-orange-500',
		amber: 'ring-amber-500',
		green: 'ring-green-500',
		teal: 'ring-teal-500',
		cyan: 'ring-cyan-500',
	};

	function readHash(): TabId {
		if (typeof window === 'undefined') return 'general';
		const hash = window.location.hash.replace('#', '') as TabId;
		if (TABS.some((t) => t.id === hash)) return hash;
		return 'general';
	}

	function switchTab(tab: TabId) {
		activeTab = tab;
		window.location.hash = tab;
	}

	onMount(() => {
		activeTab = readHash();

		const onHashChange = () => {
			activeTab = readHash();
		};
		window.addEventListener('hashchange', onHashChange);

		getMe()
			.then((user) => {
				profile = user;
			})
			.catch(() => {})
			.finally(() => {
				loading = false;
			});

		return () => {
			window.removeEventListener('hashchange', onHashChange);
		};
	});

	let userInitial = $derived.by(() => {
		if (!profile) return '?';
		const display = profile.name || profile.email;
		return display.charAt(0).toUpperCase();
	});
</script>

<svelte:head>
	<title>Settings - LLM Lab</title>
</svelte:head>

<div class="mx-auto max-w-4xl space-y-6">
	<div class="page-header">
		<h1>Settings</h1>
		<p>Customize your account and application preferences.</p>
	</div>

	<!-- Tab Navigation -->
	<div class="flex gap-6 border-b border-border overflow-x-auto flex-nowrap whitespace-nowrap">
		{#each TABS as tab}
			<button
				type="button"
				class="pb-2 text-sm transition-colors {activeTab === tab.id
					? 'border-b-2 border-primary text-foreground font-medium'
					: 'text-muted-foreground hover:text-foreground'}"
				onclick={() => switchTab(tab.id)}
			>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- ====================== TAB 1: GENERAL ====================== -->
	{#if activeTab === 'general'}
		<div class="space-y-6">
			<PreferencesSection {avatarColorMap} {accentRingMap} />
		</div>

	<!-- ====================== TAB 2: PROFILE ====================== -->
	{:else if activeTab === 'profile'}
		<div class="space-y-6">
			{#if loading}
				<div class="space-y-4 animate-pulse">
					<div class="h-48 rounded-lg bg-muted"></div>
				</div>
			{:else}
				<ProfileSection {profile} onUpdated={(user) => (profile = user)} />
				<SecuritySection />
			{/if}
		</div>

	<!-- ====================== TAB 3: API ACCESS ====================== -->
	{:else if activeTab === 'api'}
		<div class="space-y-6">
			<TokenSection />

			<!-- Avatar Color -->
			<Card.Root>
				<Card.Header>
					<Card.Title>Avatar Color</Card.Title>
					<Card.Description>Choose the color for your user avatar.</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-4">
					<div class="flex flex-col items-center gap-4 sm:flex-row sm:gap-6">
						<div
							class="flex h-14 w-14 items-center justify-center rounded-full text-xl font-bold text-white {avatarColorMap[prefs.avatarColor]}"
						>
							{userInitial}
						</div>
						<div class="flex flex-wrap gap-2">
							{#each VALID_COLORS as color}
								<button
									type="button"
									class="h-8 w-8 rounded-full cursor-pointer transition-all {avatarColorMap[color]} {prefs.avatarColor ===
									color
										? `ring-2 ring-offset-2 ring-offset-background ${accentRingMap[color]}`
										: 'hover:scale-110'}"
									title={color}
									onclick={() => prefs.setAvatarColor(color)}
								></button>
							{/each}
						</div>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Cookie & Data Settings -->
			<Card.Root>
				<Card.Header>
					<Card.Title class="flex items-center gap-2">
						<Cookie class="h-5 w-5" />
						Cookie &amp; Data Settings
					</Card.Title>
					<Card.Description>Manage how we use cookies and process your data.</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-5">
					<!-- Essential -->
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-0.5">
							<div class="flex items-center gap-2">
								<Shield class="h-4 w-4 text-muted-foreground" />
								<p class="text-sm font-medium">Essential</p>
							</div>
							<p class="text-xs text-muted-foreground">Required for basic functionality including authentication and security.</p>
						</div>
						<label class="relative inline-flex cursor-not-allowed items-center opacity-60">
							<input type="checkbox" checked={true} disabled class="peer sr-only" />
							<div
								class="h-5 w-9 rounded-full bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:translate-x-4 after:content-['']"
							></div>
						</label>
					</div>

					<Separator />

					<!-- Analytics -->
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-0.5">
							<p class="text-sm font-medium">Analytics &amp; Performance</p>
							<p class="text-xs text-muted-foreground">Help us understand how you use the application to improve performance.</p>
						</div>
						<label class="relative inline-flex cursor-pointer items-center">
							<input
								type="checkbox"
								checked={prefs.cookieConsent.analytics}
								onchange={(e) => prefs.setCookieConsent({ analytics: e.currentTarget.checked })}
								class="peer sr-only"
							/>
							<div
								class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
							></div>
						</label>
					</div>

					<Separator />

					<!-- Functional -->
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-0.5">
							<p class="text-sm font-medium">Functional &amp; Preferences</p>
							<p class="text-xs text-muted-foreground">Remember your preferences and settings for a personalized experience.</p>
						</div>
						<label class="relative inline-flex cursor-pointer items-center">
							<input
								type="checkbox"
								checked={prefs.cookieConsent.functional}
								onchange={(e) => prefs.setCookieConsent({ functional: e.currentTarget.checked })}
								class="peer sr-only"
							/>
							<div
								class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
							></div>
						</label>
					</div>

					<Separator />

					<!-- AI Processing -->
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-0.5">
							<p class="text-sm font-medium">AI Processing &amp; History</p>
							<p class="text-xs text-muted-foreground">Store AI analysis results and processing history for faster access.</p>
						</div>
						<label class="relative inline-flex cursor-pointer items-center">
							<input
								type="checkbox"
								checked={prefs.cookieConsent.ai}
								onchange={(e) => prefs.setCookieConsent({ ai: e.currentTarget.checked })}
								class="peer sr-only"
							/>
							<div
								class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
							></div>
						</label>
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	{/if}
</div>
