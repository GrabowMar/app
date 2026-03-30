<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Play from '@lucide/svelte/icons/play';
	import Square from '@lucide/svelte/icons/square';
	import RotateCw from '@lucide/svelte/icons/rotate-cw';
	import Wrench from '@lucide/svelte/icons/wrench';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Download from '@lucide/svelte/icons/download';
	import SquareTerminal from '@lucide/svelte/icons/square-terminal';
	import FileText from '@lucide/svelte/icons/file-text';
	import FolderOpen from '@lucide/svelte/icons/folder-open';
	import ScrollText from '@lucide/svelte/icons/scroll-text';
	import Database from '@lucide/svelte/icons/database';
	import Terminal from '@lucide/svelte/icons/terminal';
	import MessageSquare from '@lucide/svelte/icons/message-square';
	import Settings from '@lucide/svelte/icons/settings';
	import Shield from '@lucide/svelte/icons/shield';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Copy from '@lucide/svelte/icons/copy';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import Eye from '@lucide/svelte/icons/eye';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import Skull from '@lucide/svelte/icons/skull';

	const slug = $derived($page.params.slug ?? '');
	const appNum = $derived(Number($page.params.appNum));

	const statusColors: Record<string, string> = {
		'Running': 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		'Stopped': 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
		'Building': 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		'Build Failed': 'bg-orange-500/15 text-orange-500 border-orange-500/30',
		'Dead': 'bg-red-500/15 text-red-400 border-red-500/30',
	};

	// Mock data
	const app = $derived({
		modelSlug: slug,
		modelName: slug === 'gpt-4o' ? 'GPT-4o' : slug === 'claude-3-5-sonnet' ? 'Claude 3.5 Sonnet' : slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
		modelProvider: slug.startsWith('gpt') ? 'OpenAI' : slug.startsWith('claude') ? 'Anthropic' : slug.startsWith('gemini') ? 'Google' : 'Other',
		appNumber: appNum,
		version: 'v1.0',
		status: 'Running',
		generationMode: 'guarded' as const,
		templateName: 'Task Manager',
		templateSlug: 'task-manager',
		createdAt: '2025-03-19 14:32:00',
		containerStatus: 'Running',
		containerId: 'a1b2c3d4e5f6',
		backendPort: 5001,
		frontendPort: 8001,
		containerSize: '245 MB',
		totalLoc: 2847,
		totalFiles: 42,
		byLanguage: { Python: 1523, JavaScript: 892, HTML: 312, CSS: 120 },
		generationAttempts: 1,
		totalFixes: 0,
		fixBreakdown: { retry: 0, auto: 0, llm: 0, manual: 0 },
		frameworks: { backend: 'Flask', frontend: 'React', database: 'SQLite' },
		generationDuration: '34.2s',
		tokensUsed: 12450,
		analyses: [
			{ id: 'task-001', status: 'Complete', type: 'Full', findings: 3, duration: '2m 15s', createdAt: '19 Mar 15:00' },
			{ id: 'task-002', status: 'Complete', type: 'Static', findings: 1, duration: '45s', createdAt: '19 Mar 14:50' },
			{ id: 'task-003', status: 'Running', type: 'Dynamic', findings: 0, duration: '—', createdAt: '19 Mar 15:10' },
		],
		artifacts: [
			{ name: 'PROJECT_INDEX.md', size: '4.2 KB' },
			{ name: 'README.md', size: '2.1 KB' },
			{ name: 'docker-compose.yml', size: '1.8 KB' },
		],
		fileStats: { total: 42, size: '245 KB', code: 35, config: 7 },
		files: [
			{ path: 'backend/', type: 'dir', children: ['app.py', 'models.py', 'routes/', 'requirements.txt'] },
			{ path: 'frontend/', type: 'dir', children: ['src/', 'package.json', 'index.html'] },
			{ path: 'docker-compose.yml', type: 'file' },
			{ path: 'README.md', type: 'file' },
		],
		extensions: { '.py': 45, '.js': 25, '.html': 12, '.css': 8, '.json': 6, '.yml': 4 },
		ports: [
			{ container: 5000, host: 5001, protocol: 'TCP', status: 'Open' },
			{ container: 3000, host: 8001, protocol: 'TCP', status: 'Open' },
		],
		envVars: [
			{ key: 'FLASK_APP', value: 'app.py' },
			{ key: 'FLASK_ENV', value: 'development' },
			{ key: 'DATABASE_URL', value: 'sqlite:///app.db' },
			{ key: 'SECRET_KEY', value: '••••••••' },
		],
		dependencies: {
			backend: ['flask==3.0.0', 'flask-sqlalchemy==3.1.1', 'flask-cors==4.0.0', 'gunicorn==21.2.0'],
			frontend: ['react@18.2.0', 'react-dom@18.2.0', 'axios@1.6.0', 'tailwindcss@3.4.0'],
		},
		prompts: {
			backend: { question: 'Generate a Flask REST API for a task manager...', response: 'Here is the Flask application with CRUD endpoints...' },
			frontend: { question: 'Generate a React frontend for the task manager API...', response: 'Here is the React application with components...' },
		},
		logs: [
			{ level: 'INFO', timestamp: '15:32:01', message: 'Server started on port 5000' },
			{ level: 'INFO', timestamp: '15:32:02', message: 'Database initialized' },
			{ level: 'WARNING', timestamp: '15:32:05', message: 'No production WSGI server configured' },
			{ level: 'INFO', timestamp: '15:32:10', message: 'GET /api/tasks 200 12ms' },
			{ level: 'ERROR', timestamp: '15:33:01', message: 'Failed to connect to external service' },
			{ level: 'INFO', timestamp: '15:33:15', message: 'POST /api/tasks 201 8ms' },
		],
	});

	const sections = [
		{ id: 'overview', label: 'Overview' },
		{ id: 'container', label: 'Container' },
		{ id: 'analyses', label: 'Analyses' },
		{ id: 'artifacts', label: 'Artifacts' },
		{ id: 'files', label: 'Files' },
		{ id: 'logs', label: 'Logs' },
		{ id: 'metadata', label: 'Metadata' },
		{ id: 'prompts', label: 'Prompts' },
		{ id: 'ports', label: 'Ports' },
		{ id: 'tools', label: 'Tools' },
	];

	let activeSection = $state('overview');

	function scrollToSection(id: string) {
		activeSection = id;
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	const kpis = $derived([
		{ label: 'Total LOC', value: app.totalLoc.toLocaleString(), sub: 'Lines of code' },
		{ label: 'Files', value: app.totalFiles.toString(), sub: 'Total files' },
		{ label: 'Analyses', value: app.analyses.length.toString(), sub: `${app.analyses.filter(a => a.status === 'Complete').length} complete` },
		{ label: 'Fixes', value: app.totalFixes.toString(), sub: 'Applied' },
		{ label: 'Gen Time', value: app.generationDuration, sub: 'Duration' },
		{ label: 'Tokens', value: app.tokensUsed.toLocaleString(), sub: 'Used' },
	]);

	const logLevelColors: Record<string, string> = {
		'INFO': 'text-blue-400',
		'WARNING': 'text-amber-500',
		'ERROR': 'text-red-400',
		'DEBUG': 'text-zinc-400',
	};
</script>

<svelte:head>
	<title>{app.modelName} #{app.appNumber} - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="ghost" size="sm" href="/applications" class="gap-1.5 px-2">
			<ArrowLeft class="h-3.5 w-3.5" />
			Applications
		</Button>
		<span>/</span>
		<a href="/models/{app.modelSlug}" class="hover:text-foreground">{app.modelName}</a>
		<span>/</span>
		<span class="text-foreground font-medium">App #{app.appNumber}</span>
	</div>

	<!-- Warning Banner (if unhealthy) -->
	{#if app.status === 'Dead' || app.status === 'Build Failed'}
		<div class="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3">
			<AlertTriangle class="h-5 w-5 text-red-400 shrink-0" />
			<div>
				<p class="text-sm font-medium text-red-400">Container Unhealthy</p>
				<p class="text-xs text-muted-foreground">This application's container has issues. Check logs for details.</p>
			</div>
			<Button variant="outline" size="sm" class="ml-auto" href="/applications/{app.modelSlug}/{app.appNumber}/failure">
				View Failure Details
			</Button>
		</div>
	{/if}

	<!-- Header Card -->
	<Card.Root class="border-border/60">
		<Card.Content class="p-6">
			<div class="flex items-start justify-between">
				<div class="flex items-center gap-4">
					<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
						<Cpu class="h-6 w-6 text-muted-foreground" />
					</div>
					<div>
						<div class="flex items-center gap-3">
							<h1 class="text-xl font-semibold">{app.modelName} #{app.appNumber}</h1>
							<Badge variant="outline">{app.modelProvider}</Badge>
							<Badge variant="outline" class="{statusColors[app.status] ?? ''}">
								{#if app.status === 'Running'}
									<span class="mr-1.5 h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
								{/if}
								{app.status}
							</Badge>
							<Badge variant="outline" class="gap-1 border-emerald-500/30 text-emerald-500">
								<Shield class="h-3 w-3" /> {app.generationMode}
							</Badge>
						</div>
						<p class="mt-1 text-sm text-muted-foreground">{app.templateName} • {app.version} • Created {app.createdAt}</p>
					</div>
				</div>
				<div class="flex items-center gap-3 text-sm text-muted-foreground">
					<div class="text-center">
						<div class="font-semibold text-foreground">{app.totalLoc.toLocaleString()}</div>
						<div class="text-xs">LOC</div>
					</div>
					<Separator orientation="vertical" class="h-8" />
					<div class="text-center">
						<div class="font-semibold text-foreground">{app.totalFiles}</div>
						<div class="text-xs">Files</div>
					</div>
					<Separator orientation="vertical" class="h-8" />
					<div class="text-center">
						<div class="font-semibold text-foreground">{app.containerSize}</div>
						<div class="text-xs">Size</div>
					</div>
				</div>
			</div>
			<div class="mt-4 flex items-center gap-2">
				{#if app.status === 'Running'}
					<Button variant="outline" size="sm" disabled><Square class="mr-1.5 h-3.5 w-3.5" /> Stop</Button>
					<Button variant="outline" size="sm" disabled><RotateCw class="mr-1.5 h-3.5 w-3.5" /> Restart</Button>
					{#if app.frontendPort}
						<Button variant="outline" size="sm" disabled><ExternalLink class="mr-1.5 h-3.5 w-3.5" /> Open App</Button>
					{/if}
				{:else}
					<Button variant="outline" size="sm" disabled><Play class="mr-1.5 h-3.5 w-3.5" /> Start</Button>
				{/if}
				<Button variant="outline" size="sm" disabled><Wrench class="mr-1.5 h-3.5 w-3.5" /> Rebuild</Button>
				<Button variant="outline" size="sm" disabled><Download class="mr-1.5 h-3.5 w-3.5" /> Download</Button>
				<Button variant="ghost" size="sm" disabled><RefreshCw class="mr-1.5 h-3.5 w-3.5" /> Refresh</Button>
			</div>
		</Card.Content>
	</Card.Root>

	<!-- KPI Grid -->
	<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
		{#each kpis as kpi}
			<Card.Root>
				<Card.Content class="p-4 text-center">
					<div class="text-2xl font-bold">{kpi.value}</div>
					<div class="text-sm font-medium text-muted-foreground">{kpi.label}</div>
					<div class="text-xs text-muted-foreground/70">{kpi.sub}</div>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>

	<!-- Section Navigation -->
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

	<!-- ===== SECTION: Overview ===== -->
	<div id="overview" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Overview</h2>
		<div class="grid gap-4 md:grid-cols-2">
			<!-- Identity -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Identity</Card.Title></Card.Header>
				<Card.Content>
					<dl class="grid grid-cols-2 gap-y-2 text-sm">
						<dt class="text-muted-foreground">Model</dt><dd><a href="/models/{app.modelSlug}" class="hover:underline">{app.modelName}</a></dd>
						<dt class="text-muted-foreground">Provider</dt><dd>{app.modelProvider}</dd>
						<dt class="text-muted-foreground">App Number</dt><dd>#{app.appNumber}</dd>
						<dt class="text-muted-foreground">Template</dt><dd>{app.templateName}</dd>
						<dt class="text-muted-foreground">Version</dt><dd>{app.version}</dd>
						<dt class="text-muted-foreground">Mode</dt><dd>{app.generationMode}</dd>
					</dl>
				</Card.Content>
			</Card.Root>

			<!-- Code Footprint -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Code Footprint</Card.Title></Card.Header>
				<Card.Content>
					<div class="mb-3 flex items-baseline gap-2">
						<span class="text-2xl font-bold">{app.totalLoc.toLocaleString()}</span>
						<span class="text-sm text-muted-foreground">lines in {app.totalFiles} files</span>
					</div>
					<div class="space-y-1.5">
						{#each Object.entries(app.byLanguage) as [lang, lines]}
							<div class="flex items-center justify-between text-sm">
								<span>{lang}</span>
								<span class="font-mono text-muted-foreground">{lines.toLocaleString()}</span>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Lifecycle -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Lifecycle</Card.Title></Card.Header>
				<Card.Content>
					<dl class="grid grid-cols-2 gap-y-2 text-sm">
						<dt class="text-muted-foreground">Container</dt><dd><Badge variant="outline" class="{statusColors[app.containerStatus] ?? ''} text-xs">{app.containerStatus}</Badge></dd>
						<dt class="text-muted-foreground">Created</dt><dd>{app.createdAt}</dd>
						<dt class="text-muted-foreground">Backend Port</dt><dd class="font-mono">{app.backendPort ?? '—'}</dd>
						<dt class="text-muted-foreground">Frontend Port</dt><dd class="font-mono">{app.frontendPort ?? '—'}</dd>
						<dt class="text-muted-foreground">Attempts</dt><dd>{app.generationAttempts}</dd>
						<dt class="text-muted-foreground">Duration</dt><dd>{app.generationDuration}</dd>
					</dl>
				</Card.Content>
			</Card.Root>

			<!-- Frameworks -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Frameworks & Stack</Card.Title></Card.Header>
				<Card.Content>
					<dl class="grid grid-cols-2 gap-y-2 text-sm">
						<dt class="text-muted-foreground">Backend</dt><dd><Badge variant="secondary">{app.frameworks.backend}</Badge></dd>
						<dt class="text-muted-foreground">Frontend</dt><dd><Badge variant="secondary">{app.frameworks.frontend}</Badge></dd>
						<dt class="text-muted-foreground">Database</dt><dd><Badge variant="secondary">{app.frameworks.database}</Badge></dd>
						<dt class="text-muted-foreground">Tokens Used</dt><dd class="font-mono">{app.tokensUsed.toLocaleString()}</dd>
					</dl>
				</Card.Content>
			</Card.Root>
		</div>
	</div>

	<!-- ===== SECTION: Container ===== -->
	<div id="container" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Container</h2>
		<Card.Root>
			<Card.Content class="p-6">
				<div class="flex items-center gap-4 mb-4">
					<div class="flex items-center gap-2">
						{#if app.containerStatus === 'Running'}
							<span class="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
						{:else}
							<span class="h-2.5 w-2.5 rounded-full bg-zinc-500"></span>
						{/if}
						<span class="text-lg font-semibold">{app.containerStatus}</span>
					</div>
					<Badge variant="outline" class="font-mono text-xs">{app.containerId}</Badge>
					<Badge variant="outline" class="text-xs">{app.containerSize}</Badge>
				</div>

				<div class="flex flex-wrap gap-2 mb-6">
					{#if app.containerStatus === 'Running'}
						<Button variant="outline" size="sm" disabled><Square class="mr-1.5 h-3.5 w-3.5" /> Stop</Button>
						<Button variant="outline" size="sm" disabled><RotateCw class="mr-1.5 h-3.5 w-3.5" /> Restart</Button>
					{:else}
						<Button variant="outline" size="sm" disabled><Play class="mr-1.5 h-3.5 w-3.5" /> Start</Button>
					{/if}
					<Button variant="outline" size="sm" disabled><Wrench class="mr-1.5 h-3.5 w-3.5" /> Build</Button>
					<Button variant="outline" size="sm" disabled><RefreshCw class="mr-1.5 h-3.5 w-3.5" /> Refresh</Button>
					<Button variant="outline" size="sm" disabled><SquareTerminal class="mr-1.5 h-3.5 w-3.5" /> Logs</Button>
					<Button variant="outline" size="sm" disabled><Download class="mr-1.5 h-3.5 w-3.5" /> Download</Button>
				</div>

				<h3 class="mb-2 text-sm font-medium">Port Mappings</h3>
				<div class="overflow-x-auto rounded-md border">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Container</th>
								<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Host</th>
								<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Protocol</th>
								<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
								<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Actions</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each app.ports as port}
								<tr class="hover:bg-muted/30">
									<td class="px-3 py-2 font-mono">{port.container}</td>
									<td class="px-3 py-2 font-mono">{port.host}</td>
									<td class="px-3 py-2">{port.protocol}</td>
									<td class="px-3 py-2">
										<Badge variant="outline" class="text-xs bg-emerald-500/15 text-emerald-500 border-emerald-500/30">{port.status}</Badge>
									</td>
									<td class="px-3 py-2">
										<div class="flex gap-1">
											<Button variant="ghost" size="sm" class="h-6 w-6 p-0" disabled title="Copy">
												<Copy class="h-3 w-3" />
											</Button>
											<Button variant="ghost" size="sm" class="h-6 w-6 p-0" disabled title="Open">
												<ExternalLink class="h-3 w-3" />
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
	</div>

	<!-- ===== SECTION: Analyses ===== -->
	<div id="analyses" class="scroll-mt-16 space-y-4">
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold">Analyses</h2>
			<Button variant="outline" size="sm" href="/analysis" disabled>New Analysis</Button>
		</div>

		<div class="flex gap-3">
			<Badge variant="outline">{app.analyses.length} total</Badge>
			<Badge variant="outline" class="border-emerald-500/30 text-emerald-500">{app.analyses.filter(a => a.status === 'Complete').length} done</Badge>
			<Badge variant="outline" class="border-blue-500/30 text-blue-400">{app.analyses.filter(a => a.status === 'Running').length} running</Badge>
		</div>

		<Card.Root>
			<Card.Content class="p-0">
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Task ID</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Type</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Findings</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Duration</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Actions</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each app.analyses as analysis}
								<tr class="hover:bg-muted/30">
									<td class="px-4 py-2.5 font-mono text-xs">{analysis.id}</td>
									<td class="px-4 py-2.5">{analysis.type}</td>
									<td class="px-4 py-2.5">
										<Badge variant="outline" class="text-[10px] {analysis.status === 'Complete' ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30' : analysis.status === 'Running' ? 'bg-blue-500/15 text-blue-400 border-blue-500/30' : ''}">
											{#if analysis.status === 'Running'}
												<span class="mr-1 h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse"></span>
											{/if}
											{analysis.status}
										</Badge>
									</td>
									<td class="px-4 py-2.5">
										<span class="font-mono {analysis.findings > 5 ? 'text-red-400' : analysis.findings > 0 ? 'text-amber-500' : 'text-muted-foreground'}">{analysis.findings}</span>
									</td>
									<td class="px-4 py-2.5 text-muted-foreground">{analysis.duration}</td>
									<td class="px-4 py-2.5 text-muted-foreground">{analysis.createdAt}</td>
									<td class="px-4 py-2.5">
										<Button variant="ghost" size="sm" class="h-7 px-2 text-xs" disabled>
											<Eye class="mr-1 h-3 w-3" /> View
										</Button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- ===== SECTION: Artifacts ===== -->
	<div id="artifacts" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Artifacts</h2>
		<div class="grid gap-3 md:grid-cols-3">
			{#each app.artifacts as artifact}
				<Card.Root class="hover:bg-muted/30 transition-colors cursor-pointer">
					<Card.Content class="flex items-center gap-3 p-4">
						<FileText class="h-8 w-8 text-muted-foreground shrink-0" />
						<div class="min-w-0 flex-1">
							<p class="text-sm font-medium truncate">{artifact.name}</p>
							<p class="text-xs text-muted-foreground">{artifact.size}</p>
						</div>
						<Button variant="ghost" size="sm" class="h-7 w-7 p-0 shrink-0" disabled>
							<Eye class="h-3.5 w-3.5" />
						</Button>
					</Card.Content>
				</Card.Root>
			{/each}
		</div>
	</div>

	<!-- ===== SECTION: Files ===== -->
	<div id="files" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Files</h2>
		<div class="flex gap-3 mb-3">
			<Badge variant="outline">{app.fileStats.total} files</Badge>
			<Badge variant="outline">{app.fileStats.size}</Badge>
			<Badge variant="outline">{app.fileStats.code} code</Badge>
			<Badge variant="outline">{app.fileStats.config} config</Badge>
		</div>

		<div class="grid gap-4 md:grid-cols-2">
			<!-- File Tree -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Explorer</Card.Title></Card.Header>
				<Card.Content>
					<div class="space-y-1 text-sm font-mono">
						{#each app.files as item}
							{#if item.type === 'dir'}
								<div>
									<div class="flex items-center gap-1.5 py-1 text-muted-foreground hover:text-foreground cursor-pointer">
										<FolderOpen class="h-3.5 w-3.5 text-amber-500" />
										<span>{item.path}</span>
									</div>
									{#if item.children}
										<div class="ml-5 space-y-0.5">
											{#each item.children as child}
												<div class="flex items-center gap-1.5 py-0.5 text-muted-foreground hover:text-foreground cursor-pointer">
													{#if child.endsWith('/')}
														<FolderOpen class="h-3 w-3 text-amber-500" />
													{:else}
														<FileText class="h-3 w-3" />
													{/if}
													<span class="text-xs">{child}</span>
												</div>
											{/each}
										</div>
									{/if}
								</div>
							{:else}
								<div class="flex items-center gap-1.5 py-1 text-muted-foreground hover:text-foreground cursor-pointer">
									<FileText class="h-3.5 w-3.5" />
									<span>{item.path}</span>
								</div>
							{/if}
						{/each}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Extension Breakdown -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Extension Breakdown</Card.Title></Card.Header>
				<Card.Content>
					<div class="space-y-2">
						{#each Object.entries(app.extensions) as [ext, pct]}
							<div class="flex items-center justify-between text-sm">
								<span class="font-mono">{ext}</span>
								<div class="flex items-center gap-2">
									<div class="h-2 w-24 rounded-full bg-muted overflow-hidden">
										<div class="h-full rounded-full bg-primary/60" style="width: {pct}%"></div>
									</div>
									<span class="text-xs text-muted-foreground w-8 text-right">{pct}%</span>
								</div>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	</div>

	<!-- ===== SECTION: Logs ===== -->
	<div id="logs" class="scroll-mt-16 space-y-4">
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold">Logs</h2>
			<div class="flex items-center gap-2">
				<Button variant="outline" size="sm" disabled>Download</Button>
			</div>
		</div>
		<Card.Root>
			<Card.Content class="p-0">
				<div class="flex items-center gap-3 border-b px-4 py-2">
					<Badge variant="outline" class="text-xs text-blue-400">{app.logs.filter(l => l.level === 'INFO').length} info</Badge>
					<Badge variant="outline" class="text-xs text-amber-500">{app.logs.filter(l => l.level === 'WARNING').length} warn</Badge>
					<Badge variant="outline" class="text-xs text-red-400">{app.logs.filter(l => l.level === 'ERROR').length} error</Badge>
				</div>
				<div class="bg-zinc-950 p-4 font-mono text-xs leading-relaxed max-h-80 overflow-y-auto">
					{#each app.logs as log}
						<div class="flex gap-3">
							<span class="text-zinc-500 select-none">{log.timestamp}</span>
							<span class="{logLevelColors[log.level] ?? 'text-zinc-400'} w-16 shrink-0">[{log.level}]</span>
							<span class="text-zinc-300">{log.message}</span>
						</div>
					{/each}
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- ===== SECTION: Metadata ===== -->
	<div id="metadata" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Metadata</h2>
		<div class="grid gap-4 md:grid-cols-2">
			<!-- Environment Variables -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Environment Variables</Card.Title></Card.Header>
				<Card.Content>
					<div class="space-y-1.5">
						{#each app.envVars as env}
							<div class="flex items-center justify-between text-sm font-mono rounded bg-muted/30 px-3 py-1.5">
								<span class="text-muted-foreground">{env.key}</span>
								<span>{env.value}</span>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Dependencies -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Dependencies</Card.Title></Card.Header>
				<Card.Content>
					<div class="space-y-3">
						<div>
							<h4 class="mb-1.5 text-xs font-medium text-muted-foreground uppercase">Backend</h4>
							<div class="flex flex-wrap gap-1">
								{#each app.dependencies.backend as dep}
									<Badge variant="secondary" class="text-xs font-mono">{dep}</Badge>
								{/each}
							</div>
						</div>
						<Separator />
						<div>
							<h4 class="mb-1.5 text-xs font-medium text-muted-foreground uppercase">Frontend</h4>
							<div class="flex flex-wrap gap-1">
								{#each app.dependencies.frontend as dep}
									<Badge variant="secondary" class="text-xs font-mono">{dep}</Badge>
								{/each}
							</div>
						</div>
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	</div>

	<!-- ===== SECTION: Prompts ===== -->
	<div id="prompts" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Prompts</h2>
		<div class="grid gap-4 md:grid-cols-2">
			{#each Object.entries(app.prompts) as [type, prompt]}
				<Card.Root>
					<Card.Header>
						<Card.Title class="text-sm capitalize">{type} Prompt</Card.Title>
					</Card.Header>
					<Card.Content class="space-y-3">
						<div>
							<h4 class="mb-1 text-xs font-medium text-muted-foreground uppercase">Question</h4>
							<div class="rounded-md bg-muted/30 p-3 text-sm">{prompt.question}</div>
						</div>
						<div>
							<h4 class="mb-1 text-xs font-medium text-muted-foreground uppercase">Response</h4>
							<div class="rounded-md bg-muted/30 p-3 text-sm max-h-40 overflow-y-auto">{prompt.response}</div>
						</div>
					</Card.Content>
				</Card.Root>
			{/each}
		</div>
	</div>

	<!-- ===== SECTION: Ports ===== -->
	<div id="ports" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Ports</h2>
		<Card.Root>
			<Card.Content class="p-0">
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Container Port</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Host Port</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Protocol</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each app.ports as port}
								<tr class="hover:bg-muted/30">
									<td class="px-4 py-2.5 font-mono">{port.container}</td>
									<td class="px-4 py-2.5 font-mono">{port.host}</td>
									<td class="px-4 py-2.5">{port.protocol}</td>
									<td class="px-4 py-2.5">
										<Badge variant="outline" class="text-xs bg-emerald-500/15 text-emerald-500 border-emerald-500/30">{port.status}</Badge>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- ===== SECTION: Tools ===== -->
	<div id="tools" class="scroll-mt-16 space-y-4">
		<h2 class="text-lg font-semibold">Tools</h2>
		<div class="grid gap-4 md:grid-cols-2">
			<!-- API Tester -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">API Tester</Card.Title></Card.Header>
				<Card.Content>
					<div class="space-y-3">
						<div class="flex gap-2">
							<select class="h-9 rounded-md border border-input bg-background px-2 text-sm" disabled>
								<option>GET</option>
								<option>POST</option>
								<option>PUT</option>
								<option>DELETE</option>
							</select>
							<input type="text" value="/api/tasks" class="h-9 flex-1 rounded-md border border-input bg-background px-3 text-sm font-mono" disabled />
							<Button size="sm" disabled>Send</Button>
						</div>
						<div class="rounded-md bg-zinc-950 p-3 font-mono text-xs text-zinc-400 h-24">
							// Response will appear here
						</div>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Quick Commands -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Quick Commands</Card.Title></Card.Header>
				<Card.Content>
					<div class="grid grid-cols-2 gap-2">
						{#each ['pip list', 'npm list', 'health check', 'list routes', 'processes', 'env vars', 'disk usage'] as cmd}
							<Button variant="outline" size="sm" class="justify-start text-xs font-mono" disabled>
								<Terminal class="mr-1.5 h-3 w-3" /> {cmd}
							</Button>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Dependencies Viewer -->
			<Card.Root class="md:col-span-2">
				<Card.Header><Card.Title class="text-sm">Dependencies</Card.Title></Card.Header>
				<Card.Content>
					<div class="grid gap-4 md:grid-cols-2">
						<div>
							<h4 class="mb-2 text-xs font-medium text-muted-foreground uppercase">Backend (pip)</h4>
							<div class="rounded-md bg-zinc-950 p-3 font-mono text-xs text-zinc-300 max-h-32 overflow-y-auto">
								{#each app.dependencies.backend as dep}
									<div>{dep}</div>
								{/each}
							</div>
						</div>
						<div>
							<h4 class="mb-2 text-xs font-medium text-muted-foreground uppercase">Frontend (npm)</h4>
							<div class="rounded-md bg-zinc-950 p-3 font-mono text-xs text-zinc-300 max-h-32 overflow-y-auto">
								{#each app.dependencies.frontend as dep}
									<div>{dep}</div>
								{/each}
							</div>
						</div>
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
</div>
