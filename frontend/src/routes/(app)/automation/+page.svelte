<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Separator } from '$lib/components/ui/separator';
	import Wand from '@lucide/svelte/icons/wand';
	import Play from '@lucide/svelte/icons/play';
	import Pause from '@lucide/svelte/icons/pause';
	import RotateCcw from '@lucide/svelte/icons/rotate-ccw';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Search from '@lucide/svelte/icons/search';
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import Clock from '@lucide/svelte/icons/clock';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import Settings from '@lucide/svelte/icons/settings';
	import Download from '@lucide/svelte/icons/download';
	import Upload from '@lucide/svelte/icons/upload';
	import Save from '@lucide/svelte/icons/save';
	import FolderOpen from '@lucide/svelte/icons/folder-open';
	import Shield from '@lucide/svelte/icons/shield';
	import Zap from '@lucide/svelte/icons/zap';
	import Gauge from '@lucide/svelte/icons/gauge';
	import Brain from '@lucide/svelte/icons/brain';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';

	let step = $state(1);
	let genMode = $state<'new' | 'existing'>('new');
	let templateSearch = $state('');
	let modelSearch = $state('');
	let existingSearch = $state('');
	let existingModelFilter = $state('all');
	let existingStatusFilter = $state('all');
	let parallel = $state(true);
	let maxConcurrent = $state(5);
	let analysisParallel = $state(true);
	let analysisMaxConcurrent = $state(2);
	let autoStart = $state(true);
	let stopAfter = $state(false);
	let pipelineName = $state('');

	const templates = [
		{ slug: 'todo-app', name: 'Todo Application', description: 'A full-featured task management app with CRUD operations and user authentication', category: 'Productivity' },
		{ slug: 'blog-platform', name: 'Blog Platform', description: 'Content management system with posts, comments, and user profiles', category: 'Content' },
		{ slug: 'ecommerce', name: 'E-Commerce Store', description: 'Online store with product catalog, cart, and checkout flow', category: 'Commerce' },
		{ slug: 'dashboard', name: 'Analytics Dashboard', description: 'Data visualization dashboard with charts and real-time metrics', category: 'Analytics' },
		{ slug: 'chat-app', name: 'Chat Application', description: 'Real-time messaging app with rooms and direct messages', category: 'Communication' },
		{ slug: 'weather-app', name: 'Weather App', description: 'Weather forecast application with location search and maps', category: 'Utility' },
		{ slug: 'recipe-manager', name: 'Recipe Manager', description: 'Recipe collection app with search, categories, and meal planning', category: 'Lifestyle' },
		{ slug: 'project-tracker', name: 'Project Tracker', description: 'Project management tool with kanban boards and team collaboration', category: 'Productivity' },
	];

	const models = [
		{ slug: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', inputPrice: 2.50, outputPrice: 10.00 },
		{ slug: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', inputPrice: 0.15, outputPrice: 0.60 },
		{ slug: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', inputPrice: 3.00, outputPrice: 15.00 },
		{ slug: 'claude-3-haiku', name: 'Claude 3 Haiku', provider: 'Anthropic', inputPrice: 0.25, outputPrice: 1.25 },
		{ slug: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', provider: 'Google', inputPrice: 1.25, outputPrice: 5.00 },
		{ slug: 'gemini-1-5-flash', name: 'Gemini 1.5 Flash', provider: 'Google', inputPrice: 0.075, outputPrice: 0.30 },
	];

	const existingApps = [
		{ modelSlug: 'gpt-4o', appNumber: 1, templateSlug: 'todo-app', createdAt: '2025-03-15', status: 'completed' },
		{ modelSlug: 'gpt-4o', appNumber: 2, templateSlug: 'blog-platform', createdAt: '2025-03-14', status: 'completed' },
		{ modelSlug: 'claude-3-5-sonnet', appNumber: 1, templateSlug: 'todo-app', createdAt: '2025-03-13', status: 'completed' },
		{ modelSlug: 'claude-3-5-sonnet', appNumber: 2, templateSlug: 'ecommerce', createdAt: '2025-03-12', status: 'failed' },
		{ modelSlug: 'gemini-1-5-pro', appNumber: 1, templateSlug: 'dashboard', createdAt: '2025-03-11', status: 'completed' },
		{ modelSlug: 'gpt-4o-mini', appNumber: 1, templateSlug: 'chat-app', createdAt: '2025-03-10', status: 'pending' },
	];

	const analysisTools: Record<string, { name: string; displayName: string; description: string; available: boolean }[]> = {
		static: [
			{ name: 'bandit', displayName: 'Bandit', description: 'Python security linter', available: true },
			{ name: 'eslint', displayName: 'ESLint', description: 'JavaScript/TypeScript linter', available: true },
			{ name: 'ruff', displayName: 'Ruff', description: 'Fast Python linter', available: true },
		],
		dynamic: [
			{ name: 'zap', displayName: 'OWASP ZAP', description: 'Web application security scanner', available: true },
			{ name: 'port-scan', displayName: 'Port Scanner', description: 'Network port scanning', available: true },
			{ name: 'connectivity', displayName: 'Connectivity Test', description: 'Service reachability checks', available: true },
		],
		performance: [
			{ name: 'lighthouse', displayName: 'Lighthouse', description: 'Web performance audits', available: true },
			{ name: 'load-test', displayName: 'Load Test', description: 'Concurrent request load testing', available: true },
		],
		ai: [
			{ name: 'requirements-scanner', displayName: 'Requirements Scanner', description: 'AI requirement compliance check', available: true },
			{ name: 'code-quality', displayName: 'Code Quality', description: 'AI code quality review', available: true },
		],
	};

	const pipelines = [
		{ id: 'pipe-001', name: 'Full Benchmark Run', status: 'completed', progress: 100, createdAt: '2025-03-18 14:30', duration: '12m 45s' },
		{ id: 'pipe-002', name: 'Static Analysis Only', status: 'running', progress: 65, createdAt: '2025-03-19 09:15', duration: '3m 20s' },
		{ id: 'pipe-003', name: 'Quick Security Scan', status: 'failed', progress: 40, createdAt: '2025-03-17 11:00', duration: '5m 12s' },
		{ id: 'pipe-004', name: 'Nightly Regression', status: 'pending', progress: 0, createdAt: '2025-03-19 22:00', duration: '—' },
		{ id: 'pipe-005', name: 'Claude vs GPT Compare', status: 'completed', progress: 100, createdAt: '2025-03-16 10:30', duration: '18m 03s' },
	];

	let selectedTemplates = $state<Set<string>>(new Set());
	let selectedModels = $state<Set<string>>(new Set());
	let selectedExisting = $state<Set<string>>(new Set());
	let selectedTools = $state<Set<string>>(new Set(['bandit', 'eslint', 'ruff', 'zap', 'lighthouse', 'requirements-scanner']));

	const filteredTemplates = $derived(templates.filter(t =>
		t.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
		t.description.toLowerCase().includes(templateSearch.toLowerCase())
	));
	const filteredModels = $derived(models.filter(m =>
		m.name.toLowerCase().includes(modelSearch.toLowerCase())
	));
	const filteredExisting = $derived(existingApps.filter(a =>
		(existingModelFilter === 'all' || a.modelSlug === existingModelFilter) &&
		(existingStatusFilter === 'all' || a.status === existingStatusFilter) &&
		(existingSearch === '' || a.modelSlug.includes(existingSearch.toLowerCase()) || a.templateSlug.includes(existingSearch.toLowerCase()))
	));

	const totalJobs = $derived(
		genMode === 'new' ? selectedTemplates.size * selectedModels.size : selectedExisting.size
	);

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		running: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		failed: 'bg-red-500/15 text-red-400 border-red-500/30',
		pending: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
		paused: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		partial_success: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		cancelled: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const toolCategoryIcons: Record<string, { icon: typeof Shield; color: string; label: string }> = {
		static: { icon: Shield, label: 'Static Analysis', color: 'text-blue-400' },
		dynamic: { icon: Zap, label: 'Dynamic Analysis', color: 'text-emerald-500' },
		performance: { icon: Gauge, label: 'Performance', color: 'text-cyan-400' },
		ai: { icon: Brain, label: 'AI Review', color: 'text-amber-500' },
	};

	function toggleTemplate(slug: string) {
		const s = new Set(selectedTemplates);
		s.has(slug) ? s.delete(slug) : s.add(slug);
		selectedTemplates = s;
	}
	function toggleModel(slug: string) {
		const s = new Set(selectedModels);
		s.has(slug) ? s.delete(slug) : s.add(slug);
		selectedModels = s;
	}
	function toggleExisting(key: string) {
		const s = new Set(selectedExisting);
		s.has(key) ? s.delete(key) : s.add(key);
		selectedExisting = s;
	}
	function toggleTool(name: string) {
		const s = new Set(selectedTools);
		s.has(name) ? s.delete(name) : s.add(name);
		selectedTools = s;
	}
	function selectAllTemplates() { selectedTemplates = new Set(filteredTemplates.map(t => t.slug)); }
	function clearTemplates() { selectedTemplates = new Set(); }
	function selectAllModels() { selectedModels = new Set(filteredModels.map(m => m.slug)); }
	function clearModels() { selectedModels = new Set(); }

	const providers = $derived([...new Set(models.map(m => m.provider))]);
</script>

<svelte:head>
	<title>Automation - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<div class="flex items-center gap-3">
				<h1 class="text-2xl font-bold tracking-tight">Automation Pipeline</h1>
				<Badge variant="outline" class="text-xs">End-to-end</Badge>
			</div>
			<p class="mt-1 text-sm text-muted-foreground">End-to-end workflow: Generation → Analysis</p>
		</div>
	</div>

	<div class="grid gap-6 lg:grid-cols-[1fr_340px]">
		<!-- Left Column: Wizard -->
		<div class="space-y-6">
			<!-- Step Indicator -->
			<div class="flex items-center gap-2">
				{#each [{ n: 1, label: 'Generate' }, { n: 2, label: 'Analyze' }, { n: 3, label: 'Execute' }] as s}
					<button
						class="flex items-center gap-2 rounded-full px-4 py-1.5 text-sm transition-colors {step === s.n ? 'bg-primary text-primary-foreground font-medium' : step > s.n ? 'bg-emerald-500/15 text-emerald-500' : 'bg-muted text-muted-foreground'}"
						onclick={() => { if (s.n <= step) step = s.n; }}
					>
						{#if step > s.n}<Check class="h-3.5 w-3.5" />{:else}<span class="font-mono text-xs">{s.n}</span>{/if}
						{s.label}
					</button>
					{#if s.n < 3}<div class="h-px flex-1 bg-border"></div>{/if}
				{/each}
			</div>

			<!-- Step 1: Sample Generation -->
			{#if step === 1}
				<Card.Root>
					<Card.Header>
						<div class="flex items-center justify-between">
							<div>
								<Card.Title>Sample Generation</Card.Title>
								<Card.Description>Select templates and models or use existing applications.</Card.Description>
							</div>
							<div class="flex gap-1 rounded-lg bg-muted p-1">
								<button class="rounded-md px-3 py-1 text-xs transition-colors {genMode === 'new' ? 'bg-background shadow-sm font-medium' : 'text-muted-foreground'}" onclick={() => genMode = 'new'}>Generate New</button>
								<button class="rounded-md px-3 py-1 text-xs transition-colors {genMode === 'existing' ? 'bg-background shadow-sm font-medium' : 'text-muted-foreground'}" onclick={() => genMode = 'existing'}>Use Existing</button>
							</div>
						</div>
					</Card.Header>
					<Card.Content>
						{#if genMode === 'new'}
							<div class="grid gap-4 md:grid-cols-2">
								<!-- Templates -->
								<div class="space-y-3">
									<div class="flex items-center justify-between">
										<h3 class="text-sm font-medium">Templates</h3>
										<div class="flex gap-1">
											<button class="text-[10px] text-primary hover:underline" onclick={selectAllTemplates}>Select All</button>
											<span class="text-muted-foreground">|</span>
											<button class="text-[10px] text-muted-foreground hover:underline" onclick={clearTemplates}>Clear</button>
										</div>
									</div>
									<div class="relative">
										<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
										<Input bind:value={templateSearch} placeholder="Search templates..." class="h-8 pl-8 text-xs" />
									</div>
									<div class="max-h-60 space-y-1 overflow-y-auto">
										{#each filteredTemplates as t}
											<button
												class="flex w-full items-start gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-muted/50 {selectedTemplates.has(t.slug) ? 'bg-primary/5 ring-1 ring-primary/20' : ''}"
												onclick={() => toggleTemplate(t.slug)}
											>
												<div class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border {selectedTemplates.has(t.slug) ? 'bg-primary border-primary text-primary-foreground' : 'border-border'}">
													{#if selectedTemplates.has(t.slug)}<Check class="h-3 w-3" />{/if}
												</div>
												<div class="min-w-0">
													<div class="font-medium">{t.name}</div>
													<div class="text-xs text-muted-foreground line-clamp-1">{t.description}</div>
												</div>
												<Badge variant="secondary" class="ml-auto shrink-0 text-[10px]">{t.category}</Badge>
											</button>
										{/each}
									</div>
								</div>

								<!-- Models -->
								<div class="space-y-3">
									<div class="flex items-center justify-between">
										<h3 class="text-sm font-medium">Models</h3>
										<div class="flex gap-1">
											<button class="text-[10px] text-primary hover:underline" onclick={selectAllModels}>Select All</button>
											<span class="text-muted-foreground">|</span>
											<button class="text-[10px] text-muted-foreground hover:underline" onclick={clearModels}>Clear</button>
										</div>
									</div>
									<div class="relative">
										<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
										<Input bind:value={modelSearch} placeholder="Search models..." class="h-8 pl-8 text-xs" />
									</div>
									<div class="max-h-60 space-y-1 overflow-y-auto">
										{#each providers as provider}
											<div class="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{provider}</div>
											{#each filteredModels.filter(m => m.provider === provider) as m}
												<button
													class="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-muted/50 {selectedModels.has(m.slug) ? 'bg-primary/5 ring-1 ring-primary/20' : ''}"
													onclick={() => toggleModel(m.slug)}
												>
													<div class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border {selectedModels.has(m.slug) ? 'bg-primary border-primary text-primary-foreground' : 'border-border'}">
														{#if selectedModels.has(m.slug)}<Check class="h-3 w-3" />{/if}
													</div>
													<span class="font-medium">{m.name}</span>
													<span class="ml-auto font-mono text-xs text-muted-foreground">${m.inputPrice} / ${m.outputPrice}</span>
												</button>
											{/each}
										{/each}
									</div>
								</div>
							</div>

							<!-- Summary -->
							<div class="mt-4 flex items-center justify-between rounded-lg bg-muted/50 px-4 py-3">
								<div class="text-sm">
									<span class="font-mono font-semibold">{selectedTemplates.size}</span> templates × <span class="font-mono font-semibold">{selectedModels.size}</span> models = <span class="font-mono font-bold text-primary">{totalJobs}</span> jobs
								</div>
								<div class="flex items-center gap-4 text-xs text-muted-foreground">
									<label class="flex items-center gap-1.5">
										<input type="checkbox" bind:checked={parallel} class="rounded" />
										Parallel
									</label>
									<label class="flex items-center gap-1.5">
										Max:
										<Input type="number" bind:value={maxConcurrent} min={1} max={10} class="h-6 w-14 text-xs" />
									</label>
								</div>
							</div>
						{:else}
							<!-- Existing Apps -->
							<div class="space-y-3">
								<div class="flex gap-2">
									<div class="relative flex-1">
										<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
										<Input bind:value={existingSearch} placeholder="Search..." class="h-8 pl-8 text-xs" />
									</div>
									<select bind:value={existingModelFilter} class="h-8 rounded-md border bg-background px-2 text-xs">
										<option value="all">All Models</option>
										{#each [...new Set(existingApps.map(a => a.modelSlug))] as slug}
											<option value={slug}>{slug}</option>
										{/each}
									</select>
									<select bind:value={existingStatusFilter} class="h-8 rounded-md border bg-background px-2 text-xs">
										<option value="all">All Status</option>
										<option value="completed">Completed</option>
										<option value="failed">Failed</option>
										<option value="pending">Pending</option>
									</select>
								</div>
								<table class="w-full text-sm">
									<thead>
										<tr class="border-b bg-muted/30">
											<th class="w-8 px-3 py-2"></th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Model</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">App #</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Template</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Created</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
										</tr>
									</thead>
									<tbody class="divide-y">
										{#each filteredExisting as app}
											{@const key = `${app.modelSlug}-${app.appNumber}`}
											<tr class="hover:bg-muted/30 cursor-pointer" onclick={() => toggleExisting(key)}>
												<td class="px-3 py-2">
													<div class="flex h-4 w-4 items-center justify-center rounded border {selectedExisting.has(key) ? 'bg-primary border-primary text-primary-foreground' : 'border-border'}">
														{#if selectedExisting.has(key)}<Check class="h-3 w-3" />{/if}
													</div>
												</td>
												<td class="px-3 py-2 font-medium">{app.modelSlug}</td>
												<td class="px-3 py-2">#{app.appNumber}</td>
												<td class="px-3 py-2">{app.templateSlug}</td>
												<td class="px-3 py-2 text-muted-foreground">{app.createdAt}</td>
												<td class="px-3 py-2"><Badge variant="outline" class="text-[10px] {statusColors[app.status] ?? ''}">{app.status}</Badge></td>
											</tr>
										{/each}
									</tbody>
								</table>
								<div class="text-sm text-muted-foreground">{selectedExisting.size} selected</div>
							</div>
						{/if}
					</Card.Content>
				</Card.Root>
			{/if}

			<!-- Step 2: Analysis Configuration -->
			{#if step === 2}
				<Card.Root>
					<Card.Header>
						<Card.Title>Analysis Configuration</Card.Title>
						<Card.Description>Select analysis tools and configure execution options.</Card.Description>
					</Card.Header>
					<Card.Content class="space-y-4">
						<div class="grid gap-4 md:grid-cols-2">
							{#each Object.entries(analysisTools) as [cat, tools]}
								{@const meta = toolCategoryIcons[cat]}
								<Card.Root>
									<Card.Header class="pb-2">
										<div class="flex items-center gap-2">
											<meta.icon class="h-4 w-4 {meta.color}" />
											<Card.Title class="text-sm">{meta.label}</Card.Title>
										</div>
									</Card.Header>
									<Card.Content class="space-y-1">
										{#each tools as tool}
											<button
												class="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-muted/50 {selectedTools.has(tool.name) ? 'bg-primary/5' : ''}"
												onclick={() => toggleTool(tool.name)}
											>
												<div class="flex h-4 w-4 shrink-0 items-center justify-center rounded border {selectedTools.has(tool.name) ? 'bg-primary border-primary text-primary-foreground' : 'border-border'}">
													{#if selectedTools.has(tool.name)}<Check class="h-3 w-3" />{/if}
												</div>
												<div>
													<div class="font-medium">{tool.displayName}</div>
													<div class="text-xs text-muted-foreground">{tool.description}</div>
												</div>
												{#if !tool.available}
													<Badge variant="outline" class="ml-auto text-[10px] bg-zinc-500/15 text-zinc-400">Unavailable</Badge>
												{/if}
											</button>
										{/each}
									</Card.Content>
								</Card.Root>
							{/each}
						</div>

						<!-- Options -->
						<div class="flex flex-wrap items-center gap-4 rounded-lg bg-muted/50 px-4 py-3 text-sm">
							<label class="flex items-center gap-1.5">
								<input type="checkbox" bind:checked={analysisParallel} class="rounded" />
								Parallel execution
							</label>
							<label class="flex items-center gap-1.5">
								Max concurrent:
								<Input type="number" bind:value={analysisMaxConcurrent} min={1} max={10} class="h-6 w-14 text-xs" />
							</label>
							<label class="flex items-center gap-1.5">
								<input type="checkbox" bind:checked={autoStart} class="rounded" />
								Auto-start containers
							</label>
							<label class="flex items-center gap-1.5">
								<input type="checkbox" bind:checked={stopAfter} class="rounded" />
								Stop after analysis
							</label>
						</div>
						<div class="text-sm text-muted-foreground">{selectedTools.size} tools selected</div>
					</Card.Content>
				</Card.Root>
			{/if}

			<!-- Step 3: Review & Execute -->
			{#if step === 3}
				<div class="space-y-4">
					<div class="grid gap-4 md:grid-cols-2">
						<Card.Root>
							<Card.Header><Card.Title class="text-sm">Generation Summary</Card.Title></Card.Header>
							<Card.Content class="space-y-2 text-sm">
								<div class="flex justify-between"><span class="text-muted-foreground">Mode</span><span class="font-medium capitalize">{genMode}</span></div>
								{#if genMode === 'new'}
									<div class="flex justify-between"><span class="text-muted-foreground">Templates</span><span class="font-mono">{selectedTemplates.size}</span></div>
									<div class="flex justify-between"><span class="text-muted-foreground">Models</span><span class="font-mono">{selectedModels.size}</span></div>
								{/if}
								<div class="flex justify-between"><span class="text-muted-foreground">Jobs</span><span class="font-bold text-primary">{totalJobs}</span></div>
								<div class="flex justify-between"><span class="text-muted-foreground">Parallel</span><span>{parallel ? `Yes (max ${maxConcurrent})` : 'No'}</span></div>
							</Card.Content>
						</Card.Root>
						<Card.Root>
							<Card.Header><Card.Title class="text-sm">Analysis Summary</Card.Title></Card.Header>
							<Card.Content class="space-y-2 text-sm">
								<div class="flex justify-between"><span class="text-muted-foreground">Tools</span><span class="font-mono">{selectedTools.size}</span></div>
								<div class="flex justify-between"><span class="text-muted-foreground">Parallel</span><span>{analysisParallel ? `Yes (max ${analysisMaxConcurrent})` : 'No'}</span></div>
								<div class="flex justify-between"><span class="text-muted-foreground">Auto-start</span><span>{autoStart ? 'Yes' : 'No'}</span></div>
								<div class="flex justify-between"><span class="text-muted-foreground">Stop after</span><span>{stopAfter ? 'Yes' : 'No'}</span></div>
								<div class="flex flex-wrap gap-1 pt-1">
									{#each [...selectedTools] as t}
										<Badge variant="secondary" class="text-[10px]">{t}</Badge>
									{/each}
								</div>
							</Card.Content>
						</Card.Root>
					</div>

					<!-- Estimates -->
					<Card.Root>
						<Card.Content class="py-3">
							<div class="flex flex-wrap items-center gap-6 text-sm">
								<div><span class="text-muted-foreground">Est. Duration:</span> <span class="font-mono font-medium">~{totalJobs * 2}m</span></div>
								<div><span class="text-muted-foreground">Total Operations:</span> <span class="font-mono">{totalJobs * selectedTools.size}</span></div>
								<div><span class="text-muted-foreground">Concurrency:</span> <span class="font-mono">{Math.min(maxConcurrent, analysisMaxConcurrent)}</span></div>
							</div>
						</Card.Content>
					</Card.Root>

					<!-- Pipeline Name -->
					<div class="flex items-center gap-3">
						<label class="text-sm font-medium whitespace-nowrap">Pipeline Name</label>
						<Input bind:value={pipelineName} placeholder="e.g. Full Benchmark Run" class="max-w-sm" />
					</div>

					{#if genMode === 'new' && totalJobs > 0}
						<Card.Root>
							<Card.Header><Card.Title class="text-sm">Job Queue Preview</Card.Title></Card.Header>
							<Card.Content class="p-0">
								<table class="w-full text-sm">
									<thead>
										<tr class="border-b bg-muted/30">
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">#</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Template</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Model</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Analysis</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Est. Time</th>
										</tr>
									</thead>
									<tbody class="divide-y">
										{#each [...selectedTemplates].flatMap(t => [...selectedModels].map(m => ({ t, m }))).slice(0, 10) as job, i}
											<tr class="hover:bg-muted/30">
												<td class="px-3 py-2 font-mono text-xs text-muted-foreground">{i + 1}</td>
												<td class="px-3 py-2">{templates.find(t => t.slug === job.t)?.name ?? job.t}</td>
												<td class="px-3 py-2">{models.find(m => m.slug === job.m)?.name ?? job.m}</td>
												<td class="px-3 py-2 font-mono text-xs">{selectedTools.size} tools</td>
												<td class="px-3 py-2 font-mono text-xs text-muted-foreground">~2m</td>
											</tr>
										{/each}
										{#if totalJobs > 10}
											<tr><td colspan="5" class="px-3 py-2 text-center text-xs text-muted-foreground">...and {totalJobs - 10} more jobs</td></tr>
										{/if}
									</tbody>
								</table>
							</Card.Content>
						</Card.Root>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Right Column: Sidebar -->
		<div class="space-y-4">
			<!-- Wizard Nav -->
			<Card.Root>
				<Card.Content class="p-4 space-y-4">
					<!-- Progress -->
					<div class="flex h-1.5 rounded-full bg-muted overflow-hidden">
						<div class="rounded-full bg-primary transition-all" style="width: {(step / 3) * 100}%"></div>
					</div>
					<div class="text-center text-sm text-muted-foreground">Step {step} of 3</div>

					{#if totalJobs > 0}
						<div class="rounded-lg bg-muted/50 p-3 text-center">
							<div class="text-2xl font-bold text-primary">{totalJobs}</div>
							<div class="text-xs text-muted-foreground">
								{genMode === 'new' ? `${selectedTemplates.size} × ${selectedModels.size}` : 'selected'} jobs
							</div>
						</div>
					{/if}

					<div class="flex gap-2">
						<Button variant="outline" size="sm" class="flex-1" disabled={step === 1} onclick={() => step--}>
							<ChevronLeft class="mr-1 h-3.5 w-3.5" /> Back
						</Button>
						{#if step < 3}
							<Button size="sm" class="flex-1" onclick={() => step++}>
								Next <ChevronRight class="ml-1 h-3.5 w-3.5" />
							</Button>
						{:else}
							<Button size="sm" class="flex-1" disabled>
								<Play class="mr-1 h-3.5 w-3.5" /> Start
							</Button>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Tools -->
			<Card.Root>
				<Card.Content class="p-4">
					<h3 class="mb-3 text-sm font-medium">Tools</h3>
					<div class="grid grid-cols-2 gap-2">
						<Button variant="outline" size="sm" class="gap-1.5 text-xs" disabled><Save class="h-3 w-3" /> Save</Button>
						<Button variant="outline" size="sm" class="gap-1.5 text-xs" disabled><FolderOpen class="h-3 w-3" /> Load</Button>
						<Button variant="outline" size="sm" class="gap-1.5 text-xs" disabled><Download class="h-3 w-3" /> Export</Button>
						<Button variant="outline" size="sm" class="gap-1.5 text-xs" disabled><Upload class="h-3 w-3" /> Import</Button>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Pipeline Executions -->
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm">Pipeline Executions</Card.Title>
				</Card.Header>
				<Card.Content class="p-0">
					<div class="max-h-72 overflow-y-auto">
						{#each pipelines as pipe}
							<div class="flex items-center gap-3 border-b px-4 py-2.5 last:border-0 hover:bg-muted/30">
								<div class="relative flex h-2.5 w-2.5 shrink-0">
									{#if pipe.status === 'running'}
										<span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75"></span>
									{/if}
									<span class="relative inline-flex h-2.5 w-2.5 rounded-full {pipe.status === 'completed' ? 'bg-emerald-500' : pipe.status === 'running' ? 'bg-amber-500' : pipe.status === 'failed' ? 'bg-red-400' : 'bg-zinc-400'}"></span>
								</div>
								<div class="min-w-0 flex-1">
									<div class="text-sm font-medium truncate">{pipe.name}</div>
									<div class="flex items-center gap-2 text-[10px] text-muted-foreground">
										<Badge variant="outline" class="text-[9px] {statusColors[pipe.status] ?? ''}">{pipe.status}</Badge>
										<span>{pipe.createdAt}</span>
									</div>
									{#if pipe.status === 'running'}
										<div class="mt-1 h-1 w-full rounded-full bg-muted overflow-hidden">
											<div class="h-full rounded-full bg-amber-500 transition-all" style="width: {pipe.progress}%"></div>
										</div>
									{/if}
								</div>
								<span class="text-[10px] text-muted-foreground font-mono">{pipe.duration}</span>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
</div>
