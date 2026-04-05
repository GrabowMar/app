<script lang="ts">
	import FlaskConical from '@lucide/svelte/icons/flask-conical';
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
	import ChevronsLeft from '@lucide/svelte/icons/chevrons-left';
	import ChevronsRight from '@lucide/svelte/icons/chevrons-right';
	import Circle from '@lucide/svelte/icons/circle';
	import { page } from '$app/state';
	import { cn } from '$lib/utils';
	import { getPreferences } from '$lib/stores/preferences.svelte';
	import type { Component } from 'svelte';

	const prefs = getPreferences();

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
		if (href === '/') return page.url.pathname === '/';
		// Exact match for child routes to avoid parent always being active
		if (page.url.pathname === href) return true;
		// Only match parent if we're not on a more specific child
		return page.url.pathname.startsWith(href + '/') || page.url.pathname === href;
	}
</script>

<aside
	class={cn(
		'hidden shrink-0 border-r bg-sidebar md:flex md:flex-col transition-all duration-200 touch-mobile-hide',
		prefs.sidebarCollapsed ? 'w-16' : 'w-64'
	)}
>
	<!-- Brand header -->
	<div class="flex h-14 items-center border-b px-3 justify-between">
		<a href="/" class="flex items-center gap-2 min-w-0">
			<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
				<FlaskConical class="h-4 w-4" />
			</div>
			{#if !prefs.sidebarCollapsed}
				<span class="font-semibold text-sidebar-foreground truncate">LLM Lab</span>
			{/if}
		</a>
		<button
			onclick={() => prefs.toggleSidebar()}
			class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-sidebar-foreground/50 hover:bg-sidebar-accent hover:text-sidebar-foreground transition-colors"
			title={prefs.sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
		>
			{#if prefs.sidebarCollapsed}
				<ChevronsRight class="h-4 w-4" />
			{:else}
				<ChevronsLeft class="h-4 w-4" />
			{/if}
		</button>
	</div>

	<!-- Navigation -->
	<nav class="flex-1 overflow-y-auto no-scrollbar py-2" style="max-height: calc(100vh - 3.5rem - 3rem);">
		{#each navSections as section (section.title)}
			{#if !prefs.sidebarCollapsed}
				<div class="px-4 pt-4 pb-1">
					<span class="text-[0.65rem] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
						{section.title}
					</span>
				</div>
			{:else}
				<div class="my-2 mx-3">
					<div class="h-px bg-sidebar-foreground/10"></div>
				</div>
			{/if}

			<div class={cn('flex flex-col gap-0.5', prefs.sidebarCollapsed ? 'px-2' : 'px-3')}>
				{#each section.items as item (item.href)}
					<a
						href={item.href}
						class={cn(
							'group relative flex items-center rounded-lg text-sm transition-colors',
							prefs.sidebarCollapsed ? 'justify-center px-0 py-2.5' : 'gap-3 px-3 py-2',
							isActive(item.href)
								? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
								: 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground'
						)}
						title={prefs.sidebarCollapsed ? item.label : undefined}
					>
						<item.icon class="h-4 w-4 shrink-0" />
						{#if !prefs.sidebarCollapsed}
							{item.label}
						{/if}
						<!-- Tooltip for collapsed state -->
						{#if prefs.sidebarCollapsed}
							<div class="pointer-events-none absolute left-full ml-2 hidden rounded-md bg-popover px-2.5 py-1.5 text-xs font-medium text-popover-foreground shadow-md border group-hover:block z-50 whitespace-nowrap">
								{item.label}
							</div>
						{/if}
					</a>
				{/each}
			</div>
		{/each}
	</nav>

	<!-- Status footer -->
	<div class={cn('border-t px-3 py-2.5 mt-auto', prefs.sidebarCollapsed ? 'flex justify-center' : '')}>
		{#if prefs.sidebarCollapsed}
			<div class="relative" title="System Online">
				<Circle class="h-3 w-3 fill-green-500 text-green-500" />
			</div>
		{:else}
			<div class="flex items-center gap-2.5">
				<div class="relative flex h-2 w-2 shrink-0">
					<span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
					<span class="relative inline-flex h-2 w-2 rounded-full bg-green-500"></span>
				</div>
				<div class="min-w-0">
					<div class="text-xs font-medium text-sidebar-foreground">System Online</div>
					<div class="text-[0.65rem] text-sidebar-foreground/50">v2.0.0 · Stable</div>
				</div>
			</div>
		{/if}
	</div>
</aside>
