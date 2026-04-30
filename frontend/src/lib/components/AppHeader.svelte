<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import PanelLeft from '@lucide/svelte/icons/panel-left';
	import FlaskConical from '@lucide/svelte/icons/flask-conical';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import User from '@lucide/svelte/icons/user';
	import Settings from '@lucide/svelte/icons/settings';
	import Key from '@lucide/svelte/icons/key';
	import LogOut from '@lucide/svelte/icons/log-out';
	import Boxes from '@lucide/svelte/icons/boxes';
	import AppWindow from '@lucide/svelte/icons/app-window';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import FileText from '@lucide/svelte/icons/file-text';
	import WandSparkles from '@lucide/svelte/icons/wand-sparkles';
	import Trophy from '@lucide/svelte/icons/trophy';
	import ChartColumn from '@lucide/svelte/icons/chart-column';
	import BookOpen from '@lucide/svelte/icons/book-open';
	import Zap from '@lucide/svelte/icons/zap';
	import Layers from '@lucide/svelte/icons/layers';
	import Circle from '@lucide/svelte/icons/circle';
	import X from '@lucide/svelte/icons/x';
	import { Separator } from '$lib/components/ui/separator';
	import * as Sheet from '$lib/components/ui/sheet';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import { getAuth } from '$lib/stores/auth.svelte';
	import { getPreferences } from '$lib/stores/preferences.svelte';
	import { cn } from '$lib/utils';
	import type { Component } from 'svelte';

	interface AuthState {
		isAuthenticated: boolean;
		user: { id: number; email: string; display?: string; name?: string } | null;
	}

	interface NavItem {
		label: string;
		href: string;
		icon: Component;
	}

	interface NavSection {
		title: string;
		items: NavItem[];
	}

	const navSections: NavSection[] = [
		{
			title: 'Platform',
			items: [
				{ label: 'Dashboard', href: '/', icon: FlaskConical },
				{ label: 'Models', href: '/models', icon: Boxes },
				{ label: 'Applications', href: '/applications', icon: AppWindow },
				{ label: 'Analysis', href: '/analysis', icon: BarChart3 },
			],
		},
		{
			title: 'Tools',
			items: [
				{ label: 'Automation', href: '/automation', icon: Zap },
				{ label: 'Sample Generator', href: '/sample-generator', icon: WandSparkles },
				{ label: 'Templates', href: '/sample-generator/templates', icon: Layers },
				{ label: 'Reports', href: '/reports', icon: FileText },
			],
		},
		{
			title: 'Insights',
			items: [
				{ label: 'Rankings', href: '/rankings', icon: Trophy },
				{ label: 'Statistics', href: '/statistics', icon: ChartColumn },
				{ label: 'Docs', href: '/docs', icon: BookOpen },
			],
		},
	];

	function isActive(href: string): boolean {
		const pathname = page.url?.pathname ?? '/';
		if (href === '/') return pathname === '/';
		return pathname === href || pathname.startsWith(href + '/');
	}

	let { auth }: { auth: AuthState } = $props();

	const authStore = getAuth();
	const preferences = getPreferences();

	let mobileMenuOpen = $state(false);
	let dropdownOpen = $state(false);

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
		cyan: 'bg-cyan-500'
	};

	const routeLabels: Record<string, string> = {
		'/': 'Dashboard',
		'/models': 'Models',
		'/applications': 'Applications',
		'/analysis': 'Analysis',
		'/reports': 'Reports',
		'/rankings': 'Rankings',
		'/statistics': 'Statistics',
		'/sample-generator': 'Sample Generator',
		'/automation': 'Automation',
		'/docs': 'Docs',
		'/about': 'About',
		'/privacy': 'Privacy Policy',
		'/users/settings': 'Settings'
	};

	let breadcrumbSegments = $derived.by(() => {
		const pathname = page.url?.pathname ?? '/';
		if (pathname === '/') return [{ label: 'Dashboard', href: '/' }];

		const parts = pathname.split('/').filter(Boolean);
		const segments: { label: string; href: string }[] = [];

		let accumulated = '';
		for (const part of parts) {
			accumulated += '/' + part;
			const label = routeLabels[accumulated];
			if (label) {
				segments.push({ label, href: accumulated });
			}
		}

		// If no segments matched (e.g. /models/some-slug), try the first-level path
		if (segments.length === 0) {
			const firstLevel = '/' + parts[0];
			const label = routeLabels[firstLevel];
			if (label) {
				segments.push({ label, href: firstLevel });
			}
		}

		// For sub-pages like /models/[slug], add the parent if not already present
		if (segments.length === 1 && parts.length > 1) {
			// Already have parent, which is correct for sub-page breadcrumb
		} else if (segments.length === 0) {
			// Unknown route — show pathname as-is
			segments.push({ label: parts[parts.length - 1], href: pathname });
		}

		return segments;
	});

	let avatarBgClass = $derived(avatarColorMap[preferences.avatarColor] ?? 'bg-blue-500');

	let userInitial = $derived.by(() => {
		if (!auth.user) return '?';
		const name = auth.user.display || auth.user.name || auth.user.email;
		return name.charAt(0).toUpperCase();
	});

	let userDisplayName = $derived.by(() => {
		if (!auth.user) return '';
		return auth.user.display || auth.user.name || auth.user.email;
	});

	function toggleDropdown() {
		dropdownOpen = !dropdownOpen;
	}

	function closeDropdown() {
		dropdownOpen = false;
	}

	function handleWindowClick(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (dropdownOpen && !target.closest('[data-user-menu]')) {
			closeDropdown();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && dropdownOpen) {
			closeDropdown();
		}
	}

	async function handleLogout() {
		closeDropdown();
		await authStore.logout();
		goto('/auth/login');
	}
</script>

<svelte:window onclick={handleWindowClick} onkeydown={handleKeydown} />

<header
	class="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/95 px-3 backdrop-blur supports-[backdrop-filter]:bg-background/60 sm:px-4 md:gap-4 md:px-6"
>
	<!-- Mobile sidebar trigger -->
	<Sheet.Root bind:open={mobileMenuOpen}>
		<Sheet.Trigger
			class="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground md:hidden touch-mobile-show"
		>
			<PanelLeft class="h-5 w-5" />
			<span class="sr-only">Toggle menu</span>
		</Sheet.Trigger>
		<Sheet.Content side="left" class="w-72 p-0" showClose={false}>
			<!-- Mobile nav header -->
			<div class="flex h-14 items-center justify-between border-b px-4">
				<a href="/" class="flex items-center gap-2" onclick={() => (mobileMenuOpen = false)}>
					<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
						<FlaskConical class="h-4 w-4" />
					</div>
					<span class="font-semibold">LLM Lab</span>
				</a>
				<button
					class="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
					onclick={() => (mobileMenuOpen = false)}
				>
					<X class="h-4 w-4" />
				</button>
			</div>

			<!-- Mobile nav sections -->
			<nav class="flex-1 overflow-y-auto py-3">
				{#each navSections as section (section.title)}
					<div class="px-4 pt-4 pb-1.5">
						<span class="text-[0.65rem] font-semibold uppercase tracking-wider text-muted-foreground/60">
							{section.title}
						</span>
					</div>
					<div class="flex flex-col gap-0.5 px-3">
						{#each section.items as item (item.href)}
							<a
								href={item.href}
								class={cn(
									'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
									isActive(item.href)
										? 'bg-accent text-accent-foreground font-medium'
										: 'text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground'
								)}
								onclick={() => (mobileMenuOpen = false)}
							>
								<item.icon class="h-4 w-4 shrink-0" />
								{item.label}
							</a>
						{/each}
					</div>
				{/each}
			</nav>

			<!-- Mobile nav footer -->
			<div class="border-t px-4 py-3">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2.5">
						<div class="relative flex h-2 w-2 shrink-0">
							<span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
							<span class="relative inline-flex h-2 w-2 rounded-full bg-green-500"></span>
						</div>
						<span class="text-xs text-muted-foreground">System Online</span>
					</div>
					<ThemeToggle />
				</div>
			</div>
		</Sheet.Content>
	</Sheet.Root>

	<a href="/" class="flex items-center gap-2 font-semibold">
		<FlaskConical class="h-5 w-5 text-primary" />
		<span class="hidden md:inline touch-mobile-hide-text">LLM Lab</span>
	</a>

	{#if breadcrumbSegments.length > 0}
		<nav aria-label="Breadcrumb" class="hidden items-center gap-1 text-sm text-muted-foreground md:flex touch-mobile-hide-nav">
			<ChevronRight class="h-4 w-4" />
			{#each breadcrumbSegments as segment, i}
				{#if i > 0}
					<ChevronRight class="h-4 w-4" />
				{/if}
				{#if i === breadcrumbSegments.length - 1}
					<span class="font-medium text-foreground">{segment.label}</span>
				{:else}
					<a href={segment.href} class="hover:text-foreground transition-colors">{segment.label}</a>
				{/if}
			{/each}
		</nav>
	{/if}

	<div class="flex-1"></div>

	<div class="flex items-center gap-2">
		<ThemeToggle />

		{#if auth.isAuthenticated && auth.user}
			<Separator orientation="vertical" class="mx-1 h-6" />

			<div class="relative" data-user-menu>
				<button
					class="flex items-center gap-2 rounded-full p-0.5 hover:ring-2 hover:ring-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
					onclick={toggleDropdown}
					aria-expanded={dropdownOpen}
					aria-haspopup="true"
				>
					<div
						class="{avatarBgClass} flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold text-white"
					>
						{userInitial}
					</div>
				</button>

				{#if dropdownOpen}
					<div
						class="absolute right-0 top-full mt-2 w-56 rounded-lg border bg-popover p-1.5 text-popover-foreground shadow-lg"
						role="menu"
					>
						<div class="px-3 py-2">
							<p class="text-sm font-medium">{userDisplayName}</p>
							{#if auth.user.display || auth.user.name}
								<p class="text-xs text-muted-foreground">{auth.user.email}</p>
							{/if}
						</div>

						<div role="separator" class="my-1 h-[1px] bg-border"></div>

						<a
							href="/users/settings#profile"
							class="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent"
							role="menuitem"
							onclick={closeDropdown}
						>
							<User class="h-4 w-4" />
							Profile
						</a>
						<a
							href="/users/settings#general"
							class="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent"
							role="menuitem"
							onclick={closeDropdown}
						>
							<Settings class="h-4 w-4" />
							Settings
						</a>
						<a
							href="/users/settings#api"
							class="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent"
							role="menuitem"
							onclick={closeDropdown}
						>
							<Key class="h-4 w-4" />
							API Access
						</a>

						<div role="separator" class="my-1 h-[1px] bg-border"></div>

						<button
							class="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm text-destructive hover:bg-accent"
							role="menuitem"
							onclick={handleLogout}
						>
							<LogOut class="h-4 w-4" />
							Logout
						</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</header>
