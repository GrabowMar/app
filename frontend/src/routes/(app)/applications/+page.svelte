<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import Search from '@lucide/svelte/icons/search';
	import Plus from '@lucide/svelte/icons/plus';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Download from '@lucide/svelte/icons/download';
	import SquareTerminal from '@lucide/svelte/icons/square-terminal';
	import Play from '@lucide/svelte/icons/play';
	import Square from '@lucide/svelte/icons/square';
	import RotateCw from '@lucide/svelte/icons/rotate-cw';
	import Trash2 from '@lucide/svelte/icons/trash-2';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import Eye from '@lucide/svelte/icons/eye';
	import Shield from '@lucide/svelte/icons/shield';
	import Unlock from '@lucide/svelte/icons/unlock';
	import MoreHorizontal from '@lucide/svelte/icons/more-horizontal';
	import Wrench from '@lucide/svelte/icons/wrench';

	interface Application {
		id: string;
		modelSlug: string;
		modelName: string;
		modelProvider: string;
		appNumber: number;
		version: string;
		templateSlug: string;
		templateName: string;
		generationMode: 'guarded' | 'unguarded';
		generationAttempts: number;
		status: string;
		totalFixes: number;
		containerSize: string;
		backendPort: number | null;
		frontendPort: number | null;
		analysisStatus: string;
		analysisIssues: number;
		createdAt: string;
	}

	const statusColors: Record<string, string> = {
		'Running': 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		'Stopped': 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
		'Building': 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		'Build Failed': 'bg-orange-500/15 text-orange-500 border-orange-500/30',
		'Dead': 'bg-red-500/15 text-red-400 border-red-500/30',
		'Error': 'bg-red-500/15 text-red-400 border-red-500/30',
		'Not Created': 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const analysisStatusColors: Record<string, string> = {
		'Complete': 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		'Running': 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		'Pending': 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		'None': 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
		'Failed': 'bg-red-500/15 text-red-400 border-red-500/30',
	};

	const apps: Application[] = [
		{ id: 'gpt-4o-1', modelSlug: 'gpt-4o', modelName: 'GPT-4o', modelProvider: 'OpenAI', appNumber: 1, version: 'v1.0', templateSlug: 'task-manager', templateName: 'Task Manager', generationMode: 'guarded', generationAttempts: 1, status: 'Running', totalFixes: 0, containerSize: '245 MB', backendPort: 5001, frontendPort: 8001, analysisStatus: 'Complete', analysisIssues: 3, createdAt: '19 Mar 14:32' },
		{ id: 'gpt-4o-2', modelSlug: 'gpt-4o', modelName: 'GPT-4o', modelProvider: 'OpenAI', appNumber: 2, version: 'v1.0', templateSlug: 'blog-platform', templateName: 'Blog Platform', generationMode: 'guarded', generationAttempts: 2, status: 'Running', totalFixes: 3, containerSize: '312 MB', backendPort: 5002, frontendPort: 8002, analysisStatus: 'Complete', analysisIssues: 7, createdAt: '19 Mar 13:15' },
		{ id: 'claude-3-5-sonnet-1', modelSlug: 'claude-3-5-sonnet', modelName: 'Claude 3.5 Sonnet', modelProvider: 'Anthropic', appNumber: 1, version: 'v1.0', templateSlug: 'task-manager', templateName: 'Task Manager', generationMode: 'guarded', generationAttempts: 1, status: 'Running', totalFixes: 0, containerSize: '198 MB', backendPort: 5003, frontendPort: 8003, analysisStatus: 'Running', analysisIssues: 0, createdAt: '19 Mar 12:45' },
		{ id: 'claude-3-5-sonnet-2', modelSlug: 'claude-3-5-sonnet', modelName: 'Claude 3.5 Sonnet', modelProvider: 'Anthropic', appNumber: 2, version: 'v1.0', templateSlug: 'e-commerce', templateName: 'E-Commerce', generationMode: 'unguarded', generationAttempts: 1, status: 'Stopped', totalFixes: 0, containerSize: '287 MB', backendPort: null, frontendPort: null, analysisStatus: 'Complete', analysisIssues: 12, createdAt: '18 Mar 22:10' },
		{ id: 'gemini-1-5-pro-1', modelSlug: 'gemini-1-5-pro', modelName: 'Gemini 1.5 Pro', modelProvider: 'Google', appNumber: 1, version: 'v1.0', templateSlug: 'task-manager', templateName: 'Task Manager', generationMode: 'guarded', generationAttempts: 3, status: 'Build Failed', totalFixes: 5, containerSize: '—', backendPort: null, frontendPort: null, analysisStatus: 'None', analysisIssues: 0, createdAt: '18 Mar 20:30' },
		{ id: 'gpt-4o-mini-1', modelSlug: 'gpt-4o-mini', modelName: 'GPT-4o Mini', modelProvider: 'OpenAI', appNumber: 1, version: 'v1.0', templateSlug: 'blog-platform', templateName: 'Blog Platform', generationMode: 'guarded', generationAttempts: 1, status: 'Running', totalFixes: 1, containerSize: '201 MB', backendPort: 5004, frontendPort: 8004, analysisStatus: 'Pending', analysisIssues: 0, createdAt: '18 Mar 19:00' },
		{ id: 'deepseek-v3-1', modelSlug: 'deepseek-v3', modelName: 'DeepSeek V3', modelProvider: 'DeepSeek', appNumber: 1, version: 'v1.0', templateSlug: 'e-commerce', templateName: 'E-Commerce', generationMode: 'unguarded', generationAttempts: 1, status: 'Dead', totalFixes: 0, containerSize: '—', backendPort: null, frontendPort: null, analysisStatus: 'Failed', analysisIssues: 0, createdAt: '18 Mar 17:45' },
		{ id: 'qwen-2-5-coder-1', modelSlug: 'qwen-2-5-coder', modelName: 'Qwen 2.5 Coder', modelProvider: 'Alibaba', appNumber: 1, version: 'v1.0', templateSlug: 'chat-app', templateName: 'Chat Application', generationMode: 'guarded', generationAttempts: 1, status: 'Running', totalFixes: 0, containerSize: '178 MB', backendPort: 5005, frontendPort: 8005, analysisStatus: 'Complete', analysisIssues: 2, createdAt: '18 Mar 16:20' },
		{ id: 'llama-3-1-405b-1', modelSlug: 'llama-3-1-405b', modelName: 'Llama 3.1 405B', modelProvider: 'Meta', appNumber: 1, version: 'v1.0', templateSlug: 'task-manager', templateName: 'Task Manager', generationMode: 'guarded', generationAttempts: 2, status: 'Stopped', totalFixes: 2, containerSize: '220 MB', backendPort: null, frontendPort: null, analysisStatus: 'Complete', analysisIssues: 8, createdAt: '18 Mar 15:00' },
		{ id: 'gemini-2-0-flash-1', modelSlug: 'gemini-2-0-flash', modelName: 'Gemini 2.0 Flash', modelProvider: 'Google', appNumber: 1, version: 'v1.0', templateSlug: 'blog-platform', templateName: 'Blog Platform', generationMode: 'guarded', generationAttempts: 1, status: 'Building', totalFixes: 0, containerSize: '—', backendPort: null, frontendPort: null, analysisStatus: 'None', analysisIssues: 0, createdAt: '18 Mar 14:30' },
	];

	let searchQuery = $state('');
	let statusFilter = $state('all');
	let modelFilter = $state('all');
	let templateFilter = $state('all');
	let selectedApps = $state(new Set<string>());
	let perPage = $state(25);
	let openMenu = $state<string | null>(null);

	const uniqueModels = [...new Map(apps.map(a => [a.modelSlug, a.modelName])).entries()];
	const uniqueTemplates = [...new Set(apps.map(a => a.templateName))];

	const filteredApps = $derived(
		apps.filter(a => {
			if (searchQuery && !a.modelName.toLowerCase().includes(searchQuery.toLowerCase()) && !a.templateName.toLowerCase().includes(searchQuery.toLowerCase())) return false;
			if (statusFilter !== 'all' && a.status !== statusFilter) return false;
			if (modelFilter !== 'all' && a.modelSlug !== modelFilter) return false;
			if (templateFilter !== 'all' && a.templateName !== templateFilter) return false;
			return true;
		})
	);

	const stats = $derived({
		total: apps.length,
		running: apps.filter(a => a.status === 'Running').length,
		analyzed: apps.filter(a => a.analysisStatus === 'Complete').length,
		uniqueModels: new Set(apps.map(a => a.modelSlug)).size,
	});

	function toggleAll() {
		if (selectedApps.size === filteredApps.length) {
			selectedApps = new Set();
		} else {
			selectedApps = new Set(filteredApps.map(a => a.id));
		}
	}

	function toggleApp(id: string) {
		const next = new Set(selectedApps);
		if (next.has(id)) next.delete(id); else next.add(id);
		selectedApps = next;
	}
</script>

<svelte:head>
	<title>Applications - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="page-header">
			<h1>Applications</h1>
			<p>View and manage generated web applications.</p>
		</div>
		<div class="flex items-center gap-2">
			<Button variant="outline" size="sm" disabled>
				<RefreshCw class="mr-2 h-3.5 w-3.5" />
				Refresh
			</Button>
			<Button size="sm" disabled>
				<Plus class="mr-2 h-3.5 w-3.5" />
				New Application
			</Button>
		</div>
	</div>

	<!-- Stats -->
	<div class="flex flex-wrap items-center gap-2">
		<Badge variant="outline" class="gap-1.5">
			<SquareTerminal class="h-3 w-3" />
			{stats.total} apps
		</Badge>
		<Badge variant="outline" class="gap-1.5 border-emerald-500/30 text-emerald-500">
			<Play class="h-3 w-3" />
			{stats.running} running
		</Badge>
		<Badge variant="outline" class="gap-1.5 border-blue-500/30 text-blue-400">
			{stats.analyzed} analyzed
		</Badge>
		<Badge variant="outline" class="gap-1.5">
			{stats.uniqueModels} models
		</Badge>
	</div>

	<!-- Filters -->
	<div class="flex flex-wrap items-center gap-3">
		<div class="relative flex-1 max-w-sm">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<input
				type="text"
				placeholder="Search applications..."
				class="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
				bind:value={searchQuery}
			/>
		</div>
		<select class="h-9 rounded-md border border-input bg-background px-3 text-sm" bind:value={modelFilter}>
			<option value="all">All Models</option>
			{#each uniqueModels as [slug, name]}
				<option value={slug}>{name}</option>
			{/each}
		</select>
		<select class="h-9 rounded-md border border-input bg-background px-3 text-sm" bind:value={statusFilter}>
			<option value="all">All Statuses</option>
			<option value="Running">Running</option>
			<option value="Stopped">Stopped</option>
			<option value="Building">Building</option>
			<option value="Build Failed">Build Failed</option>
			<option value="Dead">Dead</option>
			<option value="Error">Error</option>
			<option value="Not Created">Not Created</option>
		</select>
		<select class="h-9 rounded-md border border-input bg-background px-3 text-sm" bind:value={templateFilter}>
			<option value="all">All Templates</option>
			{#each uniqueTemplates as t}
				<option value={t}>{t}</option>
			{/each}
		</select>
		<select class="h-9 rounded-md border border-input bg-background px-3 text-sm" bind:value={perPage}>
			<option value={10}>10 / page</option>
			<option value={25}>25 / page</option>
			<option value={50}>50 / page</option>
			<option value={100}>100 / page</option>
		</select>
	</div>

	<!-- Batch Actions -->
	{#if selectedApps.size > 0}
		<div class="flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 px-4 py-2">
			<span class="text-sm font-medium">{selectedApps.size} selected</span>
			<Separator orientation="vertical" class="h-4" />
			<Button variant="outline" size="sm" disabled>
				<Play class="mr-1.5 h-3 w-3" /> Start
			</Button>
			<Button variant="outline" size="sm" disabled>
				<Square class="mr-1.5 h-3 w-3" /> Stop
			</Button>
			<Button variant="outline" size="sm" disabled>
				<RotateCw class="mr-1.5 h-3 w-3" /> Restart
			</Button>
			<Button variant="outline" size="sm" disabled>
				<Wrench class="mr-1.5 h-3 w-3" /> Build
			</Button>
			<Button variant="outline" size="sm" disabled>
				<Download class="mr-1.5 h-3 w-3" /> Export
			</Button>
			<Button variant="destructive" size="sm" disabled>
				<Trash2 class="mr-1.5 h-3 w-3" /> Delete
			</Button>
		</div>
	{/if}

	<!-- Table -->
	<Card.Root>
		<Card.Content class="p-0">
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="w-10 px-4 py-3">
								<input type="checkbox" class="rounded" checked={selectedApps.size === filteredApps.length && filteredApps.length > 0} onchange={toggleAll} />
							</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">App</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Mode</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Infra</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Analysis</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Actions</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each filteredApps.slice(0, perPage) as app (app.id)}
							<tr class="transition-colors hover:bg-muted/30">
								<!-- Checkbox -->
								<td class="px-4 py-3">
									<input type="checkbox" class="rounded" checked={selectedApps.has(app.id)} onchange={() => toggleApp(app.id)} />
								</td>

								<!-- Model -->
								<td class="px-4 py-3">
									<div class="flex flex-col gap-0.5">
										<a href="/models/{app.modelSlug}" class="text-sm font-medium hover:underline">{app.modelName}</a>
										<Badge variant="outline" class="w-fit text-[10px]">{app.modelProvider}</Badge>
									</div>
								</td>

								<!-- App -->
								<td class="px-4 py-3">
									<div class="flex flex-col gap-0.5">
										<span class="text-sm font-medium">#{app.appNumber} <span class="text-muted-foreground font-normal">{app.version}</span></span>
										<span class="text-xs text-muted-foreground">{app.templateName}</span>
										{#if app.generationAttempts > 1}
											<span class="text-xs text-amber-500">{app.generationAttempts} attempts</span>
										{/if}
									</div>
								</td>

								<!-- Created -->
								<td class="px-4 py-3 text-sm text-muted-foreground">{app.createdAt}</td>

								<!-- Mode -->
								<td class="px-4 py-3">
									{#if app.generationMode === 'guarded'}
										<Badge variant="outline" class="gap-1 border-emerald-500/30 text-emerald-500 text-[10px]">
											<Shield class="h-3 w-3" /> Guarded
										</Badge>
									{:else}
										<Badge variant="outline" class="gap-1 border-orange-500/30 text-orange-500 text-[10px]">
											<Unlock class="h-3 w-3" /> Unguarded
										</Badge>
									{/if}
								</td>

								<!-- Status -->
								<td class="px-4 py-3">
									<div class="flex items-center gap-1.5">
										<Badge variant="outline" class="text-[10px] {statusColors[app.status] ?? ''}">
											{#if app.status === 'Running'}
												<span class="mr-1 h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
											{/if}
											{app.status}
										</Badge>
										{#if app.totalFixes > 0}
											<Badge variant="secondary" class="text-[10px]">{app.totalFixes} fixes</Badge>
										{/if}
									</div>
								</td>

								<!-- Infra -->
								<td class="px-4 py-3">
									<div class="flex flex-col gap-0.5 text-xs font-mono text-muted-foreground">
										{#if app.backendPort}
											<span>:{app.backendPort}</span>
										{/if}
										{#if app.frontendPort}
											<span>:{app.frontendPort}</span>
										{/if}
										{#if !app.backendPort && !app.frontendPort}
											<span>—</span>
										{/if}
										<span class="text-[10px]">{app.containerSize}</span>
									</div>
								</td>

								<!-- Analysis -->
								<td class="px-4 py-3">
									<div class="flex items-center gap-1.5">
										<Badge variant="outline" class="text-[10px] {analysisStatusColors[app.analysisStatus] ?? ''}">
											{app.analysisStatus}
										</Badge>
										{#if app.analysisIssues > 0}
											<Badge variant="secondary" class="text-[10px] {app.analysisIssues > 10 ? 'text-red-400' : app.analysisIssues > 5 ? 'text-amber-500' : 'text-muted-foreground'}">
												{app.analysisIssues}
											</Badge>
										{/if}
									</div>
								</td>

								<!-- Actions -->
								<td class="px-4 py-3">
									<div class="flex items-center gap-1">
										<Button variant="ghost" size="sm" class="h-7 w-7 p-0" href="/applications/{app.modelSlug}/{app.appNumber}" title="View details">
											<Eye class="h-3.5 w-3.5" />
										</Button>
										{#if app.status === 'Running' && app.frontendPort}
											<Button variant="ghost" size="sm" class="h-7 w-7 p-0" title="Open app" disabled>
												<ExternalLink class="h-3.5 w-3.5" />
											</Button>
										{/if}
										<div class="relative">
											<Button variant="ghost" size="sm" class="h-7 w-7 p-0" onclick={() => openMenu = openMenu === app.id ? null : app.id}>
												<MoreHorizontal class="h-3.5 w-3.5" />
											</Button>
											{#if openMenu === app.id}
												<div class="absolute right-0 top-full z-50 mt-1 w-40 rounded-md border bg-popover p-1 shadow-md">
													{#if app.status === 'Running'}
														<button class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs hover:bg-accent" disabled>
															<Square class="h-3 w-3" /> Stop
														</button>
														<button class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs hover:bg-accent" disabled>
															<RotateCw class="h-3 w-3" /> Restart
														</button>
													{:else}
														<button class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs hover:bg-accent" disabled>
															<Play class="h-3 w-3" /> Start
														</button>
													{/if}
													<button class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs hover:bg-accent" disabled>
														<Wrench class="h-3 w-3" /> Rebuild
													</button>
													<Separator class="my-1" />
													<button class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs text-red-400 hover:bg-accent" disabled>
														<Trash2 class="h-3 w-3" /> Delete
													</button>
												</div>
											{/if}
										</div>
									</div>
								</td>
							</tr>
						{/each}

						{#if filteredApps.length === 0}
							<tr>
								<td colspan="9" class="px-4 py-12 text-center text-sm text-muted-foreground">
									No applications match your filters.
								</td>
							</tr>
						{/if}
					</tbody>
				</table>
			</div>
		</Card.Content>
	</Card.Root>

	<!-- Pagination -->
	{#if filteredApps.length > perPage}
		<div class="flex items-center justify-between text-sm text-muted-foreground">
			<span>Showing 1-{Math.min(perPage, filteredApps.length)} of {filteredApps.length}</span>
			<div class="flex items-center gap-1">
				<Button variant="outline" size="sm" disabled>Previous</Button>
				<Button variant="outline" size="sm" class="bg-primary/10">1</Button>
				<Button variant="outline" size="sm" disabled>Next</Button>
			</div>
		</div>
	{/if}
</div>
