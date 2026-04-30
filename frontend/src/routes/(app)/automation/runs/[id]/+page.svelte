<script lang="ts">
import { page } from '$app/state';
import { goto } from '$app/navigation';
import { onMount } from 'svelte';
import * as Card from '$lib/components/ui/card';
import { Badge } from '$lib/components/ui/badge';
import { Button } from '$lib/components/ui/button';
import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import RefreshCw from '@lucide/svelte/icons/refresh-cw';
import XCircle from '@lucide/svelte/icons/x-circle';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';
import { getRun, cancelRun, type PipelineRunDetail } from '$lib/api/client';

const id = page.params.id;

let run = $state<PipelineRunDetail | null>(null);
let loading = $state(true);
let error = $state('');

const statusColors: Record<string, string> = {
pending: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
succeeded: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
failed: 'bg-red-500/15 text-red-400 border-red-500/30',
cancelled: 'bg-orange-500/15 text-orange-400 border-orange-500/30'
};

async function load() {
loading = true;
try {
run = await getRun(id);
error = '';
} catch (e) {
error = 'Failed to load run';
} finally {
loading = false;
}
}

async function cancel() {
if (!confirm('Cancel this run?')) return;
run = await cancelRun(id);
}

function fmt(s: string | null) {
return s ? new Date(s).toLocaleString() : '—';
}

onMount(load);
</script>

<svelte:head><title>Run Detail — LLM Eval Lab</title></svelte:head>

<div class="container mx-auto p-6 space-y-6">
<div class="flex items-center justify-between">
<div class="flex items-center gap-3">
<Button variant="ghost" size="icon" onclick={() => history.back()}>
<ArrowLeft class="h-4 w-4" />
</Button>
<h1 class="text-2xl font-bold tracking-tight">Run Detail</h1>
{#if run}
<Badge class={statusColors[run.status] ?? ''} variant="outline">{run.status}</Badge>
{/if}
</div>
<div class="flex gap-2">
<Button variant="outline" size="sm" onclick={load}><RefreshCw class="mr-2 h-4 w-4" />Refresh</Button>
{#if run && (run.status === 'pending' || run.status === 'running')}
<Button variant="destructive" size="sm" onclick={cancel}><XCircle class="mr-2 h-4 w-4" />Cancel</Button>
{/if}
</div>
</div>

{#if loading}
<div class="flex justify-center py-12">
<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
</div>
{:else if error}
<p class="text-destructive">{error}</p>
{:else if run}
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<Card.Root>
<Card.Header><Card.Title>Run Info</Card.Title></Card.Header>
<Card.Content class="space-y-2 text-sm">
<div class="flex justify-between"><span class="text-muted-foreground">Pipeline</span>
<button class="hover:underline font-mono text-xs" onclick={() => goto(`/automation/${run!.pipeline_id}`)}>{run.pipeline_id.slice(0, 8)}…</button>
</div>
<div class="flex justify-between"><span class="text-muted-foreground">Started</span><span>{fmt(run.started_at)}</span></div>
<div class="flex justify-between"><span class="text-muted-foreground">Completed</span><span>{fmt(run.completed_at)}</span></div>
<div class="flex justify-between"><span class="text-muted-foreground">Created</span><span>{fmt(run.created_at)}</span></div>
{#if run.error}
<div class="pt-2">
<p class="text-muted-foreground text-xs font-medium uppercase">Error</p>
<p class="text-destructive text-xs mt-1 font-mono">{run.error}</p>
</div>
{/if}
</Card.Content>
</Card.Root>

<Card.Root>
<Card.Header><Card.Title>Parameters</Card.Title></Card.Header>
<Card.Content>
<pre class="text-xs font-mono bg-muted/50 rounded p-2 overflow-auto max-h-40">{JSON.stringify(run.params, null, 2)}</pre>
</Card.Content>
</Card.Root>
</div>

<!-- Step Runs -->
<Card.Root>
<Card.Header><Card.Title>Step Runs ({run.step_runs.length})</Card.Title></Card.Header>
<Card.Content>
{#if run.step_runs.length === 0}
<p class="text-sm text-muted-foreground">No step runs recorded.</p>
{:else}
<table class="w-full text-sm">
<thead class="border-b">
<tr class="text-left text-muted-foreground">
<th class="pb-2">Step</th>
<th class="pb-2">Status</th>
<th class="pb-2">Attempt</th>
<th class="pb-2">Started</th>
<th class="pb-2">Completed</th>
<th class="pb-2">Error</th>
</tr>
</thead>
<tbody class="divide-y">
{#each run.step_runs as sr}
<tr>
<td class="py-2 font-mono text-xs">{sr.step_id?.slice(0, 8) ?? '—'}…</td>
<td class="py-2"><Badge class={statusColors[sr.status] ?? ''} variant="outline">{sr.status}</Badge></td>
<td class="py-2">{sr.attempt}</td>
<td class="py-2">{fmt(sr.started_at)}</td>
<td class="py-2">{fmt(sr.completed_at)}</td>
<td class="py-2 text-destructive text-xs">{sr.error || '—'}</td>
</tr>
{/each}
</tbody>
</table>
{/if}
</Card.Content>
</Card.Root>
{/if}
</div>
