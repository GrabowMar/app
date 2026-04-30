<script lang="ts">
import { page } from '$app/state';
import { goto } from '$app/navigation';
import { onMount } from 'svelte';
import * as Card from '$lib/components/ui/card';
import { Badge } from '$lib/components/ui/badge';
import { Button } from '$lib/components/ui/button';
import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';
import { getBatch, type BatchDetail } from '$lib/api/client';

const id = page.params.id;
let batch = $state<BatchDetail | null>(null);
let loading = $state(true);
let error = $state('');

const statusColors: Record<string, string> = {
pending: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
succeeded: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
failed: 'bg-red-500/15 text-red-400 border-red-500/30',
cancelled: 'bg-orange-500/15 text-orange-400 border-orange-500/30'
};

function fmt(s: string) { return new Date(s).toLocaleString(); }

onMount(async () => {
try {
batch = await getBatch(id);
} catch (e) {
error = 'Failed to load batch';
} finally {
loading = false;
}
});
</script>

<svelte:head><title>Batch — LLM Eval Lab</title></svelte:head>

<div class="container mx-auto p-6 space-y-6">
<div class="flex items-center gap-3">
<Button variant="ghost" size="icon" onclick={() => goto('/automation/batches')}><ArrowLeft class="h-4 w-4" /></Button>
<h1 class="text-2xl font-bold tracking-tight">{batch?.name ?? 'Batch'}</h1>
{#if batch}<Badge class={statusColors[batch.status] ?? ''} variant="outline">{batch.status}</Badge>{/if}
</div>

{#if loading}
<div class="flex justify-center py-12"><LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" /></div>
{:else if error}
<p class="text-destructive">{error}</p>
{:else if batch}
<Card.Root>
<Card.Header><Card.Title>Details</Card.Title></Card.Header>
<Card.Content class="space-y-2 text-sm">
<div class="flex justify-between"><span class="text-muted-foreground">Created</span><span>{fmt(batch.created_at)}</span></div>
{#if batch.description}<p class="text-muted-foreground">{batch.description}</p>{/if}
<pre class="text-xs font-mono bg-muted/50 rounded p-2 overflow-auto max-h-40">{JSON.stringify(batch.config, null, 2)}</pre>
</Card.Content>
</Card.Root>
<Card.Root>
<Card.Header><Card.Title>Items ({batch.items.length})</Card.Title></Card.Header>
<Card.Content>
{#if batch.items.length === 0}
<p class="text-sm text-muted-foreground">No items.</p>
{:else}
<table class="w-full text-sm">
<thead class="border-b"><tr class="text-left text-muted-foreground">
<th class="pb-2">Item ID</th><th class="pb-2">Status</th><th class="pb-2">Run</th><th class="pb-2">Created</th>
</tr></thead>
<tbody class="divide-y">
{#each batch.items as item}
<tr>
<td class="py-2 font-mono text-xs">{item.id.slice(0, 8)}…</td>
<td class="py-2"><Badge class={statusColors[item.status] ?? ''} variant="outline">{item.status}</Badge></td>
<td class="py-2">
{#if item.pipeline_run_id}
<button class="hover:underline text-xs font-mono" onclick={() => goto(`/automation/runs/${item.pipeline_run_id}`)}>{item.pipeline_run_id.slice(0, 8)}…</button>
{:else}—{/if}
</td>
<td class="py-2">{fmt(item.created_at)}</td>
</tr>
{/each}
</tbody>
</table>
{/if}
</Card.Content>
</Card.Root>
{/if}
</div>
