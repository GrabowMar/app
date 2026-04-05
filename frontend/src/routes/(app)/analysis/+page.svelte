<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import Plus from '@lucide/svelte/icons/plus';
	import Search from '@lucide/svelte/icons/search';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Microscope from '@lucide/svelte/icons/microscope';
	import Eye from '@lucide/svelte/icons/eye';
	import Download from '@lucide/svelte/icons/download';
	import StopCircle from '@lucide/svelte/icons/circle-stop';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import Clock from '@lucide/svelte/icons/clock';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Ban from '@lucide/svelte/icons/ban';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';

	interface Subtask {
		service: string;
		status: string;
		progress: number;
		findings: number;
	}

	interface Task {
		id: string;
		model: string;
		modelSlug: string;
		appNumber: number;
		type: string;
		tools: string[];
		status: string;
		progress: number;
		findings: number;
		severityBreakdown: Record<string, number>;
		duration: string;
		createdAt: string;
		subtasks: Subtask[];
	}

	const statusColors: Record<string, string> = {
		'Running': 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		'Pending': 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
		'Completed': 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		'Partial': 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		'Failed': 'bg-red-500/15 text-red-400 border-red-500/30',
		'Cancelled': 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const severityColors: Record<string, string> = {
		critical: 'bg-red-500/15 text-red-400 border-red-500/30',
		high: 'bg-red-500/15 text-red-400 border-red-500/30',
		medium: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		low: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		info: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const tasks: Task[] = [
		{
			id: 'task-001', model: 'GPT-4o', modelSlug: 'gpt-4o', appNumber: 1, type: 'Full Analysis',
			tools: ['bandit', 'eslint', 'zap', 'lighthouse', 'code-quality'],
			status: 'Completed', progress: 100, findings: 12,
			severityBreakdown: { critical: 0, high: 2, medium: 5, low: 3, info: 2 },
			duration: '2m 15s', createdAt: '19 Mar 15:00',
			subtasks: [
				{ service: 'Static Analysis', status: 'Completed', progress: 100, findings: 5 },
				{ service: 'Dynamic Analysis', status: 'Completed', progress: 100, findings: 3 },
				{ service: 'Performance', status: 'Completed', progress: 100, findings: 2 },
				{ service: 'AI Review', status: 'Completed', progress: 100, findings: 2 },
			],
		},
		{
			id: 'task-002', model: 'Claude 3.5 Sonnet', modelSlug: 'claude-3-5-sonnet', appNumber: 1, type: 'Static Only',
			tools: ['bandit', 'eslint', 'ruff'],
			status: 'Running', progress: 65, findings: 3,
			severityBreakdown: { critical: 0, high: 1, medium: 2, low: 0, info: 0 },
			duration: '1m 22s', createdAt: '19 Mar 15:10',
			subtasks: [
				{ service: 'Static Analysis', status: 'Running', progress: 65, findings: 3 },
			],
		},
		{
			id: 'task-003', model: 'GPT-4o', modelSlug: 'gpt-4o', appNumber: 2, type: 'Full Analysis',
			tools: ['bandit', 'eslint', 'zap', 'lighthouse'],
			status: 'Completed', progress: 100, findings: 7,
			severityBreakdown: { critical: 1, high: 1, medium: 3, low: 1, info: 1 },
			duration: '3m 45s', createdAt: '19 Mar 14:30',
			subtasks: [
				{ service: 'Static Analysis', status: 'Completed', progress: 100, findings: 2 },
				{ service: 'Dynamic Analysis', status: 'Completed', progress: 100, findings: 3 },
				{ service: 'Performance', status: 'Completed', progress: 100, findings: 1 },
				{ service: 'AI Review', status: 'Completed', progress: 100, findings: 1 },
			],
		},
		{
			id: 'task-004', model: 'Gemini 1.5 Pro', modelSlug: 'gemini-1-5-pro', appNumber: 1, type: 'Dynamic Only',
			tools: ['zap', 'port-scan'],
			status: 'Failed', progress: 40, findings: 0,
			severityBreakdown: {},
			duration: '0m 52s', createdAt: '19 Mar 13:45',
			subtasks: [
				{ service: 'Dynamic Analysis', status: 'Failed', progress: 40, findings: 0 },
			],
		},
		{
			id: 'task-005', model: 'GPT-4o Mini', modelSlug: 'gpt-4o-mini', appNumber: 1, type: 'Full Analysis',
			tools: ['bandit', 'eslint', 'zap', 'lighthouse', 'requirements-scanner'],
			status: 'Pending', progress: 0, findings: 0,
			severityBreakdown: {},
			duration: '—', createdAt: '19 Mar 15:15',
			subtasks: [
				{ service: 'Static Analysis', status: 'Pending', progress: 0, findings: 0 },
				{ service: 'Dynamic Analysis', status: 'Pending', progress: 0, findings: 0 },
				{ service: 'Performance', status: 'Pending', progress: 0, findings: 0 },
				{ service: 'AI Review', status: 'Pending', progress: 0, findings: 0 },
			],
		},
		{
			id: 'task-006', model: 'Qwen 2.5 Coder', modelSlug: 'qwen-2-5-coder', appNumber: 1, type: 'Performance Only',
			tools: ['lighthouse', 'load-test'],
			status: 'Completed', progress: 100, findings: 4,
			severityBreakdown: { critical: 0, high: 0, medium: 2, low: 1, info: 1 },
			duration: '1m 08s', createdAt: '19 Mar 12:00',
			subtasks: [
				{ service: 'Performance', status: 'Completed', progress: 100, findings: 4 },
			],
		},
		{
			id: 'task-007', model: 'DeepSeek V3', modelSlug: 'deepseek-v3', appNumber: 1, type: 'Full Analysis',
			tools: ['bandit', 'eslint', 'zap'],
			status: 'Partial', progress: 75, findings: 8,
			severityBreakdown: { critical: 0, high: 3, medium: 3, low: 1, info: 1 },
			duration: '2m 30s', createdAt: '19 Mar 11:30',
			subtasks: [
				{ service: 'Static Analysis', status: 'Completed', progress: 100, findings: 4 },
				{ service: 'Dynamic Analysis', status: 'Completed', progress: 100, findings: 4 },
				{ service: 'Performance', status: 'Failed', progress: 0, findings: 0 },
				{ service: 'AI Review', status: 'Completed', progress: 100, findings: 0 },
			],
		},
	];

	let searchQuery = $state('');
	let statusFilter = $state('all');
	let expandedTasks = $state(new Set<string>());
	let perPage = $state(25);

	const filteredTasks = $derived(
		tasks.filter(t => {
			if (searchQuery && !t.model.toLowerCase().includes(searchQuery.toLowerCase()) && !t.id.toLowerCase().includes(searchQuery.toLowerCase())) return false;
			if (statusFilter !== 'all' && t.status !== statusFilter) return false;
			return true;
		})
	);

	const stats = $derived({
		total: tasks.length,
		active: tasks.filter(t => t.status === 'Running' || t.status === 'Pending').length,
		completed: tasks.filter(t => t.status === 'Completed').length,
	});

	function toggleExpand(id: string) {
		const next = new Set(expandedTasks);
		if (next.has(id)) next.delete(id); else next.add(id);
		expandedTasks = next;
	}
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
			<Button variant="outline" size="sm" disabled>
				<StopCircle class="mr-2 h-3.5 w-3.5" />
				<span class="hidden sm:inline">Stop All</span>
				<span class="sm:hidden">Stop</span>
			</Button>
			<Button variant="outline" size="sm" disabled>
				<RefreshCw class="mr-2 h-3.5 w-3.5" />
				Refresh
			</Button>
			<Button size="sm" href="/analysis/create">
				<Plus class="mr-2 h-3.5 w-3.5" />
				New
			</Button>
		</div>
	</div>

	<!-- Stats -->
	<div class="flex flex-wrap items-center gap-2">
		<Badge variant="outline" class="gap-1.5">
			<Microscope class="h-3 w-3" />
			{stats.total} tasks
		</Badge>
		<Badge variant="outline" class="gap-1.5 border-amber-500/30 text-amber-500">
			{stats.active} active
		</Badge>
		<Badge variant="outline" class="gap-1.5 border-emerald-500/30 text-emerald-500">
			{stats.completed} completed
		</Badge>
	</div>

	<!-- Filters -->
	<div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
		<div class="relative flex-1 sm:max-w-sm">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<input
				type="text"
				placeholder="Search by model or task ID..."
				class="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
				bind:value={searchQuery}
			/>
		</div>
		<div class="flex gap-2">
			<select class="h-9 flex-1 rounded-md border border-input bg-background px-3 text-sm sm:flex-none" bind:value={statusFilter}>
				<option value="all">All Statuses</option>
				<option value="Running">Running</option>
				<option value="Pending">Pending</option>
				<option value="Completed">Completed</option>
				<option value="Partial">Partial</option>
				<option value="Failed">Failed</option>
				<option value="Cancelled">Cancelled</option>
			</select>
			<select class="h-9 rounded-md border border-input bg-background px-3 text-sm" bind:value={perPage}>
				<option value={10}>10 / page</option>
				<option value={25}>25 / page</option>
				<option value={50}>50 / page</option>
				<option value={100}>100 / page</option>
			</select>
		</div>
	</div>

	<!-- Tasks Table (desktop) -->
	<div class="hidden md:block">
		<Card.Root>
			<Card.Content class="p-0">
				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="w-8 px-4 py-3"></th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Task ID</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">App</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Tools</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Progress / Findings</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Time</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Actions</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each filteredTasks.slice(0, perPage) as task (task.id)}
								<!-- Main Row -->
								<tr class="transition-colors hover:bg-muted/30 cursor-pointer" onclick={() => toggleExpand(task.id)}>
									<td class="px-4 py-3">
										{#if task.subtasks.length > 0}
											{#if expandedTasks.has(task.id)}
												<ChevronDown class="h-3.5 w-3.5 text-muted-foreground" />
											{:else}
												<ChevronRight class="h-3.5 w-3.5 text-muted-foreground" />
											{/if}
										{/if}
									</td>
									<td class="px-4 py-3 font-mono text-xs">{task.id}</td>
									<td class="px-4 py-3">
										<div class="flex flex-col gap-0.5">
											<a href="/models/{task.modelSlug}" class="text-sm font-medium hover:underline" onclick={(e) => e.stopPropagation()}>{task.model}</a>
											<span class="text-xs text-muted-foreground">{task.type}</span>
										</div>
									</td>
									<td class="px-4 py-3 text-sm">#{task.appNumber}</td>
									<td class="px-4 py-3">
										<div class="flex flex-wrap gap-1">
											{#each task.tools.slice(0, 3) as tool}
												<Badge variant="secondary" class="text-[10px]">{tool}</Badge>
											{/each}
											{#if task.tools.length > 3}
												<Badge variant="outline" class="text-[10px]">+{task.tools.length - 3}</Badge>
											{/if}
										</div>
									</td>
									<td class="px-4 py-3">
										<Badge variant="outline" class="text-[10px] {statusColors[task.status] ?? ''}">
											{#if task.status === 'Running'}
												<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
											{:else if task.status === 'Pending'}
												<Clock class="mr-1 h-3 w-3" />
											{:else if task.status === 'Completed'}
												<Check class="mr-1 h-3 w-3" />
											{:else if task.status === 'Failed'}
												<X class="mr-1 h-3 w-3" />
											{:else if task.status === 'Cancelled'}
												<Ban class="mr-1 h-3 w-3" />
											{/if}
											{task.status}
										</Badge>
									</td>
									<td class="px-4 py-3">
										<div class="flex items-center gap-3">
											{#if task.status === 'Running'}
												<div class="flex items-center gap-2">
													<div class="h-1.5 w-16 rounded-full bg-muted overflow-hidden">
														<div class="h-full rounded-full bg-amber-500 transition-all" style="width: {task.progress}%"></div>
													</div>
													<span class="text-xs text-muted-foreground">{task.progress}%</span>
												</div>
											{/if}
											{#if task.findings > 0}
												<div class="flex gap-1">
													{#each Object.entries(task.severityBreakdown).filter(([, v]) => v > 0) as [sev, count]}
														<Badge variant="outline" class="text-[10px] {severityColors[sev] ?? ''}">{count} {sev.charAt(0).toUpperCase()}</Badge>
													{/each}
												</div>
											{:else}
												<span class="text-xs text-muted-foreground">—</span>
											{/if}
										</div>
									</td>
									<td class="px-4 py-3 text-sm text-muted-foreground">
										<div class="flex flex-col">
											<span>{task.duration}</span>
											<span class="text-xs">{task.createdAt}</span>
										</div>
									</td>
									<td class="px-4 py-3">
										<!-- svelte-ignore a11y_no_static_element_interactions a11y_no_noninteractive_element_interactions a11y_click_events_have_key_events -->
										<div class="flex items-center gap-1" onclick={(e) => e.stopPropagation()}>
											{#if task.status === 'Completed' || task.status === 'Partial'}
												<Button variant="ghost" size="sm" class="h-7 w-7 p-0" href="/analysis/{task.id}" title="View results">
													<Eye class="h-3.5 w-3.5" />
												</Button>
												<Button variant="ghost" size="sm" class="h-7 w-7 p-0" disabled title="Download">
													<Download class="h-3.5 w-3.5" />
												</Button>
											{:else if task.status === 'Running'}
												<Button variant="ghost" size="sm" class="h-7 w-7 p-0" disabled title="Stop">
													<StopCircle class="h-3.5 w-3.5" />
												</Button>
											{/if}
										</div>
									</td>
								</tr>

								<!-- Subtask Rows -->
								{#if expandedTasks.has(task.id)}
									{#each task.subtasks as sub}
										<tr class="bg-muted/10">
											<td class="px-4 py-2"></td>
											<td class="px-4 py-2"></td>
											<td class="px-4 py-2 pl-8 text-sm text-muted-foreground">{sub.service}</td>
											<td class="px-4 py-2"></td>
											<td class="px-4 py-2"></td>
											<td class="px-4 py-2">
												<Badge variant="outline" class="text-[10px] {statusColors[sub.status] ?? ''}">{sub.status}</Badge>
											</td>
											<td class="px-4 py-2">
												<div class="flex items-center gap-2">
													{#if sub.status === 'Running'}
														<div class="h-1.5 w-12 rounded-full bg-muted overflow-hidden">
															<div class="h-full rounded-full bg-amber-500" style="width: {sub.progress}%"></div>
														</div>
														<span class="text-xs text-muted-foreground">{sub.progress}%</span>
													{/if}
													{#if sub.findings > 0}
														<span class="text-xs font-mono">{sub.findings} findings</span>
													{/if}
												</div>
											</td>
											<td class="px-4 py-2"></td>
											<td class="px-4 py-2"></td>
										</tr>
									{/each}
								{/if}
							{/each}

							{#if filteredTasks.length === 0}
								<tr>
									<td colspan="9" class="px-4 py-12 text-center text-sm text-muted-foreground">
										No tasks match your filters.
									</td>
								</tr>
							{/if}
						</tbody>
					</table>
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Tasks Cards (mobile) -->
	<div class="md:hidden space-y-3">
		{#each filteredTasks.slice(0, perPage) as task (task.id)}
			<div class="border rounded-lg p-3 bg-card">
				<!-- Card header: Task ID + Status -->
				<div class="flex items-center justify-between gap-2 mb-2">
					<div class="flex items-center gap-2 min-w-0">
						{#if task.subtasks.length > 0}
							<button class="shrink-0" onclick={() => toggleExpand(task.id)}>
								{#if expandedTasks.has(task.id)}
									<ChevronDown class="h-4 w-4 text-muted-foreground" />
								{:else}
									<ChevronRight class="h-4 w-4 text-muted-foreground" />
								{/if}
							</button>
						{/if}
						<span class="font-mono text-xs text-muted-foreground truncate">{task.id}</span>
					</div>
					<Badge variant="outline" class="shrink-0 text-[10px] {statusColors[task.status] ?? ''}">
						{#if task.status === 'Running'}
							<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
						{:else if task.status === 'Pending'}
							<Clock class="mr-1 h-3 w-3" />
						{:else if task.status === 'Completed'}
							<Check class="mr-1 h-3 w-3" />
						{:else if task.status === 'Failed'}
							<X class="mr-1 h-3 w-3" />
						{:else if task.status === 'Cancelled'}
							<Ban class="mr-1 h-3 w-3" />
						{/if}
						{task.status}
					</Badge>
				</div>

				<!-- Card body: Model, App, Progress -->
				<div class="space-y-1.5 mb-2">
					<div class="flex items-center justify-between gap-2">
						<a href="/models/{task.modelSlug}" class="text-sm font-medium hover:underline truncate">{task.model}</a>
						<span class="text-xs text-muted-foreground shrink-0">App #{task.appNumber}</span>
					</div>
					<span class="text-xs text-muted-foreground">{task.type}</span>

					{#if task.status === 'Running'}
						<div class="flex items-center gap-2">
							<div class="h-1.5 flex-1 rounded-full bg-muted overflow-hidden">
								<div class="h-full rounded-full bg-amber-500 transition-all" style="width: {task.progress}%"></div>
							</div>
							<span class="text-xs text-muted-foreground shrink-0">{task.progress}%</span>
						</div>
					{/if}

					{#if task.findings > 0}
						<div class="flex flex-wrap gap-1">
							{#each Object.entries(task.severityBreakdown).filter(([, v]) => v > 0) as [sev, count]}
								<Badge variant="outline" class="text-[10px] {severityColors[sev] ?? ''}">{count} {sev.charAt(0).toUpperCase()}</Badge>
							{/each}
						</div>
					{/if}

					<div class="flex flex-wrap gap-1">
						{#each task.tools.slice(0, 3) as tool}
							<Badge variant="secondary" class="text-[10px]">{tool}</Badge>
						{/each}
						{#if task.tools.length > 3}
							<Badge variant="outline" class="text-[10px]">+{task.tools.length - 3}</Badge>
						{/if}
					</div>
				</div>

				<!-- Card footer: Time + Actions -->
				<div class="flex items-center justify-between border-t pt-2">
					<div class="text-xs text-muted-foreground">
						<span>{task.duration}</span>
						<span class="mx-1">·</span>
						<span>{task.createdAt}</span>
					</div>
					<div class="flex items-center gap-1">
						{#if task.status === 'Completed' || task.status === 'Partial'}
							<Button variant="ghost" size="sm" class="h-7 w-7 p-0" href="/analysis/{task.id}" title="View results">
								<Eye class="h-3.5 w-3.5" />
							</Button>
							<Button variant="ghost" size="sm" class="h-7 w-7 p-0" disabled title="Download">
								<Download class="h-3.5 w-3.5" />
							</Button>
						{:else if task.status === 'Running'}
							<Button variant="ghost" size="sm" class="h-7 w-7 p-0" disabled title="Stop">
								<StopCircle class="h-3.5 w-3.5" />
							</Button>
						{/if}
					</div>
				</div>

				<!-- Inline subtasks (expanded) -->
				{#if expandedTasks.has(task.id) && task.subtasks.length > 0}
					<div class="mt-2 border-t pt-2 space-y-2">
						{#each task.subtasks as sub}
							<div class="flex items-center justify-between gap-2 rounded bg-muted/10 px-2 py-1.5">
								<span class="text-xs text-muted-foreground">{sub.service}</span>
								<div class="flex items-center gap-2">
									{#if sub.status === 'Running'}
										<div class="flex items-center gap-1">
											<div class="h-1 w-10 rounded-full bg-muted overflow-hidden">
												<div class="h-full rounded-full bg-amber-500" style="width: {sub.progress}%"></div>
											</div>
											<span class="text-[10px] text-muted-foreground">{sub.progress}%</span>
										</div>
									{/if}
									{#if sub.findings > 0}
										<span class="text-[10px] font-mono">{sub.findings} findings</span>
									{/if}
									<Badge variant="outline" class="text-[10px] {statusColors[sub.status] ?? ''}">{sub.status}</Badge>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/each}

		{#if filteredTasks.length === 0}
			<div class="px-4 py-12 text-center text-sm text-muted-foreground">
				No tasks match your filters.
			</div>
		{/if}
	</div>

	<!-- Pagination -->
	{#if filteredTasks.length > perPage}
		<div class="flex items-center justify-between text-sm text-muted-foreground">
			<span>Showing 1-{Math.min(perPage, filteredTasks.length)} of {filteredTasks.length}</span>
			<div class="flex items-center gap-1">
				<Button variant="outline" size="sm" disabled>Previous</Button>
				<Button variant="outline" size="sm" class="bg-primary/10">1</Button>
				<Button variant="outline" size="sm" disabled>Next</Button>
			</div>
		</div>
	{/if}
</div>
