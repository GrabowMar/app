<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import {
		getModels,
		getModelsStats,
		getProviders,
		syncModelsFromOpenRouter,
		type LLMModelSummary,
		type PaginatedModels,
		type ModelsStats,
	} from '$lib/api/client';
	import { onMount } from 'svelte';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Search from '@lucide/svelte/icons/search';
	import GitCompareArrows from '@lucide/svelte/icons/git-compare-arrows';
	import CloudDownload from '@lucide/svelte/icons/cloud-download';
	import Download from '@lucide/svelte/icons/download';
	import Upload from '@lucide/svelte/icons/upload';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import Trophy from '@lucide/svelte/icons/trophy';
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';

	let searchQuery = $state('');
	let selectedProvider = $state('');
	let selectedModels = $state<Set<string>>(new Set());
	let currentPage = $state(1);
	let perPage = $state(50);

	let data = $state<PaginatedModels | null>(null);
	let stats = $state<ModelsStats | null>(null);
	let providers = $state<string[]>([]);
	let loading = $state(true);
	let syncing = $state(false);
	let error = $state('');

	let debounceTimer: ReturnType<typeof setTimeout>;

	async function load() {
		loading = true;
		error = '';
		try {
			data = await getModels({
				page: currentPage,
				per_page: perPage,
				search: searchQuery,
				provider: selectedProvider,
			});
		} catch {
			error = 'Failed to load models.';
		} finally {
			loading = false;
		}
	}

	async function loadMeta() {
		const [s, p] = await Promise.all([getModelsStats(), getProviders()]);
		stats = s;
		providers = p;
	}

	function debouncedLoad() {
		clearTimeout(debounceTimer);
		currentPage = 1;
		debounceTimer = setTimeout(load, 300);
	}

	async function handleSync() {
		syncing = true;
		try {
			const result = await syncModelsFromOpenRouter();
			await Promise.all([load(), loadMeta()]);
			alert(`Synced ${result.upserted} of ${result.fetched} models from OpenRouter.`);
		} catch {
			alert('Sync failed. Check backend logs.');
		} finally {
			syncing = false;
		}
	}

	function toggleModel(slug: string) {
		const next = new Set(selectedModels);
		if (next.has(slug)) next.delete(slug); else next.add(slug);
		selectedModels = next;
	}

	function goToPage(p: number) {
		currentPage = p;
		load();
	}

	function formatPrice(price: number): string {
		if (price === 0) return 'Free';
		if (price < 0.01) return `$${price.toFixed(4)}`;
		return `$${price.toFixed(2)}`;
	}

	onMount(() => {
		load();
		loadMeta();
	});
</script>

<svelte:head>
	<title>Models - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="page-header">
			<h1>Models</h1>
			<p>Browse and manage AI models available for research.</p>
		</div>
		<div class="flex items-center gap-2">
			<Button variant="outline" size="sm" href="/rankings">
				<Trophy class="mr-2 h-3.5 w-3.5" />
				Rankings
			</Button>
			<Button variant="outline" size="sm" href="/models/import">
				<Upload class="mr-2 h-3.5 w-3.5" />
				Import
			</Button>
		</div>
	</div>

	<!-- Stats -->
	{#if stats}
		<div class="flex flex-wrap items-center gap-2">
			<Badge variant="secondary" class="gap-1.5">
				<Cpu class="h-3 w-3" />
				{stats.total} models
			</Badge>
			<Badge variant="secondary" class="gap-1.5">
				<CircleCheck class="h-3 w-3 text-emerald-500" />
				{stats.free} free
			</Badge>
			<Badge variant="outline">{stats.providers} providers</Badge>
			<Badge variant="outline">Avg ${stats.avg_input_price.toFixed(2)}/1M input</Badge>
		</div>
	{/if}

	<!-- Filters & Actions -->
	<div class="flex flex-wrap items-center gap-3">
		<div class="relative flex-1 max-w-sm">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<Input
				placeholder="Search models..."
				class="pl-9"
				bind:value={searchQuery}
				oninput={debouncedLoad}
			/>
		</div>
		<select
			class="h-9 rounded-md border border-input bg-background px-3 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
			bind:value={selectedProvider}
			onchange={() => { currentPage = 1; load(); }}
		>
			<option value="">All Providers</option>
			{#each providers as p}
				<option value={p}>{p}</option>
			{/each}
		</select>
		<div class="ml-auto flex items-center gap-2">
			{#if selectedModels.size >= 2}
				<Button size="sm" href="/models/compare?models={[...selectedModels].join(',')}">
					<GitCompareArrows class="mr-2 h-3.5 w-3.5" />
					Compare ({selectedModels.size})
				</Button>
			{/if}
			<Button variant="outline" size="sm" onclick={handleSync} disabled={syncing}>
				{#if syncing}
					<LoaderCircle class="mr-2 h-3.5 w-3.5 animate-spin" />
					Syncing…
				{:else}
					<CloudDownload class="mr-2 h-3.5 w-3.5" />
					Sync from OpenRouter
				{/if}
			</Button>
			<Button variant="outline" size="sm" disabled>
				<Download class="mr-2 h-3.5 w-3.5" />
				Export JSON
			</Button>
		</div>
	</div>

	<!-- Error -->
	{#if error}
		<div class="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
			{error}
		</div>
	{/if}

	<!-- Models Table -->
	<Card.Root>
		<Card.Content class="p-0">
			{#if loading}
				<div class="flex items-center justify-center py-20">
					<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
				</div>
			{:else if data && data.items.length > 0}
				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground w-10">
									<input type="checkbox" class="rounded" disabled />
								</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Provider</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Context</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Input $/1M</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Output $/1M</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Capabilities</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each data.items as model (model.canonical_slug)}
								<tr class="transition-colors hover:bg-muted/30 {selectedModels.has(model.canonical_slug) ? 'bg-primary/5' : ''}">
									<td class="px-4 py-3">
										<input
											type="checkbox"
											class="rounded"
											checked={selectedModels.has(model.canonical_slug)}
											onchange={() => toggleModel(model.canonical_slug)}
										/>
									</td>
									<td class="px-4 py-3">
										<a href="/models/{model.canonical_slug}" class="flex items-center gap-2.5 group/link">
											<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-muted group-hover/link:bg-primary/10 transition-colors">
												<Cpu class="h-3.5 w-3.5 text-muted-foreground group-hover/link:text-primary transition-colors" />
											</div>
											<div class="min-w-0">
												<span class="text-sm font-medium group-hover/link:text-primary transition-colors block truncate max-w-[260px]">{model.model_name}</span>
											</div>
										</a>
									</td>
									<td class="px-4 py-3">
										<span class="text-sm text-muted-foreground">{model.provider}</span>
									</td>
									<td class="px-4 py-3">
										<span class="text-sm font-mono">{model.context_window_display}</span>
									</td>
									<td class="px-4 py-3">
										<span class="text-sm font-mono">{formatPrice(model.input_price_per_million)}</span>
									</td>
									<td class="px-4 py-3">
										<span class="text-sm font-mono">{formatPrice(model.output_price_per_million)}</span>
									</td>
									<td class="px-4 py-3">
										<div class="flex flex-wrap gap-1">
											{#each model.capabilities.slice(0, 4) as cap}
												<Badge variant="outline" class="text-[10px] px-1.5 py-0">{cap}</Badge>
											{/each}
											{#if model.capabilities.length > 4}
												<Badge variant="outline" class="text-[10px] px-1.5 py-0">+{model.capabilities.length - 4}</Badge>
											{/if}
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="flex flex-col items-center justify-center py-20 gap-3">
					<Cpu class="h-10 w-10 text-muted-foreground/40" />
					<p class="text-sm text-muted-foreground">No models found. Click "Sync from OpenRouter" to load models.</p>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<!-- Pagination -->
	{#if data && data.pages > 1}
		<div class="flex items-center justify-between">
			<p class="text-sm text-muted-foreground">
				Showing {(data.page - 1) * data.per_page + 1}–{Math.min(data.page * data.per_page, data.total)} of {data.total} models
			</p>
			<div class="flex items-center gap-1">
				<Button variant="outline" size="icon" class="h-8 w-8" disabled={data.page <= 1} onclick={() => goToPage(data!.page - 1)}>
					<ChevronLeft class="h-4 w-4" />
				</Button>
				{#each Array.from({length: Math.min(data.pages, 7)}, (_, i) => {
					if (data!.pages <= 7) return i + 1;
					if (data!.page <= 4) return i + 1;
					if (data!.page >= data!.pages - 3) return data!.pages - 6 + i;
					return data!.page - 3 + i;
				}) as p}
					<Button
						variant={p === data.page ? 'default' : 'outline'}
						size="sm"
						class="h-8 min-w-8"
						onclick={() => goToPage(p)}
					>
						{p}
					</Button>
				{/each}
				<Button variant="outline" size="icon" class="h-8 w-8" disabled={data.page >= data.pages} onclick={() => goToPage(data!.page + 1)}>
					<ChevronRight class="h-4 w-4" />
				</Button>
			</div>
		</div>
	{:else if data}
		<p class="text-sm text-muted-foreground">Showing {data.total} model{data.total !== 1 ? 's' : ''}</p>
	{/if}
</div>
