<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import Clock from '@lucide/svelte/icons/clock';
	import Cpu from '@lucide/svelte/icons/cpu';
	import LineChart from '@lucide/svelte/icons/line-chart';
	import PieChart from '@lucide/svelte/icons/pie-chart';
	import Shield from '@lucide/svelte/icons/shield';
	import CheckCircle from '@lucide/svelte/icons/check-circle';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import HardDrive from '@lucide/svelte/icons/hard-drive';
	import Activity from '@lucide/svelte/icons/activity';
	import Code from '@lucide/svelte/icons/code';

	const kpis = [
		{ title: 'Total Analyses', icon: BarChart3, color: 'text-blue-500', bg: 'bg-blue-500/10', value: '156', delta: '+12 this week', up: true },
		{ title: 'Success Rate', icon: TrendingUp, color: 'text-emerald-500', bg: 'bg-emerald-500/10', value: '87.2%', delta: '+2.1% vs last', up: true },
		{ title: 'Avg. Duration', icon: Clock, color: 'text-amber-500', bg: 'bg-amber-500/10', value: '4m 32s', delta: '-18s vs last', up: true },
		{ title: 'Active Models', icon: Cpu, color: 'text-violet-500', bg: 'bg-violet-500/10', value: '8', delta: '6 providers', up: false },
	];

	const modelComparison = [
		{ name: 'Claude 3.5 Sonnet', provider: 'Anthropic', apps: 8, security: 8.4, performance: 82, quality: 8.6, mss: 85.1 },
		{ name: 'GPT-4o', provider: 'OpenAI', apps: 8, security: 7.8, performance: 85, quality: 8.1, mss: 82.4 },
		{ name: 'Gemini 2.0 Flash', provider: 'Google', apps: 8, security: 7.2, performance: 88, quality: 7.4, mss: 78.3 },
		{ name: 'DeepSeek V3', provider: 'DeepSeek', apps: 8, security: 7.1, performance: 79, quality: 7.8, mss: 76.8 },
		{ name: 'Claude 3.5 Haiku', provider: 'Anthropic', apps: 8, security: 7.0, performance: 78, quality: 7.2, mss: 73.9 },
		{ name: 'Mistral Large', provider: 'Mistral', apps: 7, security: 6.6, performance: 76, quality: 7.1, mss: 72.1 },
	];

	const toolEffectiveness = [
		{ name: 'Bandit', category: 'Security', scans: 48, findings: 312, avgPerScan: 6.5, topRule: 'B301 (pickle)' },
		{ name: 'Semgrep', category: 'Security', scans: 48, findings: 186, avgPerScan: 3.9, topRule: 'sql-injection' },
		{ name: 'ZAP', category: 'Dynamic', scans: 42, findings: 94, avgPerScan: 2.2, topRule: 'XSS-Reflected' },
		{ name: 'ESLint', category: 'Quality', scans: 48, findings: 523, avgPerScan: 10.9, topRule: 'no-unused-vars' },
		{ name: 'Ruff', category: 'Quality', scans: 48, findings: 189, avgPerScan: 3.9, topRule: 'F401 (unused)' },
		{ name: 'Lighthouse', category: 'Performance', scans: 42, findings: 168, avgPerScan: 4.0, topRule: 'render-blocking' },
	];

	const topFindings = [
		{ severity: 'critical', count: 24, label: 'Use of pickle / unsafe deserialization' },
		{ severity: 'critical', count: 18, label: 'SQL injection via string formatting' },
		{ severity: 'high', count: 31, label: 'Hardcoded credentials in source' },
		{ severity: 'high', count: 27, label: 'Missing CSRF protection' },
		{ severity: 'medium', count: 45, label: 'Missing Content-Security-Policy' },
	];

	const severityColors: Record<string, string> = {
		critical: 'bg-red-500/15 text-red-400',
		high: 'bg-orange-500/15 text-orange-400',
		medium: 'bg-amber-500/15 text-amber-500',
	};

	function scoreColor(val: number, max: number = 10): string {
		const pct = max === 100 ? val : (val / max) * 100;
		if (pct >= 80) return 'text-emerald-500';
		if (pct >= 60) return 'text-amber-500';
		return 'text-red-400';
	}
</script>

<svelte:head>
	<title>Statistics - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight">Statistics</h1>
		<p class="mt-1 text-sm text-muted-foreground">Platform-wide analytics and performance metrics.</p>
	</div>

	<!-- System Health -->
	<div class="flex items-center gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-4 py-3">
		<Activity class="h-5 w-5 text-emerald-500" />
		<div class="flex-1">
			<span class="text-sm font-medium text-emerald-500">System Healthy</span>
			<span class="ml-2 text-xs text-muted-foreground">All 4 analyzers online &middot; Redis connected &middot; Celery: 2 workers active</span>
		</div>
		<Badge variant="outline" class="text-[10px] bg-emerald-500/15 text-emerald-500 border-emerald-500/30">Operational</Badge>
	</div>

	<!-- KPIs -->
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
					<div class="text-2xl font-bold">{kpi.value}</div>
					<p class="text-xs {kpi.up ? 'text-emerald-500' : 'text-muted-foreground'}">{kpi.delta}</p>
				</Card.Content>
			</Card.Root>
		{/each}
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
				<!-- Simple bar chart placeholder with mock data bars -->
				<div class="flex items-end gap-1.5 h-40">
					{#each [18, 22, 15, 28, 20, 24, 29] as val, i}
						<div class="flex-1 flex flex-col items-center gap-1">
							<div class="w-full rounded-t bg-blue-500/70 transition-all" style="height: {(val / 30) * 100}%"></div>
							<span class="text-[9px] text-muted-foreground">{['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i]}</span>
						</div>
					{/each}
				</div>
				<p class="mt-3 text-center text-xs text-muted-foreground">Analyses run this week: 156</p>
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
				<div class="space-y-3">
					{#each [
						{ label: 'Critical', count: 42, pct: 8, color: 'bg-red-500' },
						{ label: 'High', count: 98, pct: 19, color: 'bg-orange-500' },
						{ label: 'Medium', count: 187, pct: 36, color: 'bg-amber-500' },
						{ label: 'Low', count: 134, pct: 26, color: 'bg-blue-500' },
						{ label: 'Info', count: 57, pct: 11, color: 'bg-slate-500' },
					] as sev}
						<div class="flex items-center gap-2 text-sm">
							<span class="w-14 text-xs text-muted-foreground">{sev.label}</span>
							<div class="flex-1 h-3 bg-muted rounded-full overflow-hidden">
								<div class="h-full {sev.color} rounded-full" style="width: {sev.pct}%"></div>
							</div>
							<span class="w-10 text-right text-xs font-mono">{sev.count}</span>
							<span class="w-8 text-right text-[10px] text-muted-foreground">{sev.pct}%</span>
						</div>
					{/each}
				</div>
				<p class="mt-3 text-center text-xs text-muted-foreground">Total findings: 518</p>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Model Comparison -->
	<Card.Root>
		<Card.Header>
			<Card.Title>Model Comparison</Card.Title>
		</Card.Header>
		<Card.Content class="p-0">
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="p-3 text-left text-xs font-medium text-muted-foreground">Model</th>
							<th class="p-3 text-left text-xs font-medium text-muted-foreground">Apps</th>
							<th class="p-3 text-left text-xs font-medium text-muted-foreground">Security</th>
							<th class="p-3 text-left text-xs font-medium text-muted-foreground">Performance</th>
							<th class="p-3 text-left text-xs font-medium text-muted-foreground">Quality</th>
							<th class="p-3 text-left text-xs font-medium text-muted-foreground">MSS</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each modelComparison as m}
							<tr class="hover:bg-muted/30">
								<td class="p-3">
									<div>
										<span class="font-medium">{m.name}</span>
										<div class="text-[10px] text-muted-foreground">{m.provider}</div>
									</div>
								</td>
								<td class="p-3 text-xs">{m.apps}</td>
								<td class="p-3 font-mono text-xs {scoreColor(m.security)}">{m.security.toFixed(1)}</td>
								<td class="p-3 font-mono text-xs {scoreColor(m.performance, 100)}">{m.performance}</td>
								<td class="p-3 font-mono text-xs {scoreColor(m.quality)}">{m.quality.toFixed(1)}</td>
								<td class="p-3 font-mono text-xs font-bold {scoreColor(m.mss, 100)}">{m.mss.toFixed(1)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
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
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="p-3 text-left text-xs font-medium text-muted-foreground">Tool</th>
								<th class="p-3 text-left text-xs font-medium text-muted-foreground">Category</th>
								<th class="p-3 text-left text-xs font-medium text-muted-foreground">Scans</th>
								<th class="p-3 text-left text-xs font-medium text-muted-foreground">Findings</th>
								<th class="p-3 text-left text-xs font-medium text-muted-foreground">Avg/Scan</th>
								<th class="p-3 text-left text-xs font-medium text-muted-foreground">Top Rule</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each toolEffectiveness as t}
								<tr class="hover:bg-muted/30">
									<td class="p-3 font-medium text-xs">{t.name}</td>
									<td class="p-3"><Badge variant="secondary" class="text-[10px]">{t.category}</Badge></td>
									<td class="p-3 font-mono text-xs">{t.scans}</td>
									<td class="p-3 font-mono text-xs">{t.findings}</td>
									<td class="p-3 font-mono text-xs">{t.avgPerScan.toFixed(1)}</td>
									<td class="p-3 font-mono text-[10px] text-muted-foreground">{t.topRule}</td>
								</tr>
							{/each}
						</tbody>
					</table>
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
				{#each topFindings as f}
					<div class="flex items-start gap-2">
						<Badge variant="outline" class="shrink-0 text-[9px] {severityColors[f.severity] ?? ''}">{f.severity}</Badge>
						<div class="flex-1 text-xs">{f.label}</div>
						<span class="shrink-0 font-mono text-xs text-muted-foreground">{f.count}</span>
					</div>
				{/each}
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Code Generation + Quick Stats -->
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
					<div class="grid gap-4 sm:grid-cols-3">
						{#each [
							{ label: 'Total Apps Generated', value: '64' },
							{ label: 'Success Rate', value: '89.1%' },
							{ label: 'Avg Gen Time', value: '47s' },
							{ label: 'Total Lines of Code', value: '128,400' },
							{ label: 'Unique Templates', value: '8' },
							{ label: 'Failed Generations', value: '7' },
						] as stat}
							<div class="rounded-lg border p-3 text-center">
								<div class="text-lg font-bold">{stat.value}</div>
								<div class="text-[10px] text-muted-foreground">{stat.label}</div>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		</div>

		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<HardDrive class="h-4 w-4 text-muted-foreground" />
					<Card.Title>Storage & System</Card.Title>
				</div>
			</Card.Header>
			<Card.Content class="space-y-3">
				{#each [
					{ label: 'Generated Apps', value: '2.4 GB' },
					{ label: 'Analysis Results', value: '890 MB' },
					{ label: 'Reports', value: '45 MB' },
					{ label: 'Docker Images', value: '12.6 GB' },
					{ label: 'Database', value: '128 MB' },
				] as item}
					<div class="flex items-center justify-between text-sm">
						<span class="text-muted-foreground">{item.label}</span>
						<span class="font-mono text-xs">{item.value}</span>
					</div>
				{/each}
				<div class="pt-2 border-t">
					<div class="flex items-center justify-between text-sm font-medium">
						<span>Total</span>
						<span class="font-mono text-xs">16.1 GB</span>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
	</div>
</div>
