<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import {
		getGenerationJobs,
		type GenerationJobList,
		type PaginatedJobs,
	} from '$lib/api/client';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Search from '@lucide/svelte/icons/search';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Eye from '@lucide/svelte/icons/eye';
	import Zap from '@lucide/svelte/icons/zap';
	import Layers from '@lucide/svelte/icons/layers';
	import Bot from '@lucide/svelte/icons/bot';
	import Pencil from '@lucide/svelte/icons/pencil';
	import AppWindow from '@lucide/svelte/icons/app-window';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleX from '@lucide/svelte/icons/circle-x';
	import Clock from '@lucide/svelte/icons/clock';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import ChevronsLeft from '@lucide/svelte/icons/chevrons-left';
	import ChevronsRight from '@lucide/svelte/icons/chevrons-right';
	import X from '@lucide/svelte/icons/x';
	import Copy from '@lucide/svelte/icons/copy';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import FlaskConical from '@lucide/svelte/icons/flask-conical';

	let loading = $state(true);
	let refreshing = $state(false);
	let data = $state<PaginatedJobs | null>(null);

	let searchQuery = $state('');
	let modeFilter = $state('');
	let statusFilter = $state('');
	let currentPage = $state(1);
	let perPage = $state(25);

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		failed: 'bg-red-500/15 text-red-400 border-red-500/30',
		running: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		pending: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
		cancelled: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const modeColors: Record<string, string> = {
		custom: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		scaffolding: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
		copilot: 'bg-teal-500/15 text-teal-400 border-teal-500/30',
	};

	async function fetchJobs() {
		try {
			const params: Record<string, any> = {
				page: currentPage,
				per_page: perPage,
			};
			if (modeFilter) params.mode = modeFilter;
			if (statusFilter) params.status = statusFilter;
			data = await getGenerationJobs(params);
		} catch (e: any) {
			toast.error('Failed to load applications');
		} finally {
			loading = false;
			refreshing = false;
		}
	}

	async function refresh() {
		refreshing = true;
		await fetchJobs();
		toast.success('Refreshed');
	}

	function goToPage(p: number) {
		currentPage = p;
		fetchJobs();
	}

	function applyFilters() {
		currentPage = 1;
		fetchJobs();
	}

	function clearFilters() {
		searchQuery = '';
		modeFilter = '';
		statusFilter = '';
		currentPage = 1;
		fetchJobs();
	}

	function formatDuration(seconds: number | null): string {
		if (seconds == null) return '—';
		if (seconds < 60) return `${seconds.toFixed(1)}s`;
		const m = Math.floor(seconds / 60);
		const s = Math.round(seconds % 60);
		return `${m}m ${s}s`;
	}

	function timeAgo(dateStr: string): string {
		const diff = Date.now() - new Date(dateStr).getTime();
		const mins = Math.floor(diff / 60000);
		if (mins < 1) return 'just now';
		if (mins < 60) return `${mins}m ago`;
		const hours = Math.floor(mins / 60);
		if (hours < 24) return `${hours}h ago`;
		const days = Math.floor(hours / 24);
		if (days < 30) return `${days}d ago`;
		return new Date(dateStr).toLocaleDateString();
	}

	function getDescription(job: GenerationJobList): string {
		if (job.template_name) return job.template_name;
		if (job.scaffolding_name) return job.scaffolding_name;
		return '—';
	}

	function copyId(id: string) {
		navigator.clipboard.writeText(id);
		toast.success('Copied job ID');
	}

	const filteredItems = $derived(
		data
			? searchQuery
				? data.items.filter(
						(j) =>
							(j.model_name ?? '').toLowerCase().includes(searchQuery.toLowerCase()) ||
							(j.template_name ?? '').toLowerCase().includes(searchQuery.toLowerCase()) ||
							(j.scaffolding_name ?? '').toLowerCase().includes(searchQuery.toLowerCase())
					)
				: data.items
			: []
	);

	const stats = $derived({
		total: data?.total ?? 0,
		completed: filteredItems.filter((j) => j.status === 'completed').length,
		failed: filteredItems.filter((j) => j.status === 'failed').length,
		models: new Set(filteredItems.map((j) => j.model_name).filter(Boolean)).size,
	});

	const hasFilters = $derived(modeFilter !== '' || statusFilter !== '' || searchQuery !== '');

	onMount(() => {
		fetchJobs();
	});
</script>

<svelte:head>
	<title>Applications - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="page-header">
			<h1>Applications</h1>
			<p>Generated web applications from LLM models.</p>
		</div>
		<div class="flex items-center gap-2">
			<Button variant="outline" size="sm" onclick={refresh} disabled={refreshing}>
				<RefreshCw class="mr-2 h-3.5 w-3.5 {refreshing ? 'animate-spin' : ''}" />
				Refresh
			</Button>
			<Button size="sm" href="/sample-generator">
				<FlaskConical class="mr-2 h-3.5 w-3.5" />
				Generate New
			</Button>
		</div>
	</div>

	<!-- Stats -->
	<div class="flex flex-wrap items-center gap-2">
		<Badge variant="outline" class="gap-1.5">
			<AppWindow class="h-3 w-3" />
			{stats.total} total
		</Badge>
		<Badge variant="outline" class="gap-1.5 border-emerald-500/30 text-emerald-500">
			<CircleCheck class="h-3 w-3" />
			{stats.completed} completed
		</Badge>
		{#if stats.failed > 0}
			<Badge variant="outline" class="gap-1.5 border-red-500/30 text-red-400">
				<CircleX class="h-3 w-3" />
				{stats.failed} failed
			</Badge>
		{/if}
		<Badge variant="outline" class="gap-1.5">
			{stats.models} models
		</Badge>
	</div>

	<!-- Filters -->
	<div class="flex flex-wrap items-center gap-3">
		<div class="relative flex-1 max-w-sm">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<input
				type="text"
				placeholder="Search by model or template..."
				class="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
				bind:value={searchQuery}
			/>
		</div>
		<select
			class="h-9 rounded-md border border-input bg-background px-3 text-sm"
			bind:value={modeFilter}
			onchange={applyFilters}
		>
			<option value="">All Modes</option>
			<option value="custom">Custom</option>
			<option value="scaffolding">Scaffolding</option>
			<option value="copilot">Copilot</option>
		</select>
		<select
			class="h-9 rounded-md border border-input bg-background px-3 text-sm"
			bind:value={statusFilter}
			onchange={applyFilters}
		>
			<option value="">All Statuses</option>
			<option value="completed">Completed</option>
			<option value="failed">Failed</option>
			<option value="running">Running</option>
			<option value="pending">Pending</option>
		</select>
		<select
			class="h-9 rounded-md border border-input bg-background px-3 text-sm"
			bind:value={perPage}
			onchange={applyFilters}
		>
			<option value={10}>10 / page</option>
			<option value={25}>25 / page</option>
			<option value={50}>50 / page</option>
			<option value={100}>100 / page</option>
		</select>
		{#if hasFilters}
			<Button variant="ghost" size="sm" onclick={clearFilters} class="gap-1.5">
				<X class="h-3.5 w-3.5" />
				Clear
			</Button>
		{/if}
	</div>

	<!-- Table -->
	{#if loading}
		<Card.Root>
			<Card.Content class="flex items-center justify-center py-20">
				<LoaderCircle class="h-6 w-6 animate-spin text-muted-foreground" />
				<span class="ml-2 text-sm text-muted-foreground">Loading applications...</span>
			</Card.Content>
		</Card.Root>
	{:else if filteredItems.length === 0}
		<Card.Root>
			<Card.Content class="py-16 text-center">
				<AppWindow class="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
				<h3 class="text-lg font-medium mb-1">No applications found</h3>
				<p class="text-sm text-muted-foreground mb-4">
					{hasFilters
						? 'No applications match your filters.'
						: 'Generate your first application using the Sample Generator.'}
				</p>
				{#if hasFilters}
					<Button variant="outline" size="sm" onclick={clearFilters}>Clear Filters</Button>
				{:else}
					<Button size="sm" href="/sample-generator">Go to Sample Generator</Button>
				{/if}
			</Card.Content>
		</Card.Root>
	{:else}
		<Card.Root>
			<Card.Content class="p-0">
				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Mode</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Template</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Duration</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Actions</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each filteredItems as job (job.id)}
								<tr class="transition-colors hover:bg-muted/30">
									<!-- Mode -->
									<td class="px-4 py-3">
										<Badge variant="outline" class="gap-1 text-[10px] {modeColors[job.mode] ?? ''}">
											{#if job.mode === 'custom'}
												<Pencil class="h-3 w-3" />
											{:else if job.mode === 'scaffolding'}
												<Layers class="h-3 w-3" />
											{:else if job.mode === 'copilot'}
												<Bot class="h-3 w-3" />
											{/if}
											{job.mode}
										</Badge>
									</td>

									<!-- Model -->
									<td class="px-4 py-3">
										<div class="flex flex-col gap-0.5">
											<span class="text-sm font-medium">{job.model_name ?? '—'}</span>
											<span class="text-xs text-muted-foreground font-mono">{job.model_id_str ?? ''}</span>
										</div>
									</td>

									<!-- Template -->
									<td class="px-4 py-3">
										<div class="flex flex-col gap-0.5">
											<span class="text-sm">{getDescription(job)}</span>
											{#if job.scaffolding_name && job.template_name}
												<span class="text-xs text-muted-foreground">{job.scaffolding_name}</span>
											{/if}
										</div>
									</td>

									<!-- Status -->
									<td class="px-4 py-3">
										<Badge variant="outline" class="text-[10px] {statusColors[job.status] ?? ''}">
											{#if job.status === 'running'}
												<span class="mr-1 h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse"></span>
											{/if}
											{#if job.status === 'completed'}
												<CircleCheck class="mr-1 h-3 w-3" />
											{:else if job.status === 'failed'}
												<CircleX class="mr-1 h-3 w-3" />
											{:else if job.status === 'pending'}
												<Clock class="mr-1 h-3 w-3" />
											{/if}
											{job.status}
										</Badge>
										{#if job.error_message}
											<div class="mt-1 flex items-center gap-1">
												<AlertTriangle class="h-3 w-3 text-red-400 shrink-0" />
												<span class="text-xs text-red-400 truncate max-w-[200px]">{job.error_message}</span>
											</div>
										{/if}
									</td>

									<!-- Duration -->
									<td class="px-4 py-3 text-sm font-mono text-muted-foreground">
										{formatDuration(job.duration_seconds)}
									</td>

									<!-- Created -->
									<td class="px-4 py-3">
										<div class="flex flex-col gap-0.5">
											<span class="text-sm text-muted-foreground">{timeAgo(job.created_at)}</span>
											<span class="text-xs text-muted-foreground/70">{new Date(job.created_at).toLocaleString()}</span>
										</div>
									</td>

									<!-- Actions -->
									<td class="px-4 py-3">
										<div class="flex items-center gap-1">
											<Button variant="ghost" size="sm" class="h-7 w-7 p-0" href="/applications/{job.id}" title="View details">
												<Eye class="h-3.5 w-3.5" />
											</Button>
											{#if job.status === 'failed'}
												<Button variant="ghost" size="sm" class="h-7 w-7 p-0" href="/applications/{job.id}/failure" title="Failure details">
													<AlertTriangle class="h-3.5 w-3.5 text-red-400" />
												</Button>
											{/if}
											<Button variant="ghost" size="sm" class="h-7 w-7 p-0" title="Copy ID" onclick={() => copyId(job.id)}>
												<Copy class="h-3.5 w-3.5" />
											</Button>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Pagination -->
		{#if data && data.pages > 1}
			<div class="flex items-center justify-between text-sm text-muted-foreground">
				<span>
					Page {data.page} of {data.pages} ({data.total} total)
				</span>
				<div class="flex items-center gap-1">
					<Button variant="outline" size="sm" disabled={data.page <= 1} onclick={() => goToPage(1)}>
						<ChevronsLeft class="h-3.5 w-3.5" />
					</Button>
					<Button variant="outline" size="sm" disabled={data.page <= 1} onclick={() => goToPage(data!.page - 1)}>
						<ChevronLeft class="h-3.5 w-3.5" />
					</Button>
					{#each Array.from({ length: Math.min(5, data.pages) }, (_, i) => {
						const start = Math.max(1, Math.min(data!.page - 2, data!.pages - 4));
						return start + i;
					}).filter((p) => p <= data!.pages) as p}
						<Button
							variant="outline"
							size="sm"
							class={p === data.page ? 'bg-primary/10 border-primary/30' : ''}
							onclick={() => goToPage(p)}
						>
							{p}
						</Button>
					{/each}
					<Button variant="outline" size="sm" disabled={data.page >= data.pages} onclick={() => goToPage(data!.page + 1)}>
						<ChevronRight class="h-3.5 w-3.5" />
					</Button>
					<Button variant="outline" size="sm" disabled={data.page >= data.pages} onclick={() => goToPage(data!.pages)}>
						<ChevronsRight class="h-3.5 w-3.5" />
					</Button>
				</div>
			</div>
		{/if}
	{/if}
</div>
