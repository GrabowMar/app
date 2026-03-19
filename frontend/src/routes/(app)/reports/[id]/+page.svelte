<script lang="ts">
	import { page } from '$app/state';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Printer from '@lucide/svelte/icons/printer';
	import Download from '@lucide/svelte/icons/download';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import Shield from '@lucide/svelte/icons/shield';
	import Gauge from '@lucide/svelte/icons/gauge';
	import Code from '@lucide/svelte/icons/code';
	import Brain from '@lucide/svelte/icons/brain';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import CheckCircle from '@lucide/svelte/icons/check-circle';

	const reportId = $derived(page.params.id);

	const report = {
		id: 'rpt-001',
		title: 'GPT-4o Full Analysis',
		description: 'Comprehensive analysis of GPT-4o across all 8 generated applications covering security, performance, code quality, and AI review.',
		type: 'model_analysis',
		typeLabel: 'Model Analysis',
		typeColor: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		config: 'gpt-4o',
		status: 'completed',
		createdAt: '2025-03-19 14:30',
		completedAt: '2025-03-19 14:34',
		duration: '4m 12s',
		analyzerFilter: 'All Analyzers',
	};

	interface Section {
		id: string;
		title: string;
		icon: typeof Shield;
		color: string;
		expanded: boolean;
	}

	let sections: Section[] = $state([
		{ id: 'summary', title: 'Executive Summary', icon: BarChart3, color: 'text-blue-500', expanded: true },
		{ id: 'security', title: 'Security Analysis', icon: Shield, color: 'text-red-500', expanded: true },
		{ id: 'performance', title: 'Performance Analysis', icon: Gauge, color: 'text-amber-500', expanded: false },
		{ id: 'code-quality', title: 'Code Quality', icon: Code, color: 'text-emerald-500', expanded: false },
		{ id: 'ai-review', title: 'AI Review', icon: Brain, color: 'text-violet-500', expanded: false },
		{ id: 'trends', title: 'Trends & Recommendations', icon: TrendingUp, color: 'text-cyan-500', expanded: false },
	]);

	function toggleSection(id: string) {
		sections = sections.map(s => s.id === id ? { ...s, expanded: !s.expanded } : s);
	}

	function expandAll() { sections = sections.map(s => ({ ...s, expanded: true })); }
	function collapseAll() { sections = sections.map(s => ({ ...s, expanded: false })); }

	const summaryCards = [
		{ label: 'Apps Analyzed', value: '8', sub: 'All templates' },
		{ label: 'Total Findings', value: '47', sub: '12 critical' },
		{ label: 'Avg Security', value: '7.2/10', sub: '+0.3 vs avg' },
		{ label: 'Avg Performance', value: '82', sub: 'Lighthouse' },
	];

	const securityFindings = [
		{ severity: 'critical', tool: 'Bandit', rule: 'B301', message: 'Use of pickle detected', file: 'app/utils.py', line: 45 },
		{ severity: 'critical', tool: 'ZAP', rule: 'XSS-1', message: 'Cross-Site Scripting vulnerability', file: 'templates/index.html', line: 12 },
		{ severity: 'high', tool: 'Semgrep', rule: 'python.sql-injection', message: 'SQL injection via string formatting', file: 'app/db.py', line: 78 },
		{ severity: 'high', tool: 'Bandit', rule: 'B105', message: 'Hardcoded password string', file: 'config.py', line: 3 },
		{ severity: 'medium', tool: 'ZAP', rule: 'CSP-1', message: 'Missing Content-Security-Policy header', file: 'app.py', line: 1 },
		{ severity: 'low', tool: 'Semgrep', rule: 'python.logging', message: 'Debug logging in production code', file: 'app/views.py', line: 22 },
	];

	const severityColors: Record<string, string> = {
		critical: 'bg-red-500/15 text-red-400 border-red-500/30',
		high: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
		medium: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		low: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
	};
</script>

<svelte:head>
	<title>{report.title} - Reports - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
		<div class="space-y-2">
			<div class="flex items-center gap-3">
				<Button variant="ghost" size="sm" href="/reports">
					<ArrowLeft class="mr-1.5 h-4 w-4" />
					Reports
				</Button>
				<Separator orientation="vertical" class="h-6" />
				<Badge variant="outline" class="text-[10px] {report.typeColor}">{report.typeLabel}</Badge>
				<Badge variant="outline" class="text-[10px] bg-emerald-500/15 text-emerald-500 border-emerald-500/30">
					<CheckCircle class="mr-1 h-3 w-3" />
					Completed
				</Badge>
			</div>
			<h1 class="text-2xl font-bold tracking-tight">{report.title}</h1>
			<p class="text-sm text-muted-foreground">{report.description}</p>
			<div class="flex flex-wrap gap-3 text-xs text-muted-foreground">
				<span>Model: <Badge variant="secondary" class="text-[10px] font-mono">{report.config}</Badge></span>
				<span>Created: {report.createdAt}</span>
				<span>Duration: {report.duration}</span>
				<span>Filter: {report.analyzerFilter}</span>
			</div>
		</div>
		<div class="flex gap-2 shrink-0">
			<Button variant="outline" size="sm" disabled>
				<Printer class="mr-1.5 h-3.5 w-3.5" />
				Print
			</Button>
			<Button variant="outline" size="sm" disabled>
				<Download class="mr-1.5 h-3.5 w-3.5" />
				JSON
			</Button>
			<Button variant="outline" size="sm" disabled>
				<RefreshCw class="mr-1.5 h-3.5 w-3.5" />
				Regenerate
			</Button>
		</div>
	</div>

	<!-- Section Nav -->
	<div class="flex items-center gap-2 overflow-x-auto pb-1">
		{#each sections as s}
			<a href="#{s.id}" class="shrink-0 rounded-md px-2.5 py-1 text-xs font-medium hover:bg-muted transition-colors">{s.title}</a>
		{/each}
		<div class="ml-auto flex gap-1 shrink-0">
			<Button variant="ghost" size="sm" class="h-7 text-xs" onclick={expandAll}>Expand All</Button>
			<Button variant="ghost" size="sm" class="h-7 text-xs" onclick={collapseAll}>Collapse All</Button>
		</div>
	</div>

	<!-- Sections -->
	{#each sections as section}
		<Card.Root id={section.id}>
			<button class="flex w-full items-center gap-3 p-4 text-left" onclick={() => toggleSection(section.id)}>
				{#if section.expanded}
					<ChevronDown class="h-4 w-4 shrink-0" />
				{:else}
					<ChevronRight class="h-4 w-4 shrink-0" />
				{/if}
				<section.icon class="h-4 w-4 shrink-0 {section.color}" />
				<span class="font-semibold">{section.title}</span>
			</button>

			{#if section.expanded}
				<Separator />
				<Card.Content class="pt-4">
					{#if section.id === 'summary'}
						<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
							{#each summaryCards as kpi}
								<div class="rounded-lg border p-3 text-center">
									<div class="text-2xl font-bold">{kpi.value}</div>
									<div class="text-xs font-medium">{kpi.label}</div>
									<div class="text-[10px] text-muted-foreground">{kpi.sub}</div>
								</div>
							{/each}
						</div>
						<div class="mt-4 rounded-lg bg-muted/30 p-4 text-sm">
							<p class="font-medium">Key Takeaways</p>
							<ul class="mt-2 space-y-1 text-muted-foreground list-disc list-inside">
								<li>GPT-4o shows strong code quality (avg 8.1/10) but has recurring security issues with pickle and SQL injection patterns.</li>
								<li>Performance scores are above average, with Lighthouse scores ranging from 72-94 across templates.</li>
								<li>AI Review identified consistent patterns: good error handling but weak input validation.</li>
								<li>2 applications had critical vulnerabilities requiring immediate attention.</li>
							</ul>
						</div>

					{:else if section.id === 'security'}
						<div class="flex flex-wrap gap-2 mb-4">
							<Badge variant="outline" class="text-[10px] {severityColors.critical}">2 Critical</Badge>
							<Badge variant="outline" class="text-[10px] {severityColors.high}">2 High</Badge>
							<Badge variant="outline" class="text-[10px] {severityColors.medium}">1 Medium</Badge>
							<Badge variant="outline" class="text-[10px] {severityColors.low}">1 Low</Badge>
						</div>
						<table class="w-full text-sm">
							<thead>
								<tr class="border-b bg-muted/30">
									<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Severity</th>
									<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Tool</th>
									<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Rule</th>
									<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Message</th>
									<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Location</th>
								</tr>
							</thead>
							<tbody class="divide-y">
								{#each securityFindings as f}
									<tr class="hover:bg-muted/30">
										<td class="px-3 py-2">
											<Badge variant="outline" class="text-[10px] {severityColors[f.severity] ?? ''}">{f.severity}</Badge>
										</td>
										<td class="px-3 py-2 text-xs font-mono">{f.tool}</td>
										<td class="px-3 py-2 text-xs font-mono">{f.rule}</td>
										<td class="px-3 py-2 text-xs">{f.message}</td>
										<td class="px-3 py-2 text-xs font-mono text-muted-foreground">{f.file}:{f.line}</td>
									</tr>
								{/each}
							</tbody>
						</table>

					{:else if section.id === 'performance'}
						<div class="grid gap-4 sm:grid-cols-3">
							{#each [{ label: 'Avg Lighthouse', value: '82', grade: 'B' }, { label: 'First Contentful Paint', value: '1.4s', grade: 'A' }, { label: 'Load Test P95', value: '320ms', grade: 'B+' }] as metric}
								<div class="rounded-lg border p-3 text-center">
									<div class="text-xl font-bold">{metric.value}</div>
									<div class="text-xs">{metric.label}</div>
									<Badge variant="secondary" class="mt-1 text-[10px]">Grade: {metric.grade}</Badge>
								</div>
							{/each}
						</div>
						<div class="mt-4 flex h-32 items-center justify-center rounded-lg border border-dashed bg-muted/20 text-sm text-muted-foreground">
							Performance chart placeholder
						</div>

					{:else if section.id === 'code-quality'}
						<div class="grid gap-4 sm:grid-cols-2">
							<div class="space-y-2">
								<p class="text-sm font-medium">Linting Issues by Tool</p>
								{#each [{ tool: 'ESLint', issues: 23, color: 'bg-amber-500/70' }, { tool: 'Ruff', issues: 8, color: 'bg-blue-500/70' }, { tool: 'Pylint', issues: 15, color: 'bg-violet-500/70' }] as t}
									<div class="flex items-center gap-2 text-sm">
										<span class="w-16 text-xs text-muted-foreground">{t.tool}</span>
										<div class="flex-1 h-4 bg-muted rounded-full overflow-hidden">
											<div class="h-full {t.color} rounded-full" style="width: {Math.min(t.issues * 2, 100)}%"></div>
										</div>
										<span class="w-8 text-right text-xs font-mono">{t.issues}</span>
									</div>
								{/each}
							</div>
							<div class="space-y-2">
								<p class="text-sm font-medium">Code Metrics</p>
								{#each [{ label: 'Avg Complexity', value: '4.2' }, { label: 'Duplication %', value: '3.8%' }, { label: 'Test Coverage', value: '0%' }] as m}
									<div class="flex items-center justify-between text-sm">
										<span class="text-muted-foreground">{m.label}</span>
										<span class="font-mono">{m.value}</span>
									</div>
								{/each}
							</div>
						</div>

					{:else if section.id === 'ai-review'}
						<div class="space-y-4">
							<div class="grid gap-4 sm:grid-cols-2">
								<div class="rounded-lg border p-3">
									<p class="text-sm font-medium">Requirements Met</p>
									<div class="mt-1 text-2xl font-bold">18/22</div>
									<div class="mt-1 h-2 w-full rounded-full bg-muted">
										<div class="h-full rounded-full bg-emerald-500" style="width: 81.8%"></div>
									</div>
								</div>
								<div class="rounded-lg border p-3">
									<p class="text-sm font-medium">Quality Score</p>
									<div class="mt-1 text-2xl font-bold">7.8/10</div>
									<p class="text-xs text-muted-foreground">Above platform average (7.1)</p>
								</div>
							</div>
							<div class="rounded-lg bg-muted/30 p-4 text-sm">
								<p class="font-medium flex items-center gap-2">
									<AlertTriangle class="h-4 w-4 text-amber-500" />
									Critical Issues Identified
								</p>
								<ul class="mt-2 space-y-1 text-muted-foreground list-disc list-inside">
									<li>Missing CSRF protection on 3 form endpoints</li>
									<li>No rate limiting on authentication endpoints</li>
									<li>Database queries not parameterized in 2 modules</li>
								</ul>
							</div>
						</div>

					{:else if section.id === 'trends'}
						<div class="space-y-4">
							<div class="rounded-lg bg-emerald-500/10 border border-emerald-500/30 p-4 text-sm">
								<p class="font-medium text-emerald-500 flex items-center gap-2">
									<CheckCircle class="h-4 w-4" />
									Strengths
								</p>
								<ul class="mt-2 text-muted-foreground list-disc list-inside">
									<li>Consistent code structure across all generated applications</li>
									<li>Good error handling patterns with try/except blocks</li>
									<li>Fast response times under load testing conditions</li>
								</ul>
							</div>
							<div class="rounded-lg bg-amber-500/10 border border-amber-500/30 p-4 text-sm">
								<p class="font-medium text-amber-500 flex items-center gap-2">
									<AlertTriangle class="h-4 w-4" />
									Recommendations
								</p>
								<ul class="mt-2 text-muted-foreground list-disc list-inside">
									<li>Add input validation middleware to all user-facing endpoints</li>
									<li>Replace pickle serialization with JSON or msgpack</li>
									<li>Implement Content-Security-Policy headers</li>
									<li>Add parameterized queries for all database operations</li>
								</ul>
							</div>
						</div>
					{/if}
				</Card.Content>
			{/if}
		</Card.Root>
	{/each}
</div>
