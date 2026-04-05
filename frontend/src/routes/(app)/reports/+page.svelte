<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import Plus from '@lucide/svelte/icons/plus';
	import Search from '@lucide/svelte/icons/search';
	import Eye from '@lucide/svelte/icons/eye';
	import Download from '@lucide/svelte/icons/download';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Trash2 from '@lucide/svelte/icons/trash-2';
	import Brain from '@lucide/svelte/icons/brain';
	import GitCompareArrows from '@lucide/svelte/icons/git-compare-arrows';
	import Wrench from '@lucide/svelte/icons/wrench';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import Layers from '@lucide/svelte/icons/layers';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';

	let searchQuery = $state('');
	let typeFilter = $state('all');
	let statusFilter = $state('all');
	let perPage = $state(25);

	const reports = [
		{ id: 'rpt-001', title: 'GPT-4o Full Analysis', description: 'Comprehensive analysis of GPT-4o across all applications', type: 'model_analysis', config: 'gpt-4o', status: 'completed', createdAt: '2025-03-19 14:30', progress: 100 },
		{ id: 'rpt-002', title: 'Todo App Template Comparison', description: 'Cross-model comparison on the Todo Application template', type: 'template_comparison', config: 'todo-app', status: 'completed', createdAt: '2025-03-18 16:45', progress: 100 },
		{ id: 'rpt-003', title: 'Security Tool Analysis', description: 'Effectiveness analysis of security scanning tools', type: 'tool_analysis', config: 'bandit, zap', status: 'generating', createdAt: '2025-03-19 15:00', progress: 65 },
		{ id: 'rpt-004', title: 'Weekly Generation Report', description: 'Generation success/failure patterns for the last 7 days', type: 'generation_analytics', config: '7 days', status: 'completed', createdAt: '2025-03-17 09:00', progress: 100 },
		{ id: 'rpt-005', title: 'Platform Comprehensive Report', description: 'Full platform-wide analysis including all models and tools', type: 'comprehensive', config: 'All', status: 'failed', createdAt: '2025-03-16 11:30', progress: 40 },
		{ id: 'rpt-006', title: 'Claude 3.5 Sonnet Analysis', description: 'Aggregate analysis for Claude 3.5 Sonnet model', type: 'model_analysis', config: 'claude-3-5-sonnet', status: 'completed', createdAt: '2025-03-15 10:00', progress: 100 },
		{ id: 'rpt-007', title: 'Performance Tool Report', description: 'Load testing and lighthouse tool performance', type: 'tool_analysis', config: 'lighthouse, load-test', status: 'generating', createdAt: '2025-03-19 15:10', progress: 30 },
	];

	const typeConfig: Record<string, { label: string; color: string; icon: typeof Brain }> = {
		model_analysis: { label: 'Model Analysis', color: 'bg-blue-500/15 text-blue-400 border-blue-500/30', icon: Brain },
		template_comparison: { label: 'Template Comparison', color: 'bg-purple-500/15 text-purple-400 border-purple-500/30', icon: GitCompareArrows },
		tool_analysis: { label: 'Tool Analysis', color: 'bg-teal-500/15 text-teal-400 border-teal-500/30', icon: Wrench },
		generation_analytics: { label: 'Generation Analytics', color: 'bg-orange-500/15 text-orange-400 border-orange-500/30', icon: TrendingUp },
		comprehensive: { label: 'Comprehensive', color: 'bg-red-500/15 text-red-400 border-red-500/30', icon: Layers },
	};

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		generating: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		failed: 'bg-red-500/15 text-red-400 border-red-500/30',
	};

	const filteredReports = $derived(reports.filter(r =>
		(typeFilter === 'all' || r.type === typeFilter) &&
		(statusFilter === 'all' || r.status === statusFilter) &&
		(searchQuery === '' || r.title.toLowerCase().includes(searchQuery.toLowerCase()) || r.description.toLowerCase().includes(searchQuery.toLowerCase()))
	));

	const completedCount = $derived(reports.filter(r => r.status === 'completed').length);
	const generatingCount = $derived(reports.filter(r => r.status === 'generating').length);
	const failedCount = $derived(reports.filter(r => r.status === 'failed').length);
</script>

<svelte:head>
	<title>Reports - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Reports</h1>
			<p class="mt-1 text-sm text-muted-foreground">Generate and view analysis reports.</p>
		</div>
		<Button href="/reports/create">
			<Plus class="mr-1.5 h-4 w-4" />
			New Report
		</Button>
	</div>

	<!-- Stats -->
	<div class="flex flex-wrap gap-2">
		<Badge variant="outline">{reports.length} total</Badge>
		<Badge variant="outline" class="bg-emerald-500/15 text-emerald-500 border-emerald-500/30">{completedCount} completed</Badge>
		{#if generatingCount > 0}
			<Badge variant="outline" class="bg-amber-500/15 text-amber-500 border-amber-500/30">
				<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
				{generatingCount} generating
			</Badge>
		{/if}
		{#if failedCount > 0}
			<Badge variant="outline" class="bg-red-500/15 text-red-400 border-red-500/30">{failedCount} failed</Badge>
		{/if}
	</div>

	<!-- Filters -->
	<div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
		<div class="relative sm:flex-1 sm:max-w-sm">
			<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
			<Input bind:value={searchQuery} placeholder="Search reports..." class="h-9 pl-8 text-sm" />
		</div>
		<select bind:value={typeFilter} class="h-9 rounded-md border bg-background px-3 text-sm">
			<option value="all">All Types</option>
			<option value="model_analysis">Model Analysis</option>
			<option value="template_comparison">Template Comparison</option>
			<option value="tool_analysis">Tool Analysis</option>
			<option value="generation_analytics">Generation Analytics</option>
			<option value="comprehensive">Comprehensive</option>
		</select>
		<select bind:value={statusFilter} class="h-9 rounded-md border bg-background px-3 text-sm">
			<option value="all">All Statuses</option>
			<option value="completed">Completed</option>
			<option value="generating">Generating</option>
			<option value="failed">Failed</option>
		</select>
		<select bind:value={perPage} class="h-9 rounded-md border bg-background px-2 text-sm">
			<option value={10}>10 / page</option>
			<option value={25}>25 / page</option>
			<option value={50}>50 / page</option>
		</select>
	</div>

	<!-- Table -->
	<Card.Root>
		<Card.Content class="p-0">
			<div class="table-scroll-wrapper">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b bg-muted/30">
						<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Title</th>
						<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground hide-mobile">Type</th>
						<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground hide-mobile">Config</th>
						<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
						<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
						<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#each filteredReports.slice(0, perPage) as report}
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-3">
								<div>
									{#if report.status === 'completed'}
										<a href="/reports/{report.id}" class="font-medium hover:underline">{report.title}</a>
									{:else}
										<span class="font-medium">{report.title}</span>
									{/if}
									<div class="text-xs text-muted-foreground line-clamp-1">{report.description}</div>
								</div>
							</td>
							<td class="px-4 py-3 hide-mobile">
								<Badge variant="outline" class="text-[10px] {typeConfig[report.type]?.color ?? ''}">
									{typeConfig[report.type]?.label ?? report.type}
								</Badge>
							</td>
							<td class="px-4 py-3 hide-mobile">
								<Badge variant="secondary" class="text-[10px] font-mono">{report.config}</Badge>
							</td>
							<td class="px-4 py-3">
								<div class="flex items-center gap-2">
									<Badge variant="outline" class="text-[10px] {statusColors[report.status] ?? ''}">
										{#if report.status === 'completed'}<Check class="mr-1 h-3 w-3" />
										{:else if report.status === 'generating'}<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
										{:else if report.status === 'failed'}<X class="mr-1 h-3 w-3" />{/if}
										{report.status}
									</Badge>
									{#if report.status === 'generating'}
										<span class="font-mono text-[10px] text-muted-foreground">{report.progress}%</span>
									{/if}
								</div>
							</td>
							<td class="px-4 py-3 text-xs text-muted-foreground font-mono">{report.createdAt}</td>
							<td class="px-4 py-3">
								<div class="flex gap-1">
									<Button variant="ghost" size="sm" class="h-7 w-7 p-0" disabled={report.status !== 'completed'} href={report.status === 'completed' ? `/reports/${report.id}` : undefined}>
										<Eye class="h-3.5 w-3.5" />
									</Button>
									<Button variant="ghost" size="sm" class="h-7 w-7 p-0" disabled>
										<Download class="h-3.5 w-3.5" />
									</Button>
									<Button variant="ghost" size="sm" class="h-7 w-7 p-0" disabled>
										<RefreshCw class="h-3.5 w-3.5" />
									</Button>
									<Button variant="ghost" size="sm" class="h-7 w-7 p-0 text-red-400 hover:text-red-300" disabled>
										<Trash2 class="h-3.5 w-3.5" />
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

	<div class="text-sm text-muted-foreground">Showing {Math.min(filteredReports.length, perPage)} of {filteredReports.length} reports</div>
</div>
