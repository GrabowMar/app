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
import X from '@lucide/svelte/icons/x';
import Eye from '@lucide/svelte/icons/eye';
import Wrench from '@lucide/svelte/icons/wrench';
import Radio from '@lucide/svelte/icons/radio';
import Braces from '@lucide/svelte/icons/braces';
import Gift from '@lucide/svelte/icons/gift';
import Sparkles from '@lucide/svelte/icons/sparkles';
import Zap from '@lucide/svelte/icons/zap';

let searchQuery = $state('');
let selectedProvider = $state('');
let currentPage = $state(1);
let perPage = $state(50);
let sortBy = $state('');
let sortDir = $state<'asc' | 'desc'>('asc');

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

// Active filters as removable tags
const activeFilters = $derived(() => {
const tags: { key: string; label: string; clear: () => void }[] = [];
if (filterCapability) {
const capLabels: Record<string, string> = { vision: 'Vision', function_calling: 'Functions', streaming: 'Streaming', json_mode: 'JSON Mode' };
tags.push({ key: 'cap', label: capLabels[filterCapability] ?? filterCapability, clear: () => { filterCapability = ''; applyFilterAndReload(); } });
}
if (filterPriceRange) {
const priceLabels: Record<string, string> = { free: 'Free', low: '<$1/1M', medium: '$1–$10/1M', high: '>$10/1M' };
tags.push({ key: 'price', label: priceLabels[filterPriceRange] ?? filterPriceRange, clear: () => { filterPriceRange = ''; applyFilterAndReload(); } });
}
if (filterContextRange) {
const ctxLabels: Record<string, string> = { small: '<8K ctx', medium: '8K–32K ctx', large: '32K–128K ctx', xlarge: '>128K ctx' };
tags.push({ key: 'ctx', label: ctxLabels[filterContextRange] ?? filterContextRange, clear: () => { filterContextRange = ''; applyFilterAndReload(); } });
}
if (filterFreeOnly) {
tags.push({ key: 'free', label: 'Free only', clear: () => { filterFreeOnly = false; applyFilterAndReload(); } });
}
if (selectedProvider) {
tags.push({ key: 'provider', label: `Provider: ${selectedProvider}`, clear: () => { selectedProvider = ''; applyFilterAndReload(); } });
}
return tags;
});

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

function resetFilterState() {
filterCapability = '';
filterPriceRange = '';
filterContextRange = '';
filterFreeOnly = false;
selectedProvider = '';
searchQuery = '';
sortBy = '';
sortDir = 'asc';
currentPage = 1;
}

function clearAllFilters() {
resetFilterState();
load();
}

function applyQuickFilter(type: string) {
resetFilterState();
if (type === 'free') { filterPriceRange = 'free'; }
else if (type === 'vision') { filterCapability = 'vision'; }
else if (type === 'large-context') { filterContextRange = 'xlarge'; }
else if (type === 'efficient') { sortBy = 'cost_efficiency'; sortDir = 'desc'; }
else if (type === 'functions') { filterCapability = 'function_calling'; }
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

function goToPage(p: number) {
currentPage = p;
load();
}

function formatPrice(price: number): string {
if (price === 0) return 'Free';
if (price < 0) return '—';
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

function formatTokens(n: number): string {
if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
return String(n);
}

// Capability icons - compact display
const capIconMap: Record<string, { icon: typeof Eye; color: string; label: string }> = {
'Vision': { icon: Eye, color: 'text-violet-500', label: 'Vision' },
'Function Calling': { icon: Wrench, color: 'text-orange-500', label: 'Function Calling' },
'JSON Mode': { icon: Braces, color: 'text-blue-500', label: 'JSON Mode' },
'Streaming': { icon: Radio, color: 'text-emerald-500', label: 'Streaming' },
'Code': { icon: Zap, color: 'text-slate-500', label: 'Code' },
};

const capabilityOptions = [
{ value: 'vision', label: 'Vision', icon: Eye },
{ value: 'function_calling', label: 'Functions', icon: Wrench },
{ value: 'streaming', label: 'Streaming', icon: Radio },
{ value: 'json_mode', label: 'JSON Mode', icon: Braces },
] as const;

const priceRangeOptions = [
{ value: 'free', label: 'Free' },
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
{ key: 'max_output', label: 'Max Out', sortField: 'max_output', align: 'right' },
{ key: 'input_price', label: 'In $/1M', sortField: 'input_price', align: 'right' },
{ key: 'output_price', label: 'Out $/1M', sortField: 'output_price', align: 'right' },
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

<div class="space-y-3">
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

<!-- Stats Bar -->
{#if stats}
<div class="flex flex-wrap items-center gap-2 text-xs">
<Badge variant="secondary" class="gap-1.5">
<Cpu class="h-3 w-3" />
{stats.total} models
</Badge>
<Badge variant="secondary" class="gap-1.5 text-emerald-600 dark:text-emerald-400">
<Gift class="h-3 w-3" />
{stats.free} free
</Badge>
<Badge variant="outline">{stats.providers} providers</Badge>
{#if stats.avg_input_price > 0}
<Badge variant="outline">Avg ${stats.avg_input_price.toFixed(2)}/1M input</Badge>
{/if}
</div>
{/if}

<!-- Quick Filter Presets -->
<div class="flex flex-wrap items-center gap-1.5">
<span class="text-xs text-muted-foreground mr-1">Quick:</span>
<button
class="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors hover:bg-muted {filterPriceRange === 'free' ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-700 dark:text-emerald-400' : 'border-input'}"
onclick={() => applyQuickFilter('free')}
>
<Gift class="h-3 w-3" /> Free Models
</button>
<button
class="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors hover:bg-muted {filterCapability === 'vision' ? 'bg-violet-500/10 border-violet-500/40 text-violet-700 dark:text-violet-400' : 'border-input'}"
onclick={() => applyQuickFilter('vision')}
>
<Eye class="h-3 w-3" /> Vision
</button>
<button
class="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors hover:bg-muted {filterCapability === 'function_calling' ? 'bg-orange-500/10 border-orange-500/40 text-orange-700 dark:text-orange-400' : 'border-input'}"
onclick={() => applyQuickFilter('functions')}
>
<Wrench class="h-3 w-3" /> Functions
</button>
<button
class="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors hover:bg-muted {filterContextRange === 'xlarge' ? 'bg-blue-500/10 border-blue-500/40 text-blue-700 dark:text-blue-400' : 'border-input'}"
onclick={() => applyQuickFilter('large-context')}
>
128K+ Context
</button>
<button
class="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors hover:bg-muted {sortBy === 'cost_efficiency' && sortDir === 'desc' ? 'bg-amber-500/10 border-amber-500/40 text-amber-700 dark:text-amber-400' : 'border-input'}"
onclick={() => applyQuickFilter('efficient')}
>
<Sparkles class="h-3 w-3" /> Most Efficient
</button>
</div>

<!-- Search + Provider + Actions Row -->
<div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
<div class="relative w-full sm:flex-1 sm:max-w-sm">
<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
<Input
placeholder="Search models..."
class="pl-9"
bind:value={searchQuery}
oninput={debouncedLoad}
/>
</div>
<select
class="h-9 w-full sm:w-auto rounded-md border border-input bg-background px-3 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
bind:value={selectedProvider}
onchange={() => applyFilterAndReload()}
>
<option value="">All Providers</option>
{#each providers as p}
<option value={p}>{p}</option>
{/each}
</select>
<div class="flex items-center gap-2 sm:ml-auto">
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
Export
</Button>
</div>
</div>

<!-- Advanced Filters Row (inline, not a panel) -->
<div class="flex flex-wrap items-center gap-x-6 gap-y-2">
<!-- Capabilities -->
<div class="flex items-center gap-2">
<span class="text-xs font-semibold uppercase text-muted-foreground">Cap:</span>
{#each capabilityOptions as opt}
<button
class="inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium transition-colors
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
<Separator orientation="vertical" class="h-5 hidden sm:block" />
<!-- Price Range -->
<div class="flex items-center gap-2">
<span class="text-xs font-semibold uppercase text-muted-foreground">Price:</span>
{#each priceRangeOptions as opt}
<button
class="rounded-md border px-2 py-0.5 text-xs font-medium transition-colors
{filterPriceRange === opt.value
? 'bg-primary text-primary-foreground border-primary'
: 'border-input hover:bg-muted'}"
onclick={() => { filterPriceRange = filterPriceRange === opt.value ? '' : opt.value; applyFilterAndReload(); }}
>
{opt.label}
</button>
{/each}
</div>
<Separator orientation="vertical" class="h-5 hidden sm:block" />
<!-- Context Range -->
<div class="flex items-center gap-2">
<span class="text-xs font-semibold uppercase text-muted-foreground">Context:</span>
{#each contextRangeOptions as opt}
<button
class="rounded-md border px-2 py-0.5 text-xs font-medium transition-colors
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

<!-- Active Filter Tags -->
{#if activeFilters().length > 0}
<div class="flex flex-wrap items-center gap-1.5">
<span class="text-xs text-muted-foreground">Active:</span>
{#each activeFilters() as tag (tag.key)}
<Badge variant="secondary" class="gap-1 pr-1">
{tag.label}
<button class="ml-0.5 rounded-full hover:bg-muted-foreground/20 p-0.5" onclick={tag.clear}>
<X class="h-2.5 w-2.5" />
</button>
</Badge>
{/each}
<button class="text-xs text-muted-foreground hover:text-foreground underline ml-1" onclick={clearAllFilters}>Clear all</button>
</div>
{/if}

<!-- Error -->
{#if error}
<div class="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
{error}
</div>
{/if}

<!-- Results Count -->
{#if data && !loading}
<div class="flex items-center justify-between">
<p class="text-xs text-muted-foreground">
Showing {(data.page - 1) * data.per_page + 1}–{Math.min(data.page * data.per_page, data.total)} of <strong>{data.total}</strong> models
</p>
<select
class="h-7 rounded-md border border-input bg-background px-2 text-xs ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring"
bind:value={perPage}
onchange={() => { currentPage = 1; load(); }}
>
<option value={25}>25 / page</option>
<option value={50}>50 / page</option>
<option value={100}>100 / page</option>
</select>
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
<div class="hidden md:block overflow-x-auto">
<table class="w-full">
<thead>
<tr class="border-b bg-muted/40 sticky top-0 z-10">
{#each sortableColumns as col}
<th class="px-3 py-2.5 text-{col.align ?? 'left'} text-xs font-medium text-muted-foreground whitespace-nowrap">
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
<th class="px-3 py-2.5 text-center text-xs font-medium text-muted-foreground">Capabilities</th>
</tr>
</thead>
<tbody>
{#each data.items as model, i (model.canonical_slug)}
<tr class="border-b transition-colors hover:bg-muted/50 group
{i % 2 === 0 ? '' : 'bg-muted/15'}
{model.is_free ? 'bg-emerald-500/[0.03]' : ''}">
<!-- Model Name + Description -->
<td class="px-3 py-2">
<a href="/models/{model.canonical_slug}" class="flex items-center gap-2.5 group/link">
<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted group-hover/link:bg-primary/10 transition-colors">
<Cpu class="h-4 w-4 text-muted-foreground group-hover/link:text-primary transition-colors" />
</div>
<div class="min-w-0">
<span class="text-sm font-medium group-hover/link:text-primary transition-colors block truncate max-w-[280px]">{model.model_name}</span>
{#if model.description}
<span class="text-[11px] text-muted-foreground block truncate max-w-[280px]">{model.description}</span>
{:else if model.is_free}
<span class="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">FREE</span>
{/if}
</div>
</a>
</td>
<!-- Provider -->
<td class="px-3 py-2">
<Badge variant="outline" class="text-[10px] font-normal">{model.provider}</Badge>
</td>
<!-- Context -->
<td class="px-3 py-2 text-right">
<span class="text-sm font-mono tabular-nums">{model.context_window_display}</span>
</td>
<!-- Max Output -->
<td class="px-3 py-2 text-right">
<span class="text-sm font-mono tabular-nums text-muted-foreground">{model.max_output_tokens ? formatTokens(model.max_output_tokens) : '—'}</span>
</td>
<!-- Input Price -->
<td class="px-3 py-2 text-right">
<span class="text-sm font-mono tabular-nums {model.input_price_per_million === 0 ? 'text-emerald-600 dark:text-emerald-400 font-medium' : ''}">{formatPrice(model.input_price_per_million)}</span>
</td>
<!-- Output Price -->
<td class="px-3 py-2 text-right">
<span class="text-sm font-mono tabular-nums {model.output_price_per_million === 0 ? 'text-emerald-600 dark:text-emerald-400 font-medium' : ''}">{formatPrice(model.output_price_per_million)}</span>
</td>
<!-- Efficiency -->
<td class="px-3 py-2 text-right">
{#if model.cost_efficiency > 0}
{@const eff = efficiencyGrade(model.cost_efficiency)}
<span class="inline-flex items-center justify-center h-6 w-8 rounded text-[10px] font-bold {eff.color} {eff.bg}">{eff.grade}</span>
{:else}
<span class="text-xs text-muted-foreground">—</span>
{/if}
</td>
<!-- Capabilities as icons -->
<td class="px-3 py-2">
<div class="flex items-center justify-center gap-1">
{#each model.capabilities as cap}
{#if capIconMap[cap]}
{@const ci = capIconMap[cap]}
<span title={ci.label} class="inline-flex items-center justify-center h-5 w-5 rounded {ci.color} bg-muted/60">
<ci.icon class="h-3 w-3" />
</span>
{/if}
{/each}
{#if model.capabilities.length === 0}
<span class="text-xs text-muted-foreground">—</span>
{/if}
</div>
</td>
</tr>
{/each}
</tbody>
</table>
</div>
<!-- Mobile card view -->
<div class="md:hidden">
<div class="flex items-center gap-2 border-b px-3 py-2.5">
<span class="text-xs font-medium text-muted-foreground shrink-0">Sort:</span>
<select
class="h-8 flex-1 rounded-md border border-input bg-background px-2 text-xs ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring"
bind:value={sortBy}
onchange={() => { currentPage = 1; load(); }}
>
<option value="">Default</option>
{#each sortableColumns as col}
<option value={col.sortField}>{col.label}</option>
{/each}
</select>
<button
class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input bg-background transition-colors hover:bg-muted"
onclick={() => { sortDir = sortDir === 'asc' ? 'desc' : 'asc'; currentPage = 1; load(); }}
aria-label="Toggle sort direction"
>
{#if sortDir === 'asc'}
<ArrowUp class="h-3.5 w-3.5" />
{:else}
<ArrowDown class="h-3.5 w-3.5" />
{/if}
</button>
</div>
<div class="space-y-3 p-3">
{#each data.items as model (model.canonical_slug)}
<a href="/models/{model.canonical_slug}" class="block rounded-lg border bg-card p-3 transition-colors hover:bg-muted/50 active:bg-muted/70 {model.is_free ? 'border-emerald-500/30' : ''}">
<!-- Header: Name + Provider -->
<div class="flex items-start justify-between gap-2">
<div class="flex items-center gap-2 min-w-0 flex-1">
<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
<Cpu class="h-4 w-4 text-muted-foreground" />
</div>
<div class="min-w-0">
<span class="text-sm font-medium block truncate">{model.model_name}</span>
{#if model.description}
<span class="text-[11px] text-muted-foreground block truncate">{model.description}</span>
{/if}
</div>
</div>
<div class="flex items-center gap-1.5 shrink-0">
{#if model.is_free}
<Badge variant="secondary" class="text-[10px] text-emerald-600 dark:text-emerald-400">FREE</Badge>
{/if}
<Badge variant="outline" class="text-[10px] font-normal">{model.provider}</Badge>
</div>
</div>
<!-- Stats: 2-col grid -->
<div class="grid grid-cols-2 gap-x-4 gap-y-1.5 mt-2.5 text-xs">
<div class="flex justify-between">
<span class="text-muted-foreground">Context</span>
<span class="font-mono tabular-nums">{model.context_window_display}</span>
</div>
<div class="flex justify-between">
<span class="text-muted-foreground">Max Out</span>
<span class="font-mono tabular-nums text-muted-foreground">{model.max_output_tokens ? formatTokens(model.max_output_tokens) : '—'}</span>
</div>
<div class="flex justify-between">
<span class="text-muted-foreground">In $/1M</span>
<span class="font-mono tabular-nums {model.input_price_per_million === 0 ? 'text-emerald-600 dark:text-emerald-400 font-medium' : ''}">{formatPrice(model.input_price_per_million)}</span>
</div>
<div class="flex justify-between">
<span class="text-muted-foreground">Out $/1M</span>
<span class="font-mono tabular-nums {model.output_price_per_million === 0 ? 'text-emerald-600 dark:text-emerald-400 font-medium' : ''}">{formatPrice(model.output_price_per_million)}</span>
</div>
</div>
<!-- Capabilities + Efficiency -->
<div class="flex items-center justify-between mt-2.5 pt-2 border-t border-border/50">
<div class="flex flex-wrap gap-1">
{#each model.capabilities as cap}
{#if capIconMap[cap]}
{@const ci = capIconMap[cap]}
<span class="inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] {ci.color} bg-muted/60">
<ci.icon class="h-2.5 w-2.5" />
{ci.label}
</span>
{/if}
{/each}
{#if model.capabilities.length === 0}
<span class="text-[10px] text-muted-foreground">—</span>
{/if}
</div>
{#if model.cost_efficiency > 0}
{@const eff = efficiencyGrade(model.cost_efficiency)}
<span class="inline-flex items-center justify-center h-6 w-8 rounded text-[10px] font-bold {eff.color} {eff.bg}">{eff.grade}</span>
{/if}
</div>
</a>
{/each}
</div>
</div>
{:else}
<div class="flex flex-col items-center justify-center py-20 gap-3">
{#if activeFilters().length > 0}
<Search class="h-10 w-10 text-muted-foreground/40" />
<p class="text-sm text-muted-foreground">No models match your filters.</p>
<Button variant="outline" size="sm" onclick={clearAllFilters}>Clear all filters</Button>
{:else}
<Cpu class="h-10 w-10 text-muted-foreground/40" />
<p class="text-sm text-muted-foreground">No models found. Click "Sync from OpenRouter" to load models.</p>
{/if}
</div>
{/if}
</Card.Content>
</Card.Root>

<!-- Pagination -->
{#if data && data.pages > 1}
<div class="flex flex-wrap items-center justify-center gap-1.5 sm:gap-1">
<Button variant="outline" size="icon" class="h-11 w-11 sm:h-8 sm:w-8" disabled={data.page <= 1} onclick={() => goToPage(1)}>
<ChevronsLeft class="h-4 w-4" />
</Button>
<Button variant="outline" size="icon" class="h-11 w-11 sm:h-8 sm:w-8" disabled={data.page <= 1} onclick={() => goToPage(data!.page - 1)}>
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
class="h-11 min-w-11 sm:h-8 sm:min-w-8"
onclick={() => goToPage(p)}
>
{p}
</Button>
{/each}
<Button variant="outline" size="icon" class="h-11 w-11 sm:h-8 sm:w-8" disabled={data.page >= data.pages} onclick={() => goToPage(data!.page + 1)}>
<ChevronRight class="h-4 w-4" />
</Button>
<Button variant="outline" size="icon" class="h-11 w-11 sm:h-8 sm:w-8" disabled={data.page >= data.pages} onclick={() => goToPage(data!.pages)}>
<ChevronsRight class="h-4 w-4" />
</Button>
</div>
{/if}
</div>
