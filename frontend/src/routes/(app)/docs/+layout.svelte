<script lang="ts">
	import '../../../lib/styles/pygments.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { getDocsTree, searchDocs } from '$lib/api/client';
	import type { DocNode, DocSearchResult } from '$lib/api/client';
	import Search from '@lucide/svelte/icons/search';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import FileText from '@lucide/svelte/icons/file-text';
	import Folder from '@lucide/svelte/icons/folder';
	import { Input } from '$lib/components/ui/input';

	let { children } = $props();

	let tree: DocNode[] = $state([]);
	let searchQuery = $state('');
	let searchResults: DocSearchResult[] = $state([]);
	let searchTimeout: ReturnType<typeof setTimeout> | null = null;
	let isSearching = $state(false);

	onMount(async () => {
		tree = await getDocsTree();
	});

	function handleSearch(q: string) {
		if (searchTimeout) clearTimeout(searchTimeout);
		if (!q.trim()) {
			searchResults = [];
			isSearching = false;
			return;
		}
		isSearching = true;
		searchTimeout = setTimeout(async () => {
			searchResults = await searchDocs(q);
			isSearching = false;
		}, 200);
	}

	$effect(() => {
		handleSearch(searchQuery);
	});

	function currentSlug() {
		return $page.params?.slug ?? '';
	}

	function isActive(slug: string) {
		return currentSlug() === slug;
	}
</script>

<div class="flex min-h-screen gap-0">
	<!-- Sidebar -->
	<aside class="hidden w-64 shrink-0 border-r bg-muted/30 md:flex md:flex-col">
		<div class="sticky top-0 flex flex-col gap-2 overflow-y-auto p-4 h-screen">
			<h2 class="mb-1 text-sm font-semibold tracking-tight text-foreground">Documentation</h2>

			<!-- Search box -->
			<div class="relative mb-2">
				<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
				<Input
					bind:value={searchQuery}
					placeholder="Search docs…"
					class="h-8 pl-8 text-xs"
				/>
			</div>

			{#if searchQuery.trim()}
				<!-- Search results -->
				<div class="space-y-1">
					{#if isSearching}
						<p class="px-2 text-xs text-muted-foreground">Searching…</p>
					{:else if searchResults.length === 0}
						<p class="px-2 text-xs text-muted-foreground">No results</p>
					{:else}
						{#each searchResults as r (r.slug)}
							<button
								onclick={() => { searchQuery = ''; goto(`/docs/${r.slug}`); }}
								class="w-full rounded px-2 py-1.5 text-left text-xs hover:bg-muted transition-colors {isActive(r.slug) ? 'bg-muted font-medium' : ''}"
							>
								<span class="block font-medium truncate">{r.title}</span>
								<span class="block text-muted-foreground line-clamp-1 text-[11px]">{r.snippet}</span>
							</button>
						{/each}
					{/if}
				</div>
			{:else}
				<!-- Tree nav -->
				<nav class="space-y-0.5">
					<a
						href="/docs"
						class="flex items-center gap-1.5 rounded px-2 py-1.5 text-xs transition-colors hover:bg-muted {currentSlug() === '' ? 'bg-muted font-medium' : 'text-muted-foreground hover:text-foreground'}"
					>
						<FileText class="h-3.5 w-3.5 shrink-0" />
						Overview
					</a>
					{#each tree as node (node.slug)}
						{#if node.children.length > 0}
							<div>
								<div class="flex items-center gap-1 px-2 py-1 text-xs font-medium text-foreground/70">
									<Folder class="h-3.5 w-3.5 shrink-0" />
									{node.title}
								</div>
								<div class="ml-3 space-y-0.5 border-l pl-2">
									{#each node.children as child (child.slug)}
										<a
											href="/docs/{child.slug}"
											class="flex items-center gap-1.5 rounded px-2 py-1 text-xs transition-colors hover:bg-muted {isActive(child.slug) ? 'bg-muted font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'}"
										>
											<ChevronRight class="h-3 w-3 shrink-0 opacity-50" />
											{child.title}
										</a>
									{/each}
								</div>
							</div>
						{:else}
							<a
								href="/docs/{node.slug}"
								class="flex items-center gap-1.5 rounded px-2 py-1.5 text-xs transition-colors hover:bg-muted {isActive(node.slug) ? 'bg-muted font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'}"
							>
								<FileText class="h-3.5 w-3.5 shrink-0" />
								{node.title}
							</a>
						{/if}
					{/each}
				</nav>
			{/if}
		</div>
	</aside>

	<!-- Main content -->
	<main class="min-w-0 flex-1 p-6">
		{@render children()}
	</main>
</div>
