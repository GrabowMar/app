<script lang="ts">
import { goto } from '$app/navigation';
import * as Card from '$lib/components/ui/card';
import { Button } from '$lib/components/ui/button';
import { Input } from '$lib/components/ui/input';
import { Textarea } from '$lib/components/ui/textarea';
import { Label } from '$lib/components/ui/label';
import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import { createPipeline } from '$lib/api/client';

let name = $state('');
let description = $state('');
let status = $state('draft');
let dslText = $state('{\n  "steps": []\n}');
let tags = $state('');
let saving = $state(false);
let errors = $state<string[]>([]);
let parseError = $state('');

async function save() {
parseError = '';
errors = [];
let config: Record<string, unknown>;
try {
config = JSON.parse(dslText);
} catch (e) {
parseError = 'Invalid JSON: ' + (e as Error).message;
return;
}
if (!name.trim()) {
errors = ['Name is required'];
return;
}
saving = true;
try {
const p = await createPipeline({
name: name.trim(),
description,
status,
config,
tags: tags.split(',').map((t) => t.trim()).filter(Boolean)
});
goto(`/automation/${p.id}`);
} catch (e: unknown) {
const body = e as { errors?: string[]; detail?: string };
errors = body?.errors ?? [body?.detail ?? 'Failed to create pipeline'];
} finally {
saving = false;
}
}
</script>

<svelte:head><title>New Pipeline — LLM Eval Lab</title></svelte:head>

<div class="container mx-auto p-6 max-w-2xl space-y-6">
<div class="flex items-center gap-3">
<Button variant="ghost" size="icon" onclick={() => goto('/automation')}>
<ArrowLeft class="h-4 w-4" />
</Button>
<h1 class="text-2xl font-bold tracking-tight">New Pipeline</h1>
</div>

<Card.Root>
<Card.Content class="pt-6 space-y-4">
<div class="space-y-1">
<Label for="name">Name *</Label>
<Input id="name" bind:value={name} placeholder="My Pipeline" />
</div>
<div class="space-y-1">
<Label for="desc">Description</Label>
<Textarea id="desc" bind:value={description} rows={2} placeholder="What does this pipeline do?" />
</div>
<div class="space-y-1">
<Label for="status">Status</Label>
<select id="status" bind:value={status} class="w-full rounded-md border bg-background px-3 py-2 text-sm">
<option value="draft">Draft</option>
<option value="active">Active</option>
<option value="archived">Archived</option>
</select>
</div>
<div class="space-y-1">
<Label for="tags">Tags (comma-separated)</Label>
<Input id="tags" bind:value={tags} placeholder="ci, nightly, prod" />
</div>
<div class="space-y-1">
<Label for="dsl">Pipeline DSL (JSON)</Label>
<textarea
id="dsl"
bind:value={dslText}
rows={14}
class="w-full rounded-md border bg-background p-3 font-mono text-sm resize-y focus:outline-none focus:ring-2 focus:ring-ring"
></textarea>
{#if parseError}
<p class="text-sm text-destructive">{parseError}</p>
{/if}
</div>

{#if errors.length > 0}
<div class="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive space-y-1">
{#each errors as e}<p>{e}</p>{/each}
</div>
{/if}

<div class="flex justify-end gap-2 pt-2">
<Button variant="outline" onclick={() => goto('/automation')}>Cancel</Button>
<Button onclick={save} disabled={saving}>{saving ? 'Saving...' : 'Create Pipeline'}</Button>
</div>
</Card.Content>
</Card.Root>
</div>
