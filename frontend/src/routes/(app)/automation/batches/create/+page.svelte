<script lang="ts">
import { goto } from '$app/navigation';
import { onMount } from 'svelte';
import * as Card from '$lib/components/ui/card';
import { Button } from '$lib/components/ui/button';
import { Input } from '$lib/components/ui/input';
import { Textarea } from '$lib/components/ui/textarea';
import { Label } from '$lib/components/ui/label';
import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import { createBatch, listPipelines, type PipelineListItem } from '$lib/api/client';

let pipelines = $state<PipelineListItem[]>([]);
let pipelineId = $state('');
let name = $state('');
let description = $state('');
let matrixText = $state('{\n  "models": [],\n  "templates": []\n}');
let saving = $state(false);
let errors = $state<string[]>([]);
let parseError = $state('');

onMount(async () => {
const res = await listPipelines({ per_page: 100 });
pipelines = res.items;
if (pipelines.length > 0) pipelineId = pipelines[0].id;
});

async function save() {
parseError = '';
errors = [];
let matrix: Record<string, unknown>;
try {
matrix = JSON.parse(matrixText);
} catch (e) {
parseError = 'Invalid JSON: ' + (e as Error).message;
return;
}
if (!pipelineId) { errors = ['Select a pipeline']; return; }
if (!name.trim()) { errors = ['Name is required']; return; }
saving = true;
try {
const b = await createBatch({ pipeline_id: pipelineId, name, description, matrix });
goto(`/automation/batches/${b.id}`);
} catch (e: unknown) {
const body = e as { detail?: string };
errors = [body?.detail ?? 'Failed to create batch'];
} finally {
saving = false;
}
}
</script>

<svelte:head><title>New Batch — LLM Eval Lab</title></svelte:head>

<div class="container mx-auto p-6 max-w-2xl space-y-6">
<div class="flex items-center gap-3">
<Button variant="ghost" size="icon" onclick={() => goto('/automation/batches')}><ArrowLeft class="h-4 w-4" /></Button>
<h1 class="text-2xl font-bold tracking-tight">New Batch</h1>
</div>
<Card.Root>
<Card.Content class="pt-6 space-y-4">
<div class="space-y-1">
<Label for="pipeline">Pipeline *</Label>
<select id="pipeline" bind:value={pipelineId} class="w-full rounded-md border bg-background px-3 py-2 text-sm">
{#each pipelines as p}<option value={p.id}>{p.name}</option>{/each}
</select>
</div>
<div class="space-y-1">
<Label for="name">Batch Name *</Label>
<Input id="name" bind:value={name} placeholder="My Batch Run" />
</div>
<div class="space-y-1">
<Label for="desc">Description</Label>
<Textarea id="desc" bind:value={description} rows={2} />
</div>
<div class="space-y-1">
<Label for="matrix">Matrix Config (JSON)</Label>
<textarea id="matrix" bind:value={matrixText} rows={8} class="w-full rounded-md border bg-background p-3 font-mono text-sm resize-y focus:outline-none focus:ring-2 focus:ring-ring"></textarea>
{#if parseError}<p class="text-sm text-destructive">{parseError}</p>{/if}
</div>
{#if errors.length > 0}
<div class="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive space-y-1">
{#each errors as e}<p>{e}</p>{/each}
</div>
{/if}
<div class="flex justify-end gap-2 pt-2">
<Button variant="outline" onclick={() => goto('/automation/batches')}>Cancel</Button>
<Button onclick={save} disabled={saving}>{saving ? 'Creating...' : 'Create Batch'}</Button>
</div>
</Card.Content>
</Card.Root>
</div>
