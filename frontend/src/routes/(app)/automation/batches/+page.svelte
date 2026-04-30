<script lang="ts">
import { onMount } from 'svelte';
import { goto } from '$app/navigation';
import * as Card from '$lib/components/ui/card';
import { Badge } from '$lib/components/ui/badge';
import { Button } from '$lib/components/ui/button';
import Plus from '@lucide/svelte/icons/plus';
import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import Eye from '@lucide/svelte/icons/eye';
import RefreshCw from '@lucide/svelte/icons/refresh-cw';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';
import ChevronLeft from '@lucide/svelte/icons/chevron-left';
import ChevronRight from '@lucide/svelte/icons/chevron-right';
import { listBatches, getBatch, type BatchSummary } from '$lib/api/client';

let batches = $state<BatchSummary[]>([]);
let total = $state(0);
let page = $state(1);
let pages = $state(1);
let loading = $state(true);
let error = $state('');

// Progress counts per batch
let progressMap = $state<Record<string, { succeeded: number; total: number }>>({});

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
		const res = await listBatches(page);
		batches = res.items;
		total = res.total;
		pages = res.pages;
		error = '';
		// Load item counts for progress bars
		for (const b of batches) {
			try {
				const detail = await getBatch(b.id);
				const total = detail.items.length;
				const succeeded = detail.items.filter((i) => i.status === 'succeeded').length;
				progressMap[b.id] = { succeeded, total };
			} catch { /* skip */ }
		}
	} catch (e) {
		error = 'Failed to load batches';
	} finally {
		loading = false;
	}
}

function fmt(s: string) { return new Date(s).toLocaleDateString(); }

onMount(load);
</script>

<svelte:head><title>Batches — LLM Eval Lab</title></svelte:head>

<div class="container mx-auto p-6 space-y-6">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-3">
			<Button variant="ghost" size="icon" onclick={() => goto('/automation')}>
				<ArrowLeft class="h-4 w-4" />
			</Button>
			<div>
				<h1 class="text-2xl font-bold tracking-tight">Batches</h1>
				<p class="text-sm text-muted-foreground">{total} batch{total !== 1 ? 'es' : ''}</p>
			</div>
		</div>
		<div class="flex gap-2">
			<Button variant="outline" size="sm" onclick={load}><RefreshCw class="mr-2 h-4 w-4" />Refresh</Button>
			<Button size="sm" onclick={() => goto('/automation/batches/create')}><Plus class="mr-2 h-4 w-4" />New Batch</Button>
		</div>
	</div>

	{#if loading}
		<div class="flex justify-center py-12"><LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" /></div>
	{:else if error}
		<p class="text-destructive">{error}</p>
	{:else if batches.length === 0}
		<Card.Root>
			<Card.Content class="pt-6 text-center text-muted-foreground">No batches yet.</Card.Content>
		</Card.Root>
	{:else}
		<Card.Root>
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead class="border-b">
						<tr class="text-left text-muted-foreground">
							<th class="px-4 py-3 font-medium">Name</th>
							<th class="px-4 py-3 font-medium">Status</th>
							<th class="px-4 py-3 font-medium">Progress</th>
							<th class="px-4 py-3 font-medium">Created</th>
							<th class="px-4 py-3 font-medium">Actions</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each batches as b}
							{@const prog = progressMap[b.id]}
							<tr class="hover:bg-muted/40">
								<td class="px-4 py-3 font-medium">{b.name}</td>
								<td class="px-4 py-3"><Badge class={statusColors[b.status] ?? ''} variant="outline">{b.status}</Badge></td>
								<td class="px-4 py-3 min-w-[140px]">
									{#if prog}
										<div class="space-y-0.5">
											<div class="h-1.5 w-full rounded-full bg-muted overflow-hidden">
												<div
													class="h-full rounded-full bg-emerald-500 transition-all"
													style="width: {prog.total > 0 ? (prog.succeeded / prog.total * 100).toFixed(0) : 0}%"
												></div>
											</div>
											<p class="text-xs text-muted-foreground">{prog.succeeded}/{prog.total} succeeded</p>
										</div>
									{:else}
										<span class="text-xs text-muted-foreground">—</span>
									{/if}
								</td>
								<td class="px-4 py-3 text-muted-foreground">{fmt(b.created_at)}</td>
								<td class="px-4 py-3">
									<Button size="icon" variant="ghost" onclick={() => goto(`/automation/batches/${b.id}`)}>
										<Eye class="h-4 w-4" />
									</Button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</Card.Root>
		{#if pages > 1}
			<div class="flex justify-center gap-2">
				<Button variant="outline" size="sm" disabled={page <= 1} onclick={() => { page--; load(); }}><ChevronLeft class="h-4 w-4" /></Button>
				<span class="px-3 py-2 text-sm">Page {page} / {pages}</span>
				<Button variant="outline" size="sm" disabled={page >= pages} onclick={() => { page++; load(); }}><ChevronRight class="h-4 w-4" /></Button>
			</div>
		{/if}
	{/if}
</div>
