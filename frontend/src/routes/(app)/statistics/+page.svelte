<script lang="ts">
	import { onMount } from 'svelte';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import Clock from '@lucide/svelte/icons/clock';
	import Cpu from '@lucide/svelte/icons/cpu';
	import LineChart from '@lucide/svelte/icons/line-chart';
	import PieChart from '@lucide/svelte/icons/pie-chart';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import Activity from '@lucide/svelte/icons/activity';
	import Code from '@lucide/svelte/icons/code';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import {
		getStatisticsOverview,
		getStatisticsAnalyzerHealth,
		getStatisticsTrends,
		getStatisticsSeverity,
		getStatisticsModels,
		getStatisticsTools,
		getStatisticsTopFindings,
		getStatisticsCodeGeneration,
		getStatisticsRecentActivity,
		type StatisticsOverview,
		type AnalyzerHealth,
		type AnalysisTrends,
		type SeverityDistribution,
		type ModelComparisonRow,
		type ToolEffectivenessRow,
		type TopFindingRow,
		type CodeGenerationStats,
		type RecentActivityItem,
	} from '$lib/api/client';

	// null = still loading; value = loaded (including empty defaults on error)
	let overviewData = $state<StatisticsOverview | null>(null);
	let healthData = $state<AnalyzerHealth | null>(null);
	let trendsData = $state<AnalysisTrends | null>(null);
	let severityData = $state<SeverityDistribution | null>(null);
	let modelsData = $state<ModelComparisonRow[] | null>(null);
	let toolsData = $state<ToolEffectivenessRow[] | null>(null);
	let topFindingsData = $state<TopFindingRow[] | null>(null);
	let codeGenData = $state<CodeGenerationStats | null>(null);
	let activityData = $state<RecentActivityItem[] | null>(null);

	const severityColors: Record<string, string> = {
		critical: 'bg-red-500/15 text-red-400',
		high: 'bg-orange-500/15 text-orange-400',
		medium: 'bg-amber-500/15 text-amber-500',
		low: 'bg-blue-500/15 text-blue-400',
		info: 'bg-slate-500/15 text-slate-400',
	};

	const severityBarColor: Record<string, string> = {
		critical: 'bg-red-500',
		high: 'bg-orange-500',
		medium: 'bg-amber-500',
		low: 'bg-blue-500',
		info: 'bg-slate-500',
	};

	function scoreColor(val: number, max: number = 10): string {
		const pct = max === 100 ? val : (val / max) * 100;
		if (pct >= 80) return 'text-emerald-500';
		if (pct >= 60) return 'text-amber-500';
		return 'text-red-400';
	}

	function fmtDuration(seconds: number): string {
		if (!seconds) return '—';
		if (seconds < 60) return `${seconds.toFixed(0)}s`;
		const m = Math.floor(seconds / 60);
		const s = Math.round(seconds - m * 60);
		return `${m}m ${s}s`;
	}

	function fmtNumber(n: number): string {
		return n.toLocaleString();
	}

	function fmtCost(usd: number): string {
		if (!usd) return '$0.00';
		if (usd < 1) return `$${usd.toFixed(4)}`;
		return `$${usd.toFixed(2)}`;
	}

	function dayLabel(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString(undefined, { weekday: 'short' });
	}

	let trendMax = $derived(
		Math.max(1, ...(trendsData?.series ?? []).map((p) => p.total)),
	);

	let kpis = $derived(
		overviewData && codeGenData
			? [
					{
						title: 'Total Analyses',
						icon: BarChart3,
						color: 'text-blue-500',
						bg: 'bg-blue-500/10',
						value: fmtNumber(overviewData.total_analyses),
						delta: `${overviewData.analyses_completed} completed`,
					},
					{
						title: 'Success Rate',
						icon: TrendingUp,
						color: 'text-emerald-500',
						bg: 'bg-emerald-500/10',
						value: `${overviewData.analyses_success_rate}%`,
						delta: `Apps: ${overviewData.apps_success_rate}%`,
					},
					{
						title: 'Avg. Duration',
						icon: Clock,
						color: 'text-amber-500',
						bg: 'bg-amber-500/10',
						value: fmtDuration(overviewData.avg_analysis_seconds),
						delta: 'per analysis',
					},
					{
						title: 'Active Models',
						icon: Cpu,
						color: 'text-violet-500',
						bg: 'bg-violet-500/10',
						value: fmtNumber(overviewData.models_in_use),
						delta: `${codeGenData.by_provider.length} providers`,
					},
				]
			: [],
	);

	onMount(() => {
		getStatisticsOverview()
			.then((d) => (overviewData = d))
			.catch(() => (overviewData = {} as StatisticsOverview));
		getStatisticsAnalyzerHealth()
			.then((d) => (healthData = d))
			.catch(() => (healthData = { total: 0, online: 0, offline: 0, analyzers: [] }));
		getStatisticsTrends()
			.then((d) => (trendsData = d))
			.catch(() => (trendsData = { days: 7, total: 0, series: [] }));
		getStatisticsSeverity()
			.then((d) => (severityData = d))
			.catch(() => (severityData = { total: 0, distribution: [] }));
		getStatisticsModels()
			.then((d) => (modelsData = d))
			.catch(() => (modelsData = []));
		getStatisticsTools()
			.then((d) => (toolsData = d))
			.catch(() => (toolsData = []));
		getStatisticsTopFindings()
			.then((d) => (topFindingsData = d))
			.catch(() => (topFindingsData = []));
		getStatisticsCodeGeneration()
			.then((d) => (codeGenData = d))
			.catch(() => (codeGenData = {} as CodeGenerationStats));
		getStatisticsRecentActivity()
			.then((d) => (activityData = d))
			.catch(() => (activityData = []));
	});
</script>

<svelte:head>
	<title>Statistics - LLM Lab</title>
</svelte:head>

<div class="space-y-4 sm:space-y-6">
	<div class="page-header">
		<h1>Statistics</h1>
		<p>Platform-wide analytics and performance metrics.</p>
	</div>

	<!-- System Health -->
	{#if healthData === null}
		<div class="h-12 animate-pulse rounded-lg border bg-muted/40"></div>
	{:else}
		{@const healthy = healthData.offline === 0}
		<div
			class="flex flex-wrap items-center gap-3 rounded-lg border px-4 py-3 {healthy
				? 'border-emerald-500/30 bg-emerald-500/5'
				: 'border-amber-500/30 bg-amber-500/5'}"
		>
			<Activity class="h-5 w-5 {healthy ? 'text-emerald-500' : 'text-amber-500'}" />
			<div class="flex-1">
				<span class="text-sm font-medium {healthy ? 'text-emerald-500' : 'text-amber-500'}">
					{healthy ? 'System Healthy' : 'Degraded'}
				</span>
				<span class="ml-2 text-xs text-muted-foreground">
					{healthData.online}/{healthData.total} analyzers online
				</span>
			</div>
			<Badge
				variant="outline"
				class="border-emerald-500/30 bg-emerald-500/15 text-[10px] text-emerald-500"
			>
				{healthy ? 'Operational' : 'Partial'}
			</Badge>
		</div>
	{/if}

	<!-- KPIs -->
	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#if kpis.length > 0}
			{#each kpis as kpi}
				<div class="kpi-card">
					<div class="text-xs text-muted-foreground uppercase tracking-wider">{kpi.title}</div>
					<div class="text-2xl font-semibold font-mono tabular-nums">{kpi.value}</div>
					<div class="text-xs text-muted-foreground">{kpi.delta}</div>
				</div>
			{/each}
		{:else}
			{#each Array(4) as _, i (i)}
				<div class="kpi-card animate-pulse">
					<div class="h-3 w-24 rounded bg-muted/60"></div>
					<div class="h-8 w-16 rounded bg-muted/60 mt-1"></div>
					<div class="h-3 w-20 rounded bg-muted/40 mt-1"></div>
				</div>
			{/each}
		{/if}
	</div>

	<!-- Charts Row -->
	<div class="grid gap-4 lg:grid-cols-2">
		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<LineChart class="h-5 w-5 text-muted-foreground" />
					<Card.Title>Analysis Trends</Card.Title>
				</div>
			</Card.Header>
			<Card.Content>
				{#if trendsData === null}
					<div class="flex h-40 items-center justify-center">
						<LoaderCircle class="h-5 w-5 animate-spin text-muted-foreground" />
					</div>
				{:else}
					<div class="flex h-40 items-end gap-1.5">
						{#each trendsData.series as point}
							<div class="flex flex-1 flex-col items-center gap-1">
								<div
									class="w-full rounded-t bg-blue-500/70 transition-all"
									style="height: {(point.total / trendMax) * 100}%"
								></div>
								<span class="text-[9px] text-muted-foreground">{dayLabel(point.date)}</span>
							</div>
						{/each}
					</div>
					<p class="mt-3 text-center text-xs text-muted-foreground">
						Analyses run in last {trendsData.days} days: {trendsData.total}
					</p>
				{/if}
			</Card.Content>
		</Card.Root>

		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<PieChart class="h-5 w-5 text-muted-foreground" />
					<Card.Title>Severity Distribution</Card.Title>
				</div>
			</Card.Header>
			<Card.Content>
				{#if severityData === null}
					<div class="flex items-center justify-center py-8">
						<LoaderCircle class="h-5 w-5 animate-spin text-muted-foreground" />
					</div>
				{:else}
					<div class="space-y-3">
						{#each severityData.distribution as sev}
							<div class="flex items-center gap-2 text-sm">
								<span class="w-14 text-xs capitalize text-muted-foreground">{sev.severity}</span>
								<div class="h-3 flex-1 overflow-hidden rounded-full bg-muted">
									<div
										class="h-full rounded-full {severityBarColor[sev.severity] ?? 'bg-slate-500'}"
										style="width: {sev.percent}%"
									></div>
								</div>
								<span class="w-10 text-right font-mono text-xs">{sev.count}</span>
								<span class="w-8 text-right text-[10px] text-muted-foreground">{sev.percent}%</span>
							</div>
						{/each}
					</div>
					<p class="mt-3 text-center text-xs text-muted-foreground">
						Total findings: {severityData.total}
					</p>
				{/if}
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Model Comparison -->
	<Card.Root>
		<Card.Header>
			<Card.Title>Model Comparison</Card.Title>
		</Card.Header>
		<Card.Content class="p-0">
			{#if modelsData === null}
				<div class="flex items-center justify-center py-10">
					<LoaderCircle class="h-5 w-5 animate-spin text-muted-foreground" />
				</div>
			{:else if modelsData.length === 0}
				<p class="p-6 text-center text-sm text-muted-foreground">No model data yet.</p>
			{:else}
				<div class="table-scroll-wrapper">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b bg-muted/40 sticky top-0 z-10">
								<th class="px-3 py-2.5 text-left text-xs font-medium text-muted-foreground whitespace-nowrap">Model</th>
								<th class="px-3 py-2.5 text-right text-xs font-medium text-muted-foreground whitespace-nowrap">Apps</th>
								<th class="px-3 py-2.5 text-right text-xs font-medium text-muted-foreground whitespace-nowrap">Security</th>
								<th class="px-3 py-2.5 text-right text-xs font-medium text-muted-foreground whitespace-nowrap">Performance</th>
								<th class="px-3 py-2.5 text-right text-xs font-medium text-muted-foreground whitespace-nowrap">Quality</th>
								<th class="px-3 py-2.5 text-right text-xs font-medium text-muted-foreground whitespace-nowrap">MSS</th>
							</tr>
						</thead>
						<tbody>
							{#each modelsData as m, i}
								<tr class="border-b transition-colors hover:bg-muted/50 {i % 2 === 0 ? '' : 'bg-muted/15'}">
									<td class="px-3 py-2 align-top">
										<div>
											<span class="font-medium text-sm">{m.name}</span>
											<div class="text-[10px] text-muted-foreground">{m.provider}</div>
										</div>
									</td>
									<td class="px-3 py-2 text-right align-top font-mono tabular-nums text-xs">{m.apps}</td>
									<td class="px-3 py-2 text-right align-top font-mono tabular-nums text-xs {scoreColor(m.security)}">{m.security.toFixed(1)}</td>
									<td class="px-3 py-2 text-right align-top font-mono tabular-nums text-xs {scoreColor(m.performance, 100)}">{m.performance}</td>
									<td class="px-3 py-2 text-right align-top font-mono tabular-nums text-xs {scoreColor(m.quality)}">{m.quality.toFixed(1)}</td>
									<td class="px-3 py-2 text-right align-top font-mono tabular-nums text-xs font-bold {scoreColor(m.mss, 100)}">{m.mss.toFixed(1)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<!-- Tool Effectiveness + Top Findings -->
	<div class="grid gap-4 lg:grid-cols-3">
		<div class="lg:col-span-2">
			<Card.Root>
				<Card.Header>
					<Card.Title>Tool Effectiveness</Card.Title>
				</Card.Header>
				<Card.Content class="p-0">
					{#if toolsData === null}
						<div class="flex items-center justify-center py-10">
							<LoaderCircle class="h-5 w-5 animate-spin text-muted-foreground" />
						</div>
					{:else if toolsData.length === 0}
						<p class="p-6 text-center text-sm text-muted-foreground">No analyzer runs yet.</p>
					{:else}
						<div class="table-scroll-wrapper">
							<table class="w-full text-sm">
								<thead>
									<tr class="border-b bg-muted/40 sticky top-0 z-10">
										<th class="px-3 py-2.5 text-left text-xs font-medium text-muted-foreground whitespace-nowrap">Tool</th>
										<th class="px-3 py-2.5 text-left text-xs font-medium text-muted-foreground whitespace-nowrap">Type</th>
										<th class="px-3 py-2.5 text-right text-xs font-medium text-muted-foreground whitespace-nowrap">Scans</th>
										<th class="px-3 py-2.5 text-right text-xs font-medium text-muted-foreground whitespace-nowrap">Findings</th>
										<th class="px-3 py-2.5 text-right text-xs font-medium text-muted-foreground whitespace-nowrap">Avg/Scan</th>
										<th class="px-3 py-2.5 text-left text-xs font-medium text-muted-foreground whitespace-nowrap">Top Rule</th>
									</tr>
								</thead>
								<tbody>
									{#each toolsData as t, i}
										<tr class="border-b transition-colors hover:bg-muted/50 {i % 2 === 0 ? '' : 'bg-muted/15'}">
											<td class="px-3 py-2 align-top text-xs font-medium">{t.name}</td>
											<td class="px-3 py-2 align-top">
												<Badge variant="secondary" class="text-[10px] capitalize">{t.type}</Badge>
											</td>
											<td class="px-3 py-2 text-right align-top font-mono tabular-nums text-xs">{t.scans}</td>
											<td class="px-3 py-2 text-right align-top font-mono tabular-nums text-xs">{t.findings}</td>
											<td class="px-3 py-2 text-right align-top font-mono tabular-nums text-xs">{t.avg_per_scan.toFixed(1)}</td>
											<td class="px-3 py-2 align-top font-mono text-[10px] text-muted-foreground">
												{t.top_rule || '—'}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>

		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<AlertTriangle class="h-4 w-4 text-amber-500" />
					<Card.Title>Top Findings</Card.Title>
				</div>
			</Card.Header>
			<Card.Content class="space-y-3">
				{#if topFindingsData === null}
					<div class="flex items-center justify-center py-6">
						<LoaderCircle class="h-5 w-5 animate-spin text-muted-foreground" />
					</div>
				{:else if topFindingsData.length === 0}
					<p class="text-center text-xs text-muted-foreground">No findings yet.</p>
				{:else}
					{#each topFindingsData as f}
						<div class="flex items-start gap-2">
							<Badge
								variant="outline"
								class="shrink-0 text-[9px] {severityColors[f.severity] ?? ''}"
							>
								{f.severity}
							</Badge>
							<div class="flex-1 text-xs">{f.title}</div>
							<span class="shrink-0 font-mono text-xs text-muted-foreground">{f.count}</span>
						</div>
					{/each}
				{/if}
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Code Generation + Recent Activity -->
	<div class="grid gap-4 lg:grid-cols-3">
		<div class="lg:col-span-2">
			<Card.Root>
				<Card.Header>
					<div class="flex items-center gap-2">
						<Code class="h-4 w-4 text-muted-foreground" />
						<Card.Title>Code Generation Stats</Card.Title>
					</div>
				</Card.Header>
				<Card.Content>
					{#if codeGenData === null}
						<div class="flex items-center justify-center py-8">
							<LoaderCircle class="h-5 w-5 animate-spin text-muted-foreground" />
						</div>
					{:else}
						<div class="grid gap-4 sm:grid-cols-3">
							{#each [
								{ label: 'Total Apps Generated', value: fmtNumber(codeGenData.total_apps) },
								{ label: 'Success Rate', value: `${codeGenData.success_rate}%` },
								{ label: 'Avg Gen Time', value: fmtDuration(codeGenData.avg_duration_seconds) },
								{ label: 'Lines of Code', value: fmtNumber(codeGenData.total_lines_of_code) },
								{ label: 'Total Tokens', value: fmtNumber(codeGenData.total_tokens) },
								{ label: 'Total Cost', value: fmtCost(codeGenData.total_cost_usd) },
							] as stat}
								<div class="kpi-card">
									<div class="text-xs text-muted-foreground uppercase tracking-wider">{stat.label}</div>
									<div class="text-2xl font-semibold font-mono tabular-nums">{stat.value}</div>
								</div>
							{/each}
						</div>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>

		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<Activity class="h-4 w-4 text-muted-foreground" />
					<Card.Title>Recent Activity</Card.Title>
				</div>
			</Card.Header>
			<Card.Content class="space-y-2">
				{#if activityData === null}
					<div class="flex items-center justify-center py-6">
						<LoaderCircle class="h-5 w-5 animate-spin text-muted-foreground" />
					</div>
				{:else if activityData.length === 0}
					<p class="text-center text-xs text-muted-foreground">No recent activity.</p>
				{:else}
					{#each activityData.slice(0, 8) as item}
						<div class="flex items-center justify-between gap-2 text-xs">
							<div class="flex min-w-0 items-center gap-2">
								<Badge variant="outline" class="text-[9px] capitalize">{item.kind}</Badge>
								<span class="truncate">{item.title}</span>
							</div>
							<span class="shrink-0 text-[10px] text-muted-foreground">
								{new Date(item.created_at).toLocaleDateString()}
							</span>
						</div>
					{/each}
				{/if}
			</Card.Content>
		</Card.Root>
	</div>
</div>
