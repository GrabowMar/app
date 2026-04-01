<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Separator } from '$lib/components/ui/separator';
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
	import ChevronsLeft from '@lucide/svelte/icons/chevrons-left';
	import ChevronsRight from '@lucide/svelte/icons/chevrons-right';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import ArrowUpDown from '@lucide/svelte/icons/arrow-up-down';
	import ArrowUp from '@lucide/svelte/icons/arrow-up';
	import ArrowDown from '@lucide/svelte/icons/arrow-down';
	import SlidersHorizontal from '@lucide/svelte/icons/sliders-horizontal';
	import X from '@lucide/svelte/icons/x';
	import Eye from '@lucide/svelte/icons/eye';
	import Wrench from '@lucide/svelte/icons/wrench';
	import Radio from '@lucide/svelte/icons/radio';
	import Braces from '@lucide/svelte/icons/braces';
	import Gift from '@lucide/svelte/icons/gift';

	let searchQuery = $state('');
	let selectedProvider = $state('');
	let selectedModels = $state<Set<string>>(new Set());
	let currentPage = $state(1);
	let perPage = $state(50);
	let sortBy = $state('');
	let sortDir = $state<'asc' | 'desc'>('asc');
	let filtersOpen = $state(false);

	// Advanced filters
	let filterCapability = $state('');
	let filterPriceRange = $state('');
	let filterContextRange = $state('');
	let filterFreeOnly = $state(false);

	let data = $state<PaginatedModels | null>(null);
	let stats = $state<ModelsStats | null>(null);
	let providers = $state<string[]>([]);
	let loading = $state(true);
	let syncing = $state(false);
	let error = $state('');

	let debounceTimer: ReturnType<typeof setTimeout>;

	const activeFilterCount = $derived(
		(filterCapability ? 1 : 0) +
		(filterPriceRange ? 1 : 0) +
		(filterContextRange ? 1 : 0) +
		(filterFreeOnly ? 1 : 0)
	);

	async function load() {
		loading = true;
		error = '';
		try {
			data = await getModels({
				page: currentPage,
				per_page: perPage,
				search: searchQuery,
				provider: selectedProvider,
				capability: filterCapability,
				free_only: filterFreeOnly,
				sort_by: sortBy,
				sort_dir: sortDir,
				price_range: filterPriceRange,
				context_range: filterContextRange,
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

	function applyFilterAndReload() {
		currentPage = 1;
		load();
	}

	function clearAllFilters() {
		filterCapability = '';
		filterPriceRange = '';
		filterContextRange = '';
		filterFreeOnly = false;
		selectedProvider = '';
		searchQuery = '';
		sortBy = '';
		sortDir = 'asc';
		currentPage = 1;
		load();
	}

	function toggleSort(field: string) {
		if (sortBy === field) {
			sortDir = sortDir === 'asc' ? 'desc' : 'asc';
		} else {
			sortBy = field;
			sortDir = 'asc';
		}
		currentPage = 1;
		load();
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

	function efficiencyGrade(score: number): { grade: string; color: string; bg: string } {
		if (score >= 0.9) return { grade: 'A+', color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-500/10' };
		if (score >= 0.8) return { grade: 'A', color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-500/10' };
		if (score >= 0.7) return { grade: 'A-', color: 'text-emerald-500', bg: 'bg-emerald-500/10' };
		if (score >= 0.6) return { grade: 'B+', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-500/10' };
		if (score >= 0.5) return { grade: 'B', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-500/10' };
		if (score >= 0.4) return { grade: 'B-', color: 'text-blue-500', bg: 'bg-blue-500/10' };
		if (score >= 0.3) return { grade: 'C+', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-500/10' };
		if (score >= 0.2) return { grade: 'C', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-500/10' };
		return { grade: 'D', color: 'text-red-500', bg: 'bg-red-500/10' };
	}

	function capBadgeClass(cap: string): string {
		const map: Record<string, string> = {
			'Vision': 'border-violet-500/40 text-violet-600 dark:text-violet-400',
			'Function Calling': 'border-orange-500/40 text-orange-600 dark:text-orange-400',
			'JSON Mode': 'border-blue-500/40 text-blue-600 dark:text-blue-400',
			'Streaming': 'border-emerald-500/40 text-emerald-600 dark:text-emerald-400',
			'Code': 'border-slate-500/40 text-slate-600 dark:text-slate-400',
		};
		return map[cap] ?? '';
	}

	function formatTokens(n: number): string {
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
		return String(n);
	}

	const capabilityOptions = [
		{ value: 'vision', label: 'Vision', icon: Eye },
		{ value: 'function_calling', label: 'Functions', icon: Wrench },
		{ value: 'streaming', label: 'Streaming', icon: Radio },
		{ value: 'json_mode', label: 'JSON Mode', icon: Braces },
	] as const;

	const priceRangeOptions = [
		{ value: 'free', label: 'Free', icon: Gift },
		{ value: 'low', label: '<$1/1M' },
		{ value: 'medium', label: '$1–$10/1M' },
		{ value: 'high', label: '>$10/1M' },
	] as const;

	const contextRangeOptions = [
		{ value: 'small', label: '<8K' },
		{ value: 'medium', label: '8K–32K' },
		{ value: 'large', label: '32K–128K' },
		{ value: 'xlarge', label: '>128K' },
	] as const;

	type SortableColumn = {
		key: string;
		label: string;
		sortField: string;
		align?: 'left' | 'right';
	};

	const sortableColumns: SortableColumn[] = [
		{ key: 'model', label: 'Model', sortField: 'model_name' },
		{ key: 'provider', label: 'Provider', sortField: 'provider' },
		{ key: 'context', label: 'Context', sortField: 'context_window', align: 'right' },
		{ key: 'max_output', label: 'Max Output', sortField: 'max_output', align: 'right' },
		{ key: 'input_price', label: 'Input $/1M', sortField: 'input_price', align: 'right' },
		{ key: 'output_price', label: 'Output $/1M', sortField: 'output_price', align: 'right' },
		{ key: 'efficiency', label: 'Efficiency', sortField: 'cost_efficiency', align: 'right' },
	];

	onMount(() => {
		load();
		loadMeta();
	});
</script>

<svelte:head>
	<title>Models - LLM Lab</title>
</svelte:head>

<div class="space-y-4">
	<!-- Header -->
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

	<!-- Search, Provider, Filters Toggle, Actions -->
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
			onchange={() => applyFilterAndReload()}
		>
			<option value="">All Providers</option>
			{#each providers as p}
				<option value={p}>{p}</option>
			{/each}
		</select>
		<Button
			variant={filtersOpen || activeFilterCount > 0 ? 'default' : 'outline'}
			size="sm"
			onclick={() => filtersOpen = !filtersOpen}
		>
			<SlidersHorizontal class="mr-2 h-3.5 w-3.5" />
			Filters
			{#if activeFilterCount > 0}
				<Badge variant="secondary" class="ml-1.5 h-5 min-w-5 px-1 text-[10px]">{activeFilterCount}</Badge>
			{/if}
		</Button>
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

	<!-- Advanced Filters Panel -->
	{#if filtersOpen}
		<Card.Root>
			<Card.Content class="py-4">
				<div class="space-y-4">
					<!-- Capabilities -->
					<div>
						<span class="text-xs font-semibold uppercase text-muted-foreground mb-2 block">Capabilities</span>
						<div class="flex flex-wrap gap-2">
							{#each capabilityOptions as opt}
								<button
									class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors
										{filterCapability === opt.value
											? 'bg-primary text-primary-foreground border-primary'
											: 'border-input hover:bg-muted'}"
									onclick={() => { filterCapability = filterCapability === opt.value ? '' : opt.value; applyFilterAndReload(); }}
								>
									<opt.icon class="h-3 w-3" />
									{opt.label}
								</button>
							{/each}
						</div>
					</div>

					<Separator />

					<div class="grid gap-4 sm:grid-cols-2">
						<!-- Price Range -->
						<div>
							<span class="text-xs font-semibold uppercase text-muted-foreground mb-2 block">Price Range</span>
							<div class="flex flex-wrap gap-2">
								{#each priceRangeOptions as opt}
									<button
										class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors
											{filterPriceRange === opt.value
												? 'bg-primary text-primary-foreground border-primary'
												: 'border-input hover:bg-muted'}"
										onclick={() => { filterPriceRange = filterPriceRange === opt.value ? '' : opt.value; applyFilterAndReload(); }}
									>
										{opt.label}
									</button>
								{/each}
							</div>
						</div>

						<!-- Context Range -->
						<div>
							<span class="text-xs font-semibold uppercase text-muted-foreground mb-2 block">Context Window</span>
							<div class="flex flex-wrap gap-2">
								{#each contextRangeOptions as opt}
									<button
										class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors
											{filterContextRange === opt.value
												? 'bg-primary text-primary-foreground border-primary'
												: 'border-input hover:bg-muted'}"
										onclick={() => { filterContextRange = filterContextRange === opt.value ? '' : opt.value; applyFilterAndReload(); }}
									>
										{opt.label}
									</button>
								{/each}
							</div>
						</div>
					</div>

					{#if activeFilterCount > 0}
						<div class="flex justify-end">
							<Button variant="ghost" size="sm" onclick={clearAllFilters}>
								<X class="mr-1.5 h-3 w-3" />
								Clear all filters
							</Button>
						</div>
					{/if}
				</div>
			</Card.Content>
		</Card.Root>
	{/if}

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
								<th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground w-10">
									<input type="checkbox" class="rounded" disabled />
								</th>
								{#each sortableColumns as col}
									<th class="px-3 py-3 text-{col.align ?? 'left'} text-xs font-medium text-muted-foreground">
										<button
											class="inline-flex items-center gap-1 hover:text-foreground transition-colors"
											onclick={() => toggleSort(col.sortField)}
										>
											{col.label}
											{#if sortBy === col.sortField}
												{#if sortDir === 'asc'}
													<ArrowUp class="h-3 w-3 text-primary" />
												{:else}
													<ArrowDown class="h-3 w-3 text-primary" />
												{/if}
											{:else}
												<ArrowUpDown class="h-3 w-3 opacity-30" />
											{/if}
										</button>
									</th>
								{/each}
								<th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">Capabilities</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each data.items as model (model.canonical_slug)}
								<tr class="transition-colors hover:bg-muted/40 cursor-pointer
									{selectedModels.has(model.canonical_slug) ? 'bg-primary/5' : ''}
									{model.is_free ? 'bg-emerald-500/[0.03]' : ''}">
									<td class="px-3 py-2.5">
										<input
											type="checkbox"
											class="rounded"
											checked={selectedModels.has(model.canonical_slug)}
											onchange={() => toggleModel(model.canonical_slug)}
										/>
									</td>
									<td class="px-3 py-2.5">
										<a href="/models/{model.canonical_slug}" class="flex items-center gap-2 group/link">
											<div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted group-hover/link:bg-primary/10 transition-colors">
												<Cpu class="h-3.5 w-3.5 text-muted-foreground group-hover/link:text-primary transition-colors" />
											</div>
											<div class="min-w-0">
												<span class="text-sm font-medium group-hover/link:text-primary transition-colors block truncate max-w-[240px]" title={model.model_name}>{model.model_name}</span>
												{#if model.is_free}
													<span class="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">FREE</span>
												{/if}
											</div>
										</a>
									</td>
									<td class="px-3 py-2.5">
										<span class="text-sm text-muted-foreground">{model.provider}</span>
									</td>
									<td class="px-3 py-2.5 text-right">
										<span class="text-sm font-mono">{model.context_window_display}</span>
									</td>
									<td class="px-3 py-2.5 text-right">
										<span class="text-sm font-mono text-muted-foreground">{formatTokens(model.max_output_tokens)}</span>
									</td>
									<td class="px-3 py-2.5 text-right">
										<span class="text-sm font-mono {model.input_price_per_million === 0 ? 'text-emerald-600 dark:text-emerald-400' : ''}">{formatPrice(model.input_price_per_million)}</span>
									</td>
									<td class="px-3 py-2.5 text-right">
										<span class="text-sm font-mono {model.output_price_per_million === 0 ? 'text-emerald-600 dark:text-emerald-400' : ''}">{formatPrice(model.output_price_per_million)}</span>
									</td>
									<td class="px-3 py-2.5 text-right">
										{#if model.cost_efficiency > 0}
											{@const eff = efficiencyGrade(model.cost_efficiency)}
											<Badge variant="outline" class="text-[10px] px-1.5 py-0 font-bold {eff.color} {eff.bg} border-0">{eff.grade}</Badge>
										{:else}
											<span class="text-xs text-muted-foreground">—</span>
										{/if}
									</td>
									<td class="px-3 py-2.5">
										<div class="flex flex-wrap gap-1">
											{#each model.capabilities.slice(0, 3) as cap}
												<Badge variant="outline" class="text-[10px] px-1.5 py-0 {capBadgeClass(cap)}">{cap}</Badge>
											{/each}
											{#if model.capabilities.length > 3}
												<Badge variant="outline" class="text-[10px] px-1.5 py-0 text-muted-foreground">+{model.capabilities.length - 3}</Badge>
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
	{#if data && data.total > 0}
		<div class="flex flex-wrap items-center justify-between gap-4">
			<div class="flex items-center gap-3">
				<p class="text-sm text-muted-foreground whitespace-nowrap">
					Showing {(data.page - 1) * data.per_page + 1}–{Math.min(data.page * data.per_page, data.total)} of {data.total}
				</p>
				<select
					class="h-8 rounded-md border border-input bg-background px-2 text-xs ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
					bind:value={perPage}
					onchange={() => { currentPage = 1; load(); }}
				>
					<option value={25}>25 / page</option>
					<option value={50}>50 / page</option>
					<option value={100}>100 / page</option>
				</select>
			</div>
			{#if data.pages > 1}
				<div class="flex items-center gap-1">
					<Button variant="outline" size="icon" class="h-8 w-8" disabled={data.page <= 1} onclick={() => goToPage(1)}>
						<ChevronsLeft class="h-4 w-4" />
					</Button>
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
					<Button variant="outline" size="icon" class="h-8 w-8" disabled={data.page >= data.pages} onclick={() => goToPage(data!.pages)}>
						<ChevronsRight class="h-4 w-4" />
					</Button>
				</div>
			{/if}
		</div>
	{/if}
</div>
