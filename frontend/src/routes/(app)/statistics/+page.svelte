<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import Clock from '@lucide/svelte/icons/clock';
	import Cpu from '@lucide/svelte/icons/cpu';
	import LineChart from '@lucide/svelte/icons/line-chart';
	import PieChart from '@lucide/svelte/icons/pie-chart';

	const kpis = [
		{ title: 'Total Analyses', icon: BarChart3, color: 'text-blue-500', bg: 'bg-blue-500/10' },
		{ title: 'Success Rate', icon: TrendingUp, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
		{ title: 'Avg. Duration', icon: Clock, color: 'text-amber-500', bg: 'bg-amber-500/10' },
		{ title: 'Active Models', icon: Cpu, color: 'text-violet-500', bg: 'bg-violet-500/10' }
	];
</script>

<svelte:head>
	<title>Statistics - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="page-header">
		<h1>Statistics</h1>
		<p>Platform-wide analytics and performance metrics.</p>
	</div>

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each kpis as kpi}
			<Card.Root>
				<Card.Header class="pb-2">
					<div class="flex items-center justify-between">
						<Card.Title class="text-sm font-medium text-muted-foreground">{kpi.title}</Card.Title>
						<div class="rounded-lg p-2 {kpi.bg}">
							<kpi.icon class="h-4 w-4 {kpi.color}" />
						</div>
					</div>
				</Card.Header>
				<Card.Content>
					<div class="text-2xl font-bold">&mdash;</div>
					<p class="text-xs text-muted-foreground">No data yet</p>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>

	<div class="grid gap-4 lg:grid-cols-2">
		<Card.Root>
			<Card.Header>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<LineChart class="h-5 w-5 text-muted-foreground" />
						<Card.Title>Analysis Trends</Card.Title>
					</div>
					<Badge variant="outline">Coming Soon</Badge>
				</div>
			</Card.Header>
			<Card.Content>
				<div class="flex h-48 flex-col items-center justify-center gap-2 rounded-lg border border-dashed bg-muted/20">
					<LineChart class="h-8 w-8 text-muted-foreground/40" />
					<p class="text-sm text-muted-foreground">Trend data will appear here</p>
				</div>
			</Card.Content>
		</Card.Root>

		<Card.Root>
			<Card.Header>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<PieChart class="h-5 w-5 text-muted-foreground" />
						<Card.Title>Severity Distribution</Card.Title>
					</div>
					<Badge variant="outline">Coming Soon</Badge>
				</div>
			</Card.Header>
			<Card.Content>
				<div class="flex h-48 flex-col items-center justify-center gap-2 rounded-lg border border-dashed bg-muted/20">
					<PieChart class="h-8 w-8 text-muted-foreground/40" />
					<p class="text-sm text-muted-foreground">Distribution chart will appear here</p>
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<Card.Title>Model Comparison</Card.Title>
				<Badge variant="outline">Coming Soon</Badge>
			</div>
		</Card.Header>
		<Card.Content class="p-0">
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="p-4 text-left font-medium text-muted-foreground">Model</th>
							<th class="p-4 text-left font-medium text-muted-foreground">Apps Generated</th>
							<th class="p-4 text-left font-medium text-muted-foreground">Avg. Security</th>
							<th class="p-4 text-left font-medium text-muted-foreground">Avg. Performance</th>
							<th class="p-4 text-left font-medium text-muted-foreground">Overall Score</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each Array(4) as _}
							<tr class="transition-colors hover:bg-muted/30">
								<td class="p-4"><Skeleton class="h-4 w-28" /></td>
								<td class="p-4"><Skeleton class="h-4 w-8" /></td>
								<td class="p-4"><Skeleton class="h-4 w-12" /></td>
								<td class="p-4"><Skeleton class="h-4 w-12" /></td>
								<td class="p-4"><Skeleton class="h-4 w-12" /></td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</Card.Content>
	</Card.Root>
</div>
