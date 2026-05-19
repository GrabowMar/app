<script lang="ts">
	import '$lib/styles/docs.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { getDocsTree, getDocsCategories } from '$lib/api/system';
	import type { DocNode } from '$lib/api/system';
	import { groupByCategory } from '$lib/docs/utils';
	import { metaFor, CATEGORY_ORDER } from '$lib/docs/categories';
	import CommandPalette from '$lib/components/docs/CommandPalette.svelte';
	import Search from '@lucide/svelte/icons/search';
	import Menu from '@lucide/svelte/icons/menu';
	import X from '@lucide/svelte/icons/x';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import FileText from '@lucide/svelte/icons/file-text';
	import House from '@lucide/svelte/icons/house';

	let { children } = $props();

	let tree = $state<DocNode[]>([]);
	let categoryOrder = $state<string[]>(CATEGORY_ORDER);
	let paletteOpen = $state(false);
	let mobileOpen = $state(false);

	const grouped = $derived(groupByCategory(tree, categoryOrder));
	const currentSlug = $derived(($page.params?.slug as string | undefined) ?? '');

	onMount(async () => {
		const [t, c] = await Promise.all([getDocsTree(), getDocsCategories().catch(() => CATEGORY_ORDER)]);
		tree = t;
		if (Array.isArray(c) && c.length) categoryOrder = c;
	});

	$effect(() => {
		// Close mobile drawer on navigation.
		const _ = currentSlug;
		mobileOpen = false;
	});

	function isActive(slug: string) {
		return currentSlug === slug;
	}
</script>

<svelte:head>
	<title>Documentation - LLM Lab</title>
</svelte:head>

<div class="relative flex min-h-screen">
	<!-- Mobile top bar -->
	<div class="absolute left-0 right-0 top-0 z-30 flex items-center justify-between border-b bg-background/95 px-4 py-2 backdrop-blur md:hidden">
		<button
			type="button"
			class="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-muted"
			aria-label="Open navigation"
			onclick={() => (mobileOpen = !mobileOpen)}
		>
			{#if mobileOpen}<X class="h-4 w-4" />{:else}<Menu class="h-4 w-4" />{/if}
		</button>
		<button
			type="button"
			class="inline-flex items-center gap-2 rounded border bg-muted/30 px-3 py-1 text-xs text-muted-foreground"
			onclick={() => (paletteOpen = true)}
		>
			<Search class="h-3.5 w-3.5" />
			Search docs
		</button>
	</div>

	<!-- Sidebar -->
	<aside
		class="{mobileOpen
			? 'fixed inset-0 z-40 block bg-background/95 backdrop-blur'
			: 'hidden'} w-full shrink-0 border-r bg-muted/20 md:relative md:block md:w-72"
	>
		<div class="sticky top-0 flex h-screen flex-col overflow-y-auto p-4 pt-14 md:pt-4">
			<div class="mb-3 flex items-center justify-between">
				<a href="/docs" class="flex items-center gap-2 text-sm font-semibold tracking-tight">
					<House class="h-4 w-4 text-primary" />
					Documentation
				</a>
			</div>

			<!-- Search trigger -->
			<button
				type="button"
				onclick={() => (paletteOpen = true)}
				class="mb-3 flex items-center justify-between rounded-md border bg-background px-2.5 py-1.5 text-left text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
			>
				<span class="flex items-center gap-2">
					<Search class="h-3.5 w-3.5" />
					Search docs…
				</span>
				<kbd class="hidden rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] sm:inline">
					⌘K
				</kbd>
			</button>

			<!-- Categorized tree -->
			<nav class="flex-1 space-y-4">
				<a
					href="/docs"
					class="flex items-center gap-1.5 rounded px-2 py-1.5 text-xs transition-colors hover:bg-muted {currentSlug === ''
						? 'bg-muted font-medium text-foreground'
						: 'text-muted-foreground hover:text-foreground'}"
				>
					<FileText class="h-3.5 w-3.5 shrink-0" />
					Overview
				</a>

				{#each grouped as group (group.category)}
					{@const meta = metaFor(group.category)}
					{@const Icon = meta.icon}
					<div>
						<div class="mb-1 flex items-center gap-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
							<Icon class="h-3 w-3 {meta.accent}" />
							{group.category}
						</div>
						<ul class="space-y-0.5 border-l border-border/60 pl-2">
							{#each group.items as item (item.slug)}
								<li>
									<a
										href="/docs/{item.slug}"
										class="-ml-px flex items-center gap-1.5 border-l-2 py-1 pl-2 pr-2 text-xs transition-colors {isActive(item.slug)
											? 'border-primary bg-muted font-medium text-foreground'
											: 'border-transparent text-muted-foreground hover:border-border hover:text-foreground'}"
									>
										<ChevronRight class="h-3 w-3 shrink-0 opacity-50" />
										<span class="truncate">{item.title}</span>
									</a>
								</li>
							{/each}
						</ul>
					</div>
				{/each}
			</nav>
		</div>
	</aside>

	<!-- Main content -->
	<main class="min-w-0 flex-1 pt-12 md:pt-0">
		{@render children()}
	</main>
</div>

<CommandPalette bind:open={paletteOpen} {tree} onclose={() => (paletteOpen = false)} />
