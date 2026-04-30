<script lang="ts">
import { onMount } from 'svelte';
import { goto } from '$app/navigation';
import * as Card from '$lib/components/ui/card';
import { Badge } from '$lib/components/ui/badge';
import { Button } from '$lib/components/ui/button';
import { Input } from '$lib/components/ui/input';
import { Label } from '$lib/components/ui/label';
import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import Plus from '@lucide/svelte/icons/plus';
import Trash2 from '@lucide/svelte/icons/trash-2';
import RefreshCw from '@lucide/svelte/icons/refresh-cw';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';
import {
listSchedules,
createSchedule,
setScheduleEnabled,
deleteSchedule,
listPipelines,
type ScheduleSummary,
type PipelineListItem
} from '$lib/api/client';

let schedules = $state<ScheduleSummary[]>([]);
let total = $state(0);
let loading = $state(true);
let error = $state('');
let showForm = $state(false);
let pipelines = $state<PipelineListItem[]>([]);
let newPipelineId = $state('');
let newCron = $state('0 * * * *');
let newEnabled = $state(true);
let saving = $state(false);
let formError = $state('');

async function load() {
loading = true;
try {
const res = await listSchedules();
schedules = res.items;
total = res.total;
error = '';
} catch (e) {
error = 'Failed to load schedules';
} finally {
loading = false;
}
}

async function loadPipelines() {
const res = await listPipelines({ per_page: 100 });
pipelines = res.items;
if (pipelines.length > 0) newPipelineId = pipelines[0].id;
}

async function create() {
if (!newPipelineId) { formError = 'Select a pipeline'; return; }
saving = true;
formError = '';
try {
await createSchedule({ pipeline_id: newPipelineId, cron_expression: newCron, enabled: newEnabled });
showForm = false;
await load();
} catch (e: unknown) {
const body = e as { errors?: string[]; detail?: string };
formError = body?.errors?.[0] ?? body?.detail ?? 'Failed to create schedule';
} finally {
saving = false;
}
}

async function toggle(sched: ScheduleSummary) {
await setScheduleEnabled(sched.id, !sched.enabled);
await load();
}

async function remove(id: string) {
if (!confirm('Delete this schedule?')) return;
await deleteSchedule(id);
await load();
}

function fmt(s: string | null) { return s ? new Date(s).toLocaleString() : '—'; }

onMount(() => {
load();
loadPipelines();
});
</script>

<svelte:head><title>Schedules — LLM Eval Lab</title></svelte:head>

<div class="container mx-auto p-6 space-y-6">
<div class="flex items-center justify-between">
<div class="flex items-center gap-3">
<Button variant="ghost" size="icon" onclick={() => goto('/automation')}><ArrowLeft class="h-4 w-4" /></Button>
<div>
<h1 class="text-2xl font-bold tracking-tight">Schedules</h1>
<p class="text-sm text-muted-foreground">{total} schedule{total !== 1 ? 's' : ''}</p>
</div>
</div>
<div class="flex gap-2">
<Button variant="outline" size="sm" onclick={load}><RefreshCw class="mr-2 h-4 w-4" />Refresh</Button>
<Button size="sm" onclick={() => showForm = !showForm}><Plus class="mr-2 h-4 w-4" />New Schedule</Button>
</div>
</div>

{#if showForm}
<Card.Root>
<Card.Header><Card.Title>New Schedule</Card.Title></Card.Header>
<Card.Content class="space-y-4">
<div class="space-y-1">
<Label>Pipeline</Label>
<select bind:value={newPipelineId} class="w-full rounded-md border bg-background px-3 py-2 text-sm">
{#each pipelines as p}<option value={p.id}>{p.name}</option>{/each}
</select>
</div>
<div class="space-y-1">
<Label>Cron Expression</Label>
<Input bind:value={newCron} placeholder="0 * * * *" />
<p class="text-xs text-muted-foreground">Standard 5-field cron (minute hour day month weekday)</p>
</div>
<div class="flex items-center gap-2">
<input type="checkbox" id="enabled" bind:checked={newEnabled} />
<Label for="enabled">Enabled</Label>
</div>
{#if formError}<p class="text-sm text-destructive">{formError}</p>{/if}
<div class="flex justify-end gap-2">
<Button variant="outline" onclick={() => showForm = false}>Cancel</Button>
<Button onclick={create} disabled={saving}>{saving ? 'Creating...' : 'Create'}</Button>
</div>
</Card.Content>
</Card.Root>
{/if}

{#if loading}
<div class="flex justify-center py-12"><LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" /></div>
{:else if error}
<p class="text-destructive">{error}</p>
{:else if schedules.length === 0}
<Card.Root>
<Card.Content class="pt-6 text-center text-muted-foreground">No schedules yet.</Card.Content>
</Card.Root>
{:else}
<Card.Root>
<div class="overflow-x-auto">
<table class="w-full text-sm">
<thead class="border-b">
<tr class="text-left text-muted-foreground">
<th class="px-4 py-3 font-medium">Pipeline</th>
<th class="px-4 py-3 font-medium">Cron</th>
<th class="px-4 py-3 font-medium">Enabled</th>
<th class="px-4 py-3 font-medium">Next Run</th>
<th class="px-4 py-3 font-medium">Last Run</th>
<th class="px-4 py-3 font-medium">Actions</th>
</tr>
</thead>
<tbody class="divide-y">
{#each schedules as sched}
<tr class="hover:bg-muted/40">
<td class="px-4 py-3 font-mono text-xs">{sched.pipeline_id.slice(0, 8)}…</td>
<td class="px-4 py-3 font-mono">{sched.cron_expression}</td>
<td class="px-4 py-3">
<button
class="rounded-full px-3 py-1 text-xs font-medium border {sched.enabled ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30' : 'bg-slate-500/15 text-slate-400 border-slate-500/30'}"
onclick={() => toggle(sched)}
>{sched.enabled ? 'On' : 'Off'}</button>
</td>
<td class="px-4 py-3 text-muted-foreground">{fmt(sched.next_run_at)}</td>
<td class="px-4 py-3 text-muted-foreground">{fmt(sched.last_run_at)}</td>
<td class="px-4 py-3">
<Button size="icon" variant="ghost" class="text-destructive" onclick={() => remove(sched.id)}>
<Trash2 class="h-4 w-4" />
</Button>
</td>
</tr>
{/each}
</tbody>
</table>
</div>
</Card.Root>
{/if}
</div>
