<script lang="ts">
import { onMount } from 'svelte';
import { goto } from '$app/navigation';
import * as Card from '$lib/components/ui/card';
import { Badge } from '$lib/components/ui/badge';
import { Button } from '$lib/components/ui/button';
import { Input } from '$lib/components/ui/input';
import Plus from '@lucide/svelte/icons/plus';
import Eye from '@lucide/svelte/icons/eye';
import Edit from '@lucide/svelte/icons/pencil';
import Copy from '@lucide/svelte/icons/copy';
import Trash2 from '@lucide/svelte/icons/trash-2';
import Play from '@lucide/svelte/icons/play';
import RefreshCw from '@lucide/svelte/icons/refresh-cw';
import Calendar from '@lucide/svelte/icons/calendar';
import Layers from '@lucide/svelte/icons/layers';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';
import ChevronLeft from '@lucide/svelte/icons/chevron-left';
import ChevronRight from '@lucide/svelte/icons/chevron-right';
import {
listPipelines,
deletePipeline,
clonePipeline,
triggerPipelineRun,
type PipelineListItem
} from '$lib/api/client';

let pipelines = $state<PipelineListItem[]>([]);
let total = $state(0);
let page = $state(1);
let pages = $state(1);
let loading = $state(true);
let error = $state('');
let search = $state('');
let statusFilter = $state('');

const statusColors: Record<string, string> = {
draft: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
active: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
archived: 'bg-orange-500/15 text-orange-400 border-orange-500/30'
};

async function load() {
loading = true;
error = '';
try {
const res = await listPipelines({
page,
per_page: 20,
search: search || undefined,
status: statusFilter || undefined
});
pipelines = res.items;
total = res.total;
pages = res.pages;
} catch (e) {
error = (e as Error)?.message || 'Failed to load pipelines';
} finally {
loading = false;
}
}

async function remove(id: string) {
if (!confirm('Delete this pipeline?')) return;
try {
await deletePipeline(id);
await load();
} catch (e) {
alert('Failed to delete pipeline');
}
}

async function clone(id: string, name: string) {
const newName = prompt('New pipeline name:', `${name} (copy)`);
if (!newName) return;
try {
const p = await clonePipeline(id, newName);
goto(`/automation/${p.id}`);
} catch (e) {
alert('Failed to clone pipeline');
}
}

async function run(id: string) {
if (!confirm('Trigger a new run?')) return;
try {
const r = await triggerPipelineRun(id);
goto(`/automation/runs/${r.id}`);
} catch (e) {
alert('Failed to trigger run');
}
}

function formatDate(s: string) {
return new Date(s).toLocaleDateString();
}

$effect(() => {
void search;
void statusFilter;
page = 1;
load();
});

onMount(load);
</script>

<svelte:head>
<title>Automation — LLM Eval Lab</title>
</svelte:head>

<div class="container mx-auto p-6 space-y-6">
<div class="flex items-center justify-between">
<div>
<h1 class="text-2xl font-bold tracking-tight">Automation Pipelines</h1>
<p class="text-sm text-muted-foreground">{total} pipeline{total !== 1 ? 's' : ''}</p>
</div>
<div class="flex gap-2">
<Button variant="outline" size="sm" onclick={() => goto('/automation/batches')}>
<Layers class="mr-2 h-4 w-4" />Batches
</Button>
<Button variant="outline" size="sm" onclick={() => goto('/automation/schedules')}>
<Calendar class="mr-2 h-4 w-4" />Schedules
</Button>
<Button variant="outline" size="sm" onclick={load}>
<RefreshCw class="mr-2 h-4 w-4" />Refresh
</Button>
<Button size="sm" onclick={() => goto('/automation/create')}>
<Plus class="mr-2 h-4 w-4" />New Pipeline
</Button>
</div>
</div>

<!-- Filters -->
<div class="flex gap-3">
<Input placeholder="Search pipelines..." bind:value={search} class="max-w-xs" />
<select
bind:value={statusFilter}
class="rounded-md border bg-background px-3 py-2 text-sm"
>
<option value="">All statuses</option>
<option value="draft">Draft</option>
<option value="active">Active</option>
<option value="archived">Archived</option>
</select>
</div>

{#if loading}
<div class="flex justify-center py-12">
<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
</div>
{:else if error}
<Card.Root>
<Card.Content class="pt-6 text-center text-destructive">{error}</Card.Content>
</Card.Root>
{:else if pipelines.length === 0}
<Card.Root>
<Card.Content class="pt-6 text-center text-muted-foreground">
No pipelines found.
<Button variant="link" onclick={() => goto('/automation/create')}>Create one</Button>
</Card.Content>
</Card.Root>
{:else}
<Card.Root>
<div class="overflow-x-auto">
<table class="w-full text-sm">
<thead class="border-b">
<tr class="text-left text-muted-foreground">
<th class="px-4 py-3 font-medium">Name</th>
<th class="px-4 py-3 font-medium">Status</th>
<th class="px-4 py-3 font-medium">Version</th>
<th class="px-4 py-3 font-medium">Tags</th>
<th class="px-4 py-3 font-medium">Updated</th>
<th class="px-4 py-3 font-medium">Actions</th>
</tr>
</thead>
<tbody class="divide-y">
{#each pipelines as p}
<tr class="hover:bg-muted/40">
<td class="px-4 py-3 font-medium">
<button
class="text-left hover:underline"
onclick={() => goto(`/automation/${p.id}`)}
>{p.name}</button>
</td>
<td class="px-4 py-3">
<Badge class={statusColors[p.status] ?? ''} variant="outline">{p.status}</Badge>
</td>
<td class="px-4 py-3 text-muted-foreground">v{p.version}</td>
<td class="px-4 py-3">
<div class="flex flex-wrap gap-1">
{#each p.tags as tag}
<Badge variant="secondary" class="text-xs">{tag}</Badge>
{/each}
</div>
</td>
<td class="px-4 py-3 text-muted-foreground">{formatDate(p.updated_at)}</td>
<td class="px-4 py-3">
<div class="flex gap-1">
<Button size="icon" variant="ghost" onclick={() => goto(`/automation/${p.id}`)}>
<Eye class="h-4 w-4" />
</Button>
<Button size="icon" variant="ghost" onclick={() => goto(`/automation/${p.id}/edit`)}>
<Edit class="h-4 w-4" />
</Button>
<Button size="icon" variant="ghost" onclick={() => clone(p.id, p.name)}>
<Copy class="h-4 w-4" />
</Button>
<Button size="icon" variant="ghost" onclick={() => run(p.id)}>
<Play class="h-4 w-4" />
</Button>
<Button size="icon" variant="ghost" class="text-destructive" onclick={() => remove(p.id)}>
<Trash2 class="h-4 w-4" />
</Button>
</div>
</td>
</tr>
{/each}
</tbody>
</table>
</div>
</Card.Root>

<!-- Pagination -->
{#if pages > 1}
<div class="flex justify-center gap-2">
<Button variant="outline" size="sm" disabled={page <= 1} onclick={() => { page--; load(); }}>
<ChevronLeft class="h-4 w-4" />
</Button>
<span class="px-3 py-2 text-sm">Page {page} / {pages}</span>
<Button variant="outline" size="sm" disabled={page >= pages} onclick={() => { page++; load(); }}>
<ChevronRight class="h-4 w-4" />
</Button>
</div>
{/if}
{/if}
</div>
