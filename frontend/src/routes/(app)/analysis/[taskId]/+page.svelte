<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Microscope from '@lucide/svelte/icons/microscope';
	import Download from '@lucide/svelte/icons/download';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Shield from '@lucide/svelte/icons/shield';
	import Zap from '@lucide/svelte/icons/zap';
	import Gauge from '@lucide/svelte/icons/gauge';
	import Brain from '@lucide/svelte/icons/brain';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Clock from '@lucide/svelte/icons/clock';
	import FileText from '@lucide/svelte/icons/file-text';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import Eye from '@lucide/svelte/icons/eye';

	const taskId = $derived($page.params.taskId);

	const statusColors: Record<string, string> = {
		'Completed': 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		'Running': 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		'Failed': 'bg-red-500/15 text-red-400 border-red-500/30',
		'Partial': 'bg-amber-500/15 text-amber-500 border-amber-500/30',
	};

	const result = {
		taskId: taskId,
		model: 'GPT-4o',
		modelSlug: 'gpt-4o',
		appNumber: 1,
		type: 'Full Analysis',
		status: 'Completed',
		totalFindings: 12,
		severityBreakdown: { critical: 0, high: 2, medium: 5, low: 3, info: 2 },
		toolsUsed: ['bandit', 'eslint', 'ruff', 'zap', 'port-scan', 'connectivity', 'lighthouse', 'load-test', 'requirements-scanner', 'code-quality'],
		duration: '2m 15s',
		queueTime: '3s',
		startedAt: '2025-03-19 15:00:12',
		completedAt: '2025-03-19 15:02:27',
		orchestratorVersion: '2.1.0',
		executor: 'celery-worker-1',
		analyzerVersion: '1.5.0',
		services: {
			static: {
				status: 'Completed',
				totalIssues: 5,
				codeQuality: 'B+',
				breakdownHigh: 1, breakdownMedium: 2, breakdownLow: 1, breakdownInfo: 1,
				tools: ['bandit', 'eslint', 'ruff'],
				perLanguage: [
					{ language: 'Python', tools: [{ name: 'bandit', status: 'Completed', issues: 2, severities: { h: 1, m: 1, l: 0 } }, { name: 'ruff', status: 'Completed', issues: 1, severities: { h: 0, m: 0, l: 1 } }] },
					{ language: 'JavaScript', tools: [{ name: 'eslint', status: 'Completed', issues: 2, severities: { h: 0, m: 1, l: 1 } }] },
				],
			},
			dynamic: {
				status: 'Completed',
				securityAlerts: 3,
				riskLevel: 'Medium',
				connectivityRatio: '2/2',
				riskBreakdown: { high: 0, medium: 2, low: 1 },
				targetUrls: ['http://localhost:5001', 'http://localhost:8001'],
				connectivityTests: [
					{ url: 'http://localhost:5001', reachable: true },
					{ url: 'http://localhost:8001', reachable: true },
				],
				zapAlerts: [
					{ risk: 'Medium', name: 'X-Frame-Options Header Not Set', count: 2 },
					{ risk: 'Medium', name: 'Content Security Policy Not Set', count: 1 },
					{ risk: 'Low', name: 'Server Leaks Information', count: 3 },
				],
				openPorts: [5001, 8001],
			},
			performance: {
				status: 'Completed',
				totalRequests: 150,
				avgResponseTime: '234ms',
				bestThroughput: '45.2 req/s',
				successRate: '98.7%',
				grades: { responseTime: 'B', throughput: 'B+', reliability: 'A', overall: 'B+' },
				tests: [
					{ tool: 'lighthouse', status: 'Completed', responseTime: '1.2s', throughput: '—', successRate: '100%', requests: 1, issues: 2, duration: '15s' },
					{ tool: 'load-test', status: 'Completed', responseTime: '234ms', throughput: '45.2 req/s', successRate: '98.7%', requests: 149, issues: 0, duration: '30s' },
				],
			},
			ai: {
				status: 'Completed',
				compliance: 85,
				requirementsMet: '17/20',
				codeQualityScore: 78,
				codeQualityGrade: 'B+',
				backendRequirements: [
					{ requirement: 'CRUD operations for tasks', status: 'met', confidence: 'high' },
					{ requirement: 'Authentication middleware', status: 'not_met', confidence: 'high' },
					{ requirement: 'Error handling', status: 'met', confidence: 'medium' },
					{ requirement: 'Database migrations', status: 'met', confidence: 'high' },
					{ requirement: 'API documentation', status: 'not_met', confidence: 'low' },
				],
				frontendRequirements: [
					{ requirement: 'Responsive layout', status: 'met', confidence: 'high' },
					{ requirement: 'Form validation', status: 'met', confidence: 'medium' },
					{ requirement: 'Loading states', status: 'not_met', confidence: 'high' },
				],
				qualityMetrics: [
					{ metric: 'Code Structure', score: 82, findings: 1, recommendation: 'Consider extracting utility functions' },
					{ metric: 'Error Handling', score: 65, findings: 3, recommendation: 'Add try-catch blocks to API calls' },
					{ metric: 'Documentation', score: 40, findings: 2, recommendation: 'Add docstrings and comments' },
					{ metric: 'Security Practices', score: 88, findings: 0, recommendation: 'Good — no critical issues found' },
					{ metric: 'Testing Coverage', score: 0, findings: 1, recommendation: 'No tests found — consider adding tests' },
				],
				criticalIssues: [
					'No input validation on user-submitted data',
					'Missing CORS configuration for production',
				],
			},
		},
	};

	const sections = [
		{ id: 'summary', label: 'Summary' },
		{ id: 'metadata', label: 'Metadata' },
		{ id: 'static', label: 'Static Analysis' },
		{ id: 'dynamic', label: 'Dynamic Analysis' },
		{ id: 'performance', label: 'Performance' },
		{ id: 'ai', label: 'AI Review' },
	];

	let activeSection = $state('summary');

	function scrollToSection(id: string) {
		activeSection = id;
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	const severityColors: Record<string, string> = {
		critical: 'bg-red-500/15 text-red-400',
		high: 'bg-red-500/15 text-red-400',
		medium: 'bg-amber-500/15 text-amber-500',
		low: 'bg-blue-500/15 text-blue-400',
		info: 'bg-zinc-500/15 text-zinc-400',
	};

	const gradeColors: Record<string, string> = {
		'A': 'text-emerald-500', 'A-': 'text-emerald-500', 'A+': 'text-emerald-500',
		'B': 'text-blue-400', 'B-': 'text-blue-400', 'B+': 'text-blue-400',
		'C': 'text-amber-500', 'C-': 'text-amber-500', 'C+': 'text-amber-500',
		'D': 'text-orange-500', 'F': 'text-red-400',
	};
</script>

<svelte:head>
	<title>Analysis {taskId} - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="ghost" size="sm" href="/analysis" class="gap-1.5 px-2">
			<ArrowLeft class="h-3.5 w-3.5" />
			Analysis Hub
		</Button>
		<span>/</span>
		<span class="text-foreground font-medium">{taskId}</span>
	</div>

	<!-- Header Card -->
	<Card.Root class="border-border/60">
		<Card.Content class="p-6">
			<div class="flex items-start justify-between">
				<div class="flex items-center gap-4">
					<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
						<Microscope class="h-6 w-6 text-muted-foreground" />
					</div>
					<div>
						<div class="flex items-center gap-3">
							<h1 class="text-xl font-semibold">{result.type}</h1>
							<Badge variant="outline" class="{statusColors[result.status] ?? ''}">{result.status}</Badge>
							<Badge variant="outline">{result.model}</Badge>
							<Badge variant="outline">App #{result.appNumber}</Badge>
						</div>
						<p class="mt-1 text-sm text-muted-foreground">{result.taskId} • {result.duration} • {result.totalFindings} findings</p>
					</div>
				</div>
				<div class="flex items-center gap-3 text-sm text-muted-foreground">
					<div class="text-center">
						<div class="text-2xl font-bold text-foreground">{result.totalFindings}</div>
						<div class="text-xs">Findings</div>
					</div>
					<Separator orientation="vertical" class="h-8" />
					<div class="text-center">
						<div class="text-2xl font-bold text-foreground">{result.toolsUsed.length}</div>
						<div class="text-xs">Tools</div>
					</div>
				</div>
			</div>
			<div class="mt-3 flex items-center gap-2">
				<Button variant="outline" size="sm" disabled><Download class="mr-1.5 h-3.5 w-3.5" /> Download</Button>
				<Button variant="ghost" size="sm" disabled><RefreshCw class="mr-1.5 h-3.5 w-3.5" /> Refresh</Button>
			</div>
		</Card.Content>
	</Card.Root>

	<!-- Section Nav -->
	<div class="sticky top-0 z-40 -mx-4 bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
		<nav class="flex gap-1 overflow-x-auto border-b py-2">
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
		<!-- Service Dashboard -->
		<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
			{#each [
				{ icon: Shield, label: 'Static', status: result.services.static.status, metric: `${result.services.static.totalIssues} issues`, color: 'text-blue-400' },
				{ icon: Zap, label: 'Dynamic', status: result.services.dynamic.status, metric: `${result.services.dynamic.securityAlerts} alerts`, color: 'text-emerald-500' },
				{ icon: Gauge, label: 'Performance', status: result.services.performance.status, metric: result.services.performance.avgResponseTime, color: 'text-cyan-400' },
				{ icon: Brain, label: 'AI Review', status: result.services.ai.status, metric: `${result.services.ai.compliance}%`, color: 'text-amber-500' },
			] as svc}
				<Card.Root>
					<Card.Content class="p-4">
						<div class="flex items-center gap-2 mb-2">
							<svc.icon class="h-4 w-4 {svc.color}" />
							<span class="text-sm font-medium">{svc.label}</span>
							<Badge variant="outline" class="ml-auto text-[10px] {statusColors[svc.status] ?? ''}">{svc.status}</Badge>
						</div>
						<div class="text-xl font-bold">{svc.metric}</div>
					</Card.Content>
				</Card.Root>
			{/each}
		</div>

		<!-- Timing -->
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex flex-wrap items-center gap-6 text-sm">
					<div><span class="text-muted-foreground">Duration:</span> <span class="font-mono font-medium">{result.duration}</span></div>
					<div><span class="text-muted-foreground">Queue:</span> <span class="font-mono">{result.queueTime}</span></div>
					<div><span class="text-muted-foreground">Started:</span> <span class="font-mono">{result.startedAt}</span></div>
					<div><span class="text-muted-foreground">Completed:</span> <span class="font-mono">{result.completedAt}</span></div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Severity Breakdown -->
		<div class="flex flex-wrap gap-2">
			{#each Object.entries(result.severityBreakdown) as [sev, count]}
				<Badge variant="outline" class="{severityColors[sev] ?? ''} text-xs">
					{count} {sev}
				</Badge>
			{/each}
		</div>
	</div>

	<!-- ===== Metadata ===== -->
	<div id="metadata" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Metadata</h2>
		<div class="grid gap-4 md:grid-cols-2">
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Analysis Information</Card.Title></Card.Header>
				<Card.Content>
					<dl class="grid grid-cols-2 gap-y-2 text-sm">
						<dt class="text-muted-foreground">Model</dt><dd><a href="/models/{result.modelSlug}" class="hover:underline">{result.model}</a></dd>
						<dt class="text-muted-foreground">App #</dt><dd>{result.appNumber}</dd>
						<dt class="text-muted-foreground">Type</dt><dd>{result.type}</dd>
						<dt class="text-muted-foreground">Status</dt><dd><Badge variant="outline" class="{statusColors[result.status] ?? ''} text-xs">{result.status}</Badge></dd>
						<dt class="text-muted-foreground">Task ID</dt><dd class="font-mono text-xs">{result.taskId}</dd>
					</dl>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Execution Details</Card.Title></Card.Header>
				<Card.Content>
					<dl class="grid grid-cols-2 gap-y-2 text-sm">
						<dt class="text-muted-foreground">Orchestrator</dt><dd class="font-mono text-xs">{result.orchestratorVersion}</dd>
						<dt class="text-muted-foreground">Executor</dt><dd class="font-mono text-xs">{result.executor}</dd>
						<dt class="text-muted-foreground">Analyzer</dt><dd class="font-mono text-xs">{result.analyzerVersion}</dd>
						<dt class="text-muted-foreground">Total Findings</dt><dd class="font-semibold">{result.totalFindings}</dd>
						<dt class="text-muted-foreground">Tools Used</dt><dd>{result.toolsUsed.length}</dd>
					</dl>
				</Card.Content>
			</Card.Root>
		</div>
		<div class="flex flex-wrap gap-1">
			{#each result.toolsUsed as tool}
				<Badge variant="secondary" class="text-xs">{tool}</Badge>
			{/each}
		</div>
	</div>

	<!-- ===== Static Analysis ===== -->
	<div id="static" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Static Analysis</h2>
		<div class="flex flex-wrap gap-3">
			<Badge variant="outline">{result.services.static.totalIssues} issues</Badge>
			<Badge variant="outline">Quality: {result.services.static.codeQuality}</Badge>
			<Badge variant="outline" class="bg-red-500/15 text-red-400">{result.services.static.breakdownHigh} high</Badge>
			<Badge variant="outline" class="bg-amber-500/15 text-amber-500">{result.services.static.breakdownMedium} medium</Badge>
			<Badge variant="outline" class="bg-blue-500/15 text-blue-400">{result.services.static.breakdownLow} low</Badge>
		</div>

		{#each result.services.static.perLanguage as lang}
			<Card.Root>
				<Card.Header>
					<Card.Title class="text-sm">{lang.language}</Card.Title>
				</Card.Header>
				<Card.Content class="p-0">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Tool</th>
								<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
								<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Issues</th>
								<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Severity</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each lang.tools as tool}
								<tr class="hover:bg-muted/30">
									<td class="px-4 py-2 font-medium">{tool.name}</td>
									<td class="px-4 py-2"><Badge variant="outline" class="text-[10px] bg-emerald-500/15 text-emerald-500 border-emerald-500/30">{tool.status}</Badge></td>
									<td class="px-4 py-2 font-mono">{tool.issues}</td>
									<td class="px-4 py-2">
										<div class="flex gap-1">
											{#if tool.severities.h > 0}<Badge variant="outline" class="text-[10px] bg-red-500/15 text-red-400">{tool.severities.h}H</Badge>{/if}
											{#if tool.severities.m > 0}<Badge variant="outline" class="text-[10px] bg-amber-500/15 text-amber-500">{tool.severities.m}M</Badge>{/if}
											{#if tool.severities.l > 0}<Badge variant="outline" class="text-[10px] bg-blue-500/15 text-blue-400">{tool.severities.l}L</Badge>{/if}
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>

	<!-- ===== Dynamic Analysis ===== -->
	<div id="dynamic" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Dynamic Analysis</h2>
		<div class="flex flex-wrap gap-3">
			<Badge variant="outline">{result.services.dynamic.securityAlerts} alerts</Badge>
			<Badge variant="outline">Risk: {result.services.dynamic.riskLevel}</Badge>
			<Badge variant="outline">Connectivity: {result.services.dynamic.connectivityRatio}</Badge>
		</div>

		<!-- Connectivity Tests -->
		<Card.Root>
			<Card.Header><Card.Title class="text-sm">Connectivity Tests</Card.Title></Card.Header>
			<Card.Content class="p-0">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">URL</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each result.services.dynamic.connectivityTests as test}
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2 font-mono text-xs">{test.url}</td>
								<td class="px-4 py-2">
									{#if test.reachable}
										<Badge variant="outline" class="text-[10px] bg-emerald-500/15 text-emerald-500 border-emerald-500/30">
											<Check class="mr-1 h-3 w-3" /> Reachable
										</Badge>
									{:else}
										<Badge variant="outline" class="text-[10px] bg-red-500/15 text-red-400 border-red-500/30">
											<X class="mr-1 h-3 w-3" /> Unreachable
										</Badge>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</Card.Content>
		</Card.Root>

		<!-- ZAP Alerts -->
		<Card.Root>
			<Card.Header><Card.Title class="text-sm">Security Alerts (ZAP)</Card.Title></Card.Header>
			<Card.Content class="p-0">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Risk</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Alert</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Count</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each result.services.dynamic.zapAlerts as alert}
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2">
									<Badge variant="outline" class="text-[10px] {alert.risk === 'High' ? 'bg-red-500/15 text-red-400' : alert.risk === 'Medium' ? 'bg-amber-500/15 text-amber-500' : 'bg-blue-500/15 text-blue-400'}">{alert.risk}</Badge>
								</td>
								<td class="px-4 py-2">{alert.name}</td>
								<td class="px-4 py-2 font-mono">{alert.count}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</Card.Content>
		</Card.Root>

		<!-- Open Ports -->
		<Card.Root>
			<Card.Content class="p-4">
				<h3 class="mb-2 text-sm font-medium">Open Ports</h3>
				<div class="flex gap-2">
					{#each result.services.dynamic.openPorts as port}
						<Badge variant="secondary" class="font-mono">{port}</Badge>
					{/each}
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- ===== Performance ===== -->
	<div id="performance" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Performance</h2>
		<div class="flex flex-wrap gap-3">
			<Badge variant="outline">{result.services.performance.totalRequests} requests</Badge>
			<Badge variant="outline">Avg: {result.services.performance.avgResponseTime}</Badge>
			<Badge variant="outline">Best: {result.services.performance.bestThroughput}</Badge>
			<Badge variant="outline">Success: {result.services.performance.successRate}</Badge>
		</div>

		<!-- Grades -->
		<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
			{#each Object.entries(result.services.performance.grades) as [metric, grade]}
				<Card.Root>
					<Card.Content class="p-4 text-center">
						<div class="text-3xl font-bold {gradeColors[grade] ?? 'text-foreground'}">{grade}</div>
						<div class="text-sm text-muted-foreground capitalize">{metric.replace(/([A-Z])/g, ' $1').trim()}</div>
					</Card.Content>
				</Card.Root>
			{/each}
		</div>

		<!-- Test Results -->
		<Card.Root>
			<Card.Header><Card.Title class="text-sm">Test Results</Card.Title></Card.Header>
			<Card.Content class="p-0">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Tool</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Response</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Throughput</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Success</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Requests</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Duration</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each result.services.performance.tests as test}
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2 font-medium">{test.tool}</td>
								<td class="px-4 py-2"><Badge variant="outline" class="text-[10px] bg-emerald-500/15 text-emerald-500">{test.status}</Badge></td>
								<td class="px-4 py-2 font-mono text-xs">{test.responseTime}</td>
								<td class="px-4 py-2 font-mono text-xs">{test.throughput}</td>
								<td class="px-4 py-2 font-mono text-xs">{test.successRate}</td>
								<td class="px-4 py-2 font-mono text-xs">{test.requests}</td>
								<td class="px-4 py-2 font-mono text-xs">{test.duration}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- ===== AI Review ===== -->
	<div id="ai" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">AI Review</h2>

		<!-- Overall -->
		<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
			<Card.Root>
				<Card.Content class="p-4 text-center">
					<div class="text-2xl font-bold">{result.services.ai.compliance}%</div>
					<div class="text-sm text-muted-foreground">Compliance</div>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Content class="p-4 text-center">
					<div class="text-2xl font-bold">{result.services.ai.requirementsMet}</div>
					<div class="text-sm text-muted-foreground">Requirements</div>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Content class="p-4 text-center">
					<div class="text-2xl font-bold">{result.services.ai.codeQualityScore}</div>
					<div class="text-sm text-muted-foreground">Quality Score</div>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Content class="p-4 text-center">
					<div class="text-3xl font-bold {gradeColors[result.services.ai.codeQualityGrade] ?? ''}">{result.services.ai.codeQualityGrade}</div>
					<div class="text-sm text-muted-foreground">Grade</div>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Requirements -->
		<Card.Root>
			<Card.Header><Card.Title class="text-sm">Backend Requirements</Card.Title></Card.Header>
			<Card.Content class="p-0">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="w-8 px-4 py-2"></th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Requirement</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Confidence</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each result.services.ai.backendRequirements as req}
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2">
									{#if req.status === 'met'}
										<Check class="h-4 w-4 text-emerald-500" />
									{:else}
										<X class="h-4 w-4 text-red-400" />
									{/if}
								</td>
								<td class="px-4 py-2">{req.requirement}</td>
								<td class="px-4 py-2">
									<Badge variant="outline" class="text-[10px] {req.confidence === 'high' ? 'bg-emerald-500/15 text-emerald-500' : req.confidence === 'medium' ? 'bg-amber-500/15 text-amber-500' : 'bg-zinc-500/15 text-zinc-400'}">
										{req.confidence}
									</Badge>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</Card.Content>
		</Card.Root>

		<Card.Root>
			<Card.Header><Card.Title class="text-sm">Frontend Requirements</Card.Title></Card.Header>
			<Card.Content class="p-0">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="w-8 px-4 py-2"></th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Requirement</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Confidence</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each result.services.ai.frontendRequirements as req}
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2">
									{#if req.status === 'met'}
										<Check class="h-4 w-4 text-emerald-500" />
									{:else}
										<X class="h-4 w-4 text-red-400" />
									{/if}
								</td>
								<td class="px-4 py-2">{req.requirement}</td>
								<td class="px-4 py-2">
									<Badge variant="outline" class="text-[10px] {req.confidence === 'high' ? 'bg-emerald-500/15 text-emerald-500' : req.confidence === 'medium' ? 'bg-amber-500/15 text-amber-500' : 'bg-zinc-500/15 text-zinc-400'}">
										{req.confidence}
									</Badge>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</Card.Content>
		</Card.Root>

		<!-- Quality Metrics -->
		<Card.Root>
			<Card.Header><Card.Title class="text-sm">Quality Metrics</Card.Title></Card.Header>
			<Card.Content class="p-0">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Metric</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Score</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Findings</th>
							<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Recommendation</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each result.services.ai.qualityMetrics as m}
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2 font-medium">{m.metric}</td>
								<td class="px-4 py-2">
									<div class="flex items-center gap-2">
										<div class="h-1.5 w-16 rounded-full bg-muted overflow-hidden">
											<div class="h-full rounded-full {m.score >= 80 ? 'bg-emerald-500' : m.score >= 50 ? 'bg-amber-500' : 'bg-red-400'}" style="width: {m.score}%"></div>
										</div>
										<span class="font-mono text-xs">{m.score}</span>
									</div>
								</td>
								<td class="px-4 py-2 font-mono text-xs">{m.findings}</td>
								<td class="px-4 py-2 text-xs text-muted-foreground">{m.recommendation}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</Card.Content>
		</Card.Root>

		<!-- Critical Issues -->
		{#if result.services.ai.criticalIssues.length > 0}
			<Card.Root class="border-red-500/20">
				<Card.Header>
					<div class="flex items-center gap-2">
						<AlertTriangle class="h-4 w-4 text-red-400" />
						<Card.Title class="text-sm text-red-400">Critical Issues</Card.Title>
					</div>
				</Card.Header>
				<Card.Content>
					<ul class="space-y-2">
						{#each result.services.ai.criticalIssues as issue, i}
							<li class="flex items-start gap-2 text-sm">
								<span class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-500/10 text-[10px] font-medium text-red-400">{i + 1}</span>
								<span>{issue}</span>
							</li>
						{/each}
					</ul>
				</Card.Content>
			</Card.Root>
		{/if}
	</div>
</div>
