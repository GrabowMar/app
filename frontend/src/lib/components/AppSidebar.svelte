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
	import { page } from '$app/state';
	import { cn } from '$lib/utils';
	import type { Component } from 'svelte';

	interface NavItem {
		label: string;
		href: string;
		icon: Component;
	}

	const navItems: NavItem[] = [
		{ label: 'Dashboard', href: '/', icon: FlaskConical },
		{ label: 'Models', href: '/models', icon: Boxes },
		{ label: 'Applications', href: '/applications', icon: AppWindow },
		{ label: 'Analysis', href: '/analysis', icon: BarChart3 },
		{ label: 'Reports', href: '/reports', icon: FileText },
		{ label: 'Rankings', href: '/rankings', icon: Trophy },
		{ label: 'Statistics', href: '/statistics', icon: ChartColumn },
		{ label: 'Sample Generator', href: '/sample-generator', icon: WandSparkles },
		{ label: 'Automation', href: '/automation', icon: Zap },
		{ label: 'Docs', href: '/docs', icon: BookOpen },
	];

	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}
</script>

<aside class="hidden w-64 shrink-0 border-r bg-sidebar md:block">
	<div class="flex h-14 items-center gap-2 border-b px-4">
		<FlaskConical class="h-5 w-5 text-sidebar-primary" />
		<span class="font-semibold text-sidebar-foreground">LLM Lab</span>
	</div>
	<nav class="flex flex-col gap-1 p-3 no-scrollbar overflow-y-auto" style="max-height: calc(100vh - 3.5rem);">
		{#each navItems as item (item.href)}
			<a
				href={item.href}
				class={cn(
					'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
					isActive(item.href)
						? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
						: 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground'
				)}
			>
				<item.icon class="h-4 w-4 shrink-0" />
				{item.label}
			</a>
		{/each}
	</nav>
</aside>
