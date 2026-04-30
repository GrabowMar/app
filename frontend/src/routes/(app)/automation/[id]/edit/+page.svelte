<script lang="ts">
import { page } from '$app/state';
import { goto } from '$app/navigation';
import { onMount } from 'svelte';
import * as Card from '$lib/components/ui/card';
import { Button } from '$lib/components/ui/button';
import { Input } from '$lib/components/ui/input';
import { Textarea } from '$lib/components/ui/textarea';
import { Label } from '$lib/components/ui/label';
import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';
import Code from '@lucide/svelte/icons/code-2';
import Wand from '@lucide/svelte/icons/wand-sparkles';
import { getPipeline, updatePipeline } from '$lib/api/client';
import PipelineBuilder from '$lib/components/automation/PipelineBuilder.svelte';

const id = page.params.id;

let name = $state('');
let description = $state('');
let status = $state('draft');
let tags = $state('');
let loading = $state(true);
let saving = $state(false);
let errors = $state<string[]>([]);
let showJson = $state(false);
let config = $state<Record<string, unknown>>({ steps: [] });
let dslText = $state('');
let parseError = $state('');

onMount(async () => {
	try {
		const p = await getPipeline(id);
		name = p.name;
		description = p.description;
		status = p.status;
		config = p.config ?? { steps: [] };
		dslText = JSON.stringify(config, null, 2);
		tags = p.tags.join(', ');
	} finally {
		loading = false;
	}
});

function onJsonChange(text: string) {
	dslText = text;
	parseError = '';
	try {
		config = JSON.parse(text);
	} catch (e) {
		parseError = 'Invalid JSON: ' + (e as Error).message;
	}
}

async function save() {
	parseError = '';
	errors = [];
	if (showJson) {
		try { config = JSON.parse(dslText); } catch (e) { parseError = 'Invalid JSON: ' + (e as Error).message; return; }
	}
	saving = true;
	try {
		await updatePipeline(id, {
			name,
			description,
			status,
			config,
			tags: tags.split(',').map((t) => t.trim()).filter(Boolean)
		});
		goto(`/automation/${id}`);
	} catch (e: unknown) {
		const body = e as { errors?: string[]; detail?: string };
		errors = body?.errors ?? [body?.detail ?? 'Failed to save'];
	} finally {
		saving = false;
	}
}
</script>

<svelte:head><title>Edit Pipeline — LLM Eval Lab</title></svelte:head>

<div class="container mx-auto p-6 max-w-3xl space-y-6">
	<div class="flex items-center gap-3">
		<Button variant="ghost" size="icon" onclick={() => goto(`/automation/${id}`)}>
			<ArrowLeft class="h-4 w-4" />
		</Button>
		<h1 class="text-2xl font-bold tracking-tight">Edit Pipeline</h1>
	</div>

	{#if loading}
		<div class="flex justify-center py-12">
			<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
		</div>
	{:else}
		<Card.Root>
			<Card.Content class="pt-6 space-y-4">
				<div class="grid grid-cols-2 gap-4">
					<div class="space-y-1 col-span-2 md:col-span-1">
						<Label for="name">Name *</Label>
						<Input id="name" bind:value={name} />
					</div>
					<div class="space-y-1">
						<Label for="status">Status</Label>
						<select id="status" bind:value={status} class="w-full rounded-md border bg-background px-3 py-2 text-sm">
							<option value="draft">Draft</option>
							<option value="active">Active</option>
							<option value="archived">Archived</option>
						</select>
					</div>
				</div>
				<div class="space-y-1">
					<Label for="desc">Description</Label>
					<Textarea id="desc" bind:value={description} rows={2} />
				</div>
				<div class="space-y-1">
					<Label for="tags">Tags</Label>
					<Input id="tags" bind:value={tags} placeholder="ci, nightly" />
				</div>

				<!-- Builder / JSON toggle -->
				<div class="space-y-2">
					<div class="flex items-center justify-between">
						<Label>Steps</Label>
						<Button variant="ghost" size="sm" class="text-xs gap-1.5" onclick={() => { showJson = !showJson; if (!showJson) { try { config = JSON.parse(dslText); } catch { /* keep */ } } }}>
							{#if showJson}<Wand class="h-3.5 w-3.5" />Visual Builder{:else}<Code class="h-3.5 w-3.5" />Show JSON{/if}
						</Button>
					</div>

					{#if showJson}
						<div class="space-y-1">
							<textarea
								value={dslText}
								oninput={(e) => onJsonChange((e.target as HTMLTextAreaElement).value)}
								rows={14}
								class="w-full rounded-md border bg-background p-3 font-mono text-sm resize-y focus:outline-none focus:ring-2 focus:ring-ring"
							></textarea>
							{#if parseError}<p class="text-sm text-destructive">{parseError}</p>{/if}
						</div>
					{:else}
						<PipelineBuilder bind:value={config} bind:errors />
					{/if}
				</div>

				{#if errors.length > 0}
					<div class="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive space-y-1">
						{#each errors as e}<p>{e}</p>{/each}
					</div>
				{/if}

				<div class="flex justify-end gap-2 pt-2">
					<Button variant="outline" onclick={() => goto(`/automation/${id}`)}>Cancel</Button>
					<Button onclick={save} disabled={saving}>{saving ? 'Saving...' : 'Save Changes'}</Button>
				</div>
			</Card.Content>
		</Card.Root>
	{/if}
</div>
