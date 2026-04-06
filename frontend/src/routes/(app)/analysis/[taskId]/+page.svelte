<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Microscope from '@lucide/svelte/icons/microscope';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import Ban from '@lucide/svelte/icons/ban';
	import Clock from '@lucide/svelte/icons/clock';
	import FileText from '@lucide/svelte/icons/file-text';
	import {
		getAnalysisTask,
		getAnalysisResults,
		getAnalysisFindings,
		cancelAnalysisTask,
		type AnalysisTask,
		type AnalysisResult,
		type AnalysisFinding,
		type PaginatedFindings,
	} from '$lib/api/client';

	const taskId = $derived($page.params.taskId ?? '');

	let task = $state<AnalysisTask | null>(null);
	let results = $state<AnalysisResult[]>([]);
	let loading = $state(true);
	let error = $state('');
	let cancelling = $state(false);
	let pollTimer: ReturnType<typeof setInterval> | null = null;

	// Per-result findings state keyed by result id
	let findingsMap = $state<Record<number, AnalysisFinding[]>>({});
	let findingsPagination = $state<Record<number, { page: number; pages: number; total: number }>>({});
	let findingsLoading = $state<Record<number, boolean>>({});
	let expandedFindings = $state<Record<number, boolean>>({});

	let activeSection = $state('summary');

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		failed: 'bg-red-500/15 text-red-400 border-red-500/30',
		pending: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		partial: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
		cancelled: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
		skipped: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const severityColors: Record<string, string> = {
		critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
		high: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
		medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
		low: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
		info: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
	};

	const analyzerTypeLabels: Record<string, string> = {
		static: 'Static Analysis',
		dynamic: 'Dynamic Analysis',
		performance: 'Performance',
		ai: 'AI Review',
	};

	const sections = $derived([
		{ id: 'summary', label: 'Summary' },
		...results.map((r) => ({ id: `result-${r.id}`, label: r.analyzer_name })),
	]);

	function scrollToSection(id: string) {
		activeSection = id;
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	function formatDuration(seconds: number | null): string {
		if (seconds == null) return '—';
		if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
		if (seconds < 60) return `${seconds.toFixed(1)}s`;
		const m = Math.floor(seconds / 60);
		const s = Math.round(seconds % 60);
		return `${m}m ${s}s`;
	}

	function formatDate(iso: string | null): string {
		if (!iso) return '—';
		return new Date(iso).toLocaleString();
	}

	async function fetchData() {
		try {
			const [t, r] = await Promise.all([getAnalysisTask(taskId), getAnalysisResults(taskId)]);
			task = t;
			results = r;
			error = '';
		} catch (e: any) {
			error = e?.detail || e?.message || 'Failed to load analysis task';
		} finally {
			loading = false;
		}
	}

	function startPolling() {
		stopPolling();
		pollTimer = setInterval(async () => {
			if (task && (task.status === 'running' || task.status === 'pending')) {
				try {
					const [t, r] = await Promise.all([getAnalysisTask(taskId), getAnalysisResults(taskId)]);
					task = t;
					results = r;
				} catch {
					// ignore poll errors
				}
			} else {
				stopPolling();
			}
		}, 3000);
	}

	function stopPolling() {
		if (pollTimer) {
			clearInterval(pollTimer);
			pollTimer = null;
		}
	}

	async function handleCancel() {
		if (!task || cancelling) return;
		cancelling = true;
		try {
			await cancelAnalysisTask(taskId);
			await fetchData();
		} catch {
			// ignore
		} finally {
			cancelling = false;
		}
	}

	async function loadFindings(resultObj: AnalysisResult, pageNum: number = 1) {
		const rid = resultObj.id;
		findingsLoading[rid] = true;
		try {
			const data: PaginatedFindings = await getAnalysisFindings(taskId, {
				analyzer: resultObj.analyzer_name,
				page: pageNum,
				per_page: 25,
			});
			if (pageNum === 1) {
				findingsMap[rid] = data.items;
			} else {
				findingsMap[rid] = [...(findingsMap[rid] ?? []), ...data.items];
			}
			findingsPagination[rid] = { page: data.page, pages: data.pages, total: data.total };
		} catch {
			// ignore
		} finally {
			findingsLoading[rid] = false;
		}
	}

	function toggleFindingExpand(findingId: number) {
		expandedFindings[findingId] = !expandedFindings[findingId];
	}

	$effect(() => {
		if (task && (task.status === 'running' || task.status === 'pending')) {
			startPolling();
		}
		return () => stopPolling();
	});

	onMount(() => {
		fetchData();
		return () => stopPolling();
	});
</script>

<svelte:head>
	<title>{task?.name || `Analysis ${taskId}`} - LLM Lab</title>
</svelte:head>

{#if loading}
	<!-- Loading State -->
	<div class="flex flex-col items-center justify-center py-24 text-muted-foreground">
		<LoaderCircle class="h-8 w-8 animate-spin mb-4" />
		<p class="text-sm">Loading analysis…</p>
	</div>
{:else if error}
	<!-- Error State -->
	<div class="space-y-6">
		<div class="flex items-center gap-2 text-sm text-muted-foreground">
			<Button variant="ghost" size="sm" href="/analysis" class="gap-1.5 px-2">
				<ArrowLeft class="h-3.5 w-3.5" />
				Analysis Hub
			</Button>
		</div>
		<Card.Root class="border-red-500/20">
			<Card.Content class="p-8 text-center">
				<AlertTriangle class="mx-auto h-10 w-10 text-red-400 mb-4" />
				<h2 class="text-lg font-semibold text-red-400 mb-2">Task Not Found</h2>
				<p class="text-sm text-muted-foreground">{error}</p>
				<Button variant="outline" size="sm" href="/analysis" class="mt-4">Back to Analysis Hub</Button>
			</Card.Content>
		</Card.Root>
	</div>
{:else if task}
	<div class="space-y-6">
		<!-- Breadcrumb -->
		<div class="flex items-center gap-2 text-sm text-muted-foreground">
			<Button variant="ghost" size="sm" href="/analysis" class="gap-1.5 px-2">
				<ArrowLeft class="h-3.5 w-3.5" />
				Analysis Hub
			</Button>
			<span>/</span>
			<span class="text-foreground font-medium truncate max-w-xs">{task.name || taskId}</span>
		</div>

		<!-- Header Card -->
		<Card.Root class="border-border/60">
			<Card.Content class="p-6">
				<div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
							<Microscope class="h-6 w-6 text-muted-foreground" />
						</div>
						<div>
							<div class="flex flex-wrap items-center gap-2 sm:gap-3">
								<h1 class="text-xl font-semibold">{task.name || 'Analysis Task'}</h1>
								<Badge variant="outline" class="{statusColors[task.status] ?? ''} {task.status === 'running' ? 'animate-pulse' : ''}">{task.status}</Badge>
							</div>
							<p class="mt-1 text-sm text-muted-foreground">
								{taskId}
								{#if task.duration_seconds != null} • {formatDuration(task.duration_seconds)}{/if}
								 • {task.findings_count} findings
							</p>
						</div>
					</div>
					<div class="hidden sm:flex items-center gap-3 text-sm text-muted-foreground">
						<div class="text-center">
							<div class="text-2xl font-bold text-foreground">{task.findings_count}</div>
							<div class="text-xs">Findings</div>
						</div>
						<Separator orientation="vertical" class="h-8" />
						<div class="text-center">
							<div class="text-2xl font-bold text-foreground">{results.length}</div>
							<div class="text-xs">Analyzers</div>
						</div>
					</div>
				</div>
				<div class="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
					{#if task.status === 'running' || task.status === 'pending'}
						<Button variant="destructive" size="sm" onclick={handleCancel} disabled={cancelling}>
							<Ban class="mr-1.5 h-3.5 w-3.5" />
							{cancelling ? 'Cancelling…' : 'Cancel'}
						</Button>
					{/if}
					<Button variant="ghost" size="sm" onclick={fetchData}>
						<RefreshCw class="mr-1.5 h-3.5 w-3.5" /> Refresh
					</Button>
				</div>
				{#if task.error_message}
					<div class="mt-3 rounded-md bg-red-500/10 p-3 text-sm text-red-400">
						<strong>Error:</strong> {task.error_message}
					</div>
				{/if}
			</Card.Content>
		</Card.Root>

		<!-- Section Nav -->
		<div class="sticky top-0 z-40 -mx-4 bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
			<nav class="flex gap-1 overflow-x-auto flex-nowrap border-b py-2">
				{#each sections as section}
					<button
						class="rounded-md px-3 py-1.5 text-sm transition-colors whitespace-nowrap {activeSection === section.id ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:text-foreground'}"
						onclick={() => scrollToSection(section.id)}
					>
						{section.label}
					</button>
				{/each}
			</nav>
		</div>

		<!-- ===== Summary ===== -->
		<div id="summary" class="scroll-mt-16 space-y-4">
			<h2 class="text-lg font-semibold">Summary</h2>

			<!-- Analyzer Result Cards -->
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 lg:grid-cols-4">
				{#each results as r}
					<Card.Root>
						<Card.Content class="p-4">
							<div class="flex items-center gap-2 mb-2">
								<span class="text-sm font-medium">{r.analyzer_name}</span>
								<Badge variant="outline" class="ml-auto text-[10px] {statusColors[r.status] ?? ''}">{r.status}</Badge>
							</div>
							<div class="text-xl font-bold">{r.findings_count} findings</div>
							{#if r.duration_seconds != null}
								<div class="text-xs text-muted-foreground mt-1">{formatDuration(r.duration_seconds)}</div>
							{/if}
						</Card.Content>
					</Card.Root>
				{/each}
			</div>

			<!-- Timing -->
			<Card.Root>
				<Card.Content class="p-4">
					<div class="flex flex-wrap items-center gap-3 sm:gap-6 text-sm">
						<div><span class="text-muted-foreground">Duration:</span> <span class="font-mono font-medium">{formatDuration(task.duration_seconds)}</span></div>
						<div><span class="text-muted-foreground">Started:</span> <span class="font-mono">{formatDate(task.started_at)}</span></div>
						<div><span class="text-muted-foreground">Completed:</span> <span class="font-mono">{formatDate(task.completed_at)}</span></div>
						<div><span class="text-muted-foreground">Created:</span> <span class="font-mono">{formatDate(task.created_at)}</span></div>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Severity Breakdown from results_summary -->
			{#if task.results_summary?.by_severity}
				<div class="flex flex-wrap gap-2">
					{#each Object.entries(task.results_summary.by_severity) as [sev, count]}
						<Badge variant="outline" class="{severityColors[sev] ?? ''} text-xs">
							{count} {sev}
						</Badge>
					{/each}
				</div>
			{/if}

			<!-- Metadata -->
			<div class="grid gap-4 md:grid-cols-2">
				<Card.Root>
					<Card.Header><Card.Title class="text-sm">Task Information</Card.Title></Card.Header>
					<Card.Content>
						<dl class="grid grid-cols-2 gap-y-2 text-sm">
							<dt class="text-muted-foreground">Task ID</dt><dd class="font-mono text-xs truncate">{task.id}</dd>
							<dt class="text-muted-foreground">Status</dt><dd><Badge variant="outline" class="{statusColors[task.status] ?? ''} text-xs">{task.status}</Badge></dd>
							<dt class="text-muted-foreground">Total Findings</dt><dd class="font-semibold">{task.findings_count}</dd>
							<dt class="text-muted-foreground">Analyzers Run</dt><dd>{task.results_count}</dd>
							{#if task.generation_job_name}
								<dt class="text-muted-foreground">Generation Job</dt><dd class="font-mono text-xs truncate">{task.generation_job_name}</dd>
							{/if}
						</dl>
					</Card.Content>
				</Card.Root>
				<Card.Root>
					<Card.Header><Card.Title class="text-sm">Configuration</Card.Title></Card.Header>
					<Card.Content>
						{#if task.configuration && Object.keys(task.configuration).length > 0}
							<dl class="grid grid-cols-2 gap-y-2 text-sm">
								{#if task.configuration.analyzers}
									<dt class="text-muted-foreground">Analyzers</dt>
									<dd>
										<div class="flex flex-wrap gap-1">
											{#each task.configuration.analyzers as a}
												<Badge variant="secondary" class="text-xs">{a}</Badge>
											{/each}
										</div>
									</dd>
								{/if}
								{#each Object.entries(task.configuration.settings ?? {}) as [key, val]}
									<dt class="text-muted-foreground">{key}</dt><dd class="font-mono text-xs">{JSON.stringify(val)}</dd>
								{/each}
							</dl>
						{:else}
							<p class="text-sm text-muted-foreground">No configuration data</p>
						{/if}
					</Card.Content>
				</Card.Root>
			</div>
		</div>

		<!-- ===== Per-Analyzer Result Sections ===== -->
		{#each results as r (r.id)}
			<div id="result-{r.id}" class="scroll-mt-16 space-y-4">
				<!-- Section Header -->
				<div class="flex flex-wrap items-center gap-3">
					<h2 class="text-lg font-semibold">{r.analyzer_name}</h2>
					<Badge variant="outline" class="text-xs">{analyzerTypeLabels[r.analyzer_type] ?? r.analyzer_type}</Badge>
					<Badge variant="outline" class="{statusColors[r.status] ?? ''} text-xs">{r.status}</Badge>
					{#if r.duration_seconds != null}
						<span class="text-xs text-muted-foreground flex items-center gap-1">
							<Clock class="h-3 w-3" /> {formatDuration(r.duration_seconds)}
						</span>
					{/if}
				</div>

				{#if r.error_message}
					<div class="rounded-md bg-red-500/10 p-3 text-sm text-red-400">
						<strong>Error:</strong> {r.error_message}
					</div>
				{/if}

				<!-- Severity Breakdown -->
				{#if Object.keys(r.finding_summary).length > 0}
					<div class="flex flex-wrap gap-2">
						{#each Object.entries(r.finding_summary) as [sev, count]}
							<Badge variant="outline" class="{severityColors[sev] ?? ''} text-xs">{count} {sev}</Badge>
						{/each}
						<Badge variant="outline" class="text-xs">{r.findings_count} total</Badge>
					</div>
				{/if}

				<!-- Summary Metrics from result.summary -->
				{#if r.summary && Object.keys(r.summary).length > 0}
					<Card.Root>
						<Card.Header><Card.Title class="text-sm">Summary Metrics</Card.Title></Card.Header>
						<Card.Content>
							<dl class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-x-4 gap-y-2 text-sm">
								{#each Object.entries(r.summary) as [key, val]}
									<div>
										<dt class="text-muted-foreground text-xs">{key.replace(/_/g, ' ')}</dt>
										<dd class="font-mono font-medium">
											{#if typeof val === 'object' && val !== null}
												{JSON.stringify(val)}
											{:else}
												{val}
											{/if}
										</dd>
									</div>
								{/each}
							</dl>
						</Card.Content>
					</Card.Root>
				{/if}

				<!-- Findings Table -->
				{#if r.findings_count > 0}
					{#if !findingsMap[r.id]}
						<Button variant="outline" size="sm" onclick={() => loadFindings(r)} disabled={findingsLoading[r.id]}>
							{#if findingsLoading[r.id]}
								<LoaderCircle class="mr-1.5 h-3.5 w-3.5 animate-spin" />
								Loading…
							{:else}
								<FileText class="mr-1.5 h-3.5 w-3.5" />
								Load {r.findings_count} findings
							{/if}
						</Button>
					{:else}
						<Card.Root>
							<Card.Content class="p-0">
								<div class="overflow-x-auto">
									<table class="w-full text-sm">
										<thead>
											<tr class="border-b bg-muted/30">
												<th class="w-8 px-4 py-2"></th>
												<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Severity</th>
												<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Title</th>
												<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">File</th>
												<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Line</th>
												<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Rule</th>
												<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Confidence</th>
											</tr>
										</thead>
										<tbody class="divide-y">
											{#each findingsMap[r.id] as finding (finding.id)}
												<tr
													class="hover:bg-muted/30 cursor-pointer"
													onclick={() => toggleFindingExpand(finding.id)}
													onkeydown={(e) => { if (e.key === 'Enter') toggleFindingExpand(finding.id); }}
													tabindex="0"
													role="button"
												>
													<td class="px-4 py-2">
														{#if expandedFindings[finding.id]}
															<ChevronDown class="h-3.5 w-3.5 text-muted-foreground" />
														{:else}
															<ChevronRight class="h-3.5 w-3.5 text-muted-foreground" />
														{/if}
													</td>
													<td class="px-4 py-2">
														<Badge variant="outline" class="text-[10px] {severityColors[finding.severity] ?? ''}">{finding.severity}</Badge>
													</td>
													<td class="px-4 py-2 max-w-xs truncate">{finding.title}</td>
													<td class="px-4 py-2 font-mono text-xs max-w-[200px] truncate">{finding.file_path || '—'}</td>
													<td class="px-4 py-2 font-mono text-xs">{finding.line_number ?? '—'}</td>
													<td class="px-4 py-2 font-mono text-xs">{finding.rule_id || '—'}</td>
													<td class="px-4 py-2">
														{#if finding.confidence}
															<Badge variant="outline" class="text-[10px] {finding.confidence === 'high' ? 'bg-emerald-500/15 text-emerald-500' : finding.confidence === 'medium' ? 'bg-amber-500/15 text-amber-500' : 'bg-zinc-500/15 text-zinc-400'}">{finding.confidence}</Badge>
														{/if}
													</td>
												</tr>
												{#if expandedFindings[finding.id]}
													<tr>
														<td colspan="7" class="bg-muted/20 px-6 py-4">
															<div class="space-y-3 text-sm">
																{#if finding.description}
																	<div>
																		<h4 class="text-xs font-medium text-muted-foreground mb-1">Description</h4>
																		<p>{finding.description}</p>
																	</div>
																{/if}
																{#if finding.suggestion}
																	<div>
																		<h4 class="text-xs font-medium text-muted-foreground mb-1">Suggestion</h4>
																		<p class="text-emerald-500">{finding.suggestion}</p>
																	</div>
																{/if}
																{#if finding.code_snippet}
																	<div>
																		<h4 class="text-xs font-medium text-muted-foreground mb-1">Code</h4>
																		<pre class="rounded-md bg-muted p-3 text-xs font-mono overflow-x-auto whitespace-pre-wrap">{finding.code_snippet}</pre>
																	</div>
																{/if}
																<div class="flex flex-wrap gap-3 text-xs text-muted-foreground">
																	{#if finding.category}<span>Category: <strong>{finding.category}</strong></span>{/if}
																	{#if finding.analyzer_name}<span>Analyzer: <strong>{finding.analyzer_name}</strong></span>{/if}
																</div>
															</div>
														</td>
													</tr>
												{/if}
											{/each}
										</tbody>
									</table>
								</div>
							</Card.Content>
						</Card.Root>

						<!-- Load More -->
						{#if findingsPagination[r.id] && findingsPagination[r.id].page < findingsPagination[r.id].pages}
							<Button
								variant="outline"
								size="sm"
								onclick={() => loadFindings(r, findingsPagination[r.id].page + 1)}
								disabled={findingsLoading[r.id]}
							>
								{#if findingsLoading[r.id]}
									<LoaderCircle class="mr-1.5 h-3.5 w-3.5 animate-spin" /> Loading…
								{:else}
									Load more ({findingsPagination[r.id].total - findingsMap[r.id].length} remaining)
								{/if}
							</Button>
						{/if}
					{/if}
				{:else if r.status === 'completed'}
					<p class="text-sm text-muted-foreground">No findings — clean result.</p>
				{/if}
			</div>
		{/each}
	</div>
{/if}
