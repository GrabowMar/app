<script lang="ts">
import { page } from '$app/state';
import { goto } from '$app/navigation';
import { onMount } from 'svelte';
import * as Card from '$lib/components/ui/card';
import { Badge } from '$lib/components/ui/badge';
import { Button } from '$lib/components/ui/button';
import { Label } from '$lib/components/ui/label';
import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import Edit from '@lucide/svelte/icons/pencil';
import Copy from '@lucide/svelte/icons/copy';
import Play from '@lucide/svelte/icons/play';
import Trash2 from '@lucide/svelte/icons/trash-2';
import RefreshCw from '@lucide/svelte/icons/refresh-cw';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';
import ChevronLeft from '@lucide/svelte/icons/chevron-left';
import ChevronRight from '@lucide/svelte/icons/chevron-right';
import ArrowRight from '@lucide/svelte/icons/arrow-right';
import {
getPipeline,
deletePipeline,
clonePipeline,
triggerPipelineRun,
listPipelineRuns,
type PipelineDetail,
type PipelineRunListItem
} from '$lib/api/client';

const id = page.params.id;

let pipeline = $state<PipelineDetail | null>(null);
let runs = $state<PipelineRunListItem[]>([]);
let runsTotal = $state(0);
let runsPage = $state(1);
let runsPages = $state(1);
let loading = $state(true);
let error = $state('');

// Trigger run dialog
let showTrigger = $state(false);
let paramsText = $state('{}');
let triggerError = $state('');
let triggering = $state(false);

const statusColors: Record<string, string> = {
pending: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
succeeded: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
failed: 'bg-red-500/15 text-red-400 border-red-500/30',
cancelled: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
draft: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
active: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
archived: 'bg-orange-500/15 text-orange-400 border-orange-500/30'
};

const kindIcons: Record<string, string> = {
generate: '⚙️', analyze: '🔍', report: '��', wait: '⏳', notify: '🔔', script: '💻'
};

async function load() {
loading = true;
error = '';
try {
pipeline = await getPipeline(id);
const r = await listPipelineRuns(id, runsPage);
runs = r.items;
runsTotal = r.total;
runsPages = r.pages;
} catch (e) {
error = 'Failed to load pipeline';
} finally {
loading = false;
}
}

async function remove() {
if (!confirm('Delete this pipeline?')) return;
await deletePipeline(id);
goto('/automation');
}

async function clone() {
const newName = prompt('New name:', `${pipeline?.name} (copy)`);
if (!newName) return;
const p = await clonePipeline(id, newName);
goto(`/automation/${p.id}`);
}

async function triggerRun() {
triggerError = '';
let params: Record<string, unknown> = {};
try {
params = JSON.parse(paramsText);
} catch (e) {
triggerError = 'Invalid JSON params';
return;
}
triggering = true;
try {
const r = await triggerPipelineRun(id, params);
goto(`/automation/runs/${r.id}`);
} catch (e: unknown) {
const body = e as { detail?: string };
triggerError = body?.detail ?? 'Failed to trigger run';
} finally {
triggering = false;
}
}

function fmt(s: string | null) {
return s ? new Date(s).toLocaleString() : '—';
}

function duration(a: string | null, b: string | null) {
if (!a || !b) return null;
const ms = new Date(b).getTime() - new Date(a).getTime();
if (ms < 1000) return `${ms}ms`;
if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

onMount(load);
</script>

<svelte:head><title>{pipeline?.name ?? 'Pipeline'} — LLM Eval Lab</title></svelte:head>

<div class="container mx-auto p-6 space-y-6">
<div class="flex items-center justify-between">
<div class="flex items-center gap-3">
<Button variant="ghost" size="icon" onclick={() => goto('/automation')}>
<ArrowLeft class="h-4 w-4" />
</Button>
<h1 class="text-2xl font-bold tracking-tight">{pipeline?.name ?? 'Loading...'}</h1>
{#if pipeline}
<Badge class={statusColors[pipeline.status] ?? ''} variant="outline">{pipeline.status}</Badge>
{/if}
</div>
{#if pipeline}
<div class="flex gap-2 flex-wrap">
<Button variant="outline" size="sm" onclick={load}>
<RefreshCw class="mr-2 h-4 w-4" />Refresh
</Button>
<Button variant="outline" size="sm" onclick={() => goto(`/automation/${id}/edit`)}>
<Edit class="mr-2 h-4 w-4" />Edit
</Button>
<Button variant="outline" size="sm" onclick={clone}>
<Copy class="mr-2 h-4 w-4" />Clone
</Button>
<Button size="sm" onclick={() => { showTrigger = true; }}>
<Play class="mr-2 h-4 w-4" />Run
</Button>
<Button variant="destructive" size="sm" onclick={remove}>
<Trash2 class="mr-2 h-4 w-4" />Delete
</Button>
</div>
{/if}
</div>

<!-- Trigger Run Dialog -->
{#if showTrigger}
<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onclick={(e) => { if (e.target === e.currentTarget) showTrigger = false; }}>
<div class="w-full max-w-md rounded-lg border bg-card shadow-lg p-6 space-y-4">
<h2 class="text-lg font-semibold">Trigger Pipeline Run</h2>
<div class="space-y-1">
<Label>Parameters (JSON)</Label>
<textarea
bind:value={paramsText}
rows={5}
class="w-full rounded-md border bg-background p-3 font-mono text-sm resize-y focus:outline-none focus:ring-2 focus:ring-ring"
></textarea>
{#if triggerError}<p class="text-sm text-destructive">{triggerError}</p>{/if}
</div>
<div class="flex justify-end gap-2">
<Button variant="outline" onclick={() => { showTrigger = false; triggerError = ''; }}>Cancel</Button>
<Button onclick={triggerRun} disabled={triggering}>
<Play class="mr-2 h-4 w-4" />{triggering ? 'Starting...' : 'Start Run'}
</Button>
</div>
</div>
</div>
{/if}

{#if loading}
<div class="flex justify-center py-12">
<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
</div>
{:else if error}
<p class="text-destructive">{error}</p>
{:else if pipeline}
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<Card.Root>
<Card.Header><Card.Title>Details</Card.Title></Card.Header>
<Card.Content class="space-y-2 text-sm">
<div class="flex justify-between"><span class="text-muted-foreground">Version</span><span>v{pipeline.version}</span></div>
<div class="flex justify-between"><span class="text-muted-foreground">Created</span><span>{fmt(pipeline.created_at)}</span></div>
<div class="flex justify-between"><span class="text-muted-foreground">Updated</span><span>{fmt(pipeline.updated_at)}</span></div>
{#if pipeline.description}
<p class="text-muted-foreground pt-2">{pipeline.description}</p>
{/if}
<div class="flex flex-wrap gap-1 pt-1">
{#each pipeline.tags as tag}<Badge variant="secondary" class="text-xs">{tag}</Badge>{/each}
</div>
</Card.Content>
</Card.Root>

<!-- Steps DAG / list -->
<Card.Root>
<Card.Header><Card.Title>Pipeline Steps ({pipeline.steps.length})</Card.Title></Card.Header>
<Card.Content>
{#if pipeline.steps.length === 0}
<p class="text-sm text-muted-foreground">No steps defined.</p>
{:else}
<div class="space-y-1">
{#each pipeline.steps.sort((a, b) => a.order - b.order) as step, idx}
<div class="flex items-start gap-2">
<div class="flex flex-col items-center shrink-0 pt-1">
<div class="flex h-5 w-5 items-center justify-center rounded-full bg-primary/15 text-primary text-xs font-medium">{idx + 1}</div>
{#if idx < pipeline.steps.length - 1}
<div class="w-px flex-1 bg-border mt-1 min-h-4"></div>
{/if}
</div>
<div class="flex-1 rounded-md border bg-muted/20 px-3 py-2 text-sm mb-1">
<div class="flex items-center justify-between gap-2">
<span class="font-medium">{kindIcons[step.kind] ?? '•'} {step.name}</span>
<Badge variant="outline" class="text-xs">{step.kind}</Badge>
</div>
{#if step.depends_on.length > 0}
<div class="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
<ArrowRight class="h-3 w-3" />
{step.depends_on.join(', ')}
</div>
{/if}
</div>
</div>
{/each}
</div>
{/if}
</Card.Content>
</Card.Root>
</div>

<!-- Runs history -->
<Card.Root>
<Card.Header>
<Card.Title>Run History ({runsTotal})</Card.Title>
</Card.Header>
<Card.Content>
{#if runs.length === 0}
<p class="text-sm text-muted-foreground">No runs yet. Click <strong>Run</strong> to trigger the pipeline.</p>
{:else}
<table class="w-full text-sm">
<thead class="border-b">
<tr class="text-left text-muted-foreground">
<th class="pb-2">Run ID</th>
<th class="pb-2">Status</th>
<th class="pb-2">Started</th>
<th class="pb-2">Duration</th>
</tr>
</thead>
<tbody class="divide-y">
{#each runs as r}
<tr class="hover:bg-muted/40 cursor-pointer" onclick={() => goto(`/automation/runs/${r.id}`)}>
<td class="py-2 font-mono text-xs">{r.id.slice(0, 8)}…</td>
<td class="py-2"><Badge class={statusColors[r.status] ?? ''} variant="outline">{r.status}</Badge></td>
<td class="py-2">{fmt(r.started_at)}</td>
<td class="py-2 text-muted-foreground">{duration(r.started_at, r.completed_at) ?? '—'}</td>
</tr>
{/each}
</tbody>
</table>
{#if runsPages > 1}
<div class="flex justify-center gap-2 pt-4">
<Button variant="outline" size="sm" disabled={runsPage <= 1} onclick={async () => { runsPage--; const r = await listPipelineRuns(id, runsPage); runs = r.items; runsTotal = r.total; runsPages = r.pages; }}>
<ChevronLeft class="h-4 w-4" />
</Button>
<span class="px-3 py-2 text-sm">Page {runsPage} / {runsPages}</span>
<Button variant="outline" size="sm" disabled={runsPage >= runsPages} onclick={async () => { runsPage++; const r = await listPipelineRuns(id, runsPage); runs = r.items; runsTotal = r.total; runsPages = r.pages; }}>
<ChevronRight class="h-4 w-4" />
</Button>
</div>
{/if}
{/if}
</Card.Content>
</Card.Root>
{/if}
</div>
