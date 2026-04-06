<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import Plus from '@lucide/svelte/icons/plus';
	import Search from '@lucide/svelte/icons/search';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Microscope from '@lucide/svelte/icons/microscope';
	import Eye from '@lucide/svelte/icons/eye';
	import StopCircle from '@lucide/svelte/icons/circle-stop';
	import Trash2 from '@lucide/svelte/icons/trash-2';
	import Clock from '@lucide/svelte/icons/clock';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Ban from '@lucide/svelte/icons/ban';
	import AlertTriangle from '@lucide/svelte/icons/triangle-alert';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import { onMount } from 'svelte';
	import {
		getAnalysisTasks,
		getAnalysisStats,
		cancelAnalysisTask,
		deleteAnalysisTask,
		type AnalysisTaskList,
		type AnalysisStats,
		type PaginatedAnalysisTasks,
	} from '$lib/api/client';

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		failed: 'bg-red-500/15 text-red-400 border-red-500/30',
		pending: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		partial: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
		cancelled: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const severityColors: Record<string, string> = {
		critical: 'bg-red-500/15 text-red-400 border-red-500/30',
		high: 'bg-red-500/15 text-red-400 border-red-500/30',
		medium: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		low: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		info: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	let loading = $state(true);
	let error = $state('');
	let tasks = $state<AnalysisTaskList[]>([]);
	let stats = $state<AnalysisStats | null>(null);
	let totalTasks = $state(0);
	let totalPages = $state(1);
	let currentPage = $state(1);
	let perPage = $state(25);
	let searchQuery = $state('');
	let statusFilter = $state('');
	let refreshing = $state(false);
	let cancellingIds = $state(new Set<string>());
	let deletingIds = $state(new Set<string>());

	let debounceTimer: ReturnType<typeof setTimeout> | undefined;
	let pollTimer: ReturnType<typeof setInterval> | undefined;

	let hasRunningTasks = $derived(tasks.some((t) => t.status === 'running' || t.status === 'pending'));

	async function fetchTasks() {
		try {
			const data: PaginatedAnalysisTasks = await getAnalysisTasks({
				page: currentPage,
				per_page: perPage,
				status: statusFilter || undefined,
				search: searchQuery || undefined,
			});
			tasks = data.items;
			totalTasks = data.total;
			totalPages = data.pages;
			currentPage = data.page;
			error = '';
		} catch (e) {
			error = 'Failed to load analysis tasks.';
			console.error(e);
		}
	}

	async function fetchStats() {
		try {
			stats = await getAnalysisStats();
		} catch (e) {
			console.error('Failed to load stats:', e);
		}
	}

	async function loadAll(showLoading = true) {
		if (showLoading) loading = true;
		await Promise.all([fetchTasks(), fetchStats()]);
		loading = false;
		refreshing = false;
	}

	function handleRefresh() {
		refreshing = true;
		loadAll(false);
	}

	function handleSearchInput() {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			currentPage = 1;
			fetchTasks();
		}, 300);
	}

	function handleStatusChange() {
		currentPage = 1;
		fetchTasks();
	}

	function handlePerPageChange() {
		currentPage = 1;
		fetchTasks();
	}

	function goToPage(page: number) {
		if (page < 1 || page > totalPages) return;
		currentPage = page;
		fetchTasks();
	}

	async function handleCancel(taskId: string) {
		cancellingIds = new Set([...cancellingIds, taskId]);
		try {
			await cancelAnalysisTask(taskId);
			await loadAll(false);
		} catch (e) {
			console.error('Failed to cancel task:', e);
		} finally {
			const next = new Set(cancellingIds);
			next.delete(taskId);
			cancellingIds = next;
		}
	}

	async function handleDelete(taskId: string) {
		deletingIds = new Set([...deletingIds, taskId]);
		try {
			await deleteAnalysisTask(taskId);
			await loadAll(false);
		} catch (e) {
			console.error('Failed to delete task:', e);
		} finally {
			const next = new Set(deletingIds);
			next.delete(taskId);
			deletingIds = next;
		}
	}

	function setupPolling() {
		clearInterval(pollTimer);
		pollTimer = setInterval(() => {
			if (hasRunningTasks) {
				fetchTasks();
				fetchStats();
			}
		}, 5000);
	}

	function taskDisplayName(task: AnalysisTaskList): string {
		return task.name || `Analysis #${task.id.slice(0, 8)}`;
	}

	function formatDate(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) +
			' ' +
			d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
	}

	function formatDuration(seconds: number | null): string {
		if (seconds == null) return '—';
		if (seconds < 60) return `${Math.round(seconds)}s`;
		const m = Math.floor(seconds / 60);
		const s = Math.round(seconds % 60);
		return `${m}m ${s}s`;
	}

	function getSeverityBreakdown(task: AnalysisTaskList): [string, number][] {
		const bySeverity = task.results_summary?.by_severity;
		if (!bySeverity || typeof bySeverity !== 'object') return [];
		return Object.entries(bySeverity).filter(([, v]) => (v as number) > 0) as [string, number][];
	}

	function statusLabel(status: string): string {
		return status.charAt(0).toUpperCase() + status.slice(1);
	}

	onMount(() => {
		loadAll();
		setupPolling();
		return () => {
			clearTimeout(debounceTimer);
			clearInterval(pollTimer);
		};
	});
</script>

<svelte:head>
	<title>Analysis Hub - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div class="page-header">
			<h1>Analysis Hub</h1>
			<p>Run and monitor analysis tasks across your applications.</p>
		</div>
		<div class="flex items-center gap-2">
			<Button variant="outline" size="sm" onclick={handleRefresh} disabled={refreshing}>
				<RefreshCw class="mr-2 h-3.5 w-3.5 {refreshing ? 'animate-spin' : ''}" />
				Refresh
			</Button>
			<Button size="sm" href="/analysis/create">
				<Plus class="mr-2 h-3.5 w-3.5" />
				New
			</Button>
		</div>
	</div>

	<!-- Stats -->
	{#if stats}
		<div class="flex flex-wrap items-center gap-2">
			<Badge variant="outline" class="gap-1.5">
				<Microscope class="h-3 w-3" />
				{stats.total_tasks} tasks
			</Badge>
			<Badge variant="outline" class="gap-1.5 border-blue-500/30 text-blue-400">
				{stats.running_tasks} running
			</Badge>
			<Badge variant="outline" class="gap-1.5 border-emerald-500/30 text-emerald-500">
				{stats.completed_tasks} completed
			</Badge>
			{#if stats.failed_tasks > 0}
				<Badge variant="outline" class="gap-1.5 border-red-500/30 text-red-400">
					{stats.failed_tasks} failed
				</Badge>
			{/if}
			{#if stats.total_findings > 0}
				<Badge variant="outline" class="gap-1.5">
					{stats.total_findings} findings
				</Badge>
			{/if}
		</div>
	{/if}

	<!-- Filters -->
	<div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
		<div class="relative flex-1 sm:max-w-sm">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<input
				type="text"
				placeholder="Search by name..."
				class="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
				bind:value={searchQuery}
				oninput={handleSearchInput}
			/>
		</div>
		<div class="flex gap-2">
			<select
				class="h-9 flex-1 rounded-md border border-input bg-background px-3 text-sm sm:flex-none"
				bind:value={statusFilter}
				onchange={handleStatusChange}
			>
				<option value="">All Statuses</option>
				<option value="running">Running</option>
				<option value="pending">Pending</option>
				<option value="completed">Completed</option>
				<option value="partial">Partial</option>
				<option value="failed">Failed</option>
				<option value="cancelled">Cancelled</option>
			</select>
			<select
				class="h-9 rounded-md border border-input bg-background px-3 text-sm"
				bind:value={perPage}
				onchange={handlePerPageChange}
			>
				<option value={10}>10 / page</option>
				<option value={25}>25 / page</option>
				<option value={50}>50 / page</option>
				<option value={100}>100 / page</option>
			</select>
		</div>
	</div>

	<!-- Loading -->
	{#if loading}
		<div class="flex items-center justify-center py-20">
			<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
		</div>
	{:else if error}
		<!-- Error -->
		<Card.Root>
			<Card.Content class="flex flex-col items-center gap-3 py-12">
				<AlertTriangle class="h-8 w-8 text-red-400" />
				<p class="text-sm text-muted-foreground">{error}</p>
				<Button variant="outline" size="sm" onclick={() => loadAll()}>Retry</Button>
			</Card.Content>
		</Card.Root>
	{:else if tasks.length === 0}
		<!-- Empty -->
		<Card.Root>
			<Card.Content class="flex flex-col items-center gap-3 py-16">
				<Microscope class="h-10 w-10 text-muted-foreground" />
				<p class="text-sm text-muted-foreground">
					{searchQuery || statusFilter ? 'No tasks match your filters.' : 'No analysis tasks yet.'}
				</p>
				{#if !searchQuery && !statusFilter}
					<Button size="sm" href="/analysis/create">
						<Plus class="mr-2 h-3.5 w-3.5" />
						Run your first analysis
					</Button>
				{/if}
			</Card.Content>
		</Card.Root>
	{:else}
		<!-- Tasks Table (desktop) -->
		<div class="hidden md:block">
			<Card.Root>
				<Card.Content class="p-0">
					<div class="overflow-x-auto">
						<table class="w-full">
							<thead>
								<tr class="border-b bg-muted/30">
									<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Name</th>
									<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
									<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Findings</th>
									<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
									<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Duration</th>
									<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Actions</th>
								</tr>
							</thead>
							<tbody class="divide-y">
								{#each tasks as task (task.id)}
									<tr
										class="transition-colors hover:bg-muted/30 cursor-pointer"
										onclick={() => window.location.href = `/analysis/${task.id}`}
										onkeydown={(e) => { if (e.key === 'Enter') window.location.href = `/analysis/${task.id}`; }}
										tabindex="0"
										role="link"
									>
										<td class="px-4 py-3">
											<div class="flex flex-col gap-0.5">
												<span class="text-sm font-medium">{taskDisplayName(task)}</span>
												<span class="text-xs text-muted-foreground font-mono">{task.id.slice(0, 8)}</span>
											</div>
										</td>
										<td class="px-4 py-3">
											<Badge variant="outline" class="text-[10px] {statusColors[task.status] ?? ''}">
												{#if task.status === 'running'}
													<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
												{:else if task.status === 'pending'}
													<Clock class="mr-1 h-3 w-3" />
												{:else if task.status === 'completed'}
													<Check class="mr-1 h-3 w-3" />
												{:else if task.status === 'failed'}
													<X class="mr-1 h-3 w-3" />
												{:else if task.status === 'cancelled'}
													<Ban class="mr-1 h-3 w-3" />
												{:else if task.status === 'partial'}
													<AlertTriangle class="mr-1 h-3 w-3" />
												{/if}
												{statusLabel(task.status)}
											</Badge>
										</td>
										<td class="px-4 py-3">
											{#if getSeverityBreakdown(task).length > 0}
												<div class="flex flex-wrap gap-1">
													{#each getSeverityBreakdown(task) as [sev, count]}
														<Badge variant="outline" class="text-[10px] {severityColors[sev] ?? ''}">{count} {sev.charAt(0).toUpperCase()}</Badge>
													{/each}
												</div>
											{:else}
												<span class="text-xs text-muted-foreground">—</span>
											{/if}
										</td>
										<td class="px-4 py-3 text-sm text-muted-foreground">
											{formatDate(task.created_at)}
										</td>
										<td class="px-4 py-3 text-sm text-muted-foreground">
											{formatDuration(task.duration_seconds)}
										</td>
										<td class="px-4 py-3">
											<!-- svelte-ignore a11y_no_static_element_interactions a11y_no_noninteractive_element_interactions a11y_click_events_have_key_events -->
											<div class="flex items-center gap-1" onclick={(e) => e.stopPropagation()}>
												{#if task.status === 'completed' || task.status === 'partial'}
													<Button variant="ghost" size="sm" class="h-7 w-7 p-0" href="/analysis/{task.id}" title="View results">
														<Eye class="h-3.5 w-3.5" />
													</Button>
												{/if}
												{#if task.status === 'running' || task.status === 'pending'}
													<Button
														variant="ghost"
														size="sm"
														class="h-7 w-7 p-0"
														title="Cancel"
														disabled={cancellingIds.has(task.id)}
														onclick={() => handleCancel(task.id)}
													>
														{#if cancellingIds.has(task.id)}
															<LoaderCircle class="h-3.5 w-3.5 animate-spin" />
														{:else}
															<StopCircle class="h-3.5 w-3.5" />
														{/if}
													</Button>
												{/if}
												{#if task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled'}
													<Button
														variant="ghost"
														size="sm"
														class="h-7 w-7 p-0 text-red-400 hover:text-red-300"
														title="Delete"
														disabled={deletingIds.has(task.id)}
														onclick={() => handleDelete(task.id)}
													>
														{#if deletingIds.has(task.id)}
															<LoaderCircle class="h-3.5 w-3.5 animate-spin" />
														{:else}
															<Trash2 class="h-3.5 w-3.5" />
														{/if}
													</Button>
												{/if}
											</div>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Tasks Cards (mobile) -->
		<div class="md:hidden space-y-3">
			{#each tasks as task (task.id)}
				<a href="/analysis/{task.id}" class="block border rounded-lg p-3 bg-card transition-colors hover:bg-muted/30">
					<div class="flex items-center justify-between gap-2 mb-2">
						<div class="flex flex-col min-w-0">
							<span class="text-sm font-medium truncate">{taskDisplayName(task)}</span>
							<span class="font-mono text-xs text-muted-foreground">{task.id.slice(0, 8)}</span>
						</div>
						<Badge variant="outline" class="shrink-0 text-[10px] {statusColors[task.status] ?? ''}">
							{#if task.status === 'running'}
								<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
							{:else if task.status === 'pending'}
								<Clock class="mr-1 h-3 w-3" />
							{:else if task.status === 'completed'}
								<Check class="mr-1 h-3 w-3" />
							{:else if task.status === 'failed'}
								<X class="mr-1 h-3 w-3" />
							{:else if task.status === 'cancelled'}
								<Ban class="mr-1 h-3 w-3" />
							{:else if task.status === 'partial'}
								<AlertTriangle class="mr-1 h-3 w-3" />
							{/if}
							{statusLabel(task.status)}
						</Badge>
					</div>

					<div class="space-y-1.5 mb-2">
						{#if getSeverityBreakdown(task).length > 0}
							<div class="flex flex-wrap gap-1">
								{#each getSeverityBreakdown(task) as [sev, count]}
									<Badge variant="outline" class="text-[10px] {severityColors[sev] ?? ''}">{count} {sev.charAt(0).toUpperCase()}</Badge>
								{/each}
							</div>
						{/if}
					</div>

					<div class="flex items-center justify-between border-t pt-2">
						<div class="text-xs text-muted-foreground">
							<span>{formatDuration(task.duration_seconds)}</span>
							<span class="mx-1">·</span>
							<span>{formatDate(task.created_at)}</span>
						</div>
						<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
						<div class="flex items-center gap-1" onclick={(e) => { e.preventDefault(); e.stopPropagation(); }}>
							{#if task.status === 'running' || task.status === 'pending'}
								<Button
									variant="ghost"
									size="sm"
									class="h-7 w-7 p-0"
									title="Cancel"
									disabled={cancellingIds.has(task.id)}
									onclick={() => handleCancel(task.id)}
								>
									{#if cancellingIds.has(task.id)}
										<LoaderCircle class="h-3.5 w-3.5 animate-spin" />
									{:else}
										<StopCircle class="h-3.5 w-3.5" />
									{/if}
								</Button>
							{/if}
						</div>
					</div>
				</a>
			{/each}
		</div>

		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="flex flex-col items-center gap-3 sm:flex-row sm:justify-between text-sm text-muted-foreground">
				<span>Showing {(currentPage - 1) * perPage + 1}–{Math.min(currentPage * perPage, totalTasks)} of {totalTasks}</span>
				<div class="flex items-center gap-1">
					<Button
						variant="outline"
						size="sm"
						disabled={currentPage <= 1}
						onclick={() => goToPage(currentPage - 1)}
					>
						<ChevronLeft class="h-3.5 w-3.5 mr-1" />
						Previous
					</Button>
					{#each Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
						const start = Math.max(1, Math.min(currentPage - 2, totalPages - 4));
						return start + i;
					}).filter(p => p <= totalPages) as page}
						<Button
							variant="outline"
							size="sm"
							class={page === currentPage ? 'bg-primary/10' : ''}
							onclick={() => goToPage(page)}
						>
							{page}
						</Button>
					{/each}
					<Button
						variant="outline"
						size="sm"
						disabled={currentPage >= totalPages}
						onclick={() => goToPage(currentPage + 1)}
					>
						Next
						<ChevronRight class="h-3.5 w-3.5 ml-1" />
					</Button>
				</div>
			</div>
		{/if}
	{/if}
</div>
